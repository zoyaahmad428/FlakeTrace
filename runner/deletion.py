"""W20 deletion checks (ADR-011, docs/contracts/interfaces.md Interface 4): after minimisation,
leave each kept test out, repeat the rest plus the victim m times, and label the result.
The labels use M3's Wilson interval and threshold, so there is one policy, not two."""

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from eval.baseline import FailureSignature, RunTally, TestIdentifier
from eval.outcome import DEFAULT_LOWER_BOUND_THRESHOLD
from eval.stats import wilson_interval
from runner.verify import repeat

NEEDED = "NEEDED"
NOT_NEEDED = "NOT_NEEDED"
INCONCLUSIVE = "INCONCLUSIVE"
NOT_RUN = "NOT_RUN"  # the budget ended before the check (ADR-011 section 3); produced from W24 on
DELETION_RUN = "deletion-run"
ALONE_CHECK = "alone-check"


@dataclass(frozen=True)
class DeletionCheck:
    removed: TestIdentifier
    runs: Optional[RunTally]
    status: str
    source: str
    round: int


def label(runs: RunTally, m: int) -> str:
    """NEEDED: the victim passed all m runs without the test. NOT_NEEDED: the failure still
    reproduces reliably without it. Anything else is INCONCLUSIVE (ADR-011 section 1)."""
    if runs.passed == m:
        return NEEDED
    if wilson_interval(runs.matched, m)[0] >= DEFAULT_LOWER_BOUND_THRESHOLD:
        return NOT_NEEDED
    return INCONCLUSIVE


def check_deletions(runner, polluters: List[TestIdentifier], victim: TestIdentifier,
                    reference: FailureSignature, m: int,
                    alone_tally: RunTally, can_afford: Callable[[int, int], bool] = lambda cost, kept: True,
                    ) -> Tuple[List[DeletionCheck], List[TestIdentifier]]:
    """Check every kept test in rounds (ADR-011 sections 1-3). A NOT_NEEDED test is dropped (the first
    one only) and the checks start again on the smaller set; at most len(polluters) rounds. With one
    kept test, "the rest plus the victim" is the victim alone: its alone tally is reused (section 2).
    Returns every check of every round, and the final kept tests in their original order.
    `can_afford(cost, kept)` is the budget (W24, Interface 6 B5): a check that does not fit, and every
    later check of that round, is NOT_RUN, and nothing is dropped."""
    kept, checks, round_ = list(polluters), [], 1
    while True:
        if len(kept) == 1:
            checks.append(DeletionCheck(kept[0], alone_tally, label(alone_tally, alone_tally.n), ALONE_CHECK, round_))
            return checks, kept
        this_round = []
        for i, test in enumerate(kept):
            if not can_afford(m * len(kept), len(kept)):
                this_round += [DeletionCheck(t, None, NOT_RUN, DELETION_RUN, round_) for t in kept[i:]]
                return checks + this_round, kept
            # ADR-011 "Consequences": each run line names the removed test, so ADR-013's recount can redo it.
            if hasattr(runner, "note"):
                runner.note = {"removed": str(test), "round": round_}
            runs = repeat(runner, [t for t in kept if t != test] + [victim], victim, reference, m)
            if hasattr(runner, "note"):
                runner.note = {}
            this_round.append(DeletionCheck(test, runs, label(runs, m), DELETION_RUN, round_))
        checks += this_round
        dropped = next((c.removed for c in this_round if c.status == NOT_NEEDED), None)
        if dropped is None:
            return checks, kept
        kept.remove(dropped)
        round_ += 1
