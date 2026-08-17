"""Smoke tests for the CLI. Logic itself is tested against the package
functions directly in test_cleaning.py / test_analysis.py / test_charts.py -
these tests just confirm the CLI wiring works end to end.
"""

import json
import os

import pandas as pd
from click.testing import CliRunner

from datalens.cli import cli


def _write_sample_csv(path: str) -> None:
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-02", "2026-01-03"],
            "category": ["coffee", "tea", "coffee"],
            "quantity": [2, 1, 3],
            "unit_price": [3.0, 2.5, 3.0],
            "revenue": [6.0, 2.5, 9.0],
        }
    )
    df.to_csv(path, index=False)


def test_summarize_command_smoke(tmp_path):
    csv_path = tmp_path / "sample.csv"
    _write_sample_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["summarize", str(csv_path)])

    assert result.exit_code == 0
    assert "row_count: 3" in result.output


def test_summarize_command_missing_file_errors_cleanly(tmp_path):
    runner = CliRunner()
    result = runner.invoke(cli, ["summarize", str(tmp_path / "does_not_exist.csv")])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()


def test_clean_command_smoke(tmp_path):
    csv_path = tmp_path / "sample.csv"
    output_path = tmp_path / "cleaned.csv"
    _write_sample_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["clean", str(csv_path), "--output", str(output_path)])

    assert result.exit_code == 0
    assert os.path.isfile(output_path)


def test_summarize_command_export_json(tmp_path):
    csv_path = tmp_path / "sample.csv"
    output_path = tmp_path / "summary.json"
    _write_sample_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "summarize",
            str(csv_path),
            "--by",
            "category",
            "--output",
            str(output_path),
            "--format",
            "json",
        ],
    )
    assert result.exit_code == 0
    assert os.path.isfile(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "summary" in data
    assert "breakdown" in data
    assert data["summary"]["row_count"] == 3


def test_summarize_command_export_json_without_by(tmp_path):
    csv_path = tmp_path / "sample.csv"
    output_path = tmp_path / "summary_only.json"
    _write_sample_csv(str(csv_path))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "summarize",
            str(csv_path),
            "--output",
            str(output_path),
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0
    assert os.path.isfile(output_path)

    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "summary" in data
    assert "breakdown" not in data
    assert data["summary"]["row_count"] == 3


def test_summarize_command_export_csv(tmp_path):
    csv_path = tmp_path / "sample.csv"
    output_path = tmp_path / "breakdown.csv"
    _write_sample_csv(str(csv_path))
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "summarize",
            str(csv_path),
            "--by",
            "category",
            "--output",
            str(output_path),
            "--format",
            "csv",
        ],
    )
    assert result.exit_code == 0
    assert os.path.isfile(output_path)

    df_out = pd.read_csv(output_path)
    assert "category" in df_out.columns
    assert "total_revenue" in df_out.columns


def test_quality_command_writes_issues(tmp_path):
    csv_path = tmp_path / "quality_sample.csv"
    output_path = tmp_path / "quality_issues.csv"
    df = pd.DataFrame(
        {
            "quantity": [2, -1],
            "unit_price": [3.0, 4.0],
            "revenue": [6.0, 4.0],
        }
    )
    df.to_csv(csv_path, index=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["quality", str(csv_path), "--output", str(output_path)])

    assert result.exit_code == 0
    assert "Found 1 quality issue rows" in result.output
    issues = pd.read_csv(output_path)
    assert len(issues) == 1
    assert issues.loc[0, "quantity"] == -1
    assert "negative_quantity" in issues.loc[0, "issues"]


def test_trend_command_smoke(tmp_path):
    csv_path = tmp_path / "sample.csv"
    output_path = tmp_path / "rolling_average_trend.csv"
    _write_sample_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["trend", str(csv_path), "--window", "2", "--output", str(output_path)])

    assert result.exit_code == 0
    rolling_average = pd.read_csv(output_path)
    assert len(rolling_average) == 3
    assert rolling_average.loc[1, "revenue_rolling_avg"] == 4.25


def test_trend_command_invalid_column_error(tmp_path):
    csv_path = tmp_path / "sample.csv"
    _write_sample_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["trend", str(csv_path), "--column", "not_a_column"],
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, KeyError)


def test_chart_command_line_chart(tmp_path):
    csv_path = tmp_path / "sample.csv"
    output_path = tmp_path / "line_chart.png"
    _write_sample_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["chart", str(csv_path), "--kind", "line", "--output", str(output_path)])

    assert result.exit_code == 0
    assert os.path.isfile(output_path)


def test_clean_command_verbose_prints_details(tmp_path):
    csv_path = tmp_path / "sample.csv"
    output_path = tmp_path / "cleaned.csv"

    # Build a known input: 1 duplicate row + 1 missing category + string date
    df = pd.DataFrame(
        {
            "date": ["2026-01-01", "2026-01-01", "2026-01-02"],
            "category": ["coffee", "coffee", None],
            "quantity": [1, 1, 2],
            "unit_price": [2.5, 2.5, 3.0],
            "revenue": [2.5, 2.5, 6.0],
        }
    )
    df.to_csv(csv_path, index=False)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["clean", str(csv_path), "--output", str(output_path), "--verbose"],
    )

    assert result.exit_code == 0
    assert "Cleaning Details" in result.output
    assert "Duplicates removed: 1" in result.output
    assert "Rows with missing values handled: 1" in result.output
    assert "category" in result.output  # column name appears in the affected list
    assert "date" in result.output  # date dtype coercion is reported


