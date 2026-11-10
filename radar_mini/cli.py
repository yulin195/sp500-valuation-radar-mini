"""Process boundary: argument parsing, wiring and exit codes.

Exit codes (design.md): 0 ran, 2 input/validation failure, 3 zero tickers
priced (total data failure: no brief is written).
"""

import argparse
import sys
from pathlib import Path
from typing import Sequence

from . import __version__
from .loader import AnchorError, load_anchors
from .prices import Transport, fetch_closes, urllib_transport
from .report import build_report, render_markdown, render_table


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="radar_mini",
        description="Compare your own valuation anchors with the latest "
        "completed daily close. Information aid only; not investment advice.",
    )
    parser.add_argument("--anchors", default="anchors.csv",
                        help="path to the anchor CSV (default: anchors.csv)")
    parser.add_argument("--out", default="brief.md",
                        help="path of the Markdown brief (default: brief.md)")
    parser.add_argument("--version", action="version",
                        version=f"radar_mini {__version__}")
    return parser


def main(argv: Sequence[str] | None = None,
         transport: Transport = urllib_transport,
         now: float | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        anchors = load_anchors(args.anchors)
    except AnchorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    prices = fetch_closes([a.ticker for a in anchors], transport, now)
    report = build_report(anchors, prices)
    if report.priced == 0:
        print(f"error: none of {report.total} anchors could be priced; "
              "no brief written.", file=sys.stderr)
        for ticker, why in report.no_data:
            print(f"  no-data {ticker}: {why}", file=sys.stderr)
        return 3
    print(render_table(report))
    try:
        Path(args.out).write_text(render_markdown(report), encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot write {args.out}: {exc.strerror}", file=sys.stderr)
        return 2
    print(f"\nBrief written to {args.out}")
    return 0
