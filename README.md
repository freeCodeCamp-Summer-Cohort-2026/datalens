# DataLens

A small dataset-exploration and reporting toolkit built on pandas. DataLens
gives you a reusable Python package, a CLI, and a demo notebook for
cleaning, summarising, and charting tabular data - demonstrated here on a
synthetic coffee-shop sales dataset.

This repo is the starter project for the freeCodeCamp/NHCarrigan Summer
2026 Cohort's sprint phase. If you're a cohort participant, start with
[CONTRIBUTING.md](CONTRIBUTING.md) for how to claim an issue and get a PR up.

## What's in here

- `datalens/` - the core package: cleaning functions (`datalens/cleaning.py`)
  and analysis functions (`datalens/analysis.py` and `datalens/charts.py`),
  all pandas-based and independently unit-tested.
- `datalens/cli.py` - a `click`-based CLI that wraps the package functions.
- `scripts/generate_sample_data.py` - generates the synthetic sample dataset.
- `data/sample.csv` - ~800 rows of synthetic coffee-shop sales data (with a
  few duplicate rows and missing values baked in on purpose).
- `notebooks/exploration.ipynb` - a walkthrough of the package on the sample
  dataset, with charts.
- `tests/` - pytest coverage for the cleaning/analysis/chart functions, plus
  a CLI smoke test.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` also installs this repo's `datalens` package itself (in
editable mode), which registers the `datalens` command.

Run the tests:

```bash
pytest
```

## CLI usage

```bash
# Print summary statistics for a CSV (row count, revenue totals, date range, ...)
datalens summarize data/sample.csv

# ...optionally with a group-by breakdown
datalens summarize data/sample.csv --by category

# Save a bar chart of revenue by category (or any other column) as a PNG
datalens chart data/sample.csv --by category --output chart.png

# Clean a CSV (dedupe, fix types, handle missing values) and save the result
datalens clean data/sample.csv --output cleaned.csv --missing-strategy drop

# Check for data quality (missing values in quantity, revenue, values, negative quantity, negative revenue, or revenue values that do not match quantity * unit_price within an absolute tolerance amount.Default tolerance value is 0.01)
datalens quality data/sample.csv --output quality_report.csv --tolerance 0.03

# Calculate rolling average trend for a given column
datalens trend data/sample.csv

# Find outlier rows, via Tukey fences (default) or an absolute z-score
datalens outliers data/sample.csv --column revenue --output outliers.csv
datalens outliers data/sample.csv --method zscore --threshold 3
```

Run `datalens --help` or `datalens <command> --help` for the full option
list.

## Getting Started 

If we were to run the first command of the CLI usage section (`datalens summarize data/sample.csv`), the command will summarise the data within our `sample.csv` file which is in the data directory. 

In this case, when we run the command, the output will show:

- row_count (the number of rows)
- columns (the name of each column in a list)
- total_revenue (all the individual revenue entries added together)
- mean_revenue (the total revenue divided by how many revenue entries there are)
- total_quantity (tells the user how many items are being sold in that data set)
- category_count (tells the user how many categories the data set contains)
- date_min (tells us the date the first sale was made within the data set)
- date_max (tells us the date when the latest sale was made within the data set)

Specifically, running the command on `sample.csv`, the results should output to the terminal. These results should be obtained:

```bash
DataLens summary
=================
row_count: 816
columns: ['date', 'store', 'category', 'item', 'quantity', 'unit_price', 'revenue']
total_revenue: 19734.43
mean_revenue: 24.184350490196078
total_quantity: 2791.0
category_count: 5
date_min: 2026-01-01
date_max: 2026-06-30
```

## Regenerating the sample dataset

```bash
python scripts/generate_sample_data.py --rows 800 --output data/sample.csv --seed 42
```

## The dataset

`data/sample.csv` is synthetic - generated, not scraped or sourced from a
real business - with columns:

| column      | description                                  |
|-------------|-----------------------------------------------|
| `date`      | sale date (YYYY-MM-DD)                        |
| `store`     | store location (Downtown, Riverside, ...)     |
| `category`  | product category (coffee, tea, pastry, ...)   |
| `item`      | specific item sold                            |
| `quantity`  | units sold in that transaction                |
| `unit_price`| price per unit                                |
| `revenue`   | `quantity * unit_price`                       |

A small number of rows are intentionally duplicated or missing values, so
the cleaning functions in `datalens.cleaning` have something real to clean.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the issue-claiming workflow and
how to run tests locally.

## License

[MIT](LICENSE)
