---
inclusion: always
---

# Structure — SP500 Valuation Radar Mini

## Layout (five layers, one responsibility each)

- `loader.py` — parses and validates the anchor CSV; a malformed row
  aborts the run with an error naming the row, and input is never repaired.
- `prices.py` — fetches the latest completed daily close per ticker from
  Yahoo Finance and returns either a dated close or a `no-data` reason.
- `engine.py` — the pure tier-classification function (no I/O, no
  globals); the only place tier precedence lives.
- `report.py` — renders the terminal table and the Markdown brief,
  including the coverage note and the not-investment-advice disclaimer.
- `cli.py` — argument parsing and exit codes; the only layer that talks
  to the process boundary.

Layers depend downward only: `cli` wires `loader` + `prices` into
`engine`, then hands results to `report`. I/O never leaks into `engine`.

## Repository conventions

- `/.kiro` (specs, steering, hooks) is part of the submission: it must be
  committed and must **never** be gitignored.
- **Hygiene red lines** (see `repo-hygiene.md`): no secrets or credential
  files; no real holdings; no production anchor values; no personal
  paths. The shipped `anchors.csv` holds only 5–10 large-cap **sample**
  anchors, labelled as sample data.
- The spec in `.kiro/specs/radar-mini/` is the source of truth for
  behaviour. Changing behaviour means updating requirements/design/tasks
  in the same commit as the code.
