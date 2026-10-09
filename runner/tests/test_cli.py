import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from eval.baseline import FailureSignature, TestIdentifier
from runner.cli import main
from runner.diagnose import NO_SINGLE_POLLUTER, POLLUTER_FOUND, VICTIM_FAILS_ALONE, DiagnosisRuns
from runner.integrity import SourceIntegrity

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "fixtures" / "od-fixture"

V = TestIdentifier("pkg.VictimTest", "v")
P = TestIdentifier("pkg.PolluterTest", "p")
REF = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "expected <N>")


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def project_with_pom():
    project = Path(tempfile.mkdtemp(prefix="flaketrace-cli-project-"))
    (project / "pom.xml").write_text("<project/>", encoding="utf-8")
    return project


def runs(status, record, **overrides):
    fields = dict(
        status=status, victim=V, original_order=[P, V], reference_signature=REF,
        polluters=[], sequence=[V], sequence_n=20, sequence_successes=20,
        sequence_any_failures=20, alone_n=20, alone_successes=20, search_runs=0,
        source_integrity=SourceIntegrity(True, "3 files hashed; all identical"),
        execution_record=str(record),
    )
    fields.update(overrides)
    return DiagnosisRuns(**fields)


class TestInputErrors(unittest.TestCase):
    def test_malformed_victims_exit_2(self):
        for victim in ("pkg.VictimTest", "pkg.VictimTest#", "#v"):
            with mock.patch("runner.cli.diagnose") as diagnose:
                code, _, err = run_cli(["diagnose", "--project", str(FIXTURE), "--victim", victim])
            self.assertEqual(code, 2, victim)
            self.assertIn("Class#method", err)
            diagnose.assert_not_called()

    def test_missing_project_exits_2(self):
        with mock.patch("runner.cli.diagnose") as diagnose:
            code, _, err = run_cli(["diagnose", "--project", "no/such/project", "--victim", "a.B#c"])
        self.assertEqual(code, 2)
        self.assertIn("no pom.xml", err)
        diagnose.assert_not_called()

    def test_n_below_one_exits_2_before_maven(self):
        code, _, err = run_cli(["diagnose", "--project", str(FIXTURE), "--victim", "a.B#c", "--n", "0"])
        self.assertEqual(code, 2)
        self.assertIn("n must be >= 1", err)

    def test_records_inside_the_project_exits_2_before_maven(self):
        code, _, err = run_cli(["diagnose", "--project", str(FIXTURE), "--victim", "a.B#c",
                                "--records", str(FIXTURE / "records")])
        self.assertEqual(code, 2)
        self.assertIn("inside the analysed project", err)

    def test_missing_subcommand_is_a_usage_error(self):
        with self.assertRaises(SystemExit) as raised, redirect_stderr(io.StringIO()):
            main([])
        self.assertEqual(raised.exception.code, 2)


class TestToolErrors(unittest.TestCase):
    def check(self, error, expected_code, expected_text):
        with mock.patch("runner.cli.diagnose", side_effect=error):
            code, _, err = run_cli(["diagnose", "--project", str(project_with_pom()), "--victim", "a.B#c"])
        self.assertEqual(code, expected_code)
        self.assertTrue(err.startswith("error: "), err)
        self.assertIn(expected_text, err)
        self.assertNotIn("Traceback", err)

    def test_victim_not_among_the_tests_exits_2(self):
        self.check(ValueError("victim a.B#c is not in the original order"), 2, "a.B#c")

    def test_maven_failure_exits_1(self):
        self.check(subprocess.CalledProcessError(1, ["C:/tools/mvn.cmd", "-B"]), 1, "mvn.cmd failed")

    def test_missing_tool_exits_1(self):
        self.check(RuntimeError("'javac' not found on PATH"), 1, "'javac' not found on PATH")

    def test_extractor_failure_exits_1(self):
        project = project_with_pom()  # no target/ folders, so Project() raises ExtractError(..., 2)
        found = runs(POLLUTER_FOUND, project / "r.jsonl", polluters=[P], sequence=[P, V],
                     alone_successes=0, search_runs=1)
        with mock.patch("runner.cli.diagnose", return_value=found):
            code, _, err = run_cli(["diagnose", "--project", str(project), "--victim", str(V)])
        self.assertEqual(code, 1)
        self.assertIn("error: resource evidence failed", err)


class TestReports(unittest.TestCase):
    def test_victim_fails_alone_writes_a_report_and_skips_the_extractor(self):
        records = Path(tempfile.mkdtemp(prefix="flaketrace-cli-records-"))
        record = records / "20261010T000000Z-pkg.VictimTest#v.jsonl"
        with mock.patch("runner.cli.diagnose", return_value=runs(VICTIM_FAILS_ALONE, record)), \
                mock.patch("runner.cli.analyse_test") as analyse:
            code, out, _ = run_cli(["diagnose", "--project", str(project_with_pom()), "--victim", str(V)])
        self.assertEqual(code, 0)
        analyse.assert_not_called()
        report_path = records / "20261010T000000Z-pkg.VictimTest#v.report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual((report["outcome"], report["unresolved_reason"]), ("UNRESOLVED", "VICTIM_FAILS_ALONE"))
        self.assertEqual(report["execution_record_reference"], str(record))
        self.assertTrue(out.startswith("UNRESOLVED (VICTIM_FAILS_ALONE)  pkg.VictimTest#v"), out)
        self.assertIn("alone: 20/20", out)
        self.assertIn(str(report_path), out)
        out.encode("ascii")  # the summary must print on any console

    def test_no_single_polluter_exits_3_without_a_report(self):
        records = Path(tempfile.mkdtemp(prefix="flaketrace-cli-records-"))
        record = records / "20261010T000000Z-pkg.VictimTest#v.jsonl"
        unhandled = runs(NO_SINGLE_POLLUTER, record, sequence=[P, V], alone_successes=0, search_runs=1)
        with mock.patch("runner.cli.diagnose", return_value=unhandled):
            code, out, _ = run_cli(["diagnose", "--project", str(project_with_pom()), "--victim", str(V)])
        self.assertEqual(code, 3)
        self.assertEqual(list(records.glob("*.report.json")), [])
        self.assertIn("No report: NO_SINGLE_POLLUTER", out)
        self.assertIn(str(record), out)


if __name__ == "__main__":
    unittest.main()
