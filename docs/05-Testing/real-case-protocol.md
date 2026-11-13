# Real-case protocol — the first real project through the whole pipeline

*v1 · 2026-11-13 · Status: `PROPOSED`. The choice of case and the comparator are Member 3's to
confirm; the supervisor asked to see "a feasible case and protocol" at the next review (FT008).
**Freeze this file before the first whole-pipeline run on the case.***

**Lead:** M3 · **Execution compatibility:** M2 · **Resource coverage:** M1 ·
**Independent repeat:** M1 or M2 · **Work package:** W26

---

## Why this exists

All seven diagnosed cases come from one fixture we wrote. On a real project we have run the
**extractor** (fastjson, two cases) and nothing else. The official Mid comment asks for
"real-project validation". The handbook's Final-1 gate asks for "the comparison baseline measured".

This protocol fixes, **before any result is seen**, which case, which environment, which
comparison and which numbers.

## What we already hold

The POC (`POC/`, decision record v3, 2026-09-04) built and scanned real cases with its own scripts.
Its stored results are reusable facts:

| File | What it holds |
| --- | --- |
| `POC/manifest/cases.csv` | 23 cases across json-iterator, fastjson and ormlite-core, with pinned commits, licences and build status |
| `POC/results/alone.csv` | Each victim run alone 10 times: which pass alone (victims) and which fail alone (brittle) |
| `POC/results/scan_<case>.csv` | The outcome of every `[candidate, victim]` pair, with `od_relevant` |
| `POC/results/replay.csv` | The accepted pair for each reproduced case, 10 replays |

Read straight from those files on 2026-11-13:

| Case | Project | Kind | Candidates | Relevant | First relevant in original order |
| --- | --- | --- | --- | --- | --- |
| FJ-01 | fastjson | **brittle** — fails alone 10/10 | 72 | 42 | 5 |
| FJ-02 | fastjson | **brittle** — fails alone 10/10 | 722 | 24 | 39 |
| **FJ-03** | fastjson | **victim** — passes alone 10/10 | 524 | 6 | **368** |
| **FJ-04** | fastjson | **victim** — passes alone 10/10 | 524 | 2 | **220** |

> **A correction to how we have talked about fastjson.** FJ-01 and FJ-02, the two cases the
> extractor was run on, are **brittle**: they fail alone and pass after a state-setting test. Today
> the product answers every brittle case with `UNRESOLVED(VICTIM_FAILS_ALONE)` — correctly, and
> without diagnosing it. They cannot be the first whole-pipeline case. Nine of the POC's eleven
> held-out cases are brittle too (`POC/results/alone.csv`). See "Brittle tests" below.

## The case

**Primary: FJ-03.**

