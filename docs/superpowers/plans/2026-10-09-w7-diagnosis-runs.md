# W7 Diagnosis Runs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Given a Maven/JUnit 4 project and a victim test, produce the raw evidence for a diagnosis — reference failure signature, victim-alone counts, a single polluter (if any), repeated-run counts, source-integrity result and an execution record — as one `DiagnosisRuns` object.

**Architecture:** Six small modules in `runner/` on top of W6's `OrderRunner`: `integrity.py` (hash before/after), `recording.py` (`RecordingRunner` logs every JVM run to JSON lines), `discovery.py` (Surefire-like class list + JUnit's method order via a new `FtHarness --list` mode), `search.py` (reproduce + one-by-one polluter search), `verify.py` (repeat ×n), `diagnose.py` (`run_steps` on any runner + `diagnose` wiring the real pieces). No verdict: M3's `decide()` does that in W9.

**Tech Stack:** Python 3.11+ stdlib only, Java 8+, JUnit 4.13.2 from the target project, Maven 3, `unittest`.

**Spec:** [ADR-004](../../03-Design/decisions/ADR-004-w7-diagnosis-runs.md). Builds on [ADR-003](../../03-Design/decisions/ADR-003-order-runner-junitcore-harness.md). Report fields: [report-schema.md](../../contracts/report-schema.md).

## Global Constraints

- The agent never runs `git commit`, `git push`, `git merge`, `git rebase`, `git reset`, `git stash`, or a discarding `git checkout`/`switch`; every "Hand over" step gives the member exact commands (CLAUDE.md §3).
- Branch `m2/w7-diagnosis-runs`. Title `[M2] <area>: <imperative>` ≤ 72 chars; body with `Verified:` (real command + real result) and `Refs: W7, ADR-004`; trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- `git config user.email` must print `raffay.moazzam@gmail.com`.
- Never write a number into a doc that a real run in this session did not produce (CLAUDE.md §4).
- Never write to `eval/`, `fixtures/`, `evidence/` or `docs/contracts/`. Tests may *import* `eval.baseline` and `eval.tests.fake_runner.FakeOrderRunner` (fakes only from tests; production code never imports them).
- No new dependency. Processes launched with argument lists only.
- Default `n = 20`. "Matches" always means `FailureSignature.matches()`. A `flaketrace.*` failure (crash/timeout/skip) is never a match and never the reference.
- Execution records go to `record_dir` (default `flaketrace-records/`, git-ignored), never inside the analysed project.
- Run tests from the repo root: `py -m unittest -v runner.tests.<module>` (Windows), `python -m unittest …` (CI).

## Review Focus

1. **Explicit `original_order` that does not contain the victim** → `ValueError` before Maven or any JVM runs. *(Task 5, `test_explicit_order_without_the_victim_fails_before_maven_runs`)*
2. **Victim is the first test in the order** (nothing to search) → no crash; `NO_SINGLE_POLLUTER`, `search_runs = 0`. *(Task 5, `test_victim_first_in_order_has_no_candidates`)*
3. **Project not compiled / no `target/test-classes`** → discovery finds no classes rather than crashing. *(Task 3, `test_missing_test_classes_folder_gives_no_classes`)*
4. **A source file changes during a diagnosis** → `source_integrity.passed` is false and the details name the file. *(Task 1, `test_changed_added_and_removed_files_are_named`)*
5. **The original order crashes or times out before the real failure shows** → the crash is not taken as the reference signature. *(Task 4, `test_crash_is_never_taken_as_the_reference`)*

---

### Task 0: Hand over the design (ADR-004 + this plan)

**Files:** `docs/03-Design/decisions/ADR-004-w7-diagnosis-runs.md` (written), this plan (written), `docs/genai-log-m2.md`, `docs/08-MidEval/genai-register.md`, `docs/08-MidEval/iteration-plan.md` (W7 row → In progress), `docs/09-Team/members.md` (row 2).

- [ ] **Step 1:** Append a GenAI-log entry "W7 design: ADR-004 and implementation plan" (options chosen by the member: discovery+override, one-by-one search with priority hook, n = 20, module approach A; spike results: all five fixture cases matched ground truth; N2 measured 18/60 on Windows → N2 test uses n = 40) and one register row.
- [ ] **Step 2:** W7 row State → `**In progress**: design ADR-004 agreed by M2`; members row 2 → `W7: design done; implementation next` / branch `m2/w7-diagnosis-runs`.
- [ ] **Step 3: Hand over**

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git switch -c m2/w7-diagnosis-runs
git add docs/03-Design/decisions/ADR-004-w7-diagnosis-runs.md docs/superpowers/plans/2026-10-09-w7-diagnosis-runs.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md docs/08-MidEval/iteration-plan.md docs/09-Team/members.md
git diff --staged
git commit -m "[M2] docs: propose ADR-004 for W7 diagnosis runs and its plan"   -m "Design for W7: reproduce the original failure, victim-alone check, one-by-one polluter
search, repeated runs, source integrity and an execution record, returned as raw counts
for M3's decide(). Proposes default n = 20 (open question I3).

Verified: throwaway spike on the fixture: F1/F2 POLLUTER_FOUND with the ground-truth
polluter, F3 NO_SINGLE_POLLUTER, N1/N2 VICTIM_FAILS_ALONE; spike code not committed.
Refs: W7, ADR-004"   -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -u origin m2/w7-diagnosis-runs
```

---

### Task 1: Source-integrity check

**Files:** Create `runner/integrity.py`, `runner/tests/test_integrity.py`. Docs as in the last step.

**Interfaces:**
- Produces: `runner.integrity.SourceIntegrity(passed: bool, details: str)` (frozen dataclass); `snapshot(project_dir) -> Dict[str, str]` (relative `/` path → SHA-256 hex; skips top-level `target/` and `.git/`); `compare(before, after) -> SourceIntegrity`.

- [ ] **Step 1: Write the failing tests** — `runner/tests/test_integrity.py`

```python
import tempfile
import unittest
from pathlib import Path

from runner.integrity import compare, snapshot


