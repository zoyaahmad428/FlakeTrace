"""Replay (W23, ADR-013 section 3, Interface 8 R1-R7): re-check a bundle's evidence on another checkout —
the victim alone, the deletion checks and the kept sequence, with the recorded n and lifecycle — and compare
the verdict. It never searches: a new search is a new diagnosis."""

import json
import re
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from eval.baseline import FailureSignature, TestIdentifier
from runner.budget import Budget, BudgetedRunner
from runner.bundle import BundleError, manifest as bundle_manifest, read_bundle, write_bundle
from runner.deletion import check_deletions
from runner.diagnose import (POLLUTER_FOUND, VICTIM_FAILS_ALONE, DiagnosisRuns, _label, prepare_runner,
                             record_header)
from runner.integrity import compare as compare_files, integrity_of, snapshot
from runner.recording import RecordingRunner
from runner.verify import repeat
from runner.workspace import workspace

REFUSAL = "nothing to replay: no polluter was blamed"
SAME, DIFFERENT = "same", "DIFFERENT"


def replayable(report: dict) -> Optional[str]:
    """R1: only a report that blames polluters (VERIFIED or CANDIDATE) is replayed."""
    return None if report.get("outcome") in ("VERIFIED", "CANDIDATE") and report.get("polluters") else REFUSAL


def report_reference(report: dict) -> FailureSignature:
    """R2: the reference is the original report's failure signature (a replay never re-reproduces)."""
    signature = report["failure_signature"]
    return FailureSignature(signature["exception_type"], signature["stack_trace"], signature.get("message"))


def replay_steps(runner, polluters: List[TestIdentifier], victim: TestIdentifier, reference: FailureSignature,
                 n: int, original_order: List[TestIdentifier]) -> DiagnosisRuns:
    """R2 on any OrderRunner, in diagnose's order: alone, deletion checks (which may drop a test), then the
    kept sequence. No budget: the recorded n in full."""
    ledger = BudgetedRunner(runner, Budget(), n, victim)
    _label(ledger, "alone")
    alone = repeat(ledger, [victim], victim, reference, n)
    explore = dict(order_given=True)
    if alone.matched >= 1:
        return DiagnosisRuns(VICTIM_FAILS_ALONE, victim, list(original_order), reference, [], [victim], alone, alone,
                             0, budget=ledger.account(len(original_order) - 1), **explore)
    _label(ledger, "deletion")
    checks, kept = check_deletions(ledger, list(polluters), victim, reference, n, alone)
    sequence = kept + [victim]
    _label(ledger, "verify")
    verified = repeat(ledger, sequence, victim, reference, n)
    return DiagnosisRuns(POLLUTER_FOUND, victim, list(original_order), reference, kept, sequence, verified, alone, 0,
                         deletion_checks=checks, budget=ledger.account(len(original_order) - 1), **explore)


def _verdict(report: dict) -> str:
    reasons = report.get("unresolved_reason") or ", ".join(report.get("candidate_reasons") or [])
    return report["outcome"] + (f" ({reasons})" if reasons else "")


def _same_os(old, new) -> bool:
    """Python 3.11 names Windows 11 "Windows-10" with the same build number, so only the build is compared
    (M1's W23 reproduction, #159)."""
    windows = lambda text: re.sub(r"^Windows-1[01]-", "Windows-", text) if isinstance(text, str) else text
    return windows(old) == windows(new)


def _row(label: str, old, new, judged: bool = True, same: Optional[bool] = None) -> str:
    mark = (SAME if (old == new if same is None else same) else DIFFERENT) if judged else ""
    return f"{label:<13}{old}  ->  {new}" + (f"      {mark}" if mark else "")


def compare(old_report: dict, new_report: dict, old_manifest: dict, new_manifest: dict) -> Tuple[List[str], bool]:
    """R4/R5: the verdict is the same only if the outcome, its reasons and the polluters are all equal; the
    counts and the environment are shown, and differences there are noted, not judged."""
    polluters = lambda report: [f"{p['class']}#{p['method']}" for p in report.get("polluters") or []]
    same = (_verdict(old_report) == _verdict(new_report) and polluters(old_report) == polluters(new_report))
    lines = [f"{'verdict:':<13}{_verdict(old_report)}  ->  {_verdict(new_report)}      {SAME if same else DIFFERENT}",
             _row("polluters:", ", ".join(polluters(old_report)) or "-", ", ".join(polluters(new_report)) or "-")]
    count = lambda tally, key: f"{tally[key]}/{tally['n']}" if tally else "-"
    lines.append(_row("sequence:", count(old_report.get("reproduction"), "matched") + " matched",
                      count(new_report.get("reproduction"), "matched") + " matched", judged=False))
    lines.append(_row("alone:", count(old_report.get("victim_alone"), "passed") + " passed",
                      count(new_report.get("victim_alone"), "passed") + " passed", judged=False))
    last = lambda report: {c["removed"]["class"] + "#" + c["removed"]["method"]: c["status"]
                           for c in report.get("deletion_checks") or []}
    old_checks, new_checks = last(old_report), last(new_report)
    for test in sorted(set(old_checks) | set(new_checks)):
        lines.append(_row("deletion:", f"{test} {old_checks.get(test, '-')}", f"{test} {new_checks.get(test, '-')}",
                          judged=False))
    budget = old_report.get("budget") or {}
    if budget.get("exhausted"):
        lines.append(f"{'budget:':<13}the original ran out in {budget.get('exhausted_phase')}; the replay has no limit")
    get = lambda manifest, *keys: _dig(manifest, keys)
    for label, keys in (("subject:", ("subject", "commit")), ("tool:", ("tool", "commit")),
                        ("JDK:", ("environment", "jdk")), ("OS:", ("environment", "os")),
                        ("Maven:", ("environment", "maven")), ("timezone:", ("environment", "timezone")),
                        ("locale:", ("environment", "locale")), ("encoding:", ("environment", "encoding")),
                        ("lifecycle:", ("parameters", "lifecycle"))):
        old, new = get(old_manifest, *keys), get(new_manifest, *keys)
        lines.append(_row(label, old, new, same=_same_os(old, new) if label == "OS:" else None))
    return lines, same


