"""Chart-generation helpers for DataLens.

Uses matplotlib with the non-interactive ``Agg`` backend so these functions
work headlessly (CI, servers, containers) without a display - they just save
PNG files to disk.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from datalens.analysis import group_by_summary  # noqa: E402


def plot_by_category(
    df: pd.DataFrame,
    output_path: str,
    by: str = "category",
    value_column: str = "revenue",
) -> str:
    """Save a bar chart of total ``value_column`` grouped by ``by``.

    Args:
        df: Input dataframe.
        output_path: Path (including filename) to write the PNG to.
        by: Column to group by (e.g. ``"category"``).
        value_column: Numeric column to sum per group.

    Returns:
        The ``output_path`` that was written, for convenience.
    """
    grouped = group_by_summary(df, by=by, value_column=value_column)
    total_column = f"total_{value_column}"

    fig, ax = plt.subplots(figsize=(8, 5))
    grouped[total_column].plot(kind="bar", ax=ax, color="#4C72B0")
    ax.set_title(f"Total {value_column} by {by}")
    ax.set_xlabel(by)
    ax.set_ylabel(f"Total {value_column}")
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


def plot_revenue_over_time(
    df: pd.DataFrame,
    output_path: str,
) -> str:
    """Save a line chart of daily revenue over time.

    Args:
        df: Input dataframe.
        output_path: Path (including filename) to write the PNG to.

    Returns:
        The ``output_path`` that was written, for convenience.
    """
    working = df.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")

    daily = working.groupby(working["date"].dt.date)["revenue"].sum()
    daily.index = pd.to_datetime(daily.index)
    daily = daily.sort_index()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(daily.index, daily)
    ax.set_title("Daily revenue over time")
    ax.set_xlabel("date")
    ax.set_ylabel("revenue ($)")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)

    return output_path
