import unittest

from eval.baseline import FailureSignature, RunOutcome, TestIdentifier
from eval.tests.fake_runner import FakeOrderRunner
from runner.search import candidate_order, find_polluter, reproduce
from runner.verify import repeat

A = TestIdentifier("pkg.ATest", "a")
B = TestIdentifier("pkg.BTest", "b")
C = TestIdentifier("pkg.CTest", "c")
V = TestIdentifier("pkg.VictimTest", "v")
REF = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "expected 0")
OTHER = FailureSignature("java.lang.NullPointerException", "pkg.VictimTest.v:7", None)
CRASH = FailureSignature("flaketrace.JvmCrash", "", "JVM exited with code 1")
PASS = RunOutcome(passed=True)


def fails(signature):
    return RunOutcome(passed=False, failure_signature=signature)


def victim_fails_after(polluter, signature=REF):
    def outcome(order, test):
        if test == V and polluter in order and order.index(polluter) < order.index(V):
            return fails(signature)
        return PASS
    return outcome


def scripted_victim(outcomes):
    """Victim's outcome on successive calls follows `outcomes`; other tests pass."""
    remaining = list(outcomes)
    return lambda order, test: remaining.pop(0) if test == V else PASS


class TestReproduce(unittest.TestCase):
    def test_first_real_failure_becomes_the_reference(self):
        runner = FakeOrderRunner(scripted_victim([PASS, fails(REF), fails(OTHER)]))
        self.assertEqual(reproduce(runner, [A, V], V, attempts=5), (REF, 2, 1))
        self.assertEqual(len(runner.calls), 2)

    def test_crash_is_never_taken_as_the_reference(self):
        runner = FakeOrderRunner(scripted_victim([fails(CRASH), fails(REF)]))
        self.assertEqual(reproduce(runner, [A, V], V, attempts=5), (REF, 2, 2))

    def test_never_failing_returns_none_after_all_attempts(self):
        runner = FakeOrderRunner(lambda order, test: PASS)
        self.assertEqual(reproduce(runner, [A, V], V, attempts=3), (None, 3, 0))


class TestCandidateOrder(unittest.TestCase):
    def test_original_order_without_priority(self):
        self.assertEqual(candidate_order([A, B, C, V], V), [A, B, C])

    def test_priority_first_then_the_rest_ignoring_unknown_and_later_tests(self):
        later = TestIdentifier("pkg.LaterTest", "l")
        order = [A, B, C, V, later]
        self.assertEqual(candidate_order(order, V, [C, later, C, TestIdentifier("x.Y", "z")]), [C, A, B])


class TestFindPolluter(unittest.TestCase):
    def test_finds_the_polluter_and_counts_runs(self):
        runner = FakeOrderRunner(victim_fails_after(B))
        self.assertEqual(find_polluter(runner, [A, B, C, V], V, REF), (B, 2))
        self.assertEqual(runner.calls, [[A, V], [B, V]])

    def test_priority_is_tried_first(self):
        runner = FakeOrderRunner(victim_fails_after(B))
        self.assertEqual(find_polluter(runner, [A, B, C, V], V, REF, priority=[B]), (B, 1))

    def test_failure_with_a_different_signature_is_not_a_polluter(self):
        runner = FakeOrderRunner(victim_fails_after(A, OTHER))
        self.assertEqual(find_polluter(runner, [A, B, V], V, REF), (None, 2))


class TestRepeat(unittest.TestCase):
    def test_counts_matching_and_any_failures(self):
        runner = FakeOrderRunner(scripted_victim([fails(REF), PASS, fails(OTHER), fails(CRASH), fails(REF)]))
        self.assertEqual(repeat(runner, [A, V], V, REF, 5), (2, 4))
        self.assertEqual(len(runner.calls), 5)


if __name__ == "__main__":
    unittest.main()
