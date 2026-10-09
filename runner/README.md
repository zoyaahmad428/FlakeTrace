# runner/ — bounded search and verification (Member 2)

**Owner:** Member 2 · **State:** W6 complete (2026-10-09) — ordered single-JVM runner, tested on fixture F1
locally (JDK 21) and in CI (JDK 8, job `runner`). W7 (victim-alone check, polluter search) next.

Implements the `OrderRunner` interface in [`eval/baseline.py`](../eval/baseline.py) and
everything built on it. Contract: [docs/contracts/interfaces.md](../docs/contracts/interfaces.md).
Design: [ADR-003](../docs/03-Design/decisions/ADR-003-order-runner-junitcore-harness.md).

## Order runner (W6)

```python
from runner.order_runner import OrderRunner, maven_test_classpath
from eval.baseline import TestIdentifier

runner = OrderRunner(maven_test_classpath("fixtures/od-fixture"), working_dir="fixtures/od-fixture")
results = runner.run_ordered([
    TestIdentifier("odfixture.ConfigPolluterTest", "pollute"),
    TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode"),
])   # {TestIdentifier: RunOutcome(passed, failure_signature)}
```

- `maven_test_classpath(project)` runs `mvn test-compile dependency:build-classpath` on the
  target project and returns `target/test-classes`, `target/classes` and the project's own jars.
  No dependency is added; only the git-ignored `target/` is written.
- `OrderRunner` compiles `harness/FtHarness.java` once into a temp directory. Pass the project
  directory as `working_dir` so tests using relative paths behave as under Maven. Each
  `run_ordered` call starts **one fresh JVM** that runs the tests **in exactly the given order**
  with JUnit's `JUnitCore` + `Request.method`.
- A failed test carries `FailureSignature(exception_type, stack_trace, message)`. `stack_trace`
  is the frames from the throw point down to the test, cut at the first JUnit-runner/reflection/
  harness frame, so an assertion failure gets the same signature on JDK 8 and JDK 21 (a JDK-internal
  frame *above* the cut keeps JDK-specific line numbers — compare signatures within one JDK). `message` is the first line with
  numbers, hex ids, paths and timestamps masked.

### Harness protocol

`java FtHarness <result-file>` with the classpath in `CLASSPATH`; stdin: one `Class#method` per
line. Result file, one line per test (tabs/newlines/backslashes escaped):

```
index<TAB>Class#method<TAB>PASS|FAIL|SKIP<TAB>exceptionClass<TAB>message<TAB>frame|frame|…
```

### Run the tests

Prerequisites: JDK 8+ (`java`, `javac`) and Maven on `PATH`. From the repo root:

```bash
py -m unittest -v runner.tests.test_order_runner        # Windows
python3 -m unittest -v runner.tests.test_order_runner   # Linux / WSL / CI
```

Without `java`/`javac`/`mvn` the real-JVM tests are skipped with a reason, unless
`FLAKETRACE_REQUIRE_JVM` is set (CI), in which case they fail.

### Portability

Processes are launched with argument lists (no shell), so paths with spaces work. The classpath
is joined with the running Python's `os.pathsep` and passed through `CLASSPATH`, avoiding
Windows' command-line length limit. Windows Python + Windows Java (Git Bash, PowerShell) and
Linux Python + Linux Java (WSL, CI) are supported; an MSYS/Cygwin Python driving a Windows JDK is
not.

### Every test is always reported

| Situation | Result for the affected tests |
| --- | --- |
| JVM exceeds `timeout_s` (default 120 s) | FAIL, `flaketrace.Timeout` |
| JVM exits before reporting a test (crash, `System.exit`) | FAIL, `flaketrace.JvmCrash` (exit code in the message) |
| Class or method not found | FAIL with the JVM's/JUnit's exception (`ClassNotFoundException`, `java.lang.Exception: No tests found matching …`) |
| `@Ignore` or failed `Assume` | FAIL, `flaketrace.NotExecuted` — a skip must never count as a pass |
| Same test twice in one order | `ValueError` before any JVM starts |
| Empty order | `{}`, no JVM started |

### Known limitations

- Each method is its own JUnit `Request`: `@BeforeClass`/`@AfterClass` run once per method,
  not once per class as under Maven Surefire.
- JUnit 4 only.
- Only the top-level exception is part of the signature; a wrapped cause is not compared.

## Diagnosis runs (W7, in progress)

Design: [ADR-004](../docs/03-Design/decisions/ADR-004-w7-diagnosis-runs.md). Modules land one by
one; each has its own tests in `runner/tests/`.

| Module | Job | State |
| --- | --- | --- |
| `integrity.py` | `snapshot(project)` hashes every file (SHA-256) except top-level `target/` and `.git/`; `compare(before, after)` → `SourceIntegrity(passed, details)` naming changed/added/removed files | done |
| `recording.py` | `RecordingRunner(runner, path, header)` wraps any runner; set `.step` before a phase; every JVM run is appended as one JSON line (step, order, outcomes with signatures, start, seconds) — line 1 is the header. Records go to `flaketrace-records/` (git-ignored) | done |
| `discovery.py` | original order like Surefire (classes) + JUnit (methods) | next |
| `search.py`, `verify.py` | reproduce, one-by-one polluter search, repeat ×n | planned |
| `diagnose.py` | `diagnose(project, victim, n=20)` → `DiagnosisRuns` (raw counts, no verdict) | planned |

## Planned components, in build order

| # | Component | Produces (report-schema fields) | Needed for Mid demo |
| --- | --- | --- | --- |
| 1 | Ordered single-JVM runner for JUnit 4 — **done (W6)** | per-test outcomes, `failure_signature` | Yes |
| 2 | Victim-alone check, repeated `n` times | `victim_alone` raw counts | Yes |
| 3 | Polluter search over preceding tests | `polluters`, `original_failing_order` | Yes |
| 4 | Deletion minimisation (handles F3's two-polluter case) | `reduced_sequence` | Yes (F1/F2); F3 stretch |
| 5 | Repeated-run verification of the reduced sequence | `reproduction` raw counts | Yes |
| 6 | Source-integrity check (hash target source before/after) | `source_integrity` | Yes |
| 7 | Execution record (JDK, order, seed, timestamps) | `execution_record_reference` | Yes |
| 8 | CLI entry point | — | Yes |

Test against `fixtures/od-fixture` (F1, F2, F3, N1, N2) — the expected outcomes are in
`fixtures/od-fixture/ground_truth.json`, written before any run.
