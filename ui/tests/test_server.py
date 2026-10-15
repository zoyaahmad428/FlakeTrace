import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

from ui.server import Busy, Jobs, check_diagnose_request, job_result, make_server

REPO = Path(__file__).resolve().parents[2]
F1_REPORT = REPO / "eval" / "reports" / "f1.json"
FIXTURE = REPO / "fixtures" / "od-fixture"


class TestJobResult(unittest.TestCase):
    """Exit codes from runner/cli.py: 0 report, 1 tool failed, 2 bad input, 3 no report."""

    def setUp(self):
        self.records = Path(tempfile.mkdtemp(prefix="flaketrace-ui-test-"))
        self.addCleanup(shutil.rmtree, self.records, ignore_errors=True)

    def test_exit_0_with_a_valid_report_is_done(self):
        shutil.copy(F1_REPORT, self.records / "run.report.json")
        result = job_result(0, "summary\n", "", self.records)
        self.assertEqual(result["state"], "done")
        self.assertEqual(result["report"]["outcome"], "VERIFIED")
        self.assertEqual(result["report_path"], str(self.records / "run.report.json"))

    def test_exit_0_without_a_report_file_is_failed(self):
        result = job_result(0, "", "", self.records)
        self.assertEqual((result["state"], result["kind"]), ("failed", "invalid_report"))

    def test_exit_0_with_an_invalid_report_is_failed(self):
        (self.records / "run.report.json").write_text('{"outcome": "VERIFIED"}', encoding="utf-8")
        result = job_result(0, "", "", self.records)
        self.assertEqual((result["state"], result["kind"]), ("failed", "invalid_report"))
        self.assertIn("not a valid FlakeTrace report", result["message"])

    def test_exit_1_is_a_tool_failure_with_the_cli_message(self):
        result = job_result(1, "", "error: mvn failed with exit code 1 on X; run it there to see why\n", self.records)
        self.assertEqual((result["state"], result["kind"]), ("failed", "tool"))
        self.assertEqual(result["message"], "mvn failed with exit code 1 on X; run it there to see why")

    def test_exit_2_is_an_input_error(self):
        result = job_result(2, "", "error: no pom.xml in X; --project must be a Maven project folder\n", self.records)
        self.assertEqual((result["state"], result["kind"]), ("failed", "input"))
        self.assertEqual(result["message"], "no pom.xml in X; --project must be a Maven project folder")

    def test_exit_3_names_the_status_and_the_record(self):
        out = "No report: NO_SINGLE_POLLUTER - ddmin found no polluter set\n  record: R.json\n"
        result = job_result(3, out, "", self.records)
        self.assertEqual((result["state"], result["kind"]), ("failed", "no_report"))
        self.assertEqual(result["message"], "No report: NO_SINGLE_POLLUTER - ddmin found no polluter set; record: R.json")

    def test_a_crash_without_an_error_line_keeps_the_output(self):
        result = job_result(1, "", "Traceback (most recent call last):\nKeyError: 'x'\n", self.records)
        self.assertEqual(result["message"], "the CLI exited with code 1")
        self.assertIn("KeyError", result["output_tail"])


FAKE_CLI = Path(__file__).resolve().parent / "fake_cli.py"


def fake_jobs(mode, timeout_s=60):
    return Jobs(runner=[sys.executable, str(FAKE_CLI), mode], timeout_s=timeout_s)


def wait(jobs, job_id, limit_s=60):
    deadline = time.monotonic() + limit_s
    while time.monotonic() < deadline:
        job = jobs.get(job_id)
        if job["state"] != "running":
            return job
        time.sleep(0.1)
    raise AssertionError(f"job {job_id} still running after {limit_s} s")


def pid_alive(pid):
    if os.name == "nt":
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True).stdout
        return str(pid) in out
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


class TestCheckRequest(unittest.TestCase):
    def test_a_minimal_request_is_accepted(self):
        self.assertIsNone(check_diagnose_request({"project": "p", "victim": "a.B#c"}))
        self.assertIsNone(check_diagnose_request({"project": "p", "victim": "a.B#c", "n": 20, "order": ["a.B#c"]}))

    def test_bad_requests_are_rejected(self):
        for body in (None, [], {"victim": "a.B#c"}, {"project": " ", "victim": "a.B#c"}, {"project": "p"},
                     {"project": "p", "victim": "a.B#c", "n": 0}, {"project": "p", "victim": "a.B#c", "n": True},
                     {"project": "p", "victim": "a.B#c", "n": "20"}, {"project": "p", "victim": "a.B#c", "order": "a.B#c"},
                     {"project": "p", "victim": "a.B#c", "order": ["a.B#c", ""]}):
            with self.subTest(body=body):
                self.assertIsNotNone(check_diagnose_request(body))


