"""Evidence bundle: independent recount checker (W23, ADR-013; Interface 8,
docs/contracts/interfaces.md). The runner writes bundles and replays them (`runner/bundle.py`,
`runner/replay.py`; M2); this module is M3's half of the contract -- it reads only a bundle,
never the runner's state, and independently recounts every tally in the report from
record.jsonl alone, then re-decides with eval.outcome.decide() to compare the verdict too. A
wrong count in the runner cannot hide behind a correct-looking summary.

`python -m eval.bundle verify <bundle-folder>`.

Recount coverage is exact for the shapes a real diagnosis or replay produces once a sequence
was checked at all: POLLUTER_FOUND/CANDIDATE/VERIFIED (sequence tally from "verify" lines) and
VICTIM_FAILS_ALONE/VICTIM_FAILS_ALONE_DIFFERENTLY (sequence reuses the alone tally). A
"diagnosis"-kind bundle can also be NOT_REPRODUCED with no reference ever established
(sequence tally from "reproduce" lines only, matching runner.diagnose._steps' own
RunTally(attempts, ...) shape). A "replay"-kind bundle (Interface 8) has no reproduce/shuffle/
search/minimise lines at all -- its reference signature is read from the record header's own
`reference_signature` field instead of re-derived, per the contract, not guessed from the
record the way a diagnosis bundle's is. INCONSISTENT and BUDGET_EXHAUSTED (diagnosis-only) are
not yet covered -- verify_bundle says so explicitly rather than guessing; see
docs/evidence-m3.md."""

import json
import sys
from pathlib import Path
from typing import List, Optional

from eval.baseline import SYNTHETIC_PREFIX, FailureSignature, RunOutcome, RunTally, TestIdentifier, tally
from eval.outcome import (
    DELETION_INCOMPLETE,
    DELETION_INCONCLUSIVE,
    DELETION_VERIFIED,
    DecisionInput,
    decide,
)
from eval.schema_validator import validate_report
from runner.bundle import BundleError, read_bundle


def _read_lines(record_path: Path) -> List[dict]:
    with Path(record_path).open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _header(lines: List[dict]) -> dict:
    if not lines or lines[0].get("type") != "header":
        raise BundleError("record.jsonl has no header line")
    return lines[0]


# --------------------------------------------------------------------------------------------
# verify_bundle -- ADR-013 section 2 / Interface 8: checksums, schema, recount, re-decide
# --------------------------------------------------------------------------------------------

def verify_bundle(bundle_dir) -> List[str]:
    """Reads only the bundle, never the runner's state. Returns a list of problems; empty means
    the bundle checks out (exit 0 at the CLI). Checksums are runner.bundle.read_bundle's own
    job (Interface 8): it raises BundleError on any mismatch or unreadable file, so a tampered
    bundle never even reaches the recount below pretending to be intact."""
    bundle_dir = Path(bundle_dir)
    try:
        bundle = read_bundle(bundle_dir)
    except BundleError as error:
        return [str(error)]

    problems: List[str] = []
    try:
        validate_report(bundle.report)
    except Exception as error:  # jsonschema's own exception type, not imported just to catch it
        problems.append(f"report.json does not validate against the schema: {error}")

    try:
        lines = _read_lines(bundle_dir / "record.jsonl")
        recount = _recount(lines, bundle.manifest, bundle.report)
    except (BundleError, json.JSONDecodeError) as error:
        problems.append(f"recount: {error}")
        return problems

    problems += _compare_recount(bundle.report, recount)
    return problems


def _victim_from(line: dict, victim: str) -> RunOutcome:
    for entry in line["outcomes"]:
        if entry["test"] == victim:
            sig = entry.get("failure_signature")
            return RunOutcome(
                passed=entry["passed"],
                failure_signature=None if sig is None else FailureSignature(
                    sig["exception_type"], sig["stack_trace"], sig.get("message"),
                ),
            )
    raise BundleError(f"a run line has no outcome for the victim {victim!r}")


def _first_real_failure(run_lines: List[dict], victim: str) -> Optional[FailureSignature]:
    """runner.search.reproduce's own rule: the first run where the victim fails for real (not a
    crash/timeout/skip)."""
    for line in run_lines:
        outcome = _victim_from(line, victim)
        if not outcome.passed and not outcome.failure_signature.exception_type.startswith(SYNTHETIC_PREFIX):
            return outcome.failure_signature
    return None


def _signature_from_dict(sig: Optional[dict]) -> Optional[FailureSignature]:
    if sig is None:
        return None
    return FailureSignature(sig["exception_type"], sig["stack_trace"], sig.get("message"))


