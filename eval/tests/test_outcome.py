import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.baseline import RunTally
from eval.outcome import (
    CANDIDATE_BELOW_REPLAY_THRESHOLD,
    CANDIDATE_DELETION_EVIDENCE_INCOMPLETE,
    CANDIDATE_DELETION_EVIDENCE_INCONCLUSIVE,
    CANDIDATE_NO_SUPPORTED_RESOURCE_EVIDENCE,
    DELETION_INCOMPLETE,
    DELETION_INCONCLUSIVE,
    DELETION_NOT_APPLICABLE,
    DELETION_VERIFIED,
    DecisionInput,
    OUTCOME_CANDIDATE,
    OUTCOME_UNRESOLVED,
    OUTCOME_VERIFIED,
    REASON_BUDGET_EXHAUSTED,
    REASON_INCONSISTENT_OUTCOMES,
    REASON_INFRASTRUCTURE_FAILURE,
    REASON_NOT_REPRODUCED,
    REASON_SIGNATURE_MISMATCH,
    REASON_SOURCE_INTEGRITY_FAILED,
    REASON_VICTIM_FAILS_ALONE,
    REASON_VICTIM_FAILS_ALONE_DIFFERENTLY,
    decide,
)


def alone(n=20, passed=20, matched=0, other=0, infra=0):
    return RunTally(n=n, passed=passed, matched=matched, other=other, infra=infra)


def sequence(n=20, passed=0, matched=20, other=0, infra=0):
    return RunTally(n=n, passed=passed, matched=matched, other=other, infra=infra)


def base_kwargs(**overrides):
    """A VERIFIED-shaped baseline; each test overrides just what it needs to hit its own row."""
    kwargs = dict(
        source_integrity_passed=True,
        reference_established=True,
        infrastructure_failures_anywhere=0,
        alone=alone(),
        sequence=sequence(),
        resource_edge_exists=True,
    )
    kwargs.update(overrides)
    return kwargs


