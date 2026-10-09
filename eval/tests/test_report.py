import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.baseline import FailureSignature, TestIdentifier
from eval.report import UnhandledStatus, assemble_report, find_resource_edge
from eval.schema_validator import validate_report
from runner.diagnose import DiagnosisRuns, NOT_REPRODUCED, NO_SINGLE_POLLUTER, POLLUTER_FOUND, VICTIM_FAILS_ALONE
from runner.integrity import SourceIntegrity

POLLUTER = TestIdentifier("odfixture.ConfigPolluterTest", "pollute")
VICTIM = TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode")
REF = FailureSignature("java.lang.AssertionError", "odfixture.ConfigVictimTest.expectsDefaultMode:10",
                        "expected:<0> but was:<1>")
INTEGRITY_OK = SourceIntegrity(True, "19 files hashed; all identical")
INTEGRITY_FAILED = SourceIntegrity(False, "changed: src/main/java/odfixture/Config.java")

# Literal Output-1 shapes exactly as eval.report.find_resource_edge expects them (as produced
# by evidence.extract.analyse_test) -- hand-written here to test my own correlation function
# in isolation, not a fake of Member 1's extractor.
POLLUTER_ACCESS = {
    "test": {"class": "odfixture.ConfigPolluterTest", "method": "pollute"},
    "accesses": [{
        "category": "static-field", "resource_id": "odfixture.Config#mode",
        "resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
        "access": "WRITE", "class": "odfixture.ConfigPolluterTest", "method": "pollute",
        "bytecode_offset": 1, "depth": 1,
    }],
}
VICTIM_ACCESS = {
    "test": {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"},
    "accesses": [{
        "category": "static-field", "resource_id": "odfixture.Config#mode",
        "resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
        "access": "READ", "class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode",
        "bytecode_offset": 1, "depth": 1,
    }],
}
NO_SHARED_RESOURCE_ACCESS = {
    "test": {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"},
    "accesses": [],
}


class TestFindResourceEdge(unittest.TestCase):
    def test_finds_the_shared_resource(self):
        edge = find_resource_edge(POLLUTER_ACCESS, VICTIM_ACCESS)
        self.assertIsNotNone(edge)
        self.assertEqual(edge["resource"], {"kind": "static-field", "class": "odfixture.Config", "field": "mode"})
        self.assertEqual(edge["polluter_write_location"],
                          {"class": "odfixture.ConfigPolluterTest", "method": "pollute", "bytecode_offset": 1})
        self.assertEqual(edge["victim_read_location"],
                          {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode", "bytecode_offset": 1})

    def test_no_shared_resource_returns_none(self):
        self.assertIsNone(find_resource_edge(POLLUTER_ACCESS, NO_SHARED_RESOURCE_ACCESS))

    def test_picks_lowest_combined_depth_when_multiple_shared(self):
        polluter_two_writes = {
            "accesses": [
                {"resource_id": "a", "access": "WRITE", "resource": {"kind": "static-field", "class": "X", "field": "a"},
                 "class": "P", "method": "p", "bytecode_offset": 1, "depth": 2},
                {"resource_id": "b", "access": "WRITE", "resource": {"kind": "static-field", "class": "X", "field": "b"},
                 "class": "P", "method": "p", "bytecode_offset": 2, "depth": 1},
            ]
        }
        victim_two_reads = {
            "accesses": [
                {"resource_id": "a", "access": "READ", "resource": {"kind": "static-field", "class": "X", "field": "a"},
                 "class": "V", "method": "v", "bytecode_offset": 1, "depth": 1},
                {"resource_id": "b", "access": "READ", "resource": {"kind": "static-field", "class": "X", "field": "b"},
                 "class": "V", "method": "v", "bytecode_offset": 2, "depth": 1},
            ]
        }
        # "a": write depth 2 + read depth 1 = 3. "b": write depth 1 + read depth 1 = 2 (lower, wins).
        edge = find_resource_edge(polluter_two_writes, victim_two_reads)
        self.assertEqual(edge["resource"]["field"], "b")


def _diagnosis(status, **overrides):
    defaults = dict(
        status=status, victim=VICTIM, original_order=[POLLUTER, VICTIM],
        reference_signature=REF, polluters=[POLLUTER], sequence=[POLLUTER, VICTIM],
        sequence_n=20, sequence_successes=20, sequence_any_failures=20,
        alone_n=20, alone_successes=0, search_runs=1,
        source_integrity=INTEGRITY_OK, execution_record="/tmp/record.jsonl",
    )
    defaults.update(overrides)
    return DiagnosisRuns(**defaults)


class TestAssembleReport(unittest.TestCase):
    def test_polluter_found_with_edge_gives_verified(self):
        edge = find_resource_edge(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(_diagnosis(POLLUTER_FOUND), edge)
        self.assertEqual(report["outcome"], "VERIFIED")
        self.assertIsNone(report["unresolved_reason"])
        self.assertEqual(report["shared_resource"], edge["resource"])
        self.assertEqual(report["polluters"], [POLLUTER.to_dict()])
        validate_report(report)  # must not raise

    def test_polluter_found_without_edge_gives_no_supported_resource_evidence(self):
        report = assemble_report(_diagnosis(POLLUTER_FOUND), resource_edge=None)
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "NO_SUPPORTED_RESOURCE_EVIDENCE")
        self.assertIsNone(report["shared_resource"])
        validate_report(report)

    def test_polluter_found_weak_reproduction_gives_candidate(self):
        diagnosis = _diagnosis(POLLUTER_FOUND, sequence_successes=12, sequence_any_failures=12)
        edge = find_resource_edge(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, edge)
        self.assertEqual(report["outcome"], "CANDIDATE")
        validate_report(report)

    def test_source_integrity_failed_overrides_everything(self):
        diagnosis = _diagnosis(POLLUTER_FOUND, source_integrity=INTEGRITY_FAILED)
        edge = find_resource_edge(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, edge)
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "SOURCE_INTEGRITY_FAILED")
        self.assertFalse(report["source_integrity"]["passed"])
        validate_report(report)

    def test_victim_fails_alone_gives_unresolved(self):
        diagnosis = _diagnosis(
            VICTIM_FAILS_ALONE, polluters=[], sequence=[VICTIM],
            sequence_n=20, sequence_successes=20, sequence_any_failures=20,
            alone_n=20, alone_successes=20,
        )
        report = assemble_report(diagnosis)  # no resource_edge argument -- not relevant here
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "VICTIM_FAILS_ALONE")
        self.assertEqual(report["polluters"], [])
        self.assertIsNone(report["shared_resource"])
        validate_report(report)

    def test_victim_fails_alone_ignores_a_passed_in_edge(self):
        """Even if a caller mistakenly passes a resource_edge for a VICTIM_FAILS_ALONE
        diagnosis, it must not be used -- the gate fires before resource evidence matters."""
        diagnosis = _diagnosis(
            VICTIM_FAILS_ALONE, polluters=[], sequence=[VICTIM],
            alone_n=20, alone_successes=5,
        )
        edge = find_resource_edge(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, resource_edge=edge)
        self.assertIsNone(report["shared_resource"])
        self.assertEqual(report["unresolved_reason"], "VICTIM_FAILS_ALONE")

    def test_not_reproduced_is_unhandled(self):
        diagnosis = _diagnosis(
            NOT_REPRODUCED, polluters=[], sequence=[POLLUTER, VICTIM], reference_signature=None,
            sequence_n=5, sequence_successes=0, sequence_any_failures=0,
            alone_n=0, alone_successes=0,
        )
        with self.assertRaises(UnhandledStatus):
            assemble_report(diagnosis)

    def test_no_single_polluter_is_unhandled(self):
        diagnosis = _diagnosis(NO_SINGLE_POLLUTER, polluters=[], sequence=[POLLUTER, VICTIM])
        with self.assertRaises(UnhandledStatus):
            assemble_report(diagnosis)


if __name__ == "__main__":
    unittest.main()
