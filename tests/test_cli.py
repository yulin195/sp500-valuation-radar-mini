import json
import tempfile
import unittest
import urllib.error
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

from radar_mini.cli import main

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "data" / "anchors.sample.csv"
OFFSET = -18000
NOW = int(datetime(2026, 11, 10, 17, 0, tzinfo=timezone.utc).timestamp()) - OFFSET


def _ts(d, h, m=0):
    return int(datetime(2026, 11, d, h, m, tzinfo=timezone.utc).timestamp()) - OFFSET


def chart(close):
    stamps = [_ts(9, 9, 30), _ts(10, 9, 30)]
    return json.dumps({"chart": {"result": [{
        "meta": {"gmtoffset": OFFSET, "currentTradingPeriod": {"regular": {
            "start": _ts(10, 9, 30), "end": _ts(10, 16)}}},
        "timestamp": stamps,
        "indicators": {"quote": [{"close": [close, close]}]}}]}}).encode()


def run(args, transport):
    out, err = StringIO(), StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(args, transport=transport, now=NOW)
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def test_version_and_missing_file(self):
        code, _, err = run(["--anchors", "/nonexistent.csv"], lambda u: b"")
        self.assertEqual(code, 2)
        self.assertIn("error", err)

    def test_bad_csv_exits_2_naming_line(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.csv"
            p.write_text("ticker,trigger,fair_low,fair_high,sector,cap_tier\n"
                         "AAA,x,2,3,S,mega\n")
            code, _, err = run(["--anchors", str(p), "--out", str(Path(d) / "b.md")],
                               lambda u: b"")
        self.assertEqual(code, 2)
        self.assertIn("line 2", err)

    def test_all_no_data_exits_3_and_writes_no_brief(self):
        def down(url):
            raise urllib.error.URLError("down")
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "brief.md"
            code, stdout, err = run(["--anchors", str(SAMPLE), "--out", str(out)], down)
            self.assertEqual(code, 3)
            self.assertFalse(out.exists())
        self.assertEqual(stdout, "")
        self.assertIn("no-data", err)

    def test_partial_run_exits_0_with_coverage(self):
        def t(url):
            if "/AAPL?" in url:
                return chart(140.0)   # below the 150 sample trigger -> red
            raise urllib.error.URLError("down")
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "brief.md"
            code, stdout, _ = run(["--anchors", str(SAMPLE), "--out", str(out)], t)
            brief = out.read_text(encoding="utf-8")
        self.assertEqual(code, 0)
        self.assertIn("Priced 1 of 8 anchors.", stdout)
        self.assertIn("not an all-clear", stdout)
        self.assertIn("Priced 1 of 8 anchors.", brief)
        self.assertIn("| AAPL | 140.00 |", brief)


if __name__ == "__main__":
    unittest.main()
