# FT021 reset-sensitive control Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** show with real JVM runs which state one fresh JVM per order resets and which it does not (ADR-012 §1, FT021).

**Architecture:** a Maven control project with a writer and four readers; one real-JVM test drives it through `OrderRunner` and checks each reader against an expectation table.

**Tech Stack:** JUnit 4.13.2, Java 8 source level, Python `unittest`, `runner.order_runner.OrderRunner`, `maven_test_classpath`.

**Spec:** `docs/superpowers/specs/2026-11-21-ft021-reset-control-design.md`; ADR-012 §1.

## Global Constraints

- Project path `runner/tests/resources/reset-control/`; POM like `lifecycle-control` (JUnit 4.13.2, source/target 1.8) with Surefire `skipTests` true and a comment why.
- Marker file name `flaketrace-reset-control.marker`; property `flaketrace.reset.control`.
- The test's working directory is a temporary folder; markers in it and in the temp folder are deleted before and after.
- Expectation rows, verbatim: `static field: reset`, `system property: reset`, `file in the temp folder: not reset`, `file in the working directory: not reset`.
- Skipped without JDK/Maven unless `FLAKETRACE_REQUIRE_JVM` is set (as the other real-JVM tests).
- No "sandbox", "isolated" or "clean execution" wording. Agent never commits.

## Review Focus

1. A marker left over from an earlier, crashed test run must not decide the result → markers deleted in `setUp` (pinned by the sanity test running after a clean state).
2. A reader that would pass vacuously → the same-JVM sanity test must see all four fail.
3. Class-grouped vs per-method lifecycle: the readers are in one class; the result must not depend on the mode → run the across-orders test in both modes.

---

### Task 1: control project and real-JVM test

**Files:** Create `runner/tests/resources/reset-control/pom.xml`, `.../src/test/java/ResetWriterTest.java`, `.../src/test/java/ResetReaderTest.java`; Modify `runner/tests/test_order_runner.py` (new `TestResetControl`).

- [ ] **Step 1: failing test** `TestResetControl`:
  - `test_a_new_jvm_resets_jvm_state_but_not_files` (both lifecycle modes): order 1 `[ResetWriterTest#leaveState]` passes; order 2 the four readers; `{row: outcome.passed}` equals `{row: expected == "reset"}` for every `EXPECTED` row.
  - `test_each_reader_detects_its_leftover_in_one_jvm`: one order `[writer, four readers]` → all four readers fail.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_order_runner.TestResetControl` → fails (the control project does not exist: Maven error).
- [ ] **Step 3:** write the POM and the two classes.
- [ ] **Step 4:** same command → OK; then `py -3 -m unittest runner.tests.test_order_runner` → OK.

### Task 2: docs

- [ ] `docs/04-Implementation/sandbox-runner.md` (measured reset table), `runner/README.md` (the control), `docs/10-Final1/action-register.md` (FT021/A3 evidence; status stays Partly — M3 checks), `docs/evidence-m2.md`, `docs/genai-log-m2.md`, register row, members row; the FYP-2 follow-up (detecting leftover state during a diagnosis) in `docs/00-Meta/risk-register.md`. Hand over the commit, PR text and the message for M3.
