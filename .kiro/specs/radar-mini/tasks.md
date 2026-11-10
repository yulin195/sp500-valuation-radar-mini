# Tasks — SP500 Valuation Radar Mini

Status: draft v1, 2026-11-10. Milestones per PLAN.md: v1 working by end of
November, polish Dec 1–3, submit during the day on Dec 4 (Taipei);
hard deadline Dec 5, 06:00 Taipei.

## 1. Repository bootstrap
- [x] 1.1 Create the public GitHub repository with MIT LICENSE visible in
      the About section; confirm `/.kiro` is not gitignored.
- [x] 1.2 Add `.kiro/steering/` project conventions (code style, fail-closed
      rule, no-secrets rule from requirements R5).
- [x] 1.3 Skeleton package layout from design.md (loader/prices/engine/
      report/cli) with a runnable no-op CLI.

## 2. Anchor loader (R1)
- [x] 2.1 CSV parsing + validation with row-naming errors.
- [x] 2.2 Sample `anchors.csv` with 5–10 large-cap sample anchors, labelled
      as sample data.
- [x] 2.3 Unit tests for every malformed-row case in R1.3.

## 3. Price retrieval (R2)
- [x] 3.1 Yahoo daily-close fetch, latest completed close only.
- [x] 3.2 `no-data` result path + staleness rule; no silent carry-forward.
- [x] 3.3 Unit tests for the fail-closed paths (R2.3–R2.4).

## 4. Classification engine (R3)
- [x] 4.1 Implement `engine.classify` exactly as designed (precedence:
      red > fair > yellow > watch > ok, plus `in_fair_range`).
- [x] 4.2 Property-based tests: monotonicity, boundary inclusivity,
      exclusivity (R6.1).
- [x] 4.3 Sorting + cap-tier tie-break (R4.3) with unit tests.
      (Deferred to batch 2: distance_pct and sorting live in the report
      layer, task 5.)

## 5. Reporting (R4)
- [x] 5.1 Terminal table.
- [x] 5.2 Markdown brief with coverage note and disclaimer.
- [x] 5.3 Golden-file test with fixed closes.

## 6. Kiro showcase pieces (judging: Technological Implementation)
- [x] 6.1 Agent hook: run the test suite on file save.
- [x] 6.2 At least one MCP use case, documented in the write-up.
- [x] 6.3 "How we used Kiro" write-up covering the official directions
      (spec-driven vs vibe, steering, hooks, MCP, property-based testing).

## 7. Submission polish (Dec 1–3)
- [ ] 7.1 README: install, usage, sample output, methodology, disclosure
      that code is newly written and methodology derives from the author's
      private radar; not-investment-advice disclaimer.
- [ ] 7.2 Optional GitHub Pages static demo page (sample brief) to satisfy
      the "running app URL" field.
- [ ] 7.3 Demo video < 3 minutes, public on YouTube, no copyrighted assets,
      showing a real end-to-end run.
- [ ] 7.4 Devpost project page in English; final check against
      rules-digest-2026-11-10.md (re-read the live rules page first).

## 8. Submit (Dec 4, daytime Taipei)
- [ ] 8.1 Submit on Devpost; user confirms at submission time only.
