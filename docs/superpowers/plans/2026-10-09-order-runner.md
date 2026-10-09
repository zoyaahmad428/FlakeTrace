# W6 Order Runner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `OrderRunner.run_ordered` for JUnit 4: run an explicit ordered list of test methods in one fresh JVM per call, in exactly that order, returning pass/fail and a normalised failure signature per test.

**Architecture:** A Python class (`runner/order_runner.py`) launches a small Java program (`runner/harness/FtHarness.java`) once per call. The harness runs each test with JUnit's own `JUnitCore.run(Request.method(...))`, one after another in that single JVM, and writes one result line per test to a file. Python turns those lines into `eval.baseline.RunOutcome` objects. The classpath is the target project's own, obtained from Maven, so no dependency is added.

**Tech Stack:** Python 3.11+ (stdlib only), Java 8+ (`java`, `javac`), JUnit 4.13.2 (from the target project), Maven 3 (only to get the classpath), `unittest`, GitHub Actions.

**Spec:** [ADR-003](../../03-Design/decisions/ADR-003-order-runner-junitcore-harness.md). Contract: [interfaces.md](../../contracts/interfaces.md) Interface 1; protocol in `eval/baseline.py`.

## Global Constraints

- The agent never runs `git commit`, `git push`, `git checkout`/`switch` that discards changes; it hands the member the exact commands (CLAUDE.md §3). Every "Commit" step below is a **hand-over**, not an agent action.
- Branch: `m2/order-runner`. Commit title format: `[M2] <area>: <imperative>` (≤72 chars); body has `Verified:` (real command + real result) and `Refs: W6`; trailer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- `git config user.email` must print `raffay.moazzam@gmail.com` before any commit — stop if not.
- Never write a result into a doc that was not produced by a real run in this session (CLAUDE.md §4).
- Never write to `fixtures/` or `eval/` (Member 3's folders) or `evidence/` (Member 1). Read-only use of `eval/baseline.py` types and `fixtures/od-fixture` is allowed. Build output under `fixtures/od-fixture/target/` is git-ignored and not source.
- Never edit `docs/contracts/*`.
- No new dependency in any `pom.xml` or `requirements.txt`.
- Launch processes with argument lists only (no `shell=True`); join classpath with `os.pathsep`; pass the classpath through the `CLASSPATH` environment variable.
- Harness compiled with `javac -source 8 -target 8 -Xlint:-options`.
- Run tests from the repo root. Local Windows: `py -m unittest -v runner.tests.test_order_runner`. CI/Linux: `python -m unittest …`.

## Review Focus

1. **Duplicate test in one order** → `ValueError`, never a silently merged result. *(Task 2, `test_duplicate_test_in_order_is_rejected`)*
2. **Misspelt class or method** → that test is reported FAIL with JUnit's/the JVM's exception; the rest of the order still runs. *(Task 2, `test_unknown_method_and_class_are_reported_as_failures`)*
3. **JVM hangs** → after `timeout_s`, every unreported test fails with `flaketrace.Timeout`; the call returns. *(Task 2, `test_timeout_reports_every_test_as_failed`)*
4. **JVM dies mid-run, leaving a half-written last line** → that test is reported `flaketrace.JvmCrash`, not parsed as garbage. *(Task 2, `test_truncated_last_line_is_treated_as_missing`)*
5. **Same failure on JDK 8 (CI) and JDK 21 (laptop)** → identical `stack_trace`, so `FailureSignature.matches()` holds across machines. *(Task 1, `test_jdk8_and_jdk21_give_the_same_stack`)*

---

### Task 0: Hand over the design (ADR-003 + this plan)

**Files:**
- Create (already written): `docs/03-Design/decisions/ADR-003-order-runner-junitcore-harness.md`
- Create (already written): `docs/superpowers/plans/2026-10-09-order-runner.md`
- Modify: `docs/genai-log-m2.md` (append entry)
- Modify: `docs/08-MidEval/genai-register.md` (one row)

**Interfaces:** none (docs only).

- [ ] **Step 1: Append to `docs/genai-log-m2.md`**

```markdown
## 2026-10-09 — W6 design: order runner (ADR-003) and implementation plan

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** propose at least two designs for `OrderRunner.run_ordered` (JUnit 4, one
fresh JVM per call, exact order), with trade-offs, classpath without new dependencies, and
portability on Windows/WSL/CI; stop for my choice; then write the plan.

**What was retained:** option A — Python `OrderRunner` + JUnitCore harness (ADR-003); the
implementation plan in `docs/superpowers/plans/2026-10-09-order-runner.md`.

**What I decided:** chose A over Maven Surefire (cannot honour a method-level order across
classes) and an all-Java runner (second language boundary with `eval/`).

**How it was verified:** a throwaway spike (not committed) compiled the harness against the
fixture's own classpath and ran F1 on my laptop (JDK 21): victim alone PASS; polluter then
victim FAIL `java.lang.AssertionError`; reversed order PASS.

**Errors found:** the ADR first said `javac --release 8`; the spike showed `-source 8 -target 8`
works on both JDK 8 and 21, so the ADR was corrected. Maven was not installed on my laptop —
installed 3.10.0 and added to user PATH.

**What I changed:** *fill after reviewing the ADR.*
```

- [ ] **Step 2: Add a row to the register table in `docs/08-MidEval/genai-register.md`** (after the last 2026-10-09 M2 row)

```markdown
| 2026-10-09 | M2 | Claude Opus 5.5 | L2 | ADR-003 (order-runner design), W6 implementation plan | Design alternatives, ADR text, plan | Chose option A; reviewed ADR | Spike on F1 (not committed): alone PASS, after polluter FAIL | ADR `--release 8` corrected to `-source 8 -target 8` | [[genai-log-m2]] |
```

- [ ] **Step 3: Hand over** — show `git status --short`, then give:

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git switch -c m2/order-runner
git add docs/03-Design/decisions/ADR-003-order-runner-junitcore-harness.md docs/superpowers/plans/2026-10-09-order-runner.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md
git diff --staged
git commit -m "[M2] docs: propose ADR-003 order runner design and W6 plan" \
  -m "Answers open question I1: a Python OrderRunner launches a small JUnitCore harness,
one fresh JVM per call, tests in exactly the given order. Surefire was rejected because it
cannot run a method-level order across classes.

Verified: throwaway spike on fixture F1 (JDK 21): victim alone PASS; after polluter FAIL
java.lang.AssertionError; reversed order PASS. Spike code not committed.
Refs: W6, interfaces.md I1" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push -u origin m2/order-runner
```

---

### Task 1: Harness + happy path, proven on F1 (hand-over 1)

**Files:**
- Create: `runner/harness/FtHarness.java`
- Create: `runner/order_runner.py`
- Create: `runner/tests/test_order_runner.py`
- Modify: `runner/README.md`, `docs/evidence-m2.md`, `docs/genai-log-m2.md`, `docs/08-MidEval/genai-register.md`, `docs/08-MidEval/iteration-plan.md` (W6 row), `docs/09-Team/members.md` (row 2), `docs/04-Implementation/README.md` (note link)
- Create: `docs/04-Implementation/sandbox-runner.md`

No `__init__.py` files: `eval/` has none either; `python -m unittest runner.tests.test_order_runner` works through namespace packages, same as `eval.tests.*` in CI.

**Interfaces:**
- Consumes: `eval.baseline.TestIdentifier(class_name, method)` (`str()` → `"Class#method"`), `RunOutcome(passed, failure_signature)`, `FailureSignature(exception_type, stack_trace, message)`.
- Produces:
  - `runner.order_runner.normalise_stack(frames: List[str]) -> str`
  - `runner.order_runner.normalise_message(message: str) -> str`
  - `runner.order_runner.parse_results(text: str, order: Sequence[TestIdentifier], missing_type: str, missing_message: str) -> Dict[TestIdentifier, RunOutcome]`
  - `runner.order_runner.maven_test_classpath(project_dir) -> List[str]`
  - `runner.order_runner.OrderRunner(classpath: Sequence[str], timeout_s: float = 120.0)`, attribute `classpath: List[str]`, method `run_ordered(order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]`
  - Harness protocol: `java FtHarness <result-file>`, stdin = one `Class#method` per line; result file = one line per test: `index\tClass#method\tPASS|FAIL|SKIP\texceptionClass\tmessage\tframe|frame|…` with `\\`, `\t`, `\n`, `\r` escaped.

- [ ] **Step 1: Write the failing tests** — `runner/tests/test_order_runner.py`

```python
import os
import shutil
import unittest
from pathlib import Path

from eval.baseline import TestIdentifier
from runner.order_runner import (
    OrderRunner,
    maven_test_classpath,
    normalise_message,
    normalise_stack,
    parse_results,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "od-fixture"

POLLUTER = TestIdentifier("odfixture.ConfigPolluterTest", "pollute")
VICTIM = TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode")

JDK21_FRAMES = [
    "org.junit.Assert.fail:89",
    "org.junit.Assert.assertEquals:633",
    "odfixture.ConfigVictimTest.expectsDefaultMode:10",
    "jdk.internal.reflect.DirectMethodHandleAccessor.invoke:103",
    "java.lang.reflect.Method.invoke:580",
    "org.junit.runners.model.FrameworkMethod$1.runReflectiveCall:59",
    "FtHarness.main:24",
]
JDK8_FRAMES = [
    "org.junit.Assert.fail:89",
    "org.junit.Assert.assertEquals:633",
    "odfixture.ConfigVictimTest.expectsDefaultMode:10",
    "sun.reflect.NativeMethodAccessorImpl.invoke0:-2",
    "sun.reflect.NativeMethodAccessorImpl.invoke:62",
    "java.lang.reflect.Method.invoke:498",
    "org.junit.runners.model.FrameworkMethod$1.runReflectiveCall:50",
]


class TestNormalisation(unittest.TestCase):
    def test_stack_is_cut_at_the_first_framework_frame(self):
        self.assertEqual(
            normalise_stack(JDK21_FRAMES),
            "org.junit.Assert.fail:89\norg.junit.Assert.assertEquals:633\n"
            "odfixture.ConfigVictimTest.expectsDefaultMode:10",
        )

    def test_jdk8_and_jdk21_give_the_same_stack(self):
        self.assertEqual(normalise_stack(JDK8_FRAMES), normalise_stack(JDK21_FRAMES))

    def test_message_keeps_first_line_and_masks_numbers(self):
        self.assertEqual(
            normalise_message("expected:<0> but was:<1>\nsecond line"),
            "expected:<<N>> but was:<<N>>",
        )

    def test_message_masks_object_ids(self):
        self.assertEqual(normalise_message("from Request@4c3e4790"), "from Request@<ID>")


class TestParseResults(unittest.TestCase):
    def test_pass_and_fail_lines(self):
        text = (
            "0\todfixture.ConfigPolluterTest#pollute\tPASS\t\t\t\n"
            "1\todfixture.ConfigVictimTest#expectsDefaultMode\tFAIL\tjava.lang.AssertionError\t"
            "expected:<0> but was:<1>\t" + "|".join(JDK21_FRAMES) + "\n"
        )
        results = parse_results(text, [POLLUTER, VICTIM], "flaketrace.JvmCrash", "")
        self.assertTrue(results[POLLUTER].passed)
        signature = results[VICTIM].failure_signature
        self.assertEqual(signature.exception_type, "java.lang.AssertionError")
        self.assertEqual(signature.message, "expected:<<N>> but was:<<N>>")
        self.assertTrue(signature.stack_trace.endswith("odfixture.ConfigVictimTest.expectsDefaultMode:10"))


class TestOrderRunnerOnF1(unittest.TestCase):
    """Runs real JVMs on fixtures/od-fixture. Needs java, javac and mvn on PATH."""

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        cls.runner = OrderRunner(maven_test_classpath(FIXTURE))

    def test_victim_passes_alone(self):
        self.assertTrue(self.runner.run_ordered([VICTIM])[VICTIM].passed)

    def test_victim_fails_after_polluter_in_one_jvm(self):
        results = self.runner.run_ordered([POLLUTER, VICTIM])
        self.assertTrue(results[POLLUTER].passed)
        self.assertFalse(results[VICTIM].passed)
        signature = results[VICTIM].failure_signature
        self.assertEqual(signature.exception_type, "java.lang.AssertionError")
        self.assertTrue(signature.stack_trace.endswith("odfixture.ConfigVictimTest.expectsDefaultMode:10"))

    def test_order_is_honoured_victim_first_passes(self):
        results = self.runner.run_ordered([VICTIM, POLLUTER])
        self.assertTrue(results[VICTIM].passed)
        self.assertTrue(results[POLLUTER].passed)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to confirm it fails**

Run: `py -m unittest -v runner.tests.test_order_runner`
Expected: `ModuleNotFoundError: No module named 'runner.order_runner'` (ERROR, 0 tests run).

- [ ] **Step 3: Write the harness** — `runner/harness/FtHarness.java`

```java
import java.io.BufferedReader;
import java.io.FileOutputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;

import org.junit.runner.Description;
import org.junit.runner.JUnitCore;
import org.junit.runner.Request;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;

/**
 * Runs the tests listed on stdin ("Class#method", one per line) in that exact order, in this
 * one JVM, and writes one tab-separated result line per test to the file named in args[0].
 * Launched by runner/order_runner.py; see ADR-003.
 */
public class FtHarness {

    public static void main(String[] args) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "UTF-8"));
        PrintStream out = new PrintStream(new FileOutputStream(args[0]), true, "UTF-8");
        int index = 0;
        String line;
        while ((line = in.readLine()) != null) {
            line = line.trim();
            if (line.isEmpty()) {
                continue;
            }
            out.println(index + "\t" + line + "\t" + runOne(line));
            index++;
        }
        out.close();
        // Tests may leave non-daemon threads running; exit so the JVM never hangs after the last test.
        System.exit(0);
    }

    static String runOne(String spec) {
        int hash = spec.indexOf('#');
        Class<?> cls;
        try {
            cls = Class.forName(spec.substring(0, hash));
        } catch (Throwable t) {
            return format("FAIL", t);
        }
        final Throwable[] failure = new Throwable[1];
        final boolean[] skipped = new boolean[1];
        JUnitCore core = new JUnitCore();
        core.addListener(new RunListener() {
            @Override
            public void testFailure(Failure f) {
                failure[0] = f.getException();
            }

            @Override
            public void testAssumptionFailure(Failure f) {
                skipped[0] = true;
            }

            @Override
            public void testIgnored(Description d) {
                skipped[0] = true;
            }
        });
        core.run(Request.method(cls, spec.substring(hash + 1)));
        if (failure[0] != null) {
            return format("FAIL", failure[0]);
        }
        return skipped[0] ? "SKIP\t\t\t" : "PASS\t\t\t";
    }

    static String format(String status, Throwable t) {
        StringBuilder frames = new StringBuilder();
        for (StackTraceElement e : t.getStackTrace()) {
            if (frames.length() > 0) {
                frames.append('|');
            }
            frames.append(e.getClassName()).append('.').append(e.getMethodName())
                  .append(':').append(e.getLineNumber());
        }
        String message = t.getMessage() == null ? "" : t.getMessage();
        return status + "\t" + t.getClass().getName() + "\t" + escape(message) + "\t" + escape(frames.toString());
    }

    static String escape(String s) {
        return s.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r");
    }
}
```

- [ ] **Step 4: Write the minimal Python runner** — `runner/order_runner.py`

```python
"""Ordered single-JVM test runner for JUnit 4 (W6). Design: docs/03-Design/decisions/ADR-003-order-runner-junitcore-harness.md.

Implements the OrderRunner protocol from eval/baseline.py: each run_ordered call starts one
fresh JVM that runs the given tests in exactly the given order (runner/harness/FtHarness.java).
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence

from eval.baseline import FailureSignature, RunOutcome, TestIdentifier

HARNESS_SOURCE = Path(__file__).resolve().parent / "harness" / "FtHarness.java"

# A stack is cut at the first frame from JUnit's runner, reflection or the harness. These
# frames differ between JDK 8 and JDK 21 and say nothing about the failure itself.
_FRAMEWORK_PREFIXES = (
    "org.junit.runner.",
    "org.junit.runners.",
    "org.junit.internal.runners.",
    "sun.reflect.",
    "jdk.internal.reflect.",
    "java.lang.reflect.",
    "FtHarness.",
)

# Same masks as the POC's frozen signature definition (docs/05-Testing/poc/frozen-definitions.md).
_MESSAGE_MASKS = [
    (re.compile(r"0x[0-9a-fA-F]+"), "<HEX>"),
    (re.compile(r"@[0-9a-fA-F]{4,}"), "@<ID>"),
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\S*"), "<TS>"),
    (re.compile(r"/tmp/\S+"), "<TMP>"),
    (re.compile(r"(/[\w.\-]+){2,}"), "<PATH>"),
    (re.compile(r"\d+"), "<N>"),
]

_UNESCAPES = {"t": "\t", "n": "\n", "r": "\r", "\\": "\\"}


def normalise_stack(frames: List[str]) -> str:
    kept = []
    for frame in frames:
        if frame.startswith(_FRAMEWORK_PREFIXES):
            break
        kept.append(frame)
    return "\n".join(kept)


def normalise_message(message: str) -> str:
    lines = message.strip().splitlines()
    first = lines[0].strip() if lines else ""
    for pattern, replacement in _MESSAGE_MASKS:
        first = pattern.sub(replacement, first)
    return first[:200]


def _unescape(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            out.append(_UNESCAPES.get(text[i + 1], text[i + 1]))
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def parse_results(
    text: str, order: Sequence[TestIdentifier], missing_type: str, missing_message: str
) -> Dict[TestIdentifier, RunOutcome]:
    """Turn the harness's result file into one RunOutcome per test in `order`."""
    results: Dict[TestIdentifier, RunOutcome] = {}
    for line in text.splitlines():
        index, _spec, status, exception_type, message, frames = line.split("\t")
        test = order[int(index)]
        if status == "PASS":
            results[test] = RunOutcome(passed=True)
        else:
            frame_list = _unescape(frames).split("|") if frames else []
            results[test] = RunOutcome(
                passed=False,
                failure_signature=FailureSignature(
                    exception_type, normalise_stack(frame_list), normalise_message(_unescape(message))
                ),
            )
    return results