class TestIntegrity(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="flaketrace-integrity-"))
        (self.root / "src" / "main").mkdir(parents=True)
        (self.root / "src" / "main" / "A.java").write_text("class A {}")
        (self.root / "pom.xml").write_text("<project/>")

    def test_unchanged_project_passes(self):
        before = snapshot(self.root)
        result = compare(before, snapshot(self.root))
        self.assertTrue(result.passed)
        self.assertIn("2 files", result.details)

    def test_changed_added_and_removed_files_are_named(self):
        before = snapshot(self.root)
        (self.root / "src" / "main" / "A.java").write_text("class A { int x; }")
        (self.root / "src" / "main" / "B.java").write_text("class B {}")
        (self.root / "pom.xml").unlink()
        result = compare(before, snapshot(self.root))
        self.assertFalse(result.passed)
        self.assertEqual(
            result.details, "changed: src/main/A.java; added: src/main/B.java; removed: pom.xml"
        )

    def test_target_and_git_are_ignored(self):
        before = snapshot(self.root)
        for folder in ("target/classes", ".git"):
            (self.root / folder).mkdir(parents=True)
            (self.root / folder / "x").write_text("build output")
        self.assertTrue(compare(before, snapshot(self.root)).passed)

    def test_nested_folder_named_target_is_still_hashed(self):
        (self.root / "src" / "target").mkdir()
        (self.root / "src" / "target" / "C.java").write_text("class C {}")
        self.assertIn("src/target/C.java", snapshot(self.root))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run** `py -m unittest -v runner.tests.test_integrity` — Expected: `ModuleNotFoundError: No module named 'runner.integrity'`.
- [ ] **Step 3: Implement** — `runner/integrity.py`

```python
"""Source-integrity check (W7, ADR-004): hash the analysed project's files before and after a
diagnosis. Build output (target/) and git metadata (.git/) are left out."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

EXCLUDED_DIRS = {"target", ".git"}


@dataclass(frozen=True)
class SourceIntegrity:
    passed: bool
    details: str


def snapshot(project_dir) -> Dict[str, str]:
    """SHA-256 of every file under project_dir except target/ and .git/, keyed by relative path."""
    root = Path(project_dir)
    hashes = {}
    for folder, subfolders, files in os.walk(root):
        if Path(folder) == root:
            subfolders[:] = [d for d in subfolders if d not in EXCLUDED_DIRS]
        for name in files:
            path = Path(folder) / name
            hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def compare(before: Dict[str, str], after: Dict[str, str]) -> SourceIntegrity:
    changed = sorted(p for p in before.keys() & after.keys() if before[p] != after[p])
    added = sorted(after.keys() - before.keys())
    removed = sorted(before.keys() - after.keys())
    if not (changed or added or removed):
        return SourceIntegrity(True, f"{len(before)} files hashed (SHA-256) before and after; all identical")
    parts = [f"{label}: {', '.join(paths)}" for label, paths in
             (("changed", changed), ("added", added), ("removed", removed)) if paths]
    return SourceIntegrity(False, "; ".join(parts))
```

- [ ] **Step 4: Run** `py -m unittest -v runner.tests.test_integrity` — Expected: `Ran 4 tests … OK`.
- [ ] **Step 5: Docs (CLAUDE.md §5).** With the real output of the steps above:
  - `docs/evidence-m2.md` — new dated `###` entry under a `## W7 — diagnosis runs` heading
    (create the heading in Task 1): requirement, files, exact command, the RED result, the GREEN
    result line, limitations.
  - `docs/genai-log-m2.md` — new entry (tool, level L2, asked / retained / verified / errors,
    `**What I changed:** *fill after reading the diff.*`).
  - `docs/08-MidEval/genai-register.md` — one row after the last M2 row.
  - `runner/README.md` — add a short `## Diagnosis runs (W7)` section listing the modules as they land (integrity first).
- [ ] **Step 6: Hand over**

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git add runner/integrity.py runner/tests/test_integrity.py runner/README.md docs/evidence-m2.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md
git diff --staged
git commit -m "[M2] runner: hash the project's source before and after a diagnosis" \
  -m "Source-integrity check for W7: SHA-256 of every project file except target/ and .git/;\na mismatch names the changed, added and removed files.

Verified: py -m unittest -v runner.tests.test_integrity -> <real result>.
Refs: W7, ADR-004" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

---

### Task 2: Execution record (`RecordingRunner`)

**Files:** Create `runner/recording.py`, `runner/tests/test_recording.py`; modify `.gitignore` (add `flaketrace-records/` under a `# FlakeTrace execution records` comment). Docs.

**Interfaces:**
- Consumes: `eval.baseline.RunOutcome`, `TestIdentifier`; any object with `run_ordered(order)`.
- Produces: `runner.recording.RecordingRunner(runner, path, header: dict)` — attribute `path: Path`, settable `step: str` (default `"unlabelled"`), `run_ordered(order)` returns the wrapped runner's result unchanged and appends `{"type": "run", "step", "started", "seconds", "order": [str], "outcomes": [{"test", "passed", "failure_signature"?}]}`; line 1 is `{"type": "header", **header}`.

- [ ] **Step 1: Write the failing tests** — `runner/tests/test_recording.py`

