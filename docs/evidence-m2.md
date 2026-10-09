# Evidence log — Member 2 (Search & Verification)

Each row: requirement addressed, file/function, command, real result, limitation discovered.
Format follows [[evidence-m3]]. No number in this file is invented.

## 2026-10-09 — CI pipeline (GCR requirement: automated tests on GitHub)

**Requirement:** every PR into `main` runs the project's automated tests.

- File: `.github/workflows/ci.yml`, job `python-eval`.
- Command (same as CI):
  `python3 -m unittest $(ls eval/tests/test_*.py | sed 's#/#.#g; s#\.py$##')`
- Result: `Ran 55 tests … OK` (Python 3.13, local).
- Command: `python3 eval/benchmark/yield_report.py` → runs; all 6 cases `not_yet_run`
  (correct — no runner exists yet).
- Limitation: none further — the same commands also passed on GitHub Actions in run
  `37926797625` (job `python-eval`).

**Requirement:** CI checks the fixture's ground-truth premises on every change.

- File: `.github/workflows/ci.yml`, job `fixture-build`.
- Result: **passed on GitHub Actions**, run `37926797625` on PR #1 (`chore/repo-restructure`,
  head `8347168`), 2026-10-09. Every step succeeded: compile fixture; F1, F2, F3 victims pass
  alone; F1 and F2 victims fail after their polluter; N1 fails alone. JDK: Temurin 8.
  https://github.com/zoyaahmad428/FlakeTrace-Code/actions/runs/37926797625
- Limitation: checks premises with plain Maven (victims alone, polluter→victim for F1/F2, N1
  alone). F3's two-polluter premise needs the order runner.

## Order runner (W6)

### 2026-10-09 — Hand-over 1: harness + happy path on fixture F1

**Requirement:** contract Interface 1 ([[contracts/interfaces]]) rules 1–2 — all tests in one
JVM in exactly the given order; a fresh JVM per call. Design: [[03-Design/decisions/ADR-003-order-runner-junitcore-harness]].

- Files: `runner/harness/FtHarness.java`, `runner/order_runner.py` (`OrderRunner`,
  `maven_test_classpath`, `normalise_stack`, `normalise_message`, `parse_results`),
  `runner/tests/test_order_runner.py`.
- Environment: Windows 11, Git Bash, Python 3.14 (`py`), Temurin JDK 21.0.9, Maven 3.10.0.
- Command: `py -m unittest -v runner.tests.test_order_runner`
- Before the code existed: `ModuleNotFoundError: No module named 'runner.order_runner'` (expected).
- Result: `Ran 8 tests in 10.137s — OK` (4 normalisation, 1 result parsing, 3 real-JVM runs on F1).
  - `[ConfigVictimTest#expectsDefaultMode]` alone → PASS.
  - `[ConfigPolluterTest#pollute, ConfigVictimTest#expectsDefaultMode]` in one JVM → polluter
    PASS, victim FAIL `java.lang.AssertionError`, stack ending at
    `odfixture.ConfigVictimTest.expectsDefaultMode:10`.
  - `[ConfigVictimTest#expectsDefaultMode, ConfigPolluterTest#pollute]` → both PASS (order honoured).
- Mutation check (the F1 test can fail): changed the test's order to victim-then-polluter →
  `AssertionError: True is not false`, `FAILED (failures=1)`; restored the file (byte-identical)
  → `OK`.
- Source integrity: `git status --short fixtures/` printed nothing after the runs (only the
  git-ignored `target/` is written).
- Limitations: each method runs as its own JUnit `Request`, so `@BeforeClass`/`@AfterClass` run
  once per method, not once per class; JUnit 4 only; a JVM crash, timeout or `@Ignore` is not yet
  handled (hand-over 2); JDK 8 not yet run (CI, hand-over 3).

### 2026-10-09 — Hand-over 2: every test always reported

**Requirement:** contract Interface 1 rule 3 — every test in `order` appears in the result; a
crash is reported as a failure.

- Files: `runner/order_runner.py` (`parse_results`, `OrderRunner.run_ordered`),
  `runner/tests/test_order_runner.py` (9 new tests).
- Command: `py -m unittest -v runner.tests.test_order_runner` (same environment as hand-over 1).
- Before the change: `Ran 17 tests — FAILED (failures=3, errors=2)`:
  - duplicate test → `AssertionError: ValueError not raised`
  - timeout → `subprocess.TimeoutExpired` escaped the call
  - skipped test → reported with exception type `''` instead of `flaketrace.NotExecuted`
  - test with no result line → missing from the result
  - half-written last line → `ValueError: not enough values to unpack (expected 6, got 2)`
  - Already passing, because the hand-over 1 harness handles them: fresh JVM per call,
    escaped tab/newline, empty order, unknown method (`java.lang.Exception: No tests found
    matching Method …`) and unknown class (`java.lang.ClassNotFoundException`).
- After the change: `Ran 17 tests in 11.343s — OK`.
- Real-JVM checks on F1 inside that run: polluter-then-victim followed by a second call with
  the victim alone → victim PASS (no state leaks between calls); `timeout_s=0.01` → both tests
  reported `flaketrace.Timeout`.
