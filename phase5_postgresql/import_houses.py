from typing import Any, Optional

import pandas as pd
import pg8000


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "database": "ames_platform",
    "user": "ames_user",
    "password": "ames_password",
}
TSV_PATH = "data/AmesHousing.tsv"


def clean_value(value: Any) -> Optional[Any]:
    if pd.isna(value):
        return None
    return value


def to_int(value: Any) -> Optional[int]:
    value = clean_value(value)
    if value is None:
        return None
    return int(value)


def to_float(value: Any) -> Optional[float]:
    value = clean_value(value)
    if value is None:
        return None
    return float(value)


def to_str(value: Any) -> Optional[str]:
    value = clean_value(value)
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def main() -> None:
    print(f"Lecture du fichier : {TSV_PATH}")
    df = pd.read_csv(TSV_PATH, sep="\t")

    df = df.reset_index(drop=True)
    df["house_id"] = df.index + 1

    print("Connexion a PostgreSQL...")
    conn = pg8000.connect(**DB_CONFIG)
    conn.autocommit = False

    try:
        cur = conn.cursor()

        core_rows = []
        location_rows = []
        structure_rows = []
        sale_rows = []

        for _, row in df.iterrows():
            house_id = to_int(row["house_id"])

            core_rows.append((
                house_id,
                to_str(row.get("Bldg Type")),
                to_str(row.get("House Style")),
                to_int(row.get("Overall Qual")),
                to_int(row.get("Overall Cond")),
                to_int(row.get("Year Built")),
                to_int(row.get("Year Remod/Add")),
                to_float(row.get("Gr Liv Area")),
                to_int(row.get("Bedroom AbvGr")),
                to_int(row.get("Kitchen AbvGr")),
                to_str(row.get("Kitchen Qual")),
                to_int(row.get("Full Bath")),
                to_int(row.get("Half Bath")),
                to_int(row.get("Fireplaces")),
                to_str(row.get("Central Air")),
            ))

            location_rows.append((
                house_id,
                to_str(row.get("MS Zoning")),
                to_float(row.get("Lot Frontage")),
                to_float(row.get("Lot Area")),
                to_str(row.get("Neighborhood")),
            ))

            structure_rows.append((
                house_id,
                to_float(row.get("Total Bsmt SF")),
                to_float(row.get("1st Flr SF")),
                to_float(row.get("2nd Flr SF")),
                to_float(row.get("Garage Cars")),
                to_float(row.get("Garage Area")),
                to_float(row.get("Wood Deck SF")),
                to_float(row.get("Open Porch SF")),
                to_float(row.get("Screen Porch")),
                to_float(row.get("Pool Area")),
            ))

            sale_rows.append((
                house_id,
                to_int(row.get("Mo Sold")),
                to_int(row.get("Yr Sold")),
                to_float(row.get("SalePrice")),
            ))

        cur.execute("DELETE FROM predictions;")
        cur.execute("DELETE FROM model_runs;")
        cur.execute("DELETE FROM houses_sale;")
        cur.execute("DELETE FROM houses_structure;")
        cur.execute("DELETE FROM houses_location;")
        cur.execute("DELETE FROM houses_core;")

        cur.executemany(
            """
            INSERT INTO houses_core (
                house_id, bldg_type, house_style, overall_qual, overall_cond,
                year_built, year_remod_add, gr_liv_area, bedroom_abvgr,
                kitchen_abvgr, kitchen_qual, full_bath, half_bath,
                fireplaces, central_air
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            core_rows,
        )

        cur.executemany(
            """
            INSERT INTO houses_location (
                house_id, ms_zoning, lot_frontage, lot_area, neighborhood
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            location_rows,
        )

        cur.executemany(
            """
            INSERT INTO houses_structure (
                house_id, total_bsmt_sf, first_flr_sf, second_flr_sf,
                garage_cars, garage_area, wood_deck_sf, open_porch_sf,
                screen_porch, pool_area
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            structure_rows,
        )

        cur.executemany(
            """
            INSERT INTO houses_sale (
                house_id, mo_sold, yr_sold, sale_price
            )
            VALUES (%s, %s, %s, %s)
            """,
            sale_rows,
        )

        conn.commit()
        print("Import termine avec succes.")
        print(f"Nombre de maisons importees : {len(df)}")

    except Exception as e:
        conn.rollback()
        print("Erreur pendant l'import :", e)
        raise
    finally:
        conn.close()
        print("Connexion fermee.")


if __name__ == "__main__":
    main()
