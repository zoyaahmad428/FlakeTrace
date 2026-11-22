# ADR-016 — Reproduction fallback: pair search, then "all before", when no order fails

**Date:** 2026-11-22 · **Status:** `ACCEPTED` by M1, M2 and M3 on 2026-11-22 (team WhatsApp group, recorded by M2;
confirmed by approving PR #157), as proposed: the fallback is automatic, `--no-fallback` keeps today's
behaviour. To be built in Sprint C as W35, after its Interface section is agreed ·
**Owner:** M2 (runner) with M3 (report field, measurement) · **Reviewer of the ranking use:** M1 ·
**Addresses:** M-3 / FT008 (a real case through the whole pipeline), M-2 / FT007 (a live ranked-vs-original
comparison on real code), panel action A5 · **Work package:** W35 (Sprint C, agreed 2026-11-22) ·
**Builds on:** [[03-Design/decisions/ADR-004-w7-diagnosis-runs]], [[03-Design/decisions/ADR-007-w10-ddmin-minimisation]],
[[03-Design/decisions/ADR-008-not-reproduced-and-order-search]],
[[03-Design/decisions/ADR-011-deletion-evidence]], [[03-Design/decisions/ADR-014-budget-ledger-and-ranked-search]]

## Context

FlakeTrace searches for a polluter **only after it has seen the victim fail in some full order**: the
starting order, then up to 31 class-first shuffles (ADR-008). On our one real case this never happens:

- FJ-03 (fastjson `e05e9c5`) is a genuine order-dependent victim: `[SerializeWriterTest_14#test_writer_1,
  MaxBufSizeTest#test_max_buf]` fails 10/10, the victim alone passes 10/10 (W26a premise, reproduced by M2).
- With `--scope package` (524 tests), the real command ran 12,817 invocations and gave
  `UNRESOLVED (NOT_REPRODUCED)` (M3, PR #156): in the discovered (sorted) order the polluter runs **after**
  the victim, so it is not even a candidate (the order is cut after the victim: 260 candidates); in the 16 of
  31 shuffles where it ran **before**, other tests in between reset the shared buffer — they act as
  **cleaners** — and the failure never appeared.

So the obstacle is neither the search (it finds the polluter whenever a failing order exists) nor the test (a
real victim): it is the **entry rule**. Consequences today: the real case cannot be diagnosed from the victim
alone; the budget and ranking (W24, W25) — the approved contribution — are never exercised on real code; and
the only real-case ranking result is offline (W25 item 5: no static evidence, position 368 of 524 in both orders).

How the alternatives handle this situation (from [[01-Literature/contemporary-comparison-table]]):

| Tool | Needs a failing order first? | In this situation |
| --- | --- | --- |
| iDFlakies | No — it creates orders by shuffling | Detection only; masked by the same cleaners |
| iFixFlakies | **Yes** — a known failing and a passing order | Cannot start, like FlakeTrace today |
| RankF / one-by-one pair scanning (and our POC) | **No** — runs `[candidate, victim]` pairs | Finds FJ-03's polluter; this is how the POC found it |

## Decision

### 1. One pipeline, three steps before giving up

The user still gives only the victim (and optionally `--order`, `--scope`, `--policy`, a budget). After the
alone check passes (unchanged: a victim that fails alone stops as `VICTIM_FAILS_ALONE`), and only when no order
reproduced a real failure:

```
1. Observed order:  the starting order, then shuffles               (today, ADR-008)
2. Pair search:     [candidate, victim] for each candidate in scope  (new)  → single polluters
3. "All before":    [every candidate…, victim], a few orders        (new)  → several polluters together
4. Nothing failed:  UNRESOLVED (NOT_REPRODUCED), with every step's runs and cost
```

| Step | Rule |
| --- | --- |
| 2. Pair search | Candidates are **all tests in scope except the victim**, in the policy's order (Interface 7: `original`, `ranked`, `random`). Each pair runs **once**. The first real (non-synthetic) victim failure becomes the reference signature; that pair is the failing order. From there the normal path runs: alone check (already done), deletion check (one polluter: the alone check, ADR-011 §2), the sequence check `n` times. No minimisation is needed |
| 3. "All before" | If no pair fails: run `[all candidates in scope, victim]` once in the discovered order, then up to **3** class-first shuffles of the candidates with the victim kept last. The first real failure gives a failing order; from there the existing path runs: single-polluter search over it, then `ddmin` (ADR-007), deletion checks (ADR-011), the sequence check |
| Automatic | Steps 2–3 run automatically. `--no-fallback` keeps today's behaviour (stop at step 1) |
| Honest wording | A failure found by step 2 or 3 was seen **in an order FlakeTrace constructed**, not in the project's natural run. The report says so in `limitations`: "the failure appeared only when the polluter ran directly before the victim (a constructed order); it was not seen in the project's discovered or shuffled orders" |

### 2. Cost, bounded and announced

- Steps 2–3 are **exploration** (Interface 6): they never spend the verification reserve (`3n`); when the limit
  is reached the result is `UNRESOLVED (BUDGET_EXHAUSTED)` with "tried k of N candidates" and a suggested limit.
- Before step 2 the CLI prints the worst case, e.g. "no order reproduced; pair search over 524 candidates may cost
  up to 1,048 invocations, 'all before' up to 2,100".
- **Default cap** when the user gave no `--budget-invocations`: one full pair pass + the "all before" orders + the
  reserve. A diagnosis is never unbounded.
- Ranking (W25) orders the pairs; with static evidence the polluter is usually among the first. Without evidence
  (FJ-03) it changes nothing — an honest, now **live**, result.
- Step labels `pair` and `all-before` are new record phases; the ledger, the recount (Interface 6 B8) and the
  bundle (Interface 8) count them like the others.

### 3. What the report carries (contract change)

A new field, proposed for M3's schema: `reproduced_by` — `"starting-order"`, `"shuffled-order"`, `"pair"`,
`"all-before"` or `null` (never reproduced). With step counts in the budget account's `spent` (new keys `pair`,
`all-before`). The verdict rules (ADR-010) are unchanged: a pair-found sequence is certified by the same alone
check, deletion checks and repeated sequence check.

### 4. Left for FYP-2, stated now

| Item | Why it waits | What it would add |
| --- | --- | --- |
| **Cleaner-aware search** | When a cleaner sits between the polluters and the victim in every order tried, steps 1–3 can all be masked. Solving it means **finding the cleaners** — tests that undo the pollution — and keeping them out of the constructed orders, as iFixFlakies discovers cleaners for its patches | Diagnoses masked multi-polluter cases; the cleaners found are themselves evidence for a fix (and for the gated CDR) |
| Group testing | Several candidates before the victim in one JVM clears many at once, but a cleaner inside the group hides the failure — the FJ-03 problem | Lower cost per candidate; belongs with the adaptive policy (ADR-014 §7) where it can be measured |
| Known-failure start (`--expect-failure`) | Pair search does not need a signature; a pasted CI signature only confirms it is the *same* failure CI saw | A CI-log entry point; with the Surefire report reader, a path to CI integration |
| Brittle tests | A test that fails alone and passes after a state-setter is the mirror case (agenda §6) | The second real-case family |

## Alternatives considered

| | Option | Why not chosen |
| --- | --- | --- |
| A | Keep today's rule; report FJ-03 as `NOT_REPRODUCED` | Honest, but leaves the contribution untested on real code and the user with nothing |
| B | Require a pasted CI failure signature to start a pair search | Extra work for the user; FJ-03 has no CI failure to paste; kept as the optional `--expect-failure` (§4) |
| C | Pair search **opt-in** (`--pair-search`) | Predictable, but users must know it exists; the announced cost and default cap give the same predictability automatically |
| D | Choose an order that places the polluter before the victim | Biased: we would pick it knowing the answer |

## What must be demonstrated

| # | Evidence | Owner |
| --- | --- | --- |
| 1 | FJ-03 from the victim alone (`--scope package`): pair search finds a real polluter; the alone, deletion and sequence checks certify it; a bundle | M2 runs, M3 verifies |
| 2 | The live comparison on FJ-03: `original`, `ranked`, `random` (5 seeds) under one budget, cost to the same verdict; first relevant pair at the POC's position or not, reported as it is | M3 measures, M1 or M2 repeats |
| 3 | A multi-polluter case masked in natural orders is found by "all before" + `ddmin` (a new fixture control) | M2, M3's fixture |
| 4 | A cleaner-masked case stays `NOT_REPRODUCED` with every step's cost — the stated limit, not a wrong verdict | M2 |

## Tests to write first

| Test | Expected |
| --- | --- |
| Scripted: nothing reproduces, victim passes alone, polluter is candidate k | Pair search finds it after k pairs; `POLLUTER_FOUND`; `reproduced_by: "pair"` |
| Scripted: two polluters needed together, masked in natural orders | No pair fails; "all before" fails; `ddmin` keeps both; both deletion checks `NEEDED` |
| Scripted: a cleaner always between polluter and victim | `NOT_REPRODUCED`; `spent` shows the pair and all-before runs |
| Scripted: budget cuts the pair search | `BUDGET_EXHAUSTED`, "tried k of N" |
| Scripted: victim fails alone | `VICTIM_FAILS_ALONE`; no pair runs |
| Scripted: `--no-fallback` | Today's behaviour exactly |
| Scripted: `ranked` with evidence on candidate k | Its pair runs first |
| Real F1–F4, N1–N4 | Verdicts unchanged (they reproduce at step 1) |

## Consequences

- `run_steps` gains steps 2–3 between the alone check and `NOT_REPRODUCED`; the CLI gains `--no-fallback` and
  the cost announcement. Interface 6 gains two exploration phases; Interface 7's candidate order applies to the
  pair search. Report schema: `reproduced_by` (M3). A new Interface section is written before code, as for W24/W25.
- FJ-03 becomes a real end-to-end case for W26b and the first live real-code measurement of the budget and ranking.
- Diagnoses that today stop at `NOT_REPRODUCED` may now cost more; the announcement and the default cap keep it
  predictable.
- The claim changes from "FlakeTrace diagnoses failures it can reproduce in an order" to "…in an order it observes,
  or failing ones it can construct, stating which" — recorded in the claims ledger when built.

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☑ | Agreed 2026-11-22 (team group), recorded by M2; confirmed by approving PR #157 |
| M2 | ☑ | Proposed and agreed 2026-11-22 |
| M3 | ☑ | Agreed 2026-11-22 (team group), recorded by M2; confirmed by approving PR #157 |