- Source integrity: `git status --short fixtures/` printed nothing.
- Limitations: a real JVM crash (non-zero exit mid-run) is tested only through
  `parse_results` with a hand-written result file — the fixture has no test that kills the JVM,
  and the fixture is Member 3's to change. `@Ignore`/`Assume` → `SKIP` is tested the same way
  (no ignored test in the fixture).

### 2026-10-09 — Hand-over 3: runner tests in CI

**Requirement:** CI runs every test added to the repo (CLAUDE.md §8); the real-JVM tests must
not be skipped silently in CI.

- File: `.github/workflows/ci.yml`, new job `runner` (Temurin JDK 8, Python 3.11, env
  `FLAKETRACE_REQUIRE_JVM=1`).
- Local check: the workflow parses with PyYAML into jobs `['fixture-build', 'python-eval', 'runner']`.
- Local check of the CI switch, with `java`/`javac`/`mvn` removed from `PATH`:
  without the switch → `OK (skipped=1)`; with `FLAKETRACE_REQUIRE_JVM=1` →
  `RuntimeError: FLAKETRACE_REQUIRE_JVM is set but ['java', 'javac', 'mvn'] not on PATH`,
  `FAILED (errors=1)`.
- GitHub Actions result: run `37957537495` on PR #10 (commit `1a7527e`), 2026-10-09 — all three
  jobs succeeded. Job `runner` (Temurin JDK 8): `Ran 17 tests in 16.911s — OK`.
  https://github.com/zoyaahmad428/FlakeTrace/actions/runs/37957537495
  First run of the runner on JDK 8: the F1 checks pass there too (victim fails with
  `java.lang.AssertionError`, stack ending at `odfixture.ConfigVictimTest.expectsDefaultMode:10`).
  This shows assertion failures normalise the same on JDK 8 and 21; the JDK 8 frame list in the
  unit tests is hand-written, not captured from a run. With `FLAKETRACE_REQUIRE_JVM=1` a skip would have failed the job, so the real-JVM tests ran.

### 2026-10-09 — Final review fixes (W6)

**Requirement:** a fresh-context review of the whole branch (Claude, separate agent) found no
critical issues and four important ones; three needed code fixes, one a docs correction.

- New test asset: `runner/tests/resources/ProbeTest.java` (compiled by the tests into a temp
  directory against the fixture's own JUnit jar; the fixture itself is not touched).
- New tests, run **before** the fixes: `Ran 22 tests — FAILED (failures=2, errors=1)`:
  - message containing a form feed → reported `flaketrace.JvmCrash` instead of
    `java.lang.AssertionError` (`splitlines()` split the result line on ``);
  - result line cut off without a newline → parsed as a real failure (`java.lang.Exception`)
    instead of missing;
  - `OrderRunner(..., working_dir=...)` → `TypeError` (tests ran in the caller's directory, so
    `new File("pom.xml")` failed).
  - Already passing (covering behaviour previously tested only with hand-written lines): a real
    `System.exit(3)` mid-order → that test and the next reported `flaketrace.JvmCrash`
    ("code 3" in the message); a real `@Ignore` → `flaketrace.NotExecuted`.
- Fix: split results on `"
"` only and drop the final piece; new `working_dir` argument passed
  as `cwd`.
- After: `py -m unittest -v runner.tests.test_order_runner` → `Ran 22 tests in 21.289s — OK`.
  `git status --short fixtures/` printed nothing.
- Docs correction: JDK-internal frames above the stack cut keep JDK-specific line numbers, so
  "same signature on JDK 8 and 21" holds for assertion failures only. ADR-003, `runner/README.md`,
  the four-point note and the CI entry above were reworded.
- Deferred (minor, not fixed): harness temp directory is not deleted; unused stdout/stderr are
  decoded as strict UTF-8; stdin is read while tests run; result index is not cross-checked
  against the test name; `ClassNotFoundException` stacks contain JDK class-loader frames.
- JDK 8: GitHub Actions run `37959672072` on PR #10 (commit `3579e47`), 2026-10-09 — all three
  jobs succeeded; job `runner` (Temurin JDK 8): `Ran 22 tests in 17.2s — OK`.
  https://github.com/zoyaahmad428/FlakeTrace/actions/runs/37959672072

## W7 — diagnosis runs

Design: [[03-Design/decisions/ADR-004-w7-diagnosis-runs]].

### 2026-10-09 — Task 1: source-integrity check

**Requirement:** report-schema `source_integrity` — FlakeTrace must leave the analysed project's
source unchanged, and show it (ADR-001, panel action on code modification).

- Files: `runner/integrity.py` (`snapshot`, `compare`, `SourceIntegrity`),
  `runner/tests/test_integrity.py`.
- Command: `py -m unittest -v runner.tests.test_integrity` (Windows 11, Python 3.14).
- Before the code existed: `ModuleNotFoundError: No module named 'runner.integrity'`.
- Result: `Ran 4 tests in 0.054s — OK`: unchanged project passes; a changed, an added and a
  removed file are each named (`changed: src/main/A.java; added: src/main/B.java; removed:
  pom.xml`); `target/` and `.git/` are ignored; a nested folder named `target` is still hashed.
- Limitations: only the top-level `target/` is skipped — a multi-module project's
  `module/target/` would be hashed, so building it during a diagnosis would show as "changed".
  Not relevant for the single-module fixture; revisit for real projects.
