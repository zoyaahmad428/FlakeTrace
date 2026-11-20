"""W7 entry point (ADR-004): reproduce the failure, check the victim alone, search for a single
polluter, repeat the sequence, check source integrity, record every run. When no single test is
enough, ddmin shrinks the tests before the victim with single trials (W10, ADR-007). Returns ADR-010
tallies (W18); the verdict is M3's eval.outcome.decide() (W9 builds the report)."""

import platform
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from eval.baseline import FailureSignature, RunTally, TestIdentifier, tally
from runner.budget import Budget, BudgetAccount, BudgetedRunner, BudgetExhausted, reserve
from runner.deletion import DeletionCheck, check_deletions
from runner.discovery import DiscoveryConfigError, discover_order, project_selection
from runner.integrity import SourceIntegrity, compare, integrity_of, snapshot
from runner.minimise import ddmin
from runner.orders import distinct_shuffles, search_orders
from runner.order_runner import OrderRunner, java_version, maven_test_classpath
from runner.policy import (DEEPEN_SHARE, POLICIES, SCOPES, EvidenceRanker, SearchPolicy, choose_order,
                           in_package)
from runner.recording import RecordingRunner
from runner.search import candidate_order, find_polluter, reproduce
from runner.verify import repeat, repeat_without_reference

POLLUTER_FOUND = "POLLUTER_FOUND"
VICTIM_FAILS_ALONE = "VICTIM_FAILS_ALONE"
# ADR-010 section 5: the failure was seen once and could not be obtained again.
INCONSISTENT = "INCONSISTENT"
NOT_REPRODUCED = "NOT_REPRODUCED"
# W24 (Interface 6): the budget stopped exploration before a polluter set was found.
BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


class DiagnoseInputError(ValueError):
    """A wrong argument to diagnose() (n, victim, record folder) -- the caller's input, not a bug."""


@dataclass(frozen=True)
class DiagnosisRuns:
    status: str
    victim: TestIdentifier
    original_order: List[TestIdentifier]
    reference_signature: Optional[FailureSignature]
    polluters: List[TestIdentifier]
    sequence: List[TestIdentifier]
    # ADR-010 section 1 (W18): how the n runs of the sequence and of the victim alone ended. Named
    # *_tally because `sequence` is already the test list. (The five count fields that duplicated
    # them were removed in A4, 2026-11-20, once eval/ read only the tallies.)
    sequence_tally: RunTally
    alone_tally: RunTally
    search_runs: int
    source_integrity: Optional[SourceIntegrity] = None
    execution_record: Optional[str] = None
    minimise_runs: int = 0
    # ADR-008: how the failing order was found (read by eval.report as `order_exploration`).
    order_given: bool = False
    shuffled_orders: int = 0
    orders_exhausted: bool = False
    shuffle_seed_base: int = 0
    reproducing_seed: Optional[int] = None
    infrastructure_failures: int = 0
    shuffle_infrastructure_failures: int = 0  # shuffle runs where the victim only crashed/timed out
    alone_infrastructure_failures: int = 0  # same for alone runs when nothing reproduced
    # W20 (ADR-011, Interface 4): every kept test checked by repeated removal; [] unless POLLUTER_FOUND.
    deletion_checks: List[DeletionCheck] = field(default_factory=list)
    # W24 (Interface 6): what the diagnosis spent, per phase; run_steps always sets it.
    budget: Optional[BudgetAccount] = None
    # W25 (Interface 7): how the search ordered its candidates; run_steps always sets it.
    search: Optional[SearchPolicy] = None


def _runs(status, victim, order, reference, polluters, sequence, sequence_tally: RunTally,
          alone_tally: RunTally, search_runs: int, **more) -> DiagnosisRuns:
    return DiagnosisRuns(status, victim, order, reference, polluters, sequence, sequence_tally, alone_tally,
                         search_runs, **more)


def check_budget(budget: Optional[Budget], n: int, start_length: int) -> None:
    """Interface 6 B2: the limit must cover the reserve, one run of the starting order (up to and
    including the victim) and one candidate pair."""
    if budget is None:
        return
    if budget.limit_seconds is not None and budget.limit_seconds <= 0:
        raise DiagnoseInputError(f"the seconds limit must be > 0, got {budget.limit_seconds!r}")
    limit = budget.limit_invocations
    minimum = reserve(n) + start_length + 2
    if limit is not None and limit < minimum:
        raise DiagnoseInputError(
            f"an invocation limit of {limit} is below the minimum {minimum} for n={n}: the verification "
            f"reserve {reserve(n)}, one run of the starting order ({start_length} tests) and one candidate pair")


