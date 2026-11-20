# W20 runner half — deletion checks Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** after minimisation, check every kept test by repeated removal and record the result in `DiagnosisRuns.deletion_checks` (ADR-011, Interface 4).

**Architecture:** a new `runner/deletion.py` holds `DeletionCheck`, `label()` and `check_deletions()`; `run_steps` calls it for `POLLUTER_FOUND` before the final verification, which then runs on the final set. Labels use M3's `eval.stats.wilson_interval` and `eval.outcome.DEFAULT_LOWER_BOUND_THRESHOLD`.

**Tech Stack:** Python 3.11 `unittest`, `eval.tests.fake_runner.FakeOrderRunner`, the od-fixture (JDK 8+, Maven).

**Spec:** `docs/superpowers/specs/2026-11-20-w20-deletion-checks-design.md`; ADR-011; `docs/contracts/interfaces.md` Interface 4.

## Global Constraints

- Fields exactly: `DeletionCheck(removed: TestIdentifier, runs: Optional[RunTally], status: str, source: str, round: int)`.
- Statuses `NEEDED`, `NOT_NEEDED`, `INCONCLUSIVE`, `NOT_RUN`; sources `deletion-run`, `alone-check`; rounds start at 1.
- `NEEDED` iff `runs.passed == m`; `NOT_NEEDED` iff Wilson lower bound of `runs.matched/m` ≥ 0.70; else `INCONCLUSIVE`. At m = 20: 19 matched → NOT_NEEDED (0.764), 18 → INCONCLUSIVE (0.699).
- `m = n`. No CLI flag. `NOT_RUN` is defined but not produced (W24).
- Test-first: each test is run and seen failing before its code (CLAUDE.md iteration rule 1); failing output goes in `docs/evidence-m2.md`.
- Never "1-minimal" or "minimum" in any text (claims ledger G2, D9).
- Agent never commits; hand-over commands in cmd, one line per `git commit -m … -m …`.

## Review Focus

1. A NOT_NEEDED drop that leaves one polluter: round 2 must be an `alone-check` with no new runs, not a deletion run of `[victim]`.
2. Two tests NOT_NEEDED in one round: only the first is dropped; the second is re-checked in the next round (it may become needed once the first is gone).
3. `sequence_tally` and `sequence` must describe the **final** set, not the ddmin set.
4. Every non-`POLLUTER_FOUND` status returns `deletion_checks == []`.
5. A victim whose alone runs had `other` failures: the alone-check is `INCONCLUSIVE`, not `NEEDED`.

---

### Task 1: `DeletionCheck` and `label()`

**Files:**
- Create: `runner/deletion.py`
- Test: `runner/tests/test_deletion.py`

**Interfaces:**
- Produces: `DeletionCheck` (frozen dataclass, fields above); constants `NEEDED, NOT_NEEDED, INCONCLUSIVE, NOT_RUN, DELETION_RUN, ALONE_CHECK`; `label(runs: RunTally, m: int) -> str`.

