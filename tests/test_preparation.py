"""Regression tests for stable Ames property identifiers and pipeline outputs."""
import importlib.util
from pathlib import Path

import pandas as pd
import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "phase2_docker" / "src" / "prepare_ames_housing.py"
spec = importlib.util.spec_from_file_location("prepare_ames_housing", SCRIPT)
preparation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparation)


def test_identifiers_survive_row_filtering():
    raw = pd.DataFrame({
        "Order": [1, 2, 3, 4],
        "Gr Liv Area": [1000, 4200, 2000, 3000],
    })
    filtered = preparation.remove_outliers(raw)
    with_ids = preparation.assign_stable_house_ids(filtered)
    assert with_ids["house_id"].tolist() == [1, 3, 4]


def test_duplicate_original_identifiers_rejected():
    with pytest.raises(ValueError, match="unique"):
        preparation.assign_stable_house_ids(pd.DataFrame({"Order": [1, 1, 3]}))


def test_missing_or_fractional_ids_rejected():
    for ids in ([1, None], [1, 1.5], [0, 2]):
        with pytest.raises(ValueError):
            preparation.assign_stable_house_ids(pd.DataFrame({"Order": ids}))


def test_real_dataset_preparation_matches_source_price_and_id():
    raw = preparation.load_data(ROOT / "phase2_docker" / "data" / "AmesHousing.tsv")
    cleaned = preparation.clean_data(raw)
    features = preparation.engineer_features(cleaned)
    features = preparation.assign_stable_house_ids(features)
    features = preparation.drop_unused_identifiers(features)
    prepared, _, _ = preparation.encode_features(features)

    assert len(prepared) == 2925
    assert prepared["house_id"].is_unique
    assert prepared.isna().sum().sum() == 0
    expected = raw.set_index("Order")["SalePrice"]
    assert prepared["SalePrice"].equals(prepared["house_id"].map(expected).reset_index(drop=True)) or all(
        abs(float(row.SalePrice) - float(expected.loc[int(row.house_id)])) < 0.001
        for row in prepared[["house_id", "SalePrice"]].itertuples(index=False)
    )
    assert prepared["house_id"].max() == 2930
    assert set([1499, 1761, 1768, 2181, 2182]).isdisjoint(set(prepared["house_id"]))
