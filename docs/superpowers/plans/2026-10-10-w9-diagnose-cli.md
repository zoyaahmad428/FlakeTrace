# W9 Diagnose Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `py -m runner diagnose --project <dir> --victim <Class#method>` runs the diagnosis, gets
resource evidence for a found polluter, and writes one schema-validated report next to its
execution record.

**Architecture:** `runner/cli.py` holds `main(argv=None) -> int` and calls three existing
in-process functions: M2's `runner.diagnose.diagnose`, M1's `evidence.extract`
(`Project`, `analyse_test`, `find_edges`, `report_fields`) and M3's `eval.report.assemble_report`.
`runner/__main__.py` makes `py -m runner` call it. No code in `evidence/` or `eval/` changes.

**Tech Stack:** Python 3.11 (CI) / 3.14 (local), standard library `argparse`, `unittest`,
`unittest.mock`; JDK 8+ and Maven for the real runs; `jsonschema` via `eval/requirements.txt`.

**Spec:** `docs/03-Design/decisions/ADR-005-w9-diagnose-cli.md`

## Global Constraints

- Command: `py -m runner diagnose --project <dir> --victim <Class#method> [--n 20] [--records flaketrace-records]`, run from the repository root (or with it on `PYTHONPATH`).
- Exit codes: 0 report written (any outcome, including `UNRESOLVED`); 2 input wrong; 1 tool could not do its job; 3 diagnosis ran but no report can be built yet (`UnhandledStatus`).
- Known errors: one line `error: …` on stderr, no traceback. Unexpected exceptions are not caught.
- Any `ExtractError` maps to exit 1, whatever its own `exit_code`.
- Resource evidence only for `POLLUTER_FOUND`, at `evidence.extract.DEFAULT_DEPTH` (2).
- The CLI keeps no list of supported statuses; it catches `eval.report.UnhandledStatus`.
- Report file: execution record path with `.jsonl` replaced by `.report.json`; no report file on exit 3.
- Screen output is ASCII only (`->`, not `→`), so a Windows console never fails to print it.
- No new dependencies. Fakes/mocks only under `runner/tests/`. Never modify `fixtures/`, `evidence/`, `eval/`.
- The member commits; the agent never runs `git commit/push/merge/checkout`.

## Review Focus

1. A malformed `--victim` (`Cls`, `Cls#`, `#m`) → exit 2 before Maven runs (Task 1, `test_malformed_victims_exit_2`).
2. A `--project` that does not exist → exit 2 with "no pom.xml", not a Maven traceback (Task 1, `test_missing_project_exits_2`).
3. Running from a folder other than the repo root (with `PYTHONPATH`) and the default relative `--records` → the report's `execution_record_reference` is relative to that folder and exists (Task 2, `test_f1_command_line_end_to_end`).
4. The extractor failing after the diagnosis succeeded (classes missing, javap broken) → exit 1 with one line, not exit 2 and not a traceback (Task 1, `test_extractor_failure_exits_1`).
5. A victim that is not one of the project's tests (a typo) → exit 2 after Maven, message names the victim (Task 2, `test_unknown_victim_exits_2`).

## File Structure

| File | Responsibility |
| --- | --- |
| `runner/cli.py` (create) | Parse options, run the 5-step flow of ADR-005, map known errors to exit codes, print the summary |
| `runner/__main__.py` (create) | `sys.exit(main())` |
| `runner/tests/test_cli.py` (create) | Fast tests (no JVM, `diagnose` patched) and real fixture tests |
| `.github/workflows/ci.yml` (modify, `runner` job) | Install `eval/requirements.txt` before the runner tests |
| Docs (Task 2) | `runner/README.md`, `docs/04-Implementation/diagnose-cli.md` (create) + its README row, root `README.md`, `CLAUDE.md` §8, demo plan, iteration plan W9, `members.md`, claims ledger, evidence/GenAI log, register |

---

### Task 1: The command, its errors and its report (fast tests)

**Files:**
- Create: `runner/cli.py`, `runner/__main__.py`, `runner/tests/test_cli.py`
- Modify: `.github/workflows/ci.yml` (job `runner`)

