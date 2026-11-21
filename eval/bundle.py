"""Evidence bundle: format and independent recount (W23, ADR-013). M3 owns the bundle format and
the recount checker; M2 owns capture (the record header, already carrying everything a manifest
needs -- ADR-012 section 6, W22/W24/W25) and `python -m runner replay` (ADR-013 section 3, not
built yet).

A bundle is a folder with five files (ADR-013 section 1): manifest.json, report.json,
record.jsonl, replay.md, environment.txt. The report is the output, the record is the witness,
and `verify_bundle` is the independent checker: it reads only the bundle, recomputes every tally
in the report from record.jsonl alone (never trusting the runner's own numbers), and feeds the
recount to eval.outcome.decide() to compare the verdict too.

Recount coverage (ADR-013 section 2) is exact for the shapes real diagnoses produce once a
sequence was checked: POLLUTER_FOUND/CANDIDATE/VERIFIED (sequence tally from "verify" lines),
VICTIM_FAILS_ALONE/VICTIM_FAILS_ALONE_DIFFERENTLY (sequence reuses the alone tally), and
NOT_REPRODUCED/INFRASTRUCTURE_FAILURE with no reference ever established (sequence tally from
"reproduce" lines only, matching runner.diagnose._steps' own RunTally(attempts, ...) shape).
INCONSISTENT and BUDGET_EXHAUSTED are not yet covered -- verify_bundle says so explicitly rather
than guessing; see docs/evidence-m3.md."""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from eval.baseline import SYNTHETIC_PREFIX, FailureSignature, RunOutcome, RunTally, TestIdentifier, tally
from eval.outcome import (
    DELETION_INCOMPLETE,
    DELETION_INCONCLUSIVE,
    DELETION_VERIFIED,
    DecisionInput,
    decide,
)
from eval.schema_validator import validate_report

BUNDLE_VERSION = 1
BUNDLE_FILES = ("report.json", "record.jsonl", "replay.md", "environment.txt")

# ADR-012 section 1's own table, quoted (the "contract sentence" ADR-013's manifest asks for).
RESET_ASSUMPTIONS = (
    "Reset between orders: JVM state only (static fields, system properties, loaded classes, "
    "threads). Not reset: files anywhere, the working directory, environment variables, network "
    "and external services, the system clock and timezone. (ADR-012 section 1.)"
)


class BundleError(Exception):
    """A bundle cannot be built or read -- malformed input, not a diagnosis bug."""


# --------------------------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _redact(value, replacements: Dict[str, str]):
    """Recursively replace every occurrence of each key in `replacements` with its value,
    through any string found in a JSON-like structure (ADR-013: "user names and home paths are
    replaced before export"). Keys are tried longest first so a project path inside a longer
    command-line string is not partially replaced."""
    if isinstance(value, str):
        for old in sorted(replacements, key=len, reverse=True):
            if old:
                value = value.replace(old, replacements[old])
        return value
    if isinstance(value, list):
        return [_redact(v, replacements) for v in value]
    if isinstance(value, dict):
        return {k: _redact(v, replacements) for k, v in value.items()}
    return value


def _read_lines(record_path: Path) -> List[dict]:
    with Path(record_path).open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _header(lines: List[dict]) -> dict:
    if not lines or lines[0].get("type") != "header":
        raise BundleError("record.jsonl has no header line")
    return lines[0]


def bundle_folder_name(victim: str, started: str) -> str:
    """<case>-<utc-timestamp>, ADR-013 section 1. `started` is the header's ISO timestamp."""
    ts = datetime.fromisoformat(started).strftime("%Y%m%dT%H%M%SZ")
    return f"{victim}-{ts}"


# --------------------------------------------------------------------------------------------
# create_bundle
# --------------------------------------------------------------------------------------------

