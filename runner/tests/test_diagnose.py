import json
from dataclasses import replace
import os
import platform
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from eval.baseline import FailureSignature, RunOutcome, RunTally, TestIdentifier
from eval.tests.fake_runner import FakeOrderRunner
from runner.budget import Budget
from runner.policy import SearchPolicy
from runner.tests.test_policy import FakeRanker
from runner.deletion import ALONE_CHECK, DELETION_RUN, NEEDED, NOT_NEEDED, NOT_RUN
from runner.discovery import DEFAULT_SELECTION, DiscoveryConfigError
from runner.recording import RecordingRunner
from runner.diagnose import (
    BUDGET_EXHAUSTED,
    INCONSISTENT,
    NOT_REPRODUCED,
    POLLUTER_FOUND,
    VICTIM_FAILS_ALONE,
    DiagnoseInputError,
    diagnose,
    environment,
    maven_version,
    run_steps,
    tool_environment,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "od-fixture"

A = TestIdentifier("pkg.ATest", "a")
B = TestIdentifier("pkg.BTest", "b")
V = TestIdentifier("pkg.VictimTest", "v")
LATER = TestIdentifier("pkg.ZTest", "z")
REF = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "expected 0")
PASS = RunOutcome(passed=True)
FAIL = RunOutcome(passed=False, failure_signature=REF)


def victim_fails_when(condition):
    return FakeOrderRunner(lambda order, test: FAIL if test == V and condition(order) else PASS)


