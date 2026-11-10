import tempfile
import unittest
from pathlib import Path

from radar_mini.loader import AnchorError, load_anchors, parse_anchors

HEADER = "ticker,trigger,fair_low,fair_high,sector,cap_tier"
GOOD = "AAA,100,110,130,Financials,large"


def parse(*rows: str, header: str = HEADER):
    return parse_anchors([header, *rows], source="t.csv")


class LoaderTest(unittest.TestCase):
    def test_valid_row(self):
        (a,) = parse(GOOD)
        self.assertEqual((a.ticker, a.trigger, a.fair_low, a.fair_high), ("AAA", 100, 110, 130))
        self.assertEqual((a.sector, a.cap_tier), ("Financials", "large"))

    def assert_bad(self, row: str, line: int, fragment: str):
        with self.assertRaises(AnchorError) as cm:
            parse(GOOD.replace("AAA", "OK1"), row)
        msg = str(cm.exception)
        self.assertIn(f"line {line}", msg)
        self.assertIn(fragment, msg)

    def test_missing_field(self):
        self.assert_bad("AAA,100,110,130,Financials", 3, "expected 6 fields")
        self.assert_bad("AAA,100,110,130,,large", 3, "missing field sector")
        self.assert_bad(",100,110,130,Financials,large", 3, "missing field ticker")

    def test_non_numeric(self):
        self.assert_bad("AAA,abc,110,130,Financials,large", 3, "trigger is not numeric")
        self.assert_bad("AAA,100,x,130,Financials,large", 3, "fair_low is not numeric")
        self.assert_bad("AAA,100,110,nan,Financials,large", 3, "fair_high")

    def test_non_positive_trigger(self):
        self.assert_bad("AAA,0,110,130,Financials,large", 3, "trigger must be positive")
        self.assert_bad("AAA,-5,110,130,Financials,large", 3, "trigger must be positive")

    def test_fair_low_not_above_trigger(self):
        self.assert_bad("AAA,100,100,130,Financials,large", 3, "fair_low")
        self.assert_bad("AAA,100,90,130,Financials,large", 3, "fair_low")

    def test_fair_high_below_fair_low(self):
        self.assert_bad("AAA,100,110,109,Financials,large", 3, "fair_high")

    def test_fair_high_equal_fair_low_is_allowed(self):
        self.assertEqual(len(parse("AAA,100,110,110,Financials,large")), 1)

    def test_bad_cap_tier_and_duplicate(self):
        self.assert_bad("AAA,100,110,130,Financials,huge", 3, "cap_tier")
        with self.assertRaises(AnchorError) as cm:
            parse(GOOD, GOOD)
        self.assertIn("line 3", str(cm.exception))
        self.assertIn("duplicate", str(cm.exception))

    def test_bad_header_and_empty(self):
        with self.assertRaises(AnchorError):
            parse(GOOD, header="ticker,trigger")
        with self.assertRaises(AnchorError):
            parse()

    def test_line_numbers_count_comments_and_blanks(self):
        lines = ["# sample", HEADER, "", GOOD, "AAA,bad,1,2,S,mega"]
        with self.assertRaises(AnchorError) as cm:
            parse_anchors(lines, source="t.csv")
        self.assertIn("line 5", str(cm.exception))

    def test_missing_file(self):
        with self.assertRaises(AnchorError):
            load_anchors("/nonexistent/anchors.csv")


class SampleFileTest(unittest.TestCase):
    def test_sample_loads_and_is_labelled(self):
        path = Path(__file__).resolve().parent.parent / "data" / "anchors.sample.csv"
        anchors = load_anchors(path)
        self.assertTrue(5 <= len(anchors) <= 10)
        self.assertIn("SAMPLE DATA", path.read_text(encoding="utf-8"))

    def test_load_from_disk(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.csv"
            p.write_text(HEADER + "\n" + GOOD + "\n", encoding="utf-8")
            self.assertEqual(load_anchors(p)[0].ticker, "AAA")


if __name__ == "__main__":
    unittest.main()
