"""Shrink the tests before the victim to a 1-minimal polluter set by delta debugging (W10, ADR-007).

Zeller's ddmin: try chunks, then complements, then finer chunks. The last round removes each
remaining test on its own, so every test in the result is needed (1-minimal, not minimum).
"""

from typing import Dict, FrozenSet, List, Sequence, Tuple

from eval.baseline import FailureSignature, TestIdentifier


def ddmin(
    runner, prefix: Sequence[TestIdentifier], victim: TestIdentifier, reference: FailureSignature
) -> Tuple[List[TestIdentifier], int]:
    """`prefix` must be non-empty and already known to make the victim fail with `reference`.
    Returns (1-minimal subset of `prefix` in its original order, JVM runs made)."""
    cache: Dict[FrozenSet[TestIdentifier], bool] = {frozenset(prefix): True}
    runs = 0

    def fails(subset: List[TestIdentifier]) -> bool:
        nonlocal runs
        key = frozenset(subset)
        if key not in cache:
            runs += 1
            outcome = runner.run_ordered(subset + [victim])[victim]
            # Only the reference failure counts; a crash or another exception never shrinks the set.
            cache[key] = not outcome.passed and outcome.failure_signature.matches(reference)
        return cache[key]

    current, k = list(prefix), 2
    while len(current) > 1:
        chunks = _split(current, k)
        smaller = next((chunk for chunk in chunks if fails(chunk)), None)
        if smaller is not None:
            current, k = smaller, 2
            continue
        complements = ([t for t in current if t not in chunk] for chunk in chunks)
        smaller = next((rest for rest in complements if fails(rest)), None)
        if smaller is not None:
            current, k = smaller, max(k - 1, 2)
            continue
        if k >= len(current):
            break
        k = min(2 * k, len(current))
    return current, runs


def _split(items: List[TestIdentifier], k: int) -> List[List[TestIdentifier]]:
    size, extra = divmod(len(items), k)
    chunks, start = [], 0
    for i in range(k):
        end = start + size + (1 if i < extra else 0)
        chunks.append(items[start:end])
        start = end
    return chunks
