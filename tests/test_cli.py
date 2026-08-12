"""Smoke tests for the CLI. Logic itself is tested against the package
functions directly in test_cleaning.py / test_analysis.py / test_charts.py -
these tests just confirm the CLI wiring works end to end.
"""

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
    result = runner.invoke(
        cli, ["quality", str(csv_path), "--output", str(output_path)]
    )

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