def _tool(name: str) -> str:
    # shutil.which finds mvn.cmd / java.exe on Windows; a bare "mvn" in an argument list does not.
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"'{name}' not found on PATH")
    return path


def maven_test_classpath(project_dir) -> List[str]:
    """Compile the project's tests and return its test classpath, using only the jars the
    project itself declares (JUnit included). Writes only to the project's target/."""
    project = Path(project_dir).resolve()
    with tempfile.TemporaryDirectory(prefix="flaketrace-cp-") as tmp:
        cp_file = Path(tmp) / "cp.txt"
        subprocess.run(
            [
                _tool("mvn"), "-B", "-q", "-f", str(project / "pom.xml"),
                "test-compile", "dependency:build-classpath", f"-Dmdep.outputFile={cp_file}",
            ],
            check=True,
        )
        jars = [p for p in cp_file.read_text(encoding="utf-8").strip().split(os.pathsep) if p]
    return [str(project / "target" / "test-classes"), str(project / "target" / "classes")] + jars


class OrderRunner:
    """Satisfies eval.baseline.OrderRunner. One fresh JVM per run_ordered call."""

    def __init__(self, classpath: Sequence[str], timeout_s: float = 120.0):
        self.classpath = list(classpath)
        self._timeout_s = timeout_s
        self._java = _tool("java")
        self._harness_dir = tempfile.mkdtemp(prefix="flaketrace-harness-")
        compiled = subprocess.run(
            [_tool("javac"), "-source", "8", "-target", "8", "-Xlint:-options",
             "-d", self._harness_dir, str(HARNESS_SOURCE)],
            env=_env_with_classpath(self.classpath),
            capture_output=True,
            text=True,
        )
        if compiled.returncode != 0:
            raise RuntimeError(f"could not compile FtHarness:\n{compiled.stderr}")

    def run_ordered(self, order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]:
        order = list(order)
        with tempfile.TemporaryDirectory(prefix="flaketrace-run-") as tmp:
            result_file = Path(tmp) / "results.tsv"
            subprocess.run(
                [self._java, "FtHarness", str(result_file)],
                input="".join(f"{test}\n" for test in order),
                env=_env_with_classpath([self._harness_dir] + self.classpath),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self._timeout_s,
            )
            text = result_file.read_text(encoding="utf-8")
        return parse_results(text, order, "flaketrace.JvmCrash", "")


