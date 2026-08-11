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
    
    # Check for missing quantity, unit_price, or revenue values
    missing_quantity = df["quantity"].isna()
    missing_unit_price = df["unit_price"].isna()
    missing_revenue = df["revenue"].isna()
    
    # Check for revenue mismatch beyond aboslute tolerance
    revenue_mismatch = ~(missing_quantity | missing_unit_price | missing_revenue) & ((df["revenue"] - df["quantity"] * df["unit_price"]).abs() > tolerance)
    
    # Check for negative quantity, unit_price or revenue values
    negative_quantity = df["quantity"] < 0
    negative_revenue = df["revenue"] < 0
    negative_unit_price = df["unit_price"] < 0
    
    # Combine all checks into a single mask
    checks = {
        "missing_quantity": missing_quantity,
        "missing_unit_price": missing_unit_price,
        "missing_revenue": missing_revenue,
        "negative_quantity": negative_quantity,
        "negative_revenue": negative_revenue,
        "negative_unit_price": negative_unit_price,
        "revenue_mismatch": revenue_mismatch,
    }
    
    check_mask = np.logical_or.reduce(list(checks.values()))
    
    # Filtering out rows with atleast one issue    
    result = df.loc[check_mask].copy()
    
    # Get all the check names from dictionary
    check_names = np.array(list(checks.keys()))
    
    # Convert the boolean masks to a 2D array for indexing
    full_masks = np.column_stack(list(checks.values()))
    check_masks = full_masks[check_mask]
    
    # For each row, find the names of the checks that failed
    result["issues"] = [check_names[row].tolist() for row in check_masks]
    
    return result
    