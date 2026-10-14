"""FlakeTrace web UI backend (ADR-009).

Runs `python -m runner diagnose` as a subprocess, one job at a time, and returns only the report
file the CLI writes, after checking it against eval/schema/report.schema.json. Listens on
127.0.0.1 only. Start it with `py ui/server.py` or `ui/start.cmd`.
"""
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

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


class Busy(Exception):
    """A diagnosis is already running; two runs would share the project's target/ folder."""

    def __init__(self, job: dict):
        super().__init__("a diagnosis is already running")
        self.job = job


def kill_tree(process: subprocess.Popen) -> None:
    """Stop the CLI and the JVMs it started; killing only the CLI would leave the JVMs running."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True)
    else:
        os.killpg(process.pid, signal.SIGKILL)
    process.wait()


def check_diagnose_request(body) -> Optional[str]:
    """None if `body` is a usable POST /api/diagnose request, else why not."""
    if not isinstance(body, dict):
        return "the body must be a JSON object"
    for key in ("project", "victim"):
        if not isinstance(body.get(key), str) or not body[key].strip():
            return f"{key} must be a non-empty string"
    n = body.get("n", 20)
    if isinstance(n, bool) or not isinstance(n, int) or not 1 <= n <= MAX_N:
        return f"n must be a whole number from 1 to {MAX_N}"
    order = body.get("order")
    if order is not None and (not isinstance(order, list)
                              or not all(isinstance(test, str) and test.strip() for test in order)):
        return "order must be a list of non-empty Class#method strings"
    return None


class Jobs:
    """Runs one diagnosis at a time and keeps every job's result for polling."""

    def __init__(self, runner: Optional[List[str]] = None, timeout_s: float = JOB_TIMEOUT_S, cwd: Path = REPO):
        self.runner = list(runner or RUNNER)
        self.timeout_s = timeout_s
        self.cwd = cwd
        self._lock = threading.Lock()
        self._jobs = {}
        self._running = None

    def start(self, project: str, victim: str, n: int = 20, order: Optional[List[str]] = None) -> dict:
        with self._lock:
            if self._running is not None:
                raise Busy(dict(self._jobs[self._running]))
            records = Path(tempfile.mkdtemp(prefix="flaketrace-ui-job-"))
            args = ["diagnose", "--project", project, "--victim", victim, "--n", str(n), "--records", str(records)]
            if order:
                order_file = records / "order.txt"
                order_file.write_text("\n".join(order) + "\n", encoding="utf-8")
                args += ["--order", str(order_file)]
            command = self.runner + args
            job = {"id": uuid.uuid4().hex[:12], "state": "running", "started": datetime.now().strftime("%H:%M:%S"),
                   "command": subprocess.list2cmdline(command), "records": str(records)}
            self._jobs[job["id"]] = job
            self._running = job["id"]
        threading.Thread(target=self._run, args=(job["id"], command, records), daemon=True).start()
        return dict(job)

    def get(self, job_id: str) -> Optional[dict]:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def _run(self, job_id: str, command: List[str], records: Path) -> None:
        try:
            result = self._execute(command, records)
        except Exception as error:  # a job must never stay "running" forever
            result = {"state": "failed", "kind": "tool", "message": f"the backend could not run the CLI: {error}",
                      "output_tail": ""}
        with self._lock:
            self._jobs[job_id].update(result)
            self._running = None

    def _execute(self, command: List[str], records: Path) -> dict:
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        process = subprocess.Popen(command, cwd=self.cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   text=True, encoding="utf-8", errors="replace",
                                   start_new_session=os.name != "nt")
        try:
            stdout, stderr = process.communicate(timeout=self.timeout_s)
        except subprocess.TimeoutExpired:
            kill_tree(process)
            stdout, stderr = process.communicate()
            return {"state": "failed", "kind": "timeout",
                    "message": f"timed out after {self.timeout_s:g} s; the run and its JVMs were stopped",
                    "output_tail": tail(stdout + "\n" + stderr)}
        return job_result(process.returncode, stdout, stderr, records)
