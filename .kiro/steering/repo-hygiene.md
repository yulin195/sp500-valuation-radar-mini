---
inclusion: always
---

# Repository hygiene — Radar Mini (public repo)

Draft v1, 2026-11-10 (task 1.2, requirements R5).

- This repository is public from day one. Nothing enters it that could
  not be shown to the judges and the public.
- No secrets: no API keys, tokens, passwords, cookies, or credential
  files — the tool needs none (Yahoo fetch is keyless).
- No real data: the production radar's anchor values, positions, and
  account information must never be committed. The shipped
  `anchors.csv` contains only 5–10 clearly labelled **sample** anchors.
- No personal paths, usernames, or machine-specific configuration in
  code, docs, tests, or fixtures.
- `/.kiro` (specs, steering, hooks) must be committed and must NOT be
  gitignored — it is a judged part of the submission.
- A top-level MIT `LICENSE` file is required and must be detectable in
  the GitHub About section.
- All submission-facing text (README, write-up, Devpost page) is in
  English and discloses that the code was written new for this
  hackathon and the methodology derives from the author's private
  valuation radar.
