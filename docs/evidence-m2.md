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

### 2026-10-09 — Task 2: execution record

**Requirement:** report-schema `execution_record_reference` — a record of every run backing a
diagnosis.

- Files: `runner/recording.py` (`RecordingRunner`), `runner/tests/test_recording.py`;
  `.gitignore` now ignores `flaketrace-records/`.
- Command: `py -m unittest -v runner.tests.test_recording`
- Before the code existed: `ModuleNotFoundError: No module named 'runner.recording'`.
- Result: `Ran 2 tests in 0.028s — OK`: the header is line 1 (and the record's folder is
  created if missing); each run is one line with its step label, order, every test's outcome
  and failure signature, start time and duration; results pass through unchanged.
- Uses M3's `FakeOrderRunner` from `eval/tests/fake_runner.py` (test code only).
- Limitations: the record is not yet produced by a real diagnosis — that comes with
  `diagnose.py` (Task 5).

### 2026-10-09 — Task 3: discover the original order

**Requirement:** ADR-004 step 2 — when no order is given, use the order Maven Surefire would run
(the fixture sets `runOrder=alphabetical`), with each class's methods in JUnit's own order.

- Files: `runner/harness/FtHarness.java` (new `--list` mode), `runner/order_runner.py`
  (`OrderRunner.list_methods`, `java_version`), `runner/discovery.py`,
  `runner/tests/test_discovery.py`.
