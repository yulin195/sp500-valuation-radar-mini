# SP500 Valuation Radar Mini

A self-hostable command-line tool that compares your own S&P 500 valuation
anchors against the latest daily close and flags the tickers that have
reached the zones you care about — as a terminal table and a Markdown brief.

## What it does

You maintain a small CSV of **anchors** (ticker, trigger price, fair-value
range, GICS sector, market-cap tier). Radar Mini fetches the latest
completed daily close from Yahoo Finance (no API key needed) and assigns
each ticker a single primary tier:

| Tier | Meaning |
| --- | --- |
| 🔴 **red** | Close is at or below the trigger price |
| 🟢 **fair-value zone** | Close is inside the fair-value range (above the trigger, at or below the range's lower bound) |
| 🟡 **yellow** | Close is within 5% above the trigger |
| 👀 **watch** | Close is within 20% above the trigger and in no other tier |

Tickers in no tier are simply not listed. Each result also carries an
`in_fair_range` flag, because price zone and fair-value entry are two
dimensions in the full methodology (see *Methodology & disclosure* below).

The tool fails closed: a ticker whose close cannot be retrieved is reported
as `no-data`, the brief states how many of the anchors were actually
priced, and no price is ever estimated or filled in.

## Quick start

> _Commands are placeholders — the CLI is under construction for the
> hackathon; this section will be finalized with v1._

```bash
# planned usage
python -m radar_mini --anchors anchors.csv --out brief.md
```

## Sample data

The `anchors.csv` shipped in this repository contains **sample data only**:
5–10 large-cap example anchors with illustrative values, included so the
tool can be run out of the box. They are not the author's real anchors.

## Methodology & disclosure

Radar Mini is adapted from the methodology of a private production
monitoring system the author runs for personal use. All code in this
repository was written fresh for this hackathon (Kiroween 2026); only the
valuation-signal methodology carries over.

One deliberate simplification versus the production system: production
tracks the price zone (red/yellow/watch) and fair-value entry as two
independent dimensions, while Mini reports a single primary tier with
precedence **red > fair-value zone > yellow > watch**, preserving the
second dimension in the `in_fair_range` boolean.

This tool is an information and observation aid. It is **not investment
advice**, and it contains no portfolio data, no orders, and no trading
logic.

## How Kiro was used

_To be completed during the build._ This section will document the
spec-driven workflow behind this repository: the spec in
`.kiro/specs/radar-mini/`, the project steering in `.kiro/steering/`, agent
hooks, an MCP use case, and the property-based tests around the
classification engine.

## License

MIT — see [LICENSE](LICENSE).
