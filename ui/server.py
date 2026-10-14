"""FlakeTrace web UI backend (ADR-009).

Runs `python -m runner diagnose` as a subprocess, one job at a time, and returns only the report
file the CLI writes, after checking it against eval/schema/report.schema.json. Listens on
127.0.0.1 only. Start it with `py ui/server.py` or `ui/start.cmd`.
"""
import json
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from eval.schema_validator import validate_report  # noqa: E402  (needs REPO on sys.path)

HOST = "127.0.0.1"
PORT = 8765
REPORTS = REPO / "eval" / "reports"
FIXTURE = REPO / "fixtures" / "od-fixture"
TOOLS = ("java", "javac", "javap", "mvn")
RUNNER = [sys.executable, "-m", "runner"]
JOB_TIMEOUT_S = 600
TAIL_LINES = 20
MAX_N = 1000


def tail(text: str, lines: int = TAIL_LINES) -> str:
    return "\n".join(text.strip().splitlines()[-lines:])


def report_problem(report) -> Optional[str]:
    """None if `report` is a valid FlakeTrace report, else why not."""
    try:
        validate_report(report)
    except Exception as error:  # jsonschema's ValidationError
        return f"not a valid FlakeTrace report: {getattr(error, 'message', error)}"
    return None


def load_valid_report(path: Path):
    """(report, None) for a schema-valid report file, else (None, why)."""
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return None, f"cannot read {path.name}: {error}"
    why = report_problem(report)
    return (None, why) if why else (report, None)


def _cli_error(stderr: str, returncode: int) -> str:
    lines = [line for line in stderr.strip().splitlines() if line.startswith("error: ")]
    return lines[-1][len("error: "):] if lines else f"the CLI exited with code {returncode}"


def job_result(returncode: int, stdout: str, stderr: str, records: Path) -> dict:
    """The job state for one finished CLI run (exit codes from runner/cli.py). Data comes only
    from the report file the CLI wrote, never from its printed summary."""
    output = tail(stdout + "\n" + stderr)
    if returncode == 0:
        reports = sorted(records.glob("*.report.json"))
        if not reports:
            return {"state": "failed", "kind": "invalid_report",
                    "message": "the CLI exited 0 but wrote no report", "output_tail": output}
        report, why = load_valid_report(reports[-1])
        if report is None:
            return {"state": "failed", "kind": "invalid_report", "message": why, "output_tail": output}
        return {"state": "done", "report": report, "report_path": str(reports[-1])}
    if returncode == 3:
        lines = [line.strip() for line in stdout.splitlines()
                 if line.strip().startswith(("No report:", "record:"))]
        return {"state": "failed", "kind": "no_report", "message": "; ".join(lines) or "No report",
                "output_tail": output}
    kind = "input" if returncode == 2 else "tool"
    return {"state": "failed", "kind": kind, "message": _cli_error(stderr, returncode), "output_tail": output}
