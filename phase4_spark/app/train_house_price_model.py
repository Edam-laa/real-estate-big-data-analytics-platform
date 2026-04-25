import os
import uuid
import re
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression, RandomForestRegressor, GBTRegressor
from pyspark.ml.evaluation import RegressionEvaluator


# ============================================================
# CONFIG
# ============================================================
HDFS_INPUT_PATH = "hdfs://namenode:9000/data/ames/ames_housing_prepared.csv"

JDBC_URL = "jdbc:postgresql://ames-postgres:5432/ames_platform"
DB_USER = os.getenv("AMES_POSTGRES_USER", "ames_user")
DB_PASSWORD = os.getenv("AMES_POSTGRES_PASSWORD", "ames_password")
DB_DRIVER = "org.postgresql.Driver"

TARGET_COL = "SalePrice"
ID_COL = "house_id"
FOLD_VALUE = 0
SEED = 42

MODEL_RUNS_TABLE = "model_runs"
PREDICTIONS_TABLE = "predictions"


# ============================================================
# SPARK SESSION
# ============================================================
spark = (
    SparkSession.builder
    .appName("AmesHousing_Train_And_Store_To_Postgres")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")


# ============================================================
# HELPERS
# ============================================================
def sanitize_column_name(name: str) -> str:
    cleaned = re.sub(r"[^0-9a-zA-Z_]", "_", name)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_")

def get_jdbc_connection():
    jvm = spark._sc._gateway.jvm
    try:
        conn = jvm.java.sql.DriverManager.getConnection(JDBC_URL, DB_USER, DB_PASSWORD)
        return conn
    except Exception as e:
        raise Exception(f"Erreur connexion JDBC: {str(e)}")
    
    
def get_table_columns(table_name):
    conn = get_jdbc_connection()
    try:
        sql = f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """
        stmt = conn.createStatement()
        rs = stmt.executeQuery(sql)
        cols = []
        while rs.next():
            cols.append(rs.getString("column_name"))
        rs.close()
        stmt.close()
        return cols
    finally:
        conn.close()


def get_primary_key_column(table_name):
    conn = get_jdbc_connection()
    try:
        sql = f"""
            SELECT a.attname AS column_name
            FROM pg_index i
            JOIN pg_attribute a
              ON a.attrelid = i.indrelid
             AND a.attnum = ANY(i.indkey)
            JOIN pg_class c
              ON c.oid = i.indrelid
            JOIN pg_namespace n
              ON n.oid = c.relnamespace
            WHERE i.indisprimary
              AND n.nspname = 'public'
              AND c.relname = '{table_name}'
            LIMIT 1
        """
        stmt = conn.createStatement()
        rs = stmt.executeQuery(sql)
        pk = None
        if rs.next():
            pk = rs.getString("column_name")
        rs.close()
        stmt.close()
        return pk
    finally:
        conn.close()


def first_existing_column(table_columns, candidates):
    table_columns_lower = {c.lower(): c for c in table_columns}
    for cand in candidates:
        if cand.lower() in table_columns_lower:
            return table_columns_lower[cand.lower()]
    return None


def build_insert_payload_model_run(metrics_dict, table_columns):
    payload = {}

    mapping = {
        "model_name": ["model_name", "model", "algorithm"],
        "rmse_cv": ["rmse_cv"],
        "mae_cv": ["mae_cv"],
        "r2_cv": ["r2_cv"],
        "rmse_test": ["rmse_test"],
        "mae_test": ["mae_test"],
        "r2_test": ["r2_test"],
    }

    logical_values = {
        "model_name": metrics_dict["model_name"],
        "rmse_cv": float(metrics_dict["rmse_cv"]),
        "mae_cv": float(metrics_dict["mae_cv"]),
        "r2_cv": float(metrics_dict["r2_cv"]),
        "rmse_test": float(metrics_dict["rmse_test"]),
        "mae_test": float(metrics_dict["mae_test"]),
        "r2_test": float(metrics_dict["r2_test"]),
    }

    for logical_name, candidates in mapping.items():
        real_col = first_existing_column(table_columns, candidates)
        if real_col is not None:
            payload[real_col] = logical_values[logical_name]

    return payload


def insert_model_run(metrics_dict):
    table_columns = get_table_columns(MODEL_RUNS_TABLE)
    pk_col = get_primary_key_column(MODEL_RUNS_TABLE)

    payload = build_insert_payload_model_run(metrics_dict, table_columns)

    if not payload:
        raise Exception(
            f"Aucune colonne reconnue pour la table {MODEL_RUNS_TABLE}. "
            f"Colonnes trouvées: {table_columns}"
        )

    col_names = list(payload.keys())
    placeholders = ", ".join(["?"] * len(col_names))
    columns_sql = ", ".join(col_names)

    sql = f"INSERT INTO public.{MODEL_RUNS_TABLE} ({columns_sql}) VALUES ({placeholders})"
    if pk_col:
        sql += f" RETURNING {pk_col}"

    conn = get_jdbc_connection()
    try:
        pstmt = conn.prepareStatement(sql)

        for idx, col in enumerate(col_names, start=1):
            val = payload[col]
            if isinstance(val, float):
                pstmt.setDouble(idx, val)
            else:
                pstmt.setString(idx, str(val))

        if pk_col:
            rs = pstmt.executeQuery()
            rs.next()
            run_id = rs.getObject(1)
            rs.close()
        else:
            pstmt.executeUpdate()
            run_id = None

        pstmt.close()
        return run_id
    finally:
        conn.close()


def build_prediction_rows(pred_df, model_run_id, table_columns):
    run_id_col = first_existing_column(table_columns, ["run_id", "model_run_id"])
    house_id_col = first_existing_column(table_columns, ["house_id"])
    actual_col = first_existing_column(table_columns, ["saleprice_real", "actual_value", "real_value"])
    pred_col = first_existing_column(table_columns, ["saleprice_pred", "predicted_value", "prediction"])
    abs_error_col = first_existing_column(table_columns, ["abs_error"])
    fold_col = first_existing_column(table_columns, ["fold"])

    required = [run_id_col, house_id_col, actual_col, pred_col, abs_error_col, fold_col]
    if any(c is None for c in required):
        raise Exception(
            f"Impossible de mapper correctement la table {PREDICTIONS_TABLE}. "
            f"Colonnes trouvées: {table_columns}"
        )

    rows = pred_df.select(
        F.col(ID_COL).alias("house_id"),
        F.col(TARGET_COL).cast("double").alias("actual_value"),
        F.col("prediction").cast("double").alias("predicted_value"),
        F.abs(F.col(TARGET_COL).cast("double") - F.col("prediction").cast("double")).alias("abs_error")
    ).collect()

    prepared_rows = []
    for r in rows:
        prepared_rows.append({
            run_id_col: int(model_run_id),
            house_id_col: int(r["house_id"]),
            actual_col: float(r["actual_value"]),
            pred_col: float(r["predicted_value"]),
            abs_error_col: float(r["abs_error"]),
            fold_col: int(FOLD_VALUE),
        })

    return prepared_rows


def insert_predictions(pred_df, model_run_id):
    table_columns = get_table_columns(PREDICTIONS_TABLE)
    rows = build_prediction_rows(pred_df, model_run_id, table_columns)

    if not rows:
        print("[WARN] Aucune prédiction à insérer")
        return

    insert_columns = list(rows[0].keys())
    placeholders = ", ".join(["?"] * len(insert_columns))
    columns_sql = ", ".join(insert_columns)

    sql = f"INSERT INTO public.{PREDICTIONS_TABLE} ({columns_sql}) VALUES ({placeholders})"

    conn = get_jdbc_connection()
    try:
        pstmt = conn.prepareStatement(sql)

        batch_size = 0
        for row in rows:
            for idx, col in enumerate(insert_columns, start=1):
                val = row[col]
                if isinstance(val, float):
                    pstmt.setDouble(idx, val)
                elif isinstance(val, int):
                    pstmt.setInt(idx, val)
                else:
                    pstmt.setString(idx, str(val))

            pstmt.addBatch()
            batch_size += 1

            if batch_size >= 1000:
                pstmt.executeBatch()
                batch_size = 0

        if batch_size > 0:
            pstmt.executeBatch()

        pstmt.close()
    finally:
        conn.close()


def compute_metrics(pred_df, label_col=TARGET_COL):
    evaluator_rmse = RegressionEvaluator(labelCol=label_col, predictionCol="prediction", metricName="rmse")
    evaluator_mae = RegressionEvaluator(labelCol=label_col, predictionCol="prediction", metricName="mae")
    evaluator_r2 = RegressionEvaluator(labelCol=label_col, predictionCol="prediction", metricName="r2")

    return {
        "rmse": float(evaluator_rmse.evaluate(pred_df)),
        "mae": float(evaluator_mae.evaluate(pred_df)),
        "r2": float(evaluator_r2.evaluate(pred_df))
    }


# ============================================================
# 1) LECTURE DEPUIS HDFS
# ============================================================
print("[INFO] Lecture du dataset depuis HDFS...")
df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(HDFS_INPUT_PATH)
)

print("[INFO] Schéma original du dataset :")
df.printSchema()

for old_col in df.columns:
    new_col = sanitize_column_name(old_col)
    if old_col != new_col:
        df = df.withColumnRenamed(old_col, new_col)

print("[INFO] Schéma après sanitation :")
df.printSchema()

SANITIZED_ID_COL = sanitize_column_name(ID_COL)
SANITIZED_TARGET_COL = sanitize_column_name(TARGET_COL)

if SANITIZED_ID_COL not in df.columns:
    raise Exception(f"Colonne obligatoire absente après sanitation: {SANITIZED_ID_COL}")

if SANITIZED_TARGET_COL not in df.columns:
    raise Exception(f"Colonne cible absente après sanitation: {SANITIZED_TARGET_COL}")

df = df.dropna(subset=[SANITIZED_ID_COL, SANITIZED_TARGET_COL])

numeric_types = {"int", "bigint", "double", "float", "decimal", "smallint", "tinyint", "long", "short"}
usable_cols = []

for field in df.schema.fields:
    dtype = field.dataType.simpleString().lower()
    if field.name in [SANITIZED_ID_COL, SANITIZED_TARGET_COL]:
        usable_cols.append(field.name)
    elif any(dtype.startswith(t) for t in numeric_types):
        usable_cols.append(field.name)

df = df.select(*[F.col(c) for c in usable_cols])

feature_cols = [c for c in df.columns if c not in [SANITIZED_ID_COL, SANITIZED_TARGET_COL]]

if not feature_cols:
    raise Exception("Aucune feature exploitable trouvée après filtrage.")

print(f"[INFO] Nombre de features: {len(feature_cols)}")

assembler = VectorAssembler(
    inputCols=feature_cols,
    outputCol="features",
    handleInvalid="skip"
)

data = assembler.transform(df).select(
    F.col(SANITIZED_ID_COL).alias(ID_COL),
    F.col(SANITIZED_TARGET_COL).alias(TARGET_COL),
    "features"
)

# ============================================================
# 2) TRAIN / TEST SPLIT
# ============================================================
train_df, test_df = data.randomSplit([0.8, 0.2], seed=SEED)
train_df = train_df.cache()
test_df = test_df.cache()

train_count = train_df.count()
test_count = test_df.count()

print(f"[INFO] Train rows: {train_count}")
print(f"[INFO] Test rows : {test_count}")

if train_count == 0 or test_count == 0:
    raise Exception("Le split train/test a produit un ensemble vide.")

# ============================================================
# 3) DÉFINITION DES 3 MODÈLES
# ============================================================
models = [
    (
        "Linear Regression",
        LinearRegression(
            featuresCol="features",
            labelCol=TARGET_COL,
            predictionCol="prediction",
            maxIter=100,
            regParam=0.0,
            elasticNetParam=0.0
        )
    ),
    (
        "Random Forest",
        RandomForestRegressor(
            featuresCol="features",
            labelCol=TARGET_COL,
            predictionCol="prediction",
            numTrees=100,
            maxDepth=10,
            seed=SEED
        )
    ),
    (
        "Gradient Boosting Regressor",
        GBTRegressor(
            featuresCol="features",
            labelCol=TARGET_COL,
            predictionCol="prediction",
            maxIter=100,
            maxDepth=5,
            seed=SEED
        )
    )
]

# ============================================================
# 4) ENTRAÎNEMENT + MÉTRIQUES + INSERTIONS POSTGRES
# ============================================================
summary_rows = []

for model_name, estimator in models:
    print(f"\n[INFO] ===== Modèle: {model_name} =====")

    fitted_model = estimator.fit(train_df)

    train_pred = fitted_model.transform(train_df).select(ID_COL, TARGET_COL, "prediction")
    test_pred = fitted_model.transform(test_df).select(ID_COL, TARGET_COL, "prediction")

    train_metrics = compute_metrics(train_pred)
    test_metrics = compute_metrics(test_pred)

    print(
        f"[INFO] {model_name} | "
        f"Train -> RMSE={train_metrics['rmse']:.4f}, MAE={train_metrics['mae']:.4f}, R2={train_metrics['r2']:.4f} | "
        f"Test -> RMSE={test_metrics['rmse']:.4f}, MAE={test_metrics['mae']:.4f}, R2={test_metrics['r2']:.4f}"
    )

    metrics_dict = {
        "model_name": model_name,
        "rmse_cv": train_metrics["rmse"],
        "mae_cv": train_metrics["mae"],
        "r2_cv": train_metrics["r2"],
        "rmse_test": test_metrics["rmse"],
        "mae_test": test_metrics["mae"],
        "r2_test": test_metrics["r2"],
    }

    run_id = insert_model_run(metrics_dict)
    print(f"[INFO] model_runs inséré pour {model_name}, run_id={run_id}")

    insert_predictions(test_pred, run_id)
    print(f"[INFO] predictions insérées pour {model_name}")

    summary_rows.append({
        "model_name": model_name,
        "rmse_cv": train_metrics["rmse"],
        "mae_cv": train_metrics["mae"],
        "r2_cv": train_metrics["r2"],
        "rmse_test": test_metrics["rmse"],
        "mae_test": test_metrics["mae"],
        "r2_test": test_metrics["r2"]
    })

print("\n[INFO] ===== RÉCAP =====")
for row in summary_rows:
    print(row)

print("\n[INFO] Pipeline Spark -> PostgreSQL terminé avec succès.")
spark.stop()