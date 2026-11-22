"""Outcome/decision logic for FlakeTrace diagnosis reports (ADR-010, verdict contract v2).

Decision table (docs/03-Design/decisions/ADR-010-verdict-contract-v2.md section 3, agreed by
all three members 2026-11-13, PR #101; evaluated top to bottom, first match wins):

  1. source_integrity_passed is False                          -> UNRESOLVED(SOURCE_INTEGRITY_FAILED)
  2. search_inconsistent (seen once, not again)                -> UNRESOLVED(INCONSISTENT_OUTCOMES)
  3. budget_exhausted (search ended before a sequence was found) -> UNRESOLVED(BUDGET_EXHAUSTED)
  4. no real failure anywhere, and an infra failure somewhere  -> UNRESOLVED(INFRASTRUCTURE_FAILURE)
  5. no real failure anywhere                                  -> UNRESOLVED(NOT_REPRODUCED)
  6. alone.matched >= 1                                        -> UNRESOLVED(VICTIM_FAILS_ALONE)
  7. alone.other >= 1                                          -> UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)
  8. alone.infra >= 1                                          -> UNRESOLVED(INFRASTRUCTURE_FAILURE)
  9. sequence.matched == 0 and sequence.other >= 1             -> UNRESOLVED(SIGNATURE_MISMATCH)
  10. sequence.matched == 0 and sequence.infra >= 1            -> UNRESOLVED(INFRASTRUCTURE_FAILURE)
  11. sequence.matched == 0                                    -> UNRESOLVED(NOT_REPRODUCED)
  12. any of S1, S3, R1 not established, or verification_budget_exhausted -> CANDIDATE, candidate_reasons lists each
  13. otherwise                                                -> VERIFIED

"no real failure anywhere" (rows 4-5) means no reference failure signature was EVER established,
anywhere in the diagnosis -- not just in the `alone`/`sequence` tallies below. Those two tallies
are the FINAL alone check and the FINAL sequence re-verify; a reference can be established
earlier, during the search/reproduce phase, and then not reproduce again on re-verification
(exactly ADR-011's motivating bug: single-trial ddmin can shrink to a sequence that does not
actually hold up). That later case is row 11 (NOT_REPRODUCED) or row 10 (INFRASTRUCTURE_FAILURE),
not row 4/5 -- which is why rows 4/5 take `reference_established` as its own input rather than
being derived from `alone`/`sequence`, and why rows 6-11 are checked only once a reference is
known to exist (asking "did alone match the reference" makes no sense otherwise).

What VERIFIED asserts -- exactly four claims (ADR-010 section 2), and nothing else; it does NOT
assert the resource is the cause of the failure:

  S1 reproduces          sequence tally   Wilson 95% lower bound of matched/n >= lower_bound_threshold
  S2 passes alone        alone tally      alone.passed == alone.n (rows 6-8 are what withholds this)
  S3 every kept test is needed   deletion checks (ADR-011, W20)
  R1 a static overlap exists     Member 1's edges (ADR-007, unchanged)

Budget (row 3, and the CANDIDATE_BUDGET_EXHAUSTED reason in row 12) is ADR-014/W24 (Interface 6):
`budget_exhausted` is for a search that never found a polluter at all (runner.diagnose's status
BUDGET_EXHAUSTED); `verification_budget_exhausted` is for a polluter that WAS found but whose
verification (deletion checks, final sequence check) the budget ran out before finishing. Both
default False, so a caller that predates the budget ledger never regresses. S3 is different (A1
fail-safe fix, 2026-11-19): `deletion_status=None` ("not yet
checked") does NOT satisfy S3 -- an unestablished claim is not an established one. The one case
where S3 is actually free (ADR-011 section 2): a single kept polluter's deletion check IS the
alone check, already run by the time row 12 is reached (rows 6-8 already gated alone clean) --
eval/report.py computes DELETION_VERIFIED for that case and passes it in explicitly. Multiple
kept polluters have no such free check yet (W20 builds the real one), so decide() correctly
gives CANDIDATE for them until then -- see fixture F3 (two required polluters).
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from eval.baseline import RunTally
from eval.stats import wilson_interval

OUTCOME_VERIFIED = "VERIFIED"
OUTCOME_CANDIDATE = "CANDIDATE"
OUTCOME_UNRESOLVED = "UNRESOLVED"
VALID_OUTCOMES = (OUTCOME_VERIFIED, OUTCOME_CANDIDATE, OUTCOME_UNRESOLVED)

REASON_SOURCE_INTEGRITY_FAILED = "SOURCE_INTEGRITY_FAILED"
REASON_INCONSISTENT_OUTCOMES = "INCONSISTENT_OUTCOMES"  # new, ADR-010 row 2, FT010
REASON_BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"  # new, ADR-010 row 3 / ADR-014
REASON_INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
REASON_NOT_REPRODUCED = "NOT_REPRODUCED"
REASON_VICTIM_FAILS_ALONE = "VICTIM_FAILS_ALONE"
REASON_VICTIM_FAILS_ALONE_DIFFERENTLY = "VICTIM_FAILS_ALONE_DIFFERENTLY"  # new, ADR-010 row 7, FT003
REASON_SIGNATURE_MISMATCH = "SIGNATURE_MISMATCH"
VALID_UNRESOLVED_REASONS = (
    REASON_SOURCE_INTEGRITY_FAILED,
    REASON_INCONSISTENT_OUTCOMES,
    REASON_BUDGET_EXHAUSTED,
    REASON_INFRASTRUCTURE_FAILURE,
    REASON_NOT_REPRODUCED,
    REASON_VICTIM_FAILS_ALONE,
    REASON_VICTIM_FAILS_ALONE_DIFFERENTLY,
    REASON_SIGNATURE_MISMATCH,
)
# Retired as UNRESOLVED reasons by ADR-010 section 4 (Q1, option A, agreed 2026-11-13):
# NO_SUPPORTED_RESOURCE_EVIDENCE and BELOW_CONFIDENCE_THRESHOLD are no longer abstention
# reasons -- a sequence that reproduces reliably and passes alone is CANDIDATE now, with the
# same names reused as candidate_reasons below.

# ADR-010 section 3's candidate_reasons values (row 12) -- every unmet claim, not just one.
CANDIDATE_BELOW_REPLAY_THRESHOLD = "BELOW_REPLAY_THRESHOLD"
CANDIDATE_DELETION_EVIDENCE_INCOMPLETE = "DELETION_EVIDENCE_INCOMPLETE"
CANDIDATE_DELETION_EVIDENCE_INCONCLUSIVE = "DELETION_EVIDENCE_INCONCLUSIVE"
CANDIDATE_NO_SUPPORTED_RESOURCE_EVIDENCE = "NO_SUPPORTED_RESOURCE_EVIDENCE"
CANDIDATE_BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"  # W24 (Interface 6): see
# DecisionInput.verification_budget_exhausted below -- a polluter WAS found, but the budget ran
# out during verification (deletion checks or the final sequence check), so the result can never
# be VERIFIED. Distinct from the row-3 budget_exhausted field, which is for a search that never
# found a polluter at all and short-circuits to UNRESOLVED before this row is reached.
VALID_CANDIDATE_REASONS = (
    CANDIDATE_BELOW_REPLAY_THRESHOLD,
    CANDIDATE_DELETION_EVIDENCE_INCOMPLETE,
    CANDIDATE_DELETION_EVIDENCE_INCONCLUSIVE,
    CANDIDATE_NO_SUPPORTED_RESOURCE_EVIDENCE,
    CANDIDATE_BUDGET_EXHAUSTED,
)

DEFAULT_CONFIDENCE = 0.95
DEFAULT_LOWER_BOUND_THRESHOLD = 0.70

# ADR-011 section 4's four deletion-evidence values for claim S3 (W20, not yet landed -- no
# caller can produce these yet). NOT_YET_CHECKED is this module's OWN addition, not in ADR-011's
# table: it is what DecisionInput.deletion_status=None means, and is flagged here for the other
# two members to confirm or replace in review, per docs/evidence-m3.md. It exists so a schema v2
# report can say honestly "this was not checked" rather than silently reusing NOT_APPLICABLE
# (which ADR-011 defines to mean "no polluter was found" -- a different, false claim for a
# diagnosis that DID find a polluter but whose deletion check hasn't been built yet).
DELETION_VERIFIED = "DELETION_VERIFIED"
DELETION_INCONCLUSIVE = "INCONCLUSIVE"
DELETION_INCOMPLETE = "INCOMPLETE"
DELETION_NOT_APPLICABLE = "NOT_APPLICABLE"
DELETION_NOT_YET_CHECKED = "NOT_YET_CHECKED"  # this module's addition -- see note above
VALID_DELETION_STATUSES = (
    DELETION_VERIFIED, DELETION_INCONCLUSIVE, DELETION_INCOMPLETE, DELETION_NOT_APPLICABLE,
)
# Values of deletion_status that satisfy claim S3 (do not block VERIFIED at row 12). None and
# NOT_YET_CHECKED are deliberately NOT here (A1 fail-safe fix, 2026-11-19): "not yet checked"
# is not a satisfied claim.
_DELETION_SATISFIES_S3 = (DELETION_VERIFIED, DELETION_NOT_APPLICABLE)


@dataclass(frozen=True)
class DecisionInput:
    source_integrity_passed: bool
    reference_established: bool
    """Whether ANY real (non-infrastructure) failure was ever observed, anywhere in the
    diagnosis -- the search/reproduce phase included, not just the alone/sequence tallies below.
    False is exactly runner.diagnose's NOT_REPRODUCED status (reference_signature is None)."""
    infrastructure_failures_anywhere: int
    """Combined infrastructure-failure count across every phase (search, shuffles, alone) --
    rows 4/5 only, used only when reference_established is False. Not derived from alone/
    sequence below: those are later-phase tallies that do not cover the search/shuffle phases."""
    alone: RunTally
    sequence: RunTally
    resource_edge_exists: bool
    confidence: float = DEFAULT_CONFIDENCE
    lower_bound_threshold: float = DEFAULT_LOWER_BOUND_THRESHOLD
    search_inconsistent: bool = False
    """ADR-010 row 2 (runner status INCONSISTENT, called NO_SINGLE_POLLUTER before W18): the failure was
    seen once in the starting order and could not be obtained again -- not alone, not after any
    single earlier test, not in the full order once more. Defaults False: no pre-ADR-010 caller
    reports it."""
    budget_exhausted: bool = False
    """ADR-010 row 3 / ADR-014 (W24): the execution budget ran out before a polluter set was
    found at all -- runner.diagnose's status BUDGET_EXHAUSTED. Defaults False, so a caller that
    predates the budget ledger (every existing report before W24) never regresses."""
    verification_budget_exhausted: bool = False
    """ADR-014 section 2 / Interface 6 (W24): a polluter WAS found (status POLLUTER_FOUND), but
    the budget ran out before verification could finish -- BudgetAccount.exhausted is True on a
    POLLUTER_FOUND diagnosis (a deletion check NOT_RUN for lack of budget, or the final sequence
    check running fewer than n times). Checked only in the S1/S3/R1 block below, never as an
    early return like budget_exhausted above: this is about an incomplete verification of a
    result that WAS found, not a search that found nothing. Defaults False, same reasoning as
    budget_exhausted."""
    deletion_status: Optional[str] = None
    """ADR-011 claim S3 (W20, not yet fully built): the rolled-up NEEDED/NOT_NEEDED/INCONCLUSIVE
    outcome of repeated-removal checks on every kept test. One of VALID_DELETION_STATUSES, or
    None for "not yet checked" (equivalent to DELETION_NOT_YET_CHECKED above). A1 fail-safe fix
    (2026-11-19): None does NOT satisfy S3 -- an unestablished claim is not an established one.
    A single kept polluter's check is free (ADR-011 section 2, the alone check already proves
    it); eval/report.py computes that and passes a real DELETION_VERIFIED, not None. Multiple
    kept polluters (e.g. fixture F3) have no free check yet, so they correctly read CANDIDATE
    until W20 builds the real multi-test check."""

    def __post_init__(self):
        if self.alone.n <= 0:
            raise ValueError(f"alone.n must be > 0, got {self.alone.n!r}")
        if self.sequence.n <= 0:
            raise ValueError(f"sequence.n must be > 0, got {self.sequence.n!r}")
        if not (0.0 < self.confidence < 1.0):
            raise ValueError(f"confidence must be in (0, 1), got {self.confidence!r}")
        if not (0.0 <= self.lower_bound_threshold <= 1.0):
            raise ValueError(f"lower_bound_threshold must be in [0, 1], got {self.lower_bound_threshold!r}")
        if self.infrastructure_failures_anywhere < 0:
            raise ValueError(
                f"infrastructure_failures_anywhere must be >= 0, got {self.infrastructure_failures_anywhere!r}"
            )
        if self.deletion_status is not None and self.deletion_status not in VALID_DELETION_STATUSES:
            raise ValueError(
                f"deletion_status must be None or one of {VALID_DELETION_STATUSES}, "
                f"got {self.deletion_status!r}"
            )


