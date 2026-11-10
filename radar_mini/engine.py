"""Pure tier classification (R3). No I/O, no globals."""

from dataclasses import dataclass
from typing import Literal

Tier = Literal["red", "fair", "yellow", "watch", "ok"]


@dataclass(frozen=True)
class Classification:
    tier: Tier
    in_fair_range: bool


def classify(close: float, trigger: float, fair_low: float,
             fair_high: float) -> Classification:
    """Return the single primary tier plus the independent fair-range flag.

    Precedence is fixed: red > fair > yellow > watch > ok. Bounds are
    inclusive exactly as in tasks.md item 4:
      red:    close <= trigger
      fair:   trigger < close <= fair_low
      yellow: close <= trigger * 1.05
      watch:  close <= trigger * 1.20
    in_fair_range is fair_low < close <= fair_high, kept as a separate flag
    so the second dimension survives the single-tier collapse.
    """
    if close <= trigger:
        tier: Tier = "red"
    elif close <= fair_low:
        tier = "fair"
    elif close <= trigger * 1.05:
        tier = "yellow"
    elif close <= trigger * 1.20:
        tier = "watch"
    else:
        tier = "ok"
    return Classification(tier=tier, in_fair_range=fair_low < close <= fair_high)
