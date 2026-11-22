import unittest

from eval.baseline import FailureSignature, RunOutcome, RunTally, TestIdentifier
from eval.tests.fake_runner import FakeOrderRunner
from runner.search import candidate_order, find_pair, find_polluter, reproduce
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
    def test_tallies_each_run_once(self):
        runner = FakeOrderRunner(scripted_victim([fails(REF), PASS, fails(OTHER), fails(CRASH), fails(REF)]))
        self.assertEqual(repeat(runner, [A, V], V, REF, 5), RunTally(n=5, passed=1, matched=2, other=1, infra=1))
        self.assertEqual(len(runner.calls), 5)


if __name__ == "__main__":
    unittest.main()


class TestFindPair(unittest.TestCase):
    """W35 (ADR-016, Interface 9 P3): [c, victim] once each; a real failure is adopted only if one re-run of the
    same pair fails again with a matching signature."""

    T = [TestIdentifier(f"pkg.T{i}Test", "t") for i in range(5)]

    def pair_runner(self, script):
        """script[i] = the victim's outcomes after candidate i, consumed per run; default PASS."""
        left = {i: list(outcomes) for i, outcomes in script.items()}

        def outcome(order, test):
            if test != V:
                return PASS
            i = self.T.index(order[0])
            return left[i].pop(0) if left.get(i) else PASS
        return FakeOrderRunner(outcome)

    def test_the_first_pair_failing_twice_is_adopted(self):
        runner = self.pair_runner({3: [fails(REF), fails(REF)]})
        polluter, reference, tried, firsts = find_pair(runner, self.T, V)
        self.assertEqual((polluter, reference, tried, len(firsts)), (self.T[3], REF, 4, 4))
        self.assertEqual(runner.calls[-2:], [[self.T[3], V], [self.T[3], V]])
        self.assertEqual(len(runner.calls), 5)

    def test_a_one_off_failure_is_not_adopted_and_the_scan_goes_on(self):
        runner = self.pair_runner({1: [fails(REF), PASS], 3: [fails(REF), fails(REF)]})
        polluter, reference, tried, _ = find_pair(runner, self.T, V)
        self.assertEqual((polluter, tried, len(runner.calls)), (self.T[3], 4, 6))

    def test_a_crash_is_never_re_run_or_adopted(self):
        runner = self.pair_runner({0: [fails(CRASH)]})
        self.assertEqual(find_pair(runner, self.T, V)[:3], (None, None, 5))
        self.assertEqual(len(runner.calls), 5)

    def test_a_different_signature_on_the_re_run_is_not_adopted(self):
        runner = self.pair_runner({2: [fails(REF), fails(OTHER)]})
        self.assertEqual(find_pair(runner, self.T, V)[:3], (None, None, 5))
        self.assertEqual(len(runner.calls), 6)

    def test_a_polluter_after_the_victim_in_the_discovered_order_is_still_a_candidate(self):
        runner = FakeOrderRunner(victim_fails_after(C))
        self.assertEqual(find_pair(runner, [A, B, C], V)[:3], (C, REF, 3))

    def test_no_candidates(self):
        self.assertEqual(find_pair(FakeOrderRunner(lambda order, test: PASS), [], V), (None, None, 0, []))