class TestRunSteps(unittest.TestCase):
    def test_single_polluter_found_and_verified(self):
        runner = victim_fails_when(lambda order: B in order)
        runs = run_steps(runner, [A, B, V, LATER], V, n=4)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.original_order, [A, B, V])
        self.assertEqual(runs.reference_signature, REF)
        self.assertEqual(runs.polluters, [B])
        self.assertEqual(runs.sequence, [B, V])
        self.assertEqual((runs.sequence_tally.n, runs.sequence_tally.matched, (runs.sequence_tally.n - runs.sequence_tally.passed)), (4, 4, 4))
        self.assertEqual((runs.alone_tally.n, runs.alone_tally.matched), (4, 0))
        self.assertEqual(runs.search_runs, 2)
        self.assertEqual(len(runner.calls), 1 + 4 + 2 + 4)

    def test_victim_failing_alone_stops_before_the_search(self):
        runner = victim_fails_when(lambda order: True)
        runs = run_steps(runner, [A, V], V, n=3)
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertEqual((runs.polluters, runs.sequence), ([], [V]))
        self.assertEqual((runs.sequence_tally.n, runs.sequence_tally.matched, (runs.sequence_tally.n - runs.sequence_tally.passed)), (3, 3, 3))
        self.assertEqual((runs.alone_tally.n, runs.alone_tally.matched, runs.search_runs), (3, 3, 0))
        self.assertEqual(len(runner.calls), 1 + 3)

    def test_two_polluters_needed_are_minimised_and_verified(self):
        runner = victim_fails_when(lambda order: A in order and B in order)
        runs = run_steps(runner, [A, B, V], V, n=2)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual((runs.polluters, runs.sequence), ([A, B], [A, B, V]))
        self.assertEqual((runs.sequence_tally.n, runs.sequence_tally.matched), (2, 2))
        self.assertEqual((runs.alone_tally.n, runs.alone_tally.matched, runs.search_runs, runs.minimise_runs), (2, 0, 2, 3))
        self.assertEqual(len(runner.calls), 1 + 2 + 2 + (1 + 2) + 2 * 2 + 2)  # ..., deletion checks (W20), verify

    def test_flaky_failure_is_not_blamed_on_the_whole_prefix(self):
        # The victim fails only in the very first run (the reproduce step), never again.
        calls = []
        runner = FakeOrderRunner(lambda order, test: (calls.append(1) or FAIL) if test == V and not calls else PASS)
        runs = run_steps(runner, [A, B, LATER, V], V, n=2)
        self.assertEqual(runs.status, INCONSISTENT)
        self.assertEqual(runs.polluters, [])
        self.assertEqual(runs.minimise_runs, 1)

    def test_one_test_prefix_that_passed_in_the_search_blames_nothing(self):
        calls = []
        runner = FakeOrderRunner(lambda order, test: (calls.append(1) or FAIL) if test == V and not calls else PASS)
        runs = run_steps(runner, [A, V], V, n=2)
        self.assertEqual(runs.status, INCONSISTENT)
        self.assertEqual((runs.polluters, runs.minimise_runs), ([], 0))

    def test_minimise_runs_are_recorded_as_their_own_step(self):
        record = Path(tempfile.mkdtemp(prefix="flaketrace-rec-")) / "r.jsonl"
        runner = RecordingRunner(victim_fails_when(lambda order: A in order and B in order), record, {})
        run_steps(runner, [A, LATER, B, V], V, n=1)
        lines = [json.loads(line) for line in record.read_text(encoding="utf-8").splitlines()[1:]]
        steps = [line["step"] for line in lines if line["type"] == "run"]  # W25 adds a ranking line
        self.assertIn("minimise", steps)
        self.assertEqual(steps.index("minimise"), steps.index("search") + steps.count("search"))

    def test_single_polluter_does_not_minimise(self):
        runs = run_steps(victim_fails_when(lambda order: B in order), [A, B, V], V, n=2)
        self.assertEqual(runs.minimise_runs, 0)

    def test_never_failing_without_shuffles_runs_reproduce_and_alone_only(self):
        runner = victim_fails_when(lambda order: False)
        runs = run_steps(runner, [A, V], V, n=3)
        self.assertEqual(runs.status, NOT_REPRODUCED)
        self.assertIsNone(runs.reference_signature)
        self.assertEqual((runs.sequence, runs.sequence_tally.n, runs.sequence_tally.matched), ([A, V], 3, 0))
        self.assertEqual((runs.alone_tally.n, runs.alone_tally.matched, runs.search_runs), (3, 0, 0))
        self.assertEqual(len(runner.calls), 3 + 3)

    def test_shuffle_finds_an_order_the_starting_order_could_not(self):
        # Victim fails only when LATER ran before it; the starting order puts LATER after it.
        runner = victim_fails_when(lambda order: LATER in order[: order.index(V)])
        runs = run_steps(runner, [A, V, LATER], V, n=2, shuffles=31)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.polluters, [LATER])
        self.assertIsNotNone(runs.reproducing_seed)
        self.assertEqual(runs.original_order[-1], V)
        self.assertIn(LATER, runs.original_order)
        self.assertGreater(runs.shuffled_orders, 0)

    def test_nothing_fails_anywhere_is_not_reproduced_with_all_counts(self):
        runs = run_steps(victim_fails_when(lambda order: False), [A, B, V], V, n=3, shuffles=31)
        self.assertEqual(runs.status, NOT_REPRODUCED)
        self.assertIsNone(runs.reference_signature)
        self.assertEqual((runs.sequence_tally.n, runs.alone_tally.n, runs.alone_tally.matched), (3, 3, 0))
        # Cut orders of three one-method classes: [V], [A,V], [B,V], [A,B,V], [B,A,V]; the starting
        # order [A,B,V] already ran, so 4 are new.
        self.assertEqual(runs.shuffled_orders, 4)
        self.assertTrue(runs.orders_exhausted)

    def test_failing_alone_without_a_reference_is_victim_fails_alone(self):
        runner = FakeOrderRunner(lambda order, test: FAIL if test == V and order == [V] else PASS)
        runs = run_steps(runner, [A, V], V, n=3, shuffles=0)
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertEqual(runs.reference_signature, REF)
        self.assertEqual((runs.alone_tally.n, runs.alone_tally.matched), (3, 3))
        # The only order that failed is the victim alone; the starting order never did.
        self.assertEqual(runs.original_order, [V])

    def test_crash_only_alone_and_shuffles_are_counted_not_called_never_failed(self):
        timeout = RunOutcome(passed=False, failure_signature=FailureSignature("flaketrace.Timeout", "", "120s"))
        crash = RunOutcome(passed=False, failure_signature=FailureSignature("flaketrace.JvmCrash", "", "code 1"))
        def outcome(order, test):
            if test != V or order == [A, B, V]:
                return PASS
            return timeout if order == [V] else crash
        runs = run_steps(FakeOrderRunner(outcome), [A, B, V], V, n=3, shuffles=31)
        self.assertEqual(runs.status, NOT_REPRODUCED)
        self.assertEqual(runs.infrastructure_failures, 0)
        self.assertEqual(runs.shuffle_infrastructure_failures, runs.shuffled_orders)
        self.assertEqual(runs.alone_infrastructure_failures, 3)

    def test_unknown_test_in_a_given_order_is_refused_and_says_why(self):
        project = Path(tempfile.mkdtemp(prefix="flaketrace-project-"))
        with mock.patch("runner.diagnose.maven_test_classpath", return_value=[]), \
                mock.patch("runner.diagnose.OrderRunner"), \
                mock.patch("runner.diagnose.project_selection", return_value=DEFAULT_SELECTION), \
                mock.patch("runner.diagnose.discover_order", return_value=[A, V]):
            with self.assertRaises(DiagnoseInputError) as raised:
                diagnose(project, V, original_order=[LATER, A, V], record_dir=tempfile.mkdtemp())
        self.assertIn("1 test(s)", str(raised.exception))
        self.assertIn(str(LATER), str(raised.exception))
        self.assertIn("Surefire", str(raised.exception))

    def test_unsupported_surefire_setting_is_an_input_error(self):
        project = Path(tempfile.mkdtemp(prefix="flaketrace-project-"))
        refused = DiscoveryConfigError("the project's Surefire configuration sets <test>")
        with mock.patch("runner.diagnose.maven_test_classpath", return_value=[]), \
                mock.patch("runner.diagnose.OrderRunner"), \
                mock.patch("runner.diagnose.project_selection", side_effect=refused):
            with self.assertRaises(DiagnoseInputError) as raised:
                diagnose(project, V, record_dir=tempfile.mkdtemp())
        self.assertIn("<test>", str(raised.exception))

    def test_crash_only_not_reproduced_counts_infrastructure_failures(self):
        crash = RunOutcome(passed=False, failure_signature=FailureSignature("flaketrace.JvmCrash", "", "code 1"))
        runner = FakeOrderRunner(lambda order, test: crash if test == V and order != [V] else PASS)
        runs = run_steps(runner, [A, V], V, n=3, shuffles=0)
        self.assertEqual(runs.status, NOT_REPRODUCED)
        self.assertEqual(((runs.sequence_tally.n - runs.sequence_tally.passed), runs.infrastructure_failures), (3, 3))

    def test_zero_shuffles_skips_the_phase(self):
        runner = victim_fails_when(lambda order: False)
        runs = run_steps(runner, [A, B, V], V, n=2, shuffles=0)
        self.assertEqual((runs.status, runs.shuffled_orders), (NOT_REPRODUCED, 0))
        self.assertEqual(len(runner.calls), 2 + 2)

    def test_shuffle_runs_record_their_seed(self):
        record = Path(tempfile.mkdtemp(prefix="flaketrace-rec-")) / "r.jsonl"
        runner = RecordingRunner(victim_fails_when(lambda order: False), record, {})
        run_steps(runner, [A, B, V], V, n=1, shuffles=5, seed_base=40)
        lines = [json.loads(l) for l in record.read_text(encoding="utf-8").splitlines()[1:]]
        shuffles = [l for l in lines if l["step"] == "shuffle"]
        self.assertTrue(shuffles and all(isinstance(l["seed"], int) and l["seed"] >= 40 for l in shuffles))
        self.assertTrue(all("seed" not in l for l in lines if l["step"] != "shuffle"))

    def test_given_order_with_a_duplicate_is_refused_before_maven_runs(self):
        with self.assertRaises(DiagnoseInputError):
            diagnose(Path("does-not-exist"), V, original_order=[A, A, V])

    def test_bad_input_is_rejected_before_any_run(self):
        runner = victim_fails_when(lambda order: True)
        with self.assertRaises(DiagnoseInputError):
            run_steps(runner, [A, B], V, n=3)
        with self.assertRaises(DiagnoseInputError):
            run_steps(runner, [A, V], V, n=0)
        self.assertEqual(runner.calls, [])

    def test_victim_first_in_order_has_no_candidates(self):
        outcomes = [FAIL] + [PASS] * 10
        runner = FakeOrderRunner(lambda order, test: outcomes.pop(0))
        runs = run_steps(runner, [V, A], V, n=2)
        self.assertEqual(runs.status, INCONSISTENT)
        self.assertEqual((runs.search_runs, runs.sequence), (0, [V]))

    def test_explicit_order_without_the_victim_fails_before_maven_runs(self):
        with self.assertRaises(DiagnoseInputError):
            diagnose(Path("does-not-exist"), V, original_order=[A, B])

    def test_record_folder_inside_the_project_is_refused_before_maven_runs(self):
        project = Path(tempfile.mkdtemp(prefix="flaketrace-project-"))
        with self.assertRaises(DiagnoseInputError):
            diagnose(project, V, original_order=[V], record_dir=project / "records")

    def test_record_folder_inside_the_original_of_a_copy_is_refused_before_maven_runs(self):
        original = Path(tempfile.mkdtemp(prefix="flaketrace-original-"))
        copy = Path(tempfile.mkdtemp(prefix="flaketrace-copy-"))
        with self.assertRaises(DiagnoseInputError):
            diagnose(copy, V, original_order=[V], record_dir=original / "records", origin=original)

    def test_record_folder_that_is_a_file_is_refused_before_maven_runs(self):
        project = Path(tempfile.mkdtemp(prefix="flaketrace-project-"))
        a_file = Path(tempfile.mkdtemp(prefix="flaketrace-records-")) / "records.txt"
        a_file.write_text("not a folder", encoding="utf-8")
        with self.assertRaises(DiagnoseInputError):
            diagnose(project, V, original_order=[V], record_dir=a_file)

    def test_crash_only_original_order_counts_as_failed_but_not_reproduced(self):
        crash = RunOutcome(passed=False, failure_signature=FailureSignature("flaketrace.JvmCrash", "", "code 1"))
        runner = FakeOrderRunner(lambda order, test: crash if test == V else PASS)
        runs = run_steps(runner, [A, V], V, n=3)
        self.assertEqual(runs.status, NOT_REPRODUCED)
        self.assertEqual((runs.sequence_tally.n, runs.sequence_tally.matched, (runs.sequence_tally.n - runs.sequence_tally.passed)), (3, 0, 3))
        self.assertEqual(runs.infrastructure_failures, 3)


