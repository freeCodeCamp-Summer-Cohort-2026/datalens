"""Data-cleaning functions for DataLens.

These functions are intentionally small and composable so they're easy to
unit test in isolation. They all take a ``pandas.DataFrame`` in and return a
new ``pandas.DataFrame`` out (no in-place mutation), which makes them safe to
chain together.
"""

from __future__ import annotations

import pandas as pd

NUMERIC_COLUMNS = ["quantity", "unit_price", "revenue"]


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully-duplicate rows, keeping the first occurrence.

    Args:
        df: Input dataframe.

    Returns:
        A new dataframe with duplicate rows removed. Index is reset.
    """
    return df.drop_duplicates().reset_index(drop=True)


def handle_missing_values(
    df: pd.DataFrame,
    strategy: str = "drop",
    fill_values: dict | None = None,
) -> pd.DataFrame:
    """Handle missing (NaN) values in a dataframe.

    Args:
        df: Input dataframe.
        strategy: Either ``"drop"`` (drop any row containing a NaN) or
            ``"fill"`` (fill NaNs using ``fill_values`` or sensible
            per-column defaults: numeric columns get their column mean,
            or ``0`` if the entire column is NaN (mean is undefined),
            everything else gets ``"unknown"``).
        fill_values: Optional explicit mapping of column name -> fill value.
            Only used when ``strategy == "fill"``. Columns not present in
            this mapping fall back to the default behaviour described above.

    Returns:
        A new dataframe with missing values handled according to
        ``strategy``.

    Raises:
        ValueError: If ``strategy`` is not one of ``"drop"`` or ``"fill"``.
    """
    if strategy not in {"drop", "fill"}:
        raise ValueError(f"Unknown strategy: {strategy!r}. Use 'drop' or 'fill'.")

    if strategy == "drop":
        return df.dropna().reset_index(drop=True)

    fill_values = fill_values or {}
    result = df.copy()
    for column in result.columns:
        if column in fill_values:
            result[column] = result[column].fillna(fill_values[column])
        elif pd.api.types.is_numeric_dtype(result[column]):
            mean = result[column].mean()
            # mean() is itself NaN when the whole column is NaN — fall back
            # to 0 so the column doesn't silently stay full of NaNs.
            result[column] = result[column].fillna(mean if pd.notna(mean) else 0)
        else:
            result[column] = result[column].fillna("unknown")
    return result.reset_index(drop=True)


def coerce_types(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    """Coerce known columns to appropriate dtypes.

    Parses ``date_column`` as a datetime and casts columns listed in
    ``NUMERIC_COLUMNS`` (that are present) to numeric, coercing unparsable
    values to NaN rather than raising.

    Args:
        df: Input dataframe.
        date_column: Name of the column to parse as a date.

    Returns:
        A new dataframe with coerced dtypes.
    """
    result = df.copy()
    if date_column in result.columns:
        result[date_column] = pd.to_datetime(result[date_column], errors="coerce")
    for column in NUMERIC_COLUMNS:
        if column in result.columns:
            result[column] = pd.to_numeric(result[column], errors="coerce")
    return result


def clean_data(
    df: pd.DataFrame,
    missing_strategy: str = "drop",
    date_column: str = "date",
    verbose: bool = False,
) -> pd.DataFrame:
    """Run the standard cleaning pipeline: coerce types, dedupe, handle NaNs.

    Args:
        df: Raw input dataframe.
        missing_strategy: Passed through to :func:`handle_missing_values`.
        date_column: Passed through to :func:`coerce_types`.
        verbose: if True, return a tuple of (cleaned_dataframe, details_dict).

    Returns:
        A cleaned dataframe, or (cleaned_dataframe, details_dict) if verbose is True.
    """
    
    # 1. Track initial dtypes and coerce types
    before_dtypes = df.dtypes.astype(str).to_dict()
    result = coerce_types(df, date_column=date_column)
    
    coerced_columns = {}
    for col, new_dtype in result.dtypes.astype(str).to_dict().items():
        if col in before_dtypes and before_dtypes[col] != new_dtype:
            coerced_columns[col] = f"{before_dtypes[col]} -> {new_dtype}"
    # 2. Track duplicates before dropping
    before_dedupe = len(result)
    result = remove_duplicates(result)
    duplicates_removed = before_dedupe - len(result)
    # 3. Track missing values before handling
    rows_with_missing = int(result.isna().any(axis=1).sum())
    cols_with_missing = result.columns[result.isna().any()].tolist()
    
    result = handle_missing_values(result, strategy=missing_strategy)
    if verbose:
        details = {
            "duplicates_removed": duplicates_removed,
            "missing_handled_rows": rows_with_missing,
            "missing_handled_cols": cols_with_missing,
            "coerced_dtypes": coerced_columns,
        }
        return result, details
    return result
