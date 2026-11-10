# How we used Kiro (draft)

_Draft for batch 2; to be finalized in batch 3._

## Disclosure

The valuation methodology in Radar Mini is derived from the author's private
valuation radar. All code in this repository was newly written with Kiro; no
production code, anchor values, positions or credentials are included. The
shipped anchors in `data/anchors.sample.csv` are illustrative sample data.
Radar Mini is an observation aid, not investment advice.

## Spec-driven development

The work was driven by the three files in `.kiro/specs/radar-mini/`:

- `requirements.md` fixed the scope (R1-R6) and the fail-closed behaviour.
- `design.md` fixed the five-layer layout (loader, prices, engine, report,
  cli), the data model and the exit codes.
- `tasks.md` split the build into checkable tasks. Construction ran in two
  batches, each on its own branch and Draft PR: batch 1 (skeleton, anchor
  loader, Yahoo prices, classification engine) and batch 2 (sorting,
  reporting, CLI wiring, hook, MCP server, this write-up).

When the spec and the code disagreed, `tasks.md` acceptance criteria won and
the conflict was recorded in the PR. The one real conflict was the
`classify` signature: the early design used three arguments, tasks.md used
four (`fair_high` added) so that `in_fair_range = fair_low < close <= fair_high`
carries information beyond the primary tier. The design was corrected to match.

## Steering

`.kiro/steering/` holds six always-included files: product scope, tech
constraints, structure, code style, the fail-closed rule and repository
hygiene. They kept every session consistent without restating rules: stdlib
only, completed closes only, no estimated prices, exit code 3 on total data
failure, and no secrets, real data or personal paths in a public repo.

## Agent hook

`.kiro/hooks/test-on-save.json` runs `python -m unittest discover -s tests -t .`
whenever a `.py` file is saved, so regressions in the pure engine or the
fail-closed paths surface immediately.

## MCP use case

`mcp_server.py` is a dependency-free MCP server speaking JSON-RPC over stdio
(`initialize`, `tools/list`, `tools/call`). It exposes `classify_anchor` and
`validate_anchors_csv`, so an agent can sanity-check an anchor idea or a CSV
draft (with row-numbered errors) before it goes into the real file. It is
pure: no network, no file access. A subprocess smoke test covers the round trip.

## Property-based testing

The classification engine is tested for monotonicity (lowering the close never
yields a less severe tier), boundary inclusivity at trigger, fair_low,
trigger*1.05 and trigger*1.20, tier exclusivity and `in_fair_range`
consistency. The build sandbox had no Hypothesis and no package access, so
the properties run over thousands of seeded random cases from the standard
library, plus explicit boundary cases. They can be ported to Hypothesis
unchanged in intent.

## Spec mode vs vibe mode

Vibe mode was quick for exploration and small fixes, but it left decisions
implicit. Spec mode cost some upfront writing and paid it back: acceptance
criteria made each batch checkable, the boundary rules were unambiguous, and
conflicts were found by comparing spec to code instead of by surprise. We used
the spec for anything touching behaviour and vibe-style iteration for
wording, layout and tooling.
