"""Analysis functions for DataLens.

Everything here takes a (typically already-cleaned) ``pandas.DataFrame`` and
returns either a summary ``dict``, a new ``DataFrame``, or a ``Series`` -
plain pandas objects that are easy to assert against in tests, print from
the CLI, or plot in a notebook.
"""

from __future__ import annotations

import pandas as pd


def summarize(df: pd.DataFrame) -> dict:
    """Compute a small set of summary statistics for the dataset.

    Args:
        df: Input dataframe. Expected to have ``quantity`` and ``revenue``
            numeric columns and a ``category`` column, but this degrades
            gracefully if some are missing.

    Returns:
        A dict with row count, column names, and (where available) total /
        mean revenue, total quantity, and the number of distinct categories.
    """
    summary: dict = {
        "row_count": len(df),
        "columns": list(df.columns),
    }
    if "revenue" in df.columns:
        summary["total_revenue"] = float(df["revenue"].sum())
        summary["mean_revenue"] = float(df["revenue"].mean())
    if "quantity" in df.columns:
        summary["total_quantity"] = float(df["quantity"].sum())
    if "category" in df.columns:
        summary["category_count"] = int(df["category"].nunique())
    if "date" in df.columns:
        parsed = pd.to_datetime(df["date"], errors="coerce")
        if parsed.notna().any():
            summary["date_min"] = str(parsed.min().date())
            summary["date_max"] = str(parsed.max().date())
    return summary


def group_by_summary(
    df: pd.DataFrame,
    by: str = "category",
    value_column: str = "revenue",
) -> pd.DataFrame:
    """Group rows by a column and aggregate quantity/revenue.

    Args:
        df: Input dataframe.
        by: Column name to group by (e.g. ``"category"`` or ``"store"``).
        value_column: Numeric column to sum/average per group.

    Returns:
        A dataframe indexed by the group column with ``total_<value_column>``,
        ``mean_<value_column>``, and ``count`` columns, sorted descending by
        the total.

    Raises:
        KeyError: If ``by`` or ``value_column`` is not a column in ``df``.
    """
    if by not in df.columns:
        raise KeyError(f"Column {by!r} not found in dataframe.")
    if value_column not in df.columns:
        raise KeyError(f"Column {value_column!r} not found in dataframe.")

    grouped = df.groupby(by)[value_column].agg(["sum", "mean", "count"])
    grouped = grouped.rename(
        columns={
            "sum": f"total_{value_column}",
            "mean": f"mean_{value_column}",
            "count": "count",
        }
    )
    return grouped.sort_values(f"total_{value_column}", ascending=False)


def rolling_average(
    df: pd.DataFrame,
    column: str = "revenue",
    window: int = 7,
    date_column: str = "date",
) -> pd.DataFrame:
    """Compute a rolling average of ``column`` over time.

    Rows are first grouped by day (summed), then a rolling mean is applied
    across the resulting daily series. This smooths out day-to-day noise so
    trends are easier to see on a chart.

    Args:
        df: Input dataframe with a date column and a numeric column.
        column: Numeric column to average (e.g. ``"revenue"``).
        window: Rolling window size, in days.
        date_column: Name of the date column.

    Returns:
        A dataframe indexed by date with two columns: the daily total of
        ``column`` and its rolling average (named ``f"{column}_rolling_avg"``).

    Raises:
        KeyError: If ``date_column`` or ``column`` is not present.
        ValueError: If ``window`` is not a positive integer.
    """
    if date_column not in df.columns:
        raise KeyError(f"Column {date_column!r} not found in dataframe.")
    if column not in df.columns:
        raise KeyError(f"Column {column!r} not found in dataframe.")
    if window <= 0:
        raise ValueError("window must be a positive integer.")

    working = df.copy()
    working[date_column] = pd.to_datetime(working[date_column], errors="coerce")
    daily = working.groupby(working[date_column].dt.date)[column].sum()
    daily.index = pd.to_datetime(daily.index)
    daily = daily.sort_index()

    result = pd.DataFrame({column: daily})
    result[f"{column}_rolling_avg"] = daily.rolling(window=window, min_periods=1).mean()
    return result


REQUIRED_COLUMNS = [
    "date",
    "store",
    "category",
    "item",
    "quantity",
    "unit_price",
    "revenue",
]


def validate_columns(
    df: pd.DataFrame, required_columns: list[str] | None = None
) -> list[str]:
    """Return a list of missing columns from df. Returns empty list if all exist."""
    if required_columns is None:
        required_columns = REQUIRED_COLUMNS
    missing = [col for col in required_columns if col not in df.columns]
    return missing