@dataclass(frozen=True)
class Decision:
    outcome: str
    unresolved_reason: Optional[str]
    candidate_reasons: Tuple[str, ...]  # always (), except for OUTCOME_CANDIDATE
    sequence_interval: Tuple[float, float]
    alone_interval: Tuple[float, float]
    rationale: str


def decide(d: DecisionInput) -> Decision:
    """Apply the ADR-010 decision table to a DecisionInput. See module docstring for the full
    table; this function implements it top to bottom, first match wins."""

    sequence_interval = wilson_interval(d.sequence.matched, d.sequence.n, d.confidence)
    alone_interval = wilson_interval(d.alone.matched, d.alone.n, d.confidence)

    def result(outcome, reason, rationale, candidate_reasons=()):
        return Decision(
            outcome=outcome,
            unresolved_reason=reason,
            candidate_reasons=tuple(candidate_reasons),
            sequence_interval=sequence_interval,
            alone_interval=alone_interval,
            rationale=rationale,
        )

    if not d.source_integrity_passed:
        return result(
            OUTCOME_UNRESOLVED, REASON_SOURCE_INTEGRITY_FAILED,
            "Source-integrity check failed, so no other evidence can be trusted.",
        )

    if d.search_inconsistent:
        return result(
            OUTCOME_UNRESOLVED, REASON_INCONSISTENT_OUTCOMES,
            "The failure appeared once in the starting order and could not be obtained again; "
            "likely not order-dependent. Re-run with a larger --n, or supply the exact failing "
            "order with --order.",
        )

    if d.budget_exhausted:
        return result(
            OUTCOME_UNRESOLVED, REASON_BUDGET_EXHAUSTED,
            "The execution budget ran out before a reproducing sequence was found.",
        )

    if not d.reference_established:
        # W35 (ADR-016, M2's review): reference_established=False does not mean no real failure
        # ever occurred -- pair mode's tally can have sequence.other > 0 (a pair failed once,
        # then passed its re-run, so it was never adopted). "Never reproduced ANY failure" would
        # be false in that case; say "no CONFIRMED failure" and name the unconfirmed count.
        unconfirmed = d.sequence.other + d.alone.other
        unconfirmed_note = f" ({unconfirmed} failed once but not again)" if unconfirmed else ""
        if d.infrastructure_failures_anywhere > 0:
            return result(
                OUTCOME_UNRESOLVED, REASON_INFRASTRUCTURE_FAILURE,
                f"No confirmed failure anywhere ({d.sequence.n} sequence run(s), {d.alone.n} "
                f"alone run(s){unconfirmed_note}), but {d.infrastructure_failures_anywhere} "
                "run(s) only crashed or timed out -- a tooling problem, not evidence this "
                "victim is reliable.",
            )
        return result(
            OUTCOME_UNRESOLVED, REASON_NOT_REPRODUCED,
            f"No run reproduced a confirmed failure in {d.sequence.n} sequence run(s) and "
            f"{d.alone.n} alone run(s){unconfirmed_note}.",
        )

    if d.alone.matched >= 1:
        return result(
            OUTCOME_UNRESOLVED, REASON_VICTIM_FAILS_ALONE,
            f"Victim reproduced its reference failure signature {d.alone.matched}/{d.alone.n} "
            "times when run alone; cannot attribute any polluted-order failure to a polluter.",
        )

    if d.alone.other >= 1:
        return result(
            OUTCOME_UNRESOLVED, REASON_VICTIM_FAILS_ALONE_DIFFERENTLY,
            f"Victim failed {d.alone.other}/{d.alone.n} times when run alone, with a different "
            "failure than the reference signature; cannot attribute any polluted-order failure "
            "to a polluter, even though one reproduces it.",
        )

    if d.alone.infra >= 1:
        return result(
            OUTCOME_UNRESOLVED, REASON_INFRASTRUCTURE_FAILURE,
            f"Victim run alone crashed or timed out {d.alone.infra}/{d.alone.n} times, never a "
            "real exception -- a tooling problem, not evidence the victim passes alone.",
        )

    # From here alone.passed == alone.n: the victim passed alone every time (claim S2 holds).
    if d.sequence.matched == 0:
        if d.sequence.other >= 1:
            return result(
                OUTCOME_UNRESOLVED, REASON_SIGNATURE_MISMATCH,
                f"Sequence failed {d.sequence.other + d.sequence.infra}/{d.sequence.n} times "
                "but never with the reference failure signature.",
            )
        if d.sequence.infra >= 1:
            return result(
                OUTCOME_UNRESOLVED, REASON_INFRASTRUCTURE_FAILURE,
                f"Sequence crashed or timed out {d.sequence.infra}/{d.sequence.n} times, never "
                "a real exception -- a tooling problem, not evidence of a different bug.",
            )
        return result(
            OUTCOME_UNRESOLVED, REASON_NOT_REPRODUCED,
            f"A reference failure was observed during the search, but the candidate sequence "
            f"did not reproduce it on re-verification ({d.sequence.n} runs, all passed).",
        )

    # sequence.matched >= 1 and alone.passed == alone.n from here: S2 holds, check S1/S3/R1.
    reasons = []
    if sequence_interval[0] < d.lower_bound_threshold:
        reasons.append(CANDIDATE_BELOW_REPLAY_THRESHOLD)
    if d.deletion_status not in _DELETION_SATISFIES_S3:
        reasons.append(
            CANDIDATE_DELETION_EVIDENCE_INCONCLUSIVE if d.deletion_status == DELETION_INCONCLUSIVE
            else CANDIDATE_DELETION_EVIDENCE_INCOMPLETE
        )
    if not d.resource_edge_exists:
        reasons.append(CANDIDATE_NO_SUPPORTED_RESOURCE_EVIDENCE)
    if d.verification_budget_exhausted:
        reasons.append(CANDIDATE_BUDGET_EXHAUSTED)

    if reasons:
        return result(
            OUTCOME_CANDIDATE, None,
            f"Sequence reproduced {d.sequence.matched}/{d.sequence.n} "
            f"(Wilson lower bound {sequence_interval[0]:.3f}), victim never failed alone, but: "
            f"{', '.join(reasons)}.",
            candidate_reasons=reasons,
        )

    return result(
        OUTCOME_VERIFIED, None,
        f"Sequence reproduced {d.sequence.matched}/{d.sequence.n} "
        f"(Wilson lower bound {sequence_interval[0]:.3f} >= {d.lower_bound_threshold}), victim "
        "never failed alone, every kept test is needed, and a static overlap supports it. This "
        "does not assert the resource is the cause of the failure.",
    )