```python
import json
import tempfile
import unittest
from pathlib import Path

from eval.baseline import FailureSignature, RunOutcome, TestIdentifier
from eval.tests.fake_runner import FakeOrderRunner
from runner.recording import RecordingRunner

A = TestIdentifier("pkg.ATest", "a")
B = TestIdentifier("pkg.BTest", "b")
SIG = FailureSignature("java.lang.AssertionError", "pkg.BTest.b:3", "boom")


def b_fails_after_a(order, test):
    if test == B and A in order and order.index(A) < order.index(B):
        return RunOutcome(passed=False, failure_signature=SIG)
    return RunOutcome(passed=True)


class TestRecordingRunner(unittest.TestCase):
    def setUp(self):
        self.path = Path(tempfile.mkdtemp(prefix="flaketrace-rec-")) / "nested" / "run.jsonl"
        self.fake = FakeOrderRunner(b_fails_after_a)
        self.recorder = RecordingRunner(self.fake, self.path, {"victim": str(B), "n": 3})

    def lines(self):
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines()]

    def test_header_is_written_first(self):
        self.assertEqual(self.lines(), [{"type": "header", "victim": "pkg.BTest#b", "n": 3}])

    def test_each_run_is_one_labelled_line_and_results_pass_through(self):
        self.recorder.step = "search"
        results = self.recorder.run_ordered([A, B])
        self.recorder.step = "alone"
        self.recorder.run_ordered([B])
        self.assertFalse(results[B].passed)
        self.assertEqual(self.fake.calls, [[A, B], [B]])
        header, first, second = self.lines()
        self.assertEqual(first["step"], "search")
        self.assertEqual(first["order"], ["pkg.ATest#a", "pkg.BTest#b"])
        self.assertEqual(first["outcomes"][0], {"test": "pkg.ATest#a", "passed": True})
        self.assertEqual(
            first["outcomes"][1]["failure_signature"],
            {"exception_type": "java.lang.AssertionError", "message": "boom", "stack_trace": "pkg.BTest.b:3"},
        )
        self.assertEqual(second["step"], "alone")
        self.assertTrue(second["outcomes"][0]["passed"])
        self.assertIn("seconds", second)
        self.assertIn("started", second)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run** `py -m unittest -v runner.tests.test_recording` — Expected: `ModuleNotFoundError: No module named 'runner.recording'`.
- [ ] **Step 3: Implement** — `runner/recording.py`

```python
"""Execution record (W7, ADR-004): RecordingRunner wraps an OrderRunner and appends every run
to a JSON-lines file, one line per JVM run, written as soon as the run finishes."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

from eval.baseline import RunOutcome, TestIdentifier


class RecordingRunner:
    """Satisfies eval.baseline.OrderRunner. Set `step` before a phase to label its runs."""

    def __init__(self, runner, path, header: dict):
        self._runner = runner
        self.path = Path(path)
        self.step = "unlabelled"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._write({"type": "header", **header})

    def run_ordered(self, order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]:
        started = datetime.now(timezone.utc).isoformat()
        clock = time.monotonic()
        results = self._runner.run_ordered(order)
        self._write({
            "type": "run",
            "step": self.step,
            "started": started,
            "seconds": round(time.monotonic() - clock, 3),
            "order": [str(test) for test in order],
            "outcomes": [_outcome(test, results[test]) for test in order],
        })
        return results

    def _write(self, entry: dict) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


def _outcome(test: TestIdentifier, outcome: RunOutcome) -> dict:
    entry = {"test": str(test), "passed": outcome.passed}
    if outcome.failure_signature is not None:
        signature = outcome.failure_signature
        entry["failure_signature"] = {
            "exception_type": signature.exception_type,
            "message": signature.message,
            "stack_trace": signature.stack_trace,
        }
    return entry
```

- [ ] **Step 4: Run** `py -m unittest -v runner.tests.test_recording` — Expected: `Ran 2 tests … OK`.
- [ ] **Step 5: Docs (CLAUDE.md §5).** With the real output of the steps above:
  - `docs/evidence-m2.md` — new dated `###` entry under a `## W7 — diagnosis runs` heading
    (create the heading in Task 1): requirement, files, exact command, the RED result, the GREEN
    result line, limitations.
  - `docs/genai-log-m2.md` — new entry (tool, level L2, asked / retained / verified / errors,
    `**What I changed:** *fill after reading the diff.*`).
  - `docs/08-MidEval/genai-register.md` — one row after the last M2 row.
  - `runner/README.md` — add `recording.py` to the W7 section.
- [ ] **Step 6: Hand over**

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git add runner/recording.py runner/tests/test_recording.py .gitignore runner/README.md docs/evidence-m2.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md
git diff --staged
git commit -m "[M2] runner: record every JVM run in a JSON-lines execution record" \
  -m "RecordingRunner wraps any OrderRunner and appends one line per run (step, order, each\ntest's outcome and signature, duration), so the execution record is complete by\nconstruction. Records go to flaketrace-records/, which is git-ignored.

Verified: py -m unittest -v runner.tests.test_recording -> <real result>.
Refs: W7, ADR-004" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

---

### Task 3: Discover the original order (`FtHarness --list`)

**Files:** Modify `runner/harness/FtHarness.java`, `runner/order_runner.py`; create `runner/discovery.py`, `runner/tests/test_discovery.py`. Docs.

**Interfaces:**
- Produces: `OrderRunner.list_methods(class_names: Sequence[str]) -> List[TestIdentifier]`; `runner.order_runner.java_version() -> str`; `runner.discovery.is_surefire_test_class(simple_name) -> bool`, `test_class_names(test_classes_dir) -> List[str]` (sorted FQNs; `[]` if the folder is missing), `discover_order(runner, test_classes_dir) -> List[TestIdentifier]`.
- Harness: `java FtHarness --list <file>`; stdin one class name per line; file one `Class#method` per line.

- [ ] **Step 1: Write the failing tests** — `runner/tests/test_discovery.py`

```python
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from eval.baseline import TestIdentifier
from runner.discovery import discover_order, is_surefire_test_class, test_class_names
from runner.order_runner import OrderRunner, maven_test_classpath

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "od-fixture"


class TestClassSelection(unittest.TestCase):
    def test_surefire_default_patterns(self):
        for name in ("TestFoo", "FooTest", "FooTests", "FooTestCase"):
            self.assertTrue(is_surefire_test_class(name), name)
        for name in ("Foo", "FooTestHelper", "FooTest$Inner", "Testing$1"):
            self.assertFalse(is_surefire_test_class(name), name)

    def test_class_names_are_fully_qualified_and_sorted(self):
        root = Path(tempfile.mkdtemp(prefix="flaketrace-classes-"))
        for rel in ("b/ZTest.class", "a/x/YTest.class", "a/Helper.class", "a/x/YTest$1.class",
                    "a/notes.txt", "TestTop.class"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_bytes(b"")
        self.assertEqual(test_class_names(root), ["TestTop", "a.x.YTest", "b.ZTest"])

    def test_missing_test_classes_folder_gives_no_classes(self):
        self.assertEqual(test_class_names(Path(tempfile.mkdtemp()) / "target" / "test-classes"), [])


class TestDiscoveryOnFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        runner = OrderRunner(maven_test_classpath(FIXTURE), working_dir=FIXTURE)
        cls.order = discover_order(runner, FIXTURE / "target" / "test-classes")

    def test_all_thirteen_fixture_methods_in_alphabetical_class_order(self):
        self.assertEqual(len(self.order), 13)
        classes = [t.class_name for t in self.order]
        self.assertEqual(classes, sorted(classes))
        self.assertEqual(self.order[:2], [
            TestIdentifier("odfixture.ConfigPolluterTest", "pollute"),
            TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode"),
        ])
        self.assertEqual(self.order[-1], TestIdentifier("odfixture.ToggleVictimTest", "expectsNotBothFlagsSet"))

    def test_class_with_two_methods_lists_both(self):
        math = [t.method for t in self.order if t.class_name == "odfixture.MathUtilTest"]
        self.assertEqual(sorted(math), ["addsTwoNumbers", "squaresANumber"])

    def test_class_without_tests_or_unloadable_is_left_out(self):
        runner = OrderRunner(maven_test_classpath(FIXTURE), working_dir=FIXTURE)
        self.assertEqual(runner.list_methods(["odfixture.Config", "odfixture.NoSuchTest"]), [])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run** `py -m unittest -v runner.tests.test_discovery` — Expected: `ModuleNotFoundError: No module named 'runner.discovery'`.
- [ ] **Step 3: Add the `--list` mode to `runner/harness/FtHarness.java`.** Replace the imports, class comment and the first lines of `main` with:

```java
import org.junit.internal.runners.ErrorReportingRunner;
import org.junit.runner.Description;
import org.junit.runner.JUnitCore;
import org.junit.runner.Request;
import org.junit.runner.Runner;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;

/**
 * Runs the tests listed on stdin ("Class#method", one per line) in that exact order, in this
 * one JVM, and writes one tab-separated result line per test to the file named in args[0].
 * With "--list <file>", reads class names instead and writes each class's test methods as
 * "Class#method", in the order JUnit would run them (ADR-004).
 * Launched by runner/order_runner.py; see ADR-003.
 */
public class FtHarness {

    public static void main(String[] args) throws Exception {
        if (args[0].equals("--list")) {
            list(args[1]);
            System.exit(0);
        }
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
```

and add this method directly above `static String runOne(String spec) {`:

```java
    static void list(String resultFile) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
        PrintStream out = new PrintStream(new FileOutputStream(resultFile), true, "UTF-8");
        String line;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }
            Runner runner;
            try {
                runner = Request.aClass(Class.forName(line)).getRunner();
            } catch (Throwable t) {
                continue;  // a class that cannot even load cannot be run either
            }
            if (runner instanceof ErrorReportingRunner) {
                continue;  // abstract class, or no @Test methods
            }
            for (Description child : runner.getDescription().getChildren()) {
                if (child.isTest() && child.getMethodName() != null) {
                    out.println(line + "#" + child.getMethodName());
                }
            }
        }
        out.close();
    }
```

- [ ] **Step 4: Add to `runner/order_runner.py`** — inside `class OrderRunner`, after `run_ordered`, and a module function after the class:

```python
    def list_methods(self, class_names: Sequence[str]) -> List[TestIdentifier]:
        """The test methods of each class, in the order JUnit would run them (FtHarness --list).
        Classes JUnit cannot run (abstract, no @Test methods, fail to load) are left out."""
        with tempfile.TemporaryDirectory(prefix="flaketrace-list-") as tmp:
            result_file = Path(tmp) / "methods.txt"
            subprocess.run(
                [self._java, "FtHarness", "--list", str(result_file)],
                input="".join(f"{name}\n" for name in class_names),
                env=_env_with_classpath([self._harness_dir] + self.classpath),
                cwd=self._working_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self._timeout_s,
                check=True,
            )
            lines = result_file.read_text(encoding="utf-8").split("\n")[:-1]
        return [TestIdentifier(*line.split("#", 1)) for line in lines]


def java_version() -> str:
    """First line of `java -version` (printed on stderr), for the execution record."""
    finished = subprocess.run([_tool("java"), "-version"], capture_output=True, text=True)
    return finished.stderr.strip().splitlines()[0]
```

- [ ] **Step 5: Create `runner/discovery.py`**

```python
"""Original-order discovery (W7, ADR-004): the test methods Maven Surefire would run, classes in
alphabetical order, methods in JUnit's own order."""

