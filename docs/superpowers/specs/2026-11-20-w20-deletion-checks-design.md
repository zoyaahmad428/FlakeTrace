# W20 runner half — deletion checks (design)

**Date:** 2026-11-20 · **Owner:** M2 · **Status:** approved by M2 2026-11-20 · **Builds on:**
ADR-011 (accepted 2026-11-13), `docs/contracts/interfaces.md` Interface 4 (agreed by M1, M2, M3
2026-11-20, PR #119).

## Intent

After `ddmin` keeps a set of tests, show that each one is needed by removing it and repeating the
rest plus the victim `m` times (FT004). The runner records the facts in
`DiagnosisRuns.deletion_checks`; M3's `eval/report.py` turns them into
`assurance.sequence.deletion`. Done = ADR-011 T1, T2, T4 (and T5's not-run shape) pass at the runner
level; T3 (real F3 → `VERIFIED`) needs M3's half as well.

## Goals / non-goals

- Goal: `DeletionCheck` and `deletion_checks` exactly as Interface 4 says; the restart loop of ADR-011 §3.
- Goal: one polluter costs no extra runs (`alone-check`, §2).
- Non-goal: `NOT_RUN` from a real budget (W24); the CLI summary line for checks (needs M3's report
  field); a CLI flag for `m`.
- Anti-goal: re-implementing M3's thresholds — the labels use `eval.stats.wilson_interval` and
  `eval.outcome.DEFAULT_LOWER_BOUND_THRESHOLD`.

## Approaches

1. **Chosen — a new `runner/deletion.py`** with `DeletionCheck` and `check_deletions(...)`, called at
   the end of `run_steps` for `POLLUTER_FOUND` only; reuses `runner.verify.repeat`. One file, one job,
   testable with `FakeOrderRunner`.
2. Inline in `run_steps` — rejected: `run_steps` already holds five steps; the loop would make it
   hard to read and to test alone.
3. Inside `ddmin` (repeat each trial) — rejected by ADR-011 §6: multiplies search cost.

## Design

- `DeletionCheck(removed, runs, status, source, round)` — frozen dataclass, fields as Interface 4.
- `label(runs, m) -> str`: `NEEDED` if `runs.passed == m`; `NOT_NEEDED` if the Wilson lower bound of
  `runs.matched / m` ≥ 0.70; else `INCONCLUSIVE`.
- `check_deletions(runner, polluters, victim, reference, m, alone_tally) -> (checks, final_polluters)`:
  - one polluter: one check, `source="alone-check"`, `runs=alone_tally`, label from it, no runs;
  - several: round r checks every kept test (`repeat(runner, kept - p + [victim], …, m)`), even after an
    `INCONCLUSIVE`; if any is `NOT_NEEDED`, drop the **first** such test and start round r+1 on the
    smaller set (which may become one polluter → `alone-check`); stop when a round drops nothing.
    At most k rounds.
- `run_steps`: after search/minimise, `checks, polluters = check_deletions(...)`, then the final
  `repeat()` verifies the final sequence (so `sequence_tally` is for the final set). `deletion_checks`
  defaults to `[]` on every other status.
- `m = n`. Recorded step `"deletion"`, each run line with `removed` and `round` (ADR-011 "Consequences"; corrected after the final review — this design first said `"delete"`, which departed from the ADR).

## Left to the builder

Names of private helpers; test fixture layout.
