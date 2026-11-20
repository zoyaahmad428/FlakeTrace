"""Report assembly, schema v2 (ADR-010/ADR-011, W19; Interface 3, docs/contracts/interfaces.md).

Turns Member 2's raw diagnosis tallies (runner.diagnose.DiagnosisRuns.alone_tally/sequence_tally,
ADR-010/W18) and Member 1's pair-mode resource-edge data (evidence.extract.find_edges +
report_fields, Output 2 of docs/contracts/resource-evidence.md) into one schema-v2-validated
diagnosis report. Supersedes the schema-v1 module this project shipped for the Mid (tag
mid-eval-v1): that version is unchanged there, reachable at that tag.

Which shared resource goes in the report is decided once, by Member 1's find_edges/
report_fields -- this module does not re-derive it.

With several polluters (W10, ADR-007), a caller's `resource_fields` can have
`shared_resource=None` (because not every polluter has an edge, so none is shown as the primary
resource) while still naming, in `limitations`, which polluters DID have an edge. Appending this
module's own generic "No polluter-write/victim-read resource edge was found by static analysis"
on top of that would contradict it. `resource_fields` may therefore carry an optional
`any_edge_found: bool` key: when present, it -- not `shared_resource is not None` -- decides
whether the generic line is added.

Four of runner.diagnose's DiagnosisRuns.status values are wired end to end here: POLLUTER_FOUND,
VICTIM_FAILS_ALONE, NOT_REPRODUCED and (new, ADR-010 section 5, FT010) INCONSISTENT (formerly
NO_SINGLE_POLLUTER; that alias was removed in A4, 2026-11-20). Unlike schema v1, INCONSISTENT now gets a real report instead of UnhandledStatus:
it is schema-valid, names no polluter, and exit code 3 ("no report yet") is retired for it.

ADR-010 rows 7/8 (VICTIM_FAILS_ALONE_DIFFERENTLY, and INFRASTRUCTURE_FAILURE from the alone
check) can be reached from a POLLUTER_FOUND diagnosis that DOES name a polluter: Member 2's
run_steps() (W18) deliberately does not stop the search when the victim fails alone with a
different signature or only crashes, so the report can still say what was observed after the
polluter. This module is what hides that polluter from the OUTPUT report in that case ("no test
is blamed", ADR-010 row 7) -- `diagnosis.polluters` itself is left alone.

ADR-011's deletion checks (claim S3, W20) and ADR-014's budget ledger (row 3, W24) have not
landed: every report built here passes deletion_status=None and budget_exhausted=False to
eval.outcome.decide(), which treats both as satisfied/not-exhausted (see that module's
docstring) so this change does not regress any existing VERIFIED verdict (ADR-010 test T6). The
report says so honestly via assurance.sequence.deletion = "NOT_YET_CHECKED" rather than
fabricating DELETION_VERIFIED.
"""

from typing import Optional

from eval.outcome import (
    CANDIDATE_BELOW_REPLAY_THRESHOLD,
    DELETION_INCOMPLETE,
    DELETION_NOT_YET_CHECKED,
    DELETION_VERIFIED,
    OUTCOME_CANDIDATE,
    OUTCOME_UNRESOLVED,
    OUTCOME_VERIFIED,
    REASON_INCONSISTENT_OUTCOMES,
    REASON_INFRASTRUCTURE_FAILURE,
    REASON_NOT_REPRODUCED,
    REASON_SIGNATURE_MISMATCH,
    REASON_VICTIM_FAILS_ALONE_DIFFERENTLY,
    DecisionInput,
    decide,
)
from eval.schema_validator import validate_report
from runner.diagnose import DiagnosisRuns, INCONSISTENT, NOT_REPRODUCED, POLLUTER_FOUND, VICTIM_FAILS_ALONE

SCHEMA_VERSION = 2

_ORDER_EXPLORATION_FIELDS = (
    "order_given", "shuffled_orders", "orders_exhausted", "shuffle_seed_base", "reproducing_seed",
)


class UnhandledStatus(Exception):
    """Raised for a DiagnosisRuns.status this module does not yet turn into a report."""


def _order_exploration(diagnosis: DiagnosisRuns, infrastructure_failures: int) -> Optional[dict]:
    """ADR-008's optional order_exploration report field, built only once Member 2's diagnose()
    actually tracks it (DiagnosisRuns gaining all five order fields below); otherwise None, and
    the key is omitted entirely -- the schema allows that. `infrastructure_failures` is the
    already-combined total (every phase: given/discovered order, shuffles, alone check) -- not
    recomputed here, so the report and the outcome always agree."""
    if not all(hasattr(diagnosis, f) for f in _ORDER_EXPLORATION_FIELDS):
        return None
    return {
        "order_given": diagnosis.order_given,
        "shuffled_orders_tried": diagnosis.shuffled_orders,
        "orders_exhausted": diagnosis.orders_exhausted,
        "seed_base": diagnosis.shuffle_seed_base,
        "reproducing_seed": diagnosis.reproducing_seed,
        "infrastructure_failures": infrastructure_failures,
    }