def run_steps(
    runner,
    original_order: Sequence[TestIdentifier],
    victim: TestIdentifier,
    n: int,
    priority: Optional[Sequence[TestIdentifier]] = None,
    shuffles: int = 0,
    seed_base: int = 0,
    order_given: bool = False,
    budget: Optional[Budget] = None,
    clock=time.monotonic,
    policy: str = "original",
    scope: str = "module",
    ranker_for=None,
) -> DiagnosisRuns:
    """Steps 3-6 of ADR-004 on any OrderRunner, plus ADR-008: shuffled orders when the starting
    order never fails, and the alone check always. Stops early as the ADRs' status tables say.
    Every run goes through the budget ledger (W24, Interface 6), which may stop exploration. `policy`
    orders the single-polluter search (W25, Interface 7); `ranker_for(candidates, victim)` gives the
    ranker for `ranked`."""
    if n < 1:
        raise DiagnoseInputError(f"n must be >= 1, got {n!r}")
    if victim not in original_order:
        raise DiagnoseInputError(f"victim {victim} is not in the original order")
    if policy not in POLICIES:
        raise DiagnoseInputError(f"policy must be one of {', '.join(POLICIES)}, got {policy!r}")
    if policy == "ranked" and ranker_for is None:
        raise DiagnoseInputError("the ranked policy needs a ranker")
    if priority and policy != "original":
        raise DiagnoseInputError(f"a priority list orders the search itself; it cannot be combined with policy {policy}")
    full = list(original_order)
    check_budget(budget, n, full.index(victim) + 1)
    ledger = BudgetedRunner(runner, budget or Budget(), n, victim, clock)
    chosen = {"search": SearchPolicy(policy, scope, seed_base if policy == "random" else None, [], DEEPEN_SHARE,
                                     None, None), "analysis_seconds": None}

    def order_search(candidates):
        # P1-P6: one candidate order per diagnosis, chosen once, recorded before the first search run.
        ranker = ranker_for(candidates, victim) if policy == "ranked" and ranker_for is not None else None
        order, search, scores, seconds = choose_order(policy, candidates, scope=scope, seed=seed_base, ranker=ranker,
                                                      limit_seconds=(budget or Budget()).limit_seconds)
        chosen.update(search=search, analysis_seconds=seconds)
        ledger.write_event({"type": "ranking", "policy": policy, "scope": scope, "seed": search.seed,
                            "depths": search.depths, "order": [str(test) for test in order],
                            "scores": [list(score) for score in scores], "note": search.note,
                            # M1's #138 suggestion (agreed by M3): "could not analyse" is not "no evidence".
                            "notes": {str(test): note for test, note in getattr(ranker, "notes", {}).items()}})
        return order

    result, searched = _steps(ledger, full, victim, n, priority, shuffles, seed_base, order_given, order_search)
    return replace(result, search=chosen["search"],
                   budget=ledger.account(len(searched) - 1, policy, chosen["analysis_seconds"]))


