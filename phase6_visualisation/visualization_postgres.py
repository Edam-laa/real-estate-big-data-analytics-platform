from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pg8000


# ============================================================
# CONFIGURATION
# ============================================================

# IMPORTANT:
# - This script reads DIRECTLY from PostgreSQL.
# - In your current setup, Docker PostgreSQL is exposed on port 5433.
# - If you changed the port, update DB_PORT below.

DB_HOST = os.getenv("AMES_DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("AMES_DB_PORT", "5433"))
DB_NAME = os.getenv("AMES_DB_NAME", "ames_platform")
DB_USER = os.getenv("AMES_DB_USER", "ames_user")
DB_PASSWORD = os.getenv("AMES_DB_PASSWORD", "")  # keep empty if pg_hba.conf uses trust

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Visual style
plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams["figure.figsize"] = (12, 6)
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["xtick.labelsize"] = 9
plt.rcParams["ytick.labelsize"] = 9
plt.rcParams["legend.fontsize"] = 9

COLORS = {
    "blue": "#2563EB",
    "cyan": "#06B6D4",
    "green": "#10B981",
    "amber": "#F59E0B",
    "red": "#EF4444",
    "violet": "#8B5CF6",
    "slate": "#475569",
    "pink": "#EC4899",
    "teal": "#14B8A6",
}


# ============================================================
# DATABASE HELPERS
# ============================================================

def connect_db() -> pg8000.dbapi.Connection:
    print("[INFO] Connecting directly to PostgreSQL...")
    conn = pg8000.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=str(DB_PASSWORD),
        timeout=10,
    )
    print("[OK] PostgreSQL connection successful.")
    return conn


def read_table(conn: pg8000.dbapi.Connection, table_name: str) -> pd.DataFrame:
    sql = f"SELECT * FROM public.{table_name}"
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [desc[0] for desc in cur.description]
    df = pd.DataFrame(rows, columns=cols)
    df.columns = [c.strip().lower() for c in df.columns]
    print(f"[OK] Loaded {table_name}: {df.shape}")
    return df


# ============================================================
# DATA HELPERS
# ============================================================

def pick_existing(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    cols = set(df.columns)
    for c in candidates:
        if c in cols:
            return c
    return None


def to_numeric(df: pd.DataFrame, columns: Iterable[Optional[str]]) -> None:
    for col in columns:
        if col and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")


def save_fig(filename: str) -> None:
    path = OUTPUT_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"[SAVED] {path.name}")


def safe_group_mean(df: pd.DataFrame, by: str, value: str) -> pd.Series:
    tmp = df[[by, value]].dropna().copy()
    return tmp.groupby(by)[value].mean()


