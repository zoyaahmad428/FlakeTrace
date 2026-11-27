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
import urllib.parse
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import List, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from eval.bundle import verify_bundle  # noqa: E402  (needs REPO on sys.path)
from eval.schema_validator import validate_report  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765
REPORTS = REPO / "eval" / "reports"
BUNDLES = REPO / "eval" / "bundles"
FIXTURE = REPO / "fixtures" / "od-fixture"
TOOLS = ("java", "javac", "javap", "mvn")
RUNNER = [sys.executable, "-m", "runner"]


def job_timeout(environ) -> float:
    """Seconds one diagnosis may take. 30 min by default: a package-scope pair-mode run of FJ-03's size took 8 min of
    runs plus ~3 min of Maven build (evidence-m2); FLAKETRACE_UI_JOB_TIMEOUT_S overrides it."""
    return float(environ.get("FLAKETRACE_UI_JOB_TIMEOUT_S", 1800))


JOB_TIMEOUT_S = job_timeout(os.environ)
# The demo's run options (design 2026-11-27): request field -> (CLI flag, check). Defaults are the CLI's, so an
# absent field adds no flag; the CLI stays the authority and its exit 2 is still reported as an input error.
SEARCHES, SCOPES, POLICIES = ("order", "pairs"), ("module", "package"), ("original", "ranked", "random")
_whole = lambda low: lambda v: not isinstance(v, bool) and isinstance(v, int) and v >= low
OPTIONS = {
    "search": ("--search", lambda v: v in SEARCHES, f"search must be one of {', '.join(SEARCHES)}"),
    "scope": ("--scope", lambda v: v in SCOPES, f"scope must be one of {', '.join(SCOPES)}"),
    "policy": ("--policy", lambda v: v in POLICIES, f"policy must be one of {', '.join(POLICIES)}"),
    "seed": ("--seed", _whole(0), "seed must be a whole number from 0"),
    "shuffles": ("--shuffles", _whole(0), "shuffles must be a whole number from 0"),
    "budget_invocations": ("--budget-invocations", _whole(1), "budget_invocations must be a whole number from 1"),
    "budget_seconds": ("--budget-seconds",
                       lambda v: not isinstance(v, bool) and isinstance(v, (int, float)) and v > 0,
                       "budget_seconds must be a number above 0"),
}
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
        done = {"state": "done", "report": report, "report_path": str(reports[-1])}
        bundles = sorted(path for path in (records / "bundles").glob("*") if path.is_dir())
        if bundles:
            done["bundle"] = {"path": str(bundles[-1])}
        return done
    if returncode == 3:
        lines = [line.strip() for line in stdout.splitlines()
                 if line.strip().startswith(("No report:", "record:"))]
        return {"state": "failed", "kind": "no_report", "message": "; ".join(lines) or "No report",
                "output_tail": output}
    kind = "input" if returncode == 2 else "tool"
    return {"state": "failed", "kind": kind, "message": _cli_error(stderr, returncode), "output_tail": output}


class Busy(Exception):
    """A diagnosis is already running. One at a time keeps the machine's JVM load and the job list simple
    (with --workspace in-place, two runs would also share the project's target/ folder)."""

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
    for name, (_, ok, message) in OPTIONS.items():
        if name in body and not ok(body[name]):
            return message
    if "bundle" in body and not isinstance(body["bundle"], bool):
        return "bundle must be true or false"
    # The CLI's own refusals, word for word (runner/cli.py), so the UI never starts what the CLI would refuse.
    if order and body.get("search") == "pairs":
        return "--search pairs cannot be combined with --order: pair mode takes the victim only"
    if order and body.get("scope") == "package":
        return "--scope package cannot be combined with --order: the order file already fixes the tests"
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

    def start(self, project: str, victim: str, n: int = 20, order: Optional[List[str]] = None,
              options: Optional[dict] = None) -> dict:
        with self._lock:
            if self._running is not None:
                raise Busy(dict(self._jobs[self._running]))
            records = Path(tempfile.mkdtemp(prefix="flaketrace-ui-job-"))
            # The CLI's temporary project copy goes inside the job folder, so a timed-out job's copy can be
            # removed even though the killed CLI never ran its own clean-up (W22, ADR-012 section 4).
            args = ["diagnose", "--project", project, "--victim", victim, "--n", str(n), "--records", str(records),
                    "--copy-parent", str(records / "work")]
            if order:
                order_file = records / "order.txt"
                order_file.write_text("\n".join(order) + "\n", encoding="utf-8")
                args += ["--order", str(order_file)]
            options = options or {}
            for name, (flag, _, _) in OPTIONS.items():
                if options.get(name) is not None:
                    args += [flag, str(options[name])]
            if options.get("bundle"):
                # Into the job's own folder: the UI never writes into the repository (design, builder check 1).
                args += ["--bundle", str(records / "bundles")]
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
            shutil.rmtree(records / "work", ignore_errors=True)
            return {"state": "failed", "kind": "timeout",
                    "message": f"timed out after {self.timeout_s:g} s; the run and its JVMs were stopped",
                    "output_tail": tail(stdout + "\n" + stderr)}
        return job_result(process.returncode, stdout, stderr, records)


