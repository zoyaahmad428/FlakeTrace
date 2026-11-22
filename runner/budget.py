"""Budget ledger (W24, ADR-014 sections 1-3, Interface 6): every JVM run goes through BudgetedRunner,
which counts it in test-method invocations per phase and refuses a run that would cross the limit."""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

from eval.baseline import RunOutcome, TestIdentifier

# W35: `pair` is pair mode's [candidate, victim] scan (ADR-016, Interface 9 P6), exploration like `search`.
PHASES = ("reproduce", "shuffle", "alone", "pair", "search", "minimise", "deletion", "verify")
EXPLORE = frozenset({"reproduce", "shuffle", "pair", "search", "minimise"})


@dataclass(frozen=True)
class Budget:
    limit_invocations: Optional[int] = None  # None = unlimited, still counted
    limit_seconds: Optional[float] = None


@dataclass(frozen=True)
class BudgetAccount:
    limit_invocations: Optional[int]
    limit_seconds: Optional[float]
    reserve_invocations: int
    spent: Dict[str, int]
    launches: int
    wall_seconds: float
    analysis_seconds: Optional[float]
    policy: str
    exhausted: bool
    exhausted_phase: Optional[str]
    candidates_total: int
    candidates_tried: int


class BudgetExhausted(Exception):
    def __init__(self, phase: str):
        super().__init__(f"budget exhausted in {phase}")
        self.phase = phase


def reserve(n: int) -> int:
    """Interface 6 B1: n alone runs plus n runs of [polluter, victim]."""
    return 3 * n


class BudgetedRunner:
    """Satisfies eval.baseline.OrderRunner. Exploration (B3, B7) is refused by raising BudgetExhausted;
    verification asks first with affords() / affordable_runs() (B5, B6). A refusal writes a budget-stop
    line through the recorder (B8)."""

    def __init__(self, runner, budget: Budget, n: int, victim: TestIdentifier, clock=time.monotonic):
        self._runner = runner
        self.budget = budget
        self.reserve = reserve(n)
        self._victim = victim
        self._clock = clock
        self._start = clock()
        self._step = "unlabelled"
        self._note: dict = {}
        self.spent = {phase: 0 for phase in PHASES}
        self._seconds: Dict[str, float] = {}
        self._outcomes: Dict[str, List[RunOutcome]] = {phase: [] for phase in PHASES}
        self.exhausted_phase: Optional[str] = None

    @property
    def step(self) -> str:
        return self._step

    @step.setter
    def step(self, value: str) -> None:
        self._step = value
        if hasattr(self._runner, "step"):
            self._runner.step = value

    @property
    def note(self) -> dict:
        return self._note

    @note.setter
    def note(self, value: dict) -> None:
        self._note = value
        if hasattr(self._runner, "note"):
            self._runner.note = value

    def total(self) -> int:
        return sum(self.spent.values())

    def _fits(self, phase: str, cost: int, keep: int = 0) -> bool:
        limit, seconds = self.budget.limit_invocations, self.budget.limit_seconds
        if phase in EXPLORE:
            if seconds is not None and self._clock() - self._start >= seconds:
                return False
            if limit is not None:
                explored = sum(self.spent[p] for p in EXPLORE)
                return explored + cost <= limit - self.reserve
            return True
        return limit is None or self.total() + cost + keep <= limit

    def _refuse(self, phase: str, cost: int) -> None:
        if self.exhausted_phase is None:
            self.exhausted_phase = phase
        if hasattr(self._runner, "write_event"):
            self._runner.write_event({"type": "budget-stop", "phase": phase, "would_cost": cost,
                                      "spent": self.total()})

    def affords(self, phase: str, cost: int, keep: int = 0) -> bool:
        if self._fits(phase, cost, keep):
            return True
        self._refuse(phase, cost)
        return False

    def affordable_runs(self, cost: int, n: int) -> int:
        limit = self.budget.limit_invocations
        return n if limit is None else max(0, min(n, (limit - self.total()) // cost))

    def run_ordered(self, order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]:
        cost = len(order)
        if not self.affords(self._step, cost):
            raise BudgetExhausted(self._step)
        started = self._clock()
        results = self._runner.run_ordered(order)
        self._seconds[self._step] = self._seconds.get(self._step, 0.0) + self._clock() - started
        self.spent[self._step] = self.spent.get(self._step, 0) + cost
        self._outcomes.setdefault(self._step, []).append(results[self._victim])
        return results

    def victim_outcomes(self, phase: str) -> List[RunOutcome]:
        return list(self._outcomes.get(phase, []))

    def seconds_in(self, phase: str) -> float:
        """Wall seconds spent inside the runs of `phase` (W35: the next: line's estimate)."""
        return self._seconds.get(phase, 0.0)

    def launches_in(self, phase: str) -> int:
        return len(self._outcomes.get(phase, []))

    def write_event(self, entry: dict) -> None:
        """A record line that is not a run (e.g. W25's ranking line); dropped when nothing records."""
        if hasattr(self._runner, "write_event"):
            self._runner.write_event(entry)

    def account(self, candidates_total: int, policy: str = "original",
                analysis_seconds: Optional[float] = None) -> BudgetAccount:
        return BudgetAccount(
            limit_invocations=self.budget.limit_invocations,
            limit_seconds=self.budget.limit_seconds,
            reserve_invocations=self.reserve,
            spent={phase: self.spent.get(phase, 0) for phase in PHASES},
            launches=sum(len(runs) for runs in self._outcomes.values()),
            wall_seconds=round(self._clock() - self._start, 3),
            analysis_seconds=analysis_seconds,
            policy=policy,
            exhausted=self.exhausted_phase is not None,
            exhausted_phase=self.exhausted_phase,
            candidates_total=candidates_total,
            candidates_tried=self.launches_in("search"),  # one [candidate, victim] run each
        )
