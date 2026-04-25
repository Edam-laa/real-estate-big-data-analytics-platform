from __future__ import annotations

import re
import sys
import unicodedata
from difflib import get_close_matches
from pathlib import Path

import numpy as np
import pandas as pd


RAW_FILENAME = "AmesHousing.tsv"
PREPARED_FILENAME = "ames_housing_prepared.csv"
TARGET_COLUMN = "SalePrice"


def project_root() -> Path:
    """Retourne la racine du mini-projet."""
    return Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    """Retourne le dossier data et le crÃ©e si besoin."""
    directory = project_root() / "data"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def normalize_name(name: str) -> str:
    """Normalise un nom de colonne pour faciliter les correspondances proches."""
    normalized = unicodedata.normalize("NFKD", str(name))
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_name.lower())


def resolve_column_name(columns: pd.Index, expected_name: str, required: bool = True) -> str | None:
    """
    RÃ©sout un nom de colonne mÃªme s'il contient des espaces, variantes mineures
    ou caractÃ¨res spÃ©ciaux.
    """
    if expected_name in columns:
        return expected_name

    normalized_lookup = {normalize_name(column): column for column in columns}
    normalized_expected = normalize_name(expected_name)

    if normalized_expected in normalized_lookup:
        return normalized_lookup[normalized_expected]

    matches = get_close_matches(normalized_expected, list(normalized_lookup.keys()), n=1, cutoff=0.75)
    if matches:
        return normalized_lookup[matches[0]]

    if required:
        available_preview = ", ".join(map(str, list(columns[:10])))
        raise KeyError(
            f"Colonne introuvable: '{expected_name}'. "
            f"Exemples de colonnes disponibles: {available_preview}"
        )
    return None


def require_columns(columns: pd.Index, expected_names: list[str]) -> dict[str, str]:
    """Valide et rÃ©sout un ensemble de colonnes nÃ©cessaires."""
    return {name: resolve_column_name(columns, name, required=True) for name in expected_names}


def load_data(file_path: Path) -> pd.DataFrame:
    """Charge le dataset brut Ames Housing."""
    if not file_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {file_path}")

    dataframe = pd.read_csv(file_path, sep="\t")
    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    return dataframe


def clean_text_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Supprime les espaces inutiles dans les colonnes texte."""
    cleaned = dataframe.copy()
    text_columns = cleaned.select_dtypes(include=["object"]).columns

    for column in text_columns:
        cleaned[column] = cleaned[column].apply(lambda value: value.strip() if isinstance(value, str) else value)
        cleaned[column] = cleaned[column].replace("", np.nan)

    return cleaned


def remove_outliers(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Supprime les maisons avec une surface habitable excessive."""
    gr_liv_area_column = resolve_column_name(dataframe.columns, "Gr Liv Area")
    return dataframe.loc[dataframe[gr_liv_area_column] <= 4000].copy()


def fill_absence_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Remplit les valeurs manquantes liÃ©es Ã  une absence d'Ã©quipement.
    Les colonnes qualitatives reÃ§oivent 'None' et les colonnes quantitatives reÃ§oivent 0.
    """
    filled = dataframe.copy()

    categorical_absence_candidates = [
        "Alley",
        "Fireplace Qu",
        "Pool QC",
        "Fence",
        "Misc Feature",
        "Garage Type",
        "Garage Finish",
        "Garage Qual",
        "Garage Cond",
        "Bsmt Qual",
        "Bsmt Cond",
        "Bsmt Exposure",
        "BsmtFin Type 1",
        "BsmtFin Type 2",
    ]

    numeric_absence_candidates = [
        "Garage Yr Blt",
        "Garage Cars",
        "Garage Area",
        "BsmtFin SF 1",
        "BsmtFin SF 2",
        "Bsmt Unf SF",
        "Total Bsmt SF",
        "Bsmt Full Bath",
        "Bsmt Half Bath",
    ]

    for expected_name in categorical_absence_candidates:
        actual_name = resolve_column_name(filled.columns, expected_name, required=False)
        if actual_name is not None:
            filled[actual_name] = filled[actual_name].fillna("None")

    for expected_name in numeric_absence_candidates:
        actual_name = resolve_column_name(filled.columns, expected_name, required=False)
        if actual_name is not None:
            filled[actual_name] = filled[actual_name].fillna(0)

    return filled


def impute_lot_frontage(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Impute Lot Frontage par la mÃ©diane du quartier, sinon la mÃ©diane globale."""
    imputed = dataframe.copy()
    lot_frontage_column = resolve_column_name(imputed.columns, "Lot Frontage")
    neighborhood_column = resolve_column_name(imputed.columns, "Neighborhood")

    neighborhood_medians = imputed.groupby(neighborhood_column)[lot_frontage_column].transform("median")
    global_median = imputed[lot_frontage_column].median()

    imputed[lot_frontage_column] = imputed[lot_frontage_column].fillna(neighborhood_medians)
    imputed[lot_frontage_column] = imputed[lot_frontage_column].fillna(global_median)

    return imputed