# ADR-010 tests T1-T4 at the runner level (W18). The verdicts they lead to are M3's decide() (W19).
P = TestIdentifier("pkg.PolluterTest", "p")
SIG_A = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:10", "after P")
SIG_B = FailureSignature("java.lang.IllegalStateException", "pkg.VictimTest.v:22", "alone")
TIMEOUT = RunOutcome(False, FailureSignature("flaketrace.Timeout", "", "JVM exceeded 120s"))


def scripted(alone_outcomes):
    """The victim fails with A after P; run alone, it returns `alone_outcomes` in turn (then passes)."""
    alone = list(alone_outcomes)

    def outcome(order, test):
        if test != V:
            return PASS
        if P in order:
            return RunOutcome(False, SIG_A)
        if order == [V]:
            return alone.pop(0) if alone else PASS
        return PASS
    return FakeOrderRunner(outcome)


class TestTallies(unittest.TestCase):
    def test_t1_victim_failing_alone_differently_is_counted_as_other(self):
        runs = run_steps(scripted([RunOutcome(False, SIG_B)] * 20), [P, V], V, n=20)
        self.assertEqual(runs.alone_tally, RunTally(n=20, passed=0, matched=0, other=20, infra=0))
        self.assertEqual(runs.sequence_tally, RunTally(n=20, passed=0, matched=20, other=0, infra=0))

    def test_t2_three_different_failures_in_twenty_alone_runs(self):
        runs = run_steps(scripted([RunOutcome(False, SIG_B)] * 3), [P, V], V, n=20)
        self.assertEqual(runs.alone_tally, RunTally(n=20, passed=17, matched=0, other=3, infra=0))

    def test_t3_two_timeouts_alone_are_infra_not_passes(self):
        runs = run_steps(scripted([TIMEOUT] * 2), [P, V], V, n=20)
        self.assertEqual(runs.alone_tally, RunTally(n=20, passed=18, matched=0, other=0, infra=2))

    def test_t4_a_failure_seen_once_and_never_again_is_inconsistent(self):
        calls = []
        runner = FakeOrderRunner(lambda order, test: (calls.append(1) or FAIL) if test == V and not calls else PASS)
        runs = run_steps(runner, [A, B, LATER, V], V, n=2)
        self.assertEqual(runs.status, "INCONSISTENT")
        self.assertEqual(runs.polluters, [])

    def test_old_count_fields_and_alias_are_gone(self):
        """A4 (2026-11-20, M3 agreed): eval/ reads the tallies since W19, so the five count fields
        that duplicated them, and the NO_SINGLE_POLLUTER alias, are removed."""
        import dataclasses
        import runner.diagnose as module
        names = {f.name for f in dataclasses.fields(module.DiagnosisRuns)}
        old = {"sequence_n", "sequence_successes", "sequence_any_failures", "alone_n", "alone_successes"}
        self.assertEqual(names & old, set())
        self.assertFalse(hasattr(module, "NO_SINGLE_POLLUTER"))
        runs = run_steps(scripted([RunOutcome(False, SIG_B)] * 3 + [TIMEOUT]), [P, V], V, n=20)
        self.assertIsInstance(runs.alone_tally, RunTally)
        self.assertIsInstance(runs.sequence_tally, RunTally)

    def test_victim_failing_alone_has_an_alone_tally(self):
        runs = run_steps(victim_fails_when(lambda order: True), [A, V], V, n=3)
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertEqual(runs.alone_tally, RunTally(3, 0, 3, 0, 0))

    def test_failing_alone_without_a_reference_tallies_against_the_first_real_failure(self):
        outcomes = [TIMEOUT, RunOutcome(False, SIG_B), RunOutcome(False, SIG_A), PASS]
        runner = FakeOrderRunner(lambda order, test: outcomes.pop(0) if test == V and order == [V] else PASS)
        runs = run_steps(runner, [A, V], V, n=4)  # [A, V] always passes; only the alone runs fail
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertEqual(runs.reference_signature, SIG_B)
        self.assertEqual(runs.alone_tally, RunTally(4, 1, 1, 1, 1))

    def test_not_reproduced_tallies_only_passes_and_crashes(self):
        crash = RunOutcome(False, FailureSignature("flaketrace.JvmCrash", "", "code 1"))
        runner = FakeOrderRunner(lambda order, test: crash if test == V and order == [V] else PASS)
        runs = run_steps(runner, [A, V], V, n=3)
        self.assertEqual(runs.status, NOT_REPRODUCED)
        self.assertEqual(runs.sequence_tally, RunTally(3, 3, 0, 0, 0))
        self.assertEqual(runs.alone_tally, RunTally(3, 0, 0, 0, 3))


Q = TestIdentifier("pkg.QTest", "q")


class TestDeletionChecks(unittest.TestCase):
    """W20, ADR-011: every kept test is checked by repeated removal."""

    def test_ft004_counterexample_drops_the_unneeded_test(self):
        """ADR-011 T1, the FT004 probe of 2026-11-13 (evidence-m2): P alone is enough, but [P, V]
        passes its first two runs (the search's and ddmin's single trials) and fails after."""
        trials = []

        def outcome(order, test):
            if test != V:
                return PASS
            before = order[:-1]
            if P in before and Q in before:
                return FAIL
            if before == [P]:
                trials.append(1)
                return FAIL if len(trials) > 2 else PASS
            return PASS
        runner = FakeOrderRunner(outcome)
        runs = run_steps(runner, [P, Q, V], V, n=20)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.polluters, [P])
        self.assertEqual(runner.calls[-20:], [[P, V]] * 20)  # the final set is verified, not ddmin's
        self.assertEqual(runs.sequence, [P, V])
        self.assertEqual(runs.sequence_tally, RunTally(20, 0, 20, 0, 0))
        self.assertEqual([(c.removed, c.status, c.source, c.round) for c in runs.deletion_checks],
                         [(P, NEEDED, DELETION_RUN, 1), (Q, NOT_NEEDED, DELETION_RUN, 1), (P, NEEDED, ALONE_CHECK, 2)])

    def test_other_statuses_have_no_deletion_checks(self):
        calls = []
        inconsistent = FakeOrderRunner(lambda order, test: (calls.append(1) or FAIL) if test == V and not calls else PASS)
        for runner, order in ((victim_fails_when(lambda order: True), [A, V]),
                              (victim_fails_when(lambda order: False), [A, V]),
                              (inconsistent, [A, B, LATER, V])):
            with mock.patch("runner.diagnose.check_deletions") as check:
                runs = run_steps(runner, order, V, n=2)
            self.assertNotEqual(runs.status, POLLUTER_FOUND)
            self.assertEqual(runs.deletion_checks, [])
            check.assert_not_called()

    def test_deletion_runs_are_recorded_as_their_own_step(self):
        record = Path(tempfile.mkdtemp(prefix="flaketrace-rec-")) / "r.jsonl"
        runner = RecordingRunner(victim_fails_when(lambda order: A in order and B in order), record, {})
        run_steps(runner, [A, LATER, B, V], V, n=1)
        lines = [line for line in (json.loads(x) for x in record.read_text(encoding="utf-8").splitlines()[1:])
                 if line["type"] == "run"]  # W25 adds a ranking line
        steps = [line["step"] for line in lines]
        # ADR-011 "Consequences": step `deletion`, with the removed test, so ADR-013's recount can redo each tally.
        self.assertEqual(steps.count("deletion"), 2)
        self.assertEqual(steps.index("deletion"), steps.index("minimise") + steps.count("minimise"))
        self.assertEqual(steps.index("verify"), steps.index("deletion") + 2)
        deletions = [line for line in lines if line["step"] == "deletion"]
        self.assertEqual([(line["removed"], line["round"]) for line in deletions], [(str(A), 1), (str(B), 1)])
        self.assertTrue(all("removed" not in line for line in lines if line["step"] != "deletion"))


