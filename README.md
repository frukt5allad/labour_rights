# labour_rights

An insight-driven starter project for exploring labour rights through data.

## What this project does

This repository now includes a lightweight dashboard generator that combines multiple CSV datasets into a single labour-rights report. The default sample data highlights:

- worker voice indicators such as union density and collective bargaining coverage
- workplace safety signals such as inspection coverage and serious injury rates
- equity outcomes such as the gender pay gap

The generated dashboard is designed to make it easy to compare countries, spot recent momentum, and understand which datasets are contributing to each insight.

## Project structure

- `/home/runner/work/labour_rights/labour_rights/data` — sample labour-rights datasets in a shared CSV format
- `/home/runner/work/labour_rights/labour_rights/src/generate_dashboard.py` — dashboard/report generator
- `/home/runner/work/labour_rights/labour_rights/tests/test_generate_dashboard.py` — focused validation for the generator
- `/home/runner/work/labour_rights/labour_rights/site/index.html` — generated dashboard output

## CSV schema

Each dataset should use the following columns:

`country, year, theme, metric, value, unit, goal_direction, source`

- `goal_direction` should be `higher` when larger values are better for labour rights outcomes and `lower` when smaller values are better.

## Generate the dashboard

```bash
cd /home/runner/work/labour_rights/labour_rights
python src/generate_dashboard.py
```

This writes the dashboard to `/home/runner/work/labour_rights/labour_rights/site/index.html`.

## Run the focused tests

```bash
cd /home/runner/work/labour_rights/labour_rights
python -m unittest discover -s tests
```