import os
from pathlib import Path
from typing import List

from eval.baseline import TestIdentifier


def is_surefire_test_class(simple_name: str) -> bool:
    """Surefire's default includes: Test*, *Test, *Tests, *TestCase. Inner classes ($) excluded."""
    if "$" in simple_name:
        return False
    return simple_name.startswith("Test") or simple_name.endswith(("Test", "Tests", "TestCase"))


def test_class_names(test_classes_dir) -> List[str]:
    root = Path(test_classes_dir)
    names = []
    for folder, _subfolders, files in os.walk(root):
        for name in files:
            if name.endswith(".class") and is_surefire_test_class(name[: -len(".class")]):
                relative = (Path(folder) / name).relative_to(root).with_suffix("")
                names.append(".".join(relative.parts))
    return sorted(names)


def discover_order(runner, test_classes_dir) -> List[TestIdentifier]:
    """`runner` is an order_runner.OrderRunner (it owns the harness that asks JUnit)."""
    return runner.list_methods(test_class_names(test_classes_dir))
```

- [ ] **Step 6: Run** `py -m unittest -v runner.tests.test_discovery runner.tests.test_order_runner` — Expected: `Ran 28 tests … OK` (6 discovery + 22 existing). Record the discovered fixture order (13 methods) in the evidence entry — JUnit's own method order inside `MathUtilTest`/`StringUtilTest` is whatever the run shows.
- [ ] **Step 7: Docs (CLAUDE.md §5).** With the real output of the steps above:
  - `docs/evidence-m2.md` — new dated `###` entry under a `## W7 — diagnosis runs` heading
    (create the heading in Task 1): requirement, files, exact command, the RED result, the GREEN
    result line, limitations.
  - `docs/genai-log-m2.md` — new entry (tool, level L2, asked / retained / verified / errors,
    `**What I changed:** *fill after reading the diff.*`).
  - `docs/08-MidEval/genai-register.md` — one row after the last M2 row.
  - `runner/README.md` — W7 section: discovery and the `--list` harness protocol; the Surefire `runOrder` limitation from ADR-004.
- [ ] **Step 8: Hand over**

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git add runner/harness/FtHarness.java runner/order_runner.py runner/discovery.py runner/tests/test_discovery.py runner/README.md docs/evidence-m2.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md
git diff --staged
git commit -m "[M2] runner: discover the test order like Surefire, methods from JUnit" \
  -m "Test classes come from target/test-classes using Surefire's default include patterns,\nsorted alphabetically; each class's methods come from JUnit itself through a new\nFtHarness --list mode, so the order matches what JUnit would run.

Verified: py -m unittest -v runner.tests.test_discovery runner.tests.test_order_runner ->\n<real result>; fixture discovered as 13 methods.
Refs: W7, ADR-004" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

---

### Task 4: Reproduce, polluter search, repeat