**Interfaces:**
- Consumes: `runner.diagnose.diagnose(project_dir, victim, n=20, original_order=None, priority=None, record_dir="flaketrace-records", timeout_s=120.0) -> DiagnosisRuns`; `DiagnosisRuns` fields `status, victim, polluters, execution_record, ...`; `POLLUTER_FOUND, VICTIM_FAILS_ALONE, NO_SINGLE_POLLUTER, NOT_REPRODUCED`; `eval.report.assemble_report(diagnosis, resource_fields=None, confidence=0.95) -> dict`, `eval.report.UnhandledStatus`; `evidence.extract.Project(class_dirs)`, `analyse_test(project, test_id, depth)`, `find_edges(polluter_id, polluter, victim_id, victim)`, `report_fields(pair)`, `ExtractError`, `DEFAULT_DEPTH`; `eval.baseline.TestIdentifier(class_name, method)` (`str()` gives `Class#method`).
- Produces: `runner.cli.main(argv=None) -> int`; `runner.cli.run_diagnose(project: Path, victim_id: str, n: int, records: str) -> int`; `runner.cli.resource_fields(project: Path, runs) -> dict`; `runner.cli.summary(report: dict, report_path: Path) -> str`.

- [ ] **Step 1: Write the failing fast tests**

Create `runner/tests/test_cli.py`:

