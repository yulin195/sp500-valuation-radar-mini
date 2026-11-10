"""Process boundary: argument parsing and exit codes.

Batch 1 ships a no-op entry point; wiring loader/prices/engine/report
together (and exit codes 2/3) belongs to later tasks.
"""

import argparse
from typing import Sequence

from . import __version__


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


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    print(f"radar_mini {__version__}")
    parser.print_usage()
    print("Nothing to do yet: the pipeline is not wired in this build.")
    return 0