**Files:** Create `runner/search.py`, `runner/verify.py`, `runner/tests/test_search.py`. Docs.

**Interfaces:**
- Consumes: `eval.baseline.FailureSignature.matches`; any runner with `run_ordered`.
- Produces: `runner.search.SYNTHETIC_PREFIX = "flaketrace."`; `reproduce(runner, order, victim, attempts) -> (Optional[FailureSignature], runs_made, any_failures)`; `candidate_order(original_order, victim, priority=None) -> List[TestIdentifier]`; `find_polluter(runner, original_order, victim, reference, priority=None) -> (Optional[TestIdentifier], runs_made)`; `runner.verify.repeat(runner, sequence, victim, reference, n) -> (successes, any_failures)`.

- [ ] **Step 1: Write the failing tests** — `runner/tests/test_search.py`

```python
import unittest

from eval.baseline import FailureSignature, RunOutcome, TestIdentifier
from eval.tests.fake_runner import FakeOrderRunner
from runner.search import candidate_order, find_polluter, reproduce
from runner.verify import repeat

A = TestIdentifier("pkg.ATest", "a")
B = TestIdentifier("pkg.BTest", "b")
C = TestIdentifier("pkg.CTest", "c")
V = TestIdentifier("pkg.VictimTest", "v")
REF = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "expected 0")
OTHER = FailureSignature("java.lang.NullPointerException", "pkg.VictimTest.v:7", None)
CRASH = FailureSignature("flaketrace.JvmCrash", "", "JVM exited with code 1")
PASS = RunOutcome(passed=True)


def fails(signature):
    return RunOutcome(passed=False, failure_signature=signature)


def victim_fails_after(polluter, signature=REF):
    def outcome(order, test):
        if test == V and polluter in order and order.index(polluter) < order.index(V):
            return fails(signature)
        return PASS
    return outcome


def scripted_victim(outcomes):
    """Victim's outcome on successive calls follows `outcomes`; other tests pass."""
    remaining = list(outcomes)
    return lambda order, test: remaining.pop(0) if test == V else PASS


class TestReproduce(unittest.TestCase):
    def test_first_real_failure_becomes_the_reference(self):
        runner = FakeOrderRunner(scripted_victim([PASS, fails(REF), fails(OTHER)]))
        self.assertEqual(reproduce(runner, [A, V], V, attempts=5), (REF, 2, 1))
        self.assertEqual(len(runner.calls), 2)

    def test_crash_is_never_taken_as_the_reference(self):
        runner = FakeOrderRunner(scripted_victim([fails(CRASH), fails(REF)]))
        self.assertEqual(reproduce(runner, [A, V], V, attempts=5), (REF, 2, 2))

    def test_never_failing_returns_none_after_all_attempts(self):
        runner = FakeOrderRunner(lambda order, test: PASS)
        self.assertEqual(reproduce(runner, [A, V], V, attempts=3), (None, 3, 0))


class TestCandidateOrder(unittest.TestCase):
    def test_original_order_without_priority(self):
        self.assertEqual(candidate_order([A, B, C, V], V), [A, B, C])

    def test_priority_first_then_the_rest_ignoring_unknown_and_later_tests(self):
        later = TestIdentifier("pkg.LaterTest", "l")
        order = [A, B, C, V, later]
        self.assertEqual(candidate_order(order, V, [C, later, C, TestIdentifier("x.Y", "z")]), [C, A, B])


class TestFindPolluter(unittest.TestCase):
    def test_finds_the_polluter_and_counts_runs(self):
        runner = FakeOrderRunner(victim_fails_after(B))
        self.assertEqual(find_polluter(runner, [A, B, C, V], V, REF), (B, 2))
        self.assertEqual(runner.calls, [[A, V], [B, V]])

    def test_priority_is_tried_first(self):
        runner = FakeOrderRunner(victim_fails_after(B))
        self.assertEqual(find_polluter(runner, [A, B, C, V], V, REF, priority=[B]), (B, 1))

    def test_failure_with_a_different_signature_is_not_a_polluter(self):
        runner = FakeOrderRunner(victim_fails_after(A, OTHER))
        self.assertEqual(find_polluter(runner, [A, B, V], V, REF), (None, 2))


class TestRepeat(unittest.TestCase):
    def test_counts_matching_and_any_failures(self):
        runner = FakeOrderRunner(scripted_victim([fails(REF), PASS, fails(OTHER), fails(CRASH), fails(REF)]))
        self.assertEqual(repeat(runner, [A, V], V, REF, 5), (2, 4))
        self.assertEqual(len(runner.calls), 5)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run** `py -m unittest -v runner.tests.test_search` — Expected: `ModuleNotFoundError: No module named 'runner.search'`.
- [ ] **Step 3: Implement** — `runner/search.py`

```python
"""Reproduce the original failure and search for a single polluter (W7, ADR-004)."""

from typing import List, Optional, Sequence, Tuple

from eval.baseline import FailureSignature, TestIdentifier

# Exception types the runner invents for a crashed, timed-out or skipped test (ADR-003).
SYNTHETIC_PREFIX = "flaketrace."


def reproduce(
    runner, order: Sequence[TestIdentifier], victim: TestIdentifier, attempts: int
) -> Tuple[Optional[FailureSignature], int, int]:
    """Run `order` up to `attempts` times, stopping at the first run where the victim fails with
    a real (not crash/timeout/skip) failure. Returns (reference signature or None, runs made,
    runs where the victim failed for any reason)."""
    any_failures = 0
    for run in range(1, attempts + 1):
        outcome = runner.run_ordered(list(order))[victim]
        if outcome.passed:
            continue
        any_failures += 1
        if not outcome.failure_signature.exception_type.startswith(SYNTHETIC_PREFIX):
            return outcome.failure_signature, run, any_failures
    return None, attempts, any_failures


def candidate_order(
    original_order: Sequence[TestIdentifier],
    victim: TestIdentifier,
    priority: Optional[Sequence[TestIdentifier]] = None,
) -> List[TestIdentifier]:
    """Tests before the victim: those in `priority` first (in that order), then the rest in
    original order. Priority entries not before the victim are ignored."""
    before = list(original_order[: list(original_order).index(victim)])
    first = [t for t in dict.fromkeys(priority or []) if t in before]
    return first + [t for t in before if t not in first]


