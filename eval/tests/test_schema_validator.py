import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import jsonschema

from eval.schema_validator import load_schema, validate_report

VALID_REPORT = {
    "schema_version": 2,
    "victim": {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"},
    "polluters": [{"class": "odfixture.ConfigPolluterTest", "method": "pollute"}],
    "original_failing_order": [
        {"class": "odfixture.ConfigPolluterTest", "method": "pollute"},
        {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"},
    ],
    "reduced_sequence": [
        {"class": "odfixture.ConfigPolluterTest", "method": "pollute"},
        {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode"},
    ],
    "reproduction": {"n": 20, "passed": 0, "matched": 20, "other": 0, "infra": 0, "confidence": 0.95, "lower": 0.838, "upper": 1.0},
    "victim_alone": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0, "confidence": 0.95, "lower": 0.0, "upper": 0.161},
    "shared_resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
    "polluter_write_location": {"class": "odfixture.ConfigPolluterTest", "method": "pollute", "bytecode_offset": 3},
    "victim_read_location": {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode", "bytecode_offset": 5},
    "resource_edges": [{
        "shared_resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
        "polluter_write_location": {"class": "odfixture.ConfigPolluterTest", "method": "pollute", "bytecode_offset": 3},
        "victim_read_location": {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode", "bytecode_offset": 5},
    }],
    "failure_signature": {
        "exception_type": "java.lang.AssertionError",
        "message": "expected:<0> but was:<1>",
        "stack_trace": "at odfixture.ConfigVictimTest.expectsDefaultMode(ConfigVictimTest.java:10)",
    },
    "instrumentation_level": "static-only",
    "execution_record_reference": "exec-123",
    "source_integrity": {"passed": True, "details": "ok"},
    "outcome": "VERIFIED",
    "unresolved_reason": None,
    "candidate_reasons": [],
    "limitations": [],
    "assurance": {
        "sequence": {"reproduces": "ESTABLISHED", "passes_alone": "ESTABLISHED", "deletion": "NOT_YET_CHECKED"},
        "resource": {"level": "STATIC_OVERLAP", "mechanism": "NOT_ASSESSED"},
    },
}


class TestSchemaItself(unittest.TestCase):
    def test_schema_loads_and_is_itself_valid_json_schema(self):
        schema = load_schema()
        jsonschema.Draft202012Validator.check_schema(schema)


class TestValidateReport(unittest.TestCase):
    def test_valid_report_passes(self):
        validate_report(VALID_REPORT)  # must not raise

    def test_missing_required_field_fails(self):
        bad = copy.deepcopy(VALID_REPORT)
        del bad["victim"]
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_wrong_schema_version_fails(self):
        bad = copy.deepcopy(VALID_REPORT)
        bad["schema_version"] = 1
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_unknown_outcome_value_fails(self):
        bad = copy.deepcopy(VALID_REPORT)
        bad["outcome"] = "DEFINITELY_A_BUG"
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_unresolved_without_reason_fails(self):
        bad = copy.deepcopy(VALID_REPORT)
        bad["outcome"] = "UNRESOLVED"
        bad["unresolved_reason"] = None
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_verified_with_a_reason_fails(self):
        bad = copy.deepcopy(VALID_REPORT)
        bad["outcome"] = "VERIFIED"
        bad["unresolved_reason"] = "NOT_REPRODUCED"
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_unresolved_with_reason_passes(self):
        ok = copy.deepcopy(VALID_REPORT)
        ok["outcome"] = "UNRESOLVED"
        ok["unresolved_reason"] = "VICTIM_FAILS_ALONE"
        del ok["assurance"]  # not required/shown for UNRESOLVED
        validate_report(ok)  # must not raise

    def test_retired_unresolved_reason_fails(self):
        """ADR-010 (2026-11-13): NO_SUPPORTED_RESOURCE_EVIDENCE and BELOW_CONFIDENCE_THRESHOLD
        are retired as UNRESOLVED reasons -- see candidate_reasons instead."""
        bad = copy.deepcopy(VALID_REPORT)
        bad["outcome"] = "UNRESOLVED"
        bad["unresolved_reason"] = "NO_SUPPORTED_RESOURCE_EVIDENCE"
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_additional_property_rejected(self):
        bad = copy.deepcopy(VALID_REPORT)
        bad["totally_made_up_field"] = 1
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_candidate_requires_at_least_one_reason(self):
        bad = copy.deepcopy(VALID_REPORT)
        bad["outcome"] = "CANDIDATE"
        bad["unresolved_reason"] = None
        bad["candidate_reasons"] = []
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_candidate_with_a_reason_passes(self):
        ok = copy.deepcopy(VALID_REPORT)
        ok["outcome"] = "CANDIDATE"
        ok["unresolved_reason"] = None
        ok["candidate_reasons"] = ["NO_SUPPORTED_RESOURCE_EVIDENCE"]
        validate_report(ok)  # must not raise

    def test_verified_cannot_carry_candidate_reasons(self):
        bad = copy.deepcopy(VALID_REPORT)
        bad["candidate_reasons"] = ["BELOW_REPLAY_THRESHOLD"]
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_not_reproduced_with_null_failure_signature_passes(self):
        """Row 5: no reference was ever established."""
        ok = copy.deepcopy(VALID_REPORT)
        ok["outcome"] = "UNRESOLVED"
        ok["unresolved_reason"] = "NOT_REPRODUCED"
        ok["failure_signature"] = None
        del ok["assurance"]
        validate_report(ok)  # must not raise

    def test_not_reproduced_with_real_failure_signature_also_passes(self):
        """Row 11: a reference WAS established during the search, but the candidate sequence
        did not reproduce it on re-verification -- failure_signature is non-null here,
        distinguishing it from row 5. Schema v2 allows both (see failureSignature's
        description); report-shape correctness lives in eval/report.py's tests."""
        ok = copy.deepcopy(VALID_REPORT)
        ok["outcome"] = "UNRESOLVED"
        ok["unresolved_reason"] = "NOT_REPRODUCED"
        del ok["assurance"]
        validate_report(ok)  # must not raise -- failure_signature stays the real object

    def test_null_failure_signature_requires_a_reason_that_allows_it(self):
        """A reason that always has a reference (e.g. VICTIM_FAILS_ALONE) must still carry a
        real signature."""
        bad = copy.deepcopy(VALID_REPORT)
        bad["outcome"] = "UNRESOLVED"
        bad["unresolved_reason"] = "VICTIM_FAILS_ALONE"
        bad["failure_signature"] = None
        del bad["assurance"]
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)

    def test_infrastructure_failure_allows_either_failure_signature(self):
        """ADR-010 rows 4, 8 and 10 all give INFRASTRUCTURE_FAILURE, but only row 4 (no
        reference established anywhere) has a null signature; rows 8/10 (reference established
        during search or the alone check) carry a real one. The schema allows both."""
        null_signature = copy.deepcopy(VALID_REPORT)
        null_signature["outcome"] = "UNRESOLVED"
        null_signature["unresolved_reason"] = "INFRASTRUCTURE_FAILURE"
        null_signature["failure_signature"] = None
        del null_signature["assurance"]
        validate_report(null_signature)  # must not raise

        real_signature = copy.deepcopy(VALID_REPORT)
        real_signature["outcome"] = "UNRESOLVED"
        real_signature["unresolved_reason"] = "INFRASTRUCTURE_FAILURE"
        del real_signature["assurance"]
        validate_report(real_signature)  # must not raise

    def test_order_exploration_is_optional_but_validated_when_present(self):
        ok = copy.deepcopy(VALID_REPORT)
        ok["order_exploration"] = {
            "order_given": True, "shuffled_orders_tried": 5,
            "orders_exhausted": False, "seed_base": 0, "reproducing_seed": 3,
            "infrastructure_failures": 0,
        }
        validate_report(ok)  # must not raise

        bad = copy.deepcopy(VALID_REPORT)
        bad["order_exploration"] = {"order_given": True}  # missing required sub-fields
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            validate_report(bad)


if __name__ == "__main__":
    unittest.main()