class TestDecisionTableRows(unittest.TestCase):
    """One test per row of the ADR-010 decision table in eval/outcome.py."""

    def test_row1_source_integrity_failed_overrides_everything(self):
        d = DecisionInput(**base_kwargs(source_integrity_passed=False))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_SOURCE_INTEGRITY_FAILED)

    def test_row2_search_inconsistent(self):
        d = DecisionInput(**base_kwargs(search_inconsistent=True))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_INCONSISTENT_OUTCOMES)

    def test_row3_budget_exhausted(self):
        d = DecisionInput(**base_kwargs(budget_exhausted=True))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_BUDGET_EXHAUSTED)

    def test_row4_no_reference_established_with_infra(self):
        """No reference anywhere (e.g. runner status NOT_REPRODUCED), but some run(s) --
        possibly in the search/shuffle phase, not reflected in alone/sequence at all --
        crashed or timed out."""
        d = DecisionInput(**base_kwargs(
            reference_established=False, infrastructure_failures_anywhere=5,
            alone=alone(passed=18, infra=2), sequence=sequence(passed=15, matched=0, infra=5),
        ))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_INFRASTRUCTURE_FAILURE)

    def test_row5_no_reference_established(self):
        d = DecisionInput(**base_kwargs(
            reference_established=False, infrastructure_failures_anywhere=0,
            alone=alone(), sequence=sequence(passed=20, matched=0),
        ))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_NOT_REPRODUCED)

    def test_row11_not_reproduced_after_reference_was_established_during_search(self):
        """ADR-011's motivating case: single-trial ddmin finds a candidate from one lucky
        observation, but proper re-verification shows it does not actually hold up. Distinct
        from row 5: a reference WAS established (during the search), just not by this sequence,
        on re-verification."""
        d = DecisionInput(**base_kwargs(
            reference_established=True, alone=alone(), sequence=sequence(passed=20, matched=0),
        ))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_NOT_REPRODUCED)

    def test_row6_victim_fails_alone(self):
        d = DecisionInput(**base_kwargs(alone=alone(passed=19, matched=1)))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_VICTIM_FAILS_ALONE)

    def test_row7_victim_fails_alone_differently(self):
        """FT003: a victim failing alone with a DIFFERENT signature is not a pass."""
        d = DecisionInput(**base_kwargs(alone=alone(passed=0, other=20)))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_VICTIM_FAILS_ALONE_DIFFERENTLY)

    def test_row7_beats_row6_when_both_present(self):
        """Row 6 (alone.matched >= 1) is checked first; row 7 only fires when matched == 0."""
        d = DecisionInput(**base_kwargs(alone=alone(passed=10, matched=5, other=5)))
        decision = decide(d)
        self.assertEqual(decision.unresolved_reason, REASON_VICTIM_FAILS_ALONE)

    def test_row8_infrastructure_failure_alone(self):
        d = DecisionInput(**base_kwargs(alone=alone(passed=18, infra=2)))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_INFRASTRUCTURE_FAILURE)

    def test_row9_signature_mismatch(self):
        d = DecisionInput(**base_kwargs(sequence=sequence(passed=15, matched=0, other=5)))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_SIGNATURE_MISMATCH)

    def test_row10_infrastructure_failure_in_sequence(self):
        """Reference established during search, but the candidate sequence's own
        re-verification only crashed/timed out -- distinct from row 4 (no reference at all)."""
        d = DecisionInput(**base_kwargs(sequence=sequence(passed=15, matched=0, infra=5)))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_INFRASTRUCTURE_FAILURE)

    def test_row11_not_reproduced_sequence_only(self):
        d = DecisionInput(**base_kwargs(sequence=sequence(passed=20, matched=0)))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_UNRESOLVED)
        self.assertEqual(decision.unresolved_reason, REASON_NOT_REPRODUCED)

    def test_row12_candidate_below_replay_threshold(self):
        d = DecisionInput(**base_kwargs(sequence=sequence(passed=8, matched=12, infra=0)))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_CANDIDATE)
        self.assertIsNone(decision.unresolved_reason)
        self.assertIn(CANDIDATE_BELOW_REPLAY_THRESHOLD, decision.candidate_reasons)
        self.assertLess(decision.sequence_interval[0], 0.70)

    def test_row12_candidate_no_resource_evidence(self):
        """ADR-010 section 4 (Q1, option A): a reliably-reproducing sequence with no resource
        edge is CANDIDATE now, not UNRESOLVED -- the Mid's NO_SUPPORTED_RESOURCE_EVIDENCE
        abstention is retired."""
        d = DecisionInput(**base_kwargs(resource_edge_exists=False))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_CANDIDATE)
        self.assertIsNone(decision.unresolved_reason)
        self.assertEqual(decision.candidate_reasons, (CANDIDATE_NO_SUPPORTED_RESOURCE_EVIDENCE,))

    def test_row12_candidate_deletion_incomplete(self):
        d = DecisionInput(**base_kwargs(deletion_status=DELETION_INCOMPLETE))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_CANDIDATE)
        self.assertIn(CANDIDATE_DELETION_EVIDENCE_INCOMPLETE, decision.candidate_reasons)

    def test_row12_candidate_deletion_inconclusive(self):
        d = DecisionInput(**base_kwargs(deletion_status=DELETION_INCONCLUSIVE))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_CANDIDATE)
        self.assertIn(CANDIDATE_DELETION_EVIDENCE_INCONCLUSIVE, decision.candidate_reasons)

    def test_row12_candidate_lists_every_unmet_claim_at_once(self):
        d = DecisionInput(**base_kwargs(
            sequence=sequence(passed=8, matched=12), resource_edge_exists=False,
            deletion_status=DELETION_INCONCLUSIVE,
        ))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_CANDIDATE)
        self.assertEqual(
            set(decision.candidate_reasons),
            {CANDIDATE_BELOW_REPLAY_THRESHOLD, CANDIDATE_DELETION_EVIDENCE_INCONCLUSIVE,
             CANDIDATE_NO_SUPPORTED_RESOURCE_EVIDENCE},
        )

    def test_row13_verified(self):
        d = DecisionInput(**base_kwargs())
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_VERIFIED)
        self.assertIsNone(decision.unresolved_reason)
        self.assertEqual(decision.candidate_reasons, ())
        self.assertGreaterEqual(decision.sequence_interval[0], d.lower_bound_threshold)

    def test_row13_verified_with_deletion_verified(self):
        d = DecisionInput(**base_kwargs(deletion_status=DELETION_VERIFIED))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_VERIFIED)

    def test_row13_verified_with_deletion_not_applicable(self):
        d = DecisionInput(**base_kwargs(deletion_status=DELETION_NOT_APPLICABLE))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_VERIFIED)

    def test_row13_verified_when_deletion_not_yet_checked(self):
        """deletion_status=None (W20 not landed) must not regress an otherwise-VERIFIED verdict
        -- ADR-010 test T6."""
        d = DecisionInput(**base_kwargs(deletion_status=None))
        decision = decide(d)
        self.assertEqual(decision.outcome, OUTCOME_VERIFIED)


class TestDecisionInputValidation(unittest.TestCase):
    def test_alone_n_zero_raises(self):
        with self.assertRaises(ValueError):
            DecisionInput(**base_kwargs(alone=RunTally(0, 0, 0, 0, 0)))

    def test_sequence_n_zero_raises(self):
        with self.assertRaises(ValueError):
            DecisionInput(**base_kwargs(sequence=RunTally(0, 0, 0, 0, 0)))

    def test_confidence_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            DecisionInput(**base_kwargs(confidence=1.0))

    def test_lower_bound_threshold_out_of_range_raises(self):
        with self.assertRaises(ValueError):
            DecisionInput(**base_kwargs(lower_bound_threshold=1.5))

    def test_invalid_deletion_status_raises(self):
        with self.assertRaises(ValueError):
            DecisionInput(**base_kwargs(deletion_status="NOT_A_REAL_STATUS"))

    def test_negative_infrastructure_failures_anywhere_raises(self):
        with self.assertRaises(ValueError):
            DecisionInput(**base_kwargs(infrastructure_failures_anywhere=-1))


if __name__ == "__main__":
    unittest.main()
