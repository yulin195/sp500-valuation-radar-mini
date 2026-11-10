# Design — SP500 Valuation Radar Mini

Status: draft v1, 2026-11-10. Implements requirements.md (same date).

## Architecture

A single small Python package, three layers, no framework:

```
anchors.csv ──► loader (validate, R1) ──► [Anchor]
                                              │
Yahoo daily closes ──► prices (fetch, R2) ──► {ticker: Close}
                                              │
                                     engine.classify()  ← pure, R3
                                              │
                              ┌───────────────┴───────────────┐
                              ▼                               ▼
                       terminal table                   Markdown brief
```

- `loader.py` — CSV parsing and validation. Raises `AnchorError` naming the
  offending row; never repairs input.
- `prices.py` — Yahoo Finance daily-close fetch (public chart endpoint, no
  key). Returns a result object per ticker: either a dated close or a
  `no-data` reason. Staleness rule: the close's date must be the latest
  completed trading day the endpoint reports; anything else is `no-data`.
- `engine.py` — pure classification (see below). No I/O, no globals, fully
  unit/property-testable.
- `report.py` — terminal table + Markdown rendering, including the coverage
  note (priced N of M) and disclaimer.
- `cli.py` — argument parsing (`--anchors`, `--out`), exit codes:
  0 = ran (any tier outcome), 2 = input/validation failure, 3 = zero tickers
  priced (total data failure — fail closed, no brief written as if normal).

## Classification (R3)

```python
def classify(close: float, trigger: float, fair_low: float) -> Result:
    # Result: tier (primary) + in_fair_range (bool) + distance_pct
    in_fair = trigger < close <= fair_low
    if close <= trigger:            tier = "red"
    elif in_fair:                   tier = "fair"
    elif close <= trigger * 1.05:   tier = "yellow"
    elif close <= trigger * 1.20:   tier = "watch"
    else:                           tier = "ok"
```

Design note — why fair outranks yellow: in the production methodology the
red/yellow zone and the fair-value entry are tracked as two independent
dimensions. Mini collapses them to one primary tier for readability, so the
*stronger* signal (price has actually entered the researched fair-value
range) is the headline, while `in_fair_range` preserves the second dimension
for tickers headlined as yellow or red-adjacent. This is the one deliberate
simplification versus production; it is documented in the README.

## Data model

```text
Anchor   { ticker:str, trigger:float, fair_low:float, fair_high:float,
           sector:str, cap_tier: enum(mega|large|mid|small) }
Close    { ticker:str, date:date, close:float }
Result   { ticker, close, trigger, distance_pct, tier, in_fair_range,
           sector, cap_tier }
RunReport{ results:[Result], priced:int, total:int, no_data:[ticker] }
```

`cap_tier` buckets (USD market cap): mega ≥ 200B, large 50–200B,
mid 10–50B, small < 10B — matching the production brief's labelling.
Sorting: distance_pct ascending; ties within 5pp broken by cap size
(mega > large > mid > small, then by absolute cap if known).

## Error handling

Fail closed everywhere: malformed CSV aborts (R1.3); a ticker without a
 trustworthy close is listed as `no-data`, counted in the coverage note, and
never assigned a tier (R2.3). A run pricing zero tickers exits 3 and writes
no brief.

## Testing strategy

- Property-based tests (Hypothesis) on `engine.classify`: monotonicity in
  close, boundary inclusivity at trigger / fair_low / trigger*1.05 /
  trigger*1.20, tier exclusivity, `in_fair_range` consistency.
- Unit tests: CSV validation cases, no-data path, coverage-note rendering,
  sorting/tie-break.
- One golden-file test: fixed sample anchors + fixed closes → expected
  Markdown brief.

## Kiro usage planned (for the submission write-up)

Spec-driven development from this folder (requirements/design/tasks),
project steering in `.kiro/steering/`, one agent hook (run tests on save),
property-based testing as above. All code in this repo is written fresh for
the hackathon; only the *methodology* carries over from the author's private
production radar, and that is disclosed in the README.
