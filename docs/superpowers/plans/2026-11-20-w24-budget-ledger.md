# W24 runner half — budget ledger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** every diagnosis is counted, and with a limit it stops at it, keeps the verification reserve, and reports `BUDGET_EXHAUSTED` and a `BudgetAccount` (Interface 6, rules B1–B8).

**Architecture:** a new `runner/budget.py` holds `BudgetedRunner`, which wraps the (recording) runner. Exploration runs that do not fit raise `BudgetExhausted`; `run_steps` catches it. Deletion checks and the final verify ask the ledger first (`affords`, `affordable_runs`), so nothing is cut part-way.

**Tech Stack:** Python 3.11 `unittest`, `eval.tests.fake_runner.FakeOrderRunner`, the od-fixture (JDK 8+, Maven).

**Spec:** `docs/superpowers/specs/2026-11-20-w24-budget-ledger-design.md`; `docs/contracts/interfaces.md` Interface 6; ADR-014 §1–§3.

## Global Constraints

- Cost of `run_ordered(order)` = `len(order)`. Phases: `reproduce, shuffle, alone, search, minimise, deletion, verify`; `EXPLORE = {reproduce, shuffle, search, minimise}`.
- `reserve = 3 * n`. Start minimum = `reserve + len(start) + 2` (`start` = order up to and including the victim).
- Exploration cap: exploration spend + cost ≤ `limit − reserve`. Verification: total spend + cost ≤ `limit`.
- Seconds limit applies to exploration only; measured from when the `BudgetedRunner` is created.
- `BudgetAccount` fields exactly as Interface 6, in that order; `analysis_seconds = None`, `policy = "original"`.
- Record line for a refusal: `{"type": "budget-stop", "phase", "would_cost", "spent"}` (`spent` = total so far); no `run` line.
- New status constant `BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"` in `runner/diagnose.py`.
- No limit → no verdict, run or record line changes (only the header's new `budget` key).
- Test-first; failing output goes in `docs/evidence-m2.md`. Never "minimum" for a polluter set (claims G2) — "minimum" here only means the budget floor.
- Agent never commits; hand-over in cmd.

## Review Focus

1. No limit: existing runner suite unchanged, and F1's record has the same number of `run` lines as before → Task 3 `test_no_limit_changes_nothing`.
2. Exploration cut while the victim fails alone → `VICTIM_FAILS_ALONE`, not `BUDGET_EXHAUSTED` → Task 3 `test_victim_failing_alone_outranks_the_cut`.
3. Recount with a refusal: `spent` per phase equals the record's sums; the refused run has no `run` line → Task 3 `test_record_recounts_to_the_ledger`.
4. A deletion round where the first check fits and the second does not: first labelled, rest `NOT_RUN`, nothing dropped → Task 2.
5. Limit exactly at the start minimum is accepted; one less is refused → Task 3.

---

### Task 1: `runner/budget.py` and `RecordingRunner.write_event`

**Files:** Create `runner/budget.py`; Modify `runner/recording.py`; Test `runner/tests/test_budget.py`.

**Interfaces — Produces:**
- `Budget(limit_invocations: Optional[int] = None, limit_seconds: Optional[float] = None)` frozen dataclass.
- `BudgetAccount` frozen dataclass, Interface 6 fields.
- `BudgetExhausted(Exception)` with `.phase: str`.
- `BudgetedRunner(runner, budget: Budget, n: int, victim: TestIdentifier, clock=time.monotonic)`:
  - `step` (property; setting it also sets `runner.step` if the inner runner has one) and `note` (same forwarding);
  - `run_ordered(order)`: refuse (write the line, set `exhausted`/`exhausted_phase` once, raise) or run, then add `len(order)` to `spent[step]`, count the launch, keep the victim's outcome under `step`;
  - `affords(phase, cost, keep=0) -> bool`: True if `total + cost + keep ≤ limit` (or no limit); else records a refusal for `phase` (line + flags) and returns False;
  - `affordable_runs(cost, n) -> int`: `n` without a limit, else `min(n, (limit − total) // cost)`;
  - `victim_outcomes(phase) -> List[RunOutcome]`; `launches_in(phase) -> int`;
  - `account(candidates_total: int) -> BudgetAccount` (`candidates_tried = spent["search"] // 2`).
- `RecordingRunner.write_event(entry: dict) -> None` (public wrapper of `_write`).

- [ ] **Step 1: failing tests** (`FakeOrderRunner`, `V` victim, `C = [C0..C9]`):
  - `test_counts_invocations_per_phase_without_a_limit`: steps `reproduce` run `[C0, V]`, `alone` run `[V]` ×2 → `spent == {"reproduce": 2, "alone": 2, others 0}`, `launches == 3`, `exhausted is False`, `reserve_invocations == 60` (n=20).
  - `test_exploration_run_crossing_the_cap_is_not_started`: limit 63, n=20 → cap 3; `search` runs `[C0,V]` OK, `[C1,V]` raises `BudgetExhausted` with `phase == "search"`; fake saw 1 call; `exhausted_phase == "search"`.
  - `test_verification_may_use_the_reserve`: limit 63, n=20; `alone` 60 runs of `[V]` all start (no raise); a 61st `affords("verify", 4)` is False and sets `exhausted`.
  - `test_seconds_stop_exploration_only`: clock `lambda: float(len(fake.calls))`, `limit_seconds=2.5`; three `search` runs then the fourth raises; a `verify` run after that still runs.
  - `test_refusal_writes_one_budget_stop_line`: inner = `RecordingRunner(fake, tmp, {})`; refused `search` run → last line `{"type": "budget-stop", "phase": "search", "would_cost": 2, "spent": <total>}`, no `run` line for it.
  - `test_affordable_runs`: no limit → `affordable_runs(3, 20) == 20`; limit 100 after 60 spent → `affordable_runs(3, 20) == 13`.
  - `test_account_fields_are_the_contract`: `[f.name for f in fields(BudgetAccount)]` equals Interface 6's list; `policy == "original"`, `analysis_seconds is None`.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_budget` → ERROR `No module named 'runner.budget'`.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** same command → OK.

### Task 2: deletion checks under a budget (B5)

**Files:** Modify `runner/deletion.py`; Test `runner/tests/test_deletion.py`.

**Interfaces:** Produces `check_deletions(..., alone_tally, can_afford: Callable[[int, int], bool] = lambda cost, kept: True)`. A check costs `m * len(rest + [victim])`; `kept` is the round's kept-test count; if `can_afford(cost, kept)` is False, that check and every later check of the round are `DeletionCheck(test, None, NOT_RUN, DELETION_RUN, round)`, and the function returns with the current kept set (no drop that round). The alone-check (one kept test) costs nothing and is never refused.

- [ ] **Step 1: failing tests:**
  - `test_a_check_that_does_not_fit_is_not_run_and_nothing_is_dropped`: `[P, Q]`, victim fails after P (T1 shape), `can_afford` True once then False → checks `[(P, NEEDED), (Q, NOT_RUN, runs None)]`, final `[P, Q]`, 20 runner calls.
  - `test_nothing_fits`: `can_afford` always False → both `NOT_RUN`, 0 calls.
  - `test_the_alone_check_is_free`: `[P]`, `can_afford` always False → one `ALONE_CHECK` `NEEDED`.
  - `test_cost_passed_is_m_times_the_run_length`: record the arguments asked: `[(40, 2), (40, 2)]` for `[P, Q]`, m=20.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_deletion` → the new tests fail (`unexpected keyword argument 'can_afford'`).
- [ ] **Step 3:** implement. **Step 4:** same command → OK.

### Task 3: wire the ledger into `run_steps` and `diagnose`

**Files:** Modify `runner/diagnose.py`; Test `runner/tests/test_diagnose.py` (new class `TestBudget`).

**Interfaces:**
- Consumes Tasks 1–2.
- Produces: `run_steps(..., budget: Optional[Budget] = None, clock=time.monotonic)`; `diagnose(..., budget: Optional[Budget] = None)`; `DiagnosisRuns.budget: Optional[BudgetAccount] = None` (last field; `run_steps` always sets it); constant `BUDGET_EXHAUSTED`; record header key `"budget": {"limit_invocations", "limit_seconds", "reserve_invocations"}`.

Flow (Interface 6): B2 check before any run → `DiagnoseInputError` whose message contains the minimum. Wrap the runner in `BudgetedRunner` (`_label` sets its `step`). `reproduce` and `shuffle` in one `try`; on `BudgetExhausted` skip to the alone check. `search` and `minimise` in a `try`. After a cut: alone check if not yet run (`VICTIM_FAILS_ALONE` if it fails, as today), else `BUDGET_EXHAUSTED` with `polluters=[]`, `sequence` = current order, `sequence_tally = tally(ledger.victim_outcomes("reproduce"), reference)`, `search_runs = ledger.launches_in("search")`, `minimise_runs = ledger.launches_in("minimise")`, and for a shuffle cut `shuffled_orders = ledger.launches_in("shuffle")`, `shuffle_infrastructure_failures` = failed victim outcomes in `shuffle`. Deletion: `can_afford = lambda cost, kept: ledger.affords("deletion", cost, keep=n * (kept + 1))`. Verify: `runs = ledger.affordable_runs(len(sequence), n)`; `runs < n` → `ledger.affords("verify", len(sequence) * n)` records the refusal; `runs == 0` → `BUDGET_EXHAUSTED`. `budget=ledger.account(len(order) - 1)` on every return.

Scenario `TEN`: order `[C0..C9, V]`, victim fails with REF iff `C9` precedes it, n=20 (reserve 60, start minimum 73).

- [ ] **Step 1: failing tests:**
  - `test_no_limit_changes_nothing`: `TEN`, no budget → `POLLUTER_FOUND`, `polluters == [C9]`, `budget.exhausted is False`, `budget.limit_invocations is None`, `spent["search"] == 20`, `candidates_tried == 10`, `candidates_total == 10`; and the runner call list equals the one from before the change (51 runner calls: reproduce 1, alone 20, search 10, verify 20; the one-polluter deletion check is free).
  - `test_search_stops_at_the_cap_and_the_alone_check_ran_in_full` (ADR-014 test 1): `TEN`, limit 80 → `BUDGET_EXHAUSTED`, `alone_tally.n == 20`, `spent == {reproduce: 11, alone: 20, search: 8, others 0}`, `candidates_tried == 4`, `exhausted_phase == "search"`, `launches == 25`.
  - `test_limit_below_the_start_minimum_is_refused` (ADR-014 test 2): limit 72 → `DiagnoseInputError` with `"73"` in the message, 0 runner calls; limit 73 → runs.
  - `test_victim_failing_alone_outranks_the_cut`: victim fails iff `order == [V]`; `TEN`, limit 73 → `VICTIM_FAILS_ALONE`, `exhausted_phase == "reproduce"`.
  - `test_record_recounts_to_the_ledger`: `TEN`, limit 80 through `RecordingRunner` → per step, sum of `len(order)` over `run` lines == `spent`; `run` lines == `launches`; exactly one `budget-stop` line (`phase "search"`, `would_cost 2`).
  - `test_two_kept_tests_one_deletion_check_fits` (B5): order `[P, Q, V]`, victim fails iff both P and Q precede it, n=20, limit 150 → `POLLUTER_FOUND`, checks `[(P, NEEDED), (Q, NOT_RUN)]`, `sequence_tally.n == 20`, `exhausted_phase == "deletion"`. (Unlimited spend for this scenario is 174: reproduce 3, alone 20, search 4, minimise 7, deletion 80, verify 60 — assert it in the same test.)
  - `test_short_verify_when_the_hold_back_cannot_be_paid` (B6): same order, limit 74 → both checks `NOT_RUN`, `sequence_tally.n == 13`, `status == POLLUTER_FOUND`, `exhausted is True`.
  - `test_no_verify_run_fits_is_budget_exhausted` (B6 zero): order `[P, Q, R, V]`, victim fails iff all three precede it, n=1; limit = (exploration spend of an unlimited run) + 3 → `BUDGET_EXHAUSTED`, `spent["verify"] == 0`.
  - `test_seconds_limit_stops_the_search`: `TEN`, clock `lambda: float(len(fake.calls))`, `limit_seconds=2.5` → `BUDGET_EXHAUSTED`, `alone_tally.n == 20`, `candidates_tried == 0`.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_diagnose.TestBudget` → errors (`unexpected keyword argument 'budget'`).
- [ ] **Step 3:** implement. **Step 4:** `py -3 -m unittest runner.tests.test_budget runner.tests.test_deletion runner.tests.test_diagnose` → OK; then the whole runner suite, `ui.tests.test_server`, `eval/tests` → OK (M3's `DiagnosisRuns` builders still work because `budget` defaults to `None`).

### Task 4: CLI flags, summary line, real runs, docs

**Files:** Modify `runner/cli.py`; Test `runner/tests/test_cli.py`; docs below.

**Interfaces:** `--budget-invocations N` (int ≥ 1) and `--budget-seconds S` (float > 0) → `Budget`, passed through `run_diagnose(..., budget=None)` and `_diagnose_in` to `diagnose`. A `DiagnoseInputError` from B2 exits 2 like other input errors. `_NO_REPORT_WHY[BUDGET_EXHAUSTED] = "the budget ran out before a polluter set was found; eval.report reads this from M3's W24 half"`. `summary(..., budget=None)` adds `budget:     spent {total} invocations{ of {limit}} (reserve {reserve}); search tried {tried} of {total} candidates` and `; stopped in {phase}` when exhausted.

- [ ] **Step 1: failing tests:** `test_budget_flags_reach_diagnose` (mock `diagnose`, assert `budget == Budget(80, None)`); `test_bad_budget_values_exit_2` (`0`, `-1`, `abc`); `TestSummary.test_budget_line` (no limit / with limit / exhausted); `test_budget_below_the_minimum_exits_2` on the fixture (F1, `--budget-invocations 10`).
- [ ] **Step 2:** run them → fail. **Step 3:** implement. **Step 4:** `py -3 -m unittest runner.tests.test_cli` → OK.
- [ ] **Step 5: real runs** on the od-fixture F2 (`odfixture.CacheVictimTest#...` — take the victim from `fixtures/od-fixture/ground_truth.json`): no limit, then a limit just above the start minimum. Record exit code, the budget line, and `budget-stop` lines from the record. Expected only "runs and stops"; the numbers are written as they come.
- [ ] **Step 6: docs:** `runner/README.md`; `docs/04-Implementation/diagnose-cli.md` and the runner note; root `README.md` and CLAUDE.md §8 if the command list changes; W24 plan row; members row; `docs/evidence-m2.md`; `docs/genai-log-m2.md`; genai-register row; `docs/10-Final1/demo-plan.md` if the demo gains a budget run. Hand over the commit.