def _env_with_classpath(classpath: Sequence[str]) -> Dict[str, str]:
    # CLASSPATH in the environment instead of -cp avoids Windows' ~32k command-line limit.
    return dict(os.environ, CLASSPATH=os.pathsep.join(classpath))
```

- [ ] **Step 5: Run the tests**

Run: `py -m unittest -v runner.tests.test_order_runner`
Expected: `Ran 8 tests … OK` — 4 normalisation, 1 parse, 3 F1. Record the real output.

- [ ] **Step 6: Prove the F1 test can fail (CLAUDE.md principle 7.2).** Temporarily change `test_victim_fails_after_polluter_in_one_jvm` to run `[VICTIM, POLLUTER]` instead of `[POLLUTER, VICTIM]`; run it; expect `AssertionError: True is not false` (FAIL). Restore the order; rerun → OK. Record both results.

- [ ] **Step 7: Source-integrity check** — `git status --short fixtures/` must print nothing (only `target/`, which is ignored, changed).

- [ ] **Step 8: Docs (CLAUDE.md §5).** Write each with the real numbers from Steps 5–7:
  - `docs/evidence-m2.md` — replace `*Not started.*` under `## Order runner (W6)` with a dated entry: requirement (contract Interface 1 rules 1–2), files, exact command, real result line, the step 6 mutation result, step 7 result, limitations (each method is its own `Request`, so `@BeforeClass` runs per method; JUnit 4 only; crash/timeout handling arrives in Task 2).
  - `runner/README.md` — set `State` to "W6 in progress"; add a "How to run" section with the `py -m unittest` / `python -m unittest` command, prerequisites (JDK 8+, Maven on PATH), the harness protocol, and "MSYS/Cygwin Python with Windows Java is unsupported".
  - `docs/04-Implementation/sandbox-runner.md` — four-point note: (1) what/why, (2) alternatives from ADR-003, (3) what breaks (no `mvn`/`java`; a test that hangs; JDK frame differences), (4) how to modify (e.g. grouping consecutive same-class methods into one `Request` changes `runOne` and the signature tests). Link it from the `runner/` row in `docs/04-Implementation/README.md`.
  - `docs/08-MidEval/iteration-plan.md` — W6 row: State `In progress`, Evidence `runner/order_runner.py`, `[[evidence-m2]]`.
  - `docs/09-Team/members.md` — row 2 State: "W6: harness + F1 proof done; failure paths next".
  - `docs/genai-log-m2.md` and one `genai-register.md` row (level L2, verification = the Step 5/6 commands).

