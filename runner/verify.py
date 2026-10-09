"""Repeated-run counts (W7, ADR-004)."""

from typing import Sequence, Tuple

from eval.baseline import FailureSignature, TestIdentifier


def repeat(
    runner, sequence: Sequence[TestIdentifier], victim: TestIdentifier, reference: FailureSignature, n: int
) -> Tuple[int, int]:
    """Run `sequence` n times, each in a fresh JVM. Returns (runs where the victim failed with a
    signature matching `reference`, runs where the victim failed for any reason)."""
    successes = any_failures = 0
    for _ in range(n):
        outcome = runner.run_ordered(list(sequence))[victim]
        if not outcome.passed:
            any_failures += 1
            if outcome.failure_signature.matches(reference):
                successes += 1
    return successes, any_failures
