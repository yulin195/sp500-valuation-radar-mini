import tempfile
import unittest
import urllib.error
from datetime import date
from pathlib import Path

from radar_mini.report import Result, sort_group
from tests.test_cli import SAMPLE, chart, run

GOLDEN = Path(__file__).resolve().parent / "golden" / "brief.expected.md"
# Fixed closes against data/anchors.sample.csv; XOM deliberately has no data.
CLOSES = {"AAPL": 148.0, "MSFT": 350.0, "AMZN": 146.0, "JNJ": 160.0,
          "JPM": 300.0, "PG": 142.0, "KO": 57.0}


def transport(url):
    for t, c in CLOSES.items():
        if f"/{t}?" in url:
            return chart(c)
    raise urllib.error.URLError("mock: no data")


def res(ticker, dist, cap):
    return Result(ticker, 1.0, date(2026, 11, 10), 1.0, dist, "yellow", False, "S", cap)


class SortTest(unittest.TestCase):
    def order(self, *items):
        return [r.ticker for r in sort_group(list(items))]

    def test_distance_ascending(self):
        self.assertEqual(self.order(res("B", 3.0, "mega"), res("A", -2.0, "mega"),
                                    res("C", 20.0, "mega")), ["A", "B", "C"])

    def test_cap_breaks_ties_within_5pp(self):
        self.assertEqual(self.order(res("S", 1.0, "small"), res("M", 5.9, "mega"),
                                    res("L", 3.0, "large")), ["M", "L", "S"])

    def test_gap_over_5pp_keeps_distance_order(self):
        self.assertEqual(self.order(res("S", 1.0, "small"), res("M", 6.5, "mega")),
                         ["S", "M"])

    def test_exactly_5pp_is_a_tie(self):
        self.assertEqual(self.order(res("S", 1.0, "small"), res("M", 6.0, "mega")),
                         ["M", "S"])

    def test_same_cap_falls_back_to_distance(self):
        self.assertEqual(self.order(res("B", 4.0, "mid"), res("A", 1.0, "mid")),
                         ["A", "B"])


class GoldenTest(unittest.TestCase):
    def test_brief_matches_golden_file(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "brief.md"
            code, stdout, _ = run(["--anchors", str(SAMPLE), "--out", str(out)], transport)
            brief = out.read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertEqual(brief, GOLDEN.read_text(encoding="utf-8"))

    def test_terminal_table_marks_fair_range_and_coverage(self):
        code, stdout, _ = run(["--anchors", str(SAMPLE), "--out", "/dev/null"], transport)
        self.assertIn("watch*", stdout)
        self.assertIn("Priced 7 of 8 anchors.", stdout)
        self.assertIn("XOM", stdout)
        self.assertNotIn("JPM  ", stdout.split("Priced")[0])  # ok tier not listed


if __name__ == "__main__":
    unittest.main()
