import dataclasses
import unittest

from eval.baseline import FailureSignature, RunOutcome, RunTally, TestIdentifier
from eval.tests.fake_runner import FakeOrderRunner
from runner.deletion import (
    ALONE_CHECK,
    DELETION_RUN,
    INCONCLUSIVE,
    NEEDED,
    NOT_NEEDED,
    NOT_RUN,
    DeletionCheck,
    check_deletions,
    label,
)

P = TestIdentifier("pkg.PTest", "p")
Q = TestIdentifier("pkg.QTest", "q")
R = TestIdentifier("pkg.RTest", "r")
V = TestIdentifier("pkg.VictimTest", "v")
REF = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "expected 0")
PASS = RunOutcome(passed=True)
FAIL = RunOutcome(passed=False, failure_signature=REF)
ALONE_PASSED = RunTally(20, 20, 0, 0, 0)


class TestLabel(unittest.TestCase):
    """ADR-011 section 1, with M3's 0.70 Wilson threshold (Interface 4)."""

    def test_victim_passing_every_run_without_the_test_means_needed(self):
        self.assertEqual(label(RunTally(20, 20, 0, 0, 0), 20), NEEDED)

    def test_failure_still_reproducing_without_the_test_means_not_needed(self):
        self.assertEqual(label(RunTally(20, 0, 20, 0, 0), 20), NOT_NEEDED)
        self.assertEqual(label(RunTally(20, 1, 19, 0, 0), 20), NOT_NEEDED)  # lower bound 0.764

    def test_just_below_the_threshold_is_inconclusive(self):
        self.assertEqual(label(RunTally(20, 2, 18, 0, 0), 20), INCONCLUSIVE)  # lower bound 0.699

    def test_sometimes_failing_failing_differently_or_crashing_is_inconclusive(self):
        self.assertEqual(label(RunTally(20, 11, 9, 0, 0), 20), INCONCLUSIVE)
        self.assertEqual(label(RunTally(20, 0, 0, 20, 0), 20), INCONCLUSIVE)
        self.assertEqual(label(RunTally(20, 19, 0, 0, 1), 20), INCONCLUSIVE)

    def test_deletion_check_has_the_contract_fields_and_is_frozen(self):
        check = DeletionCheck(P, ALONE_PASSED, NEEDED, DELETION_RUN, 1)
        self.assertEqual([f.name for f in dataclasses.fields(DeletionCheck)],
                         ["removed", "runs", "status", "source", "round"])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            check.status = NOT_NEEDED
        self.assertNotEqual(ALONE_CHECK, DELETION_RUN)


def fails_after_any_of(*polluters):
    return FakeOrderRunner(lambda order, test: FAIL if test == V and any(p in order for p in polluters) else PASS)


