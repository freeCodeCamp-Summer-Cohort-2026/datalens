import pandas as pd
import pytest

from datalens.quality import find_data_quality_issues


def test_negative_quantity_is_reported():
    df = pd.DataFrame({"quantity": [-2, 2], "unit_price": [5.0, 5.0], "revenue": [10.0, 10.0]})
    result = find_data_quality_issues(df)
    assert list(result.index) == [0]
    assert "negative_quantity" in result.loc[0, "issues"]


def test_negative_revenue_is_reported():
    df = pd.DataFrame({"quantity": [2, 2], "unit_price": [5.0, 5.0], "revenue": [-1.0, 10.0]})
    result = find_data_quality_issues(df)
    assert list(result.index) == [0]
    assert "negative_revenue" in result.loc[0, "issues"]


def test_mismatched_revenue_is_reported():
    df = pd.DataFrame({"quantity": [2, 2], "unit_price": [5.0, 5.0], "revenue": [11.0, 10.0]})
    result = find_data_quality_issues(df)
    assert list(result.index) == [0]
    assert result.loc[0, "issues"] == ["revenue_mismatch"]


def test_revenue_within_tolerance_is_clean():
    df = pd.DataFrame({"quantity": [3], "unit_price": [0.10], "revenue": [0.3001]})
    assert find_data_quality_issues(df).empty


def test_clean_data_returns_no_issues():
    df = pd.DataFrame({"quantity": [1, 3], "unit_price": [5.0, 2.0], "revenue": [5.0, 6.0]})
    assert find_data_quality_issues(df).empty


def test_revenue_outside_tolerance_is_reported():
    df = pd.DataFrame({"quantity": [2], "unit_price": [5.0], "revenue": [11.0]})
    result = find_data_quality_issues(df)
    assert list(result.index) == [0]
    assert result.loc[0, "issues"] == ["revenue_mismatch"]


def test_revenue_tolerance_can_be_configured():
    df = pd.DataFrame({"quantity": [1, 1], "unit_price": [10.0, 10.0], "revenue": [10.049, 10.051]})
    result = find_data_quality_issues(df, tolerance=0.05)
    assert list(result.index) == [1]


def test_negative_revenue_tolerance_is_rejected():
    df = pd.DataFrame({"quantity": [1], "unit_price": [5.0], "revenue": [5.0]})
    with pytest.raises(ValueError, match="non-negative"):
        find_data_quality_issues(df, tolerance=-0.01)
        

def test_negative_unit_price_is_reported():
    df = pd.DataFrame({"quantity": [1], "unit_price": [-5.0], "revenue": [5.0]})
    result = find_data_quality_issues(df)
    assert result.loc[0, "issues"] == ["negative_unit_price", "revenue_mismatch"]
        
        
def test_missing_quantity_is_reported():
    df = pd.DataFrame({"quantity": [None], "unit_price": [5.0], "revenue": [5.0]})
    result = find_data_quality_issues(df)
    assert result.loc[0, "issues"] == ["missing_quantity"]


def test_missing_unit_price_is_reported():
    df = pd.DataFrame({"quantity": [1], "unit_price": [None], "revenue": [5.0]})
    result = find_data_quality_issues(df)
    assert result.loc[0, "issues"] == ["missing_unit_price"]


def test_missing_revenue_is_reported():
    df = pd.DataFrame({"quantity": [1], "unit_price": [5.0], "revenue": [None]})
    result = find_data_quality_issues(df)
    assert result.loc[0, "issues"] == ["missing_revenue"]


def test_multiple_missing_required_values_are_reported():
    df = pd.DataFrame({"quantity": [None], "unit_price": [None], "revenue": [None]})
    result = find_data_quality_issues(df)
    assert result.loc[0, "issues"] == [
        "missing_quantity",
        "missing_unit_price",
        "missing_revenue",
    ]

