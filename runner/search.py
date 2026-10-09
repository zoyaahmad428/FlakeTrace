"""Reproduce the original failure and search for a single polluter (W7, ADR-004)."""

from typing import List, Optional, Sequence, Tuple

from eval.baseline import FailureSignature, TestIdentifier

# Exception types the runner invents for a crashed, timed-out or skipped test (ADR-003).
SYNTHETIC_PREFIX = "flaketrace."


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