def create_bundle(report_path, record_path, out_dir) -> Path:
    """Build an ADR-013 bundle folder under `out_dir` from an existing report.json and
    record.jsonl (as the real CLI already writes them side by side). Every environment/parameter
    field in the manifest is read from the record's own header line (ADR-012 section 6) -- this
    function reshapes and redacts, it never recomputes anything the runner already captured."""
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    lines = _read_lines(Path(record_path))
    header = _header(lines)

    project = header.get("project") or ""
    home = str(Path.home())
    replacements = {}
    # Both slash styles: a path can reach the header/command either way (e.g. a Windows absolute
    # path typed with forward slashes on a bash-like shell), and a plain string replace does not
    # normalise that on its own -- found for real bundling an actual diagnosis (2026-11-20).
    for variant in {project, project.replace("\\", "/"), project.replace("/", "\\")} if project else ():
        replacements[variant] = "<project>"
    for variant in {home, home.replace("\\", "/"), home.replace("/", "\\")} if home else ():
        replacements[variant] = "<home>"

    redacted_header = _redact(header, replacements)
    redacted_lines = [redacted_header] + [_redact(line, replacements) for line in lines[1:]]

    bundle_report = dict(report)
    bundle_report["execution_record_reference"] = "record.jsonl"

    name = bundle_folder_name(header["victim"], header["started"])
    bundle_dir = Path(out_dir) / name
    bundle_dir.mkdir(parents=True, exist_ok=False)

    (bundle_dir / "report.json").write_text(json.dumps(bundle_report, indent=2, sort_keys=False) + "\n",
                                             encoding="utf-8", newline="\n")
    with (bundle_dir / "record.jsonl").open("w", encoding="utf-8", newline="\n") as f:
        for line in redacted_lines:
            f.write(json.dumps(line) + "\n")
    (bundle_dir / "replay.md").write_text(_replay_md(redacted_header), encoding="utf-8", newline="\n")
    (bundle_dir / "environment.txt").write_text(_environment_txt(redacted_header), encoding="utf-8", newline="\n")

    checksums = {name: _sha256(bundle_dir / name) for name in BUNDLE_FILES}
    manifest = _manifest(redacted_header, report, checksums)
    (bundle_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return bundle_dir


def _replay_md(header: dict) -> str:
    command = header.get("command")
    if command:
        cmd_line = " ".join(command)
    else:
        parts = ["python", "-m", "runner", "diagnose", "--project", "<project>",
                 "--victim", header["victim"], "--n", str(header.get("n", 20))]
        budget = header.get("budget") or {}
        if budget.get("limit_invocations") is not None:
            parts += ["--budget-invocations", str(budget["limit_invocations"])]
        if budget.get("limit_seconds") is not None:
            parts += ["--budget-seconds", str(budget["limit_seconds"])]
        if header.get("policy") and header["policy"] != "original":
            parts += ["--policy", header["policy"]]
        if header.get("scope") and header["scope"] != "module":
            parts += ["--scope", header["scope"]]
        cmd_line = " ".join(parts)
    commit = header.get("project_commit") or "the recorded commit"
    return (
        "# Replay\n\n"
        "The exact command that produced this bundle (reconstructed from the record header "
        "when the CLI's own argv was not recorded):\n\n"
        f"```\n{cmd_line}\n```\n\n"
        "Once `python -m runner replay` exists (ADR-013 section 3), the one-command form is:\n\n"
        f"```\npython -m runner replay <this-bundle-folder> --project <checkout of the subject "
        f"at {commit}>\n```\n"
    )


def _environment_txt(header: dict) -> str:
    """ADR-013 asks for the output of `java -version` and `mvn -v`; today's record header
    carries only the summary line each (java_version(), maven_version()), not the full raw
    banner -- capturing that is runner-side work (M2's "capture"), not done here. Documented as
    a known gap rather than silently claiming more than what was recorded."""
    jvm = header.get("jvm") or {}
    lines = [
        header.get("java_version") or "java -version: not recorded",
        header.get("maven_version") or "mvn -v: not recorded",
        f"os: {header.get('os')}",
        f"python: {header.get('python_version')}",
    ]
    for key in sorted(jvm):
        lines.append(f"jvm.{key}: {jvm[key]}")
    return "\n".join(lines) + "\n"


def _manifest(header: dict, report: dict, checksums: Dict[str, str]) -> dict:
    victim_class = report["victim"]["class"]
    repository = "fixture" if victim_class.startswith("odfixture.") else None
    return {
        "bundle_version": BUNDLE_VERSION,
        "tool": {"commit": header.get("tool_commit"), "dirty": header.get("tool_dirty")},
        "subject": {
            "repository": repository,
            "commit": header.get("project_commit"),
            "dirty": header.get("project_dirty"),
            "module_path": header.get("project"),  # already redacted to "<project>"/"<home>" above
        },
        "victim": report["victim"],
        "command": header.get("command"),
        "parameters": {
            "n": header.get("n"), "shuffles": header.get("shuffles"), "seed": header.get("seed_base"),
            "budget": header.get("budget"), "policy": header.get("policy"), "scope": header.get("scope"),
            "lifecycle": header.get("lifecycle"), "workspace": header.get("workspace"),
        },
        "environment": {
            "os": header.get("os"), "java_version": header.get("java_version"),
            "maven_version": header.get("maven_version"), "python_version": header.get("python_version"),
            "jvm": header.get("jvm"), "container_image": header.get("container_image"),
        },
        "reset_assumptions": RESET_ASSUMPTIONS,
        "fresh_run": {"value": True, "date": header.get("started")},
        "files": checksums,
    }


# --------------------------------------------------------------------------------------------
# verify_bundle -- ADR-013 section 2: checksums, schema, recount, re-decide
# --------------------------------------------------------------------------------------------

def verify_bundle(bundle_dir) -> List[str]:
    """Reads only the bundle, never the runner's state. Returns a list of problems; empty means
    the bundle checks out (exit 0 at the CLI)."""
    bundle_dir = Path(bundle_dir)
    problems: List[str] = []

    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.exists():
        return [f"missing manifest.json in {bundle_dir}"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    for name, expected in manifest.get("files", {}).items():
        path = bundle_dir / name
        if not path.exists():
            problems.append(f"checksum: {name} is listed in manifest.json but missing from the bundle")
            continue
        actual = _sha256(path)
        if actual != expected:
            problems.append(f"checksum mismatch for {name}: manifest says {expected}, file is {actual}")

    report_path = bundle_dir / "report.json"
    if not report_path.exists():
        problems.append("report.json is missing")
        return problems
    report = json.loads(report_path.read_text(encoding="utf-8"))
    try:
        validate_report(report)
    except Exception as error:  # jsonschema's own exception type, not imported just to catch it
        problems.append(f"report.json does not validate against the schema: {error}")

    record_path = bundle_dir / "record.jsonl"
    if not record_path.exists():
        problems.append("record.jsonl is missing")
        return problems
    try:
        lines = _read_lines(record_path)
    except json.JSONDecodeError as error:
        # A tamper that breaks the checksum above can also break JSON parsing outright; the
        # checksum mismatch already failed this bundle, so report that rather than crashing.
        problems.append(f"record.jsonl is not valid JSON Lines: {error}")
        return problems

    try:
        recount = _recount(lines, report)
    except BundleError as error:
        problems.append(f"recount: {error}")
        return problems

    problems += _compare_recount(report, recount)
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


def _recount(lines: List[dict], report: dict) -> dict:
    header = _header(lines)
    victim = header["victim"]
    run_lines = [l for l in lines if l.get("type") == "run"]

    reproduce_lines = [l for l in run_lines if l["step"] in ("reproduce", "shuffle")]
    alone_lines = [l for l in run_lines if l["step"] == "alone"]
    verify_lines = [l for l in run_lines if l["step"] == "verify"]
    minimise_lines = [l for l in run_lines if l["step"] == "minimise"]
    deletion_lines = [l for l in run_lines if l["step"] == "deletion"]

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
    if len(argv) < 2 or argv[0] not in ("create", "verify"):
        print("usage: python -m eval.bundle create <report.json> <record.jsonl> [--out DIR]\n"
              "       python -m eval.bundle verify <bundle-folder>", file=sys.stderr)
        return 2
    if argv[0] == "verify":
        problems = verify_bundle(argv[1])
        if problems:
            for p in problems:
                print(p, file=sys.stderr)
            return 1
        print(f"OK: {argv[1]}")
        return 0
    # create
    if len(argv) < 3:
        print("usage: python -m eval.bundle create <report.json> <record.jsonl> [--out DIR]", file=sys.stderr)
        return 2
    out = "eval/bundles"
    if "--out" in argv:
        out = argv[argv.index("--out") + 1]
    bundle_dir = create_bundle(argv[1], argv[2], out)
    print(f"bundle: {bundle_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
