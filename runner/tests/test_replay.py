import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest import mock

from eval.baseline import FailureSignature, RunOutcome, RunTally, TestIdentifier
from eval.report import assemble_report
from eval.tests.fake_runner import FakeOrderRunner
from runner.bundle import read_bundle, write_bundle
from runner.diagnose import POLLUTER_FOUND, run_steps
from runner.integrity import SourceIntegrity
from runner.recording import RecordingRunner
from runner.replay import REFUSAL, compare, replay, replay_steps, replayable, report_reference

P = TestIdentifier("pkg.PTest", "p")
Q = TestIdentifier("pkg.QTest", "q")
V = TestIdentifier("pkg.VictimTest", "v")
REF = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "expected 0")
PASS = RunOutcome(passed=True)
FAIL = RunOutcome(passed=False, failure_signature=REF)


def fails_after_p():
    return FakeOrderRunner(lambda order, test: FAIL if test == V and P in order[:-1] else PASS)


class TestReplaySteps(unittest.TestCase):
    def test_replay_steps_run_alone_deletion_verify_in_order(self):
        runner = fails_after_p()
        runs = replay_steps(runner, [P], V, REF, 3, [P, V])
        self.assertEqual(runner.calls, [[V]] * 3 + [[P, V]] * 3)  # one polluter: the alone-check, no deletion runs
        self.assertEqual((runs.status, runs.polluters, runs.search_runs), (POLLUTER_FOUND, [P], 0))
        self.assertEqual((runs.sequence_tally, runs.alone_tally), (RunTally(3, 0, 3, 0, 0), RunTally(3, 3, 0, 0, 0)))
        self.assertEqual(runs.budget.spent["search"], 0)

    def test_replay_may_drop_a_polluter(self):
        runs = replay_steps(fails_after_p(), [P, Q], V, REF, 20, [P, Q, V])  # n=20: 20/20 is NOT_NEEDED (ADR-011)
        self.assertEqual((runs.polluters, runs.sequence), ([P], [P, V]))

    def test_a_victim_failing_alone_is_reported_as_such(self):
        runs = replay_steps(FakeOrderRunner(lambda order, test: FAIL), [P], V, REF, 2, [P, V])
        self.assertEqual((runs.status, runs.polluters), ("VICTIM_FAILS_ALONE", []))


def a_report(runner=None, n=3):
    """A real CANDIDATE report (no resource edge) from the fake runner, as diagnose's report would be."""
    runs = run_steps(runner or fails_after_p(), [P, V], V, n=n)
    runs = replace(runs, source_integrity=SourceIntegrity(True, "1 file hashed; identical"), execution_record="r.jsonl")
    return assemble_report(runs, None)


class TestReplayable(unittest.TestCase):
    def test_only_blamed_reports_are_replayable(self):
        self.assertIsNone(replayable(a_report()))
        self.assertEqual(replayable({"outcome": "UNRESOLVED", "polluters": []}), REFUSAL)
        self.assertEqual(REFUSAL, "nothing to replay: no polluter was blamed")
        self.assertEqual(report_reference(a_report()).exception_type, "java.lang.AssertionError")


MANIFEST = {"subject": {"commit": "abc"}, "tool": {"commit": "def"}, "parameters": {"lifecycle": "class-grouped"},
            "environment": {"jdk": "1.8.0_502", "os": "Windows", "maven": "3.9.9", "timezone": "UTC",
                            "locale": "en_US", "encoding": "UTF-8"}}


class TestCompare(unittest.TestCase):
    def test_compare_same_and_different(self):
        report = a_report()
        lines, same = compare(report, report, MANIFEST, MANIFEST)
        self.assertTrue(same)
        self.assertTrue(lines[0].startswith("verdict:") and lines[0].endswith("same"), lines[0])
        other = dict(report, polluters=[Q.to_dict()])
        self.assertFalse(compare(report, other, MANIFEST, MANIFEST)[1])
        self.assertFalse(compare(report, dict(report, candidate_reasons=["BELOW_REPLAY_THRESHOLD"]), MANIFEST, MANIFEST)[1])
        weaker = dict(report, reproduction=dict(report["reproduction"], matched=2, passed=1))
        self.assertTrue(compare(report, weaker, MANIFEST, MANIFEST)[1])  # 3/3 vs 2/3, same claims
        jdk = dict(MANIFEST, environment=dict(MANIFEST["environment"], jdk="21.0.9"))
        lines, same = compare(report, report, MANIFEST, jdk)
        self.assertTrue(same)
        self.assertTrue(any(line.startswith("JDK:") and line.endswith("DIFFERENT") for line in lines), lines)


