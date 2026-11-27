# A6 — M2's nearest baseline: search, minimisation and verification

*Panel action A6 (proposal defence). v1 · 2026-11-27 · M2 (Abdul Raffay), written with Claude ([[genai-log-m2]]).
Status: `DRAFT` — **every fact about a paper below is to be checked by M2 against the paper itself before report v2**.
Sources cited: only the four M2 has opened himself (his statement, 2026-11-27): [3] iDFlakies, [4] iFixFlakies,
[5] RankF, [28] Wei et al. ([[01-Literature/references]]). Delta debugging's original paper [11] is **not cited**: not
opened by M2.*

## My part, and its nearest tools

My part of FlakeTrace is `runner/`: given a known victim, **find** its polluters, **shrink** the set, **verify** it by
repeated runs, under an **execution budget**. The nearest existing tools:

| Step | Nearest tool | Why it is the nearest |
| --- | --- | --- |
| Shrink a failing order to its polluters | **iFixFlakies' Minimizer** [4] | Applies delta debugging to the tests before the order-dependent test in a failing order, to find its polluters |
| Order the candidates / find a polluter from the victim alone | **RankF** [5] (RankFO, RankFL) | Ranks candidate tests so fewer are run before a true polluter is confirmed; its baseline is one-by-one (OBO) pair scanning |
| Find that a test is order-dependent at all | **iDFlakies** [3] | Detection. **Not our task:** FlakeTrace starts from a known victim |

## What they do, what FlakeTrace does

| | iFixFlakies [4] / RankF [5] | FlakeTrace (my part), with our evidence |
| --- | --- | --- |
| **Same, and not ours** | Delta debugging on a failing order; the victim / polluter / brittle / cleaner vocabulary [4] | We use both, and claim neither as a contribution (claims ledger B1): our result is **1-minimal, never "the minimum"** (D9) |
| **Each kept test re-checked** | The Minimizer repeats isolation (its RERUN parameter) [4]; it does not necessarily find all polluters in a prefix (as reported by Wei et al. [28]) | After shrinking, **every kept test is removed and the rest re-run `m` = 20 times**; it is kept only if the victim passed all 20 (ADR-011). F3: both polluters `NEEDED`, 20/20 each (`docs/07-Defense/a4-isolation.md`) |
| **A budget** | No budget model in [4] | Every run is counted in a ledger with a **verification reserve** (3n); exploration stops as `BUDGET_EXHAUSTED` with nothing blamed (ADR-014). Real case, W39: FJ-03 under 400 invocations — `original` stopped `BUDGET_EXHAUSTED` after 170 of 524 pairs; seeds 1–3 reached `CANDIDATE` at 76, 184, 258 |
| **Search order** | RankFO ranks from previously observed orders; RankFL from test code, a learned model [5] | Three fixed orders: `original`, `ranked` (by our static evidence), `random` (seeded). **No learned ranker.** On FJ-03 our static evidence found nothing, so `ranked` = `original` (798 invocations); random seeds needed 76–436 (#165) |
| **From the victim alone** | OBO: run each candidate with the victim [5] | **Pair mode** (ADR-016): every candidate in scope as `[candidate, victim]`, a failing pair **re-run once** before it is adopted, then the same deletion and sequence checks. FJ-03: `CANDIDATE` after 368 of 524 pairs |
| **When unsure** | — | **Typed refusal:** `UNRESOLVED` with a reason (`NOT_REPRODUCED`, `BUDGET_EXHAUSTED`, `INCONSISTENT_OUTCOMES`, …), never a guess |
| **Checkable by someone else** | — | Evidence **bundles**: record, report, checksums; `verify` recounts, `replay` re-runs (ADR-013); reproduced on a second machine (M1) |

## What they have and we do not

- **Cleaners and patches** [4]: iFixFlakies finds cleaners and synthesises a fix. FlakeTrace does not repair
  (repair is gated, FYP-2).
- **A learned ranker** (RankFL [5]) and **order-history ranking** (RankFO [5]).
- **Scale:** RankF was evaluated on 155 order-dependent tests across 24 projects [5]; FlakeTrace on our fixtures and
  **one** real case (FJ-03).
- **Brittle tests:** iFixFlakies handles state-setters for brittles [4]; FlakeTrace diagnoses victims only.

## What we must not claim

- **Not "cheaper than iFixFlakies or RankF".** We have **not** run either tool on the same cases; that measured
  comparison is FYP-2 (A6, FT008).
- **Not "delta debugging is always cheaper".** Rahman et al. measured delta debugging slower than OBO in their motivating
  example [5]; on FJ-03 a random order beat both `original` and `ranked`. Cost depends on where the polluters sit.
- **Not "ranking saves executions" on the real case:** with no static evidence, `ranked` cannot reorder anything (G9).

## To check against the papers before report v2 (M2)

1. [4]: the Minimizer's RERUN behaviour, and that the framework has no budget model.
2. [28]: the statement that iFixFlakies does not necessarily find all polluters, and its exact wording.
3. [5]: RankFO's and RankFL's inputs; OBO as the baseline; the 155 tests / 24 projects; delta debugging vs OBO in the
   motivating example.
4. [3]: iDFlakies as detection (finding that a test is order-dependent), not polluter search.
