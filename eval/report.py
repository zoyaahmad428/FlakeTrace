"""W9 report assembly (Interface 3, docs/contracts/interfaces.md).

Turns Member 2's raw diagnosis counts (runner.diagnose.DiagnosisRuns) and Member 1's
pair-mode resource-edge data (evidence.extract.find_edges + report_fields, Output 2 of
docs/contracts/resource-evidence.md) into one schema-validated diagnosis report.

Which shared resource goes in the report is decided once, by Member 1's find_edges/
report_fields -- this module does not re-derive it. An earlier version of this file had its
own correlation function (find_resource_edge); it duplicated that logic, dropped M1's
FIXED_LIMITATIONS, and callers were passing --depth 1, which cannot find a resource accessed
through a one-level helper call (e.g. F2's FeatureVictimTest reads the property inside
FeatureFlags.isTurboEnabled(), not in the test method itself) -- flagged by Member 2, see
docs/evidence-m3.md.

Only two of runner.diagnose's four DiagnosisRuns.status values are wired end to end here:
POLLUTER_FOUND and VICTIM_FAILS_ALONE. NOT_REPRODUCED and NO_SINGLE_POLLUTER are deliberately
NOT handled -- see UnhandledStatus and docs/evidence-m3.md for why: runner.diagnose short-
circuits before running the isolation check when the sequence never reproduces at all, so
NOT_REPRODUCED carries no isolation data to satisfy eval.outcome.DecisionInput's
`isolation_n > 0` requirement; and NO_SINGLE_POLLUTER (M2's one-by-one search finding no
single attributable test, e.g. F3) has no corresponding value in the schema's
unresolved_reason enum yet. Both are open questions for the team, not silently invented
answers.
"""

from typing import Optional

from eval.outcome import DecisionInput, decide
from eval.schema_validator import validate_report
from runner.diagnose import DiagnosisRuns, POLLUTER_FOUND, VICTIM_FAILS_ALONE


class UnhandledStatus(Exception):
    """Raised for a DiagnosisRuns.status this module does not yet turn into a report."""


def assemble_report(
    diagnosis: DiagnosisRuns,
    resource_fields: Optional[dict] = None,
    confidence: float = 0.95,
) -> dict:
    """Build and validate one diagnosis report from a DiagnosisRuns and (for POLLUTER_FOUND)
    `resource_fields` -- the output of evidence.extract.report_fields(pair), itself built
    from evidence.extract.find_edges(polluter_id, polluter_access, victim_id, victim_access).
    Raises UnhandledStatus for any status other than POLLUTER_FOUND or VICTIM_FAILS_ALONE --
    see module docstring."""
    if diagnosis.status not in (POLLUTER_FOUND, VICTIM_FAILS_ALONE):
        raise UnhandledStatus(
            f"assemble_report does not yet handle DiagnosisRuns.status={diagnosis.status!r}; "
            "see eval/report.py's module docstring"
        )
    fields = resource_fields if diagnosis.status == POLLUTER_FOUND else None
    edge_found = bool(fields and fields["shared_resource"] is not None)

    decision_input = DecisionInput(
        source_integrity_passed=diagnosis.source_integrity.passed,
        isolation_successes=diagnosis.alone_successes,
        isolation_n=diagnosis.alone_n,
        sequence_successes=diagnosis.sequence_successes,
        sequence_n=diagnosis.sequence_n,
        sequence_failures_any=diagnosis.sequence_any_failures,
        resource_edge_exists=edge_found,
        confidence=confidence,
    )
    decision = decide(decision_input)

    ref = diagnosis.reference_signature
    assert ref is not None, "POLLUTER_FOUND/VICTIM_FAILS_ALONE always carry a reference signature"

    limitations = [
        "instrumentation_level is static-only (Iteration 1); runtime instrumentation is Iteration 2.",
    ]
    if diagnosis.status == POLLUTER_FOUND:
        if fields:
            limitations += fields["limitations"]
        if not edge_found:
            limitations.append("No polluter-write/victim-read resource edge was found by static analysis.")

    report = {
        "victim": diagnosis.victim.to_dict(),
        "polluters": [p.to_dict() for p in diagnosis.polluters],
        "original_failing_order": [t.to_dict() for t in diagnosis.original_order],
        "reduced_sequence": [t.to_dict() for t in diagnosis.sequence],
        "reproduction": {
            "successes": diagnosis.sequence_successes, "n": diagnosis.sequence_n,
            "confidence": confidence,
            "lower": decision.sequence_interval[0], "upper": decision.sequence_interval[1],
        },
        "sequence_any_signature_failures": diagnosis.sequence_any_failures,
        "victim_alone": {
            "successes": diagnosis.alone_successes, "n": diagnosis.alone_n,
            "confidence": confidence,
            "lower": decision.isolation_interval[0], "upper": decision.isolation_interval[1],
        },
        "shared_resource": fields["shared_resource"] if fields else None,
        "polluter_write_location": fields["polluter_write_location"] if fields else None,
        "victim_read_location": fields["victim_read_location"] if fields else None,
        "failure_signature": {
            "exception_type": ref.exception_type,
            "message": ref.message,
            "stack_trace": ref.stack_trace,
        },
        "instrumentation_level": "static-only",
        "execution_record_reference": diagnosis.execution_record,
        "source_integrity": {
            "passed": diagnosis.source_integrity.passed,
            "details": diagnosis.source_integrity.details,
        },
        "outcome": decision.outcome,
        "unresolved_reason": decision.unresolved_reason,
        "limitations": limitations,
    }
    validate_report(report)
    return report
