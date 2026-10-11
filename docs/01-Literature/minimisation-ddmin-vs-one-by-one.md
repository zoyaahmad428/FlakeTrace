# Minimisation: one-by-one search vs delta debugging (ddmin)

*Panel action A6 ("do more research to improve the proposed solution"), Member 1, 2026-10-11.
Design decision it supports: [[03-Design/decisions/ADR-007-w10-ddmin-minimisation]].*

> **Source check.** Every literature statement below is taken from the team's existing notes
> ([[per-paper/ifixflakies]], [[per-paper/rankf]], [[parameter-provenance]]); no new reference is
> added. Before any of it is cited in the report, the citing member opens the original:
> - [x] [4] iFixFlakies, the Minimizer section — opened by Member 1, 2026-10-11
> - [x] [11] Zeller and Hildebrandt, the ddmin algorithm and its 1-minimality property — opened by Member 1, 2026-10-11

## The question

A victim fails after a long order of earlier tests. Which of them are needed? Two ways to search:

| | One-by-one (OBO) | Delta debugging (`ddmin`) |
| --- | --- | --- |
| What it runs | `[candidate, victim]` for each earlier test | the victim after halves, then smaller and smaller chunks and complements, of the earlier tests |
| Runs needed | one per earlier test, always | few when the cause is a small set; more when the set is large or the split points are unlucky |
| Finds | a single polluter | a **1-minimal** set: removing any one test stops the failure |
| Misses | anything that needs two or more tests together | other polluter combinations in the same prefix; never claims the minimum |

## What the literature says (from our notes)

- **ddmin is the established minimiser.** iFixFlakies' Minimizer applies delta debugging to the
  tests before the order-dependent test to find its polluters [4]; its cleaner discovery falls
  back to OBO where delta debugging is inapplicable ([[per-paper/ifixflakies]]).
- **1-minimal, not minimum.** Delta debugging returns a 1-minimal result [11]; a global minimum
  needs exponential search, and it does not necessarily find all polluters in a prefix [28]
  ([[parameter-provenance]]). Our reports therefore say "1-minimal, not necessarily the minimum".
- **ddmin is not always cheaper.** Rahman et al. measured delta debugging at 166.5 s average /
  34.2 s median to the first polluter, and in one example 419.0 s against OBO's 60.9 s [5]
  ([[per-paper/ifixflakies]]). RankFL and RankFO, which rank the candidates first, reported
  faster discovery than both [5] ([[per-paper/rankf]]).
- **Joint polluters are rare but real.** Earlier work treats them as very rare; Zhang et al. found
  82% of dependent tests revealed by at most two tests, which leaves a non-empty remainder [2]
  ([[parameter-provenance]]).

## What our own runs show

All from recorded runs ([[evidence-m2]], [[evidence-m1]]):

| Case | One-by-one | ddmin | Result |
| --- | --- | --- | --- |
| F1, F2 (one polluter) | finds it | not run | `VERIFIED`; cost unchanged by W10 |
| F3 (two polluters needed), main `39b2dff`, 14 earlier tests | 14 runs, finds nothing | 10 runs (1 re-check of the full order + 9 `ddmin`) | `VERIFIED`, `setFlagA` + `setFlagB` = ground truth, 20/20, alone 0/20 |
| Fake runner: 2 needed tests in a 12-test prefix | — | 25 runs | 1-minimal |
| Fake runner: 2 needed tests in a 100-test prefix | (100 runs) | 48 runs | 1-minimal |

## What this means for FlakeTrace

1. **Order of the two searches.** OBO first (cheap when there is one polluter, which the
   literature and our fixture both show is the common case), ddmin only when OBO finds nothing
   and the full order fails once more. This is what ADR-007 built; it keeps F1/F2's cost unchanged.
2. **Claim language.** Always "1-minimal"; never "the minimum" or "all polluters".
3. **Cost is a measured claim, not a given.** Because ddmin can be slower than OBO [5], the
   evaluation must compare run counts against OBO and the iFixFlakies minimiser on real cases
   (not yet run; Final-1). The fake-runner numbers above show the shape, not real cost.
4. **Resource evidence per polluter.** With several polluters, the evidence step runs once per
   polluter (`analyse_pair`, ADR-006/ADR-007); `VERIFIED` needs an edge for every one of them.
5. **Iteration 2 candidates** (only after a member reads them): ranking candidates before the
   search (RankF [5]) to cut OBO's one-run-per-test cost.
