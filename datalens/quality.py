"""Data-quality checks for DataLens datasets."""

from __future__ import annotations

import numpy as np
import pandas as pd


def find_data_quality_issues(
    df: pd.DataFrame, *, tolerance: float = 0.01
) -> pd.DataFrame:
    """Return rows failing negative quantity, negative revenue, or revenue mismatch checks.

    Revenue mismatch means the absolute difference between revenue and
    ``quantity * unit_price`` exceeds the supplied currency tolerance.
    The result preserves the original columns and adds ``issues``, a list of
    every failed check for each returned row.
    """
    required = {"quantity", "revenue", "unit_price"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if tolerance < 0:
        raise ValueError("Revenue tolerance must be non-negative")
    missing_quantity = df["quantity"].isna()
    missing_unit_price = df["unit_price"].isna()
    missing_revenue = df["revenue"].isna()
    complete_revenue_inputs = ~(
        missing_quantity | missing_unit_price | missing_revenue
    )
    difference = (df["revenue"] - df["quantity"] * df["unit_price"]).abs()
    matches = difference <= tolerance
    checks = pd.DataFrame({
        "missing_quantity": missing_quantity,
        "missing_unit_price": missing_unit_price,
        "missing_revenue": missing_revenue,
        "negative_quantity": df["quantity"] < 0,
        "negative_revenue": df["revenue"] < 0,
        "revenue_mismatch": complete_revenue_inputs & ~matches,
    }, index=df.index)
    issues = checks.apply(
        lambda row: [name for name, failed in row.items() if failed], axis=1
    )
    result = df.copy()
    result["issues"] = issues
    return result.loc[issues.map(bool)].copy()