"""Yahoo Finance daily-close retrieval (R2).

Fail closed: every ticker yields either a dated completed close or a
no-data reason. Nothing is estimated, filled in, or carried forward, and the
bar for a trading day that is still in progress is never used.
"""

import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Iterable

CHART_URL = ("https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
             "?range=5d&interval=1d")
# Longest normal gap between a completed session and a run (long weekend:
# Thursday close seen on Monday = 4 days). Older than this is stale.
MAX_AGE_DAYS = 4

# A transport maps a URL to the raw response body; injectable for tests.
Transport = Callable[[str], bytes]


@dataclass(frozen=True)
class Close:
    ticker: str
    date: date
    close: float


@dataclass(frozen=True)
class NoData:
    ticker: str
    reason: str


PriceResult = Close | NoData


def urllib_transport(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "radar-mini/0.1"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read()


def parse_chart(ticker: str, body: bytes, now: float) -> PriceResult:
    """Extract the latest completed daily close from a chart API body."""
    try:
        doc = json.loads(body)
        result = doc["chart"]["result"]
        if not result:
            return NoData(ticker, "no result in response")
        r = result[0]
        meta = r["meta"]
        stamps = r["timestamp"]
        closes = r["indicators"]["quote"][0]["close"]
        offset = int(meta.get("gmtoffset", 0))
        period = meta["currentTradingPeriod"]["regular"]
        today_start, today_end = int(period["start"]), int(period["end"])
    except (ValueError, KeyError, IndexError, TypeError):
        return NoData(ticker, "unexpected response format")
    if not stamps or len(stamps) != len(closes):
        return NoData(ticker, "no daily bars")

    # Bars from the current session's start onward belong to today; they
    # count only once the session has ended. Otherwise today's value is a
    # live/intraday quote and must not trigger a tier.
    completed = [(t, c) for t, c in zip(stamps, closes)
                 if t < today_start or now >= today_end]
    if not completed:
        return NoData(ticker, "no completed daily bar")
    ts, close = max(completed, key=lambda tc: tc[0])
    # Deliberately no fallback to an earlier bar when the latest is empty.
    if (isinstance(close, bool) or not isinstance(close, (int, float))
            or not math.isfinite(close) or close <= 0):
        return NoData(ticker, "latest completed close is missing or invalid")

    bar_date = datetime.fromtimestamp(ts + offset, tz=timezone.utc).date()
    today = datetime.fromtimestamp(now + offset, tz=timezone.utc).date()
    if today - bar_date > timedelta(days=MAX_AGE_DAYS):
        return NoData(ticker, f"stale close dated {bar_date.isoformat()}")
    return Close(ticker, bar_date, float(close))


def fetch_close(ticker: str, transport: Transport = urllib_transport,
                now: float | None = None) -> PriceResult:
    """Fetch one ticker; any failure becomes NoData, never an exception."""
    url = CHART_URL.format(symbol=urllib.parse.quote(ticker, safe=""))
    try:
        body = transport(url)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return NoData(ticker, f"fetch failed: {type(exc).__name__}")
    return parse_chart(ticker, body, time.time() if now is None else now)


def fetch_closes(tickers: Iterable[str], transport: Transport = urllib_transport,
                 now: float | None = None) -> dict[str, PriceResult]:
    stamp = time.time() if now is None else now
    return {t: fetch_close(t, transport, stamp) for t in tickers}


def coverage(results: dict[str, PriceResult]) -> tuple[int, int, list[str]]:
    """Return (priced, total, sorted no-data tickers) for the coverage note."""
    no_data = sorted(t for t, r in results.items() if isinstance(r, NoData))
    return len(results) - len(no_data), len(results), no_data
