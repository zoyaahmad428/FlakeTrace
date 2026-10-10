import unittest

from eval.baseline import FailureSignature, RunOutcome, TestIdentifier
from eval.tests.fake_runner import FakeOrderRunner
from runner.minimise import ddmin

V = TestIdentifier("pkg.VictimTest", "v")
REF = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "expected <N>")
PASS = RunOutcome(passed=True)
FAIL = RunOutcome(passed=False, failure_signature=REF)
CRASH = RunOutcome(passed=False, failure_signature=FailureSignature("flaketrace.JvmCrash", "", "code 1"))
OTHER = RunOutcome(passed=False, failure_signature=FailureSignature("java.lang.IllegalStateException", "x:1", "y"))


def tests(count):
    return [TestIdentifier(f"pkg.T{i:03d}Test", "t") for i in range(count)]


def needs(*required):
    """Victim fails iff every `required` test ran before it."""
    return FakeOrderRunner(lambda order, test: FAIL if test == V and all(r in order for r in required) else PASS)


class TestDdmin(unittest.TestCase):
    def test_two_required_polluters_in_twelve_tests_like_f3(self):
        prefix = tests(12)
        runner = needs(prefix[1], prefix[9])
        minimal, runs = ddmin(runner, prefix, V, REF)
        self.assertEqual(minimal, [prefix[1], prefix[9]])
        self.assertEqual(runs, len(runner.calls))
        self.assertGreater(runs, 0)

    def test_three_required_polluters(self):
        prefix = tests(12)
        minimal, _ = ddmin(needs(prefix[0], prefix[5], prefix[11]), prefix, V, REF)
        self.assertEqual(minimal, [prefix[0], prefix[5], prefix[11]])

    def test_polluters_first_and_last(self):
        prefix = tests(9)
        minimal, _ = ddmin(needs(prefix[0], prefix[8]), prefix, V, REF)
        self.assertEqual(minimal, [prefix[0], prefix[8]])

    def test_single_polluter_is_found_too(self):
        prefix = tests(7)
        minimal, _ = ddmin(needs(prefix[4]), prefix, V, REF)
        self.assertEqual(minimal, [prefix[4]])

    def test_crash_or_other_exception_counts_as_not_failing(self):
        prefix = tests(6)
        a, b = prefix[1], prefix[3]

        def outcome(order, test):
            if test != V:
                return PASS
            if a in order and b in order:
                return FAIL
            return CRASH if a in order else OTHER if b in order else PASS
        minimal, _ = ddmin(FakeOrderRunner(outcome), prefix, V, REF)
        self.assertEqual(minimal, [a, b])

    def test_no_subset_is_run_twice_and_the_full_prefix_is_not_rerun(self):
        prefix = tests(10)
        runner = needs(prefix[2], prefix[7])
        ddmin(runner, prefix, V, REF)
        subsets = [tuple(order[:-1]) for order in runner.calls]
        self.assertEqual(len(subsets), len(set(subsets)))
        self.assertNotIn(tuple(prefix), subsets)
        self.assertTrue(all(order[-1] == V for order in runner.calls))

    def test_result_is_one_minimal(self):
        prefix = tests(12)
        required = [prefix[3], prefix[6]]
        minimal, _ = ddmin(needs(*required), prefix, V, REF)
        check = needs(*required)
        for dropped in minimal:
            rest = [t for t in minimal if t != dropped]
            self.assertTrue(check.run_ordered(rest + [V])[V].passed)

    def test_every_run_keeps_the_original_relative_order(self):
        prefix = tests(12)
        runner = needs(prefix[2], prefix[10])
        ddmin(runner, prefix, V, REF)
        for order in runner.calls:
            subset = order[:-1]
            self.assertEqual(subset, sorted(subset, key=prefix.index))

    def test_order_sensitive_polluters_are_found(self):
        prefix = tests(10)
        a, b = prefix[2], prefix[6]
        runner = FakeOrderRunner(lambda order, test: FAIL if test == V and a in order and b in order
                                 and order.index(a) < order.index(b) else PASS)
        minimal, _ = ddmin(runner, prefix, V, REF)
        self.assertEqual(minimal, [a, b])

    def test_long_prefix_needs_few_runs(self):
        prefix = tests(100)
        minimal, runs = ddmin(needs(prefix[13], prefix[77]), prefix, V, REF)
        self.assertEqual(minimal, [prefix[13], prefix[77]])
        self.assertLess(runs, 100)

    def test_single_test_prefix_is_final(self):
        prefix = tests(1)
        runner = needs(prefix[0])
        self.assertEqual(ddmin(runner, prefix, V, REF), (prefix, 0))
        self.assertEqual(runner.calls, [])


if __name__ == "__main__":
    unittest.main()