class TestEnvironment(unittest.TestCase):
    """Panel action A7: each execution record names the project's commit and the OS."""

    def test_folder_without_git_records_unknown_commit_and_still_names_the_os(self):
        folder = Path(tempfile.mkdtemp(prefix="flaketrace-nogit-"))
        env = environment(folder)
        self.assertEqual((env["project_commit"], env["project_dirty"]), (None, None))
        self.assertEqual(env["os"], platform.platform())

    @unittest.skipUnless(shutil.which("git"), "git not on PATH")
    def test_git_project_records_its_commit_and_whether_it_has_uncommitted_changes(self):
        repo = Path(tempfile.mkdtemp(prefix="flaketrace-git-"))
        git = ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "A.java").write_text("class A {}", encoding="utf-8")
        subprocess.run(git + ["add", "A.java"], check=True)
        subprocess.run(git + ["commit", "-q", "-m", "one"], check=True)
        head = subprocess.run(git + ["rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual((environment(repo)["project_commit"], environment(repo)["project_dirty"]), (head, False))
        (repo / "A.java").write_text("class A { int x; }", encoding="utf-8")
        self.assertTrue(environment(repo)["project_dirty"])

    def test_maven_version_is_the_apache_maven_line_without_colour(self):
        text = "WARNING: something\n\x1b[1mApache Maven 3.9.9 (8e8579a9)\x1b[m\nMaven home: x\n"
        self.assertEqual(maven_version(text), "Apache Maven 3.9.9 (8e8579a9)")
        self.assertIsNone(maven_version("no version here\n"))

    def test_tool_outside_git_records_unknown_commit(self):
        with mock.patch("runner.diagnose.shutil.which", return_value=None):
            env = tool_environment()
        self.assertEqual((env["tool_commit"], env["tool_dirty"], env["maven_version"]), (None, None, None))
        self.assertEqual(env["python_version"], platform.python_version())


class TestDiagnoseOnFixture(unittest.TestCase):
    """Real JVM runs on fixtures/od-fixture, checked against ground_truth.json."""

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        cls.records = tempfile.mkdtemp(prefix="flaketrace-records-")
        cls.truth = {c["id"]: c for c in json.loads((FIXTURE / "ground_truth.json").read_text())["cases"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.records, ignore_errors=True)

    def diagnose_case(self, case_id, n):
        victim = TestIdentifier.from_dict(self.truth[case_id]["victim"])
        runs = diagnose(FIXTURE, victim, n=n, record_dir=self.records)
        self.assertTrue(runs.source_integrity.passed, runs.source_integrity.details)
        self.assertTrue(Path(runs.execution_record).exists())
        return runs

    def expected_polluters(self, case_id):
        return [TestIdentifier.from_dict(p) for p in self.truth[case_id]["polluters"]]

    def test_record_header_states_the_environment(self):
        victim = TestIdentifier.from_dict(self.truth["F1"]["victim"])
        runs = diagnose(FIXTURE, victim, n=1, record_dir=self.records, command=["diagnose", "--n", "1"])
        header = json.loads(Path(runs.execution_record).read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(header["jvm"]["junit.version"], "4.13.2")
        self.assertTrue(header["maven_version"].startswith("Apache Maven"))
        self.assertEqual((header["lifecycle"], header["workspace"], header["container_image"]),
                         ("class-grouped", "in-place", None))
        self.assertEqual(header["command"], ["diagnose", "--n", "1"])
        self.assertIn("tool_commit", header)
        self.assertIn("java_version", header)  # old keys kept

    def test_f1_under_class_grouped_lifecycle_finds_the_same_polluter(self):
        victim = TestIdentifier.from_dict(self.truth["F1"]["victim"])
        runs = diagnose(FIXTURE, victim, n=3, record_dir=self.records, lifecycle="class-grouped")
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.polluters, self.expected_polluters("F1"))
        header = json.loads(Path(runs.execution_record).read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(header["lifecycle"], "class-grouped")

    def fresh_fixture(self):
        folder = Path(tempfile.mkdtemp(prefix="flaketrace-fixture-")) / "od-fixture"
        shutil.copytree(FIXTURE, folder, ignore=shutil.ignore_patterns("target"))
        return folder

    def run_cli_on(self, project, *extra):
        from runner.cli import main
        victim = str(TestIdentifier.from_dict(self.truth["F1"]["victim"]))
        with mock.patch("sys.stdout"):
            code = main(["diagnose", "--project", str(project), "--victim", victim, "--n", "3",
                         "--records", self.records] + list(extra))
        record = max(Path(self.records).glob(f"*-{victim}.jsonl"), key=lambda p: p.stat().st_mtime)
        report = json.loads(record.with_suffix(".report.json").read_text(encoding="utf-8"))
        return code, json.loads(record.read_text(encoding="utf-8").splitlines()[0]), report

    def test_default_copy_never_writes_to_the_project(self):
        project = self.fresh_fixture()
        code, header, report = self.run_cli_on(project)
        self.assertEqual(code, 0)
        self.assertFalse((project / "target").exists())
        self.assertTrue(report["source_integrity"]["passed"], report["source_integrity"])
        self.assertIn("original project:", report["source_integrity"]["details"])
        self.assertEqual((header["workspace"], header["project"]), ("copy", str(project.resolve())))

    def test_in_place_still_builds_in_the_project(self):
        project = self.fresh_fixture()
        code, header, report = self.run_cli_on(project, "--workspace", "in-place")
        self.assertEqual(code, 0)
        self.assertTrue((project / "target").is_dir())
        self.assertNotIn("original project:", report["source_integrity"]["details"])
        self.assertEqual(header["workspace"], "in-place")

    def test_a_change_to_the_original_during_a_copy_run_fails_integrity(self):
        from runner.workspace import workspace
        original = self.fresh_fixture()
        victim = TestIdentifier.from_dict(self.truth["F1"]["victim"])
        real_run_steps = run_steps

        def edit_original_then_run(*args, **kwargs):
            (original / "pom.xml").write_text((original / "pom.xml").read_text(encoding="utf-8") + "\n", encoding="utf-8")
            return real_run_steps(*args, **kwargs)
        with workspace(original, "copy") as work, \
                mock.patch("runner.diagnose.run_steps", side_effect=edit_original_then_run):
            runs = diagnose(work, victim, n=1, record_dir=self.records, workspace="copy", origin=original)
        self.assertFalse(runs.source_integrity.passed)
        self.assertIn("original project: changed: pom.xml", runs.source_integrity.details)

    def test_failed_jvm_probe_records_null_and_the_diagnosis_goes_on(self):
        victim = TestIdentifier.from_dict(self.truth["F1"]["victim"])
        with mock.patch("runner.diagnose.OrderRunner.jvm_environment", return_value={}):
            runs = diagnose(FIXTURE, victim, n=1, record_dir=self.records)
        header = json.loads(Path(runs.execution_record).read_text(encoding="utf-8").splitlines()[0])
        self.assertIsNone(header["jvm"])
        for key in ("tool_commit", "tool_dirty", "maven_version", "python_version",
                    "lifecycle", "workspace", "container_image", "command"):
            self.assertIn(key, header)
        self.assertEqual(runs.status, POLLUTER_FOUND)

    def test_f1_single_static_field_polluter(self):
        runs = self.diagnose_case("F1", n=20)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.polluters, self.expected_polluters("F1"))
        self.assertEqual((runs.sequence_tally.matched, runs.sequence_tally.n), (20, 20))
        self.assertEqual((runs.alone_tally.matched, runs.alone_tally.n), (0, 20))
        record = Path(runs.execution_record).read_text(encoding="utf-8").splitlines()
        types = [json.loads(line)["type"] for line in record]
        # No deletion runs: one polluter. W25 adds one ranking line (Interface 7, P6).
        self.assertEqual((types.count("run"), types.count("ranking"), len(types)),
                         (1 + 20 + runs.search_runs + 20, 1, 1 + 1 + 1 + 20 + runs.search_runs + 20))
        self.assertEqual([(c.status, c.source) for c in runs.deletion_checks], [(NEEDED, ALONE_CHECK)])
        header = json.loads(record[0])
        self.assertRegex(header["project_commit"], r"^[0-9a-f]{40}$")
        self.assertIsInstance(header["project_dirty"], bool)
        self.assertEqual(header["os"], platform.platform())

    def test_f2_single_system_property_polluter(self):
        runs = self.diagnose_case("F2", n=5)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.polluters, self.expected_polluters("F2"))
        self.assertEqual(runs.sequence_tally.matched, 5)

    def test_f3_two_polluters_are_found_by_minimisation(self):
        runs = self.diagnose_case("F3", n=5)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.polluters, self.expected_polluters("F3"))
        # One search run per earlier test; counted from the order, so new fixture cases don't break it.
        self.assertEqual(runs.search_runs, len(runs.original_order) - 1)
        self.assertGreater(runs.minimise_runs, 0)
        self.assertEqual(runs.sequence_tally.matched, 5)
        # ADR-011 T3 at the runner level: both polluters needed (the verdict needs M3's half of W20).
        self.assertEqual([(c.removed, c.status, c.source, c.runs.passed) for c in runs.deletion_checks],
                         [(p, NEEDED, DELETION_RUN, 5) for p in self.expected_polluters("F3")])

    def test_n1_fails_alone(self):
        runs = self.diagnose_case("N1", n=20)
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertEqual((runs.alone_tally.matched, runs.alone_tally.n), (20, 20))

    def test_f4_only_a_shuffled_order_reproduces(self):
        runs = self.diagnose_case("F4", n=5)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.polluters, self.expected_polluters("F4"))
        self.assertIsNotNone(runs.reproducing_seed)
        self.assertEqual(runs.sequence_tally.matched, 5)

    def test_n3_is_not_reproduced_after_shuffles_and_alone(self):
        runs = self.diagnose_case("N3", n=5)
        self.assertEqual(runs.status, NOT_REPRODUCED)
        self.assertEqual((runs.sequence_tally.n, runs.alone_tally.n, runs.alone_tally.matched), (5, 5, 0))
        self.assertEqual(runs.shuffled_orders, 31)
        self.assertFalse(runs.orders_exhausted)

    def test_n2_intermittent_failure_fails_alone_and_blames_no_polluter(self):
        # N2 fails ~50% of runs (Random.nextBoolean, PR #14); 20 runs with no failure ~ 1e-6.
        runs = self.diagnose_case("N2", n=20)
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertEqual(runs.polluters, [])
        self.assertGreaterEqual(runs.alone_tally.matched, 1)