- [ ] **Step 1: failing tests** in `TestLabel`:
  `label(RunTally(20,20,0,0,0),20) == NEEDED`; `label(RunTally(20,0,20,0,0),20) == NOT_NEEDED`;
  `label(RunTally(20,1,19,0,0),20) == NOT_NEEDED`; `label(RunTally(20,2,18,0,0),20) == INCONCLUSIVE`;
  `label(RunTally(20,11,9,0,0),20) == INCONCLUSIVE`; `label(RunTally(20,0,0,20,0),20) == INCONCLUSIVE`;
  `label(RunTally(20,19,0,0,1),20) == INCONCLUSIVE`; and `DeletionCheck` is frozen with the five fields in order.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_deletion` → Expected: ERROR `ModuleNotFoundError: No module named 'runner.deletion'`.
- [ ] **Step 3:** implement in `runner/deletion.py`.
- [ ] **Step 4:** same command → Expected: OK.

### Task 2: `check_deletions()`

**Files:** Modify `runner/deletion.py`; Test `runner/tests/test_deletion.py`

**Interfaces:**
- Consumes: `runner.verify.repeat(runner, sequence, victim, reference, n) -> RunTally`.
- Produces: `check_deletions(runner, polluters: List[TestIdentifier], victim, reference, m: int, alone_tally: RunTally) -> Tuple[List[DeletionCheck], List[TestIdentifier]]` (all checks of all rounds, final polluters in original order).

- [ ] **Step 1: failing tests** in `TestCheckDeletions` (all `FakeOrderRunner`):
  - `test_one_polluter_reuses_the_alone_tally_and_runs_nothing`: polluters `[P]`, alone `RunTally(20,20,0,0,0)` → one check `(P, alone, NEEDED, ALONE_CHECK, 1)`, `runner.calls == []`.
  - `test_one_polluter_whose_victim_failed_alone_differently_is_inconclusive`: alone `RunTally(20,17,0,3,0)` → `INCONCLUSIVE`.
  - `test_not_needed_test_is_dropped_and_the_rest_rechecked` (ADR-011 T1 shape): victim fails with REF whenever P is before it; `[P, Q]` → round 1: Q removed → `[P,V]` 20/20 matched → `NOT_NEEDED`; P removed → `[Q,V]` passes → `NEEDED`; round 2: `[P]` → `ALONE_CHECK`, `NEEDED`; final `[P]`; exactly 40 runner calls.
  - `test_inconclusive_keeps_both_tests` (T2): `[P,V]` fails on 9 of 20 runs, `[Q,V]` passes → Q `INCONCLUSIVE`, P `NEEDED`, final `[P, Q]`, one round only.
  - `test_only_the_first_not_needed_test_is_dropped_per_round`: polluters `[P, Q, R]`, victim fails with REF after any one of them → round 1: three `NOT_NEEDED` checks, P dropped; round 2 on `[Q, R]`: two `NOT_NEEDED`, Q dropped; round 3 on `[R]`: one `ALONE_CHECK`, `NEEDED`. Rounds recorded `[1, 1, 1, 2, 2, 3]`; final `[R]`.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_deletion.TestCheckDeletions` → Expected: ERROR `ImportError: cannot import name 'check_deletions'`.
- [ ] **Step 3:** implement: per round, check every kept test (`repeat(runner, kept-without-p + [victim], …, m)`); one kept test → alone-check from `alone_tally`; drop the first `NOT_NEEDED`, `round += 1`, repeat; stop when nothing is dropped.
- [ ] **Step 4:** same command → Expected: OK; then whole `runner.tests.test_deletion` OK.

### Task 3: wire into `run_steps`, fixture checks, docs

**Files:** Modify `runner/diagnose.py` (`DiagnosisRuns.deletion_checks: List = field(default_factory=list)`; call after search/minimise for `POLLUTER_FOUND`, step label `"delete"`; final `repeat()` on the final set); Test `runner/tests/test_diagnose.py`; docs listed in step 6.

- [ ] **Step 1: failing tests:**
  - `TestDeletionChecks.test_ft004_counterexample_drops_the_unneeded_test` (T1): the FT004 script from `docs/evidence-m2.md` (2026-11-13) on `[P, Q, V]` — `[P, V]` passes its first 2 runs, fails after → `polluters == [P]`, `sequence == [P, V]`, `sequence_tally.matched == 20`, Q's check `NOT_NEEDED`.
  - `test_other_statuses_have_no_deletion_checks`: VICTIM_FAILS_ALONE, NOT_REPRODUCED, INCONSISTENT → `[]`.
  - `test_deletion_runs_are_recorded_as_their_own_step`: record contains `"delete"` steps between `"minimise"` and `"verify"`.
  - Fixture: in `test_f1_single_static_field_polluter` assert one check, `source == "alone-check"`, `NEEDED` (record line count unchanged = no extra runs); in the F3 test (n=5) both polluters `NEEDED`, `runs.passed == 5`.
- [ ] **Step 2:** run them → Expected: FT004 test fails with `[P, Q] != [P]` (the old behaviour, as on `7cf453d`); others fail on the missing attribute / step.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** `py -3 -m unittest runner.tests.test_deletion runner.tests.test_diagnose` → OK; then the whole runner suite, `ui.tests.test_server` and eval suite → OK.
- [ ] **Step 5:** real `py -3 -m runner diagnose` on F3 and F1 → record outcome lines (F3 stays `CANDIDATE` until M3's half).
- [ ] **Step 6: docs:** `runner/README.md`, `docs/04-Implementation/` runner note, iteration-2-plan W20 row, `docs/09-Team/members.md`, `docs/evidence-m2.md`, `docs/genai-log-m2.md`, genai-register row; hand over the commit.
