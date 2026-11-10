"""Property-based tests for engine.classify (R6.1).

hypothesis is not installed here and the sandbox cannot download packages,
so the properties run over many random cases from the standard library
`random` module with fixed seeds (reproducible). Boundary values are also
exercised explicitly, since random floats rarely land exactly on them.
"""
import random
import unittest

from radar_mini.engine import classify

SEVERITY = {"red": 4, "fair": 3, "yellow": 2, "watch": 1, "ok": 0}
N = 5000


def cases(seed: int, n: int = N):
    rng = random.Random(seed)
    for _ in range(n):
        trigger = round(rng.uniform(1, 1000), 2)
        fair_low = round(trigger * rng.uniform(1.0001, 2.0), 2)
        if fair_low <= trigger:
            fair_low = round(trigger + 0.01, 2)
        fair_high = round(fair_low * rng.uniform(1.0, 1.8), 2)
        close = round(trigger * rng.uniform(0.3, 2.5), 2)
        yield close, trigger, fair_low, fair_high


class BoundaryTest(unittest.TestCase):
    def test_literal_boundaries(self):
        t, lo, hi = 100.0, 110.0, 130.0
        c = lambda x: classify(x, t, lo, hi)
        self.assertEqual(c(100.0).tier, "red")          # == trigger: red
        self.assertEqual(c(100.01).tier, "fair")         # just above trigger
        self.assertEqual(c(110.0).tier, "fair")          # == fair_low: fair
        self.assertEqual(c(110.01).tier, "watch")        # above fair_low
        self.assertEqual(c(99.0).tier, "red")

    def test_yellow_and_watch_edges_with_low_fair_band(self):
        # fair_low just above trigger so the yellow/watch edges are reachable.
        t, lo, hi = 100.0, 101.0, 102.0
        self.assertEqual(classify(104.99, t, lo, hi).tier, "yellow")
        self.assertEqual(classify(t * 1.05, t, lo, hi).tier, "yellow")
        self.assertEqual(classify(t * 1.05 + 0.01, t, lo, hi).tier, "watch")
        self.assertEqual(classify(t * 1.20, t, lo, hi).tier, "watch")
        self.assertEqual(classify(t * 1.20 + 0.01, t, lo, hi).tier, "ok")

    def test_in_fair_range_edges(self):
        t, lo, hi = 100.0, 110.0, 130.0
        self.assertFalse(classify(110.0, t, lo, hi).in_fair_range)   # == fair_low excluded
        self.assertTrue(classify(110.01, t, lo, hi).in_fair_range)
        self.assertTrue(classify(130.0, t, lo, hi).in_fair_range)    # == fair_high included
        self.assertFalse(classify(130.01, t, lo, hi).in_fair_range)

    def test_in_fair_range_true_while_tier_not_fair(self):
        r = classify(120.0, 100.0, 110.0, 130.0)
        self.assertTrue(r.in_fair_range)
        self.assertNotEqual(r.tier, "fair")

    def test_in_fair_range_with_yellow_tier(self):
        r = classify(104.0, 100.0, 101.0, 110.0)
        self.assertEqual(r.tier, "yellow")
        self.assertTrue(r.in_fair_range)


class PropertyTest(unittest.TestCase):
    def test_tier_matches_literal_spec(self):
        for close, t, lo, hi in cases(1):
            r = classify(close, t, lo, hi)
            if close <= t:
                exp = "red"
            elif t < close <= lo:
                exp = "fair"
            elif close <= t * 1.05:
                exp = "yellow"
            elif close <= t * 1.20:
                exp = "watch"
            else:
                exp = "ok"
            self.assertEqual(r.tier, exp, (close, t, lo, hi))

    def test_exclusivity_single_valid_tier_and_deterministic(self):
        for args in cases(2):
            r = classify(*args)
            self.assertIn(r.tier, SEVERITY)
            self.assertEqual(r, classify(*args))
            self.assertIsInstance(r.in_fair_range, bool)

    def test_monotonicity_lower_close_never_less_severe(self):
        # The dip below fair_low can only move severity up via red/fair, but
        # fair (3) outranks yellow (2) so severity is monotone in close.
        rng = random.Random(3)
        for close, t, lo, hi in cases(4):
            lower = round(close * rng.uniform(0.2, 1.0), 4)
            a = SEVERITY[classify(close, t, lo, hi).tier]
            b = SEVERITY[classify(lower, t, lo, hi).tier]
            self.assertGreaterEqual(b, a, (close, lower, t, lo, hi))

    def test_in_fair_range_consistency(self):
        for close, t, lo, hi in cases(5):
            r = classify(close, t, lo, hi)
            self.assertEqual(r.in_fair_range, lo < close <= hi)
            if r.tier in ("red", "fair"):
                self.assertFalse(r.in_fair_range)   # close <= fair_low there

    def test_boundary_inclusivity_random_anchors(self):
        for _, t, lo, hi in cases(6):
            self.assertEqual(classify(t, t, lo, hi).tier, "red")
            self.assertEqual(classify(lo, t, lo, hi).tier, "fair")
            self.assertFalse(classify(lo, t, lo, hi).in_fair_range)
            self.assertTrue(classify(hi, t, lo, hi).in_fair_range or hi == lo)
            if t * 1.05 > lo:
                self.assertEqual(classify(t * 1.05, t, lo, hi).tier, "yellow")
            if t * 1.20 > lo:
                self.assertIn(classify(t * 1.20, t, lo, hi).tier, ("yellow", "watch"))


if __name__ == "__main__":
    unittest.main()