| | |
| --- | --- |
| Project | `https://github.com/alibaba/fastjson` — Apache-2.0 |
| Commit | `e05e9c5e4be580691cc55a59f3256595393203a1` |
| Victim | `com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` |
| Known polluter (POC's accepted pair) | `com.alibaba.json.bvt.serializer.SerializeWriterTest_14#test_writer_1` |
| Expected failure | `junit.framework.AssertionFailedError`, top frame `MaxBufSizeTest.test_max_buf` |
| Test style | JUnit 3 `TestCase` |
| Candidate scope | The victim's package: 524 tests (the frozen scope rule) |
| Why this one | A true **victim**, so today's pipeline applies. Only 6 of 524 candidates are relevant and the first is 368th — the situation where an execution budget and ranking matter |

**Second, if the first completes: FJ-04** (`JSONSerializerTest2#test_0`, 2 relevant of 524).
**Second project, if time allows: one ormlite-core case** (commit
`632b87c2a455b8eab4a6c09324e1f166273588d8`, ISC licence), where the POC needed the whole module as
scope.

Not fetched or built by us yet in this iteration. **The first task is to find out whether it still
builds.** A case that will not build is recorded with its error and replaced by the next; it is
not dropped silently.

## Environment — pinned and recorded

| | |
| --- | --- |
| JDK | Temurin 8, as the POC used (`1.8.0_502` recorded there) |
| Build | The project's own Maven build, `test-compile` |
| Timezone and locale | **Set explicitly and recorded.** fastjson date tests change behaviour with the timezone; the POC's container ran in UTC |
| Lifecycle mode | Recorded. Results are produced only after the lifecycle control of ADR-012 passes |
| Where | The pinned container of ADR-012 if it exists by then; otherwise a named laptop, with the versions in the bundle |
| Source | Fetched by script at the pinned commit. Never copied into our repository |

## Steps

| # | Step | Output | If it fails |
| --- | --- | --- | --- |
| 1 | Fetch at the pinned commit, build | Build log | Record the error. Try the next case |
| 2 | Confirm the premise with the runner directly: victim alone ×10; `[known polluter, victim]` ×10 | Two tallies | If the victim does not pass alone 10/10 or the pair does not fail, the case is not reproduced under our runner. **That is a finding about our harness** — compare lifecycle modes before discarding it |
| 3 | Fix the starting order: the package's discovered order, cut after the victim. Save it as an `--order` file | The order file, in the bundle | — |
| 4 | Check the starting order fails. If not, let the shuffled-order search look for one | A failing order and its seed | `NOT_REPRODUCED` is a valid, reportable result |
| 5 | **Freeze this file.** Commit it with the order file's checksum | A commit | — |
| 6 | Whole pipeline, policy `original`, a stated budget, `n = 20` | A bundle (ADR-013) | Whatever the verdict, it is kept |
| 7 | Whole pipeline, policy `ranked`, **same** budget, `n` and order | A bundle | Same |
| 8 | Policy `random`, five fixed seeds | Five bundles | Same |
| 9 | An independent repeat of step 6 or 7 by another member on another machine | A reproduction record | Differences are recorded |

Steps 6 to 8 need the budget ledger and the policies of ADR-014. Steps 1 to 5 need only what
exists now, and are the **preparatory output for the next supervision meeting**.

## The comparison

**The question:** under the same execution budget, does evidence-ranked search reach the same
certified result with fewer test-method invocations than searching in the original order?

| | |
| --- | --- |
| Same endpoint | Every policy runs the same pipeline to a report: search, minimisation, sequence check, deletion checks. Not "first failure seen" |
| Cost | **Total** test-method invocations, verification included. JVM launches, wall-clock and analysis seconds reported beside it |
| Yield | The verdict each policy reached, and whether the blamed tests are among the POC's `od_relevant` set |
| Uncertainty | With one or two cases there is no statistic to compute. Each case is reported separately, with the five random seeds as the spread. Paired intervals across projects need the larger FYP-2 set |

**Free and available now — the offline comparison.** `scan_FJ-03.csv` already holds the outcome of
all 524 pairs. Any candidate order can be scored against it without one JVM run: the position of
the first relevant test is the number of confirmations that order would have needed. Member 3
computes it for `original` (368, read from the file), `random` (expected value and seeds) and the
product's `rank_candidates`. The same for FJ-04, and for the brittle cases once their direction is
supported.

**What we may and may not say afterwards**

| May | May not |
| --- | --- |
| "On FJ-03, with a budget of B invocations, `ranked` reached `<verdict>` in X and `original` in Y" | "FlakeTrace is N% cheaper" — two cases from one project are not a rate |
| "The POC measured a 39.3% median saving offline on eight held-out fastjson cases with its own extractor" | That the product reproduces that figure, until it has been measured with the product |
| "iFixFlakies and RankF are the published comparators; integrating them is FYP-2 work" | That we have compared against any published tool |

A result that shows no saving, or a ranking that puts the polluters last, is **reported as it is**.

## Development and held-out cases

| Set | Cases | Rule |
| --- | --- | --- |
| Development | The fixture; FJ-01 to FJ-04; the ormlite cases; the POC's HO cases, which have already been looked at | May be used to build and debug |
| Held-out | The five IDoFT entries in `eval/benchmark/manifest.json` (dropwizard, http-request, marine-api, openpojo, spring-boot) — metadata only so far | **Not built, run or inspected** until the ranking rule, the thresholds and the budget policy are frozen. Then run once |

Results on development cases are always labelled as development results.

## Brittle tests — an open scope question

A **brittle** test fails alone and passes only after a test that sets the state it needs. The
certificate contract has always listed "victim, brittle, mixed" as a classification, and the
frozen definitions describe both directions. The product implements one.

| | |
| --- | --- |
| What supporting it means | When the victim fails alone every time: search for a predecessor after which it **passes**; verify `[state-setter, victim]` passes `n` of `n` and the victim alone fails `n` of `n`; report the classification and the state-setter |
| Why it matters | Most reproducible fastjson cases we hold are brittle. FJ-02 has 24 relevant tests among 722 with the first at position 39 |
| Why it is not in this iteration | The supervisor's instruction is to fix certification, then budget, then one real case — not to add a direction. It also changes the report contract |
| Proposed | Decide at the next supervision meeting whether it is the first FYP-2 increment ([[10-Final1/supervisor-agenda]] item 6) |

## Records kept

Every run of steps 2 to 9 produces a bundle or a log that is kept, including failed builds,
unreproduced cases and unfavourable comparisons. The yield — attempted, built, premise confirmed,
diagnosed — is reported with every excluded case and its reason.
