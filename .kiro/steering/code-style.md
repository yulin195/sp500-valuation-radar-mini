---
inclusion: always
---

# Code style — Radar Mini

Draft v1, 2026-11-10 (task 1.2). Companion files: `fail-closed.md`,
`repo-hygiene.md`.

- Python 3.11+, standard library only for v1. No framework, no ORM, no
  global state.
- Layout follows design.md exactly: `loader.py` (CSV validation),
  `prices.py` (Yahoo daily closes), `engine.py` (pure classification),
  `report.py` (terminal table + Markdown brief), `cli.py` (args, exit
  codes). Do not merge layers or let I/O leak into `engine.py`.
- `engine.classify` stays a pure function of (close, trigger, fair_low).
  Tier precedence is fixed: red > fair-value zone > yellow > watch > ok,
  with `in_fair_range` carried as a separate boolean. Changing precedence
  requires updating design.md, requirements.md (R3) and the README
  disclosure in the same commit.
- Type hints on public functions; `dataclasses` for Anchor / Close /
  Result / RunReport as modelled in design.md.
- Sorting: distance_pct ascending; ties within 5pp broken by cap tier
  (mega > large > mid > small).
- Every behaviour in requirements.md gets a test; the classification
  engine additionally gets property-based tests (R6: monotonicity,
  boundary inclusivity, tier exclusivity).
- Comments explain *why*, not *what*. No commented-out code in commits.
