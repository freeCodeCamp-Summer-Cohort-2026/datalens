"""Performance benchmarking script for DataLens.

Measures execution times for core data cleaning and analysis pipeline operations
(`clean_data`, `group_by_summary`, and `rolling_average`) using a 100k+ row dataset.
Used for bottleneck detection and verification of performance optimizations.
"""

from __future__ import annotations

import time
import pandas as pd

from datalens.analysis import (
    group_by_summary,
    rolling_average,
    summarize,
    validate_columns,
)
from datalens.cleaning import clean_data


def performance_check_for_larger_dataset() -> None:
    """Benchmark DataLens pipeline execution speed against a 100k-row dataset.

    Loads raw data from ``data/sample_100k.csv`` into memory and records high-precision
    wall-clock timing (using :func:`time.perf_counter`) across data cleaning, categorical 
    summarization, and rolling average calculations. Prints timing results to stdout.
    """
    print("Loading 100k dataset into memory...")
    df = pd.read_csv("data/sample_100k.csv")
    print(f"Loaded {len(df)} rows successfully.\n")

    # 1. measure data cleaning speed
    t0 = time.perf_counter()
    cleaned_df = clean_data(df)
    t1 = time.perf_counter()
    print(f"clean_data:         {t1 - t0:.4f} seconds")

    # 2. measure categorical summary speed
    t0 = time.perf_counter()
    _ = group_by_summary(cleaned_df)
    t1 = time.perf_counter()
    print(f"group_by_summary:   {t1 - t0:.4f} seconds")

    # 3. measure rolling average calculation speed
    t0 = time.perf_counter()
    _ = rolling_average(cleaned_df)
    t1 = time.perf_counter()
    print(f"rolling_average:    {t1 - t0:.4f} seconds")

    print("____________________________________________\n")


if __name__ == "__main__":
    performance_check_for_larger_dataset()
