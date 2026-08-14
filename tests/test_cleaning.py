import numpy as np
import pandas as pd
import pytest

from datalens.cleaning import (
    clean_data,
    coerce_types,
    handle_missing_values,
    remove_duplicates,
)


def test_remove_duplicates_drops_exact_dupes():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-02"],
            "category": ["coffee", "coffee", "tea"],
            "revenue": [5.0, 5.0, 3.0],
        }
    )
    result = remove_duplicates(df)
    assert len(result) == 2
    assert list(result["revenue"]) == [5.0, 3.0]


def test_remove_duplicates_keeps_distinct_rows():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    result = remove_duplicates(df)
    assert len(result) == 3


def test_handle_missing_values_drop_strategy():
    df = pd.DataFrame({"a": [1, np.nan, 3], "b": ["x", "y", None]})
    result = handle_missing_values(df, strategy="drop")
    assert len(result) == 1
    assert result.iloc[0]["a"] == 1


def test_handle_missing_values_fill_strategy_numeric_uses_mean():
    df = pd.DataFrame({"a": [2.0, np.nan, 4.0]})
    result = handle_missing_values(df, strategy="fill")
    assert result["a"].isna().sum() == 0
    assert result.loc[1, "a"] == pytest.approx(3.0)


def test_handle_missing_values_fill_strategy_all_nan_numeric_column():
    df = pd.DataFrame({"a": [np.nan, np.nan, np.nan]})
    result = handle_missing_values(df, strategy="fill")
    # mean() of an all-NaN column is itself NaN, so fillna(mean) used to be
    # a no-op — the column stayed full of NaNs. It should now fall back to 0.
    assert result["a"].isna().sum() == 0
    assert (result["a"] == 0).all()


def test_handle_missing_values_fill_strategy_categorical_defaults_to_unknown():
    df = pd.DataFrame({"category": ["coffee", None, "tea"]})
    result = handle_missing_values(df, strategy="fill")
    assert result.loc[1, "category"] == "unknown"


def test_handle_missing_values_fill_strategy_respects_explicit_fill_values():
    df = pd.DataFrame({"store": ["Downtown", None]})
    result = handle_missing_values(df, strategy="fill", fill_values={"store": "Unspecified"})
    assert result.loc[1, "store"] == "Unspecified"


def test_handle_missing_values_invalid_strategy_raises():
    df = pd.DataFrame({"a": [1, 2]})
    with pytest.raises(ValueError):
        handle_missing_values(df, strategy="nonsense")


def test_coerce_types_parses_date_and_numeric_columns():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "not-a-date"],
            "quantity": ["3", "oops"],
            "revenue": ["9.5", "10.0"],
        }
    )
    result = coerce_types(df)
    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert pd.isna(result["date"].iloc[1])
    assert pd.api.types.is_numeric_dtype(result["quantity"])
    assert pd.isna(result["quantity"].iloc[1])


def test_clean_data_pipeline_dedupes_and_drops_missing_by_default():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-02"],
            "category": ["coffee", "coffee", None],
            "quantity": [1, 1, 2],
            "unit_price": [2.5, 2.5, 3.0],
            "revenue": [2.5, 2.5, 6.0],
        }
    )
    result = clean_data(df)
    # The exact duplicate row is dropped, and the row with a missing
    # category is dropped under the default "drop" strategy.
    assert len(result) == 1
    assert result.iloc[0]["category"] == "coffee"


def test_clean_data_verbose_returns_tuple():
    df = pd.DataFrame(
        {
            # date as string -> will be coerced to datetime
            "date": ["2026-01-01", "2026-01-01", "2026-01-02"],
            # one missing category -> row will be dropped
            "category": ["coffee", "coffee", None],
            "quantity": [1, 1, 2],
            "unit_price": [2.5, 2.5, 3.0],
            "revenue": [2.5, 2.5, 6.0],
        }
    )
    result = clean_data(df, verbose=True)

    # Must return a 2-tuple
    assert isinstance(result, tuple)
    cleaned, details = result

    # The cleaned DataFrame is still correct
    assert len(cleaned) == 1

    # 1 exact duplicate row was removed (row 0 and row 1 are identical)
    assert details["duplicates_removed"] == 1

    # After deduplication, 1 row had a missing value (the None category)
    assert details["missing_handled_rows"] == 1
    assert "category" in details["missing_handled_cols"]

    # 'date' column was coerced from object/str to datetime
    assert "date" in details["coerced_dtypes"]


def test_clean_data_verbose_false_returns_dataframe():
    df = pd.DataFrame({"date": ["2026-01-01"], "quantity": [1], "revenue": [5.0], "unit_price": [5.0]})
    result = clean_data(df, verbose=False)

    # Default behavior: returns plain DataFrame, not a tuple
    assert isinstance(result, pd.DataFrame)