class TestJobs(unittest.TestCase):
    def test_a_report_run_ends_done(self):
        jobs = fake_jobs("report")
        job = jobs.start("proj", "a.B#c")
        self.assertEqual(job["state"], "running")
        self.assertIn("diagnose", job["command"])
        done = wait(jobs, job["id"])
        self.assertEqual(done["state"], "done")
        self.assertEqual(done["report"]["outcome"], "VERIFIED")

    def test_arguments_with_spaces_reach_the_cli_intact(self):
        jobs = fake_jobs("args")
        project = str(Path(tempfile.gettempdir()) / "a folder" / "with spaces")
        done = wait(jobs, jobs.start(project, "a.B#c", 7, ["x.Y#z", "a.B#c"])["id"])
        args = json.loads((Path(done["report_path"]).parent / "args.json").read_text(encoding="utf-8"))
        self.assertEqual(args[args.index("--project") + 1], project)
        self.assertEqual(args[args.index("--n") + 1], "7")
        order_file = Path(args[args.index("--order") + 1])
        self.assertEqual(order_file.read_text(encoding="utf-8").split(), ["x.Y#z", "a.B#c"])

    def test_non_ascii_cli_output_is_kept(self):
        jobs = fake_jobs("unicode-error")
        done = wait(jobs, jobs.start("proj", "a.B#c")["id"])
        self.assertEqual((done["kind"], done["message"]), ("tool", "café ✓ failed"))

    def test_a_second_job_while_one_runs_is_busy(self):
        jobs = fake_jobs("sleep", timeout_s=3)
        first = jobs.start("proj", "a.B#c")
        with self.assertRaises(Busy) as caught:
            jobs.start("proj", "a.B#c")
        self.assertEqual(caught.exception.job["id"], first["id"])
        wait(jobs, first["id"])

    def test_a_job_over_the_limit_is_stopped_and_the_next_may_start(self):
        jobs = fake_jobs("sleep", timeout_s=1)
        done = wait(jobs, jobs.start("proj", "a.B#c")["id"])
        self.assertEqual((done["state"], done["kind"]), ("failed", "timeout"))
        self.assertIn("timed out after 1 s", done["message"])
        wait(jobs, jobs.start("proj", "a.B#c")["id"])

    def test_timeout_also_stops_child_processes(self):
        jobs = fake_jobs("spawn-sleep", timeout_s=3)
        job = jobs.start("proj", "a.B#c")
        wait(jobs, job["id"])
        child = int((Path(job["records"]) / "child.pid").read_text(encoding="utf-8"))
        deadline = time.monotonic() + 5
        while pid_alive(child) and time.monotonic() < deadline:
            time.sleep(0.2)
        self.assertFalse(pid_alive(child), f"child process {child} still running after the timeout")

    def test_an_unknown_job_is_none(self):
        self.assertIsNone(fake_jobs("report").get("nope"))


@contextmanager
def serving(jobs):
    server = make_server(0, jobs)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield server, f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