```python
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from eval.baseline import FailureSignature, TestIdentifier
from evidence.extract import ExtractError
from runner.cli import main
from runner.diagnose import NO_SINGLE_POLLUTER, POLLUTER_FOUND, VICTIM_FAILS_ALONE, DiagnosisRuns
from runner.integrity import SourceIntegrity

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "fixtures" / "od-fixture"

V = TestIdentifier("pkg.VictimTest", "v")
P = TestIdentifier("pkg.PolluterTest", "p")
REF = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "expected <N>")


def run_cli(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def project_with_pom():
    project = Path(tempfile.mkdtemp(prefix="flaketrace-cli-project-"))
    (project / "pom.xml").write_text("<project/>", encoding="utf-8")
    return project


def runs(status, record, **overrides):
    fields = dict(
        status=status, victim=V, original_order=[P, V], reference_signature=REF,
        polluters=[], sequence=[V], sequence_n=20, sequence_successes=20,
        sequence_any_failures=20, alone_n=20, alone_successes=20, search_runs=0,
        source_integrity=SourceIntegrity(True, "3 files hashed; all identical"),
        execution_record=str(record),
    )
    fields.update(overrides)
    return DiagnosisRuns(**fields)


class TestInputErrors(unittest.TestCase):
    def test_malformed_victims_exit_2(self):
        for victim in ("pkg.VictimTest", "pkg.VictimTest#", "#v"):
            with mock.patch("runner.cli.diagnose") as diagnose:
                code, _, err = run_cli(["diagnose", "--project", str(FIXTURE), "--victim", victim])
            self.assertEqual(code, 2, victim)
            self.assertIn("Class#method", err)
            diagnose.assert_not_called()

    def test_missing_project_exits_2(self):
        with mock.patch("runner.cli.diagnose") as diagnose:
            code, _, err = run_cli(["diagnose", "--project", "no/such/project", "--victim", "a.B#c"])
        self.assertEqual(code, 2)
        self.assertIn("no pom.xml", err)
        diagnose.assert_not_called()

    def test_n_below_one_exits_2_before_maven(self):
        code, _, err = run_cli(["diagnose", "--project", str(FIXTURE), "--victim", "a.B#c", "--n", "0"])
        self.assertEqual(code, 2)
        self.assertIn("n must be >= 1", err)

    def test_records_inside_the_project_exits_2_before_maven(self):
        code, _, err = run_cli(["diagnose", "--project", str(FIXTURE), "--victim", "a.B#c",
                                "--records", str(FIXTURE / "records")])
        self.assertEqual(code, 2)
        self.assertIn("inside the analysed project", err)

    def test_missing_subcommand_is_a_usage_error(self):
        with self.assertRaises(SystemExit) as raised, redirect_stderr(io.StringIO()):
            main([])
        self.assertEqual(raised.exception.code, 2)


class TestToolErrors(unittest.TestCase):
    def check(self, error, expected_code, expected_text):
        with mock.patch("runner.cli.diagnose", side_effect=error):
            code, _, err = run_cli(["diagnose", "--project", str(project_with_pom()), "--victim", "a.B#c"])
        self.assertEqual(code, expected_code)
        self.assertTrue(err.startswith("error: "), err)
        self.assertIn(expected_text, err)
        self.assertNotIn("Traceback", err)

    def test_victim_not_among_the_tests_exits_2(self):
        self.check(ValueError("victim a.B#c is not in the original order"), 2, "a.B#c")

    def test_maven_failure_exits_1(self):
        self.check(subprocess.CalledProcessError(1, ["C:/tools/mvn.cmd", "-B"]), 1, "mvn.cmd failed")

    def test_missing_tool_exits_1(self):
        self.check(RuntimeError("'javac' not found on PATH"), 1, "'javac' not found on PATH")

    def test_extractor_failure_exits_1(self):
        project = project_with_pom()  # no target/ folders, so Project() raises ExtractError(..., 2)
        found = runs(POLLUTER_FOUND, project / "r.jsonl", polluters=[P], sequence=[P, V],
                     alone_successes=0, search_runs=1)
        with mock.patch("runner.cli.diagnose", return_value=found):
            code, _, err = run_cli(["diagnose", "--project", str(project), "--victim", str(V)])
        self.assertEqual(code, 1)
        self.assertIn("error: resource evidence failed", err)


class TestReports(unittest.TestCase):
    def test_victim_fails_alone_writes_a_report_and_skips_the_extractor(self):
        records = Path(tempfile.mkdtemp(prefix="flaketrace-cli-records-"))
        record = records / "20261010T000000Z-pkg.VictimTest#v.jsonl"
        with mock.patch("runner.cli.diagnose", return_value=runs(VICTIM_FAILS_ALONE, record)), \
                mock.patch("runner.cli.analyse_test") as analyse:
            code, out, _ = run_cli(["diagnose", "--project", str(project_with_pom()), "--victim", str(V)])
        self.assertEqual(code, 0)
        analyse.assert_not_called()
        report_path = records / "20261010T000000Z-pkg.VictimTest#v.report.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual((report["outcome"], report["unresolved_reason"]), ("UNRESOLVED", "VICTIM_FAILS_ALONE"))
        self.assertEqual(report["execution_record_reference"], str(record))
        self.assertTrue(out.startswith("UNRESOLVED (VICTIM_FAILS_ALONE)  pkg.VictimTest#v"), out)
        self.assertIn("alone: 20/20", out)
        self.assertIn(str(report_path), out)
        out.encode("ascii")  # the summary must print on any console

    def test_no_single_polluter_exits_3_without_a_report(self):
        records = Path(tempfile.mkdtemp(prefix="flaketrace-cli-records-"))
        record = records / "20261010T000000Z-pkg.VictimTest#v.jsonl"
        unhandled = runs(NO_SINGLE_POLLUTER, record, sequence=[P, V], alone_successes=0, search_runs=1)
        with mock.patch("runner.cli.diagnose", return_value=unhandled):
            code, out, _ = run_cli(["diagnose", "--project", str(project_with_pom()), "--victim", str(V)])
        self.assertEqual(code, 3)
        self.assertEqual(list(records.glob("*.report.json")), [])
        self.assertIn("No report: NO_SINGLE_POLLUTER", out)
        self.assertIn(str(record), out)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run (repo root): `py -m unittest -v runner.tests.test_cli`
Expected: ERROR — `ModuleNotFoundError: No module named 'runner.cli'`.

- [ ] **Step 3: Write `runner/cli.py`**

```python
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
```

Create `runner/__main__.py`:

```python
import sys

from runner.cli import main

sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `py -m unittest -v runner.tests.test_cli`
Expected: `Ran 11 tests … OK`.

- [ ] **Step 5: Mutation check (the report tests must be able to fail)**

Temporarily change `if runs.status == POLLUTER_FOUND else None` to `if True else None` in `runner/cli.py`; run `py -m unittest runner.tests.test_cli.TestReports`.
Expected: FAIL (`analyse.assert_not_called()` / `IndexError` on `polluters[0]`). Restore with a text replacement (not `git checkout`) and check `git diff runner/cli.py` shows only the new file's content; rerun → OK.

