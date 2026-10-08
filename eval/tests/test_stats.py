import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.stats import _norm_ppf, wilson_interval, compare_sequence_to_isolation


class TestNormPpf(unittest.TestCase):
    """_norm_ppf is checked against well-known published critical values of
    the standard normal distribution (not values I made up)."""

    def test_known_critical_values(self):
        cases = {
            0.95: 1.6448536269514722,   # one-sided 95% / two-sided 90%
            0.975: 1.959963984540054,   # two-sided 95%
            0.995: 2.5758293035489004,  # two-sided 99%
        }
        for p, expected in cases.items():
            with self.subTest(p=p):
                # Acklam's approximation has ~1.15e-9 relative error, so for
                # z in [1.6, 2.6] allow ~3e-9 absolute tolerance (places=8).
                self.assertAlmostEqual(_norm_ppf(p), expected, places=8)

    def test_rejects_out_of_range(self):
        for bad in (0.0, 1.0, -0.1, 1.1):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    _norm_ppf(bad)


class TestWilsonInterval(unittest.TestCase):
    def test_zero_successes_gives_exact_zero_lower_bound(self):
        # Wilson score interval has a closed-form property: with 0
        # successes, the lower bound is exactly 0.
        lower, upper = wilson_interval(0, 20, confidence=0.95)
        self.assertEqual(lower, 0.0)
        self.assertGreater(upper, 0.0)
        self.assertLess(upper, 1.0)

    def test_all_successes_gives_exact_one_upper_bound(self):
        # Symmetric closed-form property: with successes == n, the upper
        # bound is exactly 1.
        lower, upper = wilson_interval(20, 20, confidence=0.95)
        self.assertEqual(upper, 1.0)
        self.assertGreater(lower, 0.0)
        self.assertLess(lower, 1.0)

    def test_n_zero_raises_clear_error(self):
        with self.assertRaises(ValueError) as ctx:
            wilson_interval(0, 0)
        self.assertIn("n > 0", str(ctx.exception))

    def test_successes_greater_than_n_raises(self):
        with self.assertRaises(ValueError):
            wilson_interval(21, 20)

    def test_negative_successes_raises(self):
        with self.assertRaises(ValueError):
            wilson_interval(-1, 20)

    def test_confidence_out_of_range_raises(self):
        for bad in (0.0, 1.0, -0.5, 1.5):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    wilson_interval(10, 20, confidence=bad)

    def test_interval_bounds_ordered_and_contain_point_estimate(self):
        for successes, n in [(1, 20), (5, 20), (10, 20), (19, 20), (1, 1), (0, 1)]:
            with self.subTest(successes=successes, n=n):
                lower, upper = wilson_interval(successes, n)
                self.assertLessEqual(lower, successes / n)
                self.assertLessEqual(successes / n, upper)
                self.assertLessEqual(0.0, lower)
                self.assertLessEqual(upper, 1.0)

    def test_higher_confidence_gives_wider_interval(self):
        lower_90, upper_90 = wilson_interval(10, 20, confidence=0.90)
        lower_99, upper_99 = wilson_interval(10, 20, confidence=0.99)
        self.assertLess(lower_99, lower_90)
        self.assertGreater(upper_99, upper_90)

    # Cross-validated against statsmodels.stats.proportion.proportion_confint
    # (method="wilson") -- see eval/tools/verify_wilson_oneoff.py and
    # docs/evidence-m3.md for the independent comparison run.
    def test_matches_independent_statsmodels_reference(self):
        reference = {
            (17, 20, 0.95): (0.6395811352592431, 0.9476312541037835),
            (0, 20, 0.95): (0.0, 0.16112515805281938),
            (20, 20, 0.95): (0.8388748419471806, 1.0),
            (10, 20, 0.95): (0.2992980081982123, 0.7007019918017877),
        }
        for (successes, n, confidence), expected in reference.items():
            with self.subTest(successes=successes, n=n, confidence=confidence):
                got = wilson_interval(successes, n, confidence)
                self.assertAlmostEqual(got[0], expected[0], places=9)
                self.assertAlmostEqual(got[1], expected[1], places=9)


class TestCompareSequenceToIsolation(unittest.TestCase):
    def test_structured_record_and_summary_text(self):
        record = compare_sequence_to_isolation(17, 20, 0, 20)
        self.assertEqual(record.sequence_successes, 17)
        self.assertEqual(record.sequence_n, 20)
        self.assertEqual(record.isolation_successes, 0)
        self.assertEqual(record.isolation_n, 20)
        self.assertEqual(record.summary, "sequence reproduced 17/20, victim alone 0/20")
        self.assertAlmostEqual(record.sequence_rate, 0.85)
        self.assertAlmostEqual(record.isolation_rate, 0.0)
        self.assertEqual(record.isolation_interval[0], 0.0)

    def test_isolation_n_zero_raises_clear_error(self):
        with self.assertRaises(ValueError):
            compare_sequence_to_isolation(17, 20, 0, 0)

    def test_sequence_n_zero_raises_clear_error(self):
        with self.assertRaises(ValueError):
            compare_sequence_to_isolation(0, 0, 0, 20)


if __name__ == "__main__":
    unittest.main()
