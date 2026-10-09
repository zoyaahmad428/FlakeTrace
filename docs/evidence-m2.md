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
