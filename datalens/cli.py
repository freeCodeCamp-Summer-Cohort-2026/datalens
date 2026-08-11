"""Command-line interface for DataLens.

This module is intentionally thin - it parses arguments, reads/writes files,
and prints output, but delegates all actual data-wrangling logic to the
``datalens.cleaning`` and ``datalens.analysis`` modules so that logic stays
independently unit-testable.
"""

from __future__ import annotations

import os
import sys

import click
import pandas as pd

from datalens.analysis import group_by_summary, summarize
from datalens.charts import plot_by_category
from datalens.cleaning import clean_data
from datalens.quality import find_data_quality_issues


def _load_csv(path: str) -> pd.DataFrame:
    if not os.path.isfile(path):
        raise click.ClickException(f"Input file not found: {path}")
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError as exc:
        raise click.ClickException(f"Input file is empty: {path}") from exc


@click.group()
@click.version_option()
def cli() -> None:
    """DataLens: explore and report on tabular datasets from the command line."""


@cli.command(name="summarize")
@click.argument("input_csv", type=str)
@click.option(
    "--by",
    default=None,
    help="Optional column to also show a group-by breakdown for (e.g. 'category').",
)
def summarize_cmd(input_csv: str, by: str | None) -> None:
    """Print summary statistics for INPUT_CSV."""
    df = _load_csv(input_csv)
    summary = summarize(df)
    click.echo("DataLens summary")
    click.echo("=================")
    for key, value in summary.items():
        click.echo(f"{key}: {value}")

    if by:
        click.echo("")
        click.echo(f"Breakdown by {by}:")
        try:
            breakdown = group_by_summary(df, by=by)
        except KeyError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo(breakdown.to_string())


@cli.command()
@click.argument("input_csv", type=str)
@click.option(
    "--by",
    default="category",
    show_default=True,
    help="Column to group by for the chart.",
)
@click.option(
    "--output",
    default="chart.png",
    show_default=True,
    help="Path to write the PNG chart to.",
)
def chart(input_csv: str, by: str, output: str) -> None:
    """Generate a bar chart of revenue grouped by --by from INPUT_CSV."""
    df = _load_csv(input_csv)
    try:
        path = plot_by_category(df, output_path=output, by=by)
    except KeyError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Chart saved to {path}")


@cli.command()
@click.argument("input_csv", type=str)
@click.option(
    "--output",
    default="cleaned.csv",
    show_default=True,
    help="Path to write the cleaned CSV to.",
)
@click.option(
    "--missing-strategy",
    default="drop",
    type=click.Choice(["drop", "fill"]),
    show_default=True,
    help="How to handle missing values.",
)
def clean(input_csv: str, output: str, missing_strategy: str) -> None:
    """Clean INPUT_CSV (dedupe, fix types, handle missing values) and save it."""
    df = _load_csv(input_csv)
    before = len(df)
    cleaned = clean_data(df, missing_strategy=missing_strategy)
    cleaned.to_csv(output, index=False)
    click.echo(f"Cleaned {before} rows -> {len(cleaned)} rows. Saved to {output}")

@cli.command()
@click.argument("input_csv", type=str)
@click.option(
    "--output",
    default="quality_issues.csv",
    show_default=True,
    help="Path to write the rows with quality issues to.",
)
@click.option(
    "--tolerance",
    default=0.01,
    type=click.FloatRange(min=0.0),
    show_default=True,
    help="Absolute currency tolerance for the revenue check.",
)
def quality(
    input_csv: str, output: str, tolerance: float
) -> None:
    """Find data-quality issues in INPUT_CSV and save the affected rows."""
    df = _load_csv(input_csv)
    try:
        issues = find_data_quality_issues(
            df, tolerance=tolerance
        )
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    issues.to_csv(output, index=False)
    click.echo(f"Found {len(issues)} quality issue rows. Saved to {output}")


def main() -> None:
    cli()


if __name__ == "__main__":
    sys.exit(main())