def _steps(runner: BudgetedRunner, full, victim, n, priority, shuffles, seed_base, order_given, order_search):
    """run_steps' body. Returns (the diagnosis, the order searched)."""
    order = full[: full.index(victim) + 1]
    reference, attempts, attempt_failures, cut = None, 0, 0, None
    explore = dict(order_given=order_given, shuffle_seed_base=seed_base)
    try:
        _label(runner, "reproduce")
        reference, attempts, attempt_failures = reproduce(runner, order, victim, n)
        if reference is None and shuffles > 0:
            # The starting order never failed for real: try valid shuffled orders of the whole suite (ADR-008).
            _label(runner, "shuffle")
            candidates, exhausted = distinct_shuffles(full, victim, shuffles, seed_base)
            seed, found, found_reference, tried, shuffle_any = search_orders(runner, candidates, victim)
            explore.update(shuffled_orders=tried, orders_exhausted=exhausted and found is None,
                           # every failure before the reproducing one was a crash, timeout or skip
                           shuffle_infrastructure_failures=shuffle_any - (1 if found is not None else 0))
            if found is not None:
                order, reference = found, found_reference
                explore["reproducing_seed"] = seed
    except BudgetExhausted as stop:
        # Exploration ended (B3/B7) before any real failure; the ledger kept what each phase saw.
        cut = stop.phase
        seen = runner.victim_outcomes("reproduce")
        attempts, attempt_failures = len(seen), sum(not o.passed for o in seen)
        if cut == "shuffle":
            shuffled = runner.victim_outcomes("shuffle")
            explore.update(shuffled_orders=len(shuffled), orders_exhausted=False,
                           shuffle_infrastructure_failures=sum(not o.passed for o in shuffled))

    def budget_exhausted(alone):
        # Interface 6: nothing blamed; the sequence is the order searched, tallied over the runs of that
        # order -- the reproduce runs, or the one shuffled run that reproduced.
        runs_of_order = (runner.victim_outcomes("shuffle")[-1:] if "reproducing_seed" in explore
                         else runner.victim_outcomes("reproduce"))
        return _runs(BUDGET_EXHAUSTED, victim, order, reference, [], order,
                     tally(runs_of_order, reference), alone,
                     runner.launches_in("search"), minimise_runs=runner.launches_in("minimise"), **explore), order

    _label(runner, "alone")
    if reference is None:
        alone_reference, alone = repeat_without_reference(runner, victim, n)
        if alone_reference is not None:
            # The only order that failed is the victim alone, so that is the failing order reported.
            # This outranks a cut: the alone check is complete (Interface 6 point 4).
            return _runs(VICTIM_FAILS_ALONE, victim, [victim], alone_reference, [], [victim],
                         alone, alone, 0, **explore), order
        # No real failure anywhere, so every failure counted (order, shuffles, alone) was a
        # crash, timeout or skip -- which is why the reproduce runs tally as passes and infra only.
        reproduced = RunTally(attempts, attempts - attempt_failures, 0, 0, attempt_failures)
        status = BUDGET_EXHAUSTED if cut else NOT_REPRODUCED
        return _runs(status, victim, order, None, [], order, reproduced, alone, 0,
                     infrastructure_failures=attempt_failures,
                     alone_infrastructure_failures=alone.infra, **explore), order
    alone = repeat(runner, [victim], victim, reference, n)
    if alone.matched >= 1:
        return _runs(VICTIM_FAILS_ALONE, victim, order, reference, [], [victim], alone, alone, 0, **explore), order
    # alone.other and alone.infra do not stop the search: ADR-010 rows 7-8 are decided by M3's
    # decide(), and the report still says what happened after the polluter (W19).

    try:
        searched_first = order_search(candidate_order(order, victim, priority))
        _label(runner, "search")
        polluter, search_runs = find_polluter(runner, order, victim, reference, searched_first)
        polluters, minimise_runs = ([polluter], 0) if polluter is not None else ([], 0)
        if polluter is None and len(order) > 2:
            # No single test is enough: shrink everything before the victim (ADR-007). The full order
            # must fail once more first, so a flaky failure never blames every earlier test. (With one
            # earlier test, the search already ran exactly [test, victim] and saw it pass.)
            _label(runner, "minimise")
            again = runner.run_ordered(order)[victim]
            minimise_runs = 1
            if not again.passed and again.failure_signature.matches(reference):
                polluters, ddmin_runs = ddmin(runner, order[:-1], victim, reference)
                minimise_runs += ddmin_runs
    except BudgetExhausted:
        # B3/B7: a cut search or ddmin has no repeated evidence, so nothing is blamed (Interface 6 point 3).
        return budget_exhausted(alone)
    deletion_checks = []
    if polluters:
        # ADR-011: ddmin's single trials can keep a test that is not needed; check each one n times.
        # B5: before each check, hold back the final sequence check for the kept tests.
        _label(runner, "deletion")
        deletion_checks, polluters = check_deletions(
            runner, polluters, victim, reference, n, alone,
            can_afford=lambda cost, kept: runner.affords("deletion", cost, keep=n * (kept + 1)))
    sequence = polluters + [victim] if polluters else order
    _label(runner, "verify")
    repetitions = runner.affordable_runs(len(sequence), n)  # B6
    status = POLLUTER_FOUND if polluters else INCONSISTENT
    if repetitions == 0 and polluters:
        runner.affords("verify", len(sequence))  # records the refused run
        return budget_exhausted(alone)
    if repetitions == 0:
        # INCONSISTENT: exploration finished, so this is not BUDGET_EXHAUSTED. The full order costs more
        # than the reserve pays for; its one re-check in `minimise` (it passed) is the tally instead.
        runner.affords("verify", len(sequence))
        verified = tally(runner.victim_outcomes("minimise")[:1], reference)
    else:
        verified = repeat(runner, sequence, victim, reference, repetitions)
        if repetitions < n:
            runner.affords("verify", len(sequence))  # B8: the first run that did not fit, after the runs
    return _runs(status, victim, order, reference, polluters, sequence, verified, alone, search_runs,
                 minimise_runs=minimise_runs, deletion_checks=deletion_checks, **explore), order


