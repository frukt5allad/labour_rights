from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from html import escape
from pathlib import Path


@dataclass(frozen=True)
class Record:
    dataset: str
    country: str
    year: int
    theme: str
    metric: str
    value: float
    unit: str
    goal_direction: str
    source: str


def load_records(data_dir: Path) -> list[Record]:
    records: list[Record] = []
    for csv_path in sorted(data_dir.glob("*.csv")):
        with csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                records.append(
                    Record(
                        dataset=csv_path.stem.replace("_", " ").title(),
                        country=row["country"].strip(),
                        year=int(row["year"]),
                        theme=row["theme"].strip(),
                        metric=row["metric"].strip(),
                        value=float(row["value"]),
                        unit=row["unit"].strip(),
                        goal_direction=row["goal_direction"].strip().lower(),
                        source=row["source"].strip(),
                    )
                )
    return records


def format_value(record: Record) -> str:
    if record.unit == "%":
        return f"{record.value:.1f}%"
    return f"{record.value:.1f} {record.unit}".strip()


def is_improvement(previous: Record, current: Record) -> bool:
    if current.goal_direction == "lower":
        return current.value < previous.value
    return current.value > previous.value


def choose_best(records: list[Record]) -> Record:
    directions = {record.goal_direction for record in records}
    if len(directions) != 1:
        raise ValueError("Records for the same metric must share one goal_direction.")
    direction = directions.pop()
    selector = min if direction == "lower" else max
    return selector(records, key=lambda record: record.value)


def format_country_list(countries: list[str]) -> str:
    if len(countries) <= 2:
        return " and ".join(countries)
    return ", ".join(countries[:-1]) + f", and {countries[-1]}"


def build_summary(records: list[Record]) -> dict[str, object]:
    if not records:
        raise ValueError("No CSV records found in the data directory.")

    countries = sorted({record.country for record in records})
    metrics = sorted({record.metric for record in records})
    years = sorted({record.year for record in records})
    latest_year = years[-1]

    grouped_by_metric: dict[str, list[Record]] = defaultdict(list)
    grouped_by_country_metric: dict[tuple[str, str], list[Record]] = defaultdict(list)
    sources: dict[str, set[str]] = defaultdict(set)

    for record in records:
        grouped_by_metric[record.metric].append(record)
        grouped_by_country_metric[(record.country, record.metric)].append(record)
        sources[record.dataset].add(record.source)

    latest_spotlights = []
    for metric, metric_records in sorted(grouped_by_metric.items()):
        latest_records = [record for record in metric_records if record.year == latest_year]
        if not latest_records:
            continue
        best = choose_best(latest_records)
        latest_spotlights.append(
            {
                "metric": metric,
                "country": best.country,
                "value": format_value(best),
                "theme": best.theme,
            }
        )

    momentum = []
    for country in countries:
        improved = 0
        stagnated = 0
        for metric in metrics:
            country_metric_records = sorted(
                grouped_by_country_metric.get((country, metric), []),
                key=lambda record: record.year,
            )
            if len(country_metric_records) < 2:
                continue
            first = country_metric_records[0]
            last = country_metric_records[-1]
            if first.value == last.value:
                stagnated += 1
            elif is_improvement(first, last):
                improved += 1
        momentum.append(
            {
                "country": country,
                "improved": improved,
                "stagnated": stagnated,
            }
        )

    momentum.sort(key=lambda item: (-item["improved"], item["country"]))

    theme_values: dict[str, list[float]] = defaultdict(list)
    for record in records:
        if record.year == latest_year:
            theme_values[record.theme].append(record.value)

    theme_summary = [
        {
            "theme": theme,
            "tracked_metrics": len({record.metric for record in records if record.year == latest_year and record.theme == theme}),
            "latest_observations": len(values),
        }
        for theme, values in sorted(theme_values.items())
    ]

    top_improvement_count = momentum[0]["improved"] if momentum else 0
    top_countries = [item["country"] for item in momentum if item["improved"] == top_improvement_count]
    if len(top_countries) == 1:
        momentum_card = f"{top_countries[0]} shows the strongest recent momentum, improving in {top_improvement_count} tracked metrics."
    else:
        leaders = format_country_list(top_countries)
        momentum_card = f"{leaders} each improved in {top_improvement_count} tracked metrics, signalling broad-based momentum across the latest period."

    insight_cards = [
        momentum_card if momentum else "",
        f"The dashboard currently combines {len(sources)} datasets across {len(countries)} countries from {years[0]} to {latest_year}.",
        f"The latest snapshot covers {len(latest_spotlights)} labour-rights metrics, making it easier to compare worker voice, safety, and equity outcomes together.",
    ]

    return {
        "country_count": len(countries),
        "dataset_count": len(sources),
        "metric_count": len(metrics),
        "latest_year": latest_year,
        "year_range": f"{years[0]}–{latest_year}",
        "latest_spotlights": latest_spotlights,
        "momentum": momentum,
        "theme_summary": theme_summary,
        "sources": {dataset: sorted(dataset_sources) for dataset, dataset_sources in sorted(sources.items())},
        "insight_cards": insight_cards,
    }


