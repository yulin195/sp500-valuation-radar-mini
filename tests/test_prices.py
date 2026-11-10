"""Price tests use a fake transport only; no real network access."""
import json
import unittest
import urllib.error
from datetime import date, datetime, timezone

from radar_mini.prices import Close, NoData, coverage, fetch_close, fetch_closes

OFFSET = -18000  # US Eastern standard time, as Yahoo reports gmtoffset


def ts(y, m, d, h, mi=0):
    """Local exchange wall-clock time to epoch seconds."""
    return int(datetime(y, m, d, h, mi, tzinfo=timezone.utc).timestamp()) - OFFSET


def body(stamps, closes, start, end):
    return json.dumps({"chart": {"error": None, "result": [{
        "meta": {"gmtoffset": OFFSET,
                 "currentTradingPeriod": {"regular": {"start": start, "end": end}}},
        "timestamp": stamps,
        "indicators": {"quote": [{"close": closes}]},
    }]}}).encode()


# Tue 2026-11-10 session 09:30-16:00 local; prior bars Fri 6th and Mon 9th.
BARS = [ts(2026, 11, 6, 9, 30), ts(2026, 11, 9, 9, 30), ts(2026, 11, 10, 9, 30)]
START, END = BARS[2], ts(2026, 11, 10, 16)
DURING = ts(2026, 11, 10, 12)
AFTER = ts(2026, 11, 10, 17)


def const(data):
    return lambda url: data


def boom(exc):
    def t(url):
        raise exc
    return t


class PricesTest(unittest.TestCase):
    def test_intraday_bar_is_excluded(self):
        b = body(BARS, [100.0, 101.0, 55.5], START, END)
        r = fetch_close("AAA", const(b), now=DURING)
        self.assertEqual(r, Close("AAA", date(2026, 11, 9), 101.0))

    def test_completed_today_bar_is_used_after_close(self):
        b = body(BARS, [100.0, 101.0, 99.5], START, END)
        r = fetch_close("AAA", const(b), now=AFTER)
        self.assertEqual(r, Close("AAA", date(2026, 11, 10), 99.5))

    def test_null_latest_close_is_no_data_not_carried_forward(self):
        b = body(BARS, [100.0, None, 99.5], START, END)
        r = fetch_close("AAA", const(b), now=DURING)
        self.assertIsInstance(r, NoData)

    def test_stale_close_is_no_data(self):
        b = body(BARS[:1], [100.0], START, END)
        r = fetch_close("AAA", const(b), now=ts(2026, 11, 12, 10))
        self.assertIsInstance(r, NoData)
        self.assertIn("stale", r.reason)

    def test_weekend_gap_is_not_stale(self):
        b = body(BARS[:1], [100.0], ts(2026, 11, 9, 9, 30), ts(2026, 11, 9, 16))
        r = fetch_close("AAA", const(b), now=ts(2026, 11, 9, 8))
        self.assertIsInstance(r, Close)

    def test_transport_errors_are_no_data(self):
        for exc in (urllib.error.URLError("down"), TimeoutError(), ConnectionResetError()):
            r = fetch_close("AAA", boom(exc), now=DURING)
            self.assertIsInstance(r, NoData)

    def test_malformed_payloads_are_no_data(self):
        for data in (b"not json", b"{}", b'{"chart":{"result":null}}',
                     b'{"chart":{"result":[]}}',
                     body([], [], START, END),
                     body(BARS, [1.0], START, END),
                     body(BARS, [0, -1, "x"], START, END)):
            self.assertIsInstance(fetch_close("AAA", const(data), now=AFTER), NoData)

    def test_zero_or_negative_close_is_no_data(self):
        b = body(BARS, [100.0, 0, 5], START, END)
        self.assertIsInstance(fetch_close("AAA", const(b), now=DURING), NoData)

    def test_batch_and_coverage_count(self):
        good = body(BARS, [100.0, 101.0, 55.5], START, END)

        def transport(url):
            if "/BAD?" in url:
                raise urllib.error.URLError("nope")
            return good

        res = fetch_closes(["AAA", "BAD", "CCC"], transport, now=DURING)
        self.assertEqual(coverage(res), (2, 3, ["BAD"]))
        self.assertIsInstance(res["BAD"], NoData)

    def test_ticker_is_url_quoted(self):
        seen = []

        def t(url):
            seen.append(url)
            return b"{}"

        fetch_close("A/B&x", t, now=DURING)
        self.assertIn("A%2FB%26x", seen[0])


if __name__ == "__main__":
    unittest.main()