- [ ] **Step 9: Hand over** — show `git status --short` and the verification output, then:

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git add runner/harness/FtHarness.java runner/order_runner.py runner/tests/test_order_runner.py runner/README.md docs/evidence-m2.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md docs/08-MidEval/iteration-plan.md docs/09-Team/members.md docs/04-Implementation/sandbox-runner.md docs/04-Implementation/README.md
git diff --staged
git commit -m "[M2] runner: run an ordered list of JUnit 4 tests in one JVM" \
  -m "Implements OrderRunner.run_ordered from eval/baseline.py with a small JUnitCore harness:
one fresh JVM per call, tests in exactly the given order, a normalised failure signature
(exception type + stack cut at JUnit/reflection frames) per failed test.

Verified: py -m unittest -v runner.tests.test_order_runner -> <real result>.
F1 victim passes alone and fails after ConfigPolluterTest#pollute in one JVM.
Refs: W6, ADR-003" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

---

### Task 2: Every test always reported — crash, timeout, skip, bad input (hand-over 2)

**Files:**
- Modify: `runner/order_runner.py` (`parse_results`, `OrderRunner.run_ordered`)
- Modify: `runner/tests/test_order_runner.py` (add tests)
- Modify: `runner/README.md`, `docs/evidence-m2.md`, `docs/genai-log-m2.md`, `docs/08-MidEval/genai-register.md`, `docs/04-Implementation/sandbox-runner.md`, `docs/07-Defense/claims-ledger.md`

