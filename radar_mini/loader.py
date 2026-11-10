"""Anchor CSV parsing and validation (R1).

Fail closed: any malformed row raises AnchorError naming the file line;
nothing is skipped, defaulted or repaired. Lines whose first character is
'#' are comments (used to label sample data) and blank lines are ignored;
every other line must be a valid anchor row.
"""

import csv
import math
from dataclasses import dataclass
from pathlib import Path

FIELDS = ("ticker", "trigger", "fair_low", "fair_high", "sector", "cap_tier")
CAP_TIERS = ("mega", "large", "mid", "small")


class AnchorError(ValueError):
    """Raised when the anchor CSV is malformed."""


@dataclass(frozen=True)
class Anchor:
    ticker: str
    trigger: float
    fair_low: float
    fair_high: float
    sector: str
    cap_tier: str


def _number(raw: str, name: str, where: str) -> float:
    try:
        value = float(raw)
    except ValueError:
        raise AnchorError(f"{where}: {name} is not numeric: {raw!r}") from None
    if not math.isfinite(value):
        raise AnchorError(f"{where}: {name} is not a finite number: {raw!r}")
    return value


def parse_anchors(lines: list[str], source: str = "<anchors>") -> list[Anchor]:
    """Parse and validate CSV text lines; raise AnchorError on any bad row."""
    anchors: list[Anchor] = []
    seen: dict[str, int] = {}
    header_seen = False
    reader = csv.reader(lines)
    for row in reader:
        lineno = reader.line_num
        where = f"{source}, line {lineno}"
        if not row or all(c.strip() == "" for c in row):
            continue
        if row[0].lstrip().startswith("#"):
            continue
        if not header_seen:
            if tuple(c.strip() for c in row) != FIELDS:
                raise AnchorError(
                    f"{where}: header must be exactly {','.join(FIELDS)}")
            header_seen = True
            continue
        if len(row) != len(FIELDS):
            raise AnchorError(
                f"{where}: expected {len(FIELDS)} fields, got {len(row)}")
        cells = [c.strip() for c in row]
        for name, cell in zip(FIELDS, cells):
            if cell == "":
                raise AnchorError(f"{where}: missing field {name}")
        ticker, sector, cap_tier = cells[0].upper(), cells[4], cells[5]
        trigger = _number(cells[1], "trigger", where)
        fair_low = _number(cells[2], "fair_low", where)
        fair_high = _number(cells[3], "fair_high", where)
        if trigger <= 0:
            raise AnchorError(f"{where}: trigger must be positive: {trigger}")
        if fair_low <= trigger:
            raise AnchorError(
                f"{where}: fair_low ({fair_low}) must be > trigger ({trigger})")
        if fair_high < fair_low:
            raise AnchorError(
                f"{where}: fair_high ({fair_high}) must be >= fair_low ({fair_low})")
        if cap_tier not in CAP_TIERS:
            raise AnchorError(
                f"{where}: cap_tier must be one of {', '.join(CAP_TIERS)}: {cap_tier!r}")
        if ticker in seen:
            raise AnchorError(
                f"{where}: duplicate ticker {ticker} (first on line {seen[ticker]})")
        seen[ticker] = lineno
        anchors.append(Anchor(ticker, trigger, fair_low, fair_high, sector, cap_tier))
    if not header_seen:
        raise AnchorError(f"{source}: no header row found")
    if not anchors:
        raise AnchorError(f"{source}: no anchor rows found")
    return anchors


def load_anchors(path: str | Path) -> list[Anchor]:
    """Read and validate the anchor CSV at path."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise AnchorError(f"{p}: cannot read anchor file: {exc.strerror}") from None
    return parse_anchors(text.splitlines(), source=p.name)