def find_polluter(
    runner,
    original_order: Sequence[TestIdentifier],
    victim: TestIdentifier,
    reference: FailureSignature,
    priority: Optional[Sequence[TestIdentifier]] = None,
) -> Tuple[Optional[TestIdentifier], int]:
    """Run [candidate, victim] once per candidate; return the first candidate after which the
    victim fails with the reference signature, and the number of runs made."""
    runs = 0
    for candidate in candidate_order(original_order, victim, priority):
        runs += 1
        outcome = runner.run_ordered([candidate, victim])[victim]
        if not outcome.passed and outcome.failure_signature.matches(reference):
            return candidate, runs
    return None, runs
```

- [ ] **Step 4: Implement** — `runner/verify.py`

```python
"""Repeated-run counts (W7, ADR-004)."""

from typing import Sequence, Tuple

from eval.baseline import FailureSignature, TestIdentifier


def repeat(
    runner, sequence: Sequence[TestIdentifier], victim: TestIdentifier, reference: FailureSignature, n: int
) -> Tuple[int, int]:
    """Run `sequence` n times, each in a fresh JVM. Returns (runs where the victim failed with a
    signature matching `reference`, runs where the victim failed for any reason)."""
    successes = any_failures = 0
    for _ in range(n):
        outcome = runner.run_ordered(list(sequence))[victim]
        if not outcome.passed:
            any_failures += 1
            if outcome.failure_signature.matches(reference):
                successes += 1
    return successes, any_failures
```

- [ ] **Step 5: Run** `py -m unittest -v runner.tests.test_search` — Expected: `Ran 9 tests … OK`.
- [ ] **Step 6: Docs (CLAUDE.md §5).** With the real output of the steps above:
  - `docs/evidence-m2.md` — new dated `###` entry under a `## W7 — diagnosis runs` heading
    (create the heading in Task 1): requirement, files, exact command, the RED result, the GREEN
    result line, limitations.
  - `docs/genai-log-m2.md` — new entry (tool, level L2, asked / retained / verified / errors,
    `**What I changed:** *fill after reading the diff.*`).
  - `docs/08-MidEval/genai-register.md` — one row after the last M2 row.
  - `runner/README.md` — W7 section: search and verify, the "crash is never the reference" rule.
- [ ] **Step 7: Hand over**

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git add runner/search.py runner/verify.py runner/tests/test_search.py runner/README.md docs/evidence-m2.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md
git diff --staged
git commit -m "[M2] runner: reproduce the failure and search for a single polluter" \
  -m "reproduce() takes the victim's first real failure in the original order as the reference\nsignature (a crash or timeout never is); find_polluter() tries [candidate, victim] one by\none, priority list first; repeat() counts matching and any-signature failures over n runs.

Verified: py -m unittest -v runner.tests.test_search -> <real result>.
Refs: W7, ADR-004" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

---

### Task 5: `diagnose()` end to end on the fixture

**Files:** Create `runner/diagnose.py`, `runner/tests/test_diagnose.py`; create `docs/04-Implementation/diagnosis-runs.md`. Modify `runner/README.md`, `docs/04-Implementation/README.md`, `docs/evidence-m2.md`, `docs/genai-log-m2.md`, `docs/08-MidEval/genai-register.md`, `docs/08-MidEval/iteration-plan.md`, `docs/09-Team/members.md`, `docs/08-MidEval/demo-plan.md` (Runner row of the mocked-components table), `docs/07-Defense/claims-ledger.md`.

**Interfaces:**
- Consumes: everything from Tasks 1–4 and W6 (`OrderRunner(classpath, working_dir, timeout_s)`, `maven_test_classpath`).
- Produces: status constants `POLLUTER_FOUND`, `VICTIM_FAILS_ALONE`, `NO_SINGLE_POLLUTER`, `NOT_REPRODUCED`; frozen dataclass `DiagnosisRuns(status, victim, original_order, reference_signature, polluters, sequence, sequence_n, sequence_successes, sequence_any_failures, alone_n, alone_successes, search_runs, source_integrity=None, execution_record=None)`; `run_steps(runner, original_order, victim, n, priority=None) -> DiagnosisRuns`; `diagnose(project_dir, victim, n=20, original_order=None, priority=None, record_dir="flaketrace-records", timeout_s=120.0) -> DiagnosisRuns`.

- [ ] **Step 1: Write the failing tests** — `runner/tests/test_diagnose.py`

