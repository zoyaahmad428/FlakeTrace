"""FAKE order runner -- for unit tests ONLY.

FakeOrderRunner never launches a JVM and never runs real Maven/JUnit; it
decides outcomes purely from a caller-supplied function. It exists so
eval/tests/test_baseline.py can exercise eval.baseline.run_random_order_baseline
deterministically without Member 2's real runner, which does not exist in
this repo yet (see eval/README.md).

This module must live ONLY under eval/tests/. eval/baseline.py and any real
CLI must never import it -- importing a fake runner from production code
would silently make "the baseline ran" indistinguishable from "the baseline
was faked."
"""

from typing import Callable, Dict, List

from eval.baseline import RunOutcome, TestIdentifier


class FakeOrderRunner:
    """A scriptable stand-in for the real OrderRunner.

    `outcome_fn(order, test)` decides one test's outcome given the full
    order it ran in, so a test can script scenarios like "the victim fails
    iff some specific polluter appears before it" without any real test
    execution.
    """

    def __init__(self, outcome_fn: Callable[[List[TestIdentifier], TestIdentifier], RunOutcome]):
        self._outcome_fn = outcome_fn
        self.calls: List[List[TestIdentifier]] = []

    def run_ordered(self, order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]:
        self.calls.append(list(order))
        return {test: self._outcome_fn(order, test) for test in order}