**Interfaces:**
- Consumes: everything Task 1 produces.
- Produces: no new names. New behaviour: `run_ordered` raises `ValueError` on duplicates, returns `{}` for `[]`, never omits a test; synthetic exception types `flaketrace.JvmCrash`, `flaketrace.Timeout`, `flaketrace.NotExecuted`.

- [ ] **Step 1: Add the failing tests.** Append to `TestParseResults`:

```python
    def test_escaped_tab_and_newline_in_message_are_restored(self):
        text = "0\tA#a\tFAIL\tjava.lang.Exception\tfirst\\tpart\\nsecond line\tA.a:1\n"
        test = TestIdentifier("A", "a")
        results = parse_results(text, [test], "flaketrace.JvmCrash", "")
        self.assertEqual(results[test].failure_signature.message, "first\tpart")

    def test_test_without_a_result_line_is_reported_with_the_missing_type(self):
        text = "0\todfixture.ConfigPolluterTest#pollute\tPASS\t\t\t\n"
        results = parse_results(text, [POLLUTER, VICTIM], "flaketrace.JvmCrash", "JVM exited with code 1")
        self.assertEqual(set(results), {POLLUTER, VICTIM})
        self.assertFalse(results[VICTIM].passed)
        self.assertEqual(results[VICTIM].failure_signature.exception_type, "flaketrace.JvmCrash")

    def test_truncated_last_line_is_treated_as_missing(self):
        text = "0\todfixture.ConfigPolluterTest#pollute\tPASS\t\t\t\n1\todfixture.Config"
        results = parse_results(text, [POLLUTER, VICTIM], "flaketrace.JvmCrash", "")
        self.assertEqual(results[VICTIM].failure_signature.exception_type, "flaketrace.JvmCrash")

    def test_skipped_test_is_a_failure_not_a_pass(self):
        text = "0\todfixture.ConfigVictimTest#expectsDefaultMode\tSKIP\t\t\t\n"
        results = parse_results(text, [VICTIM], "flaketrace.JvmCrash", "")
        self.assertFalse(results[VICTIM].passed)
        self.assertEqual(results[VICTIM].failure_signature.exception_type, "flaketrace.NotExecuted")
```

