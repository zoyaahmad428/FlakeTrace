import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.baseline import (
    BaselineResult,
    FailureSignature,
    RunOutcome,
    TestIdentifier,
    run_random_order_baseline,
)
from eval.tests.fake_runner import FakeOrderRunner

POLLUTER = TestIdentifier("odfixture.ConfigPolluterTest", "pollute")
VICTIM = TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode")
NOISE_1 = TestIdentifier("odfixture.MathUtilTest", "addsTwoNumbers")
NOISE_2 = TestIdentifier("odfixture.StringUtilTest", "reversesAString")

REFERENCE_SIGNATURE = FailureSignature(
    exception_type="java.lang.AssertionError",
    stack_trace="at odfixture.ConfigVictimTest.expectsDefaultMode(ConfigVictimTest.java:10)",
    message="expected:<0> but was:<1>",
)


def _victim_fails_iff_polluter_before_it(order, test):
    if test != VICTIM:
        return RunOutcome(passed=True)
    if order.index(POLLUTER) < order.index(VICTIM):
        return RunOutcome(passed=False, failure_signature=REFERENCE_SIGNATURE)
    return RunOutcome(passed=True)


def _victim_always_passes(order, test):
    return RunOutcome(passed=True)


class TestRandomOrderBaseline(unittest.TestCase):
    def test_finds_matching_order_eventually_and_stops_early(self):
        runner = FakeOrderRunner(_victim_fails_iff_polluter_before_it)
        result = run_random_order_baseline(
            runner=runner,
            victim=VICTIM,
            candidates=[POLLUTER, NOISE_1, NOISE_2],
            reference_signature=REFERENCE_SIGNATURE,
            max_runs=200,
            base_seed=0,
        )
        self.assertTrue(result.found)
        self.assertIsNotNone(result.matching_attempt)
        order = result.matching_attempt.order
        self.assertLess(order.index(POLLUTER), order.index(VICTIM))
        # Early stopping: the runner was called exactly once per recorded
        # attempt, not max_runs times.
        self.assertEqual(len(runner.calls), result.runs_attempted)
        self.assertLessEqual(result.runs_attempted, 200)

    def test_records_every_seed_even_when_never_matching(self):
        runner = FakeOrderRunner(_victim_always_passes)
        result = run_random_order_baseline(
            runner=runner,
            victim=VICTIM,
            candidates=[POLLUTER, NOISE_1, NOISE_2],
            reference_signature=REFERENCE_SIGNATURE,
            max_runs=5,
            base_seed=0,
        )
        self.assertFalse(result.found)
        self.assertIsNone(result.matching_attempt)
        self.assertEqual(result.runs_attempted, 5)
        self.assertEqual([a.seed for a in result.attempts], [0, 1, 2, 3, 4])

    def test_deterministic_given_same_seeds(self):
        kwargs = dict(
            victim=VICTIM,
            candidates=[POLLUTER, NOISE_1, NOISE_2],
            reference_signature=REFERENCE_SIGNATURE,
            max_runs=10,
            base_seed=42,
        )
        result_a = run_random_order_baseline(runner=FakeOrderRunner(_victim_always_passes), **kwargs)
        result_b = run_random_order_baseline(runner=FakeOrderRunner(_victim_always_passes), **kwargs)
        self.assertEqual(
            [a.order for a in result_a.attempts],
            [a.order for a in result_b.attempts],
        )

    def test_different_base_seed_gives_different_orders(self):
        kwargs = dict(
            victim=VICTIM,
            candidates=[POLLUTER, NOISE_1, NOISE_2],
            reference_signature=REFERENCE_SIGNATURE,
            max_runs=5,
        )
        result_a = run_random_order_baseline(runner=FakeOrderRunner(_victim_always_passes), base_seed=0, **kwargs)
        result_b = run_random_order_baseline(runner=FakeOrderRunner(_victim_always_passes), base_seed=1000, **kwargs)
        self.assertNotEqual(
            [a.order for a in result_a.attempts],
            [a.order for a in result_b.attempts],
        )

    def test_victim_in_candidates_raises(self):
        runner = FakeOrderRunner(_victim_always_passes)
        with self.assertRaises(ValueError):
            run_random_order_baseline(
                runner=runner,
                victim=VICTIM,
                candidates=[POLLUTER, VICTIM],
                reference_signature=REFERENCE_SIGNATURE,
                max_runs=5,
            )

    def test_max_runs_not_positive_raises(self):
        runner = FakeOrderRunner(_victim_always_passes)
        for bad in (0, -1):
            with self.subTest(max_runs=bad):
                with self.assertRaises(ValueError):
                    run_random_order_baseline(
                        runner=runner,
                        victim=VICTIM,
                        candidates=[POLLUTER],
                        reference_signature=REFERENCE_SIGNATURE,
                        max_runs=bad,
                    )


class TestRunOutcomeValidation(unittest.TestCase):
    def test_passed_with_signature_raises(self):
        with self.assertRaises(ValueError):
            RunOutcome(passed=True, failure_signature=REFERENCE_SIGNATURE)

    def test_failed_without_signature_raises(self):
        with self.assertRaises(ValueError):
            RunOutcome(passed=False, failure_signature=None)


class TestFailureSignatureMatches(unittest.TestCase):
    def test_matches_ignores_message(self):
        a = FailureSignature(exception_type="java.lang.AssertionError", stack_trace="X.java:1", message="expected 0")
        b = FailureSignature(exception_type="java.lang.AssertionError", stack_trace="X.java:1", message="expected 1")
        self.assertTrue(a.matches(b))

    def test_matches_requires_same_stack_trace(self):
        a = FailureSignature(exception_type="java.lang.AssertionError", stack_trace="X.java:1")
        b = FailureSignature(exception_type="java.lang.AssertionError", stack_trace="X.java:2")
        self.assertFalse(a.matches(b))

    def test_matches_requires_same_exception_type(self):
        a = FailureSignature(exception_type="java.lang.AssertionError", stack_trace="X.java:1")
        b = FailureSignature(exception_type="java.lang.NullPointerException", stack_trace="X.java:1")
        self.assertFalse(a.matches(b))


class TestTestIdentifierRoundTrip(unittest.TestCase):
    def test_to_dict_and_from_dict_round_trip(self):
        original = TestIdentifier(class_name="odfixture.ConfigVictimTest", method="expectsDefaultMode")
        round_tripped = TestIdentifier.from_dict(original.to_dict())
        self.assertEqual(original, round_tripped)
        self.assertEqual(original.to_dict(), {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"})


if __name__ == "__main__":
    unittest.main()