class TestBudget(unittest.TestCase):
    """W24, Interface 6 (B1-B8) and ADR-014's tests to write first. TEN: ten candidates, the polluter
    is the last; n=20, so the reserve is 60 and the start minimum 60 + 11 + 2 = 73."""

    C = [TestIdentifier(f"pkg.C{i}Test", "c") for i in range(10)]

    def ten(self):
        return victim_fails_when(lambda order: self.C[9] in order[:-1]), self.C + [V]

    def test_no_limit_changes_nothing(self):
        runner, order = self.ten()
        runs = run_steps(runner, order, V, n=20)
        self.assertEqual((runs.status, runs.polluters), (POLLUTER_FOUND, [self.C[9]]))
        self.assertEqual(len(runner.calls), 51)  # reproduce 1, alone 20, search 10, verify 20
        b = runs.budget
        self.assertEqual((b.exhausted, b.limit_invocations, b.spent["search"]), (False, None, 20))
        self.assertEqual((b.candidates_tried, b.candidates_total, b.reserve_invocations), (10, 10, 60))

    def test_search_stops_at_the_cap_and_the_alone_check_ran_in_full(self):
        runner, order = self.ten()
        runs = run_steps(runner, order, V, n=20, budget=Budget(80))
        self.assertEqual((runs.status, runs.polluters, runs.alone_tally.n), (BUDGET_EXHAUSTED, [], 20))
        b = runs.budget
        self.assertEqual(b.spent, {"reproduce": 11, "shuffle": 0, "alone": 20, "pair": 0, "search": 8, "minimise": 0,
                                   "deletion": 0, "verify": 0})
        self.assertEqual((b.candidates_tried, b.exhausted_phase, b.launches), (4, "search", 25))
        self.assertEqual((runs.search_runs, runs.sequence, runs.deletion_checks), (4, order, []))
        self.assertEqual(runs.sequence_tally, RunTally(1, 0, 1, 0, 0))

    def test_limit_below_the_start_minimum_is_refused(self):
        runner, order = self.ten()
        with self.assertRaisesRegex(DiagnoseInputError, "73"):
            run_steps(runner, order, V, n=20, budget=Budget(72))
        self.assertEqual(runner.calls, [])
        self.assertEqual(run_steps(runner, order, V, n=20, budget=Budget(73)).status, BUDGET_EXHAUSTED)

    def test_victim_failing_alone_outranks_the_cut(self):
        runner = victim_fails_when(lambda order: order == [V])
        runs = run_steps(runner, self.C + [V], V, n=20, budget=Budget(73))
        self.assertEqual((runs.status, runs.budget.exhausted_phase), (VICTIM_FAILS_ALONE, "reproduce"))

    def test_record_recounts_to_the_ledger(self):
        runner, order = self.ten()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            runs = run_steps(RecordingRunner(runner, path, {}), order, V, n=20, budget=Budget(80))
            lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        recount = {}
        for line in (x for x in lines if x["type"] == "run"):
            recount[line["step"]] = recount.get(line["step"], 0) + len(line["order"])
        self.assertEqual(recount, {k: v for k, v in runs.budget.spent.items() if v})
        self.assertEqual(sum(x["type"] == "run" for x in lines), runs.budget.launches)
        stops = [x for x in lines if x["type"] == "budget-stop"]
        self.assertEqual([(x["phase"], x["would_cost"]) for x in stops], [("search", 2)])

    P, Q, R = (TestIdentifier(f"pkg.{x}Test", x.lower()) for x in "PQR")

    def both(self):
        return victim_fails_when(lambda order: self.P in order and self.Q in order)

    def test_two_kept_tests_one_deletion_check_fits(self):
        free = run_steps(self.both(), [self.P, self.Q, V], V, n=20)
        self.assertEqual(free.budget.spent, {"reproduce": 3, "shuffle": 0, "alone": 20, "pair": 0, "search": 4,
                                             "minimise": 7, "deletion": 80, "verify": 60})
        runs = run_steps(self.both(), [self.P, self.Q, V], V, n=20, budget=Budget(150))
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual([(c.removed, c.status) for c in runs.deletion_checks],
                         [(self.P, NEEDED), (self.Q, NOT_RUN)])
        self.assertEqual((runs.sequence_tally.n, runs.budget.exhausted_phase), (20, "deletion"))

    def test_short_verify_when_the_hold_back_cannot_be_paid(self):
        runs = run_steps(self.both(), [self.P, self.Q, V], V, n=20, budget=Budget(74))
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual([c.status for c in runs.deletion_checks], [NOT_RUN, NOT_RUN])
        self.assertEqual((runs.sequence_tally.n, runs.budget.exhausted), (13, True))
        self.assertEqual(runs.budget.spent["verify"], 39)

    def test_no_verify_run_fits_is_budget_exhausted(self):
        three = lambda: victim_fails_when(lambda order: all(t in order for t in (self.P, self.Q, self.R)))
        order = [self.P, self.Q, self.R, V]
        free = run_steps(three(), order, V, n=1).budget.spent
        explore = free["reproduce"] + free["shuffle"] + free["search"] + free["minimise"]
        runs = run_steps(three(), order, V, n=1, budget=Budget(explore + 3))
        self.assertEqual((runs.status, runs.polluters, runs.budget.spent["verify"]), (BUDGET_EXHAUSTED, [], 0))

    def test_seconds_limit_stops_the_search(self):
        runner, order = self.ten()
        runs = run_steps(runner, order, V, n=20, budget=Budget(None, 2.5),
                         clock=lambda: float(len(runner.calls)))
        self.assertEqual((runs.status, runs.alone_tally.n, runs.budget.candidates_tried),
                         (BUDGET_EXHAUSTED, 20, 0))


    # Final review findings (2026-11-20), each seen failing first.

    def sixty(self):
        """INCONSISTENT with a 60-test prefix: the victim fails on the first run only. Exploration spends
        reproduce 61 + search 120 + minimise 61 = 242; the full-order check costs 61 a run."""
        seen = []

        def outcome(order, test):
            if test != V:
                return PASS
            seen.append(1)
            return FAIL if len(seen) == 1 else PASS
        return FakeOrderRunner(outcome), [TestIdentifier(f"pkg.T{i}Test", "t") for i in range(60)] + [V]

    def test_inconsistent_under_a_limit_stays_inconsistent(self):
        runner, order = self.sixty()
        runs = run_steps(runner, order, V, n=20, budget=Budget(302))
        self.assertEqual((runs.status, runs.budget.exhausted_phase, runs.budget.spent["verify"]),
                         (INCONSISTENT, "verify", 0))
        self.assertEqual(runs.sequence_tally, RunTally(1, 1, 0, 0, 0))  # the full-order re-check, which passed
        runner, order = self.sixty()
        self.assertEqual(run_steps(runner, order, V, n=20, budget=Budget(362)).sequence_tally.n, 1)

    def test_short_verify_writes_its_stop_after_the_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            run_steps(RecordingRunner(self.both(), path, {}), [self.P, self.Q, V], V, n=20, budget=Budget(74))
            lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        stops = [(x["phase"], x["would_cost"], x["spent"]) for x in lines if x["type"] == "budget-stop"]
        self.assertEqual(stops, [("deletion", 40, 34), ("verify", 3, 73)])
        self.assertEqual(lines[-1]["type"], "budget-stop")  # after the 13 verify runs, not before

    def test_search_cut_after_a_shuffle_tallies_the_reproducing_order(self):
        def runner():
            return victim_fails_when(lambda order: self.C[9] in order[:-1] and order[0] != self.C[0])
        order = self.C + [V]
        free = run_steps(runner(), order, V, n=2, shuffles=31).budget.spent
        self.assertGreater(free["shuffle"], 0)
        runs = run_steps(runner(), order, V, n=2, shuffles=31,
                         budget=Budget(free["reproduce"] + free["shuffle"] + 6))
        self.assertEqual((runs.status, runs.budget.exhausted_phase), (BUDGET_EXHAUSTED, "search"))
        self.assertIsNotNone(runs.reproducing_seed)
        self.assertEqual(runs.sequence_tally, RunTally(1, 0, 1, 0, 0))

    def test_the_hold_back_after_a_drop_uses_the_round_two_kept_count(self):
        """ddmin keeps T2 by mistake (it only matters under minimise); round 1 drops it, round 2 checks
        T1 and T3. The B5 hold-back must use round 2's two kept tests, not round 1's three."""
        t = [TestIdentifier(f"pkg.T{i}Test", "t") for i in range(6)]

        def runner():
            fake = None

            def outcome(order, test):
                needed = t[1] in order and t[3] in order and (t[2] in order or ledger_step() != "minimise")
                return FAIL if test == V and needed else PASS

            def ledger_step():
                return fake.step
            fake = StepAware(outcome)
            return fake
        free = run_steps(runner(), t + [V], V, n=20)
        self.assertEqual([(c.removed, c.status, c.round) for c in free.deletion_checks][-2:],
                         [(t[1], NEEDED, 2), (t[3], NEEDED, 2)])
        base = sum(free.budget.spent.values()) - free.budget.spent["deletion"] - free.budget.spent["verify"]
        round_two = lambda limit: [c.status for c in run_steps(runner(), t + [V], V, n=20,
                                                              budget=Budget(limit)).deletion_checks if c.round == 2]
        self.assertEqual(round_two(base + 280), [NEEDED, NOT_RUN])
        self.assertEqual(round_two(base + 279), [NOT_RUN, NOT_RUN])


