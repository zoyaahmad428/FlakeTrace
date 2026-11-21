import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.bundle import verify_bundle
from runner.bundle import write_bundle

V = {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"}
P = {"class": "odfixture.ConfigPolluterTest", "method": "pollute"}
Q = {"class": "x", "method": "y"}
REF_SIG = {"exception_type": "java.lang.AssertionError", "message": "expected:<0> but was:<1>",
           "stack_trace": "at odfixture.ConfigVictimTest.expectsDefaultMode(ConfigVictimTest.java:10)"}
VICTIM_STR = "odfixture.ConfigVictimTest#expectsDefaultMode"

# Interface 8's own write_bundle is the one writer; tests here build bundles through it (not a
# hand-rolled approximation) so this module's recount is tested against the real format.
FAKE_HOME = "C:\\Users\\flaketrace-test-user"


def _victim_outcome(matched=True, other=False, infra=False):
    """One run_ordered outcome entry for the victim, in record.jsonl's own shape."""
    if not (matched or other or infra):
        return {"test": VICTIM_STR, "passed": True}
    if infra:
        sig = {"exception_type": "flaketrace.JvmCrash", "message": "crashed", "stack_trace": ""}
    elif other:
        sig = {"exception_type": "java.lang.IllegalStateException", "message": "nope", "stack_trace": "at X.y(X.java:1)"}
    else:
        sig = REF_SIG
    return {"test": VICTIM_STR, "passed": False, "failure_signature": sig}


def _run_line(step, order, victim_outcome, note=None):
    line = {
        "type": "run", "step": step, "started": "2026-11-20T18:00:00+00:00", "seconds": 0.5,
        "order": order,
        "outcomes": [{"test": t, "passed": True} for t in order[:-1]] + [victim_outcome],
    }
    if note:
        line.update(note)
    return line


def _header(**overrides):
    header = {
        "type": "header", "victim": VICTIM_STR, "n": 20,
        "project": r"C:\build\fixtures\od-fixture", "java_version": "openjdk version \"1.8.0_512\"",
        "started": "2026-11-20T18:00:00+00:00", "project_commit": "abc123", "project_dirty": False,
        "os": "Windows-11", "order_given": False, "shuffles": 31, "seed_base": 0,
        "tool_commit": "def456", "tool_dirty": False, "maven_version": "Apache Maven 3.9.11",
        "python_version": "3.11.0", "jvm": {"timezone": "UTC", "junit.version": "4.13.2"},
        "lifecycle": "class-grouped", "workspace": "in-place", "container_image": None,
        "command": ["diagnose", "--project", r"C:\build\fixtures\od-fixture", "--victim", VICTIM_STR],
        "budget": {"limit_invocations": None, "limit_seconds": None, "reserve_invocations": 60},
        "policy": "original", "scope": "module",
    }
    header.update(overrides)
    return header


def _report(**overrides):
    report = {
        "schema_version": 2, "victim": V, "polluters": [P],
        "original_failing_order": [P, V], "reduced_sequence": [P, V],
        "reproduction": {"n": 20, "passed": 0, "matched": 20, "other": 0, "infra": 0,
                          "confidence": 0.95, "lower": 0.839, "upper": 1.0},
        "victim_alone": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0,
                          "confidence": 0.95, "lower": 0.0, "upper": 0.161},
        "shared_resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
        "polluter_write_location": {"class": "odfixture.ConfigPolluterTest", "method": "pollute", "bytecode_offset": 3},
        "victim_read_location": {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode", "bytecode_offset": 5},
        "resource_edges": [{
            "shared_resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
            "polluter_write_location": {"class": "odfixture.ConfigPolluterTest", "method": "pollute", "bytecode_offset": 3},
            "victim_read_location": {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode", "bytecode_offset": 5},
        }],
        "deletion_checks": [{
            "removed": P, "runs": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0},
            "status": "NEEDED", "source": "alone-check", "round": 1,
        }],
        "failure_signature": REF_SIG, "instrumentation_level": "static-only",
        "execution_record_reference": "will be overwritten by write_bundle",
        "source_integrity": {"passed": True, "details": "19 files hashed; all identical"},
        "outcome": "VERIFIED", "unresolved_reason": None, "candidate_reasons": [], "limitations": [],
        "assurance": {
            "sequence": {"reproduces": "ESTABLISHED", "passes_alone": "ESTABLISHED", "deletion": "DELETION_VERIFIED"},
            "resource": {"level": "STATIC_OVERLAP", "mechanism": "NOT_ASSESSED"},
        },
    }
    report.update(overrides)
    return report


def _record_lines_f1_shape():
    lines = [_header()]
    lines.append(_run_line("reproduce", ["odfixture.ConfigPolluterTest#pollute", VICTIM_STR],
                            _victim_outcome(matched=True)))
    for _ in range(20):
        lines.append(_run_line("alone", [VICTIM_STR], _victim_outcome(matched=False)))
    for _ in range(20):
        lines.append(_run_line("verify", ["odfixture.ConfigPolluterTest#pollute", VICTIM_STR],
                                _victim_outcome(matched=True)))
    return lines


class BundleTestCase(unittest.TestCase):
    """Builds bundles through the real runner.bundle.write_bundle -- this module is tested
    against the actual contract, not a hand-rolled approximation of it."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self._next = 0

    def tearDown(self):
        self._tmp.cleanup()

    def bundle(self, report=None, lines=None, **kwargs):
        self._next += 1
        record_path = self.tmp / f"2026112{self._next:01d}T180000Z-{VICTIM_STR}.jsonl"
        with record_path.open("w", encoding="utf-8", newline="\n") as f:
            for line in (lines if lines is not None else _record_lines_f1_shape()):
                f.write(json.dumps(line) + "\n")
        args = dict(paths={}, home=FAKE_HOME, user="flaketrace-test-user", environment_text="java -version\nmvn -v\n",
                    repository="fixture", module_path="fixtures/od-fixture")
        args.update(kwargs)
        return write_bundle(self.tmp / "out", report if report is not None else _report(), record_path, **args)


class TestVerifyBundleHappyPath(BundleTestCase):
    def test_a_freshly_made_bundle_verifies_clean(self):
        bundle_dir = self.bundle()
        self.assertEqual(verify_bundle(bundle_dir), [])

    def test_changing_a_report_count_is_caught_by_recount(self):
        bad = _report()
        bad["reproduction"] = dict(bad["reproduction"], matched=19, passed=1)
        bundle_dir = self.bundle(report=bad)
        problems = verify_bundle(bundle_dir)
        self.assertTrue(any("reproduction" in p for p in problems), problems)

    def test_changing_one_byte_of_the_record_breaks_the_checksum(self):
        bundle_dir = self.bundle()
        record_path = bundle_dir / "record.jsonl"
        text = record_path.read_text(encoding="utf-8")
        record_path.write_text(text[:-2] + "X\n", encoding="utf-8")
        problems = verify_bundle(bundle_dir)
        self.assertTrue(any("checksum" in p for p in problems), problems)

    def test_deleting_one_alone_line_with_the_checksum_fixed_is_still_caught_by_recount(self):
        """ADR-013's own test: fixing the checksum after tampering must not hide the mismatch --
        the recount is a second, independent check from the checksum (Interface 8)."""
        bundle_dir = self.bundle()
        record_path = bundle_dir / "record.jsonl"
        lines = [json.loads(l) for l in record_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        dropped, kept = False, []
        for line in lines:
            if not dropped and line.get("step") == "alone":
                dropped = True
                continue
            kept.append(line)
        self.assertTrue(dropped)
        with record_path.open("w", encoding="utf-8", newline="\n") as f:
            for line in kept:
                f.write(json.dumps(line) + "\n")
        manifest_path = bundle_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["record.jsonl"] = hashlib.sha256(record_path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        problems = verify_bundle(bundle_dir)
        self.assertTrue(any("alone" in p for p in problems), problems)

    def test_a_bundle_with_no_manifest_is_a_clear_problem_not_a_crash(self):
        empty = self.tmp / "empty-bundle"
        empty.mkdir()
        problems = verify_bundle(empty)
        self.assertTrue(problems)


class TestVerifyBundleOtherShapes(BundleTestCase):
    def test_victim_fails_alone_shape(self):
        report = _report(polluters=[], reduced_sequence=[V], deletion_checks=[],
                         shared_resource=None, polluter_write_location=None, victim_read_location=None,
                         resource_edges=[],
                         reproduction={"n": 20, "passed": 0, "matched": 20, "other": 0, "infra": 0,
                                       "confidence": 0.95, "lower": 0.839, "upper": 1.0},
                         victim_alone={"n": 20, "passed": 0, "matched": 20, "other": 0, "infra": 0,
                                       "confidence": 0.95, "lower": 0.839, "upper": 1.0},
                         outcome="UNRESOLVED", unresolved_reason="VICTIM_FAILS_ALONE")
        del report["assurance"]
        lines = [_header()] + [_run_line("alone", [VICTIM_STR], _victim_outcome(matched=True)) for _ in range(20)]
        bundle_dir = self.bundle(report=report, lines=lines)
        self.assertEqual(verify_bundle(bundle_dir), [])

    def test_not_reproduced_shape(self):
        report = _report(polluters=[], reduced_sequence=[P, V], deletion_checks=[],
                         shared_resource=None, polluter_write_location=None, victim_read_location=None,
                         resource_edges=[], failure_signature=None,
                         reproduction={"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0,
                                       "confidence": 0.95, "lower": 0.0, "upper": 0.161},
                         victim_alone={"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0,
                                       "confidence": 0.95, "lower": 0.0, "upper": 0.161},
                         outcome="UNRESOLVED", unresolved_reason="NOT_REPRODUCED")
        del report["assurance"]
        lines = [_header()]
        lines += [_run_line("reproduce", ["odfixture.ConfigPolluterTest#pollute", VICTIM_STR],
                            _victim_outcome(matched=False)) for _ in range(20)]
        lines += [_run_line("alone", [VICTIM_STR], _victim_outcome(matched=False)) for _ in range(20)]
        bundle_dir = self.bundle(report=report, lines=lines)
        self.assertEqual(verify_bundle(bundle_dir), [])

    def test_two_polluters_deletion_run_shape(self):
        report = _report(polluters=[P, Q], reduced_sequence=[P, Q, V], deletion_checks=[
            {"removed": P, "runs": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0},
             "status": "NEEDED", "source": "deletion-run", "round": 1},
            {"removed": Q, "runs": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0},
             "status": "NEEDED", "source": "deletion-run", "round": 1},
        ])
        lines = [_header()]
        lines.append(_run_line("reproduce", ["odfixture.ConfigPolluterTest#pollute", "x#y", VICTIM_STR],
                                _victim_outcome(matched=True)))
        lines += [_run_line("alone", [VICTIM_STR], _victim_outcome(matched=False)) for _ in range(20)]
        lines += [_run_line("deletion", ["x#y", VICTIM_STR], _victim_outcome(matched=False),
                            note={"removed": "odfixture.ConfigPolluterTest#pollute", "round": 1}) for _ in range(20)]
        lines += [_run_line("deletion", ["odfixture.ConfigPolluterTest#pollute", VICTIM_STR],
                            _victim_outcome(matched=False), note={"removed": "x#y", "round": 1}) for _ in range(20)]
        lines += [_run_line("verify", ["odfixture.ConfigPolluterTest#pollute", "x#y", VICTIM_STR],
                            _victim_outcome(matched=True)) for _ in range(20)]
        bundle_dir = self.bundle(report=report, lines=lines)
        self.assertEqual(verify_bundle(bundle_dir), [])


class TestVerifyReplayBundle(BundleTestCase):
    """Interface 8: a replay bundle (kind="replay") carries reference_signature in its record
    header and has no reproduce/shuffle/search/minimise lines -- the recount must read the
    reference from there, not re-derive it (there is nothing to re-derive it from)."""

    def test_replay_polluter_found_shape_reads_the_headers_own_reference(self):
        header = _header(reference_signature=REF_SIG, replay_of="deadbeef" * 8)
        lines = [header]
        lines += [_run_line("alone", [VICTIM_STR], _victim_outcome(matched=False)) for _ in range(20)]
        lines += [_run_line("verify", ["odfixture.ConfigPolluterTest#pollute", VICTIM_STR],
                            _victim_outcome(matched=True)) for _ in range(20)]
        bundle_dir = self.bundle(report=_report(), lines=lines, kind="replay", replay_of="deadbeef" * 8)
        self.assertEqual(verify_bundle(bundle_dir), [])

    def test_replay_without_a_reference_signature_in_the_header_is_a_clear_problem(self):
        """Malformed input (a replay bundle whose header is missing the field Interface 8
        requires), not a crash."""
        lines = [_header()]  # no reference_signature
        lines += [_run_line("alone", [VICTIM_STR], _victim_outcome(matched=False)) for _ in range(20)]
        bundle_dir = self.bundle(report=_report(outcome="UNRESOLVED", unresolved_reason="VICTIM_FAILS_ALONE"),
                                 lines=lines, kind="replay", replay_of="deadbeef" * 8)
        problems = verify_bundle(bundle_dir)
        self.assertTrue(any("reference_signature" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