def diagnose(
    project_dir,
    victim: TestIdentifier,
    n: int = 20,
    original_order: Optional[Sequence[TestIdentifier]] = None,
    priority: Optional[Sequence[TestIdentifier]] = None,
    record_dir="flaketrace-records",
    timeout_s: float = 120.0,
    shuffles: int = 31,
    seed: int = 0,
    command: Optional[List[str]] = None,
    lifecycle: str = "class-grouped",
    workspace: str = "in-place",
    origin=None,
    budget: Optional[Budget] = None,
    policy: str = "original",
    scope: str = "module",
) -> DiagnosisRuns:
    """`command` is the CLI's argument list, written to the record header; None from Python.
    `lifecycle` is passed to the OrderRunner (ADR-012 section 2) and recorded. When `project_dir` is a
    disposable copy (ADR-012 section 4), `origin` is the user's project: the record names it, and it
    is hashed before and after as well; `workspace` is recorded."""
    if n < 1:
        raise DiagnoseInputError(f"n must be >= 1, got {n!r}")
    if shuffles < 0:
        raise DiagnoseInputError(f"shuffles must be >= 0, got {shuffles!r}")
    if original_order is not None and victim not in original_order:
        raise DiagnoseInputError(f"victim {victim} is not in the original order")
    if original_order is not None and len(set(original_order)) != len(original_order):
        raise DiagnoseInputError("the given order lists a test more than once")
    if policy not in POLICIES:
        raise DiagnoseInputError(f"policy must be one of {', '.join(POLICIES)}, got {policy!r}")
    if scope not in SCOPES:
        raise DiagnoseInputError(f"scope must be one of {', '.join(SCOPES)}, got {scope!r}")
    if scope == "package" and original_order is not None:
        raise DiagnoseInputError("--scope package cannot be combined with --order: the order file already fixes the tests")
    project = Path(project_dir).resolve()
    source = Path(origin).resolve() if origin is not None else None
    records = Path(record_dir).resolve()
    for folder in filter(None, (project, source)):
        if records == folder or folder in records.parents:
            # A record written inside the project would itself make the integrity check fail.
            raise DiagnoseInputError(f"record_dir {records} is inside the analysed project {folder}")
    if records.exists() and not records.is_dir():
        raise DiagnoseInputError(f"record_dir {records} is a file, not a folder")
    before_source = snapshot(source) if source is not None else None
    before = snapshot(project)
    # A1: which classes are tests follows the project's own Surefire includes/excludes.
    with tempfile.TemporaryDirectory(prefix="flaketrace-pom-") as tmp:
        effective_pom = Path(tmp) / "effective-pom.xml"
        runner = OrderRunner(maven_test_classpath(project, effective_pom=effective_pom), working_dir=project,
                             timeout_s=timeout_s, lifecycle=lifecycle)
        try:
            selection = project_selection(effective_pom)
        except DiscoveryConfigError as error:
            raise DiagnoseInputError(str(error)) from error
    discovered = discover_order(runner, project / "target" / "test-classes", selection)
    if original_order is not None:
        # A typo in a given order would fail with ClassNotFound and could pass for a reproduction.
        known = set(discovered)
        unknown = [test for test in original_order if test not in known]
        if unknown:
            raise DiagnoseInputError(
                f"{len(unknown)} test(s) in the given order are not among the project's tests (first: "
                f"{unknown[0]}); only the classes the project's Surefire configuration selects are "
                f"discovered (includes {', '.join(selection.includes)}; excludes {', '.join(selection.excludes)})")
    order = list(original_order) if original_order is not None else discovered
    if scope == "package":
        order = in_package(order, victim)  # Interface 7: the real-case protocol's frozen scope rule
    if victim not in order:
        # Checked before the recorder exists, so no empty record is left behind.
        raise DiagnoseInputError(f"victim {victim} is not among the project's tests")
    check_budget(budget, n, order.index(victim) + 1)

    started = datetime.now(timezone.utc)
    record = Path(record_dir) / f"{started.strftime('%Y%m%dT%H%M%SZ')}-{victim}.jsonl"
    recorder = RecordingRunner(runner, record, {
        "victim": str(victim), "n": n, "project": str(source or project),
        "java_version": java_version(), "started": started.isoformat(), **environment(source or project),
        "order_given": original_order is not None, "shuffles": shuffles, "seed_base": seed,
        # ADR-012 section 6: what the runs ran under, so a replay can compare it (W22, W23).
        **tool_environment(), "jvm": runner.jvm_environment() or None,
        "lifecycle": runner.lifecycle, "workspace": workspace, "container_image": None, "command": command,
        # W24 (Interface 6): the limits the runs were made under, for the recount (B8).
        "budget": {"limit_invocations": budget.limit_invocations if budget else None,
                   "limit_seconds": budget.limit_seconds if budget else None,
                   "reserve_invocations": reserve(n)},
        "policy": policy, "scope": scope,  # W25 (Interface 7)
    })
    result = run_steps(recorder, order, victim, n, priority, shuffles=shuffles, seed_base=seed,
                       order_given=original_order is not None, budget=budget, policy=policy, scope=scope,
                       ranker_for=lambda candidates, v: EvidenceRanker(project, v, candidates))
    integrity = integrity_of(compare(before, snapshot(project)),
                             compare(before_source, snapshot(source)) if source is not None else None)
    return replace(result, source_integrity=integrity, execution_record=str(record))


