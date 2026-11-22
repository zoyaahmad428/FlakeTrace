# ADR-016 — Pair mode: diagnose a known victim when no order makes it fail

**Date:** 2026-11-22 (revised the same day) · **Status:** `ACCEPTED` (revised) by M1, M2 and M3 on 2026-11-22 (team WhatsApp group, recorded by M2;
confirmed by approving PR #157). An earlier version (an automatic fallback with "all before" orders) was accepted
the same day, then found over-built on review; this revision replaces it ·
**Owner:** M2 (runner) with M3 (report field, measurement) · **Reviewer of the ranking use:** M1 ·
**Addresses:** M-3 / FT008 (a real case through the whole pipeline), M-2 / FT007 (budget and ranking on real
code), panel action A5 · **Work package:** W35 (Sprint C) ·
**Builds on:** [[03-Design/decisions/ADR-004-w7-diagnosis-runs]],
[[03-Design/decisions/ADR-008-not-reproduced-and-order-search]], [[03-Design/decisions/ADR-011-deletion-evidence]],
[[03-Design/decisions/ADR-014-budget-ledger-and-ranked-search]]

## Context

**What FlakeTrace is for** (`docs/00-Meta/project-one-pager.md`): the input is a known failure of a known victim;
the output is evidence, with a typed reason that tells the developer the next action; the process is bounded by a
budget. We do not do detection.

**How FlakeTrace starts today:** it searches for a polluter only after it has seen the victim fail in a full order
(the starting order, then up to 31 shuffles, ADR-008). Only then do the search, `ddmin`, deletion checks, the
budget and ranking act.

**What FJ-03 showed** (M3, PR #156): from the victim alone with `--scope package`, the real command ran 12,817
invocations and gave `UNRESOLVED (NOT_REPRODUCED)`. In fastjson's discovered order the polluter runs after the
victim; in the 16 of 31 shuffles where it ran before, other tests in between reset the state (cleaners). The
victim is real — `[SerializeWriterTest_14#test_writer_1, MaxBufSizeTest#test_max_buf]` fails 10/10, the victim
alone passes 10/10 — but no order FlakeTrace can find makes it fail.

**Why this is the normal case, not an odd one.** FJ-03 is "known" from a **pair scan** (our POC ran all 524
`[candidate, victim]` pairs). Our main dataset, **IDoFT** (`odr-tests.csv`, 1,908 rows, 24 projects; the five
held-out cases in `eval/benchmark/manifest.json`), also lists each victim **with its polluters, not with a failing
order**. And the setting in which ranking was measured — the POC's 39.3%, RankF — is pair scanning. So:

- today FlakeTrace cannot diagnose most dataset victims from the victim alone;
- giving it the dataset's polluters as an `--order` would hand it the answer (the evaluation plan's leakage rule:
  the oracle may not be an input) — which is what FJ-03's two-test `order.txt` does;
- budget and ranking, the approved contribution, are never exercised on real code.

| Baseline family | Its input | The FlakeTrace mode it compares with fairly |
| --- | --- | --- |
| iFixFlakies | A failing order (from iDFlakies' runs) | Order mode (today) |
| RankF, one-by-one pair scanning, our POC | The victim only — pairs | **Pair mode (this ADR)** |
| iDFlakies | Nothing (detection) | None: out of scope |

## Decision

### 1. A second search mode: pairs

`--search order` (default, today's pipeline, unchanged) or `--search pairs`. In pair mode:

| Rule | |
| --- | --- |
| Input | The victim only (plus scope, policy, budget, `n`). Never the dataset's polluters |
| Alone check first | As today: a victim that fails alone stops as `VICTIM_FAILS_ALONE` |
| Candidates | Every test in scope except the victim, **including tests that come after it** in the discovered order (a pair has no "before" to respect), in the policy's order (Interface 7: `original`, `ranked`, `random`) |
| Each pair | `[c, victim]` runs once. A real (non-synthetic) victim failure is **re-run once**; only if it fails again with the same signature is it adopted (the same safeguard as the re-check before `ddmin`, ADR-007). Otherwise the scan continues |
| Found | The adopted pair is the failing order; its signature is the reference. The normal path certifies it: the alone check (done), the deletion check (one polluter: the alone check, ADR-011 §2), the sequence check `n` times |
| None found | `UNRESOLVED (NOT_REPRODUCED)`, with the pairs tried |
| Budget | Pairs are exploration (Interface 6): never the verification reserve; a cut gives `BUDGET_EXHAUSTED` with "tried k of N" |

### 2. Simple for the user: the verdict names the next step

Pair mode is not started automatically. When order mode ends `NOT_REPRODUCED`, the summary names the next step with
its cost, measured from the run itself (illustrative numbers):

```
UNRESOLVED (NOT_REPRODUCED)  com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf
  next:       no order reproduced the failure. To search pairs instead:
              py -m runner diagnose ... --search pairs   (524 candidates, about 25 min at 2.8 s per JVM)
```

This is the one-pager's design — a typed outcome mapped to a next action — and the user never starts an unseen
multi-hour run.

### 3. Honest report

A new report field `reproduced_by`: `"order"` (the starting or a shuffled order) or `"pair"`, or `null` when never
reproduced. For `"pair"`, a `limitations` line: *"The failure appeared when the polluter ran directly before the
victim (a constructed pair); it was not seen in the project's own or shuffled orders."* The verdict rules (ADR-010)
do not change. (Interface 9 fixes the exact fields.)

### 4. Not in this ADR

| Item | When | Why |
| --- | --- | --- |
| A real case that fails in a **recorded failing order** (order mode on real code; the iFixFlakies comparison) | **Next iteration** | IDoFT gives no failing orders; finding a development victim that fails naturally needs several tries. Every attempt is recorded |
| Automatic switch to pairs | Later, if users want it | The typed next step is simpler and never surprises |
| "All before" orders + `ddmin` (several polluters together, masked) | FYP-2 | Rarer; most exposed to cleaners |
| **Cleaner-aware search** | FYP-2 | When cleaners mask every order, find them (as iFixFlakies discovers cleaners) and keep them out of constructed orders; also evidence for a fix |
| Group testing; a CI-signature start (`--expect-failure`); brittle tests | FYP-2 | Need measurement (ADR-014 §7) or a new input |

## Alternatives considered

| | Option | Why not chosen |
| --- | --- | --- |
| A | Change nothing; FJ-03 stays `NOT_REPRODUCED` | The contribution stays unproven on real code, and dataset victims stay out of reach |
| B | This ADR's first version: automatic fallback, then "all before" | Over-built: could start hour-long runs unasked; its cost cap never triggered; "all before" is the part most hurt by cleaners |
| C | Feed the dataset's polluters as `--order` | Gives the tool the answer (leakage); nothing left for search, budget or ranking to do |
| D | Pick only real cases that fail in natural orders | Needed too (next iteration), but excludes most of the dataset |

## What must be demonstrated

| # | Evidence | Owner |
| --- | --- | --- |
| 1 | FJ-03 from the victim alone with `--search pairs --scope package`: a polluter found, certified, a bundle | M2 runs, M3 verifies |
| 2 | The live comparison on FJ-03: `original`, `ranked`, `random` (5 seeds), one budget, cost to the same verdict, reported as it is | M3 measures; M1 or M2 repeats |
| 3 | A randomly failing victim in a pair is not adopted (the re-run), and the scan continues | M2 (scripted, plus fixture N2) |
| 4 | Real F1–F4, N1–N4 in order mode: unchanged | M2 |

## Tests to write first

| Test | Expected |
| --- | --- |
| Scripted: polluter is candidate k, after the victim in the discovered order | Found after k pairs; `POLLUTER_FOUND`; `reproduced_by: "pair"` |
| Scripted: candidate j fails once by chance | Re-run passes; the scan continues to k |
| Scripted: no pair fails | `NOT_REPRODUCED`; pairs tried = N |
| Scripted: budget cuts the scan | `BUDGET_EXHAUSTED`, "tried k of N" |
| Scripted: victim fails alone | `VICTIM_FAILS_ALONE`; no pairs run |
| Scripted: `ranked` with evidence on candidate k | Its pair runs first |
| Order mode `NOT_REPRODUCED` | The summary's `next:` line names `--search pairs` with a time estimate |
| Real F1–F4, N1–N4 (order mode) | Verdicts unchanged |

## Consequences

- The runner gains `--search pairs` (`run_steps` / `diagnose(search=…)`), a `pair` budget phase and record step, and
  the `next:` line. Report schema: `reproduced_by` (M3). Interface 9 before code.
- FJ-03 becomes a real end-to-end case diagnosed from the victim alone, and budget and ranking are measured live on
  real code, in the setting the POC and RankF used.
- The claim becomes: "FlakeTrace diagnoses a known victim from a failing order or, when none can be found, from pairs
  — saying which."

## Agreement

*The earlier version was ticked by all three on 2026-11-22; this revision was ticked again the same day.*

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☑ | Agreed to the revision 2026-11-22 (team group), recorded by M2; confirmed by approving PR #157 |
| M2 | ☑ | Revised 2026-11-22 after review; replaces the accepted first version |
| M3 | ☑ | Agreed to the revision 2026-11-22 (team group), recorded by M2; confirmed by approving PR #157 |