def write_text_report(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[SAVED] {path.name}")


# ============================================================
# LOAD DATA
# ============================================================

conn = connect_db()

houses_core = read_table(conn, "houses_core")
houses_location = read_table(conn, "houses_location")
houses_structure = read_table(conn, "houses_structure")
houses_sale = read_table(conn, "houses_sale")
model_runs = read_table(conn, "model_runs")
predictions = read_table(conn, "predictions")

conn.close()
print("[INFO] Connection closed.")


# ============================================================
# BUILD MASTER DATASET
# ============================================================

if "house_id" not in houses_core.columns:
    raise ValueError("house_id not found in houses_core")

master = houses_core.copy()

for df in [houses_location, houses_structure, houses_sale]:
    if "house_id" not in df.columns:
        raise ValueError("house_id missing in one of the house tables")
    overlap = [c for c in df.columns if c != "house_id" and c in master.columns]
    df = df.rename(columns={c: f"{c}_dup" for c in overlap})
    master = master.merge(df, on="house_id", how="left")

sale_price_col = pick_existing(master, ["sale_price", "saleprice"])
neighborhood_col = pick_existing(master, ["neighborhood"])
gr_liv_area_col = pick_existing(master, ["gr_liv_area", "grlivarea"])
overall_qual_col = pick_existing(master, ["overall_qual", "overallqual"])
year_built_col = pick_existing(master, ["year_built", "yearbuilt"])
full_bath_col = pick_existing(master, ["full_bath", "fullbath"])
half_bath_col = pick_existing(master, ["half_bath", "halfbath"])
fireplaces_col = pick_existing(master, ["fireplaces", "fireplace"])
garage_cars_col = pick_existing(master, ["garage_cars", "garagecars"])
pool_area_col = pick_existing(master, ["pool_area", "poolarea"])
total_bsmt_sf_col = pick_existing(master, ["total_bsmt_sf", "totalbsmtsf"])
first_flr_sf_col = pick_existing(master, ["first_flr_sf", "1st_flr_sf", "firstflrsf"])
second_flr_sf_col = pick_existing(master, ["second_flr_sf", "2nd_flr_sf", "secondflrsf"])
ms_zoning_col = pick_existing(master, ["ms_zoning", "mszoning"])

to_numeric(
    master,
    [
        sale_price_col, gr_liv_area_col, overall_qual_col, year_built_col,
        full_bath_col, half_bath_col, fireplaces_col, garage_cars_col,
        pool_area_col, total_bsmt_sf_col, first_flr_sf_col, second_flr_sf_col,
    ],
)

if year_built_col:
    master["house_age"] = 2010 - master[year_built_col]

master["totalsf"] = (
    (master[total_bsmt_sf_col].fillna(0) if total_bsmt_sf_col else 0)
    + (master[first_flr_sf_col].fillna(0) if first_flr_sf_col else 0)
    + (master[second_flr_sf_col].fillna(0) if second_flr_sf_col else 0)
)

master["totalbath"] = (
    (master[full_bath_col].fillna(0) if full_bath_col else 0)
    + 0.5 * (master[half_bath_col].fillna(0) if half_bath_col else 0)
)

if garage_cars_col:
    master["has_garage"] = (master[garage_cars_col].fillna(0) > 0).astype(int)

if fireplaces_col:
    master["has_fireplace"] = (master[fireplaces_col].fillna(0) > 0).astype(int)

if pool_area_col:
    master["has_pool"] = (master[pool_area_col].fillna(0) > 0).astype(int)
else:
    master["has_pool"] = 0

analytics = master.copy()
if sale_price_col:
    analytics = analytics[analytics[sale_price_col].notna()].copy()

# Save enriched data snapshot
analytics.to_csv(OUTPUT_DIR / "houses_master_enriched.csv", index=False)


# ============================================================
# BUILD PREDICTIONS ENRICHED
# ============================================================

pred_run_col = pick_existing(predictions, ["run_id", "model_run_id"])
run_id_col = pick_existing(model_runs, ["run_id"])
model_name_col = pick_existing(model_runs, ["model_name"])

real_col = pick_existing(predictions, ["saleprice_real", "sale_price_real", "real_price", "actual_price"])
pred_col = pick_existing(predictions, ["saleprice_pred", "sale_price_pred", "predicted_price", "prediction"])
abs_error_col = pick_existing(predictions, ["abs_error", "absolute_error"])

to_numeric(predictions, [pred_run_col, real_col, pred_col, abs_error_col])
to_numeric(model_runs, ["run_id", "rmse_cv", "mae_cv", "r2_cv", "rmse_test", "mae_test", "r2_test"])

if abs_error_col is None and real_col and pred_col:
    predictions["abs_error"] = (predictions[real_col] - predictions[pred_col]).abs()
    abs_error_col = "abs_error"

if pred_run_col and run_id_col:
    pred_enriched = predictions.merge(
        model_runs,
        left_on=pred_run_col,
        right_on=run_id_col,
        how="left",
        suffixes=("", "_run"),
    )
else:
    pred_enriched = predictions.copy()

if "house_id" in pred_enriched.columns:
    keep_cols = ["house_id"]
    for col in [neighborhood_col, sale_price_col, gr_liv_area_col, overall_qual_col, "totalsf", "house_age", "totalbath"]:
        if col and col not in keep_cols and col in analytics.columns:
            keep_cols.append(col)
    pred_enriched = pred_enriched.merge(analytics[keep_cols], on="house_id", how="left")

pred_enriched.to_csv(OUTPUT_DIR / "predictions_enriched.csv", index=False)
model_runs.to_csv(OUTPUT_DIR / "model_runs_snapshot.csv", index=False)


# ============================================================
# KPI SUMMARY
# ============================================================

summary_lines = []
if sale_price_col:
    mean_price = analytics[sale_price_col].mean()
    median_price = analytics[sale_price_col].median()
    min_price = analytics[sale_price_col].min()
    max_price = analytics[sale_price_col].max()
    total_houses = int(analytics["house_id"].nunique())

    summary_lines.extend(
        [
            "AMES HOUSING ANALYTICS PLATFORM - KPI SUMMARY",
            "-" * 50,
            f"Total houses: {total_houses}",
            f"Average price: {mean_price:,.2f}",
            f"Median price: {median_price:,.2f}",
            f"Minimum price: {min_price:,.2f}",
            f"Maximum price: {max_price:,.2f}",
        ]
    )

write_text_report(OUTPUT_DIR / "kpi_summary.txt", summary_lines)


# ============================================================
# 1) MARKET ANALYSIS
# ============================================================

if sale_price_col:
    plt.figure(figsize=(12, 6))
    plt.hist(analytics[sale_price_col].dropna(), bins=30, color=COLORS["blue"], edgecolor="white", alpha=0.85)
    plt.axvline(analytics[sale_price_col].mean(), color=COLORS["red"], linestyle="--", linewidth=2, label="Mean price")
    plt.axvline(analytics[sale_price_col].median(), color=COLORS["green"], linestyle="-.", linewidth=2, label="Median price")
    plt.title("01 - Distribution des prix immobiliers")
    plt.xlabel("Sale Price")
    plt.ylabel("Nombre de maisons")
    plt.legend()
    save_fig("01_distribution_prix.png")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis("off")
    text = (
        f"Nombre de maisons : {total_houses:,}\n"
        f"Prix moyen : {mean_price:,.0f}\n"
        f"Prix médian : {median_price:,.0f}\n"
        f"Prix minimum : {min_price:,.0f}\n"
        f"Prix maximum : {max_price:,.0f}"
    )
    ax.text(0.03, 0.5, text, fontsize=16, va="center", color=COLORS["slate"])
    plt.title("02 - Indicateurs clés du marché", color=COLORS["violet"])
    save_fig("02_kpis_marche.png")

if neighborhood_col and sale_price_col:
    s = safe_group_mean(analytics, neighborhood_col, sale_price_col).sort_values(ascending=False).head(15).sort_values()
    plt.figure(figsize=(12, 7))
    plt.barh(s.index.astype(str), s.values, color=plt.cm.Blues(np.linspace(0.45, 0.95, len(s))))
    plt.title("03 - Prix moyen par quartier (Top 15)")
    plt.xlabel("Prix moyen")
    plt.ylabel("Neighborhood")
    save_fig("03_prix_moyen_par_quartier.png")

if gr_liv_area_col and sale_price_col:
    plt.figure(figsize=(12, 6))
    plt.scatter(analytics[gr_liv_area_col], analytics[sale_price_col], alpha=0.55, color=COLORS["cyan"], edgecolors="none", label="Houses")
    plt.title("04 - Surface habitable vs prix")
    plt.xlabel("Gr Liv Area")
    plt.ylabel("Sale Price")
    plt.legend()
    save_fig("04_surface_vs_prix.png")

if overall_qual_col and sale_price_col:
    s = safe_group_mean(analytics, overall_qual_col, sale_price_col).sort_index()
    plt.figure(figsize=(11, 6))
    plt.plot(s.index, s.values, marker="o", linewidth=2.5, color=COLORS["violet"], label="Average price")
    plt.fill_between(s.index, s.values, alpha=0.15, color=COLORS["violet"])
    plt.title("05 - Qualité générale vs prix moyen")
    plt.xlabel("Overall Qual")
    plt.ylabel("Prix moyen")
    plt.legend()
    save_fig("05_qualite_vs_prix.png")

if ms_zoning_col and sale_price_col:
    s = safe_group_mean(analytics, ms_zoning_col, sale_price_col).sort_values(ascending=False)
    plt.figure(figsize=(10, 5))
    plt.bar(s.index.astype(str), s.values, color=plt.cm.PuBuGn(np.linspace(0.35, 0.95, len(s))))
    plt.title("06 - Prix moyen par zone résidentielle")
    plt.xlabel("MS Zoning")
    plt.ylabel("Prix moyen")
    save_fig("06_prix_par_zone_residentielle.png")

if year_built_col and sale_price_col:
    yearly = analytics.groupby(year_built_col)[sale_price_col].mean().dropna().sort_index()
    plt.figure(figsize=(12, 6))
    plt.plot(yearly.index, yearly.values, color=COLORS["teal"], linewidth=2.2, label="Average price by year built")
    plt.title("07 - Prix moyen selon l'année de construction")
    plt.xlabel("Year Built")
    plt.ylabel("Prix moyen")
    plt.legend()
    save_fig("07_prix_par_annee_construction.png")


# ============================================================
# 2) PRICE DRIVERS / FACTORS
# ============================================================

if "totalsf" in analytics.columns and sale_price_col:
    plt.figure(figsize=(12, 6))
    plt.scatter(analytics["totalsf"], analytics[sale_price_col], alpha=0.5, color=COLORS["green"], label="Houses")
    plt.title("08 - TotalSF vs prix")
    plt.xlabel("TotalSF")
    plt.ylabel("Sale Price")
    plt.legend()
    save_fig("08_totalsf_vs_prix.png")

if "house_age" in analytics.columns and sale_price_col:
    plt.figure(figsize=(12, 6))
    plt.scatter(analytics["house_age"], analytics[sale_price_col], alpha=0.5, color=COLORS["amber"], label="Houses")
    plt.title("09 - HouseAge vs prix")
    plt.xlabel("House Age")
    plt.ylabel("Sale Price")
    plt.legend()
    save_fig("09_house_age_vs_prix.png")

if "totalbath" in analytics.columns and sale_price_col:
    tmp = analytics[["totalbath", sale_price_col]].dropna().copy()
    tmp["totalbath_round"] = tmp["totalbath"].round(1)
    groups = [g[sale_price_col].values for _, g in tmp.groupby("totalbath_round")]
    labels = [str(k) for k in sorted(tmp["totalbath_round"].unique())]
    if groups:
        plt.figure(figsize=(12, 6))
        plt.boxplot(groups, tick_labels=labels, patch_artist=True,
                    boxprops=dict(facecolor=COLORS["cyan"], alpha=0.5),
                    medianprops=dict(color=COLORS["red"], linewidth=2))
        plt.title("10 - Distribution du prix selon TotalBath")
        plt.xlabel("TotalBath")
        plt.ylabel("Sale Price")
        save_fig("10_totalbath_vs_prix_boxplot.png")

if "has_garage" in analytics.columns and sale_price_col:
    s = safe_group_mean(analytics, "has_garage", sale_price_col).sort_index()
    plt.figure(figsize=(8, 5))
    plt.bar(["No Garage", "Has Garage"], s.values, color=[COLORS["slate"], COLORS["blue"]])
    plt.title("11 - Effet du garage sur le prix moyen")
    plt.ylabel("Prix moyen")
    save_fig("11_effet_garage.png")

if "has_fireplace" in analytics.columns and sale_price_col:
    s = safe_group_mean(analytics, "has_fireplace", sale_price_col).sort_index()
    plt.figure(figsize=(8, 5))
    plt.bar(["No Fireplace", "Has Fireplace"], s.values, color=[COLORS["slate"], COLORS["red"]])
    plt.title("12 - Effet de la cheminée sur le prix moyen")
    plt.ylabel("Prix moyen")
    save_fig("12_effet_cheminee.png")

if "has_pool" in analytics.columns and sale_price_col:
    s = safe_group_mean(analytics, "has_pool", sale_price_col).sort_index()
    plt.figure(figsize=(8, 5))
    labels = ["No Pool", "Has Pool"]
    values = [s.get(0, np.nan), s.get(1, np.nan)]
    plt.bar(labels, values, color=[COLORS["slate"], COLORS["teal"]])
    plt.title("13 - Effet de la piscine sur le prix moyen")
    plt.ylabel("Prix moyen")
    save_fig("13_effet_piscine.png")

corr_candidates = [sale_price_col, gr_liv_area_col, overall_qual_col, "totalsf", "totalbath", "house_age", garage_cars_col]
corr_cols = [c for c in corr_candidates if c and c in analytics.columns]
if len(corr_cols) >= 3:
    corr = analytics[corr_cols].corr(numeric_only=True)
    plt.figure(figsize=(9, 7))
    plt.imshow(corr, cmap="coolwarm", aspect="auto", vmin=-1, vmax=1)
    plt.colorbar(label="Correlation")
    plt.xticks(range(len(corr.columns)), corr.columns, rotation=45, ha="right")
    plt.yticks(range(len(corr.index)), corr.index)
    plt.title("14 - Heatmap des corrélations")
    for i in range(len(corr.index)):
        for j in range(len(corr.columns)):
            plt.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", color="black", fontsize=8)
    save_fig("14_heatmap_correlations.png")

if overall_qual_col and sale_price_col:
    tmp = analytics[[overall_qual_col, sale_price_col]].dropna()
    groups = [g[sale_price_col].values for _, g in tmp.groupby(overall_qual_col)]
    labels = [str(k) for k in sorted(tmp[overall_qual_col].unique())]
    if groups:
        plt.figure(figsize=(12, 6))
        plt.boxplot(groups, tick_labels=labels, patch_artist=True,
                    boxprops=dict(facecolor=COLORS["violet"], alpha=0.4),
                    medianprops=dict(color=COLORS["red"], linewidth=2))
        plt.title("15 - Boxplot du prix par niveau de qualité")
        plt.xlabel("Overall Qual")
        plt.ylabel("Sale Price")
        save_fig("15_boxplot_qualite_prix.png")


# ============================================================
# 3) ML MODELS
# ============================================================

if model_name_col and not model_runs.empty:
    if "rmse_test" in model_runs.columns:
        tmp = model_runs[[model_name_col, "rmse_test"]].dropna().sort_values("rmse_test", ascending=True)
        plt.figure(figsize=(10, 5))
        plt.bar(tmp[model_name_col], tmp["rmse_test"], color=plt.cm.Oranges(np.linspace(0.45, 0.95, len(tmp))))
        plt.title("16 - RMSE test par modèle")
        plt.xlabel("Model")
        plt.ylabel("RMSE test")
        plt.xticks(rotation=20, ha="right")
        save_fig("16_rmse_test_par_modele.png")

    if "mae_test" in model_runs.columns:
        tmp = model_runs[[model_name_col, "mae_test"]].dropna().sort_values("mae_test", ascending=True)
        plt.figure(figsize=(10, 5))
        plt.bar(tmp[model_name_col], tmp["mae_test"], color=plt.cm.Greens(np.linspace(0.45, 0.95, len(tmp))))
        plt.title("17 - MAE test par modèle")
        plt.xlabel("Model")
        plt.ylabel("MAE test")
        plt.xticks(rotation=20, ha="right")
        save_fig("17_mae_test_par_modele.png")

    if "r2_test" in model_runs.columns:
        tmp = model_runs[[model_name_col, "r2_test"]].dropna().sort_values("r2_test", ascending=False)
        plt.figure(figsize=(10, 5))
        plt.bar(tmp[model_name_col], tmp["r2_test"], color=plt.cm.Purples(np.linspace(0.45, 0.95, len(tmp))))
        plt.title("18 - R² test par modèle")
        plt.xlabel("Model")
        plt.ylabel("R² test")
        plt.xticks(rotation=20, ha="right")
        save_fig("18_r2_test_par_modele.png")

    best_text = ["MEILLEUR MODELE", "-" * 30]
    if "rmse_test" in model_runs.columns and model_name_col:
        best_rmse = model_runs.loc[model_runs["rmse_test"].idxmin()]
        best_text.append(f"Best RMSE: {best_rmse[model_name_col]} ({best_rmse['rmse_test']:.4f})")
    if "mae_test" in model_runs.columns and model_name_col:
        best_mae = model_runs.loc[model_runs["mae_test"].idxmin()]
        best_text.append(f"Best MAE: {best_mae[model_name_col]} ({best_mae['mae_test']:.4f})")
    if "r2_test" in model_runs.columns and model_name_col:
        best_r2 = model_runs.loc[model_runs["r2_test"].idxmax()]
        best_text.append(f"Best R²: {best_r2[model_name_col]} ({best_r2['r2_test']:.4f})")

    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.axis("off")
    ax.text(0.03, 0.5, "\n".join(best_text), fontsize=14, va="center", color=COLORS["slate"])
    plt.title("19 - Synthèse du meilleur modèle", color=COLORS["pink"])
    save_fig("19_best_model_summary.png")


# ============================================================
# 4) PREDICTIONS / ERRORS
# ============================================================

real_col = pick_existing(pred_enriched, ["saleprice_real", "sale_price_real", "real_price", "actual_price"])
pred_col = pick_existing(pred_enriched, ["saleprice_pred", "sale_price_pred", "predicted_price", "prediction"])
abs_error_col = pick_existing(pred_enriched, ["abs_error", "absolute_error"])

to_numeric(pred_enriched, [real_col, pred_col, abs_error_col])

if real_col and pred_col:
    tmp = pred_enriched[[real_col, pred_col]].dropna()
    plt.figure(figsize=(12, 6))
    plt.scatter(tmp[real_col], tmp[pred_col], alpha=0.45, color=COLORS["blue"], label="Predictions")
    line_min = min(tmp[real_col].min(), tmp[pred_col].min())
    line_max = max(tmp[real_col].max(), tmp[pred_col].max())
    plt.plot([line_min, line_max], [line_min, line_max], color=COLORS["red"], linestyle="--", linewidth=2, label="Perfect fit")
    plt.title("20 - Réel vs prédit")
    plt.xlabel("Prix réel")
    plt.ylabel("Prix prédit")
    plt.legend()
    save_fig("20_reel_vs_predit.png")

if abs_error_col:
    tmp = pred_enriched[abs_error_col].dropna()
    plt.figure(figsize=(12, 6))
    plt.hist(tmp, bins=30, color=COLORS["amber"], edgecolor="white")
    plt.title("21 - Distribution des erreurs absolues")
    plt.xlabel("Abs Error")
    plt.ylabel("Nombre de prédictions")
    save_fig("21_distribution_abs_error.png")

    if "house_id" in pred_enriched.columns:
        top_errors = pred_enriched[["house_id", abs_error_col]].dropna().sort_values(abs_error_col, ascending=False).head(20)
        top_errors.to_csv(OUTPUT_DIR / "top_20_errors.csv", index=False)

        plt.figure(figsize=(12, 7))
        plt.barh(top_errors["house_id"].astype(str), top_errors[abs_error_col], color=plt.cm.Reds(np.linspace(0.4, 0.95, len(top_errors))))
        plt.title("22 - Top 20 plus fortes erreurs")
        plt.xlabel("Abs Error")
        plt.ylabel("House ID")
        plt.gca().invert_yaxis()
        save_fig("22_top_20_erreurs.png")

    if neighborhood_col and neighborhood_col in pred_enriched.columns:
        s = pred_enriched[[neighborhood_col, abs_error_col]].dropna().groupby(neighborhood_col)[abs_error_col].mean().sort_values(ascending=False).head(15).sort_values()
        plt.figure(figsize=(12, 7))
        plt.barh(s.index.astype(str), s.values, color=plt.cm.magma(np.linspace(0.25, 0.85, len(s))))
        plt.title("23 - Erreur moyenne par quartier (Top 15)")
        plt.xlabel("Abs Error moyen")
        plt.ylabel("Neighborhood")
        save_fig("23_erreur_moyenne_par_quartier.png")

if real_col and abs_error_col:
    tmp = pred_enriched[[real_col, abs_error_col]].dropna().copy()
    tmp["price_bucket"] = pd.cut(
        tmp[real_col],
        bins=[0, 100000, 150000, 200000, 300000, 500000, np.inf],
        labels=["<100k", "100k-150k", "150k-200k", "200k-300k", "300k-500k", ">500k"],
    )
    s = tmp.groupby("price_bucket", observed=False)[abs_error_col].mean()
    plt.figure(figsize=(10, 5))
    plt.bar(s.index.astype(str), s.values, color=plt.cm.cividis(np.linspace(0.25, 0.85, len(s))))
    plt.title("24 - Erreur moyenne selon la gamme de prix")
    plt.xlabel("Price bucket")
    plt.ylabel("Abs Error moyen")
    save_fig("24_erreur_par_gamme_prix.png")

if real_col and pred_col:
    tmp = pred_enriched[[real_col, pred_col]].dropna().copy()
    tmp["residual"] = tmp[real_col] - tmp[pred_col]
    plt.figure(figsize=(12, 6))
    plt.scatter(tmp[real_col], tmp["residual"], alpha=0.45, color=COLORS["pink"], label="Residuals")
    plt.axhline(0, color=COLORS["slate"], linestyle="--", linewidth=1.5)
    plt.title("25 - Résidus selon le prix réel")
    plt.xlabel("Prix réel")
    plt.ylabel("Résidu (réel - prédit)")
    plt.legend()
    save_fig("25_residus_vs_prix_reel.png")

    if "house_id" in pred_enriched.columns:
        tmp2 = pred_enriched.copy()
        tmp2["residual"] = tmp2[real_col] - tmp2[pred_col]
        tmp2 = tmp2.dropna(subset=["residual", "house_id"])
        tmp2.sort_values("residual", ascending=False).head(15).to_csv(
            OUTPUT_DIR / "top_15_underestimated.csv", index=False
        )
        tmp2.sort_values("residual", ascending=True).head(15).to_csv(
            OUTPUT_DIR / "top_15_overestimated.csv", index=False
        )


print("\n[INFO] All graphs generated successfully.")
print(f"[INFO] Output folder: {OUTPUT_DIR.resolve()}")
