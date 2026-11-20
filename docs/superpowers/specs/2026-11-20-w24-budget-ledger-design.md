# W24 runner half — budget ledger: design

**Date:** 2026-11-20 · **Owner:** M2 · **Contract:** `docs/contracts/interfaces.md` Interface 6 (agreed by
M1, M2, M3 on 2026-11-20) · **ADR:** ADR-014 §1–§3 · **Closes (with M3's half):** ADR-014 evidence items 1–3, FT007 part

## Intent

A diagnosis runs inside one budget, stops at it, and keeps enough to verify what it found. Today it
runs until it finishes. This is the "count total execution cost, stop at the shared limit, retain
verification resources" half of the supervisor's wording; the ranked comparison is W25.

## Goals / non-goals / anti-goals

- **Goals:** Interface 6 rules B1–B8, status `BUDGET_EXHAUSTED`, `DiagnosisRuns.budget`
  (`BudgetAccount`), `NOT_RUN` deletion checks, the `budget-stop` record line, CLI flags
  `--budget-invocations` and `--budget-seconds`, a CLI summary line.
- **Non-goals:** `--policy`, ranking, `analysis_seconds` (W25); the report's `budget` field (M3).
- **Anti-goals:** any search function counting invocations by hand; a `VERIFIED` whose verification
  was cut; a check cut part-way; a change to any verdict when no limit is given.

## Approaches

| | Approach | Trade-off |
| --- | --- | --- |
| **A (chosen)** | `BudgetedRunner` wraps the runner (outside `RecordingRunner`) and raises `BudgetExhausted(phase)` before a run that does not fit. `run_steps` catches it per phase | ADR-014 §1 prescribes this; search, ddmin and shuffle code stay unchanged |
| B | Pass a ledger into `reproduce`, `find_polluter`, `ddmin`, ... | Every function counts by hand — what ADR-014 rules out |
| C | Precompute how many runs each phase may make | Search and ddmin cost is not known in advance |

The deletion checks and the final verify do not use the exception: they ask the ledger first
(`remaining()`), because Interface 6 says a check is either run in full or `NOT_RUN` (B5) and the verify
count is computed (B6).

## Design

- **`runner/budget.py`** (new): `Budget`, `BudgetAccount` (Interface 6 fields), `BudgetExhausted`,
  `BudgetedRunner(runner, budget, n, clock=time.monotonic)`. Tracks `spent` per phase, `launches`,
  first/last run times. `EXPLORE = {reproduce, shuffle, search, minimise}`. Exploration cap
  `limit − 3n` (B3); seconds checked only for exploration (B7). A refusal writes the `budget-stop`
  line through the recorder (B8) and sets `exhausted`/`exhausted_phase` once. `remaining()` = limit −
  total (None when unlimited). `account(candidates_total)` builds the `BudgetAccount`;
  `candidates_tried = spent["search"] // 2` (each search run is one pair).
- **`run_steps`**: always wraps in a `BudgetedRunner` (unlimited when `budget=None`, so it still counts).
  B2 start check before any run. An exploration cut ends exploration: the alone check runs (if not yet
  run), `VICTIM_FAILS_ALONE` wins if it fails alone, otherwise status `BUDGET_EXHAUSTED` with the
  fields Interface 6 lists.
- **`check_deletions`** gains `can_afford(cost) -> bool` (default always true). B5 hold-back is
  computed per round from the current kept set.
- **Final verify**: `min(n, remaining // len(sequence))` runs; 0 → `BUDGET_EXHAUSTED`.
- **`_label`** sets the step on both wrappers.
- **CLI**: two flags → `Budget`; summary line `budget: spent X of Y invocations (reserve R)…`;
  `BUDGET_EXHAUSTED` reaches `eval.report` like any status (exit 3 until M3's half lands).
- **Docs**: runner README, `docs/04-Implementation/` notes, W24 plan row, members, evidence, GenAI log.

## Left to the builder

Exact wording of the CLI summary line; the record line's field order.