class TestCheckDeletions(unittest.TestCase):
    def test_one_polluter_reuses_the_alone_tally_and_runs_nothing(self):
        runner = fails_after_any_of(P)
        checks, final = check_deletions(runner, [P], V, REF, 20, ALONE_PASSED)
        self.assertEqual(checks, [DeletionCheck(P, ALONE_PASSED, NEEDED, ALONE_CHECK, 1)])
        self.assertEqual(final, [P])
        self.assertEqual(runner.calls, [])

    def test_one_polluter_whose_victim_failed_alone_differently_is_inconclusive(self):
        alone = RunTally(20, 17, 0, 3, 0)
        checks, final = check_deletions(fails_after_any_of(P), [P], V, REF, 20, alone)
        self.assertEqual(checks, [DeletionCheck(P, alone, INCONCLUSIVE, ALONE_CHECK, 1)])
        self.assertEqual(final, [P])

    def test_not_needed_test_is_dropped_and_the_rest_rechecked(self):
        """ADR-011 T1's shape: P alone is enough, Q was kept by mistake."""
        runner = fails_after_any_of(P)
        checks, final = check_deletions(runner, [P, Q], V, REF, 20, ALONE_PASSED)
        self.assertEqual(checks, [
            DeletionCheck(P, RunTally(20, 20, 0, 0, 0), NEEDED, DELETION_RUN, 1),
            DeletionCheck(Q, RunTally(20, 0, 20, 0, 0), NOT_NEEDED, DELETION_RUN, 1),
            DeletionCheck(P, ALONE_PASSED, NEEDED, ALONE_CHECK, 2),
        ])
        self.assertEqual(final, [P])
        self.assertEqual(len(runner.calls), 40)
        self.assertEqual((runner.calls[0], runner.calls[20]), ([Q, V], [P, V]))

    def test_inconclusive_keeps_both_tests(self):
        """ADR-011 T2: without Q the failure comes back in 9 of 20 runs."""
        seen = []

        def outcome(order, test):
            if test != V:
                return PASS
            if order == [P, V]:
                seen.append(1)
                return FAIL if len(seen) <= 9 else PASS
            return FAIL if P in order and Q in order else PASS
        checks, final = check_deletions(FakeOrderRunner(outcome), [P, Q], V, REF, 20, ALONE_PASSED)
        self.assertEqual([(c.removed, c.status, c.round) for c in checks],
                         [(P, NEEDED, 1), (Q, INCONCLUSIVE, 1)])
        self.assertEqual(checks[1].runs, RunTally(20, 11, 9, 0, 0))
        self.assertEqual(final, [P, Q])

    def test_only_the_first_not_needed_test_is_dropped_per_round(self):
        checks, final = check_deletions(fails_after_any_of(P, Q, R), [P, Q, R], V, REF, 20, ALONE_PASSED)
        self.assertEqual([(c.removed, c.status, c.source, c.round) for c in checks], [
            (P, NOT_NEEDED, DELETION_RUN, 1), (Q, NOT_NEEDED, DELETION_RUN, 1), (R, NOT_NEEDED, DELETION_RUN, 1),
            (Q, NOT_NEEDED, DELETION_RUN, 2), (R, NOT_NEEDED, DELETION_RUN, 2),
            (R, NEEDED, ALONE_CHECK, 3),
        ])
        self.assertEqual(final, [R])


class TestDeletionBudget(unittest.TestCase):
    """Interface 6 B5: a check runs in full or is NOT_RUN; nothing is dropped in a cut round."""

    def test_a_check_that_does_not_fit_is_not_run_and_nothing_is_dropped(self):
        runner, answers = fails_after_any_of(P), iter([True, False])
        checks, final = check_deletions(runner, [P, Q], V, REF, 20, ALONE_PASSED,
                                        can_afford=lambda cost, kept: next(answers))
        self.assertEqual(checks, [DeletionCheck(P, RunTally(20, 20, 0, 0, 0), NEEDED, DELETION_RUN, 1),
                                  DeletionCheck(Q, None, NOT_RUN, DELETION_RUN, 1)])
        self.assertEqual((final, len(runner.calls)), ([P, Q], 20))

    def test_nothing_fits(self):
        runner = fails_after_any_of(P)
        checks, final = check_deletions(runner, [P, Q, R], V, REF, 20, ALONE_PASSED,
                                        can_afford=lambda cost, kept: False)
        self.assertEqual([(c.removed, c.status, c.runs) for c in checks],
                         [(P, NOT_RUN, None), (Q, NOT_RUN, None), (R, NOT_RUN, None)])
        self.assertEqual((final, runner.calls), ([P, Q, R], []))

    def test_the_alone_check_is_free(self):
        checks, final = check_deletions(fails_after_any_of(P), [P], V, REF, 20, ALONE_PASSED,
                                        can_afford=lambda cost, kept: False)
        self.assertEqual(checks, [DeletionCheck(P, ALONE_PASSED, NEEDED, ALONE_CHECK, 1)])

    def test_cost_passed_is_m_times_the_run_length(self):
        asked = []
        check_deletions(fails_after_any_of(P, Q), [P, Q], V, REF, 20, ALONE_PASSED,
                        can_afford=lambda cost, kept: asked.append((cost, kept)) or True)
        self.assertEqual(asked, [(40, 2), (40, 2)])


if __name__ == "__main__":
    unittest.main()