def _dig(data: dict, keys) -> Optional[str]:
    for key in keys:
        data = (data or {}).get(key)
    return data


def replay(bundle_folder, project, out_folder, records, timeout_s: float, workspace_mode: str,
           command: Optional[List[str]]) -> Tuple[int, List[str], Optional[Path]]:
    """R1-R7. Returns (exit code, the lines to print, the new bundle or None). Exit 0 same verdict, 4 the verdict
    differs, 2 the input cannot be replayed. Tool failures (Maven, the JVM) raise, as in diagnose."""
    from runner.cli import _environment_text, _subject, resource_fields  # the CLI's helpers, imported late
    from eval.report import assemble_report
    try:
        original = read_bundle(bundle_folder)
    except BundleError as error:
        return 2, [str(error)], None
    refusal = replayable(original.report)
    if refusal:
        return 2, [refusal], None
    report, parameters = original.report, original.manifest.get("parameters") or {}
    # R2: the recorded n and lifecycle come from the record, which the checksums protect; manifest.json is not.
    n, lifecycle = original.header.get("n"), original.header.get("lifecycle") or "class-grouped"
    if (parameters.get("n"), parameters.get("lifecycle") or "class-grouped") != (n, lifecycle):
        return 2, [f"manifest.json and the record disagree on n or lifecycle ({parameters.get('n')}, "
                   f"{parameters.get('lifecycle')} vs {n}, {lifecycle}); the bundle was changed"], None
    bundle_root = Path(bundle_folder).resolve()
    for chosen in (Path(out_folder).resolve(), Path(records).resolve()):
        if chosen == bundle_root or bundle_root in chosen.parents:
            return 2, [f"{chosen} is inside the original bundle; replay never writes there (Interface 8 R7)"], None
    victim = TestIdentifier.from_dict(report["victim"])
    polluters = [TestIdentifier.from_dict(p) for p in report["polluters"]]
    order = [TestIdentifier.from_dict(t) for t in report.get("original_failing_order") or []] or polluters + [victim]
    project = Path(project)
    with workspace(project, workspace_mode) as work:
        work = Path(work).resolve()
        before, before_source = snapshot(work), snapshot(project) if work != project.resolve() else None
        runner, discovered, _ = prepare_runner(work, timeout_s, lifecycle)
        missing = [str(t) for t in polluters + [victim] if t not in set(discovered)]
        if missing:
            return 2, [f"not among the checkout's tests: {', '.join(missing)}; is --project the right checkout?"], None
        started = datetime.now(timezone.utc)
        Path(records).mkdir(parents=True, exist_ok=True)
        record = Path(records) / f"{started.strftime('%Y%m%dT%H%M%SZ')}-{victim}.jsonl"
        header = record_header(runner, victim, n, project, started, order_given=True, workspace=workspace_mode,
                               command=command, reference_signature=report["failure_signature"],
                               replay_of=original.manifest["files"]["report.json"])
        runs = replay_steps(RecordingRunner(runner, record, header), polluters, victim, report_reference(report), n,
                            order)
        integrity = integrity_of(compare_files(before, snapshot(work)),
                                 compare_files(before_source, snapshot(project)) if before_source is not None else None)
        runs = replace(runs, source_integrity=integrity, execution_record=str(record))
        fields = resource_fields(work, runs) if runs.status == POLLUTER_FOUND else None
    new_report = assemble_report(runs, fields)
    record.with_suffix(".report.json").write_text(json.dumps(new_report, indent=2) + "\n", encoding="utf-8")
    # One comparison, printed and written: the new manifest is built from the same header write_bundle uses,
    # so every row (the Maven version too) is what the written bundle says.
    preview = bundle_manifest(header, kind="replay", repository=None, module_path=None,
                              replay_of=original.manifest["files"]["report.json"], files={})
    lines, same = compare(report, new_report, original.manifest, preview)
    folder = write_bundle(out_folder, new_report, record, environment_text=_environment_text(), kind="replay",
                          replay_of=original.manifest["files"]["report.json"],
                          paths={str(work): "<project>", str(project.resolve()): "<project>",
                                 str(Path(records).resolve()): "<records>"},
                          extra_md="\n## Comparison with the original bundle\n\n" + "\n".join(lines) + "\n",
                          **_subject(project))
    return (0 if same else 4), lines, folder