- [ ] **Step 6: CI — install the schema library in the `runner` job**

In `.github/workflows/ci.yml`, job `runner`, change the `setup-python` step and add an install step before "Runner tests":

```yaml
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip
          cache-dependency-path: eval/requirements.txt
      - name: Install dependencies
        run: pip install -r eval/requirements.txt
```

Check: `py -c "import yaml; print(list(yaml.safe_load(open('.github/workflows/ci.yml'))['jobs']))"` lists the four jobs.

- [ ] **Step 7: Full runner suite**

Run: `py -m unittest $(ls runner/tests/test_*.py | sed 's#/#.#g; s#\.py$##')` (Git Bash)
Expected: `Ran 68 tests … OK` (57 existing + 11 new). `git status --short fixtures/` empty.

- [ ] **Step 8: Docs for this hand-over, then hand over**

`docs/evidence-m2.md` (commands and real results of steps 2, 4, 5, 7), `docs/genai-log-m2.md`, a register row in `docs/08-MidEval/genai-register.md`.
Commit title: `[M2] runner: add py -m runner diagnose with exit codes and report file`.

---

### Task 2: Real end-to-end runs on the fixture, and the docs

**Files:**
- Modify: `runner/tests/test_cli.py` (add class `TestCliOnFixture`)
- Create: `docs/04-Implementation/diagnose-cli.md`
- Modify: `runner/README.md`, `docs/04-Implementation/README.md`, `README.md`, `CLAUDE.md` §8, `docs/08-MidEval/demo-plan.md`, `docs/08-MidEval/iteration-plan.md` (W9 row), `docs/09-Team/members.md`, `docs/07-Defense/claims-ledger.md`, `docs/evidence-m2.md`, `docs/genai-log-m2.md`, `docs/08-MidEval/genai-register.md`

