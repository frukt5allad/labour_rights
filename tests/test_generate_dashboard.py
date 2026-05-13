import tempfile
import unittest
from pathlib import Path

from src.generate_dashboard import build_summary, load_records, render_dashboard, write_dashboard


class DashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]
        self.data_dir = self.repo_root / "data"

    def test_load_records_reads_multiple_csv_files(self) -> None:
        records = load_records(self.data_dir)

        self.assertEqual(len(records), 30)
        self.assertEqual({record.dataset for record in records}, {"Collective Bargaining", "Equity", "Workplace Safety"})

    def test_build_summary_highlights_latest_leaders_and_momentum(self) -> None:
        summary = build_summary(load_records(self.data_dir))

        self.assertEqual(summary["dataset_count"], 3)
        self.assertEqual(summary["country_count"], 3)
        self.assertEqual(summary["latest_year"], 2024)
        self.assertEqual(summary["momentum"][0]["country"], "Chile")
        spotlights = {item["metric"]: item["country"] for item in summary["latest_spotlights"]}
        self.assertEqual(spotlights["Collective bargaining coverage"], "Sweden")
        self.assertEqual(spotlights["Gender pay gap"], "Sweden")
        self.assertIn("each improved in 5 tracked metrics", summary["insight_cards"][0])

    def test_write_dashboard_outputs_html_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "index.html"

            write_dashboard(self.data_dir, output_path)

            html = output_path.read_text(encoding="utf-8")
            self.assertIn("Labour Rights Insights Dashboard", html)
            self.assertIn("Latest metric spotlights (2024)", html)
            self.assertIn("Collective Bargaining", html)
            self.assertIn("Sweden", html)


if __name__ == "__main__":
    unittest.main()
