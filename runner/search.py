"""Reproduce the original failure and search for a single polluter (W7, ADR-004)."""

from typing import List, Optional, Sequence, Tuple

from eval.baseline import SYNTHETIC_PREFIX, FailureSignature, RunOutcome, TestIdentifier


def reproduce(
    runner, order: Sequence[TestIdentifier], victim: TestIdentifier, attempts: int
) -> Tuple[Optional[FailureSignature], int, int]:
    """Run `order` up to `attempts` times, stopping at the first run where the victim fails with
    a real (not crash/timeout/skip) failure. Returns (reference signature or None, runs made,
    runs where the victim failed for any reason)."""
    any_failures = 0
    for run in range(1, attempts + 1):
        outcome = runner.run_ordered(list(order))[victim]
        if outcome.passed:
            continue
        any_failures += 1
        if not outcome.failure_signature.exception_type.startswith(SYNTHETIC_PREFIX):
            return outcome.failure_signature, run, any_failures
    return None, attempts, any_failures


def candidate_order(
    original_order: Sequence[TestIdentifier],
    victim: TestIdentifier,
    priority: Optional[Sequence[TestIdentifier]] = None,
) -> List[TestIdentifier]:
    """Tests before the victim: those in `priority` first (in that order), then the rest in
    original order. Priority entries not before the victim are ignored."""
    before = list(original_order[: list(original_order).index(victim)])
    first = [t for t in dict.fromkeys(priority or []) if t in before]
    return first + [t for t in before if t not in first]


def find_polluter(
    runner,
    original_order: Sequence[TestIdentifier],
    victim: TestIdentifier,
    reference: FailureSignature,
    priority: Optional[Sequence[TestIdentifier]] = None,
) -> Tuple[Optional[TestIdentifier], int]:
    """Run [candidate, victim] once per candidate; return the first candidate after which the
    victim fails with the reference signature, and the number of runs made."""
    runs = 0
    for candidate in candidate_order(original_order, victim, priority):
        runs += 1
        outcome = runner.run_ordered([candidate, victim])[victim]
        if not outcome.passed and outcome.failure_signature.matches(reference):
            return candidate, runs
    return None, runs


def find_pair(
    runner, candidates: Sequence[TestIdentifier], victim: TestIdentifier, firsts: Optional[List[RunOutcome]] = None
) -> Tuple[Optional[TestIdentifier], Optional[FailureSignature], int, List[RunOutcome]]:
    """W35 pair mode (ADR-016, Interface 9 P3): run [candidate, victim] once per candidate. A real failure is
    adopted only if one re-run of the same pair fails again with a matching signature, so one random failure
    cannot end the scan. Returns (polluter, reference, pairs tried, the victim's outcome in each pair's first run).
    `firsts` is filled as the scan goes, so a caller still has the count when the budget stops it."""
    firsts = [] if firsts is None else firsts
    for candidate in candidates:
        outcome = runner.run_ordered([candidate, victim])[victim]
        firsts.append(outcome)
        if outcome.passed or outcome.failure_signature.exception_type.startswith(SYNTHETIC_PREFIX):
            continue
        again = runner.run_ordered([candidate, victim])[victim]
        if not again.passed and again.failure_signature.matches(outcome.failure_signature):
            return candidate, outcome.failure_signature, len(firsts), firsts
    return None, None, len(firsts), firsts