**Interfaces:**
- Consumes: `runner.cli.main(argv) -> int` (Task 1); `py -m runner diagnose …` (Task 1's `__main__.py`).
- Produces: nothing new in code.

- [ ] **Step 1: Write the real-run tests**

Add to `runner/tests/test_cli.py` (add `import os`, `import shutil`, `import sys` to the imports):

```python
class TestCliOnFixture(unittest.TestCase):
    """Real Maven/JVM/javap runs on fixtures/od-fixture, checked against ground_truth.json."""

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "javap", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        cls.records = tempfile.mkdtemp(prefix="flaketrace-cli-records-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.records, ignore_errors=True)

    def diagnose(self, victim, n):
        code, out, err = run_cli(["diagnose", "--project", str(FIXTURE), "--victim", victim,
                                  "--n", str(n), "--records", self.records])
        reports = sorted(Path(self.records).glob(f"*-{victim}.report.json"))
        report = json.loads(reports[-1].read_text(encoding="utf-8")) if reports else None
        return code, out, err, report

    def test_f1_command_line_end_to_end(self):
        work = Path(tempfile.mkdtemp(prefix="flaketrace-cli-cwd-"))
        finished = subprocess.run(
            [sys.executable, "-m", "runner", "diagnose", "--project", str(FIXTURE),
             "--victim", "odfixture.ConfigVictimTest#expectsDefaultMode"],
            cwd=work, env=dict(os.environ, PYTHONPATH=str(REPO)),
            capture_output=True, text=True, timeout=900,
        )
        self.assertEqual(finished.returncode, 0, finished.stderr)
        self.assertIn("VERIFIED", finished.stdout)
        reports = list((work / "flaketrace-records").glob("*.report.json"))
        self.assertEqual(len(reports), 1)
        report = json.loads(reports[0].read_text(encoding="utf-8"))
        self.assertEqual(report["outcome"], "VERIFIED")
        self.assertEqual(report["shared_resource"],
                         {"kind": "static-field", "class": "odfixture.Config", "field": "mode"})
        self.assertEqual((report["reproduction"]["successes"], report["victim_alone"]["successes"]), (20, 0))
        record = Path(report["execution_record_reference"])
        self.assertFalse(record.is_absolute())
        self.assertTrue((work / record).is_file())
        self.assertEqual(reports[0], work / record.with_suffix(".report.json"))
        shutil.rmtree(work, ignore_errors=True)

    def test_f2_depth_two_edge(self):
        code, _, err, report = self.diagnose("odfixture.FeatureVictimTest#expectsTurboDisabled", 20)
        self.assertEqual(code, 0, err)
        self.assertEqual(report["outcome"], "VERIFIED")
        self.assertEqual(report["shared_resource"], {"kind": "system-property", "key": "odfixture.turbo"})
        self.assertEqual(report["victim_read_location"],
                         {"class": "odfixture.FeatureFlags", "method": "isTurboEnabled", "bytecode_offset": 2})

    def test_f3_has_no_report_yet(self):
        code, out, _, report = self.diagnose("odfixture.ToggleVictimTest#expectsNotBothFlagsSet", 3)
        self.assertEqual(code, 3)
        self.assertIn("No report: NO_SINGLE_POLLUTER", out)
        self.assertIsNone(report)

    def test_n1_fails_alone(self):
        code, _, err, report = self.diagnose("odfixture.NegativeAloneFailTest#alwaysFails", 5)
        self.assertEqual(code, 0, err)
        self.assertEqual((report["outcome"], report["unresolved_reason"]), ("UNRESOLVED", "VICTIM_FAILS_ALONE"))
        self.assertEqual(report["polluters"], [])

    def test_unknown_victim_exits_2(self):
        code, _, err, report = self.diagnose("odfixture.ConfigVictimTest#noSuchTest", 3)
        self.assertEqual(code, 2)
        self.assertIn("odfixture.ConfigVictimTest#noSuchTest", err)
        self.assertIsNone(report)
```

- [ ] **Step 2: Run them and record the real results**

Run: `py -m unittest -v runner.tests.test_cli.TestCliOnFixture`
Expected: 5 tests OK. If one fails, stop and diagnose (systematic-debugging) before changing either the test or the code; record the real numbers either way. Also run the F1 command by hand once from the repo root and copy its screen output into `docs/evidence-m2.md`:
`py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode`

- [ ] **Step 3: Mutation check on the evidence step**

Temporarily replace `resource_fields(project, runs) if runs.status == POLLUTER_FOUND else None` with `None`; run `py -m unittest runner.tests.test_cli.TestCliOnFixture.test_f2_depth_two_edge`.
Expected: FAIL (`'UNRESOLVED' != 'VERIFIED'`, reason `NO_SUPPORTED_RESOURCE_EVIDENCE`). Restore by text replacement; `git diff --stat` shows no change from the restore; rerun → OK.

- [ ] **Step 4: Full runner suite**

Run: `py -m unittest $(ls runner/tests/test_*.py | sed 's#/#.#g; s#\.py$##')`
Expected: `Ran 73 tests … OK`. `git status --short fixtures/` empty.

- [ ] **Step 5: Docs**

- `runner/README.md`: header state (W9 command done); a "Command line (W9)" section with the command, options table, exit-code table and the F1 output from step 2; component 8 row "**done (W9)**".
- `docs/04-Implementation/diagnose-cli.md` (four-point note like `diagnosis-runs.md`: what it does, how it works, how it was verified, limitations) and its row in `docs/04-Implementation/README.md`.
- Root `README.md` "Run the checks" and `CLAUDE.md` §8: add `py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode`.
- `docs/08-MidEval/demo-plan.md` Runner row: the command works for F1, F2, N1 (real), F3 exits 3; still not built: W10.
- `docs/08-MidEval/iteration-plan.md` W9 row: add the command (M2) to M3's assembly text.
- `docs/09-Team/members.md` M2 row; `docs/07-Defense/claims-ledger.md` new row E10 for the command with its real backing.
- `docs/evidence-m2.md`, `docs/genai-log-m2.md`, register row.
- Do **not** edit `docs/contracts/interfaces.md` (I4 waits for M1/M3 on the PR).

- [ ] **Step 6: Hand over**

Commit title: `[M2] runner: prove the diagnose command end to end on the fixture`.
Then the member pushes and opens the PR for `m2/w9-cli` (description: ADR-005 asks M1 and M3 to agree on I4); CI's `runner` job line goes into `docs/evidence-m2.md` afterwards.