Append to `TestOrderRunnerOnF1`:

```python
    def test_each_call_gets_a_fresh_jvm(self):
        self.runner.run_ordered([POLLUTER, VICTIM])
        self.assertTrue(self.runner.run_ordered([VICTIM])[VICTIM].passed)

    def test_unknown_method_and_class_are_reported_as_failures(self):
        no_method = TestIdentifier("odfixture.ConfigVictimTest", "noSuchMethod")
        no_class = TestIdentifier("odfixture.NoSuchClass", "x")
        results = self.runner.run_ordered([no_method, no_class, VICTIM])
        self.assertEqual(results[no_method].failure_signature.exception_type, "java.lang.Exception")
        self.assertEqual(results[no_class].failure_signature.exception_type, "java.lang.ClassNotFoundException")
        self.assertTrue(results[VICTIM].passed)

    def test_duplicate_test_in_order_is_rejected(self):
        with self.assertRaises(ValueError):
            self.runner.run_ordered([VICTIM, VICTIM])

    def test_empty_order_returns_empty_result(self):
        self.assertEqual(self.runner.run_ordered([]), {})

    def test_timeout_reports_every_test_as_failed(self):
        runner = OrderRunner(self.runner.classpath, timeout_s=0.01)
        results = runner.run_ordered([POLLUTER, VICTIM])
        self.assertEqual(
            {r.failure_signature.exception_type for r in results.values()}, {"flaketrace.Timeout"}
        )
```