def impute_remaining_missing_values(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Impute les valeurs manquantes restantes de faÃ§on simple et robuste."""
    imputed = dataframe.copy()

    if TARGET_COLUMN not in imputed.columns:
        raise KeyError(f"La cible '{TARGET_COLUMN}' est absente du dataset.")

    numeric_columns = imputed.select_dtypes(include=[np.number]).columns.tolist()
    numeric_feature_columns = [column for column in numeric_columns if column != TARGET_COLUMN]

    for column in numeric_feature_columns:
        if imputed[column].isna().any():
            imputed[column] = imputed[column].fillna(imputed[column].median())

    categorical_columns = imputed.select_dtypes(include=["object"]).columns
    for column in categorical_columns:
        if imputed[column].isna().any():
            imputed[column] = imputed[column].fillna("Missing")

    return imputed


def clean_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """EnchaÃ®ne les Ã©tapes principales de nettoyage."""
    required_columns = [
        TARGET_COLUMN,
        "Gr Liv Area",
        "Lot Frontage",
        "Neighborhood",
    ]
    require_columns(dataframe.columns, required_columns)

    cleaned = clean_text_columns(dataframe)
    cleaned = remove_outliers(cleaned)
    cleaned = fill_absence_columns(cleaned)
    cleaned = impute_lot_frontage(cleaned)
    cleaned = impute_remaining_missing_values(cleaned)

    if cleaned[TARGET_COLUMN].isna().any():
        raise ValueError("La cible 'SalePrice' contient des valeurs manquantes aprÃ¨s nettoyage.")

    return cleaned


def engineer_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    """CrÃ©e des variables dÃ©rivÃ©es utiles pour la modÃ©lisation."""
    engineered = dataframe.copy()
    columns = require_columns(
        engineered.columns,
        [
            "Yr Sold",
            "Year Built",
            "Year Remod/Add",
            "Full Bath",
            "Half Bath",
            "Bsmt Full Bath",
            "Bsmt Half Bath",
            "Open Porch SF",
            "Enclosed Porch",
            "3Ssn Porch",
            "Screen Porch",
            "Garage Area",
            "Fireplaces",
            "Pool Area",
            "Total Bsmt SF",
            "1st Flr SF",
            "2nd Flr SF",
        ],
    )

    yr_sold = engineered[columns["Yr Sold"]]
    year_built = engineered[columns["Year Built"]]
    year_remod = engineered[columns["Year Remod/Add"]]

    engineered["HouseAge"] = (yr_sold - year_built).clip(lower=0)
    engineered["RemodAge"] = (yr_sold - year_remod).clip(lower=0)
    engineered["TotalBath"] = (
        engineered[columns["Full Bath"]]
        + 0.5 * engineered[columns["Half Bath"]]
        + engineered[columns["Bsmt Full Bath"]]
        + 0.5 * engineered[columns["Bsmt Half Bath"]]
    )
    engineered["TotalPorchSF"] = (
        engineered[columns["Open Porch SF"]]
        + engineered[columns["Enclosed Porch"]]
        + engineered[columns["3Ssn Porch"]]
        + engineered[columns["Screen Porch"]]
    )
    engineered["HasGarage"] = (engineered[columns["Garage Area"]] > 0).astype(int)
    engineered["HasFireplace"] = (engineered[columns["Fireplaces"]] > 0).astype(int)
    engineered["HasPool"] = (engineered[columns["Pool Area"]] > 0).astype(int)
    engineered["TotalSF"] = (
        engineered[columns["Total Bsmt SF"]]
        + engineered[columns["1st Flr SF"]]
        + engineered[columns["2nd Flr SF"]]
    )

    return engineered


def drop_unused_identifiers(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Supprime les colonnes d'identification inutiles pour la prÃ©diction."""
    pruned = dataframe.copy()

    for expected_name in ["Order", "PID"]:
        actual_name = resolve_column_name(pruned.columns, expected_name, required=False)
        if actual_name is not None:
            pruned = pruned.drop(columns=actual_name)

    return pruned


def encode_features(dataframe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """Encode les variables catÃ©gorielles et sÃ©pare X et y."""
    if TARGET_COLUMN not in dataframe.columns:
        raise KeyError(f"La cible '{TARGET_COLUMN}' est absente du dataset.")

    y = dataframe[TARGET_COLUMN].copy()
    house_id = dataframe["house_id"].copy()
    X = dataframe.drop(columns=[TARGET_COLUMN, "house_id"])
    X_encoded = pd.get_dummies(X, drop_first=True, dtype=int)
    prepared = pd.concat([house_id, X_encoded, y], axis=1)

    return prepared, X_encoded, y


def save_prepared_data(prepared_dataframe: pd.DataFrame, output_path: Path) -> Path:
    """Sauvegarde le dataset prÃ©parÃ© pour la modÃ©lisation."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepared_dataframe.to_csv(output_path, index=False)
    return output_path


def print_summary(
    rows_before: int,
    rows_after: int,
    columns_before: int,
    columns_after: int,
    remaining_missing_values: int,
    output_path: Path,
) -> None:
    """Affiche un rÃ©sumÃ© synthÃ©tique du traitement."""
    print("=== PrÃ©paration du dataset Ames Housing ===")
    print(f"Lignes avant nettoyage : {rows_before}")
    print(f"Lignes aprÃ¨s nettoyage : {rows_after}")
    print(f"Colonnes avant encodage : {columns_before}")
    print(f"Colonnes aprÃ¨s encodage : {columns_after}")
    print(f"Valeurs manquantes restantes : {remaining_missing_values}")
    print(f"Fichier exportÃ© : {output_path.resolve()}")


def main() -> int:
    raw_path = data_dir() / RAW_FILENAME
    fallback_raw_path = project_root() / RAW_FILENAME
    prepared_path = data_dir() / PREPARED_FILENAME

    if not raw_path.exists() and fallback_raw_path.exists():
        raw_path = fallback_raw_path

    try:
        raw_dataframe = load_data(raw_path)
        rows_before, columns_before = raw_dataframe.shape

        cleaned_dataframe = clean_data(raw_dataframe)
        prepared_base_dataframe = engineer_features(cleaned_dataframe)
        prepared_base_dataframe = drop_unused_identifiers(prepared_base_dataframe)
        prepared_base_dataframe = prepared_base_dataframe.reset_index(drop=True)
        prepared_base_dataframe["house_id"] = prepared_base_dataframe.index + 1

        prepared_dataframe, _, _ = encode_features(prepared_base_dataframe)
        saved_path = save_prepared_data(prepared_dataframe, prepared_path)

        print_summary(
            rows_before=rows_before,
            rows_after=len(prepared_base_dataframe),
            columns_before=columns_before,
            columns_after=prepared_dataframe.shape[1],
            remaining_missing_values=int(prepared_dataframe.isna().sum().sum()),
            output_path=saved_path,
        )
        return 0

    except (FileNotFoundError, KeyError, ValueError) as error:
        print(f"Erreur: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
