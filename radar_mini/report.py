"""Result assembly, ordering and rendering (R4): terminal table + Markdown brief.

No network and no tier logic here; tiers come from engine.classify.
"""

from dataclasses import dataclass
from datetime import date

from .engine import Tier, classify
from .loader import Anchor
from .prices import Close, NoData, PriceResult

TIER_ORDER: tuple[Tier, ...] = ("red", "fair", "yellow", "watch")
TIER_TITLE = {"red": "Red", "fair": "Fair-value zone", "yellow": "Yellow",
              "watch": "Watch"}
CAP_RANK = {"mega": 0, "large": 1, "mid": 2, "small": 3}
TIE_PP = 5.0  # distances within this many percentage points count as equal

DISCLAIMER = ("This brief is an information and observation aid only. It is "
              "not investment advice, places no orders, and makes no "
              "recommendation.")


@dataclass(frozen=True)
class Result:
    ticker: str
    close: float
    close_date: date
    trigger: float
    distance_pct: float
    tier: Tier
    in_fair_range: bool
    sector: str
    cap_tier: str


@dataclass(frozen=True)
class RunReport:
    results: list[Result]       # every priced ticker, any tier (incl. ok)
    priced: int
    total: int
    no_data: list[tuple[str, str]]   # (ticker, reason), sorted by ticker


def build_report(anchors: list[Anchor],
                 prices: dict[str, PriceResult]) -> RunReport:
    results: list[Result] = []
    no_data: list[tuple[str, str]] = []
    for a in anchors:
        p = prices.get(a.ticker)
        if isinstance(p, Close):
            c = classify(p.close, a.trigger, a.fair_low, a.fair_high)
            dist = (p.close - a.trigger) / a.trigger * 100.0
            results.append(Result(a.ticker, p.close, p.date, a.trigger, dist,
                                  c.tier, c.in_fair_range, a.sector, a.cap_tier))
        else:
            reason = p.reason if isinstance(p, NoData) else "no price result"
            no_data.append((a.ticker, reason))
    no_data.sort()
    return RunReport(results, len(results), len(anchors), no_data)


def sort_group(group: list[Result]) -> list[Result]:
    """Distance ascending; near-equal distances ordered by larger cap first.

    'Within 5pp' is not transitive, so a cluster starts at the lowest
    unplaced distance and takes every item within TIE_PP of that anchor
    point; inside a cluster order is cap tier, then distance, then ticker.
    """
    pending = sorted(group, key=lambda r: (r.distance_pct, r.ticker))
    out: list[Result] = []
    while pending:
        base = pending[0].distance_pct
        cluster = [r for r in pending if r.distance_pct - base <= TIE_PP]
        pending = pending[len(cluster):]
        cluster.sort(key=lambda r: (CAP_RANK.get(r.cap_tier, 99),
                                    r.distance_pct, r.ticker))
        out.extend(cluster)
    return out


def grouped(report: RunReport) -> dict[Tier, list[Result]]:
    return {t: sort_group([r for r in report.results if r.tier == t])
            for t in TIER_ORDER}


def _tier_cell(r: Result) -> str:
    return r.tier + ("*" if r.in_fair_range else "")


def _coverage_line(report: RunReport) -> str:
    return f"Priced {report.priced} of {report.total} anchors."


def render_table(report: RunReport) -> str:
    rows = [r for t in TIER_ORDER for r in grouped(report)[t]]
    head = ["Ticker", "Close", "Date", "Trigger", "Dist%", "Tier", "Cap", "Sector"]
    body = [[r.ticker, f"{r.close:.2f}", r.close_date.isoformat(),
             f"{r.trigger:.2f}", f"{r.distance_pct:+.1f}", _tier_cell(r),
             r.cap_tier, r.sector] for r in rows]
    lines: list[str] = []
    if body:
        widths = [max(len(x[i]) for x in [head] + body) for i in range(len(head))]
        fmt = lambda row: "  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip()
        lines += [fmt(head), fmt(["-" * w for w in widths])] + [fmt(b) for b in body]
        lines.append("* = close is inside the fair-value range (fair_low < close <= fair_high)")
    else:
        lines.append("No priced ticker is in a listed tier.")
    lines.append(_coverage_line(report))
    if report.no_data:
        lines.append("no-data: " + ", ".join(f"{t} ({why})" for t, why in report.no_data))
    if report.priced < report.total:
        lines.append("WARNING: partial coverage; this is not an all-clear.")
    lines.append(DISCLAIMER)
    return "\n".join(lines)


def render_markdown(report: RunReport) -> str:
    as_of = max((r.close_date for r in report.results), default=None)
    g = grouped(report)
    out = ["# Radar Mini brief", ""]
    out.append(f"Latest completed close in this run: {as_of.isoformat()}" if as_of else "")
    out += ["", "## Coverage", "", f"- {_coverage_line(report)}"]
    if report.no_data:
        out.append("- no-data (no tier assigned):")
        out += [f"  - {t}: {why}" for t, why in report.no_data]
    else:
        out.append("- no-data: none")
    if report.priced < report.total:
        out.append("- **Partial coverage: this brief is not an all-clear.**")
    for t in TIER_ORDER:
        out += ["", f"## {TIER_TITLE[t]}", ""]
        if not g[t]:
            out.append("_None._")
            continue
        out += ["| Ticker | Close | Date | Trigger | Distance to trigger | In fair range | Cap | Sector |",
                "| --- | --- | --- | --- | ---: | :---: | --- | --- |"]
        out += [f"| {r.ticker} | {r.close:.2f} | {r.close_date.isoformat()} | "
                f"{r.trigger:.2f} | {r.distance_pct:+.1f}% | "
                f"{'yes *' if r.in_fair_range else 'no'} | {r.cap_tier} | {r.sector} |"
                for r in g[t]]
    out += ["", "`*` = close is inside the fair-value range "
            "(fair_low < close <= fair_high), shown even when the headline "
            "tier is different. Tickers in no tier are not listed.",
            "", "## Disclaimer", "", DISCLAIMER, ""]
    return "\n".join(out)
