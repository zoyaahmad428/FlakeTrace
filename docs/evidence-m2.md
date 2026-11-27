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
    `java.lang.AssertionError` (`splitlines()` split the result line on `\f`);
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

### 2026-10-10 — W9 final review and fix

**Review:** separate reviewer agent on the whole branch (`6693965..77b0e31`), against ADR-005 and
the plan: no critical; one important; six minor (deferred, listed below). The five review-focus
inputs all behaved as specified (the reviewer probed them).
- **Important — fixed:** the CLI caught every `ValueError`/`RuntimeError` from `diagnose()`, so an
  internal bug (e.g. `run_ordered`'s "same test more than once", a `UnicodeDecodeError`, a
  `RecursionError`) would print as a one-line user/tool error and lose its traceback — against
  ADR-005. Fix: `runner.diagnose.DiagnoseInputError(ValueError)` for the three input checks,
  `runner.order_runner.ToolError(RuntimeError)` for a missing tool or harness compile failure; the
  CLI catches only those.
- New test `test_internal_errors_are_not_hidden_as_input_or_tool_errors`. With the classes added but
  the CLI unchanged it FAILED: `AssertionError: ValueError not raised`. After narrowing the CLI → OK.
  `test_diagnose` bad-input tests now expect `DiagnoseInputError`.
- Full runner suite: `Ran 74 tests in 210.101s — OK`.
- Six minors listed by the reviewer: fixed or decided in the next entry.

### 2026-10-10 — W9 review minors fixed (Member 2 asked for every one that can cause trouble later)

| # | Minor | Decision | Test (failed first) |
| --- | --- | --- | --- |
| 1 | `--records` names an existing file → traceback after Maven | `diagnose()` refuses it before Maven (`DiagnoseInputError`) | `test_record_folder_that_is_a_file_is_refused_before_maven_runs` — errored before the fix |
| 2 | unknown victim leaves a header-only record | `diagnose()` checks the victim against the discovered order before creating the recorder | `test_unknown_victim_exits_2` now asserts no record file; with the new check removed it FAILED (a `.jsonl` was left) |
| 3 | victim string not checked for file names | CLI accepts only `[\w.$]+#[\w$]+` (Java names, no spaces) → else exit 2 | `test_malformed_victims_exit_2` with `" pkg.VictimTest#v"`, `"…#v:x"`, `"…#a#b"`, `"pkg.Victim Test#v"`, `"…#<v>"` — FAILED (`3 != 2`) before |
| 4 | `summary()` crashed on a resource with null locations | location part printed only when both exist | `test_summary_survives_a_resource_without_locations` — `TypeError` before |
| 5a | discovery `TimeoutExpired` → traceback | CLI exit 1: `<tool> timed out after <s> s on <project>` | `test_discovery_timeout_exits_1` — errored before |
| 5b | schema `ValidationError` → traceback | **kept on purpose**: only a pipeline bug causes it; ADR-005 keeps bugs loud | — |
| 6 | no fast test of the summary resource line | added | `test_summary_shows_the_resource_and_both_locations` (passed at once: documents existing behaviour) |

- Commands: `py -m unittest runner.tests.test_cli.TestInputErrors runner.tests.test_cli.TestToolErrors
  runner.tests.test_cli.TestReports runner.tests.test_diagnose.TestRunSteps` → before the fixes
  `FAILED (failures=1, errors=3)`; after `Ran 25 tests — OK`. Real `test_unknown_victim_exits_2` → OK.
- Full runner suite: `Ran 78 tests in 233.104s — OK`. `git status --short fixtures/` empty.

### 2026-10-10 — W9 CI result (PR #26)

- PR #26 (`m2/w9-cli`) after merging `main` into it (commit `6caaaaf`): job `runner` (JDK 8, Linux)
  → `Ran 78 tests in 82.588s — OK` (line copied from the job log by Member 2). Same count as locally,
  so the 5 real CLI runs (F1 as a separate process, F2, F3, N1, unknown victim) pass on Linux/JDK 8 too.
- Merge conflicts resolved in `claims-ledger.md` (our claim renumbered E10 → E12; M1 had added
  E10/E11), `demo-plan.md`, `iteration-plan.md`, `members.md` — newer M1/M3 rows kept, M2 rows added.

### 2026-10-10 — Claim E1: JUnit 3 through our harness, and wording

**Requirement:** claim E1 said JUnit 3 is supported "via the JUnit38 adapter" and that Surefire runs
the tests. The only backing was the POC, which ran under Surefire, and FlakeTrace runs tests with its
own JUnitCore harness (ADR-003). Member 1 suggested new wording.
- Probe first (scratchpad, not committed): a JUnit 3 `TestCase` compiled against the fixture's JUnit
  and run through `OrderRunner` → `list_methods` found `testPollute`, `testVictim`; the victim passed
  alone; after the polluter it failed with `junit.framework.AssertionFailedError`, stack ending at the
  test method.
- File: `runner/tests/resources/LegacyJUnit3Test.java`, compiled in `TestOrderRunnerOnProbes` next to
  `ProbeTest.java`. Tests `test_junit3_methods_are_listed`,
  `test_junit3_victim_passes_alone_and_fails_after_its_polluter`.
- Command: `py -m unittest -v runner.tests.test_order_runner.TestOrderRunnerOnProbes` (local
  Windows, JDK 21.0.9) → `Ran 6 tests in 12.764s — OK`. Both JUnit 3 tests passed on first run:
  they document existing behaviour.
- Mutation check: `run_ordered` sent the order reversed → the pollution test FAILED
  (`True is not false`, the victim passed); restored, `git diff runner/order_runner.py` empty.
- Full runner suite on this branch (from `main`, without W9): `Ran 59 tests in 130.392s — OK`.
- Docs: claim E1 and its source `docs/02-Requirements/scope-boundary.md` (Surefire removed, Maven
  for build and classpath, JUnitCore), `runner/README.md` limitations.
- Limitation: the "Linux container" part of E1 is a committed target; nothing runs in one yet.
- CI on the E1 PR (`m2/e1-junit3`): job `runner` (JDK 8, Linux) → `Ran 59 tests in 64.239s — OK`
  (line copied from the job log by Member 2), so the JUnit 3 test also passes on Linux/JDK 8.

### 2026-10-10 — W10 design (ADR-007)

- Not a run: design only. [[03-Design/decisions/ADR-007-w10-ddmin-minimisation]] proposes `ddmin`
  over the tests before the victim when W7's one-by-one search finds nothing, `POLLUTER_FOUND` with
  one or more polluters, a new `minimise_runs` field, and a strict evidence rule for several
  polluters (every polluter needs an edge for `VERIFIED`). Needs M1/M3 confirmation of the report rule.
- Numbered ADR-007 because Member 1's PR #28 added ADR-006 (evidence depth 1–5, proposed) the same day.

### 2026-10-10 — W10 Task 1: `ddmin`

**Requirement:** ADR-007 — shrink the tests before the victim to a 1-minimal polluter set.
- Files: `runner/minimise.py` (`ddmin(runner, prefix, victim, reference) -> (minimal, runs)`),
  `runner/tests/test_minimise.py` (11 tests, `FakeOrderRunner`).
- Tests written first: `py -m unittest runner.tests.test_minimise` → `ModuleNotFoundError: No module
  named 'runner.minimise'`. After the code: `Ran 11 tests in 0.010s — OK`.
- Run counts measured on the fakes: F3's shape (2 required tests in 12) → 25 runs; 2 required tests
  in a 100-test prefix → 48 runs (one run per test would be 100).
- Mutation check: complement step removed → 7 of 11 FAILED (incl. the F3-shaped test and
  1-minimality); restored from a copy → 11 OK.
- Full runner suite: `Ran 91 tests in 221.797s — OK`.
- Limitation: not wired into `diagnose()` yet (Task 2).

### 2026-10-10 — W10 Task 2: `run_steps` minimises when no single polluter is found

- File: `runner/diagnose.py` — step 4 calls `ddmin` when `find_polluter` returns nothing and the
  prefix is not empty; `POLLUTER_FOUND` with one or more polluters; new `minimise_runs`; record step
  `"minimise"`.
- Tests first (`runner/tests/test_diagnose.py`): `py -m unittest runner.tests.test_diagnose.TestRunSteps`
  → `FAILED (failures=2, errors=1)`: `'NO_SINGLE_POLLUTER' != 'POLLUTER_FOUND'`, `'minimise' not found
  in [...]`, `no attribute 'minimise_runs'`. After the code → 12 OK.
- Real F3 (local Windows, JDK 21.0.9, `diagnose(..., n=5)`): `POLLUTER_FOUND`, polluters
  `ToggleAPolluterTest#setFlagA`, `ToggleBPolluterTest#setFlagB` (= ground truth); search 12 runs,
  **minimise 9 runs**, verify 5/5, alone 0/5, source integrity passed.
- The full suite then showed one failure the plan had not foreseen: `test_cli`'s F3 test still
  expected exit 3 (`0 != 3`) — F3 now gets a report. Updated in this task (exit 0, `VERIFIED`, both
  polluters, `flagA`) → `Ran 1 test in 34.227s — OK`.
- Full runner suite: `Ran 93 tests in 245.061s — OK`. `git status --short fixtures/` empty.

### 2026-10-10 — W10 Task 3: report several polluters; F3 end to end

**Requirement:** ADR-007 § Evidence and report — evidence per polluter; `VERIFIED` only if every
polluter has an edge; the first shown, the others named in `limitations`, M1's fixed lines once.
- File: `runner/cli.py` — `resource_fields` analyses the victim once and each polluter, then
  `combine_fields(pairs)`; the exit-3 message for `NO_SINGLE_POLLUTER` now says the victim is first.
- Real edges checked before writing tests: F3's pairs give `odfixture.Toggles#flagA` (A) and
  `#flagB` (B); every pair carries the same 7 fixed limitation lines (hence the de-duplication).
- Tests first: `py -m unittest runner.tests.test_cli.TestCombineFields` → `ImportError: cannot import
  name 'combine_fields'`. After the code: fast CLI tests OK; real `test_f3_two_polluters_verified`
  (n = 20, now also checking the `flagB` limitation and the summary line) → `Ran 1 test in 33.936s — OK`.
- Mutation check: evidence for the first polluter only (`runs.polluters[:1]`) → the real F3 test
  FAILED (no `flagB` line); restored from a copy.
- Full runner suite: `Ran 97 tests in 238.770s — OK`. `git status --short fixtures/` empty.
- By hand from the repo root, exit 0:

```
VERIFIED  odfixture.ToggleVictimTest#expectsNotBothFlagsSet
  polluter:   odfixture.ToggleAPolluterTest#setFlagA, odfixture.ToggleBPolluterTest#setFlagB
  resource:   static-field odfixture.Toggles flagA (write odfixture.ToggleAPolluterTest#setFlagA@1 -> read odfixture.ToggleVictimTest#expectsNotBothFlagsSet@0)
  reproduced: 20/20 (lower bound 0.839)   alone: 0/20
  report:     flaketrace-records\20261010T104124Z-odfixture.ToggleVictimTest#expectsNotBothFlagsSet.report.json
  record:     flaketrace-records\20261010T104124Z-odfixture.ToggleVictimTest#expectsNotBothFlagsSet.jsonl
```

  The report's `limitations` (9 lines, none duplicated) include "Polluter
  odfixture.ToggleBPolluterTest#setFlagB: shared resource odfixture.Toggles#flagB is not shown in this
  report".
- Docs: `runner/README.md`, [[04-Implementation/diagnose-cli]], demo plan (F3 row, known
  limitations, Runner row), iteration plan W10, members, claims E9/E12 updated and new E14 (numbered E13 until merging main, where M1 added E13), an update
  note in ADR-005. `fixtures/od-fixture/ground_truth.json`'s F3 note ("needs W10") is M3's — not edited.
- CI on JDK 8: not yet run (runs on the PR).

### 2026-10-10 — W10 final review and fixes