- [ ] **Step 2: Run to confirm the new ones fail**

Run: `py -m unittest -v runner.tests.test_order_runner`
Expected failures: missing-line test (`KeyError`/set mismatch), truncated-line (`ValueError: not enough values to unpack`), skip test (`flaketrace.NotExecuted` vs `""`), duplicate (no `ValueError`), timeout (`TimeoutExpired` raised). `test_each_call_gets_a_fresh_jvm`, the escape test, the empty-order test (the harness writes an empty file) and the unknown-class/method test may already pass — that is expected (the harness from Task 1 already does this); record which ones.

- [ ] **Step 3: Replace `parse_results`** in `runner/order_runner.py`

```python
def parse_results(
    text: str, order: Sequence[TestIdentifier], missing_type: str, missing_message: str
) -> Dict[TestIdentifier, RunOutcome]:
    """Turn the harness's result file into one RunOutcome per test in `order`. A test with no
    complete result line (the JVM crashed or timed out first) fails with `missing_type`."""
    results: Dict[TestIdentifier, RunOutcome] = {}
    for line in text.splitlines():
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        index, _spec, status, exception_type, message, frames = fields
        test = order[int(index)]
        if status == "PASS":
            results[test] = RunOutcome(passed=True)
        elif status == "SKIP":
            results[test] = RunOutcome(
                passed=False,
                failure_signature=FailureSignature(
                    "flaketrace.NotExecuted", "", "ignored or an assumption failed"
                ),
            )
        else:
            frame_list = _unescape(frames).split("|") if frames else []
            results[test] = RunOutcome(
                passed=False,
                failure_signature=FailureSignature(
                    exception_type, normalise_stack(frame_list), normalise_message(_unescape(message))
                ),
            )
    for test in order:
        if test not in results:
            results[test] = RunOutcome(
                passed=False, failure_signature=FailureSignature(missing_type, "", missing_message)
            )
    return results
```

- [ ] **Step 4: Replace `OrderRunner.run_ordered`**

```python
    def run_ordered(self, order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]:
        order = list(order)
        if len(set(order)) != len(order):
            raise ValueError("order contains the same test more than once")
        if not order:
            return {}
        with tempfile.TemporaryDirectory(prefix="flaketrace-run-") as tmp:
            result_file = Path(tmp) / "results.tsv"
            try:
                finished = subprocess.run(
                    [self._java, "FtHarness", str(result_file)],
                    input="".join(f"{test}\n" for test in order),
                    env=_env_with_classpath([self._harness_dir] + self.classpath),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=self._timeout_s,
                )
                missing = (
                    "flaketrace.JvmCrash",
                    f"JVM exited with code {finished.returncode} before this test reported",
                )
            except subprocess.TimeoutExpired:
                missing = ("flaketrace.Timeout", f"JVM exceeded {self._timeout_s}s")
            text = result_file.read_text(encoding="utf-8") if result_file.exists() else ""
        return parse_results(text, order, *missing)
```

- [ ] **Step 5: Run all tests**

Run: `py -m unittest -v runner.tests.test_order_runner`
Expected: `Ran 17 tests … OK`. Record the real output.

- [ ] **Step 6: Source integrity** — `git status --short fixtures/` prints nothing.

- [ ] **Step 7: Docs.** `docs/evidence-m2.md` (new dated entry: Review Focus items 1–4 with the real command/result), `runner/README.md` (error table from ADR-003), `docs/04-Implementation/sandbox-runner.md` point 3 (what the runner does on crash/timeout/skip), `docs/genai-log-m2.md` + register row, and a claims-ledger row in the most fitting section of `docs/07-Defense/claims-ledger.md`:

