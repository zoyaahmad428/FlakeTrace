import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.baseline import FailureSignature, RunTally, TestIdentifier
from eval.report import UnhandledStatus, assemble_report
from eval.schema_validator import validate_report
from evidence.extract import find_edges, report_fields
from runner.diagnose import DiagnosisRuns, INCONSISTENT, NOT_REPRODUCED, POLLUTER_FOUND, VICTIM_FAILS_ALONE
from runner.integrity import SourceIntegrity

POLLUTER = TestIdentifier("odfixture.ConfigPolluterTest", "pollute")
VICTIM = TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode")
REF = FailureSignature("java.lang.AssertionError", "odfixture.ConfigVictimTest.expectsDefaultMode:10",
                        "expected:<0> but was:<1>")
DIFFERENT = FailureSignature("java.lang.IllegalStateException", "at V.t(V.java:22)")
INTEGRITY_OK = SourceIntegrity(True, "19 files hashed; all identical")
INTEGRITY_FAILED = SourceIntegrity(False, "changed: src/main/java/odfixture/Config.java")

# Literal Output-1 shapes exactly as evidence.extract.find_edges expects them (as produced by
# evidence.extract.analyse_test) -- hand-written here to drive Member 1's real find_edges/
# report_fields with known inputs, not a fake of Member 1's extractor.
POLLUTER_ID = "odfixture.ConfigPolluterTest#pollute"
VICTIM_ID = "odfixture.ConfigVictimTest#expectsDefaultMode"
POLLUTER_ACCESS = {
    "test": {"class": "odfixture.ConfigPolluterTest", "method": "pollute"},
    "accesses": [{
        "category": "static-field", "resource_id": "odfixture.Config#mode",
        "resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
        "access": "WRITE", "class": "odfixture.ConfigPolluterTest", "method": "pollute",
        "bytecode_offset": 1, "depth": 1,
    }],
    "unsupported_observations": [],
}
VICTIM_ACCESS = {
    "test": {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"},
    "accesses": [{
        "category": "static-field", "resource_id": "odfixture.Config#mode",
        "resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
        "access": "READ", "class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode",
        "bytecode_offset": 1, "depth": 1,
    }],
    "unsupported_observations": [],
}
NO_SHARED_RESOURCE_ACCESS = {
    "test": {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"},
    "accesses": [],
    "unsupported_observations": [],
}


def resource_fields(polluter_access, victim_access):
    """Drive the report fields through Member 1's real pair-mode functions, the way
    eval/tools/run_w9_integration.py does -- not through a local correlation function."""
    pair = find_edges(POLLUTER_ID, polluter_access, VICTIM_ID, victim_access)
    return report_fields(pair)


class TestResourceFieldsViaM1(unittest.TestCase):
    """find_edges/report_fields are Member 1's; these tests only check this module calls
    them correctly and reads their output the way assemble_report expects."""

    def test_finds_the_shared_resource(self):
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        self.assertEqual(fields["shared_resource"], {"kind": "static-field", "class": "odfixture.Config", "field": "mode"})
        self.assertEqual(fields["polluter_write_location"],
                          {"class": "odfixture.ConfigPolluterTest", "method": "pollute", "bytecode_offset": 1})
        self.assertEqual(fields["victim_read_location"],
                          {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode", "bytecode_offset": 1})
        self.assertIn("Static analysis only; no runtime evidence (Iteration 2).", fields["limitations"])

    def test_no_shared_resource_gives_none_fields(self):
        fields = resource_fields(POLLUTER_ACCESS, NO_SHARED_RESOURCE_ACCESS)
        self.assertIsNone(fields["shared_resource"])


def _tally(n, passed, matched=0, other=0, infra=0):
    return RunTally(n=n, passed=passed, matched=matched, other=other, infra=infra)


def _diagnosis(status, *, alone_tally=None, sequence_tally=None, **overrides):
    """A DiagnosisRuns whose old scalar fields agree with its tallies (mirrors
    runner.diagnose._runs). Defaults: always passes alone, sequence always reproduces 20/20 --
    each test overrides only the tally it needs to hit its own decision-table row."""
    alone_tally = alone_tally if alone_tally is not None else _tally(20, 20)
    sequence_tally = sequence_tally if sequence_tally is not None else _tally(20, 0, matched=20)
    defaults = dict(
        status=status, victim=VICTIM, original_order=[POLLUTER, VICTIM],
        reference_signature=REF, polluters=[POLLUTER], sequence=[POLLUTER, VICTIM],
        sequence_n=sequence_tally.n, sequence_successes=sequence_tally.matched,
        sequence_any_failures=sequence_tally.n - sequence_tally.passed,
        alone_n=alone_tally.n, alone_successes=alone_tally.matched, search_runs=1,
        source_integrity=INTEGRITY_OK, execution_record="/tmp/record.jsonl",
        alone_tally=alone_tally, sequence_tally=sequence_tally,
    )
    defaults.update(overrides)
    return DiagnosisRuns(**defaults)


class TestAssembleReport(unittest.TestCase):
    def test_polluter_found_with_edge_gives_verified(self):
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(_diagnosis(POLLUTER_FOUND), fields)
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["outcome"], "VERIFIED")
        self.assertIsNone(report["unresolved_reason"])
        self.assertEqual(report["candidate_reasons"], [])
        self.assertEqual(report["shared_resource"], fields["shared_resource"])
        self.assertEqual(report["resource_edges"], [{
            "shared_resource": fields["shared_resource"],
            "polluter_write_location": fields["polluter_write_location"],
            "victim_read_location": fields["victim_read_location"],
        }])
        self.assertEqual(report["polluters"], [POLLUTER.to_dict()])
        self.assertEqual(report["assurance"]["sequence"]["deletion"], "NOT_YET_CHECKED")
        self.assertEqual(report["assurance"]["resource"]["level"], "STATIC_OVERLAP")
        self.assertIn("Static analysis only; no runtime evidence (Iteration 2).", report["limitations"])
        validate_report(report)  # must not raise

    def test_polluter_found_without_edge_gives_candidate(self):
        """ADR-010 section 4 (Q1, option A, agreed 2026-11-13): a reproducing, passes-alone
        sequence with no resource edge is CANDIDATE now, not UNRESOLVED -- the Mid's
        NO_SUPPORTED_RESOURCE_EVIDENCE abstention is retired."""
        report = assemble_report(_diagnosis(POLLUTER_FOUND), resource_fields=None)
        self.assertEqual(report["outcome"], "CANDIDATE")
        self.assertIsNone(report["unresolved_reason"])
        self.assertEqual(report["candidate_reasons"], ["NO_SUPPORTED_RESOURCE_EVIDENCE"])
        self.assertIsNone(report["shared_resource"])
        self.assertEqual(report["resource_edges"], [])
        self.assertEqual(report["assurance"]["resource"]["level"], "NONE")
        self.assertIn(
            "No polluter-write/victim-read resource edge was found by static analysis.",
            report["limitations"],
        )
        validate_report(report)

    def test_several_polluters_partial_evidence_suppresses_the_generic_no_edge_line(self):
        """W10 (ADR-007): a caller combining several polluters' pair-mode results can set
        shared_resource=None (not every polluter has an edge, so none is shown as the primary
        resource) while any_edge_found=True (some polluter did have one) and name the specifics
        in limitations. The generic blanket line would contradict that and must not appear."""
        fields = {
            "shared_resource": None, "polluter_write_location": None, "victim_read_location": None,
            "instrumentation_level": "static-only", "any_edge_found": True,
            "limitations": [
                "Polluter odfixture.ToggleAPolluterTest#setFlagA: shared resource "
                "odfixture.Toggles#flagA was found, but not every polluter has evidence",
                "No polluter-write/victim-read resource edge was found for polluter "
                "odfixture.ToggleBPolluterTest#setFlagB",
            ],
        }
        diagnosis = _diagnosis(POLLUTER_FOUND, polluters=[POLLUTER, TestIdentifier("x", "y")])
        report = assemble_report(diagnosis, fields)
        # any_edge_found=True still gives no resource_edges entry (shared_resource is None, the
        # edge Member 1 DID find for the other polluter is only free text in limitations today).
        self.assertEqual(report["candidate_reasons"], ["NO_SUPPORTED_RESOURCE_EVIDENCE"])
        self.assertIsNone(report["shared_resource"])
        self.assertEqual(report["resource_edges"], [])
        self.assertNotIn(
            "No polluter-write/victim-read resource edge was found by static analysis.",
            report["limitations"],
        )
        self.assertIn(
            "Polluter odfixture.ToggleAPolluterTest#setFlagA: shared resource "
            "odfixture.Toggles#flagA was found, but not every polluter has evidence",
            report["limitations"],
        )
        validate_report(report)

    def test_several_polluters_zero_evidence_keeps_the_generic_no_edge_line(self):
        """Same shape as above, but no polluter had any edge at all (any_edge_found=False) --
        the generic line is the correct, non-contradictory thing to say here."""
        fields = {
            "shared_resource": None, "polluter_write_location": None, "victim_read_location": None,
            "instrumentation_level": "static-only", "any_edge_found": False,
            "limitations": ["No polluter-write/victim-read resource edge was found for polluter x#y"],
        }
        diagnosis = _diagnosis(POLLUTER_FOUND, polluters=[POLLUTER, TestIdentifier("x", "y")])
        report = assemble_report(diagnosis, fields)
        self.assertIn(
            "No polluter-write/victim-read resource edge was found by static analysis.",
            report["limitations"],
        )
        validate_report(report)

    def test_polluter_found_weak_reproduction_gives_candidate(self):
        diagnosis = _diagnosis(POLLUTER_FOUND, sequence_tally=_tally(20, 8, matched=12))
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, fields)
        self.assertEqual(report["outcome"], "CANDIDATE")
        self.assertEqual(report["candidate_reasons"], ["BELOW_REPLAY_THRESHOLD"])
        self.assertEqual(report["assurance"]["sequence"]["reproduces"], "NOT_ESTABLISHED")
        validate_report(report)

    def test_source_integrity_failed_overrides_everything(self):
        diagnosis = _diagnosis(POLLUTER_FOUND, source_integrity=INTEGRITY_FAILED)
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, fields)
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "SOURCE_INTEGRITY_FAILED")
        self.assertFalse(report["source_integrity"]["passed"])
        validate_report(report)

    def test_victim_fails_alone_gives_unresolved(self):
        diagnosis = _diagnosis(
            VICTIM_FAILS_ALONE, polluters=[], sequence=[VICTIM],
            sequence_tally=_tally(20, 0, matched=20), alone_tally=_tally(20, 0, matched=20),
        )
        report = assemble_report(diagnosis)  # no resource_fields argument -- not relevant here
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "VICTIM_FAILS_ALONE")
        self.assertEqual(report["polluters"], [])
        self.assertIsNone(report["shared_resource"])
        validate_report(report)

    def test_victim_fails_alone_ignores_a_passed_in_edge(self):
        """Even if a caller mistakenly passes resource_fields for a VICTIM_FAILS_ALONE
        diagnosis, it must not be used -- the gate fires before resource evidence matters."""
        diagnosis = _diagnosis(
            VICTIM_FAILS_ALONE, polluters=[], sequence=[VICTIM],
            alone_tally=_tally(20, 15, matched=5),
        )
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, resource_fields=fields)
        self.assertIsNone(report["shared_resource"])
        self.assertEqual(report["unresolved_reason"], "VICTIM_FAILS_ALONE")

    def test_victim_fails_alone_differently_blames_no_test(self):
        """ADR-010 row 7, FT003, T1: the victim fails alone with a DIFFERENT signature. The
        search (W18) keeps going and finds a polluter for the reference signature, but the
        report must not blame it -- the correctexpected ADR-010 regression for the Mid's bug."""
        diagnosis = _diagnosis(
            POLLUTER_FOUND, alone_tally=_tally(20, 0, other=20),
            sequence_tally=_tally(20, 0, matched=20),
        )
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, fields)
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "VICTIM_FAILS_ALONE_DIFFERENTLY")
        self.assertEqual(report["polluters"], [])
        self.assertEqual(report["reduced_sequence"], [VICTIM.to_dict()])
        # The resource evidence names the un-blamed polluter -- withheld along with it.
        self.assertIsNone(report["shared_resource"])
        self.assertEqual(report["resource_edges"], [])
        self.assertTrue(any("no test is blamed" in line for line in report["limitations"]))
        validate_report(report)

    def test_victim_fails_alone_differently_intermittently_blames_no_test(self):
        """ADR-010 row 7, T2: only some alone runs differ -- still no match, still no blame."""
        diagnosis = _diagnosis(
            POLLUTER_FOUND, alone_tally=_tally(20, 17, other=3),
            sequence_tally=_tally(20, 0, matched=20),
        )
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, fields)
        self.assertEqual(report["unresolved_reason"], "VICTIM_FAILS_ALONE_DIFFERENTLY")
        self.assertEqual(report["polluters"], [])
        validate_report(report)

    def test_alone_infrastructure_failure_blames_no_test(self):
        """ADR-010 row 8, T3: the victim crashes/times out sometimes when run alone -- strict,
        withholds VERIFIED even though the sequence reproduces reliably, and blames no test."""
        diagnosis = _diagnosis(
            POLLUTER_FOUND, alone_tally=_tally(20, 18, infra=2),
            sequence_tally=_tally(20, 0, matched=20),
        )
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, fields)
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "INFRASTRUCTURE_FAILURE")
        self.assertEqual(report["polluters"], [])
        self.assertTrue(any("no test is blamed" in line for line in report["limitations"]))
        validate_report(report)

    def test_inconsistent_gives_a_real_report_not_unhandled(self):
        """ADR-010 section 5, FT010, T4: INCONSISTENT (formerly NO_SINGLE_POLLUTER) now gets a
        schema-valid report instead of UnhandledStatus/exit code 3."""
        diagnosis = _diagnosis(
            INCONSISTENT, polluters=[], sequence=[POLLUTER, VICTIM],
            sequence_tally=_tally(20, 20, matched=0), alone_tally=_tally(20, 20, matched=0),
        )
        report = assemble_report(diagnosis)
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "INCONSISTENT_OUTCOMES")
        self.assertEqual(report["polluters"], [])
        # ADR-010 section 5: reduced_sequence is the starting order, not collapsed to [victim] --
        # no polluter was ever found here to un-blame.
        self.assertEqual(report["reduced_sequence"], [POLLUTER.to_dict(), VICTIM.to_dict()])
        self.assertIsNotNone(report["failure_signature"])
        self.assertTrue(any("could not be obtained again" in line for line in report["limitations"]))
        validate_report(report)

    def test_not_reproduced_with_todays_real_shape_is_unhandled_not_a_crash(self):
        """A hand-built NOT_REPRODUCED diagnosis with alone_n=0 (the pre-ADR-008 shape) must
        fail loudly (UnhandledStatus), not with a bare ValueError the CLI does not catch."""
        diagnosis = _diagnosis(
            NOT_REPRODUCED, polluters=[], sequence=[POLLUTER, VICTIM], reference_signature=None,
            sequence_tally=_tally(5, 5, matched=0), alone_tally=_tally(5, 5, matched=0),
            alone_n=0, alone_successes=0,
        )
        with self.assertRaises(UnhandledStatus):
            assemble_report(diagnosis)

    def test_not_reproduced_with_isolation_data_gives_unresolved(self):
        """ADR-008's real shape: alone_n > 0 even though nothing ever reproduced."""
        diagnosis = _diagnosis(
            NOT_REPRODUCED, polluters=[], sequence=[POLLUTER, VICTIM], reference_signature=None,
            sequence_tally=_tally(20, 20, matched=0), alone_tally=_tally(20, 20, matched=0),
            order_given=True,
        )
        report = assemble_report(diagnosis)
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "NOT_REPRODUCED")
        self.assertIsNone(report["failure_signature"])
        self.assertIsNone(report["shared_resource"])
        self.assertEqual(report["polluters"], [])
        self.assertTrue(any("Not reproduced: 20 runs of the given order," in line
                            for line in report["limitations"]))
        self.assertEqual(report["order_exploration"]["infrastructure_failures"], 0)
        validate_report(report)

    def test_not_reproduced_names_discovered_order_and_shuffle_count(self):
        diagnosis = _diagnosis(
            NOT_REPRODUCED, polluters=[], sequence=[POLLUTER, VICTIM], reference_signature=None,
            sequence_tally=_tally(20, 20, matched=0), alone_tally=_tally(20, 20, matched=0),
            order_given=False, shuffled_orders=3, orders_exhausted=True,
        )
        report = assemble_report(diagnosis)
        self.assertTrue(any(
            "Not reproduced: 20 runs of the discovered order (plus 3 shuffled order(s))," in line
            for line in report["limitations"]
        ))
        self.assertEqual(report["order_exploration"]["shuffled_orders_tried"], 3)
        validate_report(report)

    def test_infrastructure_failure_within_sequence_gives_unresolved_with_null_signature(self):
        diagnosis = _diagnosis(
            NOT_REPRODUCED, polluters=[], sequence=[POLLUTER, VICTIM], reference_signature=None,
            sequence_tally=_tally(20, 15, matched=0, infra=5), alone_tally=_tally(20, 20, matched=0),
            infrastructure_failures=5,
        )
        report = assemble_report(diagnosis)
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "INFRASTRUCTURE_FAILURE")
        self.assertIsNone(report["failure_signature"])
        self.assertTrue(any("crashed or timed out" in line for line in report["limitations"]))
        self.assertEqual(report["order_exploration"]["infrastructure_failures"], 5)
        validate_report(report)

    def test_infrastructure_failure_elsewhere_gives_unresolved_with_null_signature(self):
        diagnosis = _diagnosis(
            NOT_REPRODUCED, polluters=[], sequence=[POLLUTER, VICTIM], reference_signature=None,
            sequence_tally=_tally(20, 20, matched=0), alone_tally=_tally(20, 16, matched=0, infra=4),
            alone_infrastructure_failures=4,
        )
        report = assemble_report(diagnosis)
        self.assertEqual(report["outcome"], "UNRESOLVED")
        self.assertEqual(report["unresolved_reason"], "INFRASTRUCTURE_FAILURE")
        self.assertIsNone(report["failure_signature"])
        self.assertTrue(any(
            "never failed for real in 20 runs, but 4 run(s) somewhere" in line for line in report["limitations"]
        ))
        self.assertEqual(report["order_exploration"]["infrastructure_failures"], 4)
        validate_report(report)

    def test_missing_tallies_is_a_value_error_not_a_crash_elsewhere(self):
        diagnosis = DiagnosisRuns(
            status=POLLUTER_FOUND, victim=VICTIM, original_order=[POLLUTER, VICTIM],
            reference_signature=REF, polluters=[POLLUTER], sequence=[POLLUTER, VICTIM],
            sequence_n=20, sequence_successes=20, sequence_any_failures=20,
            alone_n=20, alone_successes=0, search_runs=1,
            source_integrity=INTEGRITY_OK, execution_record="/tmp/record.jsonl",
        )
        with self.assertRaises(ValueError):
            assemble_report(diagnosis)


if __name__ == "__main__":
    unittest.main()