def environment(project: Path) -> dict:
    """Execution-record facts for panel action A7: the analysed project's git commit, whether it had
    uncommitted changes, and the OS. Commit and dirty are None when the project is not in a git
    repository or git is missing -- unknown provenance never stops a diagnosis."""
    commit, dirty = git_state(project)
    return {"project_commit": commit, "project_dirty": dirty, "os": platform.platform()}


def git_state(folder: Path) -> Tuple[Optional[str], Optional[bool]]:
    """(HEAD commit, uncommitted changes under `folder`), or (None, None) outside git or without git."""
    git = shutil.which("git")
    if git:
        head = subprocess.run([git, "-C", str(folder), "rev-parse", "HEAD"], capture_output=True, text=True)
        status = subprocess.run([git, "-C", str(folder), "status", "--porcelain", "--", "."],
                                capture_output=True, text=True)
        if head.returncode == 0 and status.returncode == 0:
            return head.stdout.strip(), bool(status.stdout.strip())
    return None, None


def maven_version(text: str) -> Optional[str]:
    """The "Apache Maven x.y.z" line of `mvn -v`, without colour codes; None if there is none."""
    for line in re.sub(r"\x1b\[[0-9;]*m", "", text).splitlines():
        if line.startswith("Apache Maven"):
            return line.strip()
    return None


def tool_environment() -> dict:
    """FlakeTrace's own commit and dirty flag, Maven and Python versions (ADR-012 section 6).
    A missing tool gives None -- unknown provenance never stops a diagnosis."""
    commit, dirty = git_state(Path(__file__).resolve().parents[1])
    maven = None
    mvn = shutil.which("mvn")
    if mvn:
        try:
            maven = maven_version(subprocess.run([mvn, "-v"], capture_output=True, text=True, timeout=60).stdout)
        except (OSError, subprocess.SubprocessError):
            maven = None
    return {"tool_commit": commit, "tool_dirty": dirty, "maven_version": maven,
            "python_version": platform.python_version()}


def _label(runner, step: str) -> None:
    if isinstance(runner, (RecordingRunner, BudgetedRunner)):
        runner.step = step
