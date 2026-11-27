# Final demo plan — Form 4

*v2 · 2026-11-27 (M2) · Status: **target plan, driven from the web UI. Not yet rehearsed.** Mark each step
`REHEARSED` with its date and the commit only after it has run on the demo machine. v2: the UI runs every option the
demo needs (branch `m2/ui-demo`); step 5 is FJ-03 in pair mode from its committed bundle, because the v1 step
("`original` against `ranked`") cannot run: FJ-03 is `NOT_REPRODUCED` in order mode and `ranked = original` on it.*

15 minutes for presentation and demo together. The panel scores implementation progress (25),
demo quality and robustness (15) and testing (10) largely from what it sees here.

**What the panel should leave believing:** the tool tells the truth about what it established, it
stops at a budget, it works on a project we did not write, and each of us understands our part.

## Running order (all in the web UI unless stated)

| # | Step | In the UI | Shows | Presenter | Time | State |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | `git describe` → `final1-v1`; the action register on screen | A terminal, then the register | The version; previous actions addressed | M2 | 1 min | — |
| 1 | Diagnose fixture F1 live, with a budget | Source → "Use the seeded fixture"; Target → F1, Advanced → budget, Diagnose | The normal case: verdict, tallies, deletion evidence, budget account. The wording "static overlap, not confirmed as the cause" | M2 | 2 min | — |
| 2 | Open the resource evidence behind step 1 | Evidence graph | Bytecode offsets on both sides; every edge listed; then **F3** (A4): Source → Committed evidence → `20261121T184910Z-odfixture.ToggleVictimTest#expectsNotBothFlagsSet` — 17 earlier tests reduced to 2 polluters; the Diagnosis step's **Deletion checks** panel shows each removed for 20 runs with the victim passing 20/20 (`NEEDED`), 20/20 and 0/20, static overlap only ([[07-Defense/a4-isolation]]) | M1 | 1 min | — |
| 3 | **The case the Mid build got wrong:** the victim that fails alone differently (fixture N4) | Target → N4, Diagnose | `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)`. Then the regression test, and its failing run on the Mid commit (terminal) | M3 | 2 min | — |
| 4 | A budget too small to finish | Target → F1, Advanced → budget 66 invocations | `UNRESOLVED(BUDGET_EXHAUSTED)` with a report; the alone check still ran in full | M2 | 1 min | — |
| 5 | **The real case:** fastjson FJ-03 in pair mode, from the victim alone | Source → Committed evidence → `20261122T120044Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | `CANDIDATE`, `SerializeWriterTest_14#test_writer_1` after 368 of 524 pairs, 798 invocations, "found in a constructed pair"; `verify` run on opening. Then the table's other six pair-mode rows: `ranked` = `original` (798, no static edge to rank with), five random seeds 76–436 invocations, each to a `CANDIDATE` polluter (no static edge, so not `VERIFIED`) — four distinct polluters across the seven runs. **Under a stated budget** (W39, `--budget-invocations 400`): `original` stops `BUDGET_EXHAUSTED` after 170 of 524 pairs, nothing blamed; random seeds 1–3 reach `CANDIDATE` at 76, 184, 258 (rows `20261127T1037…`–`…1049…`). Order mode on the same scope: `NOT_REPRODUCED` after 12,817 (row `20261124T151413Z`) | M3, M1 | 3 min | — |
| 6 | Change one number in a copy of step 5's bundle, and check it | Source → "Check a bundle folder" → the copy's path | "report.json does not match its checksum in manifest.json; the bundle was changed": **the checksum catches it** before the recount runs. The committed bundle still checks OK | M3 | 1 min | — |
| 7 | CI and the test counts | GitHub Actions | Tests executed, not claimed | M3 | 1 min | — |
| 8 | What is built, what is not, what FYP-2 measures | The greyed labels in the UI | Honest boundary; the evaluation plan | M1 | 2 min | — |

Step 5 is not run live: a package-scope pair run of FJ-03 takes about 11 minutes (8 min of runs + ~3 min Maven build)
and needs JDK 8. Its bundle is real committed evidence, re-checked by `verify` when opened, and the UI labels it
"pre-run, not run now". Say so aloud.

## What is mocked, hardcoded or pre-run

| Component | State | Said aloud at |
| --- | --- | --- |
| Step 5's FJ-03 runs | **Pre-run** on 2026-11-22 (M3's machine; M1 reproduced the pair diagnosis, #163); committed bundles, verified when opened | Step 5 |
| Step 6's changed copy | **Prepared before the slot** by hand (copy step 5's bundle to a scratch folder, change `"n": 20` to 21 in `report.json`); the committed bundle is never touched | Step 6 |
| Steps 1, 3, 4 | Live runs on the demo machine | — |
| Nothing in the UI is simulated | ADR-009; `ui/web/src/lib/nosim.test.ts` | Step 8, if asked |

## Changed-input questions to expect

The supervisor's briefing lists what a panel should try. Rehearse each:

| They may ask | Be ready to |
| --- | --- |
| "Change the budget and predict what happens" | State the minimum for `n`, then run it |
| "Remove one of F3's polluters" | Predict that the victim passes again — ground truth says both are required. **Updated 2026-11-20 (W20):** the report already answers this — F3's `deletion_checks` show each polluter removed for 20 runs and the victim passing 20/20 each time (`NEEDED`), which is why F3 is `VERIFIED`. F1/F2/F4 (one polluter each) reuse the alone runs for this check (ADR-011 §2). Before W20, F3 was `CANDIDATE` |
| "Analyse F2 at depth 1 with deepening off" | Predict that the edge disappears — the property is read one call down, in `FeatureFlags.isTurboEnabled` — and say what the verdict would then be |
| "Show me the run behind this number" | Open the record line from the bundle |
| "What does VERIFIED not tell me?" | The four claims, and the resource sentence |

## Fallback

The fixture steps run offline once Maven's cache is warm; confirm with `mvn -o test-compile` on
the demo machine the day before. A recorded session is backup evidence only — the handbook caps
demo marks at 40% when no live system is shown without a verified reason.
