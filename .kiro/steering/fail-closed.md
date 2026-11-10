---
inclusion: always
---

# Fail-closed rule — Radar Mini

Draft v1, 2026-11-10 (task 1.2). This is the project's core safety
convention; it overrides convenience in every conflict.

- Malformed anchor CSV row (missing field, non-numeric or non-positive
  trigger, `fair_low <= trigger`, `fair_high < fair_low`): abort the run
  with an error naming the row. Never skip, repair, or guess (R1.3).
- A ticker whose latest completed daily close cannot be retrieved, or
  whose close is stale, is reported as `no-data` in the brief's coverage
  note and receives no tier (R2.3). Intraday / pre-market quotes never
  count.
- Missing data is never estimated, carried forward silently, or filled
  in by an AI (R2.4).
- A run that prices zero tickers exits with code 3 and writes no brief
  presented as normal (design.md exit codes: 0 ran, 2 input failure,
  3 total data failure).
- A partial run must state its coverage (priced N of M) in the brief;
  it is never presented as an all-clear.
- The tool is an information/observation aid only: no orders, no
  portfolio logic, no investment advice, in code, output, or docs.