**Review:** separate reviewer agent on the whole branch (`a7ced91..8a16388`) against ADR-007 and the
plan: no critical; three important; six minor. All five review-focus items held (the reviewer probed them).
- **Important 1 — fixed:** a victim that failed only once (in the reproduce run) made `ddmin` treat the
  whole prefix as failing and blame **every earlier test** (reviewer's probe: 20 bystanders); with one
  earlier test it blamed a test the search had just seen pass. Fix in `run_steps`: run the full order
  once more before `ddmin` and minimise only if it fails again; skip `ddmin` for a one-test prefix.
  Tests `test_flaky_failure_is_not_blamed_on_the_whole_prefix` and
  `test_one_test_prefix_that_passed_in_the_search_blames_nothing` FAILED before
  (`'POLLUTER_FOUND' != 'NO_SINGLE_POLLUTER'`) and pass after; the two-polluter test's counts now
  include the re-check (`minimise_runs` 3, 10 calls).
- **Important 3 — fixed:** two polluters writing the same resource got a line saying that resource is
  not shown, although it was the one shown. `combine_fields` skips edges on the shown resource and takes
  only M1's fixed lines from later polluters (which also fixes minor 4, a resource named twice). Tests
  `test_resource_written_by_both_polluters_is_not_called_hidden` and
  `test_extra_resource_of_a_later_polluter_is_named_once` FAILED before (`True is not false`, `2 != 1`).
- **Important 2 — ruling, no code change:** with mixed evidence our lines name the found edges while
  M3's generic line says no edge was found; that line is in `eval/` (M3). Recorded in ADR-007; M3 asked
  to make it conditional.
- Docs honesty (minors 5, 6): ADR-007's cost sentence corrected (the search still runs once per test);
  claim E14 (then E13) status SETTLED → OPEN until CI and M1/M3 agreement. The exit-3 message for
  `NO_SINGLE_POLLUTER` now says the failure did not come back and is likely flaky (minor 9).
- Real F3 after the fix (`diagnose(..., n=5)`): `POLLUTER_FOUND`, same polluters, search 12, minimise
  **10** (1 re-check + 9 `ddmin`), verify 5/5.
- Full runner suite: `Ran 101 tests in 236.259s — OK`. `git status --short fixtures/` empty.
- Deferred minor: `minimise_runs` is not shown in the report or summary (noted in ADR-007).

### 2026-10-10 — W10: `analyse_pair` per polluter (ADR-006 follow-up), M3's flag, F3 offsets

**Requirement:** ADR-006 (accepted, implemented by Member 1 in PR #34) — callers switch to
`analyse_pair`, which deepens a pair only when nothing is found at depth 2; Member 2 promised this in
the ADR. With several polluters each pair deepens on its own, and Member 1's depth warning covers only
the shown edge. Member 3's PR #38 added an optional `any_edge_found` flag to `assemble_report`
(review finding 2).
- File: `runner/cli.py` — `resource_fields` calls `analyse_pair(classes, polluter, victim)` once per
  polluter; `combine_fields` adds "(evidence at depth N, above the default 2)" to a named edge deeper than
  2 (same measure as `report_fields`) and sets `any_edge_found` in the mixed case.
- Tests first (`runner/tests/test_cli.py`): `test_deep_evidence_of_a_later_polluter_is_named_with_its_depth`,
  `test_mixed_evidence_report_does_not_also_say_no_edge_was_found` (through M3's real `assemble_report`),
  `test_resource_fields_asks_analyse_pair_once_per_polluter` → before the code: 1 failure, 2 errors
  (`KeyError: 'any_edge_found'`, no `analyse_pair` in `runner.cli`, line not found). After → OK. The
  existing "skips the extractor" test now patches `analyse_pair`.
- Real CLI runs on the fixture (`TestCliOnFixture`, F1/F2/F3/N1/unknown victim): `Ran 5 tests in
  129.780s — OK` — the fixture stays at depth 2 as Member 1 measured.
- **F3 offsets by hand** (`javap -c -p`, JDK 21.0.9, `fixtures/od-fixture/target`): `ToggleAPolluterTest.setFlagA`
  `1: putstatic Toggles.flagA`; `ToggleBPolluterTest.setFlagB` `1: putstatic Toggles.flagB`;
  `ToggleVictimTest.expectsNotBothFlagsSet` `0: getstatic Toggles.flagA`, `6: getstatic Toggles.flagB`.
  The F3 report shows write `setFlagA@1`, read `expectsNotBothFlagsSet@0` — match. (Promised in a
  comment on PR #31, contract question 4.)
- Full runner suite: `Ran 104 tests in 246.800s — OK`.

### 2026-10-10 — W10 CI result

- W10 PR (`m2/w10-minimise`, commit `539b2dc`): job `runner` (JDK 8, Linux) -> `Ran 104 tests in 114.111s — OK`
  (line copied from the job log by Member 2). Same count as locally, so ddmin, the re-check, the
  per-polluter `analyse_pair` and the real F3 report also pass on Linux/JDK 8. Claim E14 now cites it;
  it stays OPEN until Member 1 and Member 3 confirm ADR-007.

### 2026-10-10 — W10 follow-up: minimisation shown in the command's summary

**Requirement:** the deferred W10 review minor — `minimise_runs` reached neither the report nor the
summary. The report has no field for it (schema, Member 3's contract), so only the summary changes:
when `ddmin` found the polluters it says how far the order was shrunk and that the result is
1-minimal, not necessarily the minimum (`parameter-provenance.md`).
- File: `runner/cli.py` — `summary(report, report_path, minimised=None)`; `run_diagnose` passes
  `(earlier tests, minimise_runs)` only when `minimise_runs > 0` and polluters were found.
- Tests first: `test_summary_names_the_minimisation_when_ddmin_ran`,
  `test_command_shows_the_minimisation_only_when_ddmin_found_polluters` → before the code
  `TypeError: summary() got an unexpected keyword argument 'minimised'` and the line not found; after → OK.
  The real F3 CLI test also checks the line.
- By hand (local Windows, JDK 21.0.9):
  `py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ToggleVictimTest#expectsNotBothFlagsSet`
  → exit 0, `VERIFIED`, new line `minimised:  12 earlier tests -> 2 polluters in 10 runs (1-minimal, not
  necessarily the minimum)`. F1/F2/N1 summaries unchanged (no `ddmin`).
- Full runner suite: `Ran 106 tests in 230.261s — OK`.
- CI on the PR (`m2/w10-summary`, commit `478d3ac`): job `runner` (JDK 8, Linux) -> `Ran 106 tests in 110.675s — OK`
  (line copied from the job log by Member 2).

### 2026-10-10 — Panel action A7: commit and OS in the execution record

**Requirement:** panel action A7 — "each run records commit, test order, JDK, OS/container, seed,
timestamps". Order (every run line), JDK and timestamps were already recorded; the analysed project's
commit and the OS were not.
- File: `runner/diagnose.py` — `environment(project)` returns `project_commit` (`git rev-parse HEAD` in
  the project folder), `project_dirty` (`git status --porcelain -- .` not empty) and `os`
  (`platform.platform()`); commit/dirty are `None` when the project is not in a git repository or git
  is missing, and the diagnosis carries on. `diagnose()` adds them to the record header.
- Tests first (`runner/tests/test_diagnose.py`): `TestEnvironment` (a folder without git → `None`,
  `None`, the OS; a temp git repo → its commit and `dirty` false, then true after an edit) and the real
  F1 test now checks the header → before the code `ImportError: cannot import name 'environment'`;
  after → OK.
- Mutation checks: header without the fields → F1 test `KeyError: 'project_commit'`; `dirty` always
  false → the git test FAILED (`False is not true`); both restored.
- Real header (F1 by hand, local Windows, JDK 21.0.9): `"project_commit": "15c8a3388f22d3e3a2cac1b3945b701187d45e93"`
  (= `git rev-parse HEAD`), `"project_dirty": false`, `"os": "Windows-11-10.0.26200-SP0"`.
- Full runner suite (branch from main, without the summary PR): `Ran 106 tests in 230.811s — OK`.
- Not applicable, stated rather than faked: **container** (nothing runs in one yet; the Linux container is
  a committed target, claim E1) and **seed** (the runner never shuffles; orders are discovered or given).
- CI on the PR (`m2/panel-actions`, commit `03fe83a`): job `runner` (JDK 8, Linux) -> `Ran 106 tests in 97.388s — OK`
  (line copied from the job log by Member 2), so the header fields are also written on Linux.

### 2026-10-10 — ADR-008 design (NOT_REPRODUCED, given order, valid shuffled orders)

- Not a run: design only. [[03-Design/decisions/ADR-008-not-reproduced-and-order-search]] proposes
  `--order`, up to 31 distinct class-first shuffled orders when the starting order does not reproduce,
  an always-run alone check, and a schema change for Member 3 (`failure_signature` null only for
  `NOT_REPRODUCED`, optional `order_exploration`, `INFRASTRUCTURE_FAILURE`), plus fixture cases F4 and N3.
- Facts checked: `eval.stats.wilson_interval(0, 20, 0.95)` → upper `0.1611`; `(0, 31)` → `0.1103`.
  `docs/01-Literature/references.md`: [3] iDFlakies, [4] iFixFlakies, [5] Rahman et al., [12] Gruber et al.
  — **"An empirical study of flaky tests in Python"**, so the 31-order figure is a Python result; ADR-008
  labels its use for JUnit an assumption.

### 2026-10-11 — Runner tests no longer hardcode the fixture's size (before M3's F4/N3)

**Requirement:** Member 3's ADR-008 branch (`m3/adr008-not-reproduced`, commit `691e2c2`) adds three
fixture test classes (F4, N3). Three of our real-run tests hardcoded counts from today's fixture, so CI's
`runner` job would fail on M3's PR although M3 did nothing wrong.
- Reproduced first, in a temporary worktree of M3's branch (scratchpad, removed afterwards): today's
  `test_f3_two_polluters_are_found_by_minimisation` → `AssertionError: 14 != 12`;
  `test_f3_two_polluters_verified` → `'minimised:  12 earlier tests …' not found`; the full runner suite
  there also showed `test_all_thirteen_fixture_methods_in_alphabetical_class_order` → `16 != 13`.
- Files: `runner/tests/test_diagnose.py` (search runs = earlier tests in the real order),
  `runner/tests/test_cli.py` (the `minimised:` count from the report's `original_failing_order`),
  `runner/tests/test_discovery.py` (renamed `test_every_fixture_test_method_once_in_alphabetical_class_order`:
  expected set = every `@Test` method in the fixture sources, read independently of the discovery code;
  no duplicates; classes alphabetical).
- Mutation check on the discovery test: dropping `*Test` from the include rule → FAILED on the set
  comparison ("items in the second set but not the first"). A first version shared the include rule with
  the code under test and failed only on an empty set — rewritten to be independent.
- Full runner suite: on our branch `Ran 108 tests in 240.907s — OK`; on M3's fixture with these tests
  `Ran 108 tests in 237.031s — OK`.

### 2026-10-11 — ADR-008 Task 1: class-first shuffled orders

**Requirement:** ADR-008 — valid shuffled orders (classes shuffled, then methods within each class,
never interleaved), distinct orders only, honest exhaustion, and a search that stops at the first real
failure.
- Files: `runner/orders.py` (`class_first_shuffle`, `distinct_shuffles`, `search_orders`),
  `runner/tests/test_orders.py` (9 tests, `FakeOrderRunner`).
- Tests first: `py -m unittest runner.tests.test_orders` → `ModuleNotFoundError: No module named
  'runner.orders'`. After the code: 8 passed, 1 error in the test itself (it sorted `TestIdentifier`
  tuples, which are not orderable) — compared as a set plus a length check instead → `Ran 9 tests — OK`.
- Mutation check: a flat shuffle (classes interleaved) → `test_methods_of_a_class_stay_together`
  FAILED; restored from a copy → 9 OK.
- Full runner suite: `Ran 117 tests in 249.541s — OK`.
- Limitation: not wired into `diagnose()` yet (Task 2).

### 2026-10-11 — ADR-008 Task 2: shuffled orders in the diagnosis; alone check always

**Requirement:** ADR-008 — when the starting order never fails for real, try up to 31 distinct shuffled
orders; always run the victim alone; give Member 3's `eval/report.py` the fields it reads.
- Files: `runner/diagnose.py` (shuffle phase, alone always, six `DiagnosisRuns` fields, given-order
  checks, header fields `order_given`/`shuffles`/`seed_base`), `runner/verify.py`
  (`repeat_without_reference`), `runner/recording.py` (`note`, used for the seed on shuffle lines).
- Tests first (`test_recording.py`, `test_diagnose.py`): `py -m unittest runner.tests.test_recording
  runner.tests.test_diagnose.TestRunSteps` → `FAILED (failures=1, errors=9)` (`unexpected keyword
  argument 'shuffles'`, `KeyError: 'seed'`, no `infrastructure_failures`, alone counts `(0, 0, 0)`).
  After → `Ran 33 tests — OK` (with `test_orders`).
- Real runs (local Windows, JDK 21.0.9, `diagnose(..., n=5)`):
  **F4** (`AlwaysEarlyVictimTest#expectsLateFlagUnset`) → `POLLUTER_FOUND`, polluter
  `ZzzLatePolluterTest#setLateFlag` (= ground truth), reproduced by **seed 1 after 2 shuffled orders**,
  5/5, alone 0/5, 18 s. **N3** (`EnvDependentNegativeTest#onlyFailsUnderCI`) → `NOT_REPRODUCED`,
  31 distinct shuffled orders (not exhausted), 0/5 in its order, 0/5 alone, no infrastructure failures, 30 s.
- Mutation checks: shuffle phase skipped → the fake shuffle test and real F4 FAILED; duplicate orders
  counted → `test_small_suite_is_exhausted_honestly` FAILED; both restored from copies.
- Full runner suite: `Ran 127 tests in 293.984s — OK`.

### 2026-10-11 — ADR-008 Task 3: the command — `--order`, `--shuffles`, `--seed`; F4 and N3 reports

**Requirement:** ADR-008 § Command — the real failing order from a file, the shuffle budget and seed,
summary lines, and real reports for F4 and N3 through the command.
- File: `runner/cli.py` — `read_order` / `OrderFileError` (BOM, CRLF, comments allowed; bad line,
  duplicate, missing victim → exit 2), the three options, `orders:`/`bound:` summary lines.
- Tests first: `ImportError: cannot import name 'OrderFileError'`; after → fast CLI tests OK. While
  checking N3's real output, the summary said "given order" although no order was given — a new test
  (`test_summary_says_discovered_order_when_no_order_was_given`) FAILED, then the wording uses
  "discovered" unless `--order` was used → OK.
- Mutation check: the "victim must be in the file" check removed → `test_bad_order_files_are_refused`
  FAILED (`OrderFileError not raised`); restored.
- By hand (local Windows, JDK 21.0.9), exit 0 both:

```
VERIFIED  odfixture.AlwaysEarlyVictimTest#expectsLateFlagUnset
  polluter:   odfixture.ZzzLatePolluterTest#setLateFlag
  orders:     reproduced in shuffled order (seed 1) after 2 shuffled orders
  resource:   static-field odfixture.LateFlag isSet (write odfixture.ZzzLatePolluterTest#setLateFlag@1 -> read odfixture.AlwaysEarlyVictimTest#expectsLateFlagUnset@0)
  reproduced: 20/20 (lower bound 0.839)   alone: 0/20

UNRESOLVED (NOT_REPRODUCED)  odfixture.EnvDependentNegativeTest#onlyFailsUnderCI
  orders:     discovered order 20x, 31 distinct shuffled orders, alone 20x: never failed
  bound:      failure rate in the discovered order < 0.161 (95% Wilson), not proof of reliability
  reproduced: 0/20 (lower bound 0.000)   alone: 0/20
```

  (The N3 lines above are from the run after the wording fix; the first run printed "given order".)
- Full runner suite: `Ran 137 tests in 337.792s — OK`.
- For Member 3: the report's own `limitations` text from `assemble_report` says "runs of the given
  order" even without `--order`; `DiagnosisRuns.order_given` now tells which. Not edited (eval/ is M3's).

### 2026-10-11 — ADR-008 final review and fixes

**Review:** separate reviewer agent on the whole branch (`39b2dff..92b4e96`) against ADR-008 and the
plan: no critical; three important; six minor. The five review-focus items held (BOM/CRLF file, a
two-order suite, victim-first shuffle, `--shuffles 0`, seeds in the record).
- Fixed, each with a test that FAILED first (fast run before the fixes: `FAILED (failures=5, errors=4)`):
  1. alone or shuffle runs that only crashed/timed out were summarised as "never failed" → counted in
     `shuffle_infrastructure_failures` / `alone_infrastructure_failures`; summary says "no real failure
     (N runs crashed or timed out)" (`test_crash_only_alone_and_shuffles_are_counted_not_called_never_failed`,
     `test_summary_names_crashes_instead_of_never_failed`);
  2. an `--order` file in UTF-16 (PowerShell 5.1 `>`) crashed with `UnicodeDecodeError` → read as UTF-16;
     non-text bytes → exit 2 (`test_utf16_order_file_from_powershell_is_read`,
     `test_order_file_that_is_not_text_is_refused_not_a_traceback`);
  3. the unknown-test check had no test → `test_unknown_test_in_a_given_order_is_refused_and_says_why`;
     the message now gives the count and that only Surefire's default includes are discovered;
  4. (re-graded from minor) the starting order was counted as one of the shuffled orders → excluded
     (`test_the_starting_order_is_never_counted_as_a_shuffle`; the two-order and three-class counts
     drop by one);
  5. (re-graded) "(all possible)" claimed exhaustion that is only sampled → "(no further distinct order found)";
  6. (re-graded) for a victim that fails only alone, `original_failing_order` named an order that never
     failed → `[victim]`.
  README: `NO_SINGLE_POLLUTER` can now also follow a one-off shuffle failure (documented).
- After: fast tests `Ran 73 tests — OK`; full runner suite `Ran 143 tests in 330.187s — OK`; F4 and N3 by
  hand unchanged (F4 `VERIFIED` via seed 1 after 2 orders; N3 `NOT_REPRODUCED`, 31 orders, bound 0.161).
- Deferred minor: `read_order`'s duplicate check is quadratic (fine for thousands of lines).
- For Member 3: crash counts for shuffles and alone runs are on `DiagnosisRuns` but not in the report;
  whether alone-only crashes should become `INFRASTRUCTURE_FAILURE` is the decision table's call.
- Follow-up (the deferred minor, at Member 2's request): `read_order`'s duplicate check used a list.
  New `test_long_order_file_is_read_quickly` (20,001 lines, < 5 s) FAILED first:
  `AssertionError: 33.42655189999641 not less than 5.0` — the minor was more than cosmetic. With a set:
  20,001 lines in 0.094 s; duplicates still refused. Full runner suite: `Ran 144 tests in 327.282s — OK`.
- CI on the PR (`m2/adr-008-runner`, commit `0299e7b`): job `runner` (JDK 8, Linux) -> `Ran 144 tests in 105.225s — OK`
  (line copied from the job log by Member 2), so F4 via a shuffle and the N3 report also pass on Linux/JDK 8.
  Claim E15 SETTLED.
### 2026-10-11 — Docs sync after PR #49 (ADR-008 merged)

- Requirement: docs must match the merged code before the Mid packaging (CLAUDE.md §5).
- Re-ran on main `557d901` (JDK 21, Windows 11), records to a temp folder (not committed):
  `py -m runner diagnose --project fixtures/od-fixture --victim odfixture.AlwaysEarlyVictimTest#expectsLateFlagUnset`
  -> `VERIFIED`, polluter `ZzzLatePolluterTest#setLateFlag`, reproduced in shuffled order (seed 1) after 2 shuffled
  orders, resource `odfixture.LateFlag isSet`, 20/20 (lower bound 0.839), alone 0/20, 36 s.
  `py -m runner diagnose --project fixtures/od-fixture --victim odfixture.EnvDependentNegativeTest#onlyFailsUnderCI`
  -> `UNRESOLVED (NOT_REPRODUCED)`, discovered order 20x, 31 distinct shuffled orders, alone 20x, bound < 0.161, 37 s.
- Checked the F4 execution record for panel action A7: header has `"shuffles": 31, "seed_base": 0`; shuffled run lines
  carry `"seed": 0` and `"seed": 1`; the report has `"reproducing_seed": 1`.
- Docs changed: ADR-003/004/005/007/008 status `ACCEPTED` (ticks already present); W14 row merged; W9 row, A1, A5,
  A7 (seed no longer "not applicable"), demo-plan status and mocked table, members row, architecture status line.
- Limitation: F4/N3 JSON reports are still not in `eval/reports/` (Member 3's `run_w9_integration.py` covers F1/F2/N1/N2).

### 2026-10-11 — Root README: every setup command run before the report quotes it

- Requirement: Form 3 #7 caps implementation marks if setup is not reproducible; the Mid report's Chapter 6
  copies its setup commands from the root `README.md`, which still said the runner and extractor were not built
  and listed only `runner.tests.test_order_runner` (CI runs every `runner/tests/test_*.py`).
- Ran the Windows form of each command from the repo root on `main` `0e6723a` + the README change (Windows 11,
  Python 3.14.0, JDK 21.0.9, Maven 3.10.0, `jsonschema` 4.26.0 already installed):
  - `py -m unittest` over the 7 `eval/tests/test_*.py` modules -> `Ran 85 tests in 2.753s — OK`
  - `mvn -B -q -f fixtures/od-fixture/pom.xml test-compile` and the `m1-selftest` compile -> exit 0 both
  - `py -m unittest evidence.tests.test_extract` -> `Ran 39 tests in 86.267s — OK`
  - `py -m unittest` over the 9 `runner/tests/test_*.py` modules -> `Ran 144 tests in 344.837s — OK`
  - `py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode`
    (records to a temp folder) -> exit 0, `VERIFIED`, polluter `ConfigPolluterTest#pollute`, resource
    `static-field odfixture.Config mode` (write @1 -> read @1), 20/20 (lower bound 0.839), alone 0/20.
  - `git status --short` afterwards: only `README.md` modified; the fixture is unchanged.
- README changed: status line; the runner line now runs every runner test module (as CI does); a Windows block next
  to the bash one; prerequisites stated. The bash block was not run here (CI runs the same module lists on Linux).

### 2026-10-11 — F3 re-run for the Mid report (fixture now has F4/N3)

- Requirement: the report quotes `ddmin` on F3; the last recorded figure ("12 earlier tests -> 2 polluters in
  10 runs", 2026-10-10) predates M3's F4/N3 classes, which sort before `ToggleVictimTest` and lengthen the order.
- `py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ToggleVictimTest#expectsNotBothFlagsSet`
  (Windows 11, JDK 21.0.9, `main` + report commits, records to a temp folder) -> exit 0, 37.0 s wall:
  `VERIFIED`, polluters `setFlagA`, `setFlagB`, `minimised: 14 earlier tests -> 2 polluters in 10 runs (1-minimal,
  not necessarily the minimum)`, 20/20 (lower bound 0.839), alone 0/20.
- Execution record, run lines per step: reproduce 1, alone 20, search 14, minimise 10 (includes the one full-order
  re-run), verify 20 = 65 JVM runs, 22.2 s of JVM time.
- Size for the report: `wc -l` -> runner product code 1,119 lines (11 Python files + `FtHarness.java`), tests 1,488 lines.
- `git status --short fixtures/` empty.

## 2026-10-14 — UI backend: job results (ADR-009, Task 1)

- Requirement: spec `docs/03-Design/specs/2026-10-14-ui-design.md` section 4 — a finished CLI run becomes a job
  result from the CLI's exit code and the report file only (0 report, 1 tool failed, 2 bad input, 3 no report).
- `ui/server.py` `job_result`, `load_valid_report`, `report_problem` (schema check via `eval.schema_validator`).
- Before the code: `py -m unittest -v ui.tests.test_server` -> `ModuleNotFoundError: No module named 'ui.server'`.
- After: `py -m unittest -v ui.tests.test_server` -> `Ran 7 tests in 0.097s — OK` (Windows 11, branch `m2/ui`).
- Limitation: tested with hand-written CLI outputs; the real CLI is exercised in Task 4.

## UI backend: jobs (Task 2)

- Requirement: spec section 4 rules 1, 5, 6 — one job at a time (`busy`), a 10-minute limit that stops the run,
  a new temp records folder per job; arguments (paths with spaces, `--order`) reach the CLI intact.
- `ui/server.py` `Jobs`, `Busy`, `kill_tree`, `check_diagnose_request`; `ui/tests/fake_cli.py` (FakeCli, tests only).
- Before the code: `py -m unittest -v ui.tests.test_server` -> `ImportError: cannot import name 'Busy'`.
- After: `Ran 16 tests in 10.179s — OK` (Windows 11).
- Mutation check: with the timeout killing only the CLI process (`process.kill()`) instead of the process tree,
  `test_timeout_also_stops_child_processes` failed (`job ... still running after 60 s`): the orphaned child kept
  the output pipe open, so the job never finished. Restored `kill_tree`; 16 OK again.
- Limitation: the tree kill was checked on Windows (`taskkill /T`); the Linux path (`killpg`) runs in CI.

## UI backend: HTTP API (Task 3)

- Requirement: spec section 4 API table and rules 3 (validated reports) and 4 (local only).
- `ui/server.py` `Handler`, `make_server`, `health`, `list_reports`, `get_report`; endpoints `GET /api/health`,
  `/api/reports`, `/api/reports/<name>`, `/api/jobs/<id>`, `POST /api/diagnose` (400, 409), `/api/validate`.
- Before the code: `ImportError: cannot import name 'make_server'`. After: `Ran 26 tests in 21.118s — OK`.
- Smoke run: `py ui/server.py`, then `curl -s http://127.0.0.1:8765/api/reports` -> 7 entries starting
  `{"name": "f1", "victim": "odfixture.ConfigVictimTest#expectsDefaultMode", "outcome": "VERIFIED"}`;
  `/api/health` -> `missing: []` (JDK 21.0.9, Maven 3.10.0, Python 3.14.0 on this laptop).
- `eval/reports/baseline_results.json` is not a report and is not listed (it fails the schema check).

## UI backend: real F1 run (Task 4)

- Requirement: spec section 7, backend test 7 — one real `POST`-equivalent diagnose of F1 through the backend ends
  `done`, `VERIFIED`, polluter `ConfigPolluterTest#pollute`.
- `ui/tests/test_server.py` `TestRealRunOnFixture` (skipped without JDK/Maven locally; required in CI via
  `FLAKETRACE_REQUIRE_JVM`); new CI job `ui` in `.github/workflows/ci.yml`.
- Seen failing first on purpose: expected polluter `polluteX` -> `AssertionError: Lists differ: [{... 'pollute'}] !=
  [{... 'polluteX'}]` after a real run (`Ran 1 test in 50.552s`), so the run itself completed and was VERIFIED.
- After restoring `pollute`: `py -m unittest -v ui.tests.test_server` -> `Ran 27 tests in 50.033s — OK`
  (Windows 11, JDK 21.0.9, Maven 3.10.0).
- Timing: the single real F1 run took about 50 s here, longer than the 23.3 s recorded for F1 on 2026-10-09; the
  UI's "about 20–40 seconds" wording is to be checked against the Task 7 live run.
- CI job not yet run on GitHub (runs on the final PR).

## UI web: scaffold and report mapping (Task 5)

- Requirement: spec sections 5 and 7 — every screen value comes from a real report; every null field gets a stated
  reason; unbuilt parts carry the exact approved label; no POC simulated or recorded data.
- Copied from `POC/POC/flaketrace-ui` only the look: `package.json`, lock file, `tsconfig.json`, `index.html`,
  favicon, `index.css`, the lockup image, `components/ui.tsx`, `components/Trace.tsx` (link label "writes, never
  restores" changed to "writes": the extractor does not check restoring). New: `src/lib/format.ts`, `report.ts`,
  `labels.ts`, three test files. Vitest 5.0.4 with vite 8.3.0 (no peer conflict).
- Before the code: `npm test` -> `Cannot find module './labels'` and `'./report'`; `nosim.test.ts` passed.
- The no-simulation test can fail: with the POC's `sim.ts` copied into `src/lib/`, both of its checks failed
  (`lib/sim.ts: expected true to be false`); file removed again.
- After: `npm test` -> `Test Files 3 passed (3), Tests 26 passed (26)`; `npm run typecheck` -> no errors. The
  expected values for all seven reports (outcome, polluters, order length, reduced length, reproduction, alone)
  are the spec's table, read from `eval/reports/*.json`.
- `npm audit` flagged one high-severity build-time package inherited from the POC lock file (`source-map-js`,
  GHSA-68fv-2mgg-jv7q); `npm audit fix` updated it to 1.2.2 -> `found 0 vulnerabilities`; tests re-run, 26 passed.

## UI web: screens (Task 6)

- Requirement: spec sections 5 and 6 — nine POC screens on real reports; open-report and live mode; unbuilt parts
  greyed and labelled; busy, input, tool, no-report, restart and backend-down states.
- Copied unchanged from the POC: `App.tsx`, `main.tsx`, `components/StepRail.tsx`. New: `src/lib/api.ts`,
  `src/state.tsx`, `components/Header.tsx`, `components/NotBuilt.tsx`, nine `screens/*.tsx`.
- Before the code: `npm run typecheck` -> 19 errors (`Cannot find module './state'`, `./screens/Source`, ...).
- After: `npm run typecheck` -> no errors; `npm test` -> `Tests 26 passed (26)`; `npm run build` -> `built in 2.05s`.
- Found while checking: Vite bound `localhost` (IPv6 `::1` on this laptop), so `http://127.0.0.1:5174` did not
  answer; `vite.config.ts` now sets `host: "127.0.0.1"` -> 200.
- Live run through the web app's proxy (2026-10-15): `POST /api/diagnose` for
  `odfixture.ConfigVictimTest#expectsDefaultMode` on `fixtures/od-fixture` -> `done` after 66 s, `VERIFIED`, polluter
  `odfixture.ConfigPolluterTest#pollute`, 20/20, alone 0/20. The Target screen's estimate was changed from
  "20–40 seconds" to "about one minute (50–66 s measured)".
- Backend stopped: `GET /api/health` through the proxy -> `502` with an empty body, which `api.ts` reports as
  "Backend not running".
- Screens checked by M2 in the browser (2026-10-15): F3 (15 tests, 2 polluters, reduced 3, VERIFIED 20/20 vs 0/20,
  `odfixture.Toggles.flagA` with the one-resource note), N1 (`UNRESOLVED(VICTIM_FAILS_ALONE)` and its reason, no shared
  resource), Repair/Verify/EvoSuite (NOT BUILT card only) -> M2 reported "all OK".

## UI: live end-to-end check (Task 7)

- Requirement: spec section 7, manual check — start the UI with `ui\start.cmd`, run F1 live, check the busy and
  bad-input states, open N1's report.
- Run by M2 on 2026-10-15 (Windows 11, JDK 21.0.9, Maven 3.10.0), results as M2 reported them:
  1. Source -> Use the seeded fixture; Target -> f1, n 20 -> Diagnose: running timer and command shown, then
     Diagnosis with `ConfigPolluterTest#pollute`, Certificate `VERIFIED` 20/20 vs 0/20; about one minute.
  2. Diagnose pressed twice: "A diagnosis is already running (started ...)".
  3. Project folder `C:\Users\raffa\Desktop` -> Diagnose: "The runner rejected the input: no pom.xml in ...".
  4. Source -> n1: `UNRESOLVED(VICTIM_FAILS_ALONE)`.
  M2's summary: "all OK, F1 took about a minute".
- Observed: right after `ui\start.cmd`, Vite logged `http proxy error ... ECONNREFUSED 127.0.0.1:8765` for the first
  `/api/health` and `/api/reports` calls: the page asked before the backend window had started. `py server.py`
  started and served normally when run on its own; the page needs "Check again" (or a reload) in that case.
- Final runs: `py -m unittest -v ui.tests.test_server` -> `Ran 27 tests in 51.909s — OK`; `npm test` ->
  `Tests 26 passed (26)`; `npm run typecheck` -> no errors; `npm run build` -> `built in 1.89s`.

## UI: fixes from the final branch review

- Review by a fresh reviewer agent (most capable model) of `m2/ui` 86d8355..ddcc8f7: 0 Critical, 2 Important, 8 Minor.
- I1 (security): any website open in the browser could start a diagnosis — the backend accepted a `text/plain` POST
  from any Host. Now: requests must have `Host` 127.0.0.1/localhost on the backend's port (else 403), POSTs must be
  `application/json` (else 415), `Content-Length` must be 0..1 MiB (else 400/413); the Vite proxy uses
  `changeOrigin` so the UI's own requests pass. Three tests failed first (`HTTPError not raised` x3, two
  `TimeoutError` for a negative and a 10 MiB length); after: `py -m unittest -v ui.tests.test_server` ->
  `Ran 30 tests in 69.648s — OK`. Live: proxy health 200, `Host: evil.example` 403, text/plain POST 415.
- I2 (the startup race seen in the live check): the first health check is retried every 2 s, up to 8 attempts, while
  the backend is unreachable. `retryWhileDown` tests (3) failed first (`retryWhileDown` missing); after: `npm test`
  -> `Tests 29 passed (29)`; typecheck clean; build OK. Live: proxy answered 502 before the backend started and 200
  after.
- Eight Minor findings deferred and listed in the PR description.


## Post-Mid: the two certification defects reproduced on `main` (2026-11-13)

**Requirement:** before designing a fix, confirm the supervisor's findings FT003 and FT004 on our
own copy of the code, not from the review's description.

- Code: `main` `7cf453d` (the Mid tag `mid-eval-v1` is `86d8355`; the only commits since are the web
  UI, PR #99 — `runner/diagnose.py`, `runner/minimise.py`, `runner/verify.py`, `eval/outcome.py` and
  `eval/report.py` are unchanged since the tag).
- Method: a scratch script, **not committed**, driving the real `runner.diagnose.run_steps` and the
  real `eval.report.assemble_report` with `eval/tests/fake_runner.py`'s scripted runner. No JVM.
  Run by Claude in its own cloud copy of the repository (Python 3, `jsonschema` 4.26.0), not on my
  laptop.
- Command: `PYTHONPATH=. python3 probe.py` from the repository root.
- Real output:

  ```
  FT003: VERIFIED None | polluters ['P#t'] | alone 0 / 20
  FT004: VERIFIED | retained ['P#t', 'Q#t']
  FT004: sequence with Q deleted ([P, V]) then fails 20 / 20
  ```

- **FT003 confirmed.** Scenario: the victim alone always fails with `IllegalStateException`; after
  P it always fails with `AssertionError`. Result: a schema-valid `VERIFIED` blaming P, with the
  report showing "alone 0/20". Cause, read in the code: `run_steps` (lines 109–112) keeps
  `alone_successes` (reference-matching failures) and never uses `alone_any`; the final
  `DiagnosisRuns` (lines 131–132) always carries `alone_successes = 0`.
- **FT004 confirmed.** Scenario: P alone is enough, but `[P, V]` passes on its first two runs — the
  one the one-by-one search gives it and the one `ddmin` gives it — and fails on every run after.
  Result: P **and Q** kept, `VERIFIED`; the shorter sequence `[P, V]` then fails 20 of 20.
- Limitation: both scenarios are scripted outcome functions, as the supervisor's probes were. They
  show the logic gap; they are not Java tests. The integrated Java regression for FT003 is fixture
  case N4, planned in ADR-010. Nothing was fixed in this session.
- The script, so the result can be repeated before the regression tests exist:

  ```python
  """Scratch probes (not committed): reproduce FT003 and FT004 against main 7cf453d."""
  import random, sys
  from eval.baseline import RunOutcome, TestIdentifier, FailureSignature
  from eval.tests.fake_runner import FakeOrderRunner
  from eval.report import assemble_report
  from runner.diagnose import run_steps
  from runner.integrity import SourceIntegrity
  from dataclasses import replace

  T = lambda c, m="t": TestIdentifier(c, m)
  A = FailureSignature("java.lang.AssertionError", "V.t:10", "A")
  B = FailureSignature("java.lang.IllegalStateException", "V.t:22", "B")
  P, Q, X, V = T("P"), T("Q"), T("X"), T("V")
  EDGE = {"shared_resource": {"kind": "static-field", "class": "C", "field": "f"},
          "polluter_write_location": {"class": "P", "method": "t", "bytecode_offset": 1},
          "victim_read_location": {"class": "V", "method": "t", "bytecode_offset": 1},
          "limitations": []}

  def finish(runs):
      runs = replace(runs, source_integrity=SourceIntegrity(True, "probe"), execution_record="probe.jsonl")
      return runs, assemble_report(runs, EDGE)

  # ---- FT003: alone always fails with B; after P always fails with A
  def ft003(order, test):
      if test != V: return RunOutcome(True)
      return RunOutcome(False, A if P in order else B)
  runs, rep = finish(run_steps(FakeOrderRunner(ft003), [X, P, V], V, n=20))
  print("FT003:", rep["outcome"], rep["unresolved_reason"], "| polluters", [str(p) for p in runs.polluters],
        "| alone", rep["victim_alone"]["successes"], "/", rep["victim_alone"]["n"])

  # ---- FT004: victim fails with A after P always; after Q alone never; ddmin's single trial is noisy:
  # the pair-with-P-removed subset passes on its first (cached) trial only.
  seen = {}
  def ft004(order, test):
      if test != V: return RunOutcome(True)
      pre = tuple(order[:-1])
      if P in pre:
          if Q not in pre and len(pre) == 1:
              k = seen[pre] = seen.get(pre, 0) + 1   # [P, V]: passes on trials 1-2, fails afterwards
              return RunOutcome(True) if k <= 2 else RunOutcome(False, A)
          return RunOutcome(False, A)
      return RunOutcome(True)
  runs, rep = finish(run_steps(FakeOrderRunner(ft004), [P, Q, V], V, n=20))
  print("FT004:", rep["outcome"], "| retained", [str(p) for p in runs.polluters])
  r = FakeOrderRunner(ft004)
  fails = sum(1 for _ in range(20) if not r.run_ordered([P, V])[V].passed)
  print("FT004: sequence with Q deleted ([P, V]) then fails", fails, "/ 20")
  ```

## W16: retired claims qualified in `runner/` and `ui/` (2026-11-14)

- **Requirement:** W16 ([[10-Final1/iteration-2-plan]]); claims ledger G1–G4; ADR-010 §2 and Q3;
  ADR-011 §5; ADR-012 §1. Branch `m2/w16-retire-claims`, from `main` `b802600`.
- **Changed:** `runner/cli.py` `summary()`: headline `VERIFIED (sequence)`; a shown resource gets
  "static overlap: a possible mechanism, not confirmed as the cause"; the alone count is labelled
  "alone (same failure)"; the minimise line says "reduced by single-trial delta debugging; not
  deletion-verified". UI: `outcomeLabel()` in `ui/web/src/lib/report.ts` (used by the Certificate
  headline, the step rail and the report list); fixed sentences on the Certificate and Evidence
  graph screens. Docstrings, `runner/README.md` and three notes in `docs/04-Implementation/`.
- **Test first.** New and changed assertions in `runner/tests/test_cli.py` and
  `ui/web/src/lib/report.test.ts`, run on the unchanged code:
  - `py -3 -m unittest runner.tests.test_cli.TestReports` → **13 run, 5 failed**, each on the old
    wording, e.g. `AssertionError: 'VERIFIED  pkg.VictimTest#v' != 'VERIFIED (sequence)  pkg.VictimTest#v'`
    and `'alone (same failure): 0/20' not found in '... alone: 0/20 ...'`.
  - `npx vitest run src/lib/report.test.ts` → **4 failed, 17 passed**: f1–f4
    `expected 'VERIFIED' to be 'VERIFIED (sequence)'`.
- **After the change** (Windows 11, Python 3.14, Node 22.21.1, local JDK):
  - every `runner/tests/test_*.py` (as CI runs them) → **147 tests OK** (338 s, real JVM runs included)
  - every `eval/tests/test_*.py` → **85 OK** · `ui.tests.test_server` → **30 OK**
  - `ui/web`: `npm test` → **29 passed** · `npm run typecheck` clean · `npm run build` OK
  - Real command: `py -3 -m runner diagnose --project fixtures/od-fixture --victim
    odfixture.ConfigVictimTest#expectsDefaultMode --records <scratch>` → exit 0:
    ```
    VERIFIED (sequence)  odfixture.ConfigVictimTest#expectsDefaultMode
      polluter:   odfixture.ConfigPolluterTest#pollute
      resource:   static-field odfixture.Config mode (write odfixture.ConfigPolluterTest#pollute@1 -> read odfixture.ConfigVictimTest#expectsDefaultMode@1)
                  static overlap: a possible mechanism, not confirmed as the cause
      reproduced: 20/20 (lower bound 0.839)   alone (same failure): 0/20
    ```
  - Search of `runner/`, `ui/`, `.github/`, `docs/04-Implementation/` for *1-minimal, never
    modified, sandboxed, found mechanism, root cause, caused by, explains the failure, passes
    alone* → one hit, the qualified "1-minimal only for the single trials ddmin saw" (ledger G2).
- **Limitations:** wording only — the FT003 and FT004 defects are still in the code (W18, W20).
  The UI's fixed sentences have no unit test (a test would repeat the string); they were checked
  by typecheck, build and the phrase search, **not yet viewed in a browser**. `evidence/` tests
  were not run (no file there changed). The report's `limitations` text comes from `eval/` and
  `evidence/` and is M3's and M1's part of W16. The CI step name "Victims pass alone (F1, F2, F3)"
  is kept: it names a real Maven check of the fixture, not a claim about a report.

## W19 step 1: `RunTally`, `classify` and `tally` in `eval/baseline.py` (2026-11-14)

- **Requirement:** ADR-010 §1 (four outcome categories, one classifier, one synthetic prefix);
  W19 step 1, written by M2 in M3's file by M3's agreement of 2026-11-13. Branch `m2/w19-runtally`,
  stacked on `m2/w16-retire-claims` (`9a05788`).
- **Choices made by M2 (2026-11-14):** tests in `eval/tests/test_baseline.py`; `classify` raises
  `ValueError` for a real failure when there is no reference; a `tally(outcomes, reference)` helper
  so the runner (W18) and the recount checker (ADR-013) count the same way.
- **Test first:** `py -3 -m unittest eval.tests.test_baseline` on the unchanged module →
  `ImportError: cannot import name 'INFRA' from 'eval.baseline'` (FAILED, errors=1).
- **After:** `py -3 -m unittest eval.tests.test_baseline` → **27 OK** (14 new).
- **Mutation check** (scratch script; the file restored and compared byte for byte after):

  | Mutation | Tests that failed |
  | --- | --- |
  | Sum check removed from `RunTally` | `test_counts_that_do_not_add_up_are_refused` |
  | Crash/timeout/skip no longer `INFRA` | `test_pass_and_infra_need_no_reference`, `test_crash_timeout_and_not_executed_are_infra`, `test_counts_each_category_once` |
  | Every real failure counted as `MATCH` | `test_a_different_real_failure_is_other`, `test_counts_each_category_once`, `test_ft003_alone_runs_failing_differently_are_not_passes` |

- **Runner refactor:** `runner/search.py`, `verify.py`, `orders.py` import `SYNTHETIC_PREFIX` from
  `eval/baseline.py`; `order_runner.py`'s three `"flaketrace.…"` literals use it. No behaviour
  change intended; checked by the existing suites: every `runner/tests/test_*.py` → **147 OK**
  (336 s, real JVM runs), every `eval/tests/test_*.py` → **99 OK**, `ui.tests.test_server` → **30 OK**.
- **Limitations:** nothing uses the tallies yet — the defect FT003 is still in `runner/verify.py`
  until W18. Awaiting review by M3 (owner of the file).

## W18: the runner counts every phase as an ADR-010 tally (2026-11-14)

- **Requirement:** ADR-010 §1 and §5, tests T1–T4 at the runner level; FT003, FT010. Branch
  `m2/w18-tallies` from `main` `d1e4d4f`. Landing chosen by M2 (2026-11-14): tallies **beside** the
  old count fields, `NO_SINGLE_POLLUTER` kept as an alias of `INCONSISTENT`, so no `eval/` file
  changes until W19.
- **Test first**, on the unchanged runner:
  - `py -3 -m unittest runner.tests.test_diagnose.TestTallies` → **8 run: 7 errors**
    (`'DiagnosisRuns' object has no attribute 'alone_tally'` / `'sequence_tally'`) and **1 failure**,
    T4: `AssertionError: 'NO_SINGLE_POLLUTER' != 'INCONSISTENT'`. (A first version of one test
    erred with `IndexError` because its order `[V]` also consumed the scripted alone outcomes in
    the reproduce step; fixed in the test before any code was written.)
  - `py -3 -m unittest runner.tests.test_search.TestRepeat` → `AssertionError: (2, 4) != RunTally(n=5, passed=1, matched=2, other=1, infra=1)`.
  - What the unchanged runner returns for the three scripted defects (scratch script):
    ```
    T1 POLLUTER_FOUND alone_n 20 alone_successes 0 polluters ['pkg.PolluterTest#p']
    T2 POLLUTER_FOUND alone_n 20 alone_successes 0 polluters ['pkg.PolluterTest#p']
    T3 POLLUTER_FOUND alone_n 20 alone_successes 0 polluters ['pkg.PolluterTest#p']
    ```
    Failing alone 20/20 differently, 3/20 differently, and timing out 2/20 are indistinguishable
    from passing alone 20/20 — FT003.
- **After:**
  ```
  T1 POLLUTER_FOUND alone RunTally(n=20, passed=0, matched=0, other=20, infra=0) | old alone_successes 0
  T2 POLLUTER_FOUND alone RunTally(n=20, passed=17, matched=0, other=3, infra=0) | old alone_successes 0
  T3 POLLUTER_FOUND alone RunTally(n=20, passed=18, matched=0, other=0, infra=2) | old alone_successes 0
  F1 POLLUTER_FOUND alone RunTally(n=20, passed=20, matched=0, other=0, infra=0) sequence RunTally(n=20, passed=0, matched=20, other=0, infra=0)
  ```
  (F1 is a real `diagnose()` on `fixtures/od-fixture`.) Every `runner/tests/test_*.py` → **155 OK**
  (337 s, real JVM runs); every `eval/tests/test_*.py` → **99 OK**, no `eval/` file changed;
  `ui.tests.test_server` → **30 OK**.
- **Limitations:** the runner still blames P in T1–T3 and the report would still say `VERIFIED`:
  `decide()` reads the old `alone_successes`, which is still 0. ADR-010 rows 6–8 and the
  `INCONSISTENT` report are M3's W19. T4's report (exit 0) also waits for W19; the command still
  exits 3 with "No report: INCONSISTENT".

## W22 job 1: environment fields in the execution record (2026-11-14)

- **Requirement:** ADR-012 §6 (FT006, FT021; feeds ADR-013's manifest `environment`, W23).
  Design `docs/superpowers/specs/2026-11-14-w22-record-environment-design.md`, plan
  `docs/superpowers/plans/2026-11-14-w22-record-environment.md`. Branch `m2/w22-record-env`, stacked
  on `m2/w18-tallies` (`e49fa13`).
- **Task 1 — `FtHarness --env`, `OrderRunner.jvm_environment()`.** Test first:
  `py -3 -m unittest runner.tests.test_order_runner` → `ImportError: cannot import name 'parse_env'`.
  After: **29 OK**, none skipped. The timezone test forces `-Duser.timezone=Pacific/Kiritimati`
  through `JAVA_TOOL_OPTIONS` and reads it back, so the value comes from the test JVM, not Python.
  Real probe on this machine: `{'java.version': '21.0.9', 'timezone': 'Asia/Karachi', 'locale': 'en_US', 'file.encoding': 'UTF-8', 'junit.version': '4.13.2'}`.
- **Task 2 — header fields and the CLI's command line.** Test first: `TestEnvironment` →
  `ImportError: cannot import name 'maven_version'`; the CLI test → `KeyError: 'command'`. After:
  the three new test groups **14 OK**; every `runner/tests/test_*.py` → **164 OK** (372 s, none
  skipped), **165 OK** after the review fix below; every `eval/tests/test_*.py` OK; `ui.tests.test_server` OK.
- **Real command:** `py -3 -m runner diagnose --project fixtures/od-fixture --victim
  odfixture.ConfigVictimTest#expectsDefaultMode --n 2 --records <scratch>` → first record line:
  ```
  {"type": "header", "victim": "odfixture.ConfigVictimTest#expectsDefaultMode", "n": 2, ..., "java_version": "openjdk version \"21.0.9\" 2025-10-21 LTS", ..., "project_commit": "e49fa13b…", "project_dirty": false, "os": "Windows-11-10.0.26200-SP0", ..., "tool_commit": "e49fa13b…", "tool_dirty": true, "maven_version": "Apache Maven 3.10.0 (c43a36b8…)", "python_version": "3.14.0", "jvm": {"java.version": "21.0.9", "timezone": "Asia/Karachi", "locale": "en_US", "file.encoding": "UTF-8", "junit.version": "4.13.2"}, "lifecycle": "per-method", "workspace": "in-place", "container_image": null, "command": ["diagnose", "--project", "fixtures/od-fixture", "--victim", "odfixture.ConfigVictimTest#expectsDefaultMode", "--n", "2", "--records", "<scratch>"]}
  ```
  (`CANDIDATE` at `--n 2` is expected: two runs cannot reach the 0.70 Wilson lower bound.)
- **Review** (fresh reviewer, Claude Opus, read-only): 0 critical, 1 important, 4 minor. Important:
  the design's test "a failed probe still gives a header" had been left out of the plan. Added
  `test_failed_jvm_probe_records_null_and_the_diagnosis_goes_on`; with `or None` removed from the
  header code it fails (`AssertionError: {} is not None`), restored it passes; suite 165 OK.
  Deferred minors: a `null` JVM property would make the harness drop the whole `jvm` entry; one test
  named "outside git" really tests "git not installed"; `mvn.cmd -v` timeout may not stop a hung
  Maven on Windows; `tool_dirty` counts untracked files.
- **Limitations:** `lifecycle` and `workspace` are constants until W22 jobs 3 and 4.
  `command` and `project` hold absolute paths with the user's name; ADR-013's redaction at bundle
  export removes them, nothing here does. A JVM probe adds one short JVM launch per diagnosis.

## W22 job 2: the JUnit spike for class-grouped execution (2026-11-14) — throwaway, not merged

- **Requirement:** ADR-012 §2 "spike before committing to this". Code in a scratch folder only
  (`Spike.java`: `Request.aClass(cls).filterWith(methods).sortWith(by requested index)` with a
  `RunListener`; `PerMethod.java`: one `Request.method` per test, today's harness; test classes
  `LifecycleControlTest` (ADR-012 §3, plus a `third`), `Legacy3Test` (JUnit 3, `testC` fails),
  `BrokenSetupTest` (`@BeforeClass` throws)). Compiled `javac -source 8 -target 8` against
  `junit-4.13.2.jar` + `hamcrest-core-1.3.jar`; run on OpenJDK 21.0.9.
- **Results (real output, abridged):**
  ```
  == LifecycleControlTest requested [third, first, second]
  started third / finished third / started first / finished first / started second / finished second   run count 3
  == Legacy3Test requested [testC, testA]
  started testA / finished testA / started testC / FAILED testC : AssertionFailedError: C fails on purpose   run count 2
  == BrokenSetupTest requested [b, a]
  FAILED null : java.lang.IllegalStateException: setup broke   run count 0
  == per-method (today's harness)
  first PASS
  second FAIL : java.lang.AssertionError: expected:<1> but was:<2>
  testC FAIL ... / testA PASS
  ```
- **Findings:** JUnit 4 class requests filter and sort as needed, with `@BeforeClass` once; JUnit 3
  sorting is silently ignored, so JUnit 3 classes stay `per-method`; a failing `@BeforeClass` must be
  mapped to every test of its block by the harness; today's mode fails the control as ADR-012 §3
  predicted. Written into ADR-012 §2.
- **Limitations:** JDK 21 only (no JDK 8 installed here). Not tried: `@ClassRule`, `@RunWith`
  runners other than the default (e.g. `Parameterized`), JUnit 3 `suite()` with `TestSetup`.

## W22 job 3: class-grouped execution and the lifecycle control (2026-11-14)

- **Requirement:** ADR-012 §2–§3, FT006. Design
  `docs/superpowers/specs/2026-11-14-w22-class-grouped-execution-design.md`, plan
  `docs/superpowers/plans/2026-11-14-w22-class-grouped-execution.md`. Branch `m2/w22-record-env`.
  Default mode decided: `per-method` until M1's control run (Claude's call on M2's delegation).
- **Checked first:** the runner class JUnit 4.13.2 gives — plain JUnit 4 class `org.junit.runners.JUnit4`,
  JUnit 3 `JUnit38ClassRunner`, `@RunWith(Parameterized)` `Parameterized` (scratch probe).
- **Task 1, test first:** `py -3 -m unittest runner.tests.test_order_runner` → `TypeError: OrderRunner.__init__()
  got an unexpected keyword argument 'lifecycle'` (3 errors). The `per-method` control row passed
  before and after: it measures today's behaviour (`second` fails, `expected:<<N>> but was:<<N>>`).
  After: **39 OK**. Mutations, each restored byte for byte: grouping disabled →
  `test_class_grouped_runs_class_setup_once` fails; a failing `@BeforeClass` no longer given to the
  block → `test_grouped_setup_failure_fails_every_test_of_the_block` fails.
- **The control, three ways, on this machine (OpenJDK 21.0.9, Maven 3.10.0):**

  | Execution | Command | Result |
  | --- | --- | --- |
  | Surefire | `mvn -B -q -f runner/tests/resources/lifecycle-control/pom.xml test` | exit 0; report `tests="2" failures="0"` (ran `second`, `first`) |
  | Harness `per-method`, `[first, second]` | `TestLifecycleControl.test_per_method_runs_class_setup_per_test` | `first` pass, `second` `AssertionError expected:<1> but was:<2>` |
  | Harness `class-grouped`, same order | `TestLifecycleControl.test_class_grouped_runs_class_setup_once` | both pass |

- **Task 2, test first:** CLI test → `KeyError: 'lifecycle'`; fixture test → `TypeError: diagnose()
  got an unexpected keyword argument 'lifecycle'`. (The usage-error test passed before too — argparse
  rejected the unknown option then, the bad value now.) After: every `runner/tests/test_*.py` →
  **178 OK**, **180 OK** after the review fixes below (417 s, none skipped); every `eval/tests/test_*.py` → **99 OK**; `ui.tests.test_server` → **30 OK**.
- **Real command:** `py -3 -m runner diagnose --project fixtures/od-fixture --victim
  odfixture.ConfigVictimTest#expectsDefaultMode --lifecycle class-grouped --records <scratch>` →
  `VERIFIED (sequence)`, polluter `ConfigPolluterTest#pollute`, reproduced 20/20, alone (same
  failure) 0/20; header `lifecycle: class-grouped`.
- **Review** (fresh reviewer, Claude Opus, read-only, with its own scratch probes): 0 critical,
  2 important, 4 minor. Both important ones fixed test-first, each new test seen failing first:
  (1) a throwing static initializer lost its cause in `class-grouped`
  (`AssertionError: 'java.lang.NoClassDefFoundError' != 'java.lang.ExceptionInInitializerError'`) —
  now reported exactly as `per-method` does; (2) an assumption failing in `@BeforeClass` was written
  as a fake "No tests found" failure (`'java.lang.Exception' != 'flaketrace.NotExecuted'`) — now a
  skip, as `per-method`. Probes `StaticInitProbeTest`, `AssumeSetupProbeTest`; suite 180 OK;
  Surefire control still exit 0. Deferred minors: the grouped "No tests found" message lacks
  `per-method`'s ` from ClassRequest@…` and stack frame, so an unknown method's signature differs
  between the modes (the design said "same"); a spec line without `#` stops the harness (never sent
  by Python); the harness alone treats an unknown mode as `per-method` (`OrderRunner` rejects it);
  a test method named `initializationError` could take the empty-filter error.
- **Limitations:** default unchanged until M1's run. JUnit 3, `@RunWith` and `suite()` classes
  keep per-test lifecycle. An `@AfterClass` failure is not charged to a test in `class-grouped`.
  JDK 8 not run locally — CI runs the control and the runner tests on JDK 8.

## W22 job 3 follow-up: the four deferred review minors fixed (2026-11-14)

- **Asked by M2:** fix the minors deferred in the job 3 review. Each got a test first, seen failing
  on `bbaa0d2` (`py -3 -m unittest runner.tests.test_order_runner.TestOrderRunnerOnProbes` →
  19 run, **4 failures**):

  | Minor | Failing output first | Fix in `runner/harness/FtHarness.java` |
  | --- | --- | --- |
  | Unknown method: different signature in the two modes | grouped `{… method='nope' …}` ≠ per-method | a test JUnit never ran (and no class-setup failure/skip) gets `runOne` — exactly the per-method result; no test code runs, the method does not exist |
  | A method requested as `initializationError` took JUnit's empty-filter error | `…SortingRequ…` ≠ per-method message | listener only counts descriptions of this class (`index()`) |
  | A line without `#` stopped the whole harness | `AssertionError: 1 != 0 : per-method` (exit 1) | `className`/`runOne` handle it; that line alone fails (`IllegalArgumentException`) |
  | Harness accepted an unknown `--lifecycle` | `(0, [… PASS …]) != (2, [])` | usage error, exit 2, no results |

- **After:** `runner.tests.test_order_runner` → **45 OK**; every `runner/tests/test_*.py` →
  **184 OK** (435 s); every `eval/tests/test_*.py` → **99 OK**; `ui.tests.test_server` → **30 OK**;
  Surefire control exit 0.
- **Limitation:** the "no such test" path in `class-grouped` costs one extra `Request.method`
  for that test (no test code runs).

## W22 job 4: diagnose on a disposable copy (2026-11-14)

- **Requirement:** ADR-012 §4, FT021, panel action A3. Design
  `docs/superpowers/specs/2026-11-14-w22-disposable-copy-design.md`, plan
  `docs/superpowers/plans/2026-11-14-w22-disposable-copy.md`. Branch `m2/w22-record-env`.
  Calls made by Claude on M2's delegation: the CLI owns the copy; `copy` is the CLI default.
- **Found while designing:** today the diagnosis writes `target/` **inside the user's project**
  (`mvn test-compile` in `maven_test_classpath`); the integrity check leaves `target/` out, so this
  never showed. The new real test showed it before the fix: on a fresh fixture copy without
  `target/`, `test_default_copy_never_writes_to_the_project` → `AssertionError: True is not false`
  (`target/` existed afterwards).
- **Test first:** `runner.tests.test_workspace` → `ModuleNotFoundError: No module named
  'runner.workspace'`; `test_integrity` → `ImportError: cannot import name 'integrity_of'`; the CLI
  tests → the given project was passed instead of a copy, and `--workspace` was an unknown option
  (`SystemExit: 2`).
- **After:** `test_workspace` 6 OK; targeted CLI/integrity/fixture tests 70 OK; every
  `runner/tests/test_*.py` → **199 OK** (456 s, none skipped); every `eval/tests/test_*.py` →
  **99 OK**; `ui.tests.test_server` → **30 OK**.
- **Real command** on a fresh copy of the fixture in a folder whose name has a space,
  `py -3 -m runner diagnose --project "<scratch>/od fixture" --victim odfixture.ConfigVictimTest#expectsDefaultMode --records <scratch>`
  → `VERIFIED (sequence)`, exit 0; the project folder afterwards holds only `ground_truth.json`,
  `pom.xml`, `src` (no `target/`); report `source_integrity`: `{'passed': True, 'details': 'copy: 23
  files hashed (SHA-256) before and after; all identical; original project: 23 files hashed (SHA-256)
  before and after; all identical'}`; no `flaketrace-work-*` folder left in the temp directory.
- **Limitations:** files written outside the project (temp, home, network) are not contained; a
  build that needs `.git` fails in the copy (use `--workspace in-place`); one full compile per
  diagnosis. The UI's integrity caption (W16) is still true but does not mention the copy.
- **Review** (fresh reviewer, Claude Opus, read-only; it ran real probes in a folder named
  `my prøject ü`): 0 critical, 4 important, 7 minor. Confirmed working: records inside the original
  refused; a change to the original during the run → `original project: changed: pom.xml`,
  `UNRESOLVED (SOURCE_INTEGRITY_FAILED)`; non-ASCII paths; no temp path in the report or summary.
  **Fixed, each test seen failing first:**
  (1) a multi-module child fails in a copy (its parent `pom.xml` is outside) and the error said "run
  it there" — now it suggests `--workspace in-place` (`'--workspace in-place' not found in 'error:
  mvn failed …; run it there to see why'` before); (2) the UI kills the CLI on timeout, so the CLI's
  clean-up never ran and a copy was left in `%TEMP%` (reviewer reproduced it) — new `--copy-parent`;
  the UI puts the copy in the job folder and deletes it after a kill (test: `'tool' != 'timeout'`
  before, FakeCli mode `copy-sleep`); (3) a copy that cannot be deleted is now named on stderr
  instead of silently left; (4) the `diagnose()`-level tests the design asked for (records inside
  the original; a change to the original) — they passed at once because the code already worked;
  each was proved by breaking that code (records check without the original → test errors;
  original not hashed → `AssertionError: True is not false`), file restored byte for byte. Two
  minors re-graded up because a user sees them: an `ExtractError` printed the deleted temp path
  (now the project path); a copy failure printed a Python traceback (now exit 1 with a
  `--workspace in-place` hint). Doc truth: G4 wording narrowed ("FlakeTrace writes nothing there; a
  test that does is caught by the hash"); a stale UI docstring corrected; the other minors written
  as limitations in `runner/README.md`.
- **A leak in my own test, found by checking `%TEMP%` after the run:** two `flaketrace-work-*`
  folders holding `my project` — left by `test_a_copy_that_cannot_be_deleted_is_named_on_stderr`,
  which fakes a failed delete. The test now removes it; the two folders were deleted; none remain.
- **After the fixes:** every `runner/tests/test_*.py` → **212 OK** (471 s, none skipped); every
  `eval/tests/test_*.py` → **99 OK**; `ui.tests.test_server` → **31 OK**; `ui/web` `npm test` → **29 passed**.

## PR #106 integration: making M3's W19 mergeable (2026-11-19)

- **Why:** PR #106 (M3, W19 verdict contract v2) had a merge conflict with `main` and two failing
  CI jobs; PR #107 (M1, W21 controls) had one. M3 gave M2 permission to merge `main` into #106,
  resolve the two doc tables, use M1's `resource_edges`, and answer "`VERIFIED` without deletion
  checks". Branch `m3/w19-verdict-contract-v2`.
- **CI failures reproduced first** (in throwaway worktrees of each PR head):
  - #107 `evidence`: as CI runs it, `ERROR: setUpClass (… Ft005ControlsTest) … FT005 controls not
    compiled`; after `mvn … ft005-controls/pom.xml test-compile`, 45 OK. Fix: `ci.yml` compiles the
    controls when present (guarded, because they arrive with #107 and the line must not break #106).
  - #106 `build-report`: `KeyError: 'successes'` — the Mid report's table generator reads
    `eval/reports/`, now schema v2.
  - #106 `ui`: `ui/web` 9 of 21 tests failed (`expected 'undefined/20' to be '20/20'`, order lengths).
- **Merge** (`git merge origin/main`, run by M2): conflicts only in `genai-register.md` and
  `iteration-2-plan.md`; resolved by keeping M3's and M1's rows. Combined code: eval 119 OK.
- **Found, not caught by any test:** `eval/report.py` still said "Member 1's extractor reports one
  edge" after PR #105 made `report_fields` return every edge.
- **Fixes, each test first:**
  1. `eval/report.py` uses M1's `resource_edges`; `runner/cli.py` `combine_fields` lists every
     polluter's edges; schema `resourceEdge` gains an optional `depth` (5-line diff). Before:
     `Lists differ: ['a'] != ['a', 'b']` and three report tests failing.
  2. Deletion answer (ADR-011 §2/§4): one polluter passing alone → `DELETION_VERIFIED`; two or more →
     `INCOMPLETE` → `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]`. Before: `'NOT_YET_CHECKED' !=
     'DELETION_VERIFIED'`; real F3 `('VERIFIED', []) != ('CANDIDATE', ['DELETION_EVIDENCE_INCOMPLETE'])`.
  3. `ui/web` on schema v2 (`matched`, `candidate_reasons`, `resource_edges`, the full alone tally
     "passed · failed differently · crashed" so N4 cannot read as "never failed alone").
  4. Mid-report check: `json_to_tex.py --reports DIR`; `report.yml` extracts `eval/reports` from tag
     `mid-eval-v1`. Locally: the generator on the tag's reports reproduces the committed tables
     (`git diff --exit-code` → 0).
- **Committed reports regenerated** with M3's tool, real runs: `py -3 eval/tools/run_w9_integration.py`
  → F1, F2, F4 `VERIFIED` (`DELETION_VERIFIED`); F3 `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]` with
  2 `resource_edges`; N1, N2 `UNRESOLVED (VICTIM_FAILS_ALONE)`; N3 `NOT_REPRODUCED`; N4
  `VICTIM_FAILS_ALONE_DIFFERENTLY` (alone `other` 20).
- **After:** every `eval/tests/test_*.py` → **122 OK**; every `runner/tests/test_*.py` → 213 run, 1
  failure (`test_mixed_evidence…`: two polluters now also give `DELETION_EVIDENCE_INCOMPLETE` — the
  intended change; expectation updated, `TestCombineFields` → 10 OK); `ui/web` → **33 passed**,
  typecheck and build clean. *(The UI backend and evidence suites: see the hand-over message.)*
- **Limitations:** F3's ground truth stays `VERIFIED` (the target after W20); until then the real F3
  verdict is `CANDIDATE`. The UI shows only the primary edge on the Evidence graph screen; the list
  of all edges is in the report JSON.

## A1: discovery reads the project's own Surefire includes (2026-11-20)

- **Requirement:** risk-register row "Discovery misses real test classes with custom Surefire
  includes" (found by M3 in W26a, FJ-03); unblocks W26a steps 6–9. Design
  `docs/superpowers/specs/2026-11-20-discovery-surefire-includes-design.md`, plan
  `docs/superpowers/plans/2026-11-20-discovery-surefire-includes.md`. Branch
  `m2/a1-discovery-includes` from `main` `f47b503`.
- **Probe first:** `mvn -B -q -f fixtures/od-fixture/pom.xml help:effective-pom -Doutput=<scratch>`
  → exit 0, about 28 s the first time (plugin download), 6 s after; nothing written to the fixture.
- **Test first:** `py -3 -m unittest runner.tests.test_discovery.TestClassSelection` →
  `ImportError: cannot import name 'DEFAULT_SELECTION'`; the Task 2 tests →
  `cannot import name 'project_selection'` / `diagnose` has no `project_selection`. Today's rule on
  the new test project `runner/tests/resources/custom-includes/` (include `**/bvt/**/*.java`, exclude
  `**/bvt/**/Skip*.java`): `['pkg.OutsideTest', 'pkg.bvt.SkipMeTest']` — the two classes the project
  does **not** run, and not `pkg.bvt.PlainCase`, the one it does.
- **After:** `runner.tests.test_discovery` → **18 OK** (custom project discovers exactly
  `PlainCase#first`, `#second`; no file written to it outside `target/`; fixture order unchanged).
  Whole suites: see the hand-over.
- **Real configuration, fastjson at `e05e9c5`** (shallow fetch into a scratch folder, never
  committed): `help:effective-pom` → selection `includes=('**/bvt/**/*.java',)`,
  `excludes=('**/*$*',)`. Applied to its 2,496 test sources: **2,106 selected**; the old default-name
  rule: 675, of which 76 the project never runs. `SerializeWriterTest_14` (the FJ-03 polluter):
  selected now, missed by the old rule; `MaxBufSizeTest` (victim): selected by both.
- **Review** (fresh reviewer, Claude Opus, read-only; it ran the real Surefire 2.22.2 and 3.6.0
  on scratch projects and compared): 1 critical, 4 important, 7 minor. **Critical, reproduced first:**
  the first surefire `<plugin>` anywhere was used, and Maven prints `pluginManagement` before
  `build/plugins` — `AssertionError: ('**/FromManagement*.java',) != ('**/bvt/**/*.java',)`; with a
  parent that only pins the version, the defaults would have been used silently. Fixed: only
  `project/build/plugins` is read; a reactor POM is refused. **Important, each test failing first:**
  patterns without a leading `**/` (an exclude `*Slow*.java` let `SlowThingTest` in); dotted class
  names (`pkg.a.Bar`); `excludedGroups`, `testClassesDirectory`, `dependenciesToScan`,
  `skip`/`skipTests`=true and a second test execution are now refused; `%regex[…]` is refused
  (Surefire's own regex input differs between versions). After: `runner.tests.test_discovery` →
  **24 OK**; every `runner/tests/test_*.py` → **232 OK** (590 s); fastjson's selection unchanged
  (2,106 of 2,496, polluter selected). **The 7 minors, fixed at M2's request** (each test failing
  first — 5 failures: `True is not false`, three `DiscoveryConfigError not raised`, `TypeError not
  raised`): `**` inside a name stays in one folder; patterns ending `.*` or starting `/` (Surefire
  2.x and 3.x disagree) are refused with how to write them; `#` method filters and unresolved
  `${…}` properties are refused, naming the pattern; `selection` is now a required argument of
  `discover_order`/`test_class_names`. (The other two minors — the spec's inner-class line and the
  reactor POM — were already fixed in the pass above.) After: `runner.tests.test_discovery` →
  **29 OK**; every `runner/tests/test_*.py` → **237 OK** (570 s); fastjson unchanged.
- **Limitations:** not run: full `discover_order` on a compiled fastjson (needs JDK 8; this machine
  has JDK 21) — M3's W26a step 6. `-Dtest`, `includesFile`, `excludesFile`, `groups` are refused with
  an input error. Surefire's `runOrder` is still not reproduced (alphabetical, as before).

## Follow-ups after M1's verification (PR #108) and M3's PR #109 (2026-11-20)

- **Inputs:** M1's four notes (W22 and W18 verified; Python floor; hidden first-run download; the
  handover's W18 "before" step restored the old tests too) and M3's three (UI test hard-codes N2;
  claim E14 stale; a `setup-java` flake). Branch `m2/after-verification` from `main` `843ef3d`.
- **UI test, N2.** Reproduced first: with #109's regenerated `n2.json`,
  `npx vitest run src/lib/report.test.ts` → `Expected: "15/20" Received: "12/20"`. N2
  (`NegativeFlakyTest`) fails at random by design, so its expected rate is now read from the report;
  every deterministic case stays hard-coded. After: `npm test` → **33 passed** with `main`'s
  `n2.json` **and** with #109's; typecheck clean.
- **Lifecycle default → `class-grouped`** (CLI, `diagnose()`, `OrderRunner`). Test first:
  `test_lifecycle_reaches_diagnose_and_defaults_to_class_grouped` and
  `test_default_is_class_grouped_since_m1s_control_run` → `AssertionError: 'per-method' !=
  'class-grouped'` (2 failures). After: see the hand-over for the whole runner suite.
- **Python floor:** PyPI says `jsonschema 4.26.0` `requires_python >=3.10`; the README already said
  3.11+ (CI) and now also says 3.10 is the floor and 3.9 fails; CLAUDE.md §8 says it too.
- **First-run download note** with a pre-fetch command, run once here:
  `mvn -B -f fixtures/od-fixture/pom.xml test-compile dependency:build-classpath help:effective-pom
  -Daether.connector.connectTimeout=60000 -Daether.connector.requestTimeout=180000` → `BUILD SUCCESS`.
- **Also found:** the README's Windows test list missed `runner.tests.test_workspace` — added.
- **Docs:** handover's W18 step corrected to restore only `runner/diagnose.py`, `runner/verify.py`,
  `runner/cli.py`; claim E14 qualified (F3 `CANDIDATE` until W20, no "1-minimal"); W18 and W22
  rows marked verified by M1 (PR #108).

## CLI alone line names the other failures; N4 under the new default (2026-11-20)

- **Requirement:** FT003 / claims ledger G1. Found by M1's W19 reproduction (PR #114), raised by
  M3: the summary printed only `alone (same failure): matched/n`, so N4 (`other: 20`) and F1
  (`other: 0`) looked the same on the console. The report JSON and the UI already showed `other`.
- **File/function:** `runner/cli.py` `summary()`; test
  `test_summary_tells_a_different_alone_failure_from_no_alone_failure` in `runner/tests/test_cli.py`.
  Three older hand-built test reports lacked `other`, which schema v2 requires; they now carry it.
- **Before (test-first):** `py -3 -m unittest runner.tests.test_cli.TestReports.test_summary_tells_a_different_alone_failure_from_no_alone_failure`
  → `AssertionError: 'alone (same failure): 0/20, other failure: 0/20' not found` — FAILED (failures=1).
- **After:** `runner.tests.test_cli.TestReports` → `Ran 14 tests … OK`.
- **Real runs, default lifecycle (records' header `lifecycle: class-grouped`), Windows 11, local JDK:**
  - N4 `odfixture.DualFailureVictimTest#expectsStateTwo` → `UNRESOLVED (VICTIM_FAILS_ALONE_DIFFERENTLY)`,
    `reproduced: 20/20 (lower bound 0.839)   alone (same failure): 0/20, other failure: 20/20`.
  - F1 `odfixture.ConfigVictimTest#expectsDefaultMode` → `VERIFIED (sequence)`,
    `… alone (same failure): 0/20, other failure: 0/20`.
  This answers M1's note that N4 had only been run under the old `per-method` default (PR #114 at `03c9b30`).
- **Registers:** FT006/FT021 action-register row → `Partly` (W22 reproduced by M1, PR #108).

## CI: retry `setup-java` once, move to v5 (2026-11-20)

- **Problem:** `actions/setup-java@v4` failed with `The process '/usr/bin/tar' failed with exit code 2`
  before any test ran — PRs #109, #113, #114, #119's first run and `main` at `9980f97` (`evidence`,
  `runner`, `fixture-build` at once). Other jobs on the same commits passed the same step, so it is
  intermittent. Read from the public check-run annotations; the full log needs a sign-in, so whether
  the JDK download or the Maven cache restore failed is **not known**.
- **Change (`.github/workflows/ci.yml`):** in all four Java jobs, `setup-java@v5` (GitHub's deprecation
  warning asks for it) with `continue-on-error: true`, and a second identical step only
  `if: steps.java.outcome == 'failure'`. A retry, not a root-cause fix: the cause is outside our code.
- **Checked here:** the workflow parses (`yaml.safe_load`); each of `fixture-build`, `runner`,
  `evidence`, `ui` has the two steps; no `@v4` left. **Not checked here:** the retry path itself —
  it runs only when GitHub's download fails. The PR's own CI shows whether v5 works.

## W20 runner half: deletion checks (2026-11-20)

- **Requirement:** FT004 / ADR-011 / `docs/contracts/interfaces.md` Interface 4 (agreed by M1, M2, M3,
  PR #119). Every kept test is checked by repeated removal; `DiagnosisRuns.deletion_checks`.
- **Files:** `runner/deletion.py` (`DeletionCheck`, `label`, `check_deletions`), `runner/diagnose.py`
  (`run_steps` calls it for `POLLUTER_FOUND`, record step `deletion` with `removed` and `round`, then verifies the **final** set);
  tests `runner/tests/test_deletion.py` (10) and `runner/tests/test_diagnose.py` `TestDeletionChecks` (3)
  plus F1/F3 fixture assertions. Branch `m2/w20-deletion-checks` from `main` `88e90b5`.
- **Test-first (Windows 11, local JDK, Python 3):**
  - Task 1 before code: `py -3 -m unittest runner.tests.test_deletion` → `ModuleNotFoundError: No module named 'runner.deletion'`. After: 5 OK.
  - Task 2 before code: → `ImportError: cannot import name 'check_deletions'`. After: 10 OK.
  - Task 3 before wiring: `runner.tests.test_diagnose.TestDeletionChecks` → `FAILED (failures=2, errors=1)`;
    the FT004 test (ADR-011 T1) failed with `[P, Q] != [P]` — the old code keeps the unneeded Q, as on
    `7cf453d` (2026-11-13 entry). After: OK.
  - One older test's run count changed on purpose: `test_two_polluters_needed_are_minimised_and_verified`
    now counts the `2 × n` deletion runs.
- **Labels at the edge (m = 20):** 19 matched → `NOT_NEEDED` (lower bound 0.764); 18 → `INCONCLUSIVE` (0.699).
- **Whole suite:** every `runner/tests/test_*.py`, `ui.tests.test_server` and every `eval/tests/test_*.py`
  → `Ran 406 tests in 614.351s … OK` (includes the real F1, F3 fixture runs).
- **Real CLI runs, default `class-grouped`:**
  - F3 `odfixture.ToggleVictimTest#expectsNotBothFlagsSet` → record steps `reproduce 1, alone 20, search 16,
    minimise 9, delete 40, verify 20` (run before the review renamed the step to `deletion`). Without `setFlagA` the victim passed 20/20; without `setFlagB`
    20/20 → both `NEEDED` (ADR-011 T3, runner half). Verdict still `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]`:
    M3's `eval/report.py` does not read `deletion_checks` yet.
  - F1 → `VERIFIED (sequence)`; record steps `reproduce 1, alone 20, search 2, verify 20` — **no**
    deletion runs (one polluter: `alone-check`, ADR-011 T4).
- **Not done:** T5 (budget ends mid-check) — no budget before W24; `NOT_RUN` is defined, not produced.
- **Fresh review (Claude Opus, whole change) — 0 critical, 3 important, 5 minor; all fixed test-first:**
  1. Record step was `delete` without the removed test; ADR-011 "Consequences" and ADR-014 §3 say
     `deletion`. RED: `test_deletion_runs_are_recorded_as_their_own_step` → `AssertionError: 0 != 2`.
     Now step `deletion`, each run line has `removed` and `round`.
  2. The CLI `minimised:` line would contradict the report once checks drop a test. RED:
     `summary() got an unexpected keyword argument 'deletion_checks'` (2 tests). Now the line shows
     ddmin's own count (its round-1 checks) and drops "not deletion-verified" when checks ran; a new
     `deletion:` line gives the removal runs, how many dropped and how many inconclusive.
  3. The UI said the deletion checks "have not run yet (W20)" — false once they run. Reworded to what
     `DELETION_EVIDENCE_INCOMPLETE` always means. `eval/report.py`'s similar limitation is M3's: sent to M3.
  - Minors: README state cell; FT004 test now asserts the last 20 runs are `[P, V]`; the other-statuses
    test asserts `check_deletions` is never called (a deliberate break — the guard changed to `if True:`
    — made it fail, then the code was restored); deletion runs are counted from the checks on the CLI
    line; **limitation:** with small `--n`, `NOT_NEEDED` cannot be reached (at `n = 1` a 1/1 match has
    a Wilson lower bound of about 0.21), so a test `ddmin` kept by mistake shows `INCONCLUSIVE`, not
    dropped — and `runs.n < 10` makes the report `INCOMPLETE`, so the verdict stays honest.
- **After the fixes, real F3:** CLI prints `minimised:  16 earlier tests -> 2 polluters in 9 runs (reduced by
  single-trial delta debugging)` and `deletion:   kept tests removed one at a time, 20 runs each (40 runs):
  0 dropped as not needed, 0 inconclusive`; verdict `CANDIDATE` (M3's half pending). Record: step
  `deletion` × 40, `removed` = `setFlagA` round 1 (victim passed 20/20) and `setFlagB` round 1 (20/20).
  UI: `npm test` → 33 passed; `tsc --noEmit` clean.

## A2: independent verification of M1's W21 (FT005 controls, all edges) (2026-11-20)

- **Requirement:** FT005; W21's verifier is M2 (plan). Reproduce [[evidence-m1]] "W21 part 1" and
  "W21 part 2" on my own machine, from `main`, not from M1's description.
- **Machine:** Windows 11, OpenJDK 21.0.9, Apache Maven 3.10.0, Python 3.14.0. A clean worktree of
  `main` `88e90b5` in my scratchpad (removed afterwards).
- **Compile:** `mvn -B -q -f <p>/pom.xml test-compile` for `fixtures/od-fixture`,
  `evidence/tests/resources/m1-selftest`, `evidence/tests/resources/ft005-controls` → exit 0 each.
- **M1's tests:** `set FLAKETRACE_REQUIRE_JVM=1` + `py -3 -m unittest -v evidence.tests.test_extract.ResourceEdgesTest
  evidence.tests.test_extract.Ft005ControlsTest` → `Ran 6 tests in 5.476s … OK`.
- **They fail without the change:** `evidence/extract.py` replaced by `git show 5199ef8^:evidence/extract.py`
  (the commit before M1's W21 part 1), then restored → `ResourceEdgesTest`: `FAILED (errors=3)`, each
  `KeyError: 'resource_edges'` — exactly M1's recorded failure.
- **Whole evidence suite:** `FLAKETRACE_REQUIRE_JVM=1 py -3 -m unittest evidence.tests.test_extract` →
  `Ran 56 tests in 114.257s … OK` (M1 recorded 45 on 2026-11-18; tests added since).
- **Real diagnoses** (`py -3 -m runner diagnose --project evidence/tests/resources/ft005-controls --victim … --records <scratch>`):
  - Control 1 `controls.RestoringVictimTest#check` → `VERIFIED (sequence)`, polluter
    `RestoringPolluterTest#pollute`, resource `static-field controls.State restored (write …pollute@6 ->
    read …check@1)`, "static overlap: a possible mechanism, not confirmed as the cause", 20/20, alone 0/20.
    `resource_edges`: `restored` only — no edge on `State#hidden`, the real reason, as `EXPECTED.md` says.
  - Control 2 `controls.TwoFieldVictimTest#check` → `VERIFIED (sequence)`, resource `State a`, same
    static-overlap line, 20/20, alone 0/20. `resource_edges`: **`a` and `b`** — the extra edge is visible.
  - Both reports: `assurance.resource` = `STATIC_OVERLAP` / `NOT_ASSESSED`; a search of each report for
    "the cause", "caused by", "mechanism", "root cause" finds only the `mechanism` key itself.
- **Result:** matches M1's records on every step. FT005's "Closes when" — no causal label for the
  controls, extra edges disclosed — holds.
- **Differences and unclear steps** (for M1):
  1. **A stale line in both our codes.** Control 2's `limitations` still say "Another shared resource is
     not shown in this report: controls.State#b" (`evidence/extract.py` line 666, M1's), although
     `State#b` is in `resource_edges` since schema v2. `runner/cli.py`'s several-polluter line said the
     same ("… is not shown in this report") — mine; fixed here test-first:
     `runner.tests.test_cli.TestCombineFields` → `FAILED (failures=2)` on the old wording, then the line
     reads "… is not the headline resource; it is listed in resource_edges" → `TestCombineFields` and
     `TestReports` `Ran 26 tests … OK`. The committed `eval/reports/f3.json` (M3's) still has the old
     line until it is regenerated.
  2. M1's record gives `depth_used 2` (the analysis depth); the reports here show each edge at `depth`
     1 (the deeper side of a direct read/write). Not a contradiction — two different numbers.

## A3: independent check of M3's W26a premise on real fastjson; two runner fixes (2026-11-20)

- **Requirement:** W26a's verifier is M2. Reproduce [[evidence-m3]] "W26a steps 1-5" (2026-11-19): the
  build and the step-2 premise (`eval/real-cases/fj03/premise.json`), on my machine.
- **Setup (scratchpad only, nothing installed system-wide, with M2's permission):**
  - JDK 8: Adoptium's newest Windows x64 JDK 8 (8u512, M3's) was served by GitHub as a 1,867-byte file to
    both `curl` and PowerShell (SHA-256 mismatch), while the previous releases served in full — so
    **Temurin 8u502** (`1.8.0_502`, the POC's version that the protocol names), SHA-256
    `3f193fe5e36409c564eb3b7668cb33cab96aa5879d9b284f25f8653e993b1c49` checked against Adoptium's API → `jdk8.zip: OK`. Patch-level difference from M3's 8u512, recorded.
  - fastjson: `git fetch --depth 1` of `e05e9c5e4be580691cc55a59f3256595393203a1`, outside this repo.
- **Why JDK 8:** fastjson's `pom.xml` sets `<jdk.version>1.5</jdk.version>`; JDK 21's javac →
  `error: Source option 5 is no longer supported. Use 8 or later.` (run here). The protocol pins JDK 8.
- **Build:** `mvn -B -DskipTests test-compile` (JAVA_HOME = JDK 8; Maven 3.10.0) → `Compiling 172 source files`,
  `Compiling 2496 source files`, `BUILD SUCCESS` in 2 min 54 s — M3's counts exactly. `git status` in
  fastjson empty after every step.
- **Premise** (scratch script, the real `OrderRunner.run_ordered`, `JAVA_TOOL_OPTIONS=-Duser.timezone=UTC
  -Duser.language=en -Duser.country=US`, lifecycle `class-grouped`):
  victim alone ×10 → `RunTally(n=10, passed=10, matched=0, other=0, infra=0)`;
  `[SerializeWriterTest_14#test_writer_1, victim]` ×10 → `RunTally(n=10, passed=0, matched=10, other=0, infra=0)`;
  reference `junit.framework.AssertionFailedError`, top frame `MaxBufSizeTest.test_max_buf:20`, empty
  message. **Identical to `premise.json`.**
- **A1 end to end (the case M3's CLI refused):** `py -3 -m runner diagnose --project <fastjson>
  --victim com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf --order eval/real-cases/fj03/order.txt`
  → exit 0 in 3 min 11 s: `CANDIDATE`, polluter `SerializeWriterTest_14#test_writer_1`, reproduced 20/20
  (lower bound 0.839), alone 0/20 same and 0/20 other; deletion `DELETION_VERIFIED` (alone check);
  `candidate_reasons` `NO_SUPPORTED_RESOURCE_EVIDENCE`, `resource_edges` `[]` — static analysis finds no
  edge for this real pair (a fact for M1's W25, not a defect).
- **Surprise 1 — my environment:** the first premise run compiled FtHarness with JDK 21, because a
  `C:/…` entry on bash's `PATH` splits at the colon; `cygpath -u` fixed it. It exposed a real defect:
- **Fix 1, `-proc:none` on the harness compile** (`runner/order_runner.py`). On JDK 9+, javac ran the old
  Lombok processor on fastjson's test classpath → `IllegalAccessError … lombok.javac.apt.Processor …
  jdk.compiler` → `ToolError: could not compile FtHarness`. Test
  `TestRealProjectQuirks.test_an_annotation_processor_on_the_classpath_does_not_break_the_harness`
  (a processor that throws in `init`, registered in `META-INF/services`).
- **Surprise 2 — the record header:** `java_version` was `"Picked up JAVA_TOOL_OPTIONS: …"`, not the
  version (`jvm.java.version` was right: `1.8.0_502`). **Fix 2:** `java_version()` skips "Picked up" lines.
  Test `test_java_version_skips_the_java_tool_options_banner`.
- **Test-first for both:** old code → `FAILED (failures=1, errors=1)` on JDK 21 **and** on JDK 8 (CI's);
  fixed → `Ran 2 tests … OK` on both. On real fastjson after the fix: JDK 21 compiles the harness against
  fastjson's classpath; JDK 8 + the protocol's `JAVA_TOOL_OPTIONS` → `java_version()` = `openjdk version "1.8.0_502"`.
- **Whole suite after the fixes:** every `runner/tests/test_*.py`, `ui.tests.test_server`, every
  `eval/tests/test_*.py` → `Ran 410 tests in 612.580s … OK`.
- **Limitations:** one run of each; scratch records, not committed; the shuffled search and steps 6–9 are
  M3's, not run here.

## A4: remove the old `DiagnosisRuns` count fields and the `NO_SINGLE_POLLUTER` alias (2026-11-20)

- **Requirement:** W18 left five count fields (`sequence_n`, `sequence_successes`, `sequence_any_failures`,
  `alone_n`, `alone_successes`) beside the ADR-010 tallies "until W19 reads the tallies", and the alias
  `NO_SINGLE_POLLUTER = INCONSISTENT` for M3's code. W19 is merged; both duplicates go.
- **Who still read them (searched before changing anything):** `eval/report.py:107` (`alone_n`, a
  pre-ADR-008 guard), `eval/tests/test_report.py` (3 constructions), comments in `eval/report.py` and
  `eval/outcome.py`; my runner tests and one UI test string. Nothing imported the alias. The fields were
  required arguments, so both sides had to change in one PR. **M3 agreed (2026-11-20, via M2) to M2
  editing those `eval/` files in this PR.** `eval/stats.py` has its own `sequence_successes` field
  (a different API) and is untouched.
- **Test first:** `test_old_count_fields_and_alias_are_gone` (replaces `test_old_count_fields_agree_with_the_tallies`)
  → on the old code `FAILED (failures=1)` (`Items in the first set but not the second`). After: OK.
- **Change:** `DiagnosisRuns.sequence_tally` and `alone_tally` are now **required** (were `Optional`, default
  `None`), in place of the five fields; `_runs` builds them directly; the alias is gone. `eval/report.py`'s
  pre-ADR-008 guard reads `alone_tally.n == 0`, after the existing None-tally guard. Tests read the tallies.
  `docs/contracts/interfaces.md` Interface 3's wording ("M2 passes raw counts …") now names the tallies —
  a contract text change: M3 agreed, M1 approves in the PR.
- **Fast tests:** runner (`TestRunSteps`, `TestTallies`, `TestDeletionChecks`, CLI `TestReports`, `TestCombineFields`,
  `TestInputErrors`, `test_deletion`) → `Ran 77 tests … OK`; whole `eval/tests` → `Ran 123 tests … OK`;
  `ui.tests.test_server.TestJobResult` → 7 OK.
- **Whole suite:** every `runner/tests/test_*.py`, `ui.tests.test_server`, every `eval/tests/test_*.py` and
  `evidence.tests.test_extract` → `Ran 466 tests in 719.625s … OK` (the UI test's message string was
  changed after this run started; `TestJobResult` re-run alone afterwards → 7 OK).

## Review of M3's W20 report half (PR #129); deletion-status order fixed in `eval/report.py` (2026-11-20)

- **Requirement:** Interface 4 — "`INCONCLUSIVE` ranks above `INCOMPLETE`: evidence against the result
  outweighs missing evidence." M3 flagged one reading (a short run count rules out `VERIFIED` even when
  every check says `NEEDED`); I agree with it as ADR-011's author.
- **Defect found in review:** `eval/report.py` checked "any `NOT_RUN` or `runs.n < 10`" before "any
  `INCONCLUSIVE`". With `-n 5` every check is short, so a set holding an `INCONCLUSIVE` check was reported
  `INCOMPLETE` (missing evidence) instead of `INCONCLUSIVE` (evidence against). Edited with M3's agreement.
- **Test-first:** new `TestDeletionChecksW20.test_inconclusive_outranks_a_short_run_count` (one `NEEDED` 5/5,
  one `INCONCLUSIVE` 2 passed/3 matched). Unfixed: `py -3 -m unittest eval.tests.test_report.TestDeletionChecksW20.test_inconclusive_outranks_a_short_run_count`
  → `FAILED (failures=1)`, got `['DELETION_EVIDENCE_INCOMPLETE']`. Fixed (order: `INCONCLUSIVE`, then
  `NOT_RUN`/short, then all `NEEDED`) → `OK`. `py -3 -m unittest discover -s eval/tests` → `Ran 129 tests … OK`.
- **F3 re-checked on `main` `bb85513`:** `py -3 -m unittest runner.tests.test_cli.TestCliOnFixture.test_f3_two_polluters_both_needed_gives_verified`
  (real JVM, JDK 21.0.9) → `Ran 1 test in 107.439s … OK`; committed `eval/reports/f3.json`: `VERIFIED`, two
  checks `NEEDED` n=20. Claims row E14, `docs/04-Implementation/diagnose-cli.md` and the demo plan updated
  from "F3 is `CANDIDATE`".
- **Limitations:** the short-`INCONCLUSIVE` case is tested with a fake check, not a real `-n 5` run; G2
  stays open until M1 reproduces T3.

## W24 runner half: budget ledger (2026-11-20)

- **Requirement:** Interface 6 (agreed by M1, M2, M3 on 2026-11-20; PR #131), ADR-014 §1–§3: every run
  counted in test-method invocations; a `3 × n` verification reserve; a run that would cross the
  exploration cap not started; `BUDGET_EXHAUSTED`; `DiagnosisRuns.budget`; a `budget-stop` record line.
- **Code:** `runner/budget.py` (new: `Budget`, `BudgetAccount`, `BudgetedRunner`, `BudgetExhausted`),
  `runner/diagnose.py` (`check_budget`, `run_steps` → `_steps`, status `BUDGET_EXHAUSTED`, header key
  `budget`), `runner/deletion.py` (`can_afford(cost, kept)` → `NOT_RUN`), `runner/recording.py`
  (`write_event`), `runner/cli.py` (`--budget-invocations`, `--budget-seconds`, `budget:` line).
- **Test-first (each seen failing first, fake runner, Windows 11, Python 3.14, JDK 21.0.9):**
  - `py -3 -m unittest runner.tests.test_budget` → `ModuleNotFoundError: No module named 'runner.budget'`;
    after → `Ran 11 tests … OK`.
  - `py -3 -m unittest runner.tests.test_deletion` → `FAILED (errors=4)` (`unexpected keyword argument
    'can_afford'`); after → `Ran 14 tests … OK`.
  - `py -3 -m unittest runner.tests.test_diagnose.TestBudget` → `ImportError` (`BUDGET_EXHAUSTED`); after →
    `Ran 9 tests … OK`. These are ADR-014's tests to write first: ten candidates with the polluter last,
    n=20, limit 80 → `BUDGET_EXHAUSTED`, alone 20/20 runs, spent reproduce 11 / alone 20 / search 8,
    4 of 10 candidates tried; limit 72 → refused naming 73; the recount from the record; B5 (limit 150:
    one deletion check `NEEDED`, the other `NOT_RUN`); B6 (limit 74: verify 13 runs); B6 zero; a seconds
    limit.
  - CLI: `TestBudgetOptions`, `TestBudgetLine`, a summary test with a `NOT_RUN` check → `ImportError`
    (`budget_line`); after → `Ran 22 tests … OK`.
- **Found while planning:** the summary's deletion line read `runs.n` of every check, so a `NOT_RUN`
  check (`runs = None`) would have crashed it; now counted apart ("1 not run (budget)"), with a test.
- **Whole suites after the change:** `py -3 -m unittest discover -s runner/tests` (real JVM) →
  `Ran 287 tests in 622.208s OK`; `py -3 -m unittest discover -s eval/tests` → `Ran 129 tests OK`;
  `py -3 -m unittest ui.tests.test_server` → `Ran 31 tests OK`.
- **Real runs, od-fixture F2** (`odfixture.FeatureVictimTest#expectsTurboDisabled`, default options):
  - no limit → `VERIFIED (sequence)`, `budget: spent 82 invocations, no limit (reserve 60); search tried
    7 of 7 candidates`; 48 `run` lines (1 + 20 + 7 + 20);
  - `--budget-invocations 69` → exit 2, `below the minimum 70 for n=20` (reserve 60 + 8 tests + 2); no
    record file written;
  - `--budget-invocations 70` → exit 3, `No report: BUDGET_EXHAUSTED`, `spent 30 of 70 invocations …
    search tried 1 of 7 candidates; stopped in search`; 22 `run` lines and one
    `{"type": "budget-stop", "phase": "search", "would_cost": 2, "spent": 30}`.
- **Fresh review (one reviewer, Claude Opus 5.5) and fixes, each test-first:** (1, Important) an `INCONSISTENT`
  diagnosis with a long prefix (60 tests, n=20, limit 302) became `BUDGET_EXHAUSTED` at the verify step,
  although exploration had finished — now stays `INCONSISTENT`, tallied by its full-order re-check when no
  verify run fits (`sequence.n` 0 is refused by `eval.outcome`; checked); Interface 6 does not cover this case,
  flagged to M1/M3; (2) the B6 `budget-stop` line came before the short verify and stated `len × n` — now after
  the runs, with the first refused run's cost (3); (3) a search cut after a shuffled order reproduced tallied the
  starting order — now the reproducing run; (4) `candidates_tried` counts search runs; (5) new tests: the round-2
  hold-back (a mutation using round 1's count fails it), the B6 line, no record file on a refused limit, the real
  `assemble_report` refusing `BUDGET_EXHAUSTED`; (6) the no-report text drops a developer note, and the UI's
  budget label says "in the command line only". Each new test failed on the code before its fix (4 failures).
  After the fixes: runner `Ran 292 tests in 537.158s OK` (real JVM), eval `Ran 129 tests OK`,
  `ui.tests.test_server` `Ran 31 tests OK`, `ui/web` `npm test` → `33 passed`.
- **Limitations:** no report for `BUDGET_EXHAUSTED` until M3's half (exit 3); `analysis_seconds` is
  `None` until W25; the seconds limit is tested with a fake clock only; one real run of each.

## W25 runner half: search policy (2026-11-20)

- **Requirement:** Interface 7 (agreed by M1, M2, M3 on 2026-11-20; PR #133), ADR-014 §4–§6: `--policy
  original|ranked|random`, `--scope module|package`, one candidate order per diagnosis (the same endpoint),
  the fallback, ADR-014 §6 deepening, `analysis_seconds`, a `ranking` record line.
- **Code:** `runner/policy.py` (new: `SearchPolicy`, `choose_order`, `EvidenceRanker` over M1's `rank_candidates`
  and `AnalysisCache`, `in_package`), `runner/diagnose.py` (`run_steps(policy, scope, ranker_for)`,
  `diagnose(policy, scope)`, `DiagnosisRuns.search`, header keys), `runner/budget.py` (`write_event`,
  `account(policy, analysis_seconds)`), `runner/cli.py` (`--policy`, `--scope`, `search:` line).
- **Test-first (fake runner and `FakeRanker`, Windows 11, Python 3.14, JDK 21.0.9):**
  - `py -3 -m unittest runner.tests.test_policy` → `No module named 'runner.policy'`; after → `Ran 15 tests OK`
    (evidence first, no edge keeps the order, the fallback, the four ways deepening stops, a ranker that drops a
    candidate raises).
  - `TestSearchPolicy` (7) and the budget test → 8 errors (`unexpected keyword argument 'policy'`); after → OK.
    ADR-014's test: the polluter is candidate 9 of 10 and the only one with an edge → `original` search 18
    invocations, `ranked` 2, the same verdict, totals 16 apart.
  - Task 3 → `ImportError` (`EvidenceRanker`, `search_line`); after → `Ran 45 tests OK`, including two real
    `EvidenceRanker` tests on the compiled od-fixture (F1's polluter ranked first, score ≥ 1).
- **Whole suites:** runner `Ran 325 tests in 715.912s` with 1 failure: a real F1 test counted every record line
  (45 != 44, the new `ranking` line); it now counts run lines and exactly one ranking line → OK on re-run.
  eval 129 OK, `evidence.tests.test_extract` 57 OK, `ui.tests.test_server` 31 OK, `ui/web` `npm test` 33 passed.
  Real F1–F4 with `--policy ranked` → all `VERIFIED` (the same verdicts as `original`, ADR-014's test).
- **Real runs, od-fixture F2** (`odfixture.FeatureVictimTest#expectsTurboDisabled`, no limit): `original` →
  `VERIFIED`, 82 invocations, 7 of 7 candidates tried; `ranked` → `VERIFIED`, depth 2, 1 of 7 candidates with
  evidence, 70 invocations, 1 of 7 tried; `random --seed 3` → `VERIFIED`, 76 invocations, 4 of 7 tried. The same
  polluter each time. F1 with `--scope package --policy ranked` → `VERIFIED`, 1 of 2 tried.
- **Fresh review (one reviewer, Claude Opus 5.5) and fixes, each test-first (6 new tests failed first):**
  (1, Important) a project without `target/classes` made `--policy ranked` stop with a traceback after the JVM
  runs, because `Project` was built outside P3's fallback — now built on first use, so it falls back with a note;
  (2, Important) "the same endpoint" overstated it: when several earlier tests each pollute alone, the policies
  can blame different tests (reviewer's probe: `original` blamed C1, `ranked` C4) — docs reworded, flagged to M3
  and M1 for Interface 7's wording and the comparison; (3) a diagnosis that never searched printed "original
  order" — now "no single-polluter search ran"; (4) ranked with no evidence now says the original order was kept;
  (5) `ranked` without a ranker and (7) `priority` with a non-original policy are refused before any run; (6) a
  ranker returning a different set falls back instead of raising; (8) `--scope package` leaving no candidate says
  to re-run with `--scope module`. Two need a contract change and were raised with M1/M3, not built: a per-candidate
  note for unanalysable candidates in the ranking line, and skipping ranking once the seconds limit is spent.
  After the fixes: runner `Ran 330 tests in 739.350s OK` (real JVM), eval 129 OK, `ui.tests.test_server` 31 OK.
- **Limitations:** these are fixture cases we wrote, with the ground truth known; they show the policies work
  and reach the same endpoint, **not** that ranking helps in general — that is M3's measurement (ADR-014
  evidence items 4–5, the real case W26b). The rule is M1's, fixed before any measured run (PR #112). No report
  field yet: `search_policy` is M3's half.

## Follow-ups after M3's W24 report half (#135) and M1's W20 verification (#137) (2026-11-20)

- **Requirement:** with `BUDGET_EXHAUSTED` now a report, the CLI must not present the starting order's runs as a
  verified reproduction, and its "no report yet" text is dead; M1 asked (PR #137) that the `deletion:` line say so
  plainly when every kept test is needed.
- **Test-first** (`runner/tests/test_cli.py`): `test_budget_exhausted_writes_a_report_that_claims_no_sequence`
  and `test_summary_says_each_kept_test_was_confirmed_needed` → `FAILED (failures=2)` (the summary printed
  `reproduced: 1/1 (lower bound 0.207)` and the old deletion line); after → OK.
- **Suites:** `py -3 -m unittest runner.tests.test_cli` (real fixture) → `Ran 85 tests in 405.650s OK`;
  `ui.tests.test_server` OK.
- **Real runs** (od-fixture, JDK 21): F3 → `deletion:   each kept test confirmed needed: removed one at a time, 20
  runs each (40 runs), the victim passed every run`; F2 with `--budget-invocations 70` → `UNRESOLVED
  (BUDGET_EXHAUSTED)`, exit 0, `reproduced: no sequence verified (the starting order failed 1 of 1 run(s) before
  the budget ran out)`.
- **Not changed:** claims row G2 stays `OPEN` until M3 agrees to settle it (it is M2's and M3's).

## Ranking-line notes; G2 settled; Interface 6 step 3 on F2 (2026-11-21)

- **Ranking notes (M1's #138 suggestion, agreed by M3; Interface 7 P6 now lists `notes`).** Test-first:
  `TestEvidenceRanker.test_an_unanalysable_candidate_keeps_its_note` (real fixture classes, a candidate
  `odfixture.NoSuchTest#x`) and `TestSearchPolicy.test_ranking_line_names_candidates_that_could_not_be_analysed`
  → `FAILED (errors=3)` (`no attribute 'notes'`, `KeyError: 'notes'`); after → `Ran 40 tests OK`. The note is M1's
  own text: `test class not found in project classes: odfixture.NoSuchTest`.
- **G2 → SETTLED** with M3 (M1's reproduction, PR #137), scope kept: each kept test removed alone, not every
  subset. E14's status follows.
- **Interface 6 step 3, ADR-014 evidence items 1–3 on F2** (`odfixture.FeatureVictimTest#expectsTurboDisabled`,
  n=20, `--budget-invocations 70`, the B2 minimum; JDK 21, default options):
  - `--policy original` → `UNRESOLVED (BUDGET_EXHAUSTED)`, exit 0; spent 30 (reproduce 8, alone 20, search 2);
    22 `run` lines (1 + 20 + 1) and one `budget-stop` (`search`, would_cost 2) — **item 1**: the next run was not
    started; **item 2**: a report with a budget account; alone ran 20 of 20.
  - `--policy ranked` → `VERIFIED (sequence)`, exit 0, polluter `FeaturePolluterTest#enableTurbo` tried first;
    spent **70 of 70** (reproduce 8, alone 20, search 2, verify 40); 42 `run` lines; no `budget-stop` — **item 3**:
    the alone check and the full 20-run sequence check ran, paid by the 3n reserve. `notes: {}`.
  - M3 ran item 2 at limit 72 (PR #139); these runs are mine. **Limitation:** one fixture pair, written by us with
    a known polluter; it shows the reserve and the stop work, not that ranking saves runs in general (M3's
    measurement, W26b).

## W23, M2's half: bundle writer and replay (2026-11-21)

- **Requirement:** Interface 8 (agreed by M1, M2, M3 on 2026-11-21, with two clarifications: replay bundles carry
  `reference_signature`; "same" includes the polluters), ADR-013 §1, §3.
- **Code:** `runner/bundle.py` (new: `redact`, `assert_clean`, `clean_url`, `manifest`, `write_bundle`,
  `read_bundle`), `runner/replay.py` (new: `replayable`, `report_reference`, `replay_steps`, `compare`, `replay`),
  `runner/diagnose.py` (`prepare_runner` and `record_header` extracted, behaviour unchanged), `runner/cli.py`
  (`--bundle`, `replay` subcommand), `.gitignore` (`flaketrace-bundles/`).
- **Test-first:** `runner.tests.test_bundle` → `No module named 'runner.bundle'`, then 10 OK; the Maven-version test
  failed first (`'Apache Maven 3.10.0 (…)' != '3.10.0'`); `TestBundleOption` → `no attribute 'write_bundle'`;
  `runner.tests.test_replay` → `No module named 'runner.replay'`; `TestReplayCommand` → 2 errors. One test of mine
  was wrong and corrected: dropping a polluter needs `n = 20` (3/3 has Wilson lower bound 0.44, `INCONCLUSIVE`).
- **Real runs** (od-fixture, Windows 11, JDK 21.0.9, Maven 3.10.0): F1
  (`odfixture.ConfigVictimTest#expectsDefaultMode`) and F3 (`odfixture.ToggleVictimTest#expectsNotBothFlagsSet`):
  `diagnose --bundle`, then `replay <bundle> --project fixtures/od-fixture` → exit 0, every row `same` (F1: polluter
  `ConfigPolluterTest#pollute`, 20/20 matched, 20/20 passed alone, deletion `NEEDED`; F3: both polluters, both
  deletion checks `NEEDED`). A scan of all 20 written files found no home path and no user name as a path part.
- **Fresh review** (one reviewer, Claude Opus 5.5): 2 Important — the comparison written to `replay.md` marked Maven
  `DIFFERENT` while the printed one said `same`; replay took `n` and the lifecycle from `manifest.json`, which is not
  checksummed — and 11 Minor (malformed manifest traceback, home matched inside a longer user folder, case-sensitive
  paths, a local origin path refused instead of redacted, `clean_url` gaps, one-letter user names hitting JSON
  escapes, a half-written folder, R7 not enforced, `ExtractError` traceback, replay's `in-place` option, a doc
  pointer). All fixed; 12 new tests, each failing first.
- **After the fixes:** runner `Ran 372 tests in 816.327s OK` (real JVM), eval 136 OK, `ui.tests.test_server` 31 OK;
  real F1 and F3 replayed again → exit 0, every row `same`, and the `Maven:` row in each `replay.md` now reads
  `3.10.0 -> 3.10.0 same`, as printed; 20 files scanned, no personal path.
- **Limitations:** `verify` (M3) does not exist yet, so no bundle has been recounted; one machine; fixture cases only.

## F1 fixture bundle committed; Interface 7 wording; G8 settled (2026-11-21)

- **F1 bundle** (`eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/`, with M3's agreement; M1's W32 case): made with
  `py -3 -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode
  --bundle flaketrace-bundles` from a clean worktree of `main` at `03ada56` → `VERIFIED (sequence)`; manifest
  `tool.dirty false`, `subject.dirty false`, repository `fixture`, module `fixtures/od-fixture`; the command line holds
  only relative folders.
- **Found and fixed before committing:** this machine has `core.autocrlf=true` and the repository had no
  `.gitattributes`, so Git would have turned the bundle's LF into CRLF on Windows checkouts and every checksum would
  fail. New `.gitattributes`: `eval/bundles/** -text`. Checked: `git hash-object --path=<file>` equals
  `git hash-object --no-filters <file>` for all five files ("unchanged by git").
- **Test-first:** `TestCommittedBundles.test_every_committed_bundle_reads_back` → `FAILED` ("no committed bundle found
  under eval/bundles/"); after the copy → OK (checksums match, no CRLF, tool not dirty). It also runs in CI.
- **Replay of the committed copy:** `py -3 -m runner replay eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode --project fixtures/od-fixture`
  → `verdict: VERIFIED -> VERIFIED same`, exit 0.
- **Interface 7 wording** corrected as agreed by M1, M2, M3; **G8 → SETTLED**, scoped (invocation budget on the
  fixture by all three; seconds limit unit-tested only; ranking is G9).

## FT021: the reset-sensitive control (2026-11-21)

- **Requirement:** FT021 — "add a reset-sensitive control"; "the reset boundary is written down and matches the
  code" (ADR-012 §1). Verifier: M3.
- **Code:** `runner/tests/resources/reset-control/` (new Maven project: `ResetState`, `ResetWriterTest`,
  `ResetReaderTest`; Surefire skipped, with the reason in the POM) and `TestResetControl` in
  `runner/tests/test_order_runner.py`, whose expectations are one table mirroring ADR-012 §1.
- **Test-first:** `py -3 -m unittest runner.tests.test_order_runner.TestResetControl` → error (no control project:
  Maven exit 1); after → `Ran 2 tests in 29.075s OK` (Windows 11, JDK 21.0.9, Maven 3.10.0).
- **Result** (real JVMs, a temporary working directory, markers removed before and after):
| State | Between orders (a new JVM) | Shown by |
| --- | --- | --- |
| A static field | **reset** | `ResetReaderTest#staticFieldIsDefault` passes |
| A system property | **reset** | `ResetReaderTest#systemPropertyIsUnset` passes |
| A file in the temp folder | **not reset** | `ResetReaderTest#tempFileIsAbsent` fails |
| A file in the working directory (the project, or its disposable copy) | **not reset** | `ResetReaderTest#workingDirFileIsAbsent` fails |
| Environment variables, the clock and timezone | not reset | not testable from a Java test (it cannot change them) |
  The same in `class-grouped` and `per-method`. In one JVM (writer then readers) all four readers fail — no vacuous
  pass. `py -3 -m unittest runner.tests.test_order_runner` → `Ran 50 tests OK`; no marker left behind.
- **Limitations:** one machine; environment variables and the clock are not testable from Java; detecting such
  leftovers during a diagnosis is FYP-2 (risk register).

## W35, M2's half: pair mode (2026-11-22)

- **Requirement:** ADR-016 (revised, accepted by M1, M2, M3 2026-11-22) and Interface 9 (agreed, `search_mode`
  rename agreed): a known victim that no order makes fail is diagnosed from `[candidate, victim]` pairs.
- **Code:** `runner/search.py` (`find_pair`), `runner/budget.py` (the `pair` phase), `runner/diagnose.py`
  (`_pair_steps`, `_certify` shared by both modes, `search_mode`, four `DiagnosisRuns` fields), `runner/cli.py`
  (`--search`, the leakage refusal, `pairs:` and `next:` lines).
- **Test-first:** `TestFindPair` (6) → ImportError; `TestPairMode` + `TestDiagnosePairInputs` (15) → 14 errors
  (`DiagnosisRuns` has no `search_mode`); `TestSearchMode` (6) → 6 errors (`summary()` arguments, unknown `--search`);
  budget's pair test and spent dict → 2 failures. All pass after.
- **Found on the way:** (1) M3's `classify()` refuses a real failure without a reference, so a one-off pair failure
  that is not adopted is tallied directly (as `other`); a test shows M3's report gives `UNRESOLVED (NOT_REPRODUCED)`,
  nothing blamed. (2) `summary()` has a local `runs`; the new parameter is `diagnosis` (four TestReports tests caught
  the clash). (3) Interface 9's field `search` clashed with W25's `DiagnosisRuns.search`; renamed `search_mode` before
  code, agreed by all three.
- **Real runs** (Windows 11, JDK 21.0.9, Maven 3.10.0, fixtures/od-fixture):
  - F1 `--search pairs --bundle`: `VERIFIED (sequence)`, `ConfigPolluterTest#pollute` found after 2 of 17 pairs,
    66 invocations (20 alone, 3 pair runs, 40 verify), exit 0, 40 s. Its bundle: `replay` → `same`, exit 0; the
    record has 3 `pair` lines and `"search_mode": "pairs"`; no personal path in the bundle.
  - N3 order mode (`--n 5`): `NOT_REPRODUCED`, with `next: … re-run with --search pairs (17 candidates, about 1 min
    at 0.4 s per JVM launch)`. N3 pair mode: `NOT_REPRODUCED`, "no pair failed twice in a row (17 of 17 pairs
    tried)", 39 invocations.
  - Full suite: `py -3 -m unittest discover -s runner/tests -p "test_*.py"` → `Ran 411 tests in 829.067s OK` (after the review fixes; 403 OK before them).
  - **FJ-03 from the victim alone** (with the member's permission: Temurin 8u502, SHA-256 `3f193fe5…` checked against
    Adoptium's API; fastjson `git fetch --depth 1` of `e05e9c5e4be580691cc55a59f3256595393203a1`, outside this repo;
    `mvn -B -q -DskipTests test-compile` → exit 0, `git status` empty;
    `JAVA_TOOL_OPTIONS=-Duser.timezone=UTC -Duser.language=en -Duser.country=US`):
    `py -3 -m runner diagnose --project <fastjson> --victim com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf
    --search pairs --scope package --policy original --n 20 --bundle …` → exit 0 in 8 min 1 s: **`CANDIDATE`**,
    polluter **`SerializeWriterTest_14#test_writer_1`** found after **368 of 524 pairs** (the POC's recorded position
    for the original order), reproduced 20/20, alone 0/20, deletion check from the alone runs 20/20 passed;
    **798 invocations** (20 alone, 369 pair runs = 368 + 1 re-run, 40 verify), 409 launches, 315 s of runs.
    `CANDIDATE`, not `VERIFIED`: no static edge (M1, #145). The record has 369 `pair` lines; no personal path in the
    bundle. For comparison, order mode on the same scope (M3, #156): 12,817 invocations, `NOT_REPRODUCED`.
    Candidates are 524, not #156's 260: order mode searches only tests before the victim; pair mode every package
    test but the victim (Interface 9 P2), as the POC did. This run started before the review fixes below, so its
    summary printed the old wording; the report and bundle do not contain that line. The bundle is kept outside the
    repo: `eval.bundle verify` cannot recount a pair-mode bundle until M3's half (review finding 6).
- **Fresh review** (opus, 12 findings) — fixed test-first: the pair-mode budget minimum is reserve + 4 (one pair and
  its re-run; at reserve + 2 a failing pair could never be adopted); the `next:` estimate uses the mean seconds of
  the alone runs (one-test JVMs) and counts candidates + 2n launches, labelled "at most"; `pairs:` says "pair mode
  does not run the project's own orders" (the old wording was not backed) and names one-off failures, crashes and a
  budget stop instead of "never failed"; no "starting order" wording in pair mode; `next:` after `--order` says
  "without --order", and keeps `--scope package`; the unreachable verify cut is an assertion; a priority list is
  refused before any record is written. For M3/the team: report wording, `order_exploration` and `verify` for pair
  mode; Interface 9's verbatim limitation sentence; `reproduced_by` "order" for the victim alone.
- **Limitations:** the `next:` estimate covers the pairs only (not Maven setup or verification) and assumes the
  run's own seconds per JVM launch; M3's report wording for pair mode (`reproduced_by`, the constructed-pair line,
  "pairs" instead of "discovered order") is her half of W35.

## W23 reproduction gaps 1, 2, 5, 6 (2026-11-22)

- **Requirement:** FT009 / claim G7 — M1's independent reproduction (PR #159) found that `replay.md` alone did not get
  her there; gaps 1, 2, 5 and 6 are M2's (`runner/bundle.py`, `runner/replay.py`).
- **Test-first:** three new `TestBundle` tests and `TestOsRow` → 4 failures on the old code (bare name and
  `<checkout of the subject>` in `replay.md`; `Windows-11-10.0.26300-SP0` vs `Windows-10-10.0.26300-SP0` →
  `DIFFERENT`); the guard test (different build or system → `DIFFERENT`) passed before and after. After:
  `runner.tests.test_bundle runner.tests.test_replay` → 36 OK; `eval/tests` → OK.
- **Real check** (Windows 11, JDK 21.0.9, Maven 3.10.0): a real F1 bundle written to `flaketrace-bundles`; its
  `replay.md` commands run **verbatim in Windows cmd** from the repo root (`python` → `py`, as the file says):
  `verify` → `OK`, exit 0; `replay` → `VERIFIED -> VERIFIED same`, every environment row `same`, exit 0.
- **Not run:** the 3.11 naming on this laptop (only Python 3.14 is installed, which says `Windows-11`); covered by
  the unit test with M1's exact strings.
- Full suite: `py -3 -m unittest discover -s runner/tests -p "test_*.py"` → `Ran 381 tests in 813.833s OK` (with the next commit's runner fix also in the tree).
- **Limitations:** committed bundles keep their old `replay.md` (checksummed); M3's README findings 3 and 4 are hers.

## W26b step 9: independent repeat of M3's package-scope run; the test-output decoding bug (2026-11-22)

- **Requirement:** real-case protocol step 9 — "an independent repeat of step 6 or 7 by another member on another
  machine". The run repeated: M3's #156, `--scope package --n 20 --policy original`, no `--order`, no limit.
- **Setup** (with the member's permission, scratchpad only): Temurin 8u502 (SHA-256 `3f193fe5…` checked against
  Adoptium's API); fastjson `git fetch --depth 1` of `e05e9c5e4be580691cc55a59f3256595393203a1`;
  `mvn -B -q -DskipTests test-compile` → exit 0; `JAVA_TOOL_OPTIONS=-Duser.timezone=UTC -Duser.language=en
  -Duser.country=US`; Windows 11, Python 3.14.
- **Result** (`py -3 -m runner diagnose --project <fastjson> --victim
  com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf --scope package --n 20 --policy original`): exit 0 in
  7 min 12 s, **`UNRESOLVED (NOT_REPRODUCED)`, 12,817 invocations** (reproduce 5,220, shuffle 7,577, alone 20), 31
  shuffled orders, no infrastructure failure, search tried 0 of 260 — **identical to M3's two runs**. Differences:
  JDK 8u502 here vs her 8u512; 288 s of runs here vs her 750 s.
- **Surprise:** twelve `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa0` tracebacks from Python's
  subprocess reader threads. Cause: `OrderRunner.run_ordered` and `list_methods` captured the test JVM's output and
  decoded it as UTF-8, though nothing reads it (outcomes come from the results file); fastjson's tests print 0xA0.
  Probe: on Windows the reader thread dies and the run continues (outcomes were unaffected); on Linux CPython decodes
  in the calling thread, so the error would stop the diagnosis (reasoned from CPython's POSIX `subprocess`, not run:
  no Linux here).
- **Fix, test-first:** `runner/tests/resources/NonUtf8OutputProbeTest.java` prints 0xA0 on stdout and stderr;
  `test_output_that_is_not_utf8_neither_breaks_nor_leaks_an_error` → failed (`UnicodeDecodeError('utf-8',
  b'ok \xa0\n', …)` in a thread). The output is now sent to the null device and the test list passed as bytes →
  passes; `runner.tests.test_order_runner` → 51 OK; full runner suite → `Ran 381 tests in 813.833s OK`.
- **Re-run with the fix:** the same command → 7 min 16 s, **0 tracebacks**, the same `NOT_REPRODUCED`, 12,817
  invocations.
- **Limitations:** one more machine, same OS family as M3's; the Linux effect is reasoned, not observed.

## W35 follow-up: a replayed pair-mode bundle stays pair mode (2026-11-22)

- **Requirement:** M3's finding on PR #164: `replay_steps` never set `reproduced_by`/`search_mode`, so a replayed
  pair-mode bundle would be reported `reproduced_by: "order"`, with `order_exploration` and without the
  constructed-pair line.
- **Test-first:** `test_the_mode_is_carried_and_failing_alone_is_an_order`,
  `test_a_pair_mode_bundle_replays_as_pair_mode` (a real fake-runner pair-mode report bundled with
  `search_mode: "pairs"` and replayed through `replay()` and M3's `assemble_report`),
  `test_an_order_mode_bundle_without_the_fields_stays_order` → 3 errors (`replay_steps() got an unexpected keyword
  argument 'search_mode'`; `KeyError: 'search_mode'` in the replay's header). After: `runner.tests.test_replay
  runner.tests.test_bundle` → 39 OK; `eval/tests` → OK.
- **Docs:** Interface 9's limitation sentence and ADR-016 §3's `"order"` definition reworded as agreed by M1, M2, M3
  on 2026-11-22; claim E16 settled (M1's reproduction #163, M3's report half #164).
- **Not run:** a real replay of a committed FJ-03 pair bundle (needs the fastjson checkout's 20+40 JVM runs; the
  fake-runner test exercises the same path).

## Replay takes the mode from the record (M1's #169 finding) (2026-11-24)

- **Requirement:** M1's #169 — her FJ-03 pair bundle, written on `7f95297` (after #160, before #164), replayed as
  `reproduced_by: "order"`, without the constructed-pair line.
- **Reproduced** with a probe using the test suite's helpers (a fake-runner pair-mode report without the field,
  header `search_mode: "pairs"`): `exit 0 | replay header search_mode: pairs | replayed reproduced_by: order |
  constructed-pair line: False`.
- **Root cause:** `runner/replay.py` passed `report.get("reproduced_by") or "order"`, although it had just read
  `search_mode: "pairs"` from the checksummed header; #167's tests covered "both present" and "both absent" only.
- **Design B** (approved): derive from the header; refuse a disagreeing report (exit 2), as R2 does for `n`/`lifecycle`.
- **Test-first:** `test_a_pair_bundle_from_before_the_report_field_replays_as_pair` → `AssertionError: 'order' !=
  'pair'`; `test_a_report_that_disagrees_with_its_record_is_refused` → error (replay went on to `prepare_runner`).
  After: `runner.tests.test_replay runner.tests.test_bundle` → 41 OK; `eval/tests` → OK; the probe → `pair`, the
  constructed-pair line present.
- **Committed bundles:** none would be refused (header mode vs report field, all 24): 7 `pairs`/`pair`, 17
  `order`/no field.
- **Not run:** a real replay of M1's bundle (it is on her laptop); the probe exercises the same `replay()` path.

## Every committed bundle verified by a test (2026-11-24)

- **Requirement:** after #164, 16 of the 24 committed bundles failed `eval.bundle verify` for two days unnoticed:
  no test ran the verifier on `eval/bundles/` (`runner/tests/test_bundle.py::TestCommittedBundles` checks only
  checksums and line endings).
- **Code:** `eval/tests/test_committed_bundles.py` (M3's folder, added with her agreement; her tests untouched):
  `test_every_committed_bundle_verifies` and `test_the_check_catches_a_required_field_without_a_version_bump`
  (the #164 incident re-enacted: the v2 schema made to require `reproduced_by`).
- **Surprise, fixed in the test:** the first re-enactment validated v2 reports against v3; it also rejected the 8
  newer bundles (v3 requires `schema_version: 3`), so it did not re-enact #164. Re-enacted as #164 actually was: v2
  itself requiring the field.
- **Result:** `py -3 -m unittest -v eval.tests.test_committed_bundles` → 2 OK; the re-enactment names exactly the
  16 pre-W35 bundles, first problem `report.json does not validate against the schema: 'reproduced_by' is a
  required property` (the real incident's message). `py -3 -m unittest discover -s eval/tests -p "test_*.py"` →
  `Ran 165 tests OK`. CI runs it: the python-eval job lists every `eval/tests/test_*.py`.

## UI demo, task 1: the run options reach the CLI (2026-11-27)

- **Requirement:** the UI is the Final demo (design `docs/superpowers/specs/2026-11-27-ui-demo-design.md`, approved);
  the server passed only `--n` and `--order`.
- **Code:** `ui/server.py` — `OPTIONS` (request field → CLI flag and check), `check_diagnose_request`, `Jobs.start(...,
  options)`, the bundle in the job's folder and in the result, `job_timeout` (default 1800 s, env
  `FLAKETRACE_UI_JOB_TIMEOUT_S`), `health()["job_timeout_s"]`; `ui/tests/fake_cli.py` writes a bundle folder when asked.
- **Test-first:** `TestRunOptions` (6 tests) → 11 subtests "unexpectedly None", 1 refusal mismatch, 2 errors
  (`job_timeout` missing). After: `py -3 -m unittest ui.tests.test_server` → `Ran 37 tests OK` (including the real F1
  run).

## UI demo, task 2: committed bundles and checking a folder (2026-11-27)

- **Requirement:** design goals 4 and 5a — open committed evidence with a fresh `verify`; check a bundle folder by path
  (demo step 6, M2's choice A).
- **Code:** `ui/server.py` — `list_bundles()`, `open_bundle(name)` (exact folder names only), `check_bundle(path)`
  (`eval.bundle.verify_bundle`, read-only); `GET /api/bundles`, `GET /api/bundles/<name>`, `POST /api/check-bundle`.
- **Test-first:** `TestCommittedEvidence` (6 tests) → 5 errors (`cannot import name …`), 1 failure (404 for
  `/api/bundles`). After: 6 OK — the step-5 FJ-03 bundle verifies; a copy with `"n": 20` changed to 21 in
  `report.json` → `ok: false`, problem names the checksum; `..`, `..%2Freports`, an absolute path, an unknown name →
  404 / not opened; a missing or non-bundle folder → `ok: false` with a reason. `ui.tests.test_server` → `Ran 43
  tests OK`.

## UI demo, task 3: how the failure was reproduced (2026-11-27)

- **Requirement:** design goal 3 — the Diagnosis step says how the failure was reproduced, from the report alone.
- **Code:** `ui/web/src/lib/report.ts` — `reproducedKind(r)` (`pair` / `order` / `given order` / `never`; a report without
  `reproduced_by`, schema v2, is order mode, as replay reads it), `invocations(r)`, `toView(r).reproduced`; the schema
  comment now says v3; `Diagnosis.tsx` panel "How the failure was reproduced".
- **Test-first:** 5 tests on real committed bundles → 5 failures (`reproducedKind is not a function`). After: the
  step-5 FJ-03 bundle → "Found in a constructed pair … after 368 of 524 pairs. Pair mode does not run the project's own
  orders.", 798 invocations; a 21-Nov FJ-03 bundle (no `reproduced_by`, `order_given: true`) → "given order"; the
  package-scope order run → never, "31 shuffled orders tried …", 12,817 invocations. `npm test` → `Tests 38 passed`;
  `npx tsc --noEmit` → exit 0.

## UI demo, task 4: the Advanced run options (2026-11-27)

- **Requirement:** design goal 1 — the Target step runs the demo's options with the CLI's names and defaults.
- **Code:** new `ui/web/src/lib/request.ts` (`Form`, `DEFAULT_FORM`, `toRequest`: only what differs from the CLI's
  default is sent; an empty budget box is "no limit"); `api.ts` request, health and job types; `state.tsx` uses
  `toRequest` and names a run's bundle path; `Target.tsx` "Advanced run options" (search, scope, policy, seed,
  shuffles, both budgets, bundle; lifecycle and workspace read-only) replacing the "budget: not in the UI" label, and
  the run's time limit from health.
- **Test-first:** `request.test.ts` (5 tests) → `Cannot find module './request'`. After: `npx vitest run` → `Tests 43
  passed`; `npx tsc --noEmit` → exit 0; `npx vite build` → built. **Not yet clicked in a browser** (task 7).

## UI demo, task 5: committed evidence and checking a folder, in the UI (2026-11-27)

- **Requirement:** design goals 4 and 5a, on screen.
- **Code:** new `ui/web/src/lib/bundles.ts` (`BundleEntry`, `bundleRow` — reproduced by, scope, policy, seed, polluter,
  invocations, date, from Task 3's `reproducedKind`/`invocations`; `committedLabel`: "Committed bundle … — pre-run on
  <date>, not run now"); `api.ts` `bundles()`, `bundle(name)` (name URL-encoded: every name holds a `#`),
  `checkBundle(path)`; `state.tsx` `Loaded.verify`; `Source.tsx` "Committed evidence" table (opening a row runs verify
  on the server) and "Check a bundle folder"; `Certificate.tsx` "Evidence bundle check" panel.
- **Test-first:** `bundles.test.ts` (4 tests, real committed bundles) → `Cannot find module './bundles'`. After: the
  step-5 row = CANDIDATE, pair, package, original, seed 0, `SerializeWriterTest_14#test_writer_1`, 798, 2026-11-22;
  random seed 1 = 76 invocations; a 21-Nov run = given order; the package order run = never, 12,817. `npx vitest run` →
  `Tests 47 passed`; `npx tsc --noEmit` → exit 0; `npx vite build` → built. **Not yet clicked in a browser** (task 7).

## UI demo, task 6: honest not-built labels (2026-11-27)

- **Requirement:** design goal 5 — every label true today.
- **Code:** `ui/web/src/lib/labels.ts` — `budget` and `ranking` removed (the Advanced options run both); `runtime`:
  "NOT BUILT — ADR-001's fallback replaced by ADR-015's spike (W34, stretch); awaits the supervisor"; `container`:
  "IN THE COMMAND LINE ONLY (docker run flaketrace:w27, W27) — NOT FROM THE UI; a hardened container for untrusted
  projects is FYP-2"; new `replay`: "IN THE COMMAND LINE ONLY (py -m runner replay, W23) — NOT IN THE UI", shown with the
  committed evidence; the ranking label removed from the Diagnosis step.
- **Test-first:** `labels.test.ts` → 2 failures (old wording; `budget`/`ranking` still present). After: `npx vitest run`
  → `Tests 48 passed`; `npx tsc --noEmit` → exit 0; `npx vite build` → built.

## UI demo, task 7: the real server, every demo path (2026-11-27)

- **Requirement:** the UI is the demo; each step of demo plan v2 must work through the real backend.
- **Run:** `py -3 ui/server.py` (branch `m2/ui-demo`, Windows 11, JDK 21.0.9, Maven 3.10.0), driven over its HTTP API
  by a script (the same calls the web app makes):
  - health → `job_timeout_s` 1800, no tool missing;
  - F1 with `search: pairs`, `bundle: true` → done in 42 s: `VERIFIED`, `ConfigPolluterTest`, `reproduced_by: pair`,
    the bundle written into the job's folder, `check-bundle` on it → OK;
  - F1 with `budget_invocations: 66` → `UNRESOLVED (BUDGET_EXHAUSTED)` in 28 s (demo step 4);
  - pairs with a known order → 400, "--search pairs cannot be combined with --order: pair mode takes the victim only";
  - `/api/bundles` → 24; the step-5 FJ-03 bundle opened → `verify` OK in 0.2 s, CANDIDATE, `pair`;
  - a copy with `"n": 20` changed to 21 → "report.json does not match its checksum in manifest.json; the bundle was
    changed"; the committed bundle → OK.
- **Surprise:** `verify` on opening took 0.2 s inside the server, not the ~3 s measured per CLI call (that was mostly
  Python start-up per command), so verifying at listing time would also have been affordable; verify-on-open is kept,
  since a changed bundle is then always caught.
- **Not done here:** clicking through the screens in a browser on the demo machine — that is W33's rehearsal.

## UI demo: the fresh review's 13 findings, fixed (2026-11-27)

- **Review:** a fresh opus reviewer on the whole branch; 3 Important, 10 Minor; every number in demo plan v2 checked
  against the committed bundles and found right. All 13 fixed (the member's standing rule: minors are not deferred).
- **Server, test-first** (`TestReviewFixes`, 6 tests → 4 failures, 2 errors: `JSONDecodeError`, `ValueError: could not
  convert string to float: 'abc'`): one unreadable bundle no longer hides the list (its own row, with the reason; others
  still open); a path in quotes (Windows "Copy as path") is checked; a file is "not a folder"; a live run's bundle
  carries its verify result; refusals in the CLI's order; negative seeds accepted, as the CLI does; a bad timeout setting
  falls back to 30 min. `py -3 -m unittest ui.tests.test_server` → `Ran 49 tests OK`.
- **Web, test-first** (9 failures, plus a missing `job.ts`): a pair-mode "victim fails alone" report now says so (it
  said "Never reproduced"); a budget stop in pair mode is named; a given order names its test count; a cleared seed or
  shuffles box is the default, not 0; the "pre-run" label comes first, so a narrow header keeps it; an unreadable
  bundle is its own row; a finished run does not replace a report opened after it started (the Target step offers it);
  a bundle-open error shows in its own panel and only the last click counts; the `#` in a bundle name is encoded (the
  test fails when `encodeURIComponent` is removed, passes when restored). `npx vitest run` → `Tests 57 passed`;
  `npx tsc --noEmit` → exit 0; `npx vite build` → built.
- **Correction:** the "tsc exit 0" lines in tasks 3–6 above came from `npx tsc --noEmit | tail -5; echo $?`, which
  prints `tail`'s exit code. Run without the pipe, `tsc` reported two errors (fixed here); the whole tree is now clean.
- **New:** `docs/04-Implementation/web-ui.md`, the four-point note the plan listed (finding 13).

## Vault close-out after the supervisor's 23 Nov review (2026-11-27)

- **Requirement:** the supervisor's Proposed Student Action Plan (R20261123): FT009 compatibility, FT008 counts
  and wording, current artefacts; plus A4–A6, A10, M-2, M-3 completion tests ([[10-Final1/supervisor-review-2026-11-23]]).
- **Bundles still verify on current `main` (`4f1ad39`):** `python3 -m unittest eval.tests.test_committed_bundles`
  → `Ran 2 tests in 2.266s OK` (Linux, Python 3; each report validated against the schema its own
  `schema_version` names, `eval/schema_validator.py`). Not the W36 matrix: that is M3's.
- **FT008 recount:** read `polluters` from `report.json` of the seven FJ-03 pair-mode bundles dated
  2026-11-22 in `eval/bundles/` → `SerializeWriterTest_14#test_writer_1` (×3), `#test_writer_3` (×2),
  `#test_writer_2` (×1), `SerializeWriterTest_15#test_writer_1` (×1): **four distinct**, not five as the
  protocol, [[evidence-m3]] and the claims ledger said. Claims ledger E16/G9 corrected; protocol and M3's log are W37.
- **Not run:** any Java/Maven command (no JVM run needed for this change).

## W39: FJ-03 under a stated budget (2026-11-27)

- **Requirement:** W39 (M-2, FT007; supervisor review 23 Nov): the seven FJ-03 comparison runs (#165) had no budget
  limit; the iteration objective says "under a stated budget".
- **Prediction, written before the runs** (from the unconstrained runs): with a 400-invocation limit the pairs get 340
  after the 60 reserved for verification, so `original` (798 needed) stops `BUDGET_EXHAUSTED` and seeds 1–3 (76, 184,
  258 needed) reach `CANDIDATE` at the same cost.
- **Setup** (with the member's permission, scratchpad only): Temurin 8u502 (SHA-256 `3f193fe5…` checked); fastjson
  `git fetch --depth 1` of `e05e9c5e4be580691cc55a59f3256595393203a1`, `mvn -B -q -DskipTests test-compile` → exit 0,
  `git status` empty; FlakeTrace from a **clean local clone of `main` at `bfb2f93`** (the member's checkout holds three
  untracked images of M1's, which would mark every bundle `tool.dirty: true`); records and bundles outside the clone.
- **Command** (×4, from the clone): `py -3 -m runner diagnose --project <fastjson> --victim com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf --search pairs
  --scope package --policy <original|random> --seed <0|1|2|3> --n 20 --budget-invocations 400 --bundle <folder>`.
- **Result:** FJ-03 pair mode, package scope, `--budget-invocations 400` (reserve 60): **`original` → `UNRESOLVED (BUDGET_EXHAUSTED)`** after 170 of 524 pairs, 360 of 400 spent, nothing blamed; **random seeds 1, 2, 3 → `CANDIDATE`** at **76, 184, 258** invocations (`SerializeWriterTest_14#test_writer_1`, `#test_writer_2`, `#test_writer_3`; 20/20, alone 0/20). Each run 3–6 min (10:35–10:51 UTC). **Exactly the prediction.** The clone stayed clean.
- **Bundles:** `eval/bundles/20261127T103734Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf`, `…20261127T104310Z…`, `…20261127T104600Z…`, `…20261127T104934Z…`: `eval.bundle verify` →
  OK each; `tool.dirty: false`, tool commit `bfb2f93`; no personal path. M3 agreed (2026-11-27) to them being committed
  into `eval/bundles/` and a W39 section in its README. `eval.tests.test_committed_bundles` and
  `runner.tests.test_bundle.TestCommittedBundles` → OK with 29 bundles.
- **Also:** demo plan step 5 said "each to a certified polluter" — wrong, those runs are `CANDIDATE` (M3's #180
  flag); corrected, and the budgeted runs added.
- **Limitations:** one run per policy and seed, one machine; seed 0 (436 needed) and seed 4 (148) not run; M3 to
  repeat one run.

## W36: the replay column of the bundle matrix (2026-11-27)

- **Requirement:** W36 (supervisor review 23 Nov, P1/FT009): state which bundle versions `runner replay` supports, run
  on at least one v2 and one v3 bundle. M3's matrix (#181, at `41fc150`) lists 24 bundles, all v2, and reasons from
  `runner/replay.py` that replay supports every version "by construction"; the four W39 bundles (#182) are the first
  schema-v3 bundles.
- **Predictions, before running:** both replayable bundles `same`, exit 0; both unresolved ones refused, exit 2.
- **Runs** (`main` `eb7589f`, Windows 11; fixtures with JDK 21.0.9, FJ-03 with Temurin 8u502 and
  `JAVA_TOOL_OPTIONS=-Duser.timezone=UTC -Duser.language=en -Duser.country=US`):
  `py -3 -m runner replay <bundle> --project <fixtures/od-fixture | fastjson e05e9c5> --bundle <scratch> --records <scratch>`

| Bundle | Schema | Outcome | `runner replay` (real run, 2026-11-27) |
| --- | --- | --- | --- |
| F1 `20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode` | v2 | `VERIFIED` | exit 0: `VERIFIED -> VERIFIED same`; polluter, sequence 20/20, alone, deletion `NEEDED` same; tool commit `03ada56 -> eb7589f` DIFFERENT (expected); the replay's bundle `verify` OK |
| FJ-03 W39 seed 1 `20261127T104310Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | v3 | `CANDIDATE` | exit 0 in 3 min 48 s (JDK 8u502, fastjson `e05e9c5`): `CANDIDATE (NO_SUPPORTED_RESOURCE_EVIDENCE) -> same`; polluter `SerializeWriterTest_14#test_writer_1`, 20/20, alone 20/20 passed, deletion `NEEDED` same; JDK, OS, Maven, timezone, locale, encoding, lifecycle same; the replay's report is schema v3 with `reproduced_by: pair` and the constructed-pair line; its bundle `verify` OK; fastjson's `git status` empty |
| N3 `20261121T185248Z-odfixture.EnvDependentNegativeTest#onlyFailsUnderCI` | v2 | `UNRESOLVED` | exit 2: "nothing to replay: no polluter was blamed" (R1) |
| FJ-03 W39 original `20261127T103734Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | v3 | `UNRESOLVED` | exit 2: the same refusal |

- **Answer:** `runner replay` supports schema **v2 and v3** bundles — shown by running it on one of each, both `same`,
  both new bundles `verify` OK; it refuses an unresolved report on either version (R1). Every prediction held.
- **Found on the way:** the bundles README's fixture table names eight folders that no longer exist
  (`20261121T094724Z`, `…152045Z`, `…152110Z`, `…152152Z`, `…152241Z`, `…152302Z`, `…152321Z`, `…152513Z`; the bundles
  were regenerated clean in #168); my first N3 attempt used one of those names and failed with "not a readable bundle".
  M3's file — sent to her. M3's matrix also needs the four W39 (v3) rows.
