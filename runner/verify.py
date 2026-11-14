"""Repeated runs, counted as ADR-010 tallies (W7, ADR-004; W18, ADR-010)."""

from typing import Optional, Sequence, Tuple

from eval.baseline import SYNTHETIC_PREFIX, FailureSignature, RunTally, TestIdentifier, tally


def repeat(
    runner, sequence: Sequence[TestIdentifier], victim: TestIdentifier, reference: FailureSignature, n: int
) -> RunTally:
    """Run `sequence` n times, each in a fresh JVM, and tally the victim's outcomes against `reference`."""
    return tally([runner.run_ordered(list(sequence))[victim] for _ in range(n)], reference)


def repeat_without_reference(runner, victim: TestIdentifier, n: int) -> Tuple[Optional[FailureSignature], RunTally]:
    """Run the victim alone n times when nothing reproduced yet (ADR-008). The first real failure
    becomes the reference and every run is tallied against it. Returns (reference or None, tally)."""
    outcomes = [runner.run_ordered([victim])[victim] for _ in range(n)]
    reference = next((o.failure_signature for o in outcomes if not o.passed
                      and not o.failure_signature.exception_type.startswith(SYNTHETIC_PREFIX)), None)
    return reference, tally(outcomes, reference)