class StepAware(FakeOrderRunner):
    """A fake runner that can see the step label, for a ddmin that behaves differently (FT004-style)."""
    step = "unlabelled"


class TestSearchPolicy(unittest.TestCase):
    """W25, Interface 7 (P1-P6) and ADR-014's policy tests, on the fake runner and FakeRanker."""

    C = [TestIdentifier(f"pkg.C{i}Test", "c") for i in range(10)]

    def fails_after(self, test):
        return victim_fails_when(lambda order: test in order[:-1])

    def ranked(self, edges=None, asked=None):
        def ranker_for(candidates, victim):
            if asked is not None:
                asked.append(list(candidates))
            return FakeRanker(candidates, edges=edges or {}, cut_off=False, seconds_per_rank=1.25)
        return ranker_for

    def test_original_policy_changes_nothing(self):
        runner = self.fails_after(self.C[9])
        runs = run_steps(runner, self.C + [V], V, n=20)
        self.assertEqual(len(runner.calls), 51)
        self.assertEqual((runs.search.policy, runs.budget.policy, runs.budget.analysis_seconds),
                         ("original", "original", None))

    def test_ranked_tries_one_pair_where_original_tries_nine(self):
        original = run_steps(self.fails_after(self.C[8]), self.C + [V], V, n=20)
        ranked = run_steps(self.fails_after(self.C[8]), self.C + [V], V, n=20, policy="ranked",
                           ranker_for=self.ranked({2: {8: 1}}))
        self.assertEqual((original.budget.spent["search"], ranked.budget.spent["search"]), (18, 2))
        self.assertEqual((original.status, original.polluters), (ranked.status, ranked.polluters))
        self.assertEqual(sum(original.budget.spent.values()) - sum(ranked.budget.spent.values()), 16)
        self.assertEqual((ranked.search.depths, ranked.search.candidates_with_evidence), ([2], 1))

    def test_candidates_are_the_order_searched(self):
        asked = []
        runner = victim_fails_when(lambda order: self.C[9] in order[:-1] and order[0] != self.C[0])
        runs = run_steps(runner, self.C + [V], V, n=2, shuffles=31, policy="ranked", ranker_for=self.ranked(asked=asked))
        self.assertIsNotNone(runs.reproducing_seed)
        self.assertEqual(asked, [runs.original_order[:-1]])

    def test_ranking_line_comes_before_the_first_search_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            run_steps(RecordingRunner(self.fails_after(self.C[8]), path, {}), self.C + [V], V, n=20,
                      policy="ranked", ranker_for=self.ranked({2: {8: 1}}))
            lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        at = next(i for i, line in enumerate(lines) if line["type"] == "ranking")
        self.assertEqual((lines[at - 1]["step"], lines[at + 1]["step"]), ("alone", "search"))
        ranking = lines[at]
        self.assertEqual((ranking["policy"], ranking["scope"], ranking["depths"], ranking["note"]),
                         ("ranked", "module", [2], None))
        self.assertEqual((ranking["order"][0], len(ranking["order"]), ranking["scores"][0]),
                         (str(self.C[8]), 10, [1, 2, 8]))
        self.assertEqual(ranking["notes"], {})

    def test_ranking_line_names_candidates_that_could_not_be_analysed(self):
        """M1's #138 suggestion, agreed by M3: the record tells "no evidence" from "could not analyse"."""
        def ranker_for(candidates, victim):
            ranker = FakeRanker(candidates, edges={2: {8: 1}}, cut_off=False)
            ranker.notes = {candidates[3]: "test class not found in project classes: pkg.C3Test"}
            return ranker
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            run_steps(RecordingRunner(self.fails_after(self.C[8]), path, {}), self.C + [V], V, n=20,
                      policy="ranked", ranker_for=ranker_for)
            ranking = next(json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if '"ranking"' in x)
        self.assertEqual(ranking["notes"], {str(self.C[3]): "test class not found in project classes: pkg.C3Test"})

    def test_analysis_seconds_in_the_account(self):
        runs = run_steps(self.fails_after(self.C[8]), self.C + [V], V, n=20, policy="ranked",
                         ranker_for=self.ranked({2: {8: 1}}))
        self.assertEqual((runs.budget.policy, runs.budget.analysis_seconds), ("ranked", 1.25))

    def test_random_policy_uses_the_seed(self):
        first, second = self.fails_after(self.C[8]), self.fails_after(self.C[8])
        runs = run_steps(first, self.C + [V], V, n=20, policy="random", seed_base=7)
        run_steps(second, self.C + [V], V, n=20, policy="random", seed_base=7)
        self.assertEqual((runs.search.policy, runs.search.seed), ("random", 7))
        self.assertEqual(first.calls, second.calls)

    def test_status_that_never_searches_still_has_a_search_policy(self):
        def never(candidates, victim):
            raise AssertionError("no search, so no ranking")
        runs = run_steps(victim_fails_when(lambda order: True), self.C + [V], V, n=3, policy="ranked", ranker_for=never)
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertEqual(runs.search, SearchPolicy("ranked", "module", None, [], 0.2, None, None))


