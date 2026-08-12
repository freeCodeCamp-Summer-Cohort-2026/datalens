"""Smoke tests for the CLI. Logic itself is tested against the package
functions directly in test_cleaning.py / test_analysis.py / test_charts.py -
these tests just confirm the CLI wiring works end to end.
"""

import os

import json

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
    csv_path=tmp_path/"sample.csv"
    output_path=tmp_path/"summary.json"
    _write_sample_csv(str(csv_path))

    runner=CliRunner()
    result=runner.invoke(cli,[
        "summarize",
        str(csv_path),
        "--by",
        "category",
        "--output",
        str(output_path),
        "--format",
        "json",
    ],)
    assert result.exit_code==0
    assert os.path.isfile(output_path)

    with open(output_path,"r",encoding="utf-8") as f:
        data=json.load(f)

    assert "summary" in data
    assert "breakdown" in data
    assert data["summary"]["row_count"]==3

def test_summarize_command_export_csv(tmp_path):
    csv_path=tmp_path/"sample.csv"
    output_path=tmp_path/"breakdown.csv"
    _write_sample_csv(str(csv_path))
    runner=CliRunner()
    result=runner.invoke(cli,[
        "summarize",
        str(csv_path),
        "--by",
        "category",
        "--output",
        str(output_path),
        "--format",
        "csv",
    ],)
    assert result.exit_code==0
    assert os.path.isfile(output_path)

    df_out=pd.read_csv(output_path)
    assert "category" in df_out.columns
    assert "total_revenue" in df_out.columns