```markdown
| <next #> | The order runner executes tests in exactly the requested order in one fresh JVM per call, and never drops a test (crash/timeout/skip are reported as failures) | `runner/tests/test_order_runner.py` on fixture F1 | [[evidence-m2]] | M2 | SETTLED |
```

- [ ] **Step 8: Hand over**

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git add runner/order_runner.py runner/tests/test_order_runner.py runner/README.md docs/evidence-m2.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md docs/04-Implementation/sandbox-runner.md docs/07-Defense/claims-ledger.md
git diff --staged
git commit -m "[M2] runner: report crash, timeout and skip as failures, never drop a test" \
  -m "The contract requires every test in the order to appear in the result. Tests with no
result line now fail as flaketrace.JvmCrash or flaketrace.Timeout; @Ignore/Assume failures
fail as flaketrace.NotExecuted; duplicate tests in one order raise ValueError.

Verified: py -m unittest -v runner.tests.test_order_runner -> <real result>.
Refs: W6, ADR-003" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

---

### Task 3: Runner tests in CI (hand-over 3)

**Files:**
- Modify: `.github/workflows/ci.yml` (replace the trailing comment with a `runner` job)
- Modify: `README.md` (§ "Run the checks"), `CLAUDE.md` (§8 Commands), `docs/evidence-m2.md`, `docs/08-MidEval/iteration-plan.md` (W6 → Complete once CI is green), `docs/09-Team/members.md`, `docs/genai-log-m2.md`, `docs/08-MidEval/genai-register.md`

**Interfaces:** consumes `runner/tests/test_*.py` and the `FLAKETRACE_REQUIRE_JVM` switch from Task 1.

- [ ] **Step 1: Replace the last two comment lines of `.github/workflows/ci.yml`** (`# Member 2's order runner and Member 1's evidence extractor get their own jobs here once` / `# runner/ and evidence/ contain code and tests.`) with:

```yaml
  # Member 2's order runner: unit tests plus real single-JVM runs on fixture F1.
  # FLAKETRACE_REQUIRE_JVM turns "java/mvn missing" into a failure, so CI can never skip them.
  runner:
    runs-on: ubuntu-latest
    env:
      FLAKETRACE_REQUIRE_JVM: "1"
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "8"
          cache: maven
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Runner tests (every runner/tests/test_*.py)
        run: |
          modules=$(ls runner/tests/test_*.py | sed 's#/#.#g; s#\.py$##')
          python -m unittest -v $modules

  # Member 1's evidence extractor gets its own job here once evidence/ contains code and tests.
```

- [ ] **Step 2: Check the YAML parses**

Run: `py -c "import yaml,sys; d=yaml.safe_load(open('.github/workflows/ci.yml')); print(sorted(d['jobs']))"` (needs PyYAML; if absent: `py -m pip install pyyaml` into the user site, or skip and rely on Step 4).
Expected: `['fixture-build', 'python-eval', 'runner']`.

- [ ] **Step 3: Docs.** `README.md` "Run the checks" and `CLAUDE.md` §8: add
`python3 -m unittest -v runner.tests.test_order_runner   # needs JDK 8+ and Maven on PATH`.
`docs/evidence-m2.md`: CI entry written **after** Step 4 with the real run id.

- [ ] **Step 4: Hand over, then verify on GitHub**

```bash
git config user.email            # must print raffay.moazzam@gmail.com — stop if not
git add .github/workflows/ci.yml README.md CLAUDE.md
git diff --staged
git commit -m "[M2] ci: run the order runner's tests on JDK 8 in CI" \
  -m "Adds a runner job: unit tests plus real single-JVM runs on fixture F1. The job sets
FLAKETRACE_REQUIRE_JVM so a missing JDK or Maven fails the build instead of skipping.

Verified: workflow YAML parses with three jobs; GitHub Actions result recorded after push.
Refs: W6" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```

Then open the PR (`m2/order-runner` → `main`). In the `runner` job log, confirm `Ran 17 tests … OK` and **no** `skipped`. If JDK 8 produces a different stack than JDK 21, the F1 signature test will show it — fix the prefix list, not the test.

- [ ] **Step 5: Final docs hand-over** — record the real CI run id/URL and result in `docs/evidence-m2.md`; set W6 to **Complete** in `iteration-plan.md` and `members.md`; append the session to `genai-log-m2.md` + register row; hand over:

```bash
git add docs/evidence-m2.md docs/08-MidEval/iteration-plan.md docs/09-Team/members.md docs/genai-log-m2.md docs/08-MidEval/genai-register.md
git diff --staged
git commit -m "[M2] docs: record W6 CI evidence and mark the order runner complete" \
  -m "Verified: GitHub Actions run <id>, job runner -> <real result>.
Refs: W6" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push
```