class TestReplay(unittest.TestCase):
    """replay() with the JVM side mocked: prepare_runner gives a fake runner and a discovered list."""

    def bundle(self, report=None, maven=None):
        tmp = Path(tempfile.mkdtemp(prefix="flaketrace-replay-test-"))
        record = tmp / "20261121T100000Z-pkg.VictimTest#v.jsonl"
        record.write_text(json.dumps({"type": "header", "victim": str(V), "n": 3, "lifecycle": "class-grouped",
                                      "started": "2026-11-21T10:00:00+00:00", "project_commit": "abc",
                                      "maven_version": maven}) + "\n",
                          encoding="utf-8")
        return write_bundle(tmp / "bundles", report or a_report(), record, paths={}, home="C:\\nobody", user="nobody")

    def run_replay(self, folder, discovered=(P, Q, V), tools=True):
        project = Path(tempfile.mkdtemp(prefix="flaketrace-replay-project-"))
        out = Path(tempfile.mkdtemp(prefix="flaketrace-replay-out-"))
        with mock.patch("runner.replay.prepare_runner", return_value=(fails_after_p(), list(discovered), None)), \
                mock.patch("runner.cli.resource_fields", return_value=None), \
                mock.patch("runner.cli._subject", return_value={"repository": "fixture", "module_path": "x"}), \
                mock.patch("runner.cli._environment_text", return_value="java\n"), \
                mock.patch("runner.diagnose.java_version", return_value="java 8"), \
                (mock.patch("runner.diagnose.tool_environment", return_value={}) if tools else mock.MagicMock()):
            return replay(folder, project, out / "bundles", out / "records", 60, "in-place", ["replay"])

    def test_replay_of_a_fresh_bundle_is_the_same(self):
        original = self.bundle()
        code, lines, new = self.run_replay(original)
        self.assertEqual(code, 0, lines)
        manifest = read_bundle(new).manifest
        self.assertEqual((manifest["kind"], manifest["replay_of"]),
                         ("replay", read_bundle(original).manifest["files"]["report.json"]))
        header = read_bundle(new).header
        self.assertEqual(header["reference_signature"]["exception_type"], "java.lang.AssertionError")
        self.assertIn("Comparison with the original bundle", (new / "replay.md").read_text(encoding="utf-8"))

    def test_missing_polluter_is_refused(self):
        code, lines, new = self.run_replay(self.bundle(), discovered=(Q, V))
        self.assertEqual((code, new), (2, None))
        self.assertIn("pkg.PTest#p", " ".join(lines))

    def test_nothing_to_replay(self):
        report = dict(a_report(), outcome="UNRESOLVED", polluters=[])
        code, lines, new = self.run_replay(self.bundle(report))
        self.assertEqual((code, lines, new), (2, [REFUSAL], None))

    def test_a_replay_bundle_can_be_replayed(self):
        first = self.run_replay(self.bundle())[2]
        code, lines, second = self.run_replay(first)
        self.assertEqual(code, 0, lines)
        self.assertEqual(read_bundle(second).manifest["replay_of"], read_bundle(first).manifest["files"]["report.json"])

    def test_n_and_lifecycle_come_from_the_checksummed_record(self):
        folder = self.bundle()
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        manifest["parameters"] = dict(manifest["parameters"], n=1, lifecycle="per-method")
        (folder / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        code, lines, new = self.run_replay(folder)
        self.assertEqual((code, new), (2, None))
        self.assertIn("manifest.json and the record disagree", lines[0])

    def test_the_comparison_in_replay_md_is_the_printed_one(self):
        """Review finding I1: the Maven row in replay.md compares version numbers, as the printed lines do."""
        folder = self.bundle(maven="Apache Maven 3.9.9 (abc)")
        with mock.patch("runner.diagnose.tool_environment", return_value={"maven_version": "Apache Maven 3.9.9 (abc)"}):
            code, lines, new = self.run_replay(folder, tools=False)
        written = (new / "replay.md").read_text(encoding="utf-8")
        maven = next(line for line in written.splitlines() if line.startswith("Maven:"))
        self.assertTrue(maven.endswith("same"), maven)
        self.assertIn("\n".join(lines), written)

    def test_output_inside_the_original_bundle_is_refused(self):
        folder = self.bundle()
        project = Path(tempfile.mkdtemp(prefix="flaketrace-replay-project-"))
        code, lines, new = replay(folder, project, folder / "inside", folder.parent / "rec", 60, "in-place", None)
        self.assertEqual((code, new), (2, None))
        self.assertIn("inside the original bundle", lines[0])

    def test_a_tampered_bundle_is_refused(self):
        folder = self.bundle()
        (folder / "report.json").write_text("{}", encoding="utf-8")
        code, lines, new = self.run_replay(folder)
        self.assertEqual((code, new), (2, None))
        self.assertIn("report.json", lines[0])


if __name__ == "__main__":
    unittest.main()
