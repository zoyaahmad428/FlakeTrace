import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.baseline import (
    INFRA,
    MATCH,
    OTHER,
    PASS,
    SYNTHETIC_PREFIX,
    BaselineResult,
    FailureSignature,
    RunOutcome,
    RunTally,
    TestIdentifier,
    classify,
    run_random_order_baseline,
    tally,
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

    def test_shuffle_never_interleaves_two_classes(self):
        """ADR/eval.baseline (2026-10-11): JUnitCore/Surefire run a suite class by class, so
        a proposed order where ClassA#m1, ClassB#m1, ClassA#m2 run in that sequence in one JVM
        is not something runner.order_runner.OrderRunner can actually execute. Each class's
        methods must stay contiguous in every shuffled order, however many methods it has."""
        class_a_1 = TestIdentifier("odfixture.ClassA", "m1")
        class_a_2 = TestIdentifier("odfixture.ClassA", "m2")
        class_a_3 = TestIdentifier("odfixture.ClassA", "m3")
        class_b_1 = TestIdentifier("odfixture.ClassB", "m1")
        class_b_2 = TestIdentifier("odfixture.ClassB", "m2")
        runner = FakeOrderRunner(_victim_always_passes)
        result = run_random_order_baseline(
            runner=runner,
            victim=VICTIM,
            candidates=[class_a_1, class_a_2, class_a_3, class_b_1, class_b_2],
            reference_signature=REFERENCE_SIGNATURE,
            max_runs=30,
            base_seed=0,
        )
        for attempt in result.attempts:
            order = attempt.order
            seen_classes = []
            for t in order:
                if not seen_classes or seen_classes[-1] != t.class_name:
                    # A class reappearing after another class took a turn would mean its
                    # methods got split across two non-contiguous runs -- exactly the
                    # impossible-to-execute order this shuffle must never produce.
                    self.assertNotIn(
                        t.class_name, seen_classes,
                        f"class {t.class_name} split across a non-contiguous run in {order}",
                    )
                    seen_classes.append(t.class_name)

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


# ADR-010 section 1 (W19 step 1, written by M2 for M3, agreed 2026-11-13).
PASSED = RunOutcome(passed=True)
SAME = RunOutcome(False, FailureSignature("java.lang.AssertionError", REFERENCE_SIGNATURE.stack_trace, "other message"))
DIFFERENT = RunOutcome(False, FailureSignature("java.lang.IllegalStateException", "at V.t(V.java:22)"))
CRASH = RunOutcome(False, FailureSignature("flaketrace.JvmCrash", ""))
TIMEOUT = RunOutcome(False, FailureSignature("flaketrace.Timeout", "", "JVM exceeded 120s"))
NOT_EXECUTED = RunOutcome(False, FailureSignature("flaketrace.NotExecuted", "", "ignored or an assumption failed"))


class TestClassify(unittest.TestCase):
    def test_a_pass_is_pass(self):
        self.assertEqual(classify(PASSED, REFERENCE_SIGNATURE), PASS)

    def test_the_reference_failure_is_match_even_with_another_message(self):
        self.assertEqual(classify(SAME, REFERENCE_SIGNATURE), MATCH)

    def test_a_different_real_failure_is_other(self):
        self.assertEqual(classify(DIFFERENT, REFERENCE_SIGNATURE), OTHER)

    def test_crash_timeout_and_not_executed_are_infra(self):
        for outcome in (CRASH, TIMEOUT, NOT_EXECUTED):
            self.assertEqual(classify(outcome, REFERENCE_SIGNATURE), INFRA, outcome)

    def test_pass_and_infra_need_no_reference(self):
        self.assertEqual(classify(PASSED, None), PASS)
        self.assertEqual(classify(CRASH, None), INFRA)

    def test_a_real_failure_without_a_reference_is_refused(self):
        with self.assertRaises(ValueError):
            classify(DIFFERENT, None)

    def test_the_synthetic_prefix_is_the_runners(self):
        self.assertEqual(SYNTHETIC_PREFIX, "flaketrace.")


class TestRunTally(unittest.TestCase):
    def test_counts_that_add_up_are_kept(self):
        t = RunTally(n=20, passed=17, matched=0, other=3, infra=0)
        self.assertEqual((t.n, t.passed, t.matched, t.other, t.infra), (20, 17, 0, 3, 0))

    def test_counts_that_do_not_add_up_are_refused(self):
        with self.assertRaises(ValueError):
            RunTally(n=20, passed=20, matched=1, other=0, infra=0)

    def test_a_negative_count_is_refused(self):
        with self.assertRaises(ValueError):
            RunTally(n=0, passed=1, matched=-1, other=0, infra=0)

    def test_an_empty_tally_is_allowed(self):
        self.assertEqual(RunTally(0, 0, 0, 0, 0).n, 0)


class TestTally(unittest.TestCase):
    def test_counts_each_category_once(self):
        outcomes = [PASSED, PASSED, SAME, DIFFERENT, DIFFERENT, CRASH, TIMEOUT]
        self.assertEqual(tally(outcomes, REFERENCE_SIGNATURE),
                         RunTally(n=7, passed=2, matched=1, other=2, infra=2))

    def test_no_outcomes_is_an_empty_tally(self):
        self.assertEqual(tally([], REFERENCE_SIGNATURE), RunTally(0, 0, 0, 0, 0))

    def test_ft003_alone_runs_failing_differently_are_not_passes(self):
        # The Mid build counted only matching failures, so these 20 runs read as "never failed alone".
        result = tally([DIFFERENT] * 20, REFERENCE_SIGNATURE)
        self.assertEqual((result.passed, result.matched, result.other), (0, 0, 20))


if __name__ == "__main__":
    unittest.main()