```python
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from eval.baseline import FailureSignature, RunOutcome, TestIdentifier
from eval.tests.fake_runner import FakeOrderRunner
from runner.diagnose import (
    NO_SINGLE_POLLUTER,
    NOT_REPRODUCED,
    POLLUTER_FOUND,
    VICTIM_FAILS_ALONE,
    diagnose,
    run_steps,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "od-fixture"

A = TestIdentifier("pkg.ATest", "a")
B = TestIdentifier("pkg.BTest", "b")
V = TestIdentifier("pkg.VictimTest", "v")
LATER = TestIdentifier("pkg.ZTest", "z")
REF = FailureSignature("java.lang.AssertionError", "pkg.VictimTest.v:5", "expected 0")
PASS = RunOutcome(passed=True)
FAIL = RunOutcome(passed=False, failure_signature=REF)


def victim_fails_when(condition):
    return FakeOrderRunner(lambda order, test: FAIL if test == V and condition(order) else PASS)


class TestRunSteps(unittest.TestCase):
    def test_single_polluter_found_and_verified(self):
        runner = victim_fails_when(lambda order: B in order)
        runs = run_steps(runner, [A, B, V, LATER], V, n=4)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.original_order, [A, B, V])
        self.assertEqual(runs.reference_signature, REF)
        self.assertEqual(runs.polluters, [B])
        self.assertEqual(runs.sequence, [B, V])
        self.assertEqual((runs.sequence_n, runs.sequence_successes, runs.sequence_any_failures), (4, 4, 4))
        self.assertEqual((runs.alone_n, runs.alone_successes), (4, 0))
        self.assertEqual(runs.search_runs, 2)
        self.assertEqual(len(runner.calls), 1 + 4 + 2 + 4)

    def test_victim_failing_alone_stops_before_the_search(self):
        runner = victim_fails_when(lambda order: True)
        runs = run_steps(runner, [A, V], V, n=3)
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertEqual((runs.polluters, runs.sequence), ([], [V]))
        self.assertEqual((runs.sequence_n, runs.sequence_successes, runs.sequence_any_failures), (3, 3, 3))
        self.assertEqual((runs.alone_n, runs.alone_successes, runs.search_runs), (3, 3, 0))
        self.assertEqual(len(runner.calls), 1 + 3)

    def test_two_polluters_needed_repeats_the_original_order(self):
        runner = victim_fails_when(lambda order: A in order and B in order)
        runs = run_steps(runner, [A, B, V], V, n=2)
        self.assertEqual(runs.status, NO_SINGLE_POLLUTER)
        self.assertEqual((runs.polluters, runs.sequence), ([], [A, B, V]))
        self.assertEqual((runs.sequence_n, runs.sequence_successes), (2, 2))
        self.assertEqual((runs.alone_n, runs.alone_successes, runs.search_runs), (2, 0, 2))

    def test_never_failing_is_not_reproduced_and_runs_nothing_else(self):
        runner = victim_fails_when(lambda order: False)
        runs = run_steps(runner, [A, V], V, n=3)
        self.assertEqual(runs.status, NOT_REPRODUCED)
        self.assertIsNone(runs.reference_signature)
        self.assertEqual((runs.sequence, runs.sequence_n, runs.sequence_successes), ([A, V], 3, 0))
        self.assertEqual((runs.alone_n, runs.alone_successes, runs.search_runs), (0, 0, 0))
        self.assertEqual(len(runner.calls), 3)

    def test_bad_input_is_rejected_before_any_run(self):
        runner = victim_fails_when(lambda order: True)
        with self.assertRaises(ValueError):
            run_steps(runner, [A, B], V, n=3)
        with self.assertRaises(ValueError):
            run_steps(runner, [A, V], V, n=0)
        self.assertEqual(runner.calls, [])

    def test_victim_first_in_order_has_no_candidates(self):
        outcomes = [FAIL] + [PASS] * 10
        runner = FakeOrderRunner(lambda order, test: outcomes.pop(0))
        runs = run_steps(runner, [V, A], V, n=2)
        self.assertEqual(runs.status, NO_SINGLE_POLLUTER)
        self.assertEqual((runs.search_runs, runs.sequence), (0, [V]))

    def test_explicit_order_without_the_victim_fails_before_maven_runs(self):
        with self.assertRaises(ValueError):
            diagnose(Path("does-not-exist"), V, original_order=[A, B])


class TestDiagnoseOnFixture(unittest.TestCase):
    """Real JVM runs on fixtures/od-fixture, checked against ground_truth.json."""

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        cls.records = tempfile.mkdtemp(prefix="flaketrace-records-")
        cls.truth = {c["id"]: c for c in json.loads((FIXTURE / "ground_truth.json").read_text())["cases"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.records, ignore_errors=True)

    def diagnose_case(self, case_id, n):
        victim = TestIdentifier.from_dict(self.truth[case_id]["victim"])
        runs = diagnose(FIXTURE, victim, n=n, record_dir=self.records)
        self.assertTrue(runs.source_integrity.passed, runs.source_integrity.details)
        self.assertTrue(Path(runs.execution_record).exists())
        return runs

    def expected_polluters(self, case_id):
        return [TestIdentifier.from_dict(p) for p in self.truth[case_id]["polluters"]]

    def test_f1_single_static_field_polluter(self):
        runs = self.diagnose_case("F1", n=20)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.polluters, self.expected_polluters("F1"))
        self.assertEqual((runs.sequence_successes, runs.sequence_n), (20, 20))
        self.assertEqual((runs.alone_successes, runs.alone_n), (0, 20))
        record = Path(runs.execution_record).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(record), 1 + 1 + 20 + runs.search_runs + 20)

    def test_f2_single_system_property_polluter(self):
        runs = self.diagnose_case("F2", n=5)
        self.assertEqual(runs.status, POLLUTER_FOUND)
        self.assertEqual(runs.polluters, self.expected_polluters("F2"))
        self.assertEqual(runs.sequence_successes, 5)

    def test_f3_two_polluters_needed(self):
        runs = self.diagnose_case("F3", n=5)
        self.assertEqual(runs.status, NO_SINGLE_POLLUTER)
        self.assertEqual(runs.search_runs, 12)
        self.assertEqual(runs.sequence_successes, 5)

    def test_n1_fails_alone(self):
        runs = self.diagnose_case("N1", n=20)
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertEqual((runs.alone_successes, runs.alone_n), (20, 20))

    def test_n2_intermittent_failure_fails_alone(self):
        # ~30% failure rate on Windows, ~50% on Linux (ADR-004); n = 40 keeps a false result ~1e-5.
        runs = self.diagnose_case("N2", n=40)
        self.assertEqual(runs.status, VICTIM_FAILS_ALONE)
        self.assertGreaterEqual(runs.alone_successes, 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run** `py -m unittest -v runner.tests.test_diagnose` — Expected: `ModuleNotFoundError: No module named 'runner.diagnose'`.
- [ ] **Step 3: Implement** — `runner/diagnose.py`

```python
"""W7 entry point (ADR-004): reproduce the failure, check the victim alone, search for a single
polluter, repeat the sequence, check source integrity, record every run. Returns raw counts;
the verdict is M3's eval.outcome.decide() (W9 builds the report)."""

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence

from eval.baseline import FailureSignature, TestIdentifier
from runner.discovery import discover_order
from runner.integrity import SourceIntegrity, compare, snapshot
from runner.order_runner import OrderRunner, java_version, maven_test_classpath
from runner.recording import RecordingRunner
from runner.search import find_polluter, reproduce
from runner.verify import repeat

POLLUTER_FOUND = "POLLUTER_FOUND"
VICTIM_FAILS_ALONE = "VICTIM_FAILS_ALONE"
NO_SINGLE_POLLUTER = "NO_SINGLE_POLLUTER"
NOT_REPRODUCED = "NOT_REPRODUCED"


@dataclass(frozen=True)
class DiagnosisRuns:
    status: str
    victim: TestIdentifier
    original_order: List[TestIdentifier]
    reference_signature: Optional[FailureSignature]
    polluters: List[TestIdentifier]
    sequence: List[TestIdentifier]
    sequence_n: int
    sequence_successes: int
    sequence_any_failures: int
    alone_n: int
    alone_successes: int
    search_runs: int
    source_integrity: Optional[SourceIntegrity] = None
    execution_record: Optional[str] = None


