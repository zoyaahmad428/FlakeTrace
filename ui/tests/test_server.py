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

from ui.server import job_result

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


if __name__ == "__main__":
    unittest.main()
