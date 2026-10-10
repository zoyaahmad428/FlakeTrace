"""W7 entry point (ADR-004): reproduce the failure, check the victim alone, search for a single
polluter, repeat the sequence, check source integrity, record every run. When no single test is
enough, ddmin shrinks the tests before the victim to a 1-minimal set (W10, ADR-007). Returns raw
counts; the verdict is M3's eval.outcome.decide() (W9 builds the report)."""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

from eval.baseline import FailureSignature, TestIdentifier
from runner.discovery import discover_order
from runner.integrity import SourceIntegrity, compare, snapshot
from runner.minimise import ddmin
from runner.order_runner import OrderRunner, java_version, maven_test_classpath
from runner.recording import RecordingRunner
from runner.search import find_polluter, reproduce
from runner.verify import repeat

POLLUTER_FOUND = "POLLUTER_FOUND"
VICTIM_FAILS_ALONE = "VICTIM_FAILS_ALONE"
NO_SINGLE_POLLUTER = "NO_SINGLE_POLLUTER"
NOT_REPRODUCED = "NOT_REPRODUCED"


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
    sequence_n: int
    sequence_successes: int
    sequence_any_failures: int
    alone_n: int
    alone_successes: int
    search_runs: int
    source_integrity: Optional[SourceIntegrity] = None
    execution_record: Optional[str] = None
    minimise_runs: int = 0


def run_steps(
    runner,
    original_order: Sequence[TestIdentifier],
    victim: TestIdentifier,
    n: int,
    priority: Optional[Sequence[TestIdentifier]] = None,
) -> DiagnosisRuns:
    """Steps 3-6 of ADR-004 on any OrderRunner. Stops early as the ADR's status table says."""
    if n < 1:
        raise DiagnoseInputError(f"n must be >= 1, got {n!r}")
    if victim not in original_order:
        raise DiagnoseInputError(f"victim {victim} is not in the original order")
    order = list(original_order[: list(original_order).index(victim) + 1])

    _label(runner, "reproduce")
    reference, attempts, attempt_failures = reproduce(runner, order, victim, n)
    if reference is None:
        return DiagnosisRuns(NOT_REPRODUCED, victim, order, None, [], order,
                             attempts, 0, attempt_failures, 0, 0, 0)

    _label(runner, "alone")
    alone_successes, alone_any = repeat(runner, [victim], victim, reference, n)
    if alone_successes >= 1:
        return DiagnosisRuns(VICTIM_FAILS_ALONE, victim, order, reference, [], [victim],
                             n, alone_successes, alone_any, n, alone_successes, 0)

    _label(runner, "search")
    polluter, search_runs = find_polluter(runner, order, victim, reference, priority)
    polluters, minimise_runs = ([polluter], 0) if polluter is not None else ([], 0)
    if polluter is None and len(order) > 1:
        # No single test is enough: shrink everything before the victim (ADR-007).
        _label(runner, "minimise")
        polluters, minimise_runs = ddmin(runner, order[:-1], victim, reference)
    sequence = polluters + [victim] if polluters else order
    _label(runner, "verify")
    successes, any_failures = repeat(runner, sequence, victim, reference, n)
    status = POLLUTER_FOUND if polluters else NO_SINGLE_POLLUTER
    return DiagnosisRuns(status, victim, order, reference, polluters, sequence,
                         n, successes, any_failures, n, 0, search_runs, minimise_runs=minimise_runs)


def diagnose(
    project_dir,
    victim: TestIdentifier,
    n: int = 20,
    original_order: Optional[Sequence[TestIdentifier]] = None,
    priority: Optional[Sequence[TestIdentifier]] = None,
    record_dir="flaketrace-records",
    timeout_s: float = 120.0,
) -> DiagnosisRuns:
    if n < 1:
        raise DiagnoseInputError(f"n must be >= 1, got {n!r}")
    if original_order is not None and victim not in original_order:
        raise DiagnoseInputError(f"victim {victim} is not in the original order")
    project = Path(project_dir).resolve()
    records = Path(record_dir).resolve()
    if records == project or project in records.parents:
        # A record written inside the project would itself make the integrity check fail.
        raise DiagnoseInputError(f"record_dir {records} is inside the analysed project {project}")
    if records.exists() and not records.is_dir():
        raise DiagnoseInputError(f"record_dir {records} is a file, not a folder")
    before = snapshot(project)
    runner = OrderRunner(maven_test_classpath(project), working_dir=project, timeout_s=timeout_s)
    order = list(original_order) if original_order is not None else discover_order(
        runner, project / "target" / "test-classes")
    if victim not in order:
        # Checked before the recorder exists, so no empty record is left behind.
        raise DiagnoseInputError(f"victim {victim} is not among the project's tests")

    started = datetime.now(timezone.utc)
    record = Path(record_dir) / f"{started.strftime('%Y%m%dT%H%M%SZ')}-{victim}.jsonl"
    recorder = RecordingRunner(runner, record, {
        "victim": str(victim), "n": n, "project": str(project),
        "java_version": java_version(), "started": started.isoformat(),
    })
    result = run_steps(recorder, order, victim, n, priority)
    return replace(result, source_integrity=compare(before, snapshot(project)),
                   execution_record=str(record))


def _label(runner, step: str) -> None:
    if isinstance(runner, RecordingRunner):
        runner.step = step
