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
        search_runs=1,
        source_integrity=INTEGRITY_OK, execution_record="/tmp/record.jsonl",
        alone_tally=alone_tally, sequence_tally=sequence_tally,
    )
    defaults.update(overrides)
    return DiagnosisRuns(**defaults)


EDGE_A = {"shared_resource": {"kind": "static-field", "class": "odfixture.Toggles", "field": "flagA"},
          "polluter_write_location": {"class": "odfixture.ToggleAPolluterTest", "method": "setFlagA", "bytecode_offset": 1},
          "victim_read_location": {"class": "odfixture.ToggleVictimTest", "method": "v", "bytecode_offset": 1},
          "depth": 2}
EDGE_B = dict(EDGE_A, shared_resource={"kind": "static-field", "class": "odfixture.Toggles", "field": "flagB"},
              polluter_write_location={"class": "odfixture.ToggleBPolluterTest", "method": "setFlagB", "bytecode_offset": 1})


class TestResourceEdgesFromM1(unittest.TestCase):
    """W21 (PR #105) + W19: the report lists every edge Member 1's report_fields gives, with depth."""

    def test_two_polluters_two_edges_are_both_listed(self):
        fields = {"shared_resource": EDGE_A["shared_resource"],
                  "polluter_write_location": EDGE_A["polluter_write_location"],
                  "victim_read_location": EDGE_A["victim_read_location"],
                  "instrumentation_level": "static-only", "limitations": [],
                  "resource_edges": [EDGE_A, EDGE_B]}
        report = assemble_report(_diagnosis(POLLUTER_FOUND, polluters=[POLLUTER, TestIdentifier("x", "y")]), fields)
        self.assertEqual(report["resource_edges"], [EDGE_A, EDGE_B])
        self.assertFalse([line for line in report["limitations"] if "lists only the primary edge" in line])
        validate_report(report)


class TestDeletionEvidenceBeforeW20(unittest.TestCase):
    """ADR-010 claim S3 with ADR-011 sections 2 and 4, decided 2026-11-19 (M2, with M3's permission):
    one polluter is deletion-verified by the alone check; two or more are INCOMPLETE until W20."""

    def edge_fields(self):
        return {"shared_resource": EDGE_A["shared_resource"],
                "polluter_write_location": EDGE_A["polluter_write_location"],
                "victim_read_location": EDGE_A["victim_read_location"],
                "instrumentation_level": "static-only", "limitations": [], "resource_edges": [EDGE_A, EDGE_B]}

    def test_one_polluter_passing_alone_is_deletion_verified(self):
        report = assemble_report(_diagnosis(POLLUTER_FOUND), resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS))
        self.assertEqual((report["outcome"], report["assurance"]["sequence"]["deletion"]), ("VERIFIED", "DELETION_VERIFIED"))
        self.assertTrue(any("alone" in line.lower() and "deletion" in line.lower() for line in report["limitations"]), report["limitations"])

    def test_two_polluters_without_deletion_runs_are_candidate_incomplete(self):
        diagnosis = _diagnosis(POLLUTER_FOUND, polluters=[POLLUTER, TestIdentifier("x", "y")])
        report = assemble_report(diagnosis, self.edge_fields())
        self.assertEqual(report["outcome"], "CANDIDATE")
        self.assertEqual(report["candidate_reasons"], ["DELETION_EVIDENCE_INCOMPLETE"])
        self.assertEqual(report["assurance"]["sequence"]["deletion"], "INCOMPLETE")
        validate_report(report)


class TestAssembleReport(unittest.TestCase):
    def test_polluter_found_with_edge_gives_verified(self):
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(_diagnosis(POLLUTER_FOUND), fields)
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(report["outcome"], "VERIFIED")
        self.assertIsNone(report["unresolved_reason"])
        self.assertEqual(report["candidate_reasons"], [])
        self.assertEqual(report["shared_resource"], fields["shared_resource"])
        # W21 (PR #105): every edge Member 1 found, each with its depth (ADR-010 section 6).
        self.assertEqual(report["resource_edges"], fields["resource_edges"])
        self.assertEqual(report["resource_edges"][0]["shared_resource"], fields["shared_resource"])
        self.assertIn("depth", report["resource_edges"][0])
        self.assertEqual(report["polluters"], [POLLUTER.to_dict()])
        # ADR-011 section 2: for one polluter the alone check IS the deletion check.
        self.assertEqual(report["assurance"]["sequence"]["deletion"], "DELETION_VERIFIED")
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

    def test_two_polluters_with_a_real_edge_gives_candidate_not_verified(self):
        """A1 fail-safe fix (2026-11-19): ADR-011 section 2's free deletion check only covers
        ONE kept polluter (the alone check proves it). Two or more kept polluters -- e.g.
        fixture F3, both required -- have no such free check and W20's real one hasn't
        landed, so even a real resource edge and clean reproduction only gives CANDIDATE, not
        VERIFIED. Never claim F3 is VERIFIED until W20 actually builds the multi-test check."""
        diagnosis = _diagnosis(POLLUTER_FOUND, polluters=[POLLUTER, TestIdentifier("x", "y")])
        fields = resource_fields(POLLUTER_ACCESS, VICTIM_ACCESS)
        report = assemble_report(diagnosis, fields)
        self.assertEqual(report["outcome"], "CANDIDATE")
        self.assertIsNone(report["unresolved_reason"])
        self.assertEqual(report["candidate_reasons"], ["DELETION_EVIDENCE_INCOMPLETE"])
        # M2's W20-precursor fix (2026-11-19, with M3's permission): two kept polluters get the
        # real ADR-011 value DELETION_INCOMPLETE now, not a placeholder NOT_YET_CHECKED.
        self.assertEqual(report["assurance"]["sequence"]["deletion"], "INCOMPLETE")
        self.assertEqual(report["assurance"]["resource"]["level"], "STATIC_OVERLAP")
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
        fields["resource_edges"] = [EDGE_A]
        diagnosis = _diagnosis(POLLUTER_FOUND, polluters=[POLLUTER, TestIdentifier("x", "y")])
        report = assemble_report(diagnosis, fields)
        # W21: the edge Member 1 DID find is listed structurally, though not every polluter has one.
        # Two polluters and no W20 deletion runs: also DELETION_EVIDENCE_INCOMPLETE (2026-11-19).
        self.assertEqual(report["candidate_reasons"], ["DELETION_EVIDENCE_INCOMPLETE", "NO_SUPPORTED_RESOURCE_EVIDENCE"])
        self.assertIsNone(report["shared_resource"])
        self.assertEqual(report["resource_edges"], [EDGE_A])
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
        """A hand-built NOT_REPRODUCED diagnosis with no alone runs (the pre-ADR-008 shape) must
        fail loudly (UnhandledStatus), not with a bare ValueError the CLI does not catch."""
        diagnosis = _diagnosis(
            NOT_REPRODUCED, polluters=[], sequence=[POLLUTER, VICTIM], reference_signature=None,
            sequence_tally=_tally(5, 5, matched=0), alone_tally=_tally(0, 0, matched=0),
        )
        with self.assertRaises(UnhandledStatus):
            assemble_report(diagnosis)

    def test_not_reproduced_with_isolation_data_gives_unresolved(self):
        """ADR-008's real shape: alone runs were made even though nothing ever reproduced."""
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
            sequence_tally=None, alone_tally=None, search_runs=1,  # required since A4; None still guarded
            source_integrity=INTEGRITY_OK, execution_record="/tmp/record.jsonl",
        )
        with self.assertRaises(ValueError):
            assemble_report(diagnosis)


if __name__ == "__main__":
    unittest.main()
