# labour_rights

An insight-driven starter project for exploring labour rights through data.

## What this project does

This repository now includes a lightweight dashboard generator that combines multiple CSV datasets into a single labour-rights report. The default sample data highlights:

- worker voice indicators such as union density and collective bargaining coverage
- workplace safety signals such as inspection coverage and serious injury rates
- equity outcomes such as the gender pay gap

The generated dashboard is designed to make it easy to compare countries, spot recent momentum, and understand which datasets are contributing to each insight.

## Project structure

- `data/` — sample labour-rights datasets in a shared CSV format
- `src/generate_dashboard.py` — dashboard/report generator
- `tests/test_generate_dashboard.py` — focused validation for the generator
- `site/index.html` — generated dashboard output

## CSV schema

Each dataset should use the following columns:

`country, year, theme, metric, value, unit, goal_direction, source`

- `goal_direction` should be `higher` when larger values are better for labour rights outcomes and `lower` when smaller values are better.

## Generate the dashboard

```bash
python src/generate_dashboard.py
```

Run the command from the repository root. This writes the dashboard to `site/index.html`.

## Run the focused tests

```bash
python -m unittest discover -s tests
```
