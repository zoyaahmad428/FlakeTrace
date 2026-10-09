"""W9 command line (ADR-005): py -m runner diagnose --project DIR --victim Class#method.

Runs runner.diagnose.diagnose(), Member 1's resource evidence for a found polluter and
Member 3's assemble_report(), then writes the report next to its execution record.
Exit codes: 0 report written, 2 input wrong, 1 tool failed, 3 no report can be built yet.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from eval.baseline import TestIdentifier
from eval.report import UnhandledStatus, assemble_report
from evidence.extract import DEFAULT_DEPTH, ExtractError, Project, analyse_test, find_edges, report_fields
from runner.diagnose import NO_SINGLE_POLLUTER, NOT_REPRODUCED, POLLUTER_FOUND, diagnose

_NO_REPORT_WHY = {
    NO_SINGLE_POLLUTER: "the original order fails, but no single earlier test makes the victim fail "
                        "(needs multi-polluter minimisation, W10)",
    NOT_REPRODUCED: "the victim never failed with a real failure in n runs of the original order",
}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="py -m runner")
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("diagnose", help="diagnose one failing test and write its report")
    command.add_argument("--project", required=True, help="Maven project folder (contains pom.xml)")
    command.add_argument("--victim", required=True, help="failing test as Class#method")
    command.add_argument("--n", type=int, default=20, help="repeat count (default 20)")
    command.add_argument("--records", default="flaketrace-records",
                         help="folder for the execution record and the report")
    args = parser.parse_args(argv)
    return run_diagnose(Path(args.project), args.victim, args.n, args.records)


def run_diagnose(project: Path, victim_id: str, n: int, records: str) -> int:
    class_name, _, method = victim_id.partition("#")
    if not class_name or not method:
        return _error(f"--victim must be Class#method, got {victim_id!r}", 2)
    if not (project / "pom.xml").is_file():
        return _error(f"no pom.xml in {project}; --project must be a Maven project folder", 2)

    try:
        runs = diagnose(project, TestIdentifier(class_name, method), n=n, record_dir=records)
    except ValueError as error:
        return _error(str(error), 2)
    except subprocess.CalledProcessError as error:
        tool = Path(str(error.cmd[0])).name
        return _error(f"{tool} failed with exit code {error.returncode} on {project}; run it there to see why", 1)
    except RuntimeError as error:
        return _error(str(error), 1)

    try:
        fields = resource_fields(project, runs) if runs.status == POLLUTER_FOUND else None
    except ExtractError as error:
        return _error(f"resource evidence failed: {error}", 1)

    try:
        report = assemble_report(runs, fields)
    except UnhandledStatus:
        why = _NO_REPORT_WHY.get(runs.status, "eval.report cannot build this report yet")
        print(f"No report: {runs.status} - {why}\n  record: {runs.execution_record}")
        return 3

    report_path = Path(runs.execution_record).with_suffix(".report.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(summary(report, report_path))
    return 0


def resource_fields(project: Path, runs) -> dict:
    """Member 1's pair-mode evidence for the found polluter and the victim (contract Output 2)."""
    classes = Project([str(project / "target" / "classes"), str(project / "target" / "test-classes")])
    polluter, victim = str(runs.polluters[0]), str(runs.victim)
    pair = find_edges(polluter, analyse_test(classes, polluter, DEFAULT_DEPTH),
                      victim, analyse_test(classes, victim, DEFAULT_DEPTH))
    return report_fields(pair)


def summary(report: dict, report_path: Path) -> str:
    reason = f" ({report['unresolved_reason']})" if report["unresolved_reason"] else ""
    lines = [f"{report['outcome']}{reason}  {_test(report['victim'])}"]
    if report["polluters"]:
        lines.append("  polluter:   " + ", ".join(_test(p) for p in report["polluters"]))
    if report["shared_resource"]:
        resource = " ".join(str(value) for value in report["shared_resource"].values())
        write, read = report["polluter_write_location"], report["victim_read_location"]
        lines.append(f"  resource:   {resource} (write {_test(write)}@{write['bytecode_offset']}"
                     f" -> read {_test(read)}@{read['bytecode_offset']})")
    reproduced, alone = report["reproduction"], report["victim_alone"]
    lines.append(f"  reproduced: {reproduced['successes']}/{reproduced['n']} (lower bound "
                 f"{reproduced['lower']:.3f})   alone: {alone['successes']}/{alone['n']}")
    lines.append(f"  report:     {report_path}")
    lines.append(f"  record:     {report['execution_record_reference']}")
    return "\n".join(lines)


def _test(location: dict) -> str:
    return f"{location['class']}#{location['method']}"


def _error(message: str, code: int) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code
