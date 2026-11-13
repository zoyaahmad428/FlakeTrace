# Final demo plan — Form 4

*v1 · 2026-11-13 · Status: **target plan. Nothing below has been run in this form.** Mark each
step `REHEARSED` with its date and the commit only after it has run on the demo machine.*

15 minutes for presentation and demo together. The panel scores implementation progress (25),
demo quality and robustness (15) and testing (10) largely from what it sees here.

**What the panel should leave believing:** the tool tells the truth about what it established, it
stops at a budget, it works on a project we did not write, and each of us understands our part.

## Running order

| # | Step | Shows | Presenter | Time | State |
| --- | --- | --- | --- | --- | --- |
| 0 | `git describe` → `final1-v1`; the action register on screen | The version; previous actions addressed | M2 | 1 min | — |
| 1 | Diagnose fixture F1 with a budget | The normal case: verdict, tallies, deletion evidence, budget account. The wording "static overlap, not confirmed as the cause" | M2 | 2 min | — |
| 2 | Open the resource evidence behind step 1 | Bytecode offsets on both sides; every edge listed | M1 | 1 min | — |
| 3 | **The case the Mid build got wrong:** the victim that fails alone differently (fixture N4) | `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)`. Then the regression test, and its failing run on the Mid commit | M3 | 2 min | — |
| 4 | A budget too small to finish | `UNRESOLVED(BUDGET_EXHAUSTED)` with a report; the alone check still ran in full | M2 | 1 min | — |
| 5 | **The real case:** fastjson FJ-03, `original` against `ranked`, same budget | Total invocations to the same verdict. Whatever the numbers are | M3, M1 | 3 min | — |
| 6 | `verify-bundle` on the bundle from step 5, then change one number and run it again | The recount catches it | M3 | 1 min | — |
| 7 | CI and the test counts | Tests executed, not claimed | M3 | 1 min | — |
| 8 | What is built, what is not, what FYP-2 measures | Honest boundary; the evaluation plan | M1 | 2 min | — |

Step 5 runs live only if it fits the slot; otherwise it is run before the session and its bundle is
opened and replayed in part. Say which.

## What is mocked, hardcoded or pre-run

| Component | State | Said aloud at |
| --- | --- | --- |
| *Fill in before the rehearsal. An empty table means nobody has checked* | | |

## Changed-input questions to expect

The supervisor's briefing lists what a panel should try. Rehearse each:

| They may ask | Be ready to |
| --- | --- |
| "Change the budget and predict what happens" | State the minimum for `n`, then run it |
| "Remove one of F3's polluters" | Predict the verdict; show the deletion check that already answers it |
| "Analyse F2 at depth 1 with deepening off" | Predict that the edge disappears — the property is read one call down, in `FeatureFlags.isTurboEnabled` — and say what the verdict would then be |
| "Show me the run behind this number" | Open the record line from the bundle |
| "What does VERIFIED not tell me?" | The four claims, and the resource sentence |

## Fallback

The fixture steps run offline once Maven's cache is warm; confirm with `mvn -o test-compile` on
the demo machine the day before. A recorded session is backup evidence only — the handbook caps
demo marks at 40% when no live system is shown without a verified reason.