def test_validate_command_success(tmp_path):
    csv_path = tmp_path / "valid.csv"
    df = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "store": ["Store A"],
            "category": ["coffee"],
            "item": ["latte"],
            "quantity": [2],
            "unit_price": [3.0],
            "revenue": [6.0],
        }
    )
    df.to_csv(csv_path, index=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", str(csv_path)])

    assert result.exit_code == 0
    assert "validation passed" in result.output.lower()


def test_validate_command_missing_columns(tmp_path):
    csv_path = tmp_path / "invalid.csv"
    # sample missing 'store' and 'item' columns
    df = pd.DataFrame(
        {
            "date": ["2026-01-01"],
            "category": ["coffee"],
            "quantity": [2],
            "unit_price": [3.0],
            "revenue": [6.0],
        }
    )
    df.to_csv(csv_path, index=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["validate", str(csv_path)])

    assert result.exit_code != 0
    assert "missing required columns" in result.output.lower()
    assert "store" in result.output.lower()
    assert "item" in result.output.lower()


def test_summarize_empty_csv(tmp_path):
    """Ensure summarizing an empty CSV file (headers only) works cleanly."""
    csv_path = tmp_path / "empty.csv"
    pd.DataFrame(columns=["date", "revenue", "quantity"]).to_csv(csv_path, index=False)

    runner = CliRunner()
    result = runner.invoke(cli, ["summarize", str(csv_path)])

    assert result.exit_code == 0
    assert "row_count: 0" in result.output


def test_cli_handles_corrupted_file(tmp_path):
    """Ensure pointing to a corrupted/binary file fails gracefully."""
    bad_file = tmp_path / "corrupted.csv"
    bad_file.write_bytes(b"\x00\x01\x02\xff\xfe\xfd")

    runner = CliRunner()
    result = runner.invoke(cli, ["summarize", str(bad_file)])

    assert result.exit_code != 0


def test_summarize_invalid_format_flag(tmp_path):
    """Ensure invalid --format options are rejected by Click."""
    csv_path = tmp_path / "sample.csv"
    _write_sample_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["summarize", str(csv_path), "--format", "xml"])

    assert result.exit_code != 0


def _write_outlier_csv(path: str) -> None:
    """Nine tightly-clustered revenues plus one obvious outlier."""
    df = pd.DataFrame(
        {
            "category": ["coffee"] * 9 + ["tea"],
            "revenue": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 1000.0],
        }
    )
    df.to_csv(path, index=False)


def test_outliers_command_writes_outlier_rows(tmp_path):
    csv_path = tmp_path / "outlier_sample.csv"
    output_path = tmp_path / "outliers.csv"
    _write_outlier_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["outliers", str(csv_path), "--output", str(output_path)])

    assert result.exit_code == 0
    assert "Found 1 outlier rows" in result.output
    found = pd.read_csv(output_path)
    assert len(found) == 1
    assert found.loc[0, "revenue"] == 1000.0


def test_outliers_command_zscore_method(tmp_path):
    csv_path = tmp_path / "outlier_sample.csv"
    output_path = tmp_path / "outliers_zscore.csv"
    _write_outlier_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "outliers",
            str(csv_path),
            "--method",
            "zscore",
            "--threshold",
            "2",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert "using zscore" in result.output
    found = pd.read_csv(output_path)
    assert len(found) == 1
    assert found.loc[0, "revenue"] == 1000.0


def test_outliers_command_threshold_is_honoured(tmp_path):
    """A wide enough fence must clear the planted outlier, proving --threshold
    reaches detect_outliers rather than being ignored."""
    csv_path = tmp_path / "outlier_sample.csv"
    output_path = tmp_path / "outliers_wide.csv"
    _write_outlier_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["outliers", str(csv_path), "--threshold", "1000", "--output", str(output_path)],
    )

    assert result.exit_code == 0
    assert "Found 0 outlier rows" in result.output


def test_outliers_command_missing_column_errors_cleanly(tmp_path):
    csv_path = tmp_path / "outlier_sample.csv"
    _write_outlier_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["outliers", str(csv_path), "--column", "not_a_column"])

    assert result.exit_code != 0
    assert result.exception.__class__ is SystemExit  # ClickException, not a traceback
    assert "not found" in result.output.lower()


def test_outliers_command_non_numeric_column_errors_cleanly(tmp_path):
    csv_path = tmp_path / "outlier_sample.csv"
    _write_outlier_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["outliers", str(csv_path), "--column", "category"])

    assert result.exit_code != 0
    assert "must be numeric" in result.output.lower()


def test_outliers_command_rejects_non_positive_threshold(tmp_path):
    csv_path = tmp_path / "outlier_sample.csv"
    _write_outlier_csv(str(csv_path))

    runner = CliRunner()
    result = runner.invoke(cli, ["outliers", str(csv_path), "--threshold", "0"])

    assert result.exit_code != 0
    assert "--threshold" in result.output
    assert "range x>0" in result.output
