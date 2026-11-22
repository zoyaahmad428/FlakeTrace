import dataclasses
import json
import tempfile
import unittest
from pathlib import Path

from eval.baseline import FailureSignature, RunOutcome, TestIdentifier
from eval.tests.fake_runner import FakeOrderRunner
from runner.budget import Budget, BudgetAccount, BudgetedRunner, BudgetExhausted
from runner.recording import RecordingRunner

V = TestIdentifier("pkg.VictimTest", "v")
C = [TestIdentifier(f"pkg.C{i}Test", "c") for i in range(10)]
PASS = RunOutcome(passed=True)
FAIL = RunOutcome(passed=False, failure_signature=FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "x"))


def passing():
    return FakeOrderRunner(lambda order, test: PASS)


def ledger(inner, limit=None, seconds=None, n=20, clock=None):
    return BudgetedRunner(inner, Budget(limit, seconds), n, V, **({"clock": clock} if clock else {}))


class TestBudgetedRunner(unittest.TestCase):
    def test_counts_invocations_per_phase_without_a_limit(self):
        runner = ledger(passing())
        runner.step = "reproduce"
        runner.run_ordered([C[0], V])
        runner.step = "alone"
        runner.run_ordered([V])
        runner.run_ordered([V])
        account = runner.account(10)
        self.assertEqual(account.spent, {"reproduce": 2, "shuffle": 0, "alone": 2, "pair": 0, "search": 0,
                                         "minimise": 0, "deletion": 0, "verify": 0})
        self.assertEqual((account.launches, account.exhausted, account.reserve_invocations), (3, False, 60))
        self.assertEqual((account.limit_invocations, account.exhausted_phase), (None, None))

    def test_exploration_run_crossing_the_cap_is_not_started(self):
        fake = passing()
        runner = ledger(fake, limit=63)
        runner.step = "search"
        runner.run_ordered([C[0], V])
        with self.assertRaises(BudgetExhausted) as cut:
            runner.run_ordered([C[1], V])
        self.assertEqual(cut.exception.phase, "search")
        self.assertEqual(len(fake.calls), 1)
        account = runner.account(10)
        self.assertEqual((account.exhausted, account.exhausted_phase, account.spent["search"]), (True, "search", 2))

    def test_a_pair_run_is_exploration(self):
        # W35 (Interface 9 P6): pairs never use the verification reserve.
        fake = passing()
        runner = ledger(fake, limit=63)
        runner.step = "pair"
        runner.run_ordered([C[0], V])
        with self.assertRaises(BudgetExhausted) as cut:
            runner.run_ordered([C[1], V])
        self.assertEqual((cut.exception.phase, runner.account(10).spent["pair"], len(fake.calls)), ("pair", 2, 1))

    def test_seconds_are_measured_per_phase(self):
        # W35 review finding 4: the next: estimate uses the alone runs' own seconds (one-test JVMs, like a pair).
        ticks = iter(range(100))
        runner = ledger(passing(), clock=lambda: float(next(ticks)))
        runner.step = "alone"
        runner.run_ordered([V])
        runner.run_ordered([V])
        self.assertEqual((runner.seconds_in("alone"), runner.seconds_in("pair")), (2.0, 0.0))

    def test_verification_may_use_the_reserve(self):
        fake = passing()
        runner = ledger(fake, limit=63)
        runner.step = "alone"
        for _ in range(60):
            runner.run_ordered([V])
        self.assertEqual(len(fake.calls), 60)
        self.assertFalse(runner.account(0).exhausted)
        self.assertFalse(runner.affords("verify", 4))
        self.assertTrue(runner.affords("verify", 3))
        self.assertEqual(runner.account(0).exhausted_phase, "verify")

    def test_the_first_refusal_names_the_phase(self):
        runner = ledger(passing(), limit=63)
        self.assertFalse(runner.affords("deletion", 100))
        self.assertFalse(runner.affords("verify", 100))
        self.assertEqual(runner.account(0).exhausted_phase, "deletion")

    def test_keep_is_held_back(self):
        runner = ledger(passing(), limit=100)
        self.assertTrue(runner.affords("deletion", 40, keep=60))
        self.assertFalse(runner.affords("deletion", 41, keep=60))

    def test_seconds_stop_exploration_only(self):
        fake = passing()
        runner = ledger(fake, seconds=2.5, clock=lambda: float(len(fake.calls)))
        runner.step = "search"
        for i in range(3):
            runner.run_ordered([C[i], V])
        with self.assertRaises(BudgetExhausted):
            runner.run_ordered([C[3], V])
        runner.step = "verify"
        runner.run_ordered([C[0], V])
        account = runner.account(10)
        self.assertEqual((len(fake.calls), account.exhausted_phase, account.wall_seconds), (4, "search", 4.0))

    def test_refusal_writes_one_budget_stop_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            runner = ledger(RecordingRunner(passing(), path, {}), limit=63)
            runner.step = "search"
            runner.run_ordered([C[0], V])
            with self.assertRaises(BudgetExhausted):
                runner.run_ordered([C[1], V])
            lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([line["type"] for line in lines], ["header", "run", "budget-stop"])
        self.assertEqual(lines[1]["step"], "search")
        self.assertEqual(lines[2], {"type": "budget-stop", "phase": "search", "would_cost": 2, "spent": 2})

    def test_note_and_step_reach_the_recorder(self):
        with tempfile.TemporaryDirectory() as tmp:
            recorder = RecordingRunner(passing(), Path(tmp) / "r.jsonl", {})
            runner = ledger(recorder)
            runner.step = "deletion"
            runner.note = {"removed": "x", "round": 1}
            self.assertEqual((recorder.step, recorder.note), ("deletion", {"removed": "x", "round": 1}))

    def test_affordable_runs(self):
        self.assertEqual(ledger(passing()).affordable_runs(3, 20), 20)
        runner = ledger(passing(), limit=100)
        runner.step = "alone"
        for _ in range(60):
            runner.run_ordered([V])
        self.assertEqual(runner.affordable_runs(3, 20), 13)

    def test_victim_outcomes_and_launches_per_phase(self):
        runner = ledger(FakeOrderRunner(lambda order, test: FAIL if test == V and len(order) == 1 else PASS))
        runner.step = "shuffle"
        runner.run_ordered([C[0], V])
        runner.run_ordered([V])
        self.assertEqual(runner.victim_outcomes("shuffle"), [PASS, FAIL])
        self.assertEqual((runner.launches_in("shuffle"), runner.launches_in("search")), (2, 0))

    def test_account_fields_are_the_contract(self):
        self.assertEqual([f.name for f in dataclasses.fields(BudgetAccount)], [
            "limit_invocations", "limit_seconds", "reserve_invocations", "spent", "launches", "wall_seconds",
            "analysis_seconds", "policy", "exhausted", "exhausted_phase", "candidates_total", "candidates_tried"])
        runner = ledger(passing())
        runner.step = "search"
        for i in range(3):
            runner.run_ordered([C[i], V])
        account = runner.account(10)
        self.assertEqual((account.policy, account.analysis_seconds), ("original", None))
        self.assertEqual((account.candidates_total, account.candidates_tried), (10, 3))


    def test_write_event_forwards_and_the_account_names_the_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            runner = ledger(RecordingRunner(passing(), path, {}))
            runner.write_event({"type": "ranking"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8").splitlines()[-1]), {"type": "ranking"})
        ledger(passing()).write_event({"type": "ranking"})  # no recorder: nothing to write, no error
        account = runner.account(10, policy="ranked", analysis_seconds=2.0)
        self.assertEqual((account.policy, account.analysis_seconds), ("ranked", 2.0))


if __name__ == "__main__":
    unittest.main()
