"""Random-order baseline for FlakeTrace evaluation (Iteration 1).

Defines the `OrderRunner` interface Member 2's real single-JVM order runner implements
(`runner.order_runner.OrderRunner` satisfies it structurally), and a random-shuffle baseline
built against that interface -- run for real against F1 (see eval/README.md and
docs/evidence-m3.md for status and numbers). It is unit-tested with a FakeOrderRunner that
lives ONLY under eval/tests/ (see eval/tests/fake_runner.py); this module must never import it.

Shuffling (2026-10-11) groups by class first: a shuffled order picks a random class order,
then a random method order within each class, but never interleaves two classes' methods --
see `_shuffle_classes_then_methods`'s docstring for why.
"""

import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Tuple


@dataclass(frozen=True)
class TestIdentifier:
    """A single test method. `class_name` (not `class`, a reserved word)
    mirrors the report schema's {"class": ..., "method": ...} shape."""

    class_name: str
    method: str

    def to_dict(self) -> dict:
        return {"class": self.class_name, "method": self.method}

    @staticmethod
    def from_dict(d: dict) -> "TestIdentifier":
        return TestIdentifier(class_name=d["class"], method=d["method"])

    def __str__(self) -> str:
        return f"{self.class_name}#{self.method}"


@dataclass(frozen=True)
class FailureSignature:
    """Mirrors the report schema's failure_signature shape."""

    exception_type: str
    stack_trace: str
    message: Optional[str] = None

    def matches(self, other: "FailureSignature") -> bool:
        """Signature equality compares exception_type + stack_trace only.
        `message` is ignored because it can vary run to run for the same
        underlying bug (e.g. an assertion's expected/actual values), so
        requiring exact message equality would under-count genuine matches."""
        return self.exception_type == other.exception_type and self.stack_trace == other.stack_trace


@dataclass(frozen=True)
class RunOutcome:
    """One test's outcome from one run. Exactly one of (passed, failure_signature)
    is meaningful: passed implies no signature, failed requires one."""

    passed: bool
    failure_signature: Optional[FailureSignature] = None

    def __post_init__(self):
        if self.passed and self.failure_signature is not None:
            raise ValueError("RunOutcome: passed=True cannot carry a failure_signature")
        if not self.passed and self.failure_signature is None:
            raise ValueError("RunOutcome: passed=False requires a failure_signature")


class OrderRunner(Protocol):
    """The interface Member 2's real order runner must implement: run an
    ordered list of test methods in ONE JVM, and return each test's outcome.

    This is a structural (duck-typed) interface via typing.Protocol -- any
    object with a matching run_ordered method satisfies it, no inheritance
    required. No implementation of this protocol exists in this repo yet.
    """

    def run_ordered(self, order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]:
        ...


@dataclass(frozen=True)
class BaselineAttempt:
    seed: int
    order: Tuple[TestIdentifier, ...]
    victim_outcome: RunOutcome
    matched_reference: bool


@dataclass(frozen=True)
class BaselineResult:
    victim: TestIdentifier
    reference_signature: FailureSignature
    attempts: Tuple[BaselineAttempt, ...]
    found: bool

    @property
    def runs_attempted(self) -> int:
        return len(self.attempts)

    @property
    def matching_attempt(self) -> Optional[BaselineAttempt]:
        for attempt in self.attempts:
            if attempt.matched_reference:
                return attempt
        return None


def _shuffle_classes_then_methods(pool: List[TestIdentifier], rng: random.Random) -> List[TestIdentifier]:
    """Shuffle which class runs first, then (independently) each class's own method order --
    but never interleave two classes' methods in the result. JUnitCore/Surefire run a suite
    class by class; there is no way to hand them an order where ClassA#m1, ClassB#m1, ClassA#m2
    run in that sequence in one JVM (iDFlakies [3] shuffles the same way for this reason). A
    plain whole-pool shuffle (the previous behaviour) can propose exactly that impossible order,
    which `runner.order_runner.OrderRunner` could not actually execute as requested."""
    classes: Dict[str, List[TestIdentifier]] = {}
    class_order: List[str] = []
    for t in pool:
        if t.class_name not in classes:
            classes[t.class_name] = []
            class_order.append(t.class_name)
        classes[t.class_name].append(t)

    rng.shuffle(class_order)
    order: List[TestIdentifier] = []
    for class_name in class_order:
        methods = classes[class_name][:]
        rng.shuffle(methods)
        order.extend(methods)
    return order


def run_random_order_baseline(
    runner: OrderRunner,
    victim: TestIdentifier,
    candidates: List[TestIdentifier],
    reference_signature: FailureSignature,
    max_runs: int,
    base_seed: int = 0,
) -> BaselineResult:
    """Repeatedly shuffle {candidates + victim} with a fresh seed (base_seed,
    base_seed+1, ...) and run the resulting order through `runner`, stopping
    as soon as the victim's outcome matches `reference_signature`. Every
    seed tried is recorded in the returned BaselineResult, whether it
    matched or not -- this is the "record every seed" requirement.

    Raises ValueError if max_runs <= 0 or if victim also appears in
    candidates (the pool must not contain the victim twice).
    """
    if max_runs <= 0:
        raise ValueError(f"max_runs must be > 0, got {max_runs!r}")
    if victim in candidates:
        raise ValueError(f"victim {victim} must not also appear in candidates")

    pool = list(candidates) + [victim]
    attempts: List[BaselineAttempt] = []

    for i in range(max_runs):
        seed = base_seed + i
        rng = random.Random(seed)
        order = _shuffle_classes_then_methods(pool, rng)

        outcomes = runner.run_ordered(order)
        victim_outcome = outcomes[victim]
        matched = (
            not victim_outcome.passed
            and victim_outcome.failure_signature is not None
            and victim_outcome.failure_signature.matches(reference_signature)
        )

        attempts.append(
            BaselineAttempt(
                seed=seed,
                order=tuple(order),
                victim_outcome=victim_outcome,
                matched_reference=matched,
            )
        )
        if matched:
            break

    found = attempts[-1].matched_reference if attempts else False
    return BaselineResult(
        victim=victim,
        reference_signature=reference_signature,
        attempts=tuple(attempts),
        found=found,
    )
