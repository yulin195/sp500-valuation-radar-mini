---
inclusion: always
---

# Product — SP500 Valuation Radar Mini

## What it is

An open-source, self-hostable command-line tool that turns a hand-maintained
table of S&P 500 valuation anchors into a daily signal brief:

- Input: an anchor table in CSV (`ticker`, `trigger`, `fair_low`, `fair_high`,
  GICS sector, market-cap tier).
- Prices: the latest completed daily close per ticker from Yahoo Finance
  (public data, no API key).
- Output: each ticker classified into one of four tiers — **red** (close at
  or below trigger), **fair-value zone** (close inside the fair-value range),
  **yellow** (close within 5% above the trigger), **watch** (close within
  20% above the trigger and in no other tier) — rendered as a terminal table
  plus a Markdown brief.

## Who it is for

- Individual investors who track their own valuation anchors and want a
  fast, repeatable morning check instead of eyeballing watchlists.
- Developers interested in a small, fully testable example of spec-driven
  development with Kiro (specs, steering, hooks, property-based tests).

## What it is not

- **Not investment advice.** The tool observes prices against the user's
  own anchors; it recommends nothing and places no orders.
- **Not a portfolio or trading tool.** No holdings, no broker integration,
  no risk gates, no position logic.
- **Not the production system.** The methodology is adapted from the
  author's private production valuation radar, but this repository
  contains only newly written code and clearly labelled **sample** anchors
  — no real positions and no production anchor values.