class TestPairMode(unittest.TestCase):
    """W35 (ADR-016 revised, Interface 9 P1-P6): ten candidates; the victim sorts before six of them, and its
    polluter C7 sorts after it, so no starting order fails (FJ-03's shape)."""

    C = [TestIdentifier(f"pkg.C{i}Test", "c") for i in range(10)]

    def full(self):
        return self.C[:4] + [V] + self.C[4:]

    def fails_after(self, test):
        return victim_fails_when(lambda order: test in order[:order.index(V)])

    def report(self, runs):
        from eval.report import assemble_report
        from runner.integrity import SourceIntegrity
        return assemble_report(replace(runs, source_integrity=SourceIntegrity(True, "unchanged"),
                                       execution_record="r.jsonl"), None)

    def test_order_mode_cannot_reproduce_it(self):
        runs = run_steps(self.fails_after(self.C[7]), self.full(), V, n=4)
        self.assertEqual((runs.status, runs.search_mode, runs.reproduced_by, runs.pairs_tried, runs.scope_size),
                         (NOT_REPRODUCED, "order", None, 0, 10))

    def test_pairs_find_the_polluter_after_the_victim(self):
        runner = self.fails_after(self.C[7])
        runs = run_steps(runner, self.full(), V, n=4, search_mode="pairs")
        self.assertEqual((runs.status, runs.polluters, runs.sequence), (POLLUTER_FOUND, [self.C[7]], [self.C[7], V]))
        self.assertEqual((runs.search_mode, runs.reproduced_by, runs.pairs_tried, runs.scope_size),
                         ("pairs", "pair", 8, 10))
        self.assertEqual((runs.reference_signature, runs.original_order), (REF, [self.C[7], V]))
        self.assertEqual((runs.sequence_tally.n, runs.sequence_tally.matched), (4, 4))
        self.assertEqual((runs.alone_tally.n, runs.alone_tally.matched), (4, 0))
        self.assertEqual((runs.budget.spent["pair"], runs.budget.spent["search"], runs.budget.spent["reproduce"]),
                         (18, 0, 0))
        self.assertEqual((runs.budget.candidates_total, runs.budget.candidates_tried), (10, 8))
        self.assertEqual([c.source for c in runs.deletion_checks], [ALONE_CHECK])
        self.assertEqual(len(runner.calls), 4 + 9 + 4)  # alone first, 8 pairs + 1 re-run, verify
        self.assertEqual(runner.calls[0], [V])
        self.assertEqual(self.report(runs)["outcome"], "CANDIDATE")  # no resource edge given here

    def test_victim_failing_alone_stops_before_any_pair(self):
        runner = victim_fails_when(lambda order: True)
        runs = run_steps(runner, self.full(), V, n=3, search_mode="pairs")
        self.assertEqual((runs.status, runs.reproduced_by, runs.pairs_tried), (VICTIM_FAILS_ALONE, "order", 0))
        self.assertEqual(len(runner.calls), 3)

    def test_no_pair_fails(self):
        runs = run_steps(victim_fails_when(lambda order: False), self.full(), V, n=4, search_mode="pairs")
        self.assertEqual((runs.status, runs.reproduced_by, runs.pairs_tried, runs.polluters),
                         (NOT_REPRODUCED, None, 10, []))
        self.assertEqual((runs.sequence_tally.n, runs.sequence_tally.passed), (10, 10))
        report = self.report(runs)
        self.assertEqual((report["outcome"], report["unresolved_reason"]), ("UNRESOLVED", "NOT_REPRODUCED"))

    def test_a_crashing_pair_counts_as_an_infrastructure_failure_when_nothing_is_found(self):
        crash = RunOutcome(passed=False, failure_signature=FailureSignature("flaketrace.Timeout", "", "t"))
        runner = FakeOrderRunner(lambda order, test: crash if test == V and order[0] == self.C[2] else PASS)
        runs = run_steps(runner, self.full(), V, n=4, search_mode="pairs")
        self.assertEqual((runs.status, runs.infrastructure_failures, runs.sequence_tally.infra),
                         (NOT_REPRODUCED, 1, 1))

    def test_no_candidate_in_scope_tallies_the_alone_runs(self):
        runs = run_steps(victim_fails_when(lambda order: False), [V], V, n=4, search_mode="pairs")
        self.assertEqual((runs.status, runs.pairs_tried, runs.sequence_tally.n), (NOT_REPRODUCED, 0, 4))
        self.assertEqual(self.report(runs)["unresolved_reason"], "NOT_REPRODUCED")

    def test_the_budget_cuts_the_scan(self):
        runs = run_steps(self.fails_after(self.C[7]), self.full(), V, n=20, search_mode="pairs",
                         budget=Budget(limit_invocations=60 + 6))
        self.assertEqual((runs.status, runs.polluters, runs.pairs_tried), (BUDGET_EXHAUSTED, [], 3))
        self.assertEqual((runs.budget.exhausted_phase, runs.budget.candidates_tried), ("pair", 3))
        self.assertEqual(self.report(runs)["unresolved_reason"], "BUDGET_EXHAUSTED")

    def test_a_cut_between_a_failing_pair_and_its_re_run_blames_nothing(self):
        runs = run_steps(self.fails_after(self.C[1]), self.full(), V, n=20, search_mode="pairs",
                         budget=Budget(limit_invocations=60 + 4))
        self.assertEqual((runs.status, runs.polluters, runs.reproduced_by), (BUDGET_EXHAUSTED, [], None))
        self.assertEqual((runs.sequence_tally.n, runs.sequence_tally.other, runs.pairs_tried), (2, 1, 2))
        self.assertEqual(self.report(runs)["unresolved_reason"], "BUDGET_EXHAUSTED")

    def test_a_one_off_pair_failure_is_reported_but_never_blamed(self):
        left = [FAIL, PASS]
        runner = FakeOrderRunner(lambda order, test: left.pop(0) if test == V and order[0] == self.C[2] and left
                                 else PASS)
        runs = run_steps(runner, self.full(), V, n=4, search_mode="pairs")
        self.assertEqual((runs.status, runs.polluters, runs.pairs_tried), (NOT_REPRODUCED, [], 10))
        self.assertEqual((runs.sequence_tally.passed, runs.sequence_tally.other, runs.infrastructure_failures), (9, 1, 0))
        report = self.report(runs)
        self.assertEqual((report["outcome"], report["polluters"]), ("UNRESOLVED", []))

    def test_ranked_runs_the_evidence_candidate_first(self):
        runner = self.fails_after(self.C[7])
        asked = []

        def ranker_for(candidates, victim):
            asked.append(list(candidates))
            return FakeRanker(candidates, edges={2: {7: 1}}, cut_off=False)
        runs = run_steps(runner, self.full(), V, n=4, search_mode="pairs", policy="ranked", ranker_for=ranker_for)
        self.assertEqual(asked, [self.C])
        self.assertEqual(runner.calls[4], [self.C[7], V])
        self.assertEqual((runs.pairs_tried, runs.budget.spent["pair"]), (1, 4))

    def test_ranking_line_is_written_for_the_pair_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = Path(tmp) / "r.jsonl"
            recorder = RecordingRunner(self.fails_after(self.C[7]), record, {"victim": str(V)})
            run_steps(recorder, self.full(), V, n=2, search_mode="pairs")
            lines = [json.loads(line) for line in record.read_text(encoding="utf-8").splitlines()]
        ranking = [line for line in lines if line.get("type") == "ranking"]
        self.assertEqual(len(ranking), 1)
        self.assertEqual(ranking[0]["order"], [str(c) for c in self.C])
        self.assertEqual(sum(line.get("step") == "pair" for line in lines), 9)

    def test_pair_mode_budget_minimum_is_the_reserve_and_one_pair(self):
        with self.assertRaises(DiagnoseInputError) as error:
            run_steps(self.fails_after(self.C[7]), self.full(), V, n=20, search_mode="pairs",
                      budget=Budget(limit_invocations=63))
        self.assertIn("minimum 64", str(error.exception))  # review finding 3: one pair and its re-run
        self.assertNotIn("starting order", str(error.exception))
        runs = run_steps(self.fails_after(self.C[0]), self.full(), V, n=20, search_mode="pairs",
                         budget=Budget(limit_invocations=64))
        self.assertEqual((runs.status, runs.polluters), (POLLUTER_FOUND, [self.C[0]]))

    def test_inputs_that_could_carry_the_answer_are_refused(self):
        for extra in ({"order_given": True}, {"priority": [self.C[7]]}, {"search_mode": "both"}):
            with self.subTest(extra=extra), self.assertRaises(DiagnoseInputError):
                run_steps(self.fails_after(self.C[7]), self.full(), V, n=4, **{"search_mode": "pairs", **extra})

    def test_launch_seconds_come_from_the_alone_runs(self):
        ticks = iter(float(i) for i in range(1000))
        runs = run_steps(self.fails_after(self.C[7]), self.full(), V, n=4, clock=lambda: next(ticks))
        self.assertEqual(runs.launch_seconds, 1.0)

    def test_order_mode_records_how_it_reproduced(self):
        runs = run_steps(victim_fails_when(lambda order: self.C[1] in order[:-1]), self.full(), V, n=2)
        self.assertEqual((runs.status, runs.search_mode, runs.reproduced_by, runs.pairs_tried),
                         (POLLUTER_FOUND, "order", "order", 0))


