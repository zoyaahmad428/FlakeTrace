import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.bundle import BUNDLE_FILES, BundleError, bundle_folder_name, create_bundle, verify_bundle

V = {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"}
P = {"class": "odfixture.ConfigPolluterTest", "method": "pollute"}
Q = {"class": "x", "method": "y"}
REF_SIG = {"exception_type": "java.lang.AssertionError", "message": "expected:<0> but was:<1>",
           "stack_trace": "at odfixture.ConfigVictimTest.expectsDefaultMode(ConfigVictimTest.java:10)"}


def _victim_outcome(matched=True, other=False, infra=False):
    """One run_ordered outcome entry for the victim, in record.jsonl's own shape."""
    if not (matched or other or infra):
        return {"test": "odfixture.ConfigVictimTest#expectsDefaultMode", "passed": True}
    if infra:
        sig = {"exception_type": "flaketrace.JvmCrash", "message": "crashed", "stack_trace": ""}
    elif other:
        sig = {"exception_type": "java.lang.IllegalStateException", "message": "nope", "stack_trace": "at X.y(X.java:1)"}
    else:
        sig = REF_SIG
    return {"test": "odfixture.ConfigVictimTest#expectsDefaultMode", "passed": False, "failure_signature": sig}


def _run_line(step, order, victim_outcome, note=None):
    line = {
        "type": "run", "step": step, "started": "2026-11-20T18:00:00+00:00", "seconds": 0.5,
        "order": order,
        "outcomes": [{"test": t, "passed": True} for t in order[:-1]] + [victim_outcome],
    }
    if note:
        line.update(note)
    return line


HEADER = {
    "type": "header", "victim": "odfixture.ConfigVictimTest#expectsDefaultMode", "n": 20,
    "project": r"C:\Users\zarpa\fixtures\od-fixture", "java_version": "openjdk version \"1.8.0_512\"",
    "started": "2026-11-20T18:00:00+00:00", "project_commit": "abc123", "project_dirty": False,
    "os": "Windows-11", "order_given": False, "shuffles": 31, "seed_base": 0,
    "tool_commit": "def456", "tool_dirty": False, "maven_version": "Apache Maven 3.9.11",
    "python_version": "3.11.0", "jvm": {"timezone": "UTC", "junit.version": "4.13.2"},
    "lifecycle": "class-grouped", "workspace": "in-place", "container_image": None,
    "command": ["python", "-m", "runner", "diagnose", "--project", r"C:\Users\zarpa\fixtures\od-fixture",
                "--victim", "odfixture.ConfigVictimTest#expectsDefaultMode"],
    "budget": {"limit_invocations": None, "limit_seconds": None, "reserve_invocations": 60},
    "policy": "original", "scope": "module",
}

REPORT_F1_SHAPE = {
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
    "execution_record_reference": "/tmp/somewhere/record.jsonl",
    "source_integrity": {"passed": True, "details": "19 files hashed; all identical"},
    "outcome": "VERIFIED", "unresolved_reason": None, "candidate_reasons": [], "limitations": [],
    "assurance": {
        "sequence": {"reproduces": "ESTABLISHED", "passes_alone": "ESTABLISHED", "deletion": "DELETION_VERIFIED"},
        "resource": {"level": "STATIC_OVERLAP", "mechanism": "NOT_ASSESSED"},
    },
}


def _record_lines_f1_shape():
    lines = [HEADER]
    lines.append(_run_line("reproduce", ["odfixture.ConfigPolluterTest#pollute", HEADER["victim"]],
                            _victim_outcome(matched=True)))
    for _ in range(20):
        lines.append(_run_line("alone", [HEADER["victim"]], _victim_outcome(matched=False)))
    for _ in range(20):
        lines.append(_run_line("verify", ["odfixture.ConfigPolluterTest#pollute", HEADER["victim"]],
                                _victim_outcome(matched=True)))
    return lines


def _write_record(tmp: Path, lines) -> Path:
    path = tmp / "record.jsonl"
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(json.dumps(line) + "\n")
    return path


def _write_report(tmp: Path, report: dict) -> Path:
    path = tmp / "report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


class TestCreateBundle(unittest.TestCase):
    def test_builds_the_five_files_with_checksums_and_redaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            report_path = _write_report(tmp, REPORT_F1_SHAPE)
            record_path = _write_record(tmp, _record_lines_f1_shape())
            bundle_dir = create_bundle(report_path, record_path, tmp / "out")

            for name in BUNDLE_FILES + ("manifest.json",):
                self.assertTrue((bundle_dir / name).exists(), name)

            manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["bundle_version"], 1)
            self.assertEqual(manifest["victim"], V)
            self.assertEqual(manifest["subject"]["repository"], "fixture")
            self.assertEqual(manifest["subject"]["commit"], "abc123")
            self.assertNotIn(r"C:\Users\zarpa", json.dumps(manifest))
            self.assertEqual(set(manifest["files"]), set(BUNDLE_FILES))

            bundle_report = json.loads((bundle_dir / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(bundle_report["execution_record_reference"], "record.jsonl")

            record_text = (bundle_dir / "record.jsonl").read_text(encoding="utf-8")
            self.assertNotIn(r"C:\Users\zarpa", record_text)
            self.assertIn("<project>", record_text)

    def test_redacts_a_path_that_uses_the_other_slash_style_too(self):
        """Found for real bundling an actual diagnosis (2026-11-20): the record's own `command`
        list can carry a path in the opposite slash style from Path.home()/the header's
        `project` field (e.g. a Windows path typed with forward slashes in a bash-like shell).
        A literal string replace alone misses that; create_bundle must try both styles."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            header = dict(HEADER)
            home = str(Path.home())
            forward_slash_home = home.replace("\\", "/")
            self.assertNotEqual(home, forward_slash_home, "this test needs a Windows-style home path")
            header["command"] = ["python", "-m", "runner", "diagnose", "--records",
                                  f"{forward_slash_home}/somewhere/records"]
            lines = [header] + _record_lines_f1_shape()[1:]
            report_path = _write_report(tmp, REPORT_F1_SHAPE)
            record_path = _write_record(tmp, lines)
            bundle_dir = create_bundle(report_path, record_path, tmp / "out")

            manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertNotIn(home.split("\\")[-1], json.dumps(manifest["command"]))
            self.assertIn("<home>", " ".join(manifest["command"]))

    def test_folder_name_is_case_then_utc_timestamp(self):
        name = bundle_folder_name("odfixture.ConfigVictimTest#expectsDefaultMode", "2026-11-20T18:00:00+00:00")
        self.assertEqual(name, "odfixture.ConfigVictimTest#expectsDefaultMode-20261120T180000Z")


class TestVerifyBundleHappyPath(unittest.TestCase):
    def _fresh_bundle(self, report=None, lines=None):
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        report_path = _write_report(tmp, report or REPORT_F1_SHAPE)
        record_path = _write_record(tmp, lines if lines is not None else _record_lines_f1_shape())
        return create_bundle(report_path, record_path, tmp / "out")

    def tearDown(self):
        getattr(self, "tmp", None) and self.tmp.cleanup()

    def test_a_freshly_made_bundle_verifies_clean(self):
        bundle_dir = self._fresh_bundle()
        self.assertEqual(verify_bundle(bundle_dir), [])

    def test_changing_a_report_count_is_caught_by_recount(self):
        bad = json.loads(json.dumps(REPORT_F1_SHAPE))
        bad["reproduction"]["matched"] = 19
        bad["reproduction"]["passed"] = 1
        bundle_dir = self._fresh_bundle(report=bad)
        problems = verify_bundle(bundle_dir)
        self.assertTrue(any("reproduction" in p or "sequence" in p for p in problems), problems)

    def test_changing_one_byte_of_the_record_breaks_the_checksum(self):
        bundle_dir = self._fresh_bundle()
        record_path = bundle_dir / "record.jsonl"
        text = record_path.read_text(encoding="utf-8")
        record_path.write_text(text[:-2] + "X\n", encoding="utf-8")
        problems = verify_bundle(bundle_dir)
        self.assertTrue(any("checksum" in p for p in problems), problems)

    def test_deleting_one_alone_line_with_the_checksum_fixed_is_still_caught_by_recount(self):
        """ADR-013's own test: fixing the checksum after tampering must not hide the mismatch --
        the recount is a second, independent check."""
        import hashlib
        bundle_dir = self._fresh_bundle()
        record_path = bundle_dir / "record.jsonl"
        lines = [json.loads(l) for l in record_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        # drop one "alone" line
        dropped = False
        kept = []
        for line in lines:
            if not dropped and line.get("step") == "alone":
                dropped = True
                continue
            kept.append(line)
        self.assertTrue(dropped)
        with record_path.open("w", encoding="utf-8", newline="\n") as f:
            for line in kept:
                f.write(json.dumps(line) + "\n")
        # recompute the checksum so the tamper is NOT caught by the checksum check
        manifest_path = bundle_dir / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"]["record.jsonl"] = hashlib.sha256(record_path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        problems = verify_bundle(bundle_dir)
        self.assertTrue(any("alone" in p for p in problems), problems)

    def test_report_without_a_manifest_is_a_clear_problem_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty-bundle"
            empty.mkdir()
            problems = verify_bundle(empty)
            self.assertTrue(problems)
            self.assertIn("manifest.json", problems[0])


class TestVerifyBundleOtherShapes(unittest.TestCase):
    def _bundle(self, report, lines):
        self.tmp = tempfile.TemporaryDirectory()
        tmp = Path(self.tmp.name)
        report_path = _write_report(tmp, report)
        record_path = _write_record(tmp, lines)
        return create_bundle(report_path, record_path, tmp / "out")

    def tearDown(self):
        self.tmp.cleanup()

    def test_victim_fails_alone_shape(self):
        report = json.loads(json.dumps(REPORT_F1_SHAPE))
        report.update({
            "polluters": [], "reduced_sequence": [V],
            "reproduction": {"n": 20, "passed": 0, "matched": 20, "other": 0, "infra": 0,
                              "confidence": 0.95, "lower": 0.839, "upper": 1.0},
            "victim_alone": {"n": 20, "passed": 0, "matched": 20, "other": 0, "infra": 0,
                              "confidence": 0.95, "lower": 0.839, "upper": 1.0},
            "shared_resource": None, "polluter_write_location": None, "victim_read_location": None,
            "resource_edges": [], "deletion_checks": [],
            "outcome": "UNRESOLVED", "unresolved_reason": "VICTIM_FAILS_ALONE",
        })
        del report["assurance"]
        lines = [dict(HEADER, victim=HEADER["victim"])]
        for _ in range(20):
            lines.append(_run_line("alone", [HEADER["victim"]], _victim_outcome(matched=True)))
        bundle_dir = self._bundle(report, lines)
        self.assertEqual(verify_bundle(bundle_dir), [])

    def test_not_reproduced_shape(self):
        report = json.loads(json.dumps(REPORT_F1_SHAPE))
        report.update({
            "polluters": [], "reduced_sequence": [P, V],
            "reproduction": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0,
                              "confidence": 0.95, "lower": 0.0, "upper": 0.161},
            "victim_alone": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0,
                              "confidence": 0.95, "lower": 0.0, "upper": 0.161},
            "shared_resource": None, "polluter_write_location": None, "victim_read_location": None,
            "resource_edges": [], "deletion_checks": [],
            "failure_signature": None,
            "outcome": "UNRESOLVED", "unresolved_reason": "NOT_REPRODUCED",
        })
        del report["assurance"]
        lines = [HEADER]
        for _ in range(20):
            lines.append(_run_line("reproduce", ["odfixture.ConfigPolluterTest#pollute", HEADER["victim"]],
                                    _victim_outcome(matched=False)))
        for _ in range(20):
            lines.append(_run_line("alone", [HEADER["victim"]], _victim_outcome(matched=False)))
        bundle_dir = self._bundle(report, lines)
        self.assertEqual(verify_bundle(bundle_dir), [])

    def test_two_polluters_deletion_run_shape(self):
        report = json.loads(json.dumps(REPORT_F1_SHAPE))
        report.update({
            "polluters": [P, Q], "reduced_sequence": [P, Q, V],
            "deletion_checks": [
                {"removed": P, "runs": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0},
                 "status": "NEEDED", "source": "deletion-run", "round": 1},
                {"removed": Q, "runs": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0},
                 "status": "NEEDED", "source": "deletion-run", "round": 1},
            ],
        })
        lines = [HEADER]
        lines.append(_run_line("reproduce", ["odfixture.ConfigPolluterTest#pollute", "x#y", HEADER["victim"]],
                                _victim_outcome(matched=True)))
        for _ in range(20):
            lines.append(_run_line("alone", [HEADER["victim"]], _victim_outcome(matched=False)))
        for _ in range(20):
            lines.append(_run_line("deletion", ["x#y", HEADER["victim"]], _victim_outcome(matched=False),
                                    note={"removed": "odfixture.ConfigPolluterTest#pollute", "round": 1}))
        for _ in range(20):
            lines.append(_run_line("deletion", ["odfixture.ConfigPolluterTest#pollute", HEADER["victim"]],
                                    _victim_outcome(matched=False), note={"removed": "x#y", "round": 1}))
        for _ in range(20):
            lines.append(_run_line("verify", ["odfixture.ConfigPolluterTest#pollute", "x#y", HEADER["victim"]],
                                    _victim_outcome(matched=True)))
        bundle_dir = self._bundle(report, lines)
        self.assertEqual(verify_bundle(bundle_dir), [])


class TestBundleErrors(unittest.TestCase):
    def test_create_bundle_raises_on_a_headerless_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            report_path = _write_report(tmp, REPORT_F1_SHAPE)
            record_path = tmp / "record.jsonl"
            record_path.write_text(json.dumps({"type": "run"}) + "\n", encoding="utf-8")
            with self.assertRaises(BundleError):
                create_bundle(report_path, record_path, tmp / "out")


if __name__ == "__main__":
    unittest.main()