def _recount(lines: List[dict], manifest: dict, report: dict) -> dict:
    header = _header(lines)
    victim = header["victim"]
    run_lines = [l for l in lines if l.get("type") == "run"]
    alone_lines = [l for l in run_lines if l["step"] == "alone"]
    verify_lines = [l for l in run_lines if l["step"] == "verify"]
    deletion_lines = [l for l in run_lines if l["step"] == "deletion"]

    if manifest.get("kind") == "replay":
        # Interface 8: a replay never re-reproduces -- its reference is the original report's
        # failure_signature, carried into the record header (runner.replay.replay_steps), not
        # re-derived from "reproduce"/"shuffle" lines (there are none).
        reference = _signature_from_dict(header.get("reference_signature"))
        if reference is None:
            raise BundleError("a replay bundle's record header has no reference_signature")
        alone_tally = tally([_victim_from(l, victim) for l in alone_lines], reference)
        if alone_tally.matched >= 1:
            return {"reference": reference, "alone": alone_tally, "sequence": alone_tally, "deletion_checks": []}
        sequence_tally = tally([_victim_from(l, victim) for l in verify_lines], reference)
        deletion_checks = _recount_deletion_checks(
            deletion_lines, victim, alone_tally, reference, report.get("deletion_checks", [])
        )
        return {"reference": reference, "alone": alone_tally, "sequence": sequence_tally,
                "deletion_checks": deletion_checks}

    # kind == "diagnosis": the full search may have run.
    reproduce_lines = [l for l in run_lines if l["step"] in ("reproduce", "shuffle")]
    minimise_lines = [l for l in run_lines if l["step"] == "minimise"]
    reference = _first_real_failure(reproduce_lines, victim)

    if reference is None:
        # runner.verify.repeat_without_reference's own rule: the alone check finds its own
        # reference from among its own runs when nothing reproduced first.
        alone_reference = _first_real_failure(alone_lines, victim)
        alone_outcomes = [_victim_from(l, victim) for l in alone_lines]
        alone_tally = tally(alone_outcomes, alone_reference)
        if alone_reference is not None:
            return {"reference": alone_reference, "alone": alone_tally, "sequence": alone_tally,
                    "deletion_checks": []}
        # No reference anywhere: runner.diagnose._steps' RunTally(attempts, attempts-failures, 0, 0,
        # failures) over the reproduce-phase runs only (every failure there was synthetic, by
        # construction -- a real one would have already been the reference above).
        attempts = len(reproduce_lines)
        failures = sum(1 for l in reproduce_lines if not _victim_from(l, victim).passed)
        sequence_tally = RunTally(attempts, attempts - failures, 0, 0, failures)
        return {"reference": None, "alone": alone_tally, "sequence": sequence_tally, "deletion_checks": []}

    alone_outcomes = [_victim_from(l, victim) for l in alone_lines]
    alone_tally = tally(alone_outcomes, reference)

    if alone_tally.matched >= 1:
        return {"reference": reference, "alone": alone_tally, "sequence": alone_tally, "deletion_checks": []}

    if verify_lines:
        sequence_tally = tally([_victim_from(l, victim) for l in verify_lines], reference)
    elif report.get("unresolved_reason") == "INCONSISTENT_OUTCOMES" and minimise_lines:
        sequence_tally = tally([_victim_from(minimise_lines[0], victim)], reference)
    elif report.get("unresolved_reason") == "BUDGET_EXHAUSTED":
        sequence_tally = tally([_victim_from(l, victim) for l in reproduce_lines], reference)
    else:
        raise BundleError(
            "no 'verify' lines, and the report's unresolved_reason is neither INCONSISTENT_OUTCOMES "
            "nor BUDGET_EXHAUSTED -- this bundle's shape is not one the recount covers yet"
        )

    deletion_checks = _recount_deletion_checks(
        deletion_lines, victim, alone_tally, reference, report.get("deletion_checks", [])
    )
    return {"reference": reference, "alone": alone_tally, "sequence": sequence_tally,
            "deletion_checks": deletion_checks}


def _recount_deletion_checks(deletion_lines, victim, alone_tally, reference, reported_checks) -> List[dict]:
    """One recounted entry per reported deletion check: {removed, round, runs (RunTally or None),
    problem (str or None)} -- ADR-011's alone-check reuse (section 2) and the NOT_RUN case (W24,
    Interface 6 B5: no cost, no lines) both need no matching record lines to recount correctly."""
    from runner.deletion import ALONE_CHECK, NOT_RUN

    recounted = []
    for entry in reported_checks:
        removed = str(TestIdentifier.from_dict(entry["removed"]))
        round_ = entry["round"]
        if entry["source"] == ALONE_CHECK:
            recounted.append({"removed": removed, "round": round_, "runs": alone_tally, "problem": None})
            continue
        matching = [l for l in deletion_lines if l.get("removed") == removed and l.get("round") == round_]
        if entry["status"] == NOT_RUN:
            problem = None if not matching else f"NOT_RUN check for {removed} round {round_} has record lines after all"
            recounted.append({"removed": removed, "round": round_, "runs": None, "problem": problem})
            continue
        if not matching:
            recounted.append({"removed": removed, "round": round_, "runs": None,
                               "problem": f"no deletion-run lines found for {removed} round {round_}"})
            continue
        runs = tally([_victim_from(l, victim) for l in matching], reference)
        recounted.append({"removed": removed, "round": round_, "runs": runs, "problem": None})
    return recounted


