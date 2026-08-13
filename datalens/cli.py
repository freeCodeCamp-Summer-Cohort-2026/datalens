"""Command-line interface for DataLens.

This module is intentionally thin - it parses arguments, reads/writes files,
and prints output, but delegates all actual data-wrangling logic to the
``datalens.cleaning`` and ``datalens.analysis`` modules so that logic stays
independently unit-testable.
"""

from __future__ import annotations

import os
import sys

import json

import click
import pandas as pd

from datalens.analysis import (
    group_by_summary,
    summarize,
    rolling_average,
    validate_columns,
)
from datalens.charts import plot_by_category, plot_revenue_over_time

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

@click.option(
    "--output",
    default=None,
    show_default=True,
    help="Path to write the summary/breakdown report to.",
)
@click.option(
    "--format",
    default="json",
    type=click.Choice(["csv", "json"], case_sensitive=False),
    show_default=True,
    help="Output file format when --output is specified.",
)
def summarize_cmd(
    input_csv: str, by: str | None, output: str | None, format: str
) -> None:
    """Print summary statistics for INPUT_CSV."""
    df = _load_csv(input_csv)
    summary = summarize(df)
    click.echo("DataLens summary")
    click.echo("=================")
    for key, value in summary.items():
        click.echo(f"{key}: {value}")

    breakdown = None

    if by:
        click.echo("")
        click.echo(f"Breakdown by {by}:")
        try:
            breakdown = group_by_summary(df, by=by)
        except KeyError as exc:
            raise click.ClickException(str(exc)) from exc
        click.echo(breakdown.to_string())
    if output:
        _save_summary(summary, breakdown, output, format)
        click.echo(f"Report saved to {output}")


def _save_summary(
    summary: dict, breakdown: pd.DataFrame | None, output_path: str, file_format: str
) -> None:
    if file_format == "csv":
        if breakdown is not None:
            breakdown.to_csv(output_path)
        else:
            summary_df = pd.DataFrame(
                list(summary.items()), columns=["metric", "value"]
            )
            summary_df.to_csv(output_path, index=False)
    elif file_format == "json":
        try:
            data_to_write = {"summary": summary}
            if breakdown is not None:
                data_to_write["breakdown"] = breakdown.reset_index().to_dict(
                    orient="records"
                )
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data_to_write, f, indent=2)
        except (KeyError, TypeError) as exc:
            raise click.ClickException(str(exc)) from exc


@cli.command()
@click.argument("input_csv", type=str)
@click.option(
    "--by",
    default="category",
    show_default=True,
    help="Column to group by for the chart.",
)
@click.option(
    "--kind",
    default="bar",
    type=click.Choice(["bar", "line"]),
    show_default=True,
    help="Type of chart to generate.",
)
@click.option(
    "--output",
    default="chart.png",
    show_default=True,
    help="Path to write the PNG chart to.",
)
def chart(input_csv: str, by: str, kind: str, output: str) -> None:
    """Generate a bar or line chart from INPUT_CSV."""
    df = _load_csv(input_csv)

    try:
        if kind == "line":
            path = plot_revenue_over_time(
                df,
                output_path=output,
            )
        else:
            path = plot_by_category(
                df,
                output_path=output,
                by=by,
            )
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
@click.option(
    "--verbose",
    is_flag=True,
    help="Print extra details about the cleaning pipeline.",
)
def clean(input_csv: str, output: str, missing_strategy: str, verbose: bool) -> None:
    """Clean INPUT_CSV (dedupe, fix types, handle missing values) and save it."""
    df = _load_csv(input_csv)
    before = len(df)
    
    if verbose:
        cleaned, details = clean_data(df, missing_strategy=missing_strategy, verbose=True)
    else:
        cleaned = clean_data(df, missing_strategy=missing_strategy)
        
    cleaned.to_csv(output, index=False)
    click.echo(f"Cleaned {before} rows -> {len(cleaned)} rows. Saved to {output}")
    
    if verbose:
        click.echo("\n--- Cleaning Details ---")
        click.echo(f"Duplicates removed: {details['duplicates_removed']}")
        click.echo(f"Rows with missing values handled: {details['missing_handled_rows']}")
        if details['missing_handled_cols']:
            click.echo(f"  -> Columns affected: {', '.join(details['missing_handled_cols'])}")
        
        click.echo("Dtypes coerced:")
        if details['coerced_dtypes']:
            for col, transition in details['coerced_dtypes'].items():
                click.echo(f"  -> {col}: {transition}")
        else:
            click.echo("  -> None")

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
def quality(input_csv: str, output: str, tolerance: float) -> None:
    """Find data-quality issues in INPUT_CSV and save the affected rows."""
    df = _load_csv(input_csv)
    try:
        issues = find_data_quality_issues(df, tolerance=tolerance)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    issues.to_csv(output, index=False)
    click.echo(f"Found {len(issues)} quality issue rows. Saved to {output}")


@cli.command(name="trend")
@click.argument("input_csv", type=str)
@click.option(
    "--column",
    default="revenue",
    show_default=True,
    help="Column for which rolling average needs to be calculated.",
)
@click.option(
    "--window",
    default=7,
    show_default=True,
    help="Default window size of rolling average",
)
@click.option(
    "--date-column",
    default="date",
    show_default=True,
    help="Date column to calculate the windows",
)
@click.option(
    "--output",
    default="rolling_average_trend.csv",
    show_default=True,
    help="Name of file where rolling average output is stored",
)
def trend_cmd(
    input_csv: str, column: str, window: int, date_column: str, output: str
) -> None:
    """Compute the rolling_average for the input_csv over the provided window and column"""
    df = _load_csv(input_csv)
    rolling_average_df = rolling_average(df, column, window, date_column)
    rolling_average_df.to_csv(output)
    click.echo(f"Rolling Average of {column} with window {window} saved to {output}")


@cli.command(name="validate")
@click.argument("input_csv", type=str)
def validate_cmd(input_csv: str) -> None:
    """Check that INPUT_CSV contains all required columns."""
    df = _load_csv(input_csv)
    missing = validate_columns(df)

    if missing:
        missing_str = ", ".join(missing)
        raise click.ClickException(f"Missing required columns: {missing_str}")
    click.echo("Validation passed: All required columns are present.")


def main() -> None:
    cli()


if __name__ == "__main__":
    sys.exit(main())