class TestDiagnosePairInputs(unittest.TestCase):
    def test_a_given_order_is_refused_in_pair_mode(self):
        with self.assertRaises(DiagnoseInputError) as error:
            diagnose(FIXTURE, V, original_order=[V], search_mode="pairs")
        self.assertIn("order", str(error.exception))

    def test_a_priority_list_is_refused_before_any_record_is_written(self):
        # Review finding 11: refused in diagnose(), before the recorder writes a header-only record.
        with tempfile.TemporaryDirectory() as tmp:
            records = Path(tmp) / "records"
            victim = TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode")
            with mock.patch("runner.diagnose.prepare_runner") as prepare, self.assertRaises(DiagnoseInputError) as error:
                diagnose(FIXTURE, victim, priority=[victim], search_mode="pairs", record_dir=records)
            self.assertIn("priority", str(error.exception))
            prepare.assert_not_called()
            self.assertFalse(records.exists())


class TestRunStepsPolicyInputs(unittest.TestCase):
    """Review findings 5 and 7: wrong policy inputs are refused before any JVM run."""

    def test_ranked_without_a_ranker_and_priority_with_a_policy_are_refused(self):
        for kwargs in ({"policy": "ranked"}, {"policy": "best"}, {"policy": "random", "priority": [A]},
                       {"policy": "ranked", "priority": [A], "ranker_for": lambda c, v: None}):
            runner = victim_fails_when(lambda order: A in order)
            with self.assertRaises(DiagnoseInputError, msg=kwargs):
                run_steps(runner, [A, B, V], V, n=2, **kwargs)
            self.assertEqual(runner.calls, [], kwargs)


class TestDiagnosePolicyInputs(unittest.TestCase):
    def test_scope_package_with_an_order_is_refused(self):
        empty = Path(tempfile.mkdtemp(prefix="flaketrace-empty-"))
        with self.assertRaisesRegex(DiagnoseInputError, "cannot be combined with --order"):
            diagnose(empty, V, original_order=[V], scope="package")
        with self.assertRaisesRegex(DiagnoseInputError, "policy"):
            diagnose(empty, V, policy="best")
        with self.assertRaisesRegex(DiagnoseInputError, "scope"):
            diagnose(empty, V, scope="class")


if __name__ == "__main__":
    unittest.main()