- Command: `py -m unittest -v runner.tests.test_discovery runner.tests.test_order_runner`
- Before the code existed: `ModuleNotFoundError: No module named 'runner.discovery'`.
- Result: `Ran 28 tests in 43.807s — OK` (6 discovery tests + the 22 W6 tests, unchanged).
- Real discovered order of `fixtures/od-fixture` (13 methods):
  `ConfigPolluterTest#pollute, ConfigVictimTest#expectsDefaultMode, FeaturePolluterTest#enableTurbo,
  FeatureVictimTest#expectsTurboDisabled, MathUtilTest#squaresANumber, MathUtilTest#addsTwoNumbers,
  NegativeAloneFailTest#alwaysFails, NegativeFlakyTest#sometimesFails,
  StringUtilTest#detectsPalindrome, StringUtilTest#reversesAString, ToggleAPolluterTest#setFlagA,
  ToggleBPolluterTest#setFlagB, ToggleVictimTest#expectsNotBothFlagsSet` (package `odfixture.`).
  Inside `MathUtilTest`, JUnit runs `squaresANumber` before `addsTwoNumbers` — neither source nor
  alphabetical order (JUnit 4's default method sorter), which is why methods come from JUnit.
- Classes JUnit cannot run are left out: `odfixture.Config` (no tests) and a missing class give
  an empty list. A missing `target/test-classes` gives no classes.
- `git status --short fixtures/` printed nothing.
- Limitations: Surefire 2.22's default `runOrder` is `filesystem`; for a project that keeps the
  default, pass `original_order` explicitly. Parameterised tests are not listed (ADR-003 scope).

### 2026-10-09 — Task 4: reproduce, polluter search, repeat

**Requirement:** ADR-004 steps 3–6 — a reference signature from the original order, one-by-one
search for a single polluter (priority list first), and matching / any-signature counts over
`n` runs.

- Files: `runner/search.py` (`reproduce`, `candidate_order`, `find_polluter`,
  `SYNTHETIC_PREFIX`), `runner/verify.py` (`repeat`), `runner/tests/test_search.py`.
- Command: `py -m unittest -v runner.tests.test_search`
- Before the code existed: `ModuleNotFoundError: No module named 'runner.search'`.
- Result: `Ran 9 tests in 0.001s — OK` (M3's `FakeOrderRunner`, no JVM): first real failure
  becomes the reference; a `flaketrace.JvmCrash` is never the reference; no failure in all
  attempts → `None`; candidates in original order or priority-first (duplicates, unknown and
  later tests ignored); the first matching candidate wins and runs are counted; a failure with a
  different signature is not a polluter; `repeat` counts 2 matching / 4 any of 5 scripted runs.
- Mutation check: replacing the crash rule with `if True:` → `test_crash_is_never_taken_as_the_reference`
  FAILED; file restored (byte-identical) → OK.
- Limitations: single polluters only — multi-polluter cases are W10's (ADR-004).

### 2026-10-09 — Task 5: `diagnose()` end to end on the fixture

**Requirement:** ADR-004 as a whole — raw evidence for each fixture case, checked against
`fixtures/od-fixture/ground_truth.json` (written before any run).

- Files: `runner/diagnose.py` (`DiagnosisRuns`, `run_steps`, `diagnose`),
  `runner/tests/test_diagnose.py` (7 `run_steps` tests with M3's `FakeOrderRunner`, 5 real cases).
- Before the code existed: `ModuleNotFoundError: No module named 'runner.diagnose'`.
- First real run: `Ran 12 tests in 99.860s — FAILED (failures=1)`: N2 returned `NOT_REPRODUCED`
  (never failed in 40 attempts of the original order). Investigation: N2 then failed 0/40 alone
  and 0/40 in the full order; a probe printed `System.nanoTime() % 1000` as a multiple of 100 on
  every call, and `[System.Diagnostics.Stopwatch]::Frequency` = `10000000` (10 MHz). So N2 could
  not fail on this laptop at that time, although the design spike earlier the same day saw 18/60
  failures alone — the cause of that drift was not established. The diagnosis code was right; the
  test's assumption was wrong. The N2 test now checks that no polluter is ever blamed and accepts
  `NOT_REPRODUCED` when N2 never fails (ADR-004 updated).
- After: `py -m unittest -v runner.tests.test_diagnose` → `Ran 12 tests in 92.448s — OK`.
- Real results, one `diagnose()` per case (Windows 11, JDK 21.0.9, Maven 3.10.0):

| Case | n | Time | Status | Polluter | Sequence | Alone | Search runs | Integrity | Record lines |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | 20 | 23.3 s | `POLLUTER_FOUND` | `ConfigPolluterTest#pollute` | 20/20 (any 20) | 0/20 | 1 | passed | 43 |
| F2 | 5 | 13.5 s | `POLLUTER_FOUND` | `FeaturePolluterTest#enableTurbo` | 5/5 | 0/5 | 3 | passed | 15 |
| F3 | 5 | 16.7 s | `NO_SINGLE_POLLUTER` | — | 5/5 (original order) | 0/5 | 12 | passed | 24 |
| N1 | 20 | 16.3 s | `VICTIM_FAILS_ALONE` | — | 20/20 | 20/20 | 0 | passed | 22 |
| N2 | 20 | 15.9 s | `NOT_REPRODUCED` | — | 0/20 (any 0) | not run | 0 | passed | 21 |

  F1 and F2 find the ground-truth polluter; F3 is the documented two-polluter case for W10; N1
  matches; N2's ground truth (`VICTIM_FAILS_ALONE`) assumes it fails at all — on this machine it
  did not (see above). Record lines = 1 header + one per JVM run.
- Mutation check: changing `if alone_successes >= 1:` to `>= 100` →
  `test_victim_failing_alone_stops_before_the_search` FAILED; restored (byte-identical) → OK.
- Full runner suite: `Ran 55 tests in 128.412s — OK`. `git status --short fixtures/` empty.
- Limitations: see [[04-Implementation/diagnosis-runs]] §3 — single polluters only, spurious
  polluter possible for a rarely-failing victim, `NOT_REPRODUCED` has `alone_n = 0` (W9 must
  handle), discovery assumes alphabetical order. JDK 8 (CI) not yet run.
- **For Member 3:** N2's failure rate is platform-dependent (`System.nanoTime()` parity); its
  ground-truth outcome assumes it fails. Raised as a note, not edited (fixtures are M3's).

### 2026-10-09 — W7 CI result and final review fixes

**CI:** GitHub Actions run `37971869749` on PR #11 (commit `1c1b329`) — all three jobs succeeded
(`runner`, `fixture-build`, `python-eval`). The `runner` job's "Runner tests" step (JDK 8,
Linux, 55 tests at that commit) took 60 s by the step timestamps. Its exact `Ran …` line:
not recorded for that run. The next run, `37973949489` on commit `6dccd97` (with the final
review fixes, 57 tests), passed all three jobs; job `runner` (JDK 8, Linux): `Ran 57 tests in
66.894s — OK` (line copied from the job log by Member 2).
https://github.com/zoyaahmad428/FlakeTrace/actions/runs/37973949489
https://github.com/zoyaahmad428/FlakeTrace/actions/runs/37971869749

**Final review** (separate reviewer agent, whole branch): no critical issues; three important:
1. `NOT_REPRODUCED` stored crash/timeout attempts in `sequence_any_failures`, while ADR-004 said
   0. The code is kept (a sequence that only crashed should read as `SIGNATURE_MISMATCH`); ADR-004,
   `runner/README.md` and the four-point note now say so. New test
   `test_crash_only_original_order_counts_as_failed_but_not_reproduced` pins it (passed on first
   run — it documents existing behaviour).
2. A `record_dir` inside the analysed project made the integrity check fail (the reviewer
   reproduced `added: flaketrace-records/r.jsonl`). New test
   `test_record_folder_inside_the_project_is_refused_before_maven_runs` failed first (Maven was
   reached instead of a `ValueError`); `diagnose()` now refuses such a `record_dir` → passes.
3. Docs still said "CI pending" — corrected by this entry.
- Full runner suite after the fixes: `Ran 57 tests in 121.281s — OK`. `git status --short fixtures/`
  empty.
- Deferred (minor, not fixed): victim first in the order reports `NO_SINGLE_POLLUTER` although
  there were no candidates; duplicate tests in a supplied order are rejected only after Maven
  runs; a header-only record is left when a discovered order lacks the victim; a run that raises
  leaves no record line; a broken symlink in the project crashes hashing; record file names are
  not sanitised (`:` would write an NTFS stream) and are unique only to the second;
  Parameterized/Enclosed classes are not discovered (not yet in ADR-004's Discovery section).

### 2026-10-10 — CI job for Member 1's evidence tests

**Requirement:** Member 1's extractor tests (`evidence/tests/test_extract.py`) ran in no CI job.
Without compiled classes they skip, so 22 of 27 skipped on a fresh checkout. Member 1 asked for
a job with `FLAKETRACE_REQUIRE_JVM=1` and gave the steps (answer to M1-7).
- File: `.github/workflows/ci.yml` — new job `evidence` (JDK 8, Python 3.11): installs
  `eval/requirements.txt`, compiles `fixtures/od-fixture` and `evidence/tests/resources/m1-selftest`,
  runs `python -m unittest -v evidence.tests.test_extract`.
- Before (no classes compiled, local Windows, JDK 21.0.9, Python 3.14):
  `py -m unittest evidence.tests.test_extract` → `Ran 27 tests — OK (skipped=22)`.
- The job's steps run locally: `mvn -B -q -f fixtures/od-fixture/pom.xml test-compile`,
  `mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile`, then
  `FLAKETRACE_REQUIRE_JVM=1 py -m unittest -v evidence.tests.test_extract` →
  `Ran 27 tests in 50.143s — OK`, none skipped.
- Guard check: same command with `FLAKETRACE_JAVAP=C:/nope/javap.exe` →
  `Ran 8 tests — FAILED (failures=4, errors=4)`, so a missing javap fails the job instead of skipping.
- CI on JDK 8: not yet run (runs on the PR).
- Also ticked M2's row in ADR-001 and ADR-002.

### 2026-10-10 — N2 test back to `VICTIM_FAILS_ALONE`

**Requirement:** Member 3 replaced N2's `System.nanoTime()` parity with `new Random().nextBoolean()`
(PR #14), so N2 now fails ~50% on every platform. The W7 N2 test (accepting `NOT_REPRODUCED`)
and the docs saying "N2 may end `NOT_REPRODUCED` on Windows" were out of date.
- Real runs first (local Windows, JDK 21.0.9): `diagnose(fixtures/od-fixture,
  NegativeFlakyTest#sometimesFails, n=20)` three times → `VICTIM_FAILS_ALONE` each time, no
  polluter, alone failures 16/20, 9/20, 11/20, source integrity passed.
- File: `runner/tests/test_diagnose.py` — `test_n2_intermittent_failure_fails_alone_and_blames_no_polluter`
  expects `VICTIM_FAILS_ALONE`, `polluters == []`, alone ≥ 1. Chance of 20 runs with no failure
  at 50%: 0.5^20 ≈ 1e-6.
- Command: `py -m unittest runner.tests.test_diagnose.TestDiagnoseOnFixture.test_n2_intermittent_failure_fails_alone_and_blames_no_polluter`
  → `Ran 1 test in 17.082s — OK`.
- Mutation check: `if alone_successes >= 1:` changed to `>= 100` in `runner/diagnose.py` → the test
  FAILED with `'POLLUTER_FOUND' != 'VICTIM_FAILS_ALONE'`: without the alone check, the search
  blamed an earlier test for N2's random failure. Restored; `git diff runner/diagnose.py` empty.
- Full runner suite: `Ran 57 tests in 127.173s — OK`.
- **CI on this branch** (commit `b38479c`): job `runner` (JDK 8, Linux) → `Ran 57 tests in
  63.940s — OK` (line copied from the job log by Member 2). The tightened N2 test therefore also
  passes on Linux/JDK 8.
- **CI for PR #20 (`evidence` job):** `Ran …` line not recorded yet.
- Docs updated: ADR-004 (N2 row and an update note), [[04-Implementation/diagnosis-runs]],
  demo plan Runner row, claims E9.

### 2026-10-10 — CI results for PR #20 and PR #22 (recorded late)

- PR #22 (N2 test) after merging `main` into it (commit `cf8da48`): job `runner` (JDK 8, Linux) →
  `Ran 57 tests in 66.969s — OK`; job `evidence` → `Ran 30 tests in 24.771s — OK` (30 = 27 +
  Member 1's ground-truth test from PR #23, so the new test runs in CI). Lines copied from the job
  logs by Member 2.

### 2026-10-10 — W9 CLI design (ADR-005)

- Not a run: design only. [[03-Design/decisions/ADR-005-w9-diagnose-cli]] proposes
  `py -m runner diagnose --project … --victim …` and answers I4 (pending M1/M3).
- Facts checked for the ADR: `eval.stats.wilson_interval(5, 5, 0.95)` → lower `0.5655` (< 0.70,
  so `VERIFIED` tests need n = 20); `eval/schema_validator.py` imports `jsonschema` at load; the
  `runner` CI job has no `pip install` step; `evidence.extract.DEFAULT_DEPTH` = 2.

### 2026-10-10 — W9 Task 1: `py -m runner diagnose` (fast tests)

**Requirement:** ADR-005 — one command from a failing test to a report file; exit codes 0/1/2/3.
- Files: `runner/cli.py` (`main`, `run_diagnose`, `resource_fields`, `summary`), `runner/__main__.py`,
  `runner/tests/test_cli.py`; `.github/workflows/ci.yml` (`runner` job installs `eval/requirements.txt`).
- Probe first: `py -m` runs `__main__.py` of a namespace package (no `__init__.py`, like `runner/`)
  both from its folder and via `PYTHONPATH` from another folder → `main ran`, exit 0 (Python 3.14).
- Tests written first: `py -m unittest runner.tests.test_cli` → `ModuleNotFoundError: No module
  named 'runner.cli'`. After the code: `Ran 11 tests in 0.108s — OK` (no JVM; `diagnose` replaced
  with `unittest.mock.patch` in the tool-error and report tests only).
- Mutation check: evidence step forced on (`if True else None`) → both report tests FAILED
  (`1 != 0`, `1 != 3`); restored from a copy → 11 OK.
- Full runner suite: `Ran 68 tests in 124.206s — OK`. `git status --short fixtures/` empty.
- Limitation: real Maven/JVM/javap runs of the command are Task 2.

### 2026-10-10 — W9 Task 2: the diagnose command end to end on the fixture

**Requirement:** ADR-005 verification plan — real Maven/JVM/javap runs through the command.
- File: `runner/tests/test_cli.py`, class `TestCliOnFixture` (5 tests).
- Command: `py -m unittest -v runner.tests.test_cli.TestCliOnFixture` (local Windows, JDK 21.0.9)
  → `Ran 5 tests in 87.535s — OK`:
  - F1 as a separate process (`python -m runner diagnose …`, run from a temp folder with
    `PYTHONPATH` = repo root, default `--records`) → exit 0, `VERIFIED`, resource
    `static-field odfixture.Config mode`, 20/20 reproduced, 0/20 alone; the record path in the
    report is relative, exists, and the report sits next to it;
  - F2 (n = 20) → `VERIFIED`, `system-property odfixture.turbo`, read in
    `odfixture.FeatureFlags#isTurboEnabled@2` (depth 2);
  - F3 (n = 3) → exit 3, `No report: NO_SINGLE_POLLUTER`, no report file;
  - N1 (n = 5) → exit 0, `UNRESOLVED(VICTIM_FAILS_ALONE)`, no polluter;
  - `odfixture.ConfigVictimTest#noSuchTest` → exit 2 naming the victim, no report.
- These tests passed on their first run because Task 1's code existed. Mutation check:
  `fields = None` in place of the evidence step → `test_f2_depth_two_edge` FAILED
  (`'UNRESOLVED' != 'VERIFIED'`); restored from a copy, `git diff runner/cli.py` empty.
- By hand from the repo root:
  `py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode`
  → exit 0:

```
VERIFIED  odfixture.ConfigVictimTest#expectsDefaultMode
  polluter:   odfixture.ConfigPolluterTest#pollute
  resource:   static-field odfixture.Config mode (write odfixture.ConfigPolluterTest#pollute@1 -> read odfixture.ConfigVictimTest#expectsDefaultMode@1)
  reproduced: 20/20 (lower bound 0.839)   alone: 0/20
  report:     flaketrace-records\20261009T213516Z-odfixture.ConfigVictimTest#expectsDefaultMode.report.json
  record:     flaketrace-records\20261009T213516Z-odfixture.ConfigVictimTest#expectsDefaultMode.jsonl
```

- Full runner suite: `Ran 73 tests in 212.449s — OK`. `git status --short fixtures/` empty.
- Limitations: the record path uses `\` on Windows (relative, not OS-neutral); must run from the
  repo root or with it on `PYTHONPATH`. CI on JDK 8: not yet run (runs on the PR).