def render_dashboard(summary: dict[str, object]) -> str:
    cards = "".join(
        f"<article class='card'><p>{escape(card)}</p></article>"
        for card in summary["insight_cards"]
        if card
    )
    spotlight_rows = "".join(
        "<tr>"
        f"<td>{escape(item['metric'])}</td>"
        f"<td>{escape(item['theme'])}</td>"
        f"<td>{escape(item['country'])}</td>"
        f"<td>{escape(item['value'])}</td>"
        "</tr>"
        for item in summary["latest_spotlights"]
    )
    momentum_rows = "".join(
        "<tr>"
        f"<td>{escape(item['country'])}</td>"
        f"<td>{item['improved']}</td>"
        f"<td>{item['stagnated']}</td>"
        "</tr>"
        for item in summary["momentum"]
    )
    theme_rows = "".join(
        "<tr>"
        f"<td>{escape(item['theme'])}</td>"
        f"<td>{item['tracked_metrics']}</td>"
        f"<td>{item['latest_observations']}</td>"
        "</tr>"
        for item in summary["theme_summary"]
    )
    source_items = "".join(
        "<li>"
        f"<strong>{escape(dataset)}</strong>: {escape(', '.join(dataset_sources))}"
        "</li>"
        for dataset, dataset_sources in summary["sources"].items()
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Labour Rights Insights Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --card: #ffffff;
      --border: #d8deea;
      --text: #162033;
      --accent: #315efb;
    }}
    body {{
      font-family: Arial, sans-serif;
      margin: 0;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    main {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 2rem 1rem 4rem;
    }}
    .hero, .section, .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 16px;
      box-shadow: 0 8px 24px rgba(22, 32, 51, 0.06);
    }}
    .hero {{
      padding: 2rem;
      margin-bottom: 1.5rem;
    }}
    .hero h1 {{
      margin-top: 0;
    }}
    .stats, .cards {{
      display: grid;
      gap: 1rem;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }}
    .stat {{
      padding: 1rem;
      background: #eef2ff;
      border-radius: 12px;
    }}
    .stat strong {{
      display: block;
      font-size: 1.8rem;
      color: var(--accent);
    }}
    .cards {{
      margin: 1.5rem 0;
    }}
    .card {{
      padding: 1rem 1.25rem;
    }}
    .section {{
      padding: 1.25rem;
      margin-top: 1rem;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      padding: 0.75rem;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}
    ul {{
      padding-left: 1.25rem;
      margin-bottom: 0;
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p><strong>Insight-driven labour rights project</strong></p>
      <h1>Labour Rights Insights Dashboard</h1>
      <p>This starter project turns multiple labour-related CSV datasets into a single dashboard for comparing worker voice, safety, and equity outcomes.</p>
      <div class="stats">
        <div class="stat"><span>Datasets</span><strong>{summary['dataset_count']}</strong></div>
        <div class="stat"><span>Countries</span><strong>{summary['country_count']}</strong></div>
        <div class="stat"><span>Metrics</span><strong>{summary['metric_count']}</strong></div>
        <div class="stat"><span>Coverage</span><strong>{summary['year_range']}</strong></div>
      </div>
    </section>
    <section class="cards">{cards}</section>
    <section class="section">
      <h2>Latest metric spotlights ({summary['latest_year']})</h2>
      <table>
        <thead>
          <tr><th>Metric</th><th>Theme</th><th>Top country</th><th>Latest value</th></tr>
        </thead>
        <tbody>{spotlight_rows}</tbody>
      </table>
    </section>
    <section class="section">
      <h2>Country momentum</h2>
      <table>
        <thead>
          <tr><th>Country</th><th>Improving metrics</th><th>Stagnant metrics</th></tr>
        </thead>
        <tbody>{momentum_rows}</tbody>
      </table>
    </section>
    <section class="section">
      <h2>Theme snapshot</h2>
      <table>
        <thead>
          <tr><th>Theme</th><th>Tracked metrics</th><th>Latest observations</th></tr>
        </thead>
        <tbody>{theme_rows}</tbody>
      </table>
    </section>
    <section class="section">
      <h2>Datasets in use</h2>
      <ul>{source_items}</ul>
    </section>
  </main>
</body>
</html>
"""


def write_dashboard(data_dir: Path, output_path: Path) -> None:
    summary = build_summary(load_records(data_dir))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_dashboard(summary), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a labour rights dashboard from CSV datasets.")
    parser.add_argument("--data-dir", default="data", type=Path)
    parser.add_argument("--output", default="site/index.html", type=Path)
    args = parser.parse_args()
    write_dashboard(args.data_dir, args.output)


if __name__ == "__main__":
    main()