def _recounted_deletion_status(deletion_checks: List[dict]) -> Optional[str]:
    """Same priority rule as eval/report.py's own deletion_status computation (Interface 4),
    applied to runner.deletion.label() of the recounted tallies rather than the report's own
    status strings: INCONCLUSIVE ranks above INCOMPLETE; a short run or NOT_RUN still rules out
    VERIFIED even if every label says NEEDED. Kept as a separate copy here (not imported)
    because this one works from recounted record data, not a runner.diagnose.DiagnosisRuns --
    watch the two for drift if Interface 4's rule changes."""
    from runner.deletion import NEEDED, label as deletion_label

    if not deletion_checks:
        return None  # no polluter kept, or a report shape this recount doesn't build checks for
    if any(c["problem"] for c in deletion_checks):
        return DELETION_INCOMPLETE  # a recount problem already flagged elsewhere; don't also claim VERIFIED
    labels = [None if c["runs"] is None else deletion_label(c["runs"], c["runs"].n) for c in deletion_checks]
    if "INCONCLUSIVE" in labels:
        return DELETION_INCONCLUSIVE
    if any(l is None or (c["runs"] is not None and c["runs"].n < 10) for l, c in zip(labels, deletion_checks)):
        return DELETION_INCOMPLETE
    if all(l == NEEDED for l in labels):
        return DELETION_VERIFIED
    return DELETION_INCOMPLETE


def _compare_recount(report: dict, recount: dict) -> List[str]:
    problems = []

    reported_ref = report.get("failure_signature")
    recounted_ref = recount["reference"]
    if (reported_ref is None) != (recounted_ref is None):
        problems.append(
            f"failure_signature: report says {'a signature' if reported_ref else 'null'}, "
            f"recount found {'a signature' if recounted_ref else 'none'}"
        )

    for field, recounted in (("victim_alone", recount["alone"]), ("reproduction", recount["sequence"])):
        reported = report.get(field) or {}
        for key in ("n", "passed", "matched", "other", "infra"):
            if reported.get(key) != getattr(recounted, key):
                problems.append(
                    f"{field}.{key}: report says {reported.get(key)}, recount says {getattr(recounted, key)}"
                )

    reported_checks = report.get("deletion_checks") or []
    for reported, recounted in zip(reported_checks, recount["deletion_checks"]):
        if recounted["problem"]:
            problems.append(f"deletion_checks[{recounted['removed']} round {recounted['round']}]: {recounted['problem']}")
            continue
        reported_runs = reported.get("runs")
        if recounted["runs"] is None:
            if reported_runs is not None:
                problems.append(
                    f"deletion_checks[{recounted['removed']} round {recounted['round']}]: report has runs, "
                    "recount found none (NOT_RUN)"
                )
            continue
        for key in ("n", "passed", "matched", "other", "infra"):
            if (reported_runs or {}).get(key) != getattr(recounted["runs"], key):
                problems.append(
                    f"deletion_checks[{recounted['removed']} round {recounted['round']}].{key}: "
                    f"report says {(reported_runs or {}).get(key)}, recount says {getattr(recounted['runs'], key)}"
                )

    decision_input = DecisionInput(
        source_integrity_passed=report["source_integrity"]["passed"],
        reference_established=recounted_ref is not None,
        infrastructure_failures_anywhere=0,  # not tracked by this recount's scope; see module docstring
        alone=recount["alone"], sequence=recount["sequence"],
        # R1 (a static overlap exists) is M1's static-analysis claim, not something record.jsonl's
        # runtime witness could ever recount -- taken from the report as-is, like resource_edge_exists
        # in eval/report.py itself.
        resource_edge_exists=report.get("shared_resource") is not None,
        deletion_status=_recounted_deletion_status(recount["deletion_checks"]),
    )
    try:
        decision = decide(decision_input)
        if decision.outcome != report["outcome"]:
            problems.append(f"outcome: report says {report['outcome']}, recount+decide() says {decision.outcome}")
    except ValueError:
        pass  # a sequence/alone tally of n=0 (e.g. NOT_RUN-only data) can't be re-decided; checksums/recount above still caught real tamper

    return problems


def _main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] != "verify":
        print("usage: python -m eval.bundle verify <bundle-folder>\n"
              "(bundles are written by `python -m runner diagnose --bundle <folder>`, Interface 8, M2's half)",
              file=sys.stderr)
        return 2
    problems = verify_bundle(argv[1])
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 1
    print(f"OK: {argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