REPORT_PATH = re.compile(r"/api/reports/([\w-]+)")
BUNDLE_PATH = re.compile(r"/api/bundles/([^/]+)")
JOB_PATH = re.compile(r"/api/jobs/(\w+)")


def health() -> dict:
    tools = {tool: shutil.which(tool) for tool in TOOLS}
    return {"tools": tools, "missing": [tool for tool, path in tools.items() if path is None],
            "python": sys.version.split()[0], "fixture": str(FIXTURE), "job_timeout_s": JOB_TIMEOUT_S}


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


def list_bundles() -> list:
    """Every committed bundle in eval/bundles/: its parameters (manifest.json), its mode (the record header's
    search_mode; a bundle from before W35 has none: order) and its report. Not verified here: verify takes about 3 s
    per bundle, so it runs when one is opened (design goal 4)."""
    entries = []
    for folder in sorted(path.parent for path in BUNDLES.glob("*/manifest.json")):
        manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        with open(folder / "record.jsonl", encoding="utf-8") as record:
            header = json.loads(record.readline())
        parameters = manifest.get("parameters") or {}
        entries.append({"name": folder.name, "run_date": manifest.get("run_date"),
                        "search": header.get("search_mode") or "order", "scope": parameters.get("scope"),
                        "policy": parameters.get("policy"), "seed": parameters.get("seed"),
                        "report": json.loads((folder / "report.json").read_text(encoding="utf-8"))})
    return entries


def check_bundle(path: str) -> dict:
    """eval.bundle's own verify on any folder, read-only: {"ok", "problem"} with the first problem's first line."""
    folder = Path(path) if isinstance(path, str) and path.strip() else None
    if folder is None or not folder.is_dir():
        return {"ok": False, "problem": f"no such folder: {path!r}"}
    problems = verify_bundle(folder)
    return {"ok": not problems, "problem": problems[0].splitlines()[0] if problems else None}


def open_bundle(name: str) -> Optional[dict]:
    """One committed bundle, by its exact folder name only (nothing outside eval/bundles/), verified now."""
    entry = next((entry for entry in list_bundles() if entry["name"] == name), None)
    if entry is None:
        return None
    return {"name": name, "run_date": entry["run_date"], "report": entry["report"],
            "verify": check_bundle(str(BUNDLES / name))}


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
        if path == "/api/bundles":
            return self._send(200, list_bundles())
        match = BUNDLE_PATH.fullmatch(path)
        if match:
            opened = open_bundle(urllib.parse.unquote(match.group(1)))
            return self._send(200, opened) if opened else self._send(404, {"error": "not_found"})
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
                                             body.get("order"), {name: body[name] for name in [*OPTIONS, "bundle"]
                                                                 if name in body})
            except Busy as busy:
                return self._send(409, {"error": "busy", "message": "a diagnosis is already running",
                                        "started": busy.job["started"], "command": busy.job["command"]})
            return self._send(202, {"job_id": job["id"]})
        if path == "/api/check-bundle":
            if not isinstance(body, dict) or not isinstance(body.get("path"), str):
                return self._send(400, {"error": "bad_request", "message": "path must be a string"})
            return self._send(200, check_bundle(body["path"]))
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