def run_steps(
    runner,
    original_order: Sequence[TestIdentifier],
    victim: TestIdentifier,
    n: int,
    priority: Optional[Sequence[TestIdentifier]] = None,
) -> DiagnosisRuns:
    """Steps 3-6 of ADR-004 on any OrderRunner. Stops early as the ADR's status table says."""
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n!r}")
    if victim not in original_order:
        raise ValueError(f"victim {victim} is not in the original order")
    order = list(original_order[: list(original_order).index(victim) + 1])

    _label(runner, "reproduce")
    reference, attempts, attempt_failures = reproduce(runner, order, victim, n)
    if reference is None:
        return DiagnosisRuns(NOT_REPRODUCED, victim, order, None, [], order,
                             attempts, 0, attempt_failures, 0, 0, 0)

    _label(runner, "alone")
    alone_successes, alone_any = repeat(runner, [victim], victim, reference, n)
    if alone_successes >= 1:
        return DiagnosisRuns(VICTIM_FAILS_ALONE, victim, order, reference, [], [victim],
                             n, alone_successes, alone_any, n, alone_successes, 0)

    _label(runner, "search")
    polluter, search_runs = find_polluter(runner, order, victim, reference, priority)
    sequence = order if polluter is None else [polluter, victim]
    _label(runner, "verify")
    successes, any_failures = repeat(runner, sequence, victim, reference, n)
    status = NO_SINGLE_POLLUTER if polluter is None else POLLUTER_FOUND
    polluters = [] if polluter is None else [polluter]
    return DiagnosisRuns(status, victim, order, reference, polluters, sequence,
                         n, successes, any_failures, n, 0, search_runs)


def diagnose(
    project_dir,
    victim: TestIdentifier,
    n: int = 20,
    original_order: Optional[Sequence[TestIdentifier]] = None,
    priority: Optional[Sequence[TestIdentifier]] = None,
    record_dir="flaketrace-records",
    timeout_s: float = 120.0,
) -> DiagnosisRuns:
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n!r}")
    if original_order is not None and victim not in original_order:
        raise ValueError(f"victim {victim} is not in the original order")
    project = Path(project_dir).resolve()
    before = snapshot(project)
    runner = OrderRunner(maven_test_classpath(project), working_dir=project, timeout_s=timeout_s)
    order = list(original_order) if original_order is not None else discover_order(
        runner, project / "target" / "test-classes")

    started = datetime.now(timezone.utc)
    record = Path(record_dir) / f"{started.strftime('%Y%m%dT%H%M%SZ')}-{victim}.jsonl"
    recorder = RecordingRunner(runner, record, {
        "victim": str(victim), "n": n, "project": str(project),
        "java_version": java_version(), "started": started.isoformat(),
    })
    result = run_steps(recorder, order, victim, n, priority)
    return replace(result, source_integrity=compare(before, snapshot(project)),
                   execution_record=str(record))


def _label(runner, step: str) -> None:
    if isinstance(runner, RecordingRunner):
        runner.step = step
```

- [ ] **Step 4: Run** `py -m unittest -v runner.tests.test_diagnose` — Expected: `Ran 12 tests … OK` (7 `run_steps` unit tests, 5 real fixture cases). Record the real time.
- [ ] **Step 5: Mutation check (principle 7.2).** Temporarily change `if alone_successes >= 1:` to `if alone_successes >= 100:` in `runner/diagnose.py`; run `py -m unittest runner.tests.test_diagnose.TestRunSteps`; expect `test_victim_failing_alone_stops_before_the_search` to FAIL. Restore; rerun → OK.
- [ ] **Step 6: Full runner suite** — `py -m unittest runner.tests.test_order_runner runner.tests.test_integrity runner.tests.test_recording runner.tests.test_discovery runner.tests.test_search runner.tests.test_diagnose` — Expected: `Ran 55 tests … OK`. `git status --short fixtures/` prints nothing.
- [ ] **Step 7: Docs.**
  - `docs/evidence-m2.md` — entry with each fixture case's real status, polluter, counts and time, against `ground_truth.json`; the mutation result; source integrity.
  - `docs/04-Implementation/diagnosis-runs.md` — four-point note (what/why; alternatives from ADR-004; what breaks: single polluters only, Surefire order, NOT_REPRODUCED has `alone_n = 0`, N2's platform-dependent rate; how to modify: add bisection for W10, change `n`, add a step label). Link from `docs/04-Implementation/README.md`.
  - `runner/README.md` — W7 section complete with a `diagnose()` usage example and the status table.
  - `docs/08-MidEval/demo-plan.md` — Runner row: implemented = ordered runner + W7 diagnosis runs on the fixture; mocked = none; plan = W9 report assembly.
  - `docs/07-Defense/claims-ledger.md` — row E9: "W7 identifies the ground-truth polluter for F1 and F2, reports F3 as needing more than one polluter, and N1/N2 as failing alone" with its backing (test names, evidence link), status SETTLED.
  - `docs/08-MidEval/iteration-plan.md` W7 row and `docs/09-Team/members.md` row 2 — "implemented; CI pending".
  - GenAI log entry + register row.
- [ ] **Step 8: Hand over**

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git add runner/diagnose.py runner/tests/test_diagnose.py runner/README.md docs/04-Implementation/diagnosis-runs.md docs/04-Implementation/README.md docs/evidence-m2.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md docs/08-MidEval/iteration-plan.md docs/09-Team/members.md docs/08-MidEval/demo-plan.md docs/07-Defense/claims-ledger.md
git diff --staged
git commit -m "[M2] runner: diagnose a victim end to end and return raw counts" \
  -m "diagnose() hashes the source, discovers or takes the original order, reproduces the\nfailure, checks the victim alone, searches for a single polluter, repeats the sequence\nn times and records every run. Returns DiagnosisRuns; the verdict stays with decide().

Verified: py -m unittest -v runner.tests.test_diagnose -> <real result>.\nF1 and F2 find the ground-truth polluter; F3 NO_SINGLE_POLLUTER; N1 and N2 fail alone.
Refs: W7, ADR-004" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

- [ ] **Step 9: CI evidence.** After the push, open a PR `m2/w7-diagnosis-runs` → `main`. Read the run via `https://api.github.com/repos/zoyaahmad428/FlakeTrace/actions/runs?branch=m2/w7-diagnosis-runs` (job conclusions); ask the member for the `Ran … tests` line of the `runner` job (log needs sign-in). Record run id, result and the real duration of the runner tests step in `docs/evidence-m2.md`; W7 → **Complete** in `iteration-plan.md` and `members.md`; hand over a one-file-or-few docs commit `[M2] docs: record W7 CI result and mark W7 complete`.