def call(base, method, path, body=None, raw=None):
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode("utf-8"))
    request = urllib.request.Request(base + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


class TestHttp(unittest.TestCase):
    def test_binds_localhost_only(self):
        with serving(fake_jobs("report")) as (server, _):
            self.assertEqual(server.server_address[0], "127.0.0.1")

    def test_health_names_missing_tools(self):
        with serving(fake_jobs("report")) as (_, base), \
                mock.patch("shutil.which", lambda tool: None if tool == "mvn" else f"/bin/{tool}"):
            status, body = call(base, "GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["missing"], ["mvn"])
        self.assertEqual(body["fixture"], str(FIXTURE))

    def test_reports_lists_the_seven_committed_reports(self):
        with serving(fake_jobs("report")) as (_, base):
            status, body = call(base, "GET", "/api/reports")
        self.assertEqual(status, 200)
        self.assertEqual([entry["name"] for entry in body], ["f1", "f2", "f3", "f4", "n1", "n2", "n3"])
        self.assertEqual(body[0]["victim"], "odfixture.ConfigVictimTest#expectsDefaultMode")

    def test_one_report_and_names_outside_the_list(self):
        with serving(fake_jobs("report")) as (_, base):
            status, body = call(base, "GET", "/api/reports/n1")
            self.assertEqual((status, body["unresolved_reason"]), (200, "VICTIM_FAILS_ALONE"))
            for name in ("baseline_results", "README", "nope", "..%2Fschema%2Freport.schema"):
                with self.subTest(name=name):
                    self.assertEqual(call(base, "GET", f"/api/reports/{name}")[0], 404)

    def test_diagnose_then_poll(self):
        with serving(fake_jobs("report")) as (_, base):
            status, body = call(base, "POST", "/api/diagnose", {"project": "p", "victim": "a.B#c"})
            self.assertEqual(status, 202)
            deadline = time.monotonic() + 30
            while True:
                status, job = call(base, "GET", f"/api/jobs/{body['job_id']}")
                if job["state"] != "running" or time.monotonic() > deadline:
                    break
                time.sleep(0.1)
        self.assertEqual((status, job["state"], job["report"]["outcome"]), (200, "done", "VERIFIED"))

    def test_bad_diagnose_requests_are_400(self):
        with serving(fake_jobs("report")) as (_, base):
            self.assertEqual(call(base, "POST", "/api/diagnose", raw=b"not json")[0], 400)
            status, body = call(base, "POST", "/api/diagnose", {"project": "p"})
        self.assertEqual((status, body["error"]), (400, "bad_request"))

    def test_busy_is_409(self):
        with serving(fake_jobs("sleep", timeout_s=3)) as (server, base):
            call(base, "POST", "/api/diagnose", {"project": "p", "victim": "a.B#c"})
            status, body = call(base, "POST", "/api/diagnose", {"project": "p", "victim": "a.B#c"})
            self.assertEqual((status, body["error"]), (409, "busy"))
            self.assertRegex(body["started"], r"^\d\d:\d\d:\d\d$")
            time.sleep(4)

    def test_unknown_job_is_404_with_a_reason(self):
        with serving(fake_jobs("report")) as (_, base):
            status, body = call(base, "GET", "/api/jobs/abc123")
        self.assertEqual(status, 404)
        self.assertIn("restarted", body["message"])

    def test_validate(self):
        f1 = json.loads(F1_REPORT.read_text(encoding="utf-8"))
        with serving(fake_jobs("report")) as (_, base):
            self.assertEqual(call(base, "POST", "/api/validate", f1), (200, {"valid": True, "message": None}))
            for bad in ({}, [], {"outcome": "VERIFIED"}):
                with self.subTest(bad=bad):
                    status, body = call(base, "POST", "/api/validate", bad)
                    self.assertEqual((status, body["valid"]), (200, False))
                    self.assertIn("not a valid FlakeTrace report", body["message"])

    def test_a_post_that_is_not_json_is_refused_and_starts_nothing(self):
        jobs = fake_jobs("report")
        with serving(jobs) as (_, base):
            request = urllib.request.Request(base + "/api/diagnose", method="POST",
                                             data=json.dumps({"project": "p", "victim": "a.B#c"}).encode("utf-8"),
                                             headers={"Content-Type": "text/plain"})
            with self.assertRaises(urllib.error.HTTPError) as caught:
                urllib.request.urlopen(request, timeout=10)
        self.assertEqual(caught.exception.code, 415)
        self.assertEqual(jobs._jobs, {})

    def test_a_foreign_host_is_refused(self):
        with serving(fake_jobs("report")) as (_, base):
            for method, path, body in (("GET", "/api/health", None), ("POST", "/api/diagnose", b'{"project": "p", "victim": "a.B#c"}')):
                with self.subTest(method=method):
                    request = urllib.request.Request(base + path, method=method, data=body,
                                                     headers={"Content-Type": "application/json", "Host": "evil.example"})
                    with self.assertRaises(urllib.error.HTTPError) as caught:
                        urllib.request.urlopen(request, timeout=10)
                    self.assertEqual(caught.exception.code, 403)

    def test_a_bad_content_length_is_refused_quickly(self):
        import http.client
        with serving(fake_jobs("report")) as (server, _):
            for length, expected in (("-1", 400), (str(10 * 1024 * 1024), 413)):
                with self.subTest(length=length):
                    connection = http.client.HTTPConnection("127.0.0.1", server.server_address[1], timeout=5)
                    connection.putrequest("POST", "/api/diagnose")
                    connection.putheader("Content-Type", "application/json")
                    connection.putheader("Content-Length", length)
                    connection.endheaders()
                    self.assertEqual(connection.getresponse().status, expected)
                    connection.close()

    def test_unknown_path_is_404(self):
        with serving(fake_jobs("report")) as (_, base):
            self.assertEqual(call(base, "GET", "/api/nothing")[0], 404)
            self.assertEqual(call(base, "POST", "/api/nothing", {})[0], 404)


class TestRealRunOnFixture(unittest.TestCase):
    """One real diagnose through the backend: Maven, fresh JVMs, javap and report validation."""

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "javap", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")

    def test_f1_is_verified_with_its_polluter(self):
        jobs = Jobs()
        job = jobs.start(str(FIXTURE), "odfixture.ConfigVictimTest#expectsDefaultMode")
        done = wait(jobs, job["id"], limit_s=600)
        self.assertEqual(done["state"], "done", done.get("message"))
        self.assertEqual(done["report"]["outcome"], "VERIFIED")
        self.assertEqual(done["report"]["polluters"], [{"class": "odfixture.ConfigPolluterTest", "method": "pollute"}])


if __name__ == "__main__":
    unittest.main()
