import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from eval.baseline import FailureSignature, TestIdentifier
from runner.cli import main, summary
from runner.diagnose import (NO_SINGLE_POLLUTER, POLLUTER_FOUND, VICTIM_FAILS_ALONE, DiagnoseInputError,
                             DiagnosisRuns)
from runner.integrity import SourceIntegrity
from runner.order_runner import ToolError

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
        for victim in ("pkg.VictimTest", "pkg.VictimTest#", "#v", " pkg.VictimTest#v", "pkg.VictimTest#v ",
                       "pkg.VictimTest#v:x", "pkg.VictimTest#a#b", "pkg.Victim Test#v", "pkg.VictimTest#<v>"):
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
        self.check(DiagnoseInputError("victim a.B#c is not in the original order"), 2, "a.B#c")

    def test_maven_failure_exits_1(self):
        self.check(subprocess.CalledProcessError(1, ["C:/tools/mvn.cmd", "-B"]), 1, "mvn.cmd failed")

    def test_missing_tool_exits_1(self):
        self.check(ToolError("'javac' not found on PATH"), 1, "'javac' not found on PATH")

    def test_discovery_timeout_exits_1(self):
        self.check(subprocess.TimeoutExpired(["java", "FtHarness", "--list"], 120), 1, "timed out")

    def test_internal_errors_are_not_hidden_as_input_or_tool_errors(self):
        # ADR-005: unexpected exceptions keep their traceback. These are internal, not the user's input.
        for internal in (ValueError("order contains the same test more than once"),
                         UnicodeDecodeError("utf-8", bytes([0xFF]), 0, 1, "bad byte"),
                         RecursionError("maximum recursion depth exceeded")):
            with mock.patch("runner.cli.diagnose", side_effect=internal):
                with self.assertRaises(type(internal)), redirect_stderr(io.StringIO()):
                    main(["diagnose", "--project", str(project_with_pom()), "--victim", "a.B#c"])

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

    def test_summary_shows_the_resource_and_both_locations(self):
        report = self.report_with_resource()
        line = [l for l in summary(report, Path("r.report.json")).splitlines() if "resource:" in l][0]
        self.assertEqual(line, "  resource:   static-field odfixture.Config mode "
                               "(write pkg.PolluterTest#p@1 -> read pkg.VictimTest#v@4)")

    def test_summary_survives_a_resource_without_locations(self):
        report = self.report_with_resource()
        report["polluter_write_location"] = report["victim_read_location"] = None
        text = summary(report, Path("r.report.json"))
        self.assertIn("  resource:   static-field odfixture.Config mode", text.splitlines())

    @staticmethod
    def report_with_resource():
        return {
            "victim": V.to_dict(), "polluters": [P.to_dict()], "outcome": "VERIFIED", "unresolved_reason": None,
            "shared_resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
            "polluter_write_location": {"class": "pkg.PolluterTest", "method": "p", "bytecode_offset": 1},
            "victim_read_location": {"class": "pkg.VictimTest", "method": "v", "bytecode_offset": 4},
            "reproduction": {"successes": 20, "n": 20, "lower": 0.839},
            "victim_alone": {"successes": 0, "n": 20}, "execution_record_reference": "r.jsonl",
        }

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


class TestCliOnFixture(unittest.TestCase):
    """Real Maven/JVM/javap runs on fixtures/od-fixture, checked against ground_truth.json."""

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "javap", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        cls.records = tempfile.mkdtemp(prefix="flaketrace-cli-records-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.records, ignore_errors=True)

    def diagnose(self, victim, n):
        code, out, err = run_cli(["diagnose", "--project", str(FIXTURE), "--victim", victim,
                                  "--n", str(n), "--records", self.records])
        reports = sorted(Path(self.records).glob(f"*-{victim}.report.json"))
        report = json.loads(reports[-1].read_text(encoding="utf-8")) if reports else None
        return code, out, err, report

    def test_f1_command_line_end_to_end(self):
        work = Path(tempfile.mkdtemp(prefix="flaketrace-cli-cwd-"))
        finished = subprocess.run(
            [sys.executable, "-m", "runner", "diagnose", "--project", str(FIXTURE),
             "--victim", "odfixture.ConfigVictimTest#expectsDefaultMode"],
            cwd=work, env=dict(os.environ, PYTHONPATH=str(REPO)),
            capture_output=True, text=True, timeout=900,
        )
        self.assertEqual(finished.returncode, 0, finished.stderr)
        self.assertIn("VERIFIED", finished.stdout)
        reports = list((work / "flaketrace-records").glob("*.report.json"))
        self.assertEqual(len(reports), 1)
        report = json.loads(reports[0].read_text(encoding="utf-8"))
        self.assertEqual(report["outcome"], "VERIFIED")
        self.assertEqual(report["shared_resource"],
                         {"kind": "static-field", "class": "odfixture.Config", "field": "mode"})
        self.assertEqual((report["reproduction"]["successes"], report["victim_alone"]["successes"]), (20, 0))
        record = Path(report["execution_record_reference"])
        self.assertFalse(record.is_absolute())
        self.assertTrue((work / record).is_file())
        self.assertEqual(reports[0], work / record.with_suffix(".report.json"))
        shutil.rmtree(work, ignore_errors=True)

    def test_f2_depth_two_edge(self):
        code, _, err, report = self.diagnose("odfixture.FeatureVictimTest#expectsTurboDisabled", 20)
        self.assertEqual(code, 0, err)
        self.assertEqual(report["outcome"], "VERIFIED")
        self.assertEqual(report["shared_resource"], {"kind": "system-property", "key": "odfixture.turbo"})
        self.assertEqual(report["victim_read_location"],
                         {"class": "odfixture.FeatureFlags", "method": "isTurboEnabled", "bytecode_offset": 2})

    def test_f3_two_polluters_verified(self):
        code, out, err, report = self.diagnose("odfixture.ToggleVictimTest#expectsNotBothFlagsSet", 20)
        self.assertEqual(code, 0, err)
        self.assertEqual(report["outcome"], "VERIFIED")
        self.assertEqual(report["polluters"], [{"class": "odfixture.ToggleAPolluterTest", "method": "setFlagA"},
                                               {"class": "odfixture.ToggleBPolluterTest", "method": "setFlagB"}])
        self.assertEqual(report["shared_resource"], {"kind": "static-field", "class": "odfixture.Toggles", "field": "flagA"})

    def test_n1_fails_alone(self):
        code, _, err, report = self.diagnose("odfixture.NegativeAloneFailTest#alwaysFails", 5)
        self.assertEqual(code, 0, err)
        self.assertEqual((report["outcome"], report["unresolved_reason"]), ("UNRESOLVED", "VICTIM_FAILS_ALONE"))
        self.assertEqual(report["polluters"], [])

    def test_unknown_victim_exits_2(self):
        code, _, err, report = self.diagnose("odfixture.ConfigVictimTest#noSuchTest", 3)
        self.assertEqual(code, 2)
        self.assertIn("odfixture.ConfigVictimTest#noSuchTest", err)
        self.assertIsNone(report)
        self.assertEqual(list(Path(self.records).glob("*noSuchTest*")), [])  # no empty record left behind


if __name__ == "__main__":
    unittest.main()