def assemble_report(
    diagnosis: DiagnosisRuns,
    resource_fields: Optional[dict] = None,
    confidence: float = 0.95,
) -> dict:
    """Build and validate one schema-v2 diagnosis report from a DiagnosisRuns and (for
    POLLUTER_FOUND) `resource_fields` -- the output of evidence.extract.report_fields(pair) (one
    polluter) or a caller's own combination of several such results (W10, several polluters; see
    module docstring for the optional `any_edge_found` key that case can set).
    Raises UnhandledStatus for any status other than POLLUTER_FOUND, VICTIM_FAILS_ALONE,
    NOT_REPRODUCED or INCONSISTENT -- see module docstring."""
    if diagnosis.status not in (POLLUTER_FOUND, VICTIM_FAILS_ALONE, NOT_REPRODUCED, INCONSISTENT):
        raise UnhandledStatus(
            f"assemble_report does not yet handle DiagnosisRuns.status={diagnosis.status!r}; "
            "see eval/report.py's module docstring"
        )
    if diagnosis.alone_tally is None or diagnosis.sequence_tally is None:
        raise ValueError(
            "assemble_report (schema v2) requires DiagnosisRuns.alone_tally/sequence_tally "
            "(ADR-010, W18) -- got None. This DiagnosisRuns predates W18's tallies."
        )
    if diagnosis.status == NOT_REPRODUCED and diagnosis.alone_tally.n == 0:
        # Pre-ADR-008 shape: today's real runner.diagnose() always runs the alone check, so a
        # real NOT_REPRODUCED diagnosis never has an empty alone tally any more. Kept so a
        # DiagnosisRuns built against that older contract fails loudly here (UnhandledStatus)
        # instead of raising a bare ValueError out of DecisionInput that the CLI does not catch.
        # (Read alone_n until A4, 2026-11-20, which removed the old count fields.)
        raise UnhandledStatus(
            "assemble_report cannot build a NOT_REPRODUCED report with no alone runs (pre-ADR-008 "
            "shape). See eval/report.py's module docstring."
        )

    fields = resource_fields if diagnosis.status == POLLUTER_FOUND else None
    edge_found = bool(fields and fields["shared_resource"] is not None)
    any_edge_found = fields.get("any_edge_found", edge_found) if fields else False

    # Combined across every phase (given/discovered order, shuffles, alone check) -- ADR-008's
    # field, unchanged by ADR-010. Not derivable from alone_tally/sequence_tally alone: the
    # shuffle phase is a third phase neither tally covers.
    infrastructure_failures = (
        getattr(diagnosis, "infrastructure_failures", 0)
        + getattr(diagnosis, "shuffle_infrastructure_failures", 0)
        + getattr(diagnosis, "alone_infrastructure_failures", 0)
    )

    ref = diagnosis.reference_signature
    if diagnosis.status in (POLLUTER_FOUND, VICTIM_FAILS_ALONE, INCONSISTENT):
        assert ref is not None, "POLLUTER_FOUND/VICTIM_FAILS_ALONE/INCONSISTENT always carry a reference signature"
    failure_signature = None if ref is None else {
        "exception_type": ref.exception_type,
        "message": ref.message,
        "stack_trace": ref.stack_trace,
    }

    # Claim S3 before W20's deletion runs exist (decided 2026-11-19 by M2 with M3's permission,
    # applying ADR-011 sections 2 and 4): with ONE polluter, "the sequence without it" is the victim
    # alone, so the alone check is the deletion check -- verified when the victim passed alone in
    # every run. With two or more, no deletion run has been made: INCOMPLETE, so CANDIDATE.
    # (A1 fail-safe fix, same day, independently: eval/outcome.py's row 12 no longer lets a raw
    # None escape this guard either way -- defense in depth, since this function now never
    # actually passes None through for a found-polluter case.)
    deletion_status = None
    if diagnosis.status == POLLUTER_FOUND and diagnosis.polluters:
        alone_all_passed = diagnosis.alone_tally.passed == diagnosis.alone_tally.n
        deletion_status = (DELETION_VERIFIED if len(diagnosis.polluters) == 1 and alone_all_passed
                           else DELETION_INCOMPLETE)

    decision_input = DecisionInput(
        source_integrity_passed=diagnosis.source_integrity.passed,
        reference_established=(ref is not None),
        infrastructure_failures_anywhere=infrastructure_failures,
        alone=diagnosis.alone_tally,
        sequence=diagnosis.sequence_tally,
        resource_edge_exists=edge_found,
        confidence=confidence,
        search_inconsistent=(diagnosis.status == INCONSISTENT),
        deletion_status=deletion_status,
    )
    decision = decide(decision_input)
    reason = decision.unresolved_reason
    alone = diagnosis.alone_tally
    sequence = diagnosis.sequence_tally
    reference_established = ref is not None

    # UNRESOLVED means no verdict could be made -- nothing is blamed in the OUTPUT report, even
    # if the search (which does not stop early for ADR-010 rows 7-11, W18) named a polluter and
    # a candidate sequence. diagnosis.polluters/sequence are left alone; only what is reported
    # changes (ADR-010 rows 6-8 say this explicitly -- "no test is blamed" -- and the same
    # reasoning applies to rows 9-11, where the candidate sequence did not hold up either).
    no_blame = decision.outcome == OUTCOME_UNRESOLVED and reason != "SOURCE_INTEGRITY_FAILED"
    reported_polluters = [] if no_blame else diagnosis.polluters
    # Only collapse reduced_sequence to [victim] when there was an actual found polluter to
    # un-blame (diagnosis.polluters non-empty). For INCONSISTENT/NOT_REPRODUCED, no polluter was
    # ever found and diagnosis.sequence is already just the starting order (ADR-010 section 5) --
    # showing it as-is is correct, not something to hide.
    reported_sequence = (
        [diagnosis.victim] if (no_blame and diagnosis.polluters) else diagnosis.sequence
    )

    limitations = [
        "instrumentation_level is static-only; runtime instrumentation is not built.",
    ]
    if diagnosis.status == POLLUTER_FOUND:
        if fields:
            limitations += fields["limitations"]
        if not any_edge_found:
            limitations.append("No polluter-write/victim-read resource edge was found by static analysis.")
        if decision.outcome in (OUTCOME_CANDIDATE, OUTCOME_VERIFIED):
            if deletion_status == DELETION_VERIFIED:
                limitations.append(
                    f"Deletion check from the alone runs (ADR-011 section 2): without its one polluter the "
                    f"victim passed {diagnosis.alone_tally.passed} of {diagnosis.alone_tally.n} runs alone."
                )
            else:
                limitations.append(
                    "Reduced by single-trial delta debugging; not deletion-verified (ADR-011; the "
                    "repeated deletion runs for two or more polluters are W20, not yet landed)."
                )

    order_desc = "given" if getattr(diagnosis, "order_given", True) else "discovered"
    shuffled_orders = getattr(diagnosis, "shuffled_orders", 0)
    shuffle_note = f" (plus {shuffled_orders} shuffled order(s))" if shuffled_orders else ""

    if reason == REASON_VICTIM_FAILS_ALONE_DIFFERENTLY:  # row 7
        limitations.append(
            f"Victim failed {alone.other}/{alone.n} time(s) alone with a different failure than "
            f"the {sequence.matched}/{sequence.n} reference failures seen after the search's "
            "candidate sequence -- recorded, but no test is blamed (ADR-010 row 7)."
        )
    elif reason == REASON_INFRASTRUCTURE_FAILURE and reference_established and alone.passed < alone.n:  # row 8
        limitations.append(
            f"Victim run alone crashed or timed out {alone.infra}/{alone.n} time(s), never a "
            "real exception -- a tooling problem, so no test is blamed (ADR-010 row 8)."
        )
    elif reason == REASON_INCONSISTENT_OUTCOMES:  # row 2
        limitations.append(
            f"The failure appeared once in the {order_desc} order{shuffle_note} and could not "
            f"be obtained again in {sequence.n} further run(s); likely not order-dependent. "
            "Re-run with a larger --n, or supply the exact failing order with --order."
        )
    elif reason == REASON_NOT_REPRODUCED and reference_established:  # row 11
        limitations.append(
            f"A reference failure was observed during the search, but the candidate sequence "
            f"did not reproduce it on re-verification ({sequence.n} runs, all passed) -- no "
            "test is blamed (ADR-010 row 11)."
        )
    elif reason == REASON_INFRASTRUCTURE_FAILURE and reference_established:  # row 10
        limitations.append(
            f"A reference failure was observed during the search, but the candidate sequence "
            f"only crashed or timed out on re-verification ({sequence.infra}/{sequence.n}), "
            "never reproducing it for real -- no test is blamed (ADR-010 row 10)."
        )
    elif reason == REASON_SIGNATURE_MISMATCH:  # row 9
        limitations.append(
            f"The candidate sequence failed {sequence.other + sequence.infra}/{sequence.n} "
            "time(s) on re-verification, but never with the reference failure signature -- not "
            "confirmed as this bug, so no test is blamed (ADR-010 row 9)."
        )
    elif reason == REASON_NOT_REPRODUCED:  # row 5: no reference anywhere
        limitations.append(
            f"Not reproduced: {sequence.n} runs of the {order_desc} order{shuffle_note}, "
            f"{alone.n} runs alone. In the {order_desc} order the failure rate is below "
            f"{decision.sequence_interval[1]:.3f} with {confidence:.0%} confidence (Wilson). "
            "This is not evidence that the test is reliable: flaky tests have been found only "
            "after thousands of reruns."
        )
    elif reason == REASON_INFRASTRUCTURE_FAILURE:  # row 4: no reference anywhere
        limitations.append(
            f"The {order_desc} order never failed for real in {sequence.n} runs{shuffle_note}, "
            f"but {infrastructure_failures} run(s) somewhere (the order, a shuffle, or the alone "
            "check) only crashed or timed out, never a real exception -- a tooling problem, not "
            "evidence this victim is reliable."
        )

    # Resource evidence names the polluter (polluter_write_location is its class/method) -- when
    # no_blame withholds the polluter, it withholds the resource evidence pointing at it too.
    edge = None
    if not no_blame and fields and fields["shared_resource"] is not None:
        edge = {
            "shared_resource": fields["shared_resource"],
            "polluter_write_location": fields["polluter_write_location"],
            "victim_read_location": fields["victim_read_location"],
        }
    # W21 (Member 1, PR #105): report_fields lists every edge with its depth; show all of them
    # (ADR-010 section 6). A caller without that list falls back to the primary edge.
    if no_blame or not fields:
        edges = []
    else:
        edges = fields.get("resource_edges", [edge] if edge else [])

    report = {
        "schema_version": SCHEMA_VERSION,
        "victim": diagnosis.victim.to_dict(),
        "polluters": [p.to_dict() for p in reported_polluters],
        "original_failing_order": [t.to_dict() for t in diagnosis.original_order],
        "reduced_sequence": [t.to_dict() for t in reported_sequence],
        "reproduction": {
            "n": diagnosis.sequence_tally.n, "passed": diagnosis.sequence_tally.passed,
            "matched": diagnosis.sequence_tally.matched, "other": diagnosis.sequence_tally.other,
            "infra": diagnosis.sequence_tally.infra, "confidence": confidence,
            "lower": decision.sequence_interval[0], "upper": decision.sequence_interval[1],
        },
        "victim_alone": {
            "n": alone.n, "passed": alone.passed, "matched": alone.matched, "other": alone.other,
            "infra": alone.infra, "confidence": confidence,
            "lower": decision.alone_interval[0], "upper": decision.alone_interval[1],
        },
        "shared_resource": edge["shared_resource"] if edge else None,
        "polluter_write_location": edge["polluter_write_location"] if edge else None,
        "victim_read_location": edge["victim_read_location"] if edge else None,
        "resource_edges": edges,
        "failure_signature": failure_signature,
        "instrumentation_level": "static-only",
        "execution_record_reference": diagnosis.execution_record,
        "source_integrity": {
            "passed": diagnosis.source_integrity.passed,
            "details": diagnosis.source_integrity.details,
        },
        "outcome": decision.outcome,
        "unresolved_reason": decision.unresolved_reason,
        "candidate_reasons": list(decision.candidate_reasons),
        "limitations": limitations,
    }
    if decision.outcome in (OUTCOME_CANDIDATE, OUTCOME_VERIFIED):
        report["assurance"] = {
            "sequence": {
                "reproduces": (
                    "NOT_ESTABLISHED" if CANDIDATE_BELOW_REPLAY_THRESHOLD in decision.candidate_reasons
                    else "ESTABLISHED"
                ),
                "passes_alone": "ESTABLISHED",
                "deletion": deletion_status or DELETION_NOT_YET_CHECKED,
            },
            "resource": {
                "level": "STATIC_OVERLAP" if edge_found else "NONE",
                "mechanism": "NOT_ASSESSED",
            },
        }
    order_exploration = _order_exploration(diagnosis, infrastructure_failures)
    if order_exploration is not None:
        report["order_exploration"] = order_exploration
    validate_report(report)
    return report
