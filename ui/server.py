"""FlakeTrace web UI backend (ADR-009).

Runs `python -m runner diagnose` as a subprocess, one job at a time, and returns only the report
file the CLI writes, after checking it against eval/schema/report.schema.json. Listens on
127.0.0.1 only. Start it with `py ui/server.py` or `ui/start.cmd`.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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
MAX_BODY = 1024 * 1024


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


REPORT_PATH = re.compile(r"/api/reports/([\w-]+)")
JOB_PATH = re.compile(r"/api/jobs/(\w+)")


def health() -> dict:
    tools = {tool: shutil.which(tool) for tool in TOOLS}
    return {"tools": tools, "missing": [tool for tool, path in tools.items() if path is None],
            "python": sys.version.split()[0], "fixture": str(FIXTURE)}


def list_reports() -> list:
    """The schema-valid reports in eval/reports/; other JSON there (baseline results) is skipped."""
    entries = []
    for path in sorted(REPORTS.glob("*.json")):
        report, _ = load_valid_report(path)
        if report is not None:
            victim = report["victim"]
            entries.append({"name": path.stem, "victim": f"{victim['class']}#{victim['method']}",
                            "outcome": report["outcome"]})
    return entries


def get_report(name: str) -> Optional[dict]:
    if name not in {entry["name"] for entry in list_reports()}:
        return None
    return load_valid_report(REPORTS / f"{name}.json")[0]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):  # keep the console for real errors
        pass

    def _send(self, status: int, body) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _foreign_host(self) -> bool:
        """A page on another site (or a DNS-rebinding name) must not drive or read the backend."""
        port = self.server.server_address[1]
        if self.headers.get("Host") in (f"127.0.0.1:{port}", f"localhost:{port}"):
            return False
        self._send(403, {"error": "forbidden", "message": "requests must come from this computer's UI"})
        return True

    def do_GET(self):
        if self._foreign_host():
            return
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            return self._send(200, health())
        if path == "/api/reports":
            return self._send(200, list_reports())
        match = REPORT_PATH.fullmatch(path)
        if match:
            report = get_report(match.group(1))
            return self._send(200, report) if report else self._send(404, {"error": "not_found"})
        match = JOB_PATH.fullmatch(path)
        if match:
            job = self.server.jobs.get(match.group(1))
            if job:
                return self._send(200, job)
            return self._send(404, {"error": "not_found", "message": "no such job; the backend may have restarted"})
        self._send(404, {"error": "not_found"})

    def do_POST(self):
        if self._foreign_host():
            return
        # Browsers send a text/plain POST from any site without asking first; requiring JSON forces that check.
        if self.headers.get("Content-Type", "").split(";")[0].strip() != "application/json":
            return self._send(415, {"error": "unsupported_media_type", "message": "send application/json"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if length < 0:
            return self._send(400, {"error": "bad_request", "message": "invalid Content-Length"})
        if length > MAX_BODY:
            return self._send(413, {"error": "too_large", "message": f"the body is over {MAX_BODY} bytes"})
        path = self.path.split("?", 1)[0]
        try:
            body = json.loads(self.rfile.read(length) or b"null")
        except ValueError:
            return self._send(400, {"error": "bad_request", "message": "the body is not JSON"})
        if path == "/api/diagnose":
            problem = check_diagnose_request(body)
            if problem:
                return self._send(400, {"error": "bad_request", "message": problem})
            try:
                job = self.server.jobs.start(body["project"].strip(), body["victim"].strip(), body.get("n", 20),
                                             body.get("order"))
            except Busy as busy:
                return self._send(409, {"error": "busy", "message": "a diagnosis is already running",
                                        "started": busy.job["started"], "command": busy.job["command"]})
            return self._send(202, {"job_id": job["id"]})
        if path == "/api/validate":
            problem = report_problem(body)
            return self._send(200, {"valid": problem is None, "message": problem})
        self._send(404, {"error": "not_found"})


def make_server(port: int = PORT, jobs: Optional[Jobs] = None) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((HOST, port), Handler)
    server.jobs = jobs or Jobs()
    return server


def main() -> None:
    server = make_server()
    print(f"FlakeTrace UI backend on http://{HOST}:{PORT} (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
