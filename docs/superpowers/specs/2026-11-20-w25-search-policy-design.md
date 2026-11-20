# W25 runner half — search policy: design

**Date:** 2026-11-20 · **Owner:** M2 · **Contract:** `docs/contracts/interfaces.md` Interface 7 (agreed by
M1, M2, M3 on 2026-11-20), Interface 5 (`rank_candidates`), Interface 2 (`DEPTH_LIMIT`) · **ADR:** ADR-014 §4–§6 ·
**Closes (with M3's half):** FT007's "compare with unranked search at the same endpoint"; enables W26b steps 6–8

## Intent

The project's contribution claim is that static evidence orders the polluter search so a verified
diagnosis costs fewer invocations than an unranked search **at the same endpoint** under the same budget.
W24 built the budget; W25 lets one diagnosis choose how candidates are ordered (`original`, `ranked`,
`random`), spends analysis time only where ADR-014 §6 allows, and records enough for M3 to measure it.

## Goals / non-goals / anti-goals

- **Goals:** Interface 7 rules P1–P6, `DiagnosisRuns.search` (`SearchPolicy`), `BudgetAccount.policy` and
  `analysis_seconds` filled, the `ranking` record line, CLI `--policy` and `--scope`, ADR-014's scripted tests,
  real F1–F4 with `--policy ranked` giving the same verdicts.
- **Non-goals:** M3's report field and measurement; FYP-2's adaptive policy (ADR-014 §7); any change to
  `rank_candidates` (M1's, fixed before measurement).
- **Anti-goals:** a policy changing anything after the candidate order; a ranked run dropping a candidate;
  any wording that a rank means a cause (claims G3); tuning the rule against fixture ground truth.

## Approaches

| | Approach | Trade-off |
| --- | --- | --- |
| **A (chosen)** | `run_steps(..., order_candidates=None)` takes a function `(candidates, victim) -> (order, SearchPolicy)`; `diagnose()` builds the real one from `evidence.extract` (Project over the copy's compiled classes, one `AnalysisCache`) | `run_steps` stays fake-testable; only `diagnose()` imports M1's code |
| B | `run_steps` imports `evidence.extract` and ranks itself | Every fake-runner test would need compiled classes |
| C | The CLI ranks before `diagnose()` and passes `priority` | The candidates depend on the reproducing order, known only inside `run_steps` |

Contract first was chosen by M2 (same as W24).

## Design

- **`runner/policy.py`** (new): `SearchPolicy` (Interface 7 fields), `POLICIES`, `SCOPES`, `DEEPEN_SHARE = 0.20`;
  `original_order(...)`, `random_order(candidates, seed)`, and `ranked_order(rank, cut_off, candidates, victim,
  time_left)` holding P2–P4's deepening loop over two injected functions (`rank(depth) -> List[(test, score)]`,
  `cut_off(depth) -> bool`), so the loop is tested without JVM or bytecode. `evidence_ranker(project_dir, victim,
  candidates)` adapts M1's `rank_candidates`, `AnalysisCache` and `cache.get(...)["unsupported_observations"]`.
- **`run_steps`**: after the alone check, `order, search = order_candidates(candidates, victim)`; writes the
  `ranking` line via `write_event`; passes `order` as `priority` to `find_polluter` (the hook exists).
  Default (None) = `original`, identical to today.
- **Time:** the seconds share uses the ledger: `time_left` = `limit_seconds × 0.20 − analysis seconds so far`.
  `BudgetedRunner.account(...)` takes `policy` and `analysis_seconds`.
- **`diagnose()`**: `policy`, `scope`; `scope="package"` filters the discovered order to the victim's package
  before anything runs; refused with `original_order` given. Header gains `policy`, `scope`.
- **CLI**: `--policy`, `--scope` (choices); `--scope package` with `--order` exits 2; summary line
  `search:     ranked at depth 2 (3 of 7 candidates with evidence)` / `original order` / `random (seed 0)`,
  plus the fallback note.
- **Docs**: runner README, `docs/04-Implementation/` notes, W25 plan row, members, evidence, GenAI log.

## Left to the builder

The summary line's exact wording; whether `evidence_ranker` lives in `runner/policy.py` or `runner/cli.py`
(it needs the compiled-classes paths, which `diagnose()` has).
