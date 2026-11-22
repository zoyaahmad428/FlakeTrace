# Real-case protocol — the first real project through the whole pipeline

*v1 · 2026-11-13 · Status: `STEPS 1-8 COMPLETE FOR FJ-03` (2026-11-21, M3). Steps 1-5 complete
2026-11-19 — see "Findings" below. **Steps 6-9 were blocked** on a real tool gap found while
doing steps 3-4 (`runner/discovery.py` could not discover or validate an `--order` naming the
known polluter) — **fixed by M2 2026-11-20** (PR #110,
[[00-Meta/risk-register]]), unblocking steps 6-9. **Steps 6-8 run for real 2026-11-21** (M3,
[[evidence-m3]]): `original`, `ranked` and `random` (five seeds) all give the identical real
verdict at the identical real cost. **Step 9 (independent repeat) is the one piece left**,
pending M1 or M2 on another machine. The choice of case and the comparator are Member 3's to
confirm; the supervisor asked to see "a feasible case and protocol" at the next review (FT008).*

## Findings (2026-11-19, M3, real runs — native Windows, JDK 24 for the runner itself,
real Temurin 8 (`1.8.0_512`, downloaded as a portable zip for this build only, not installed)
for building and running fastjson, as the POC did)

**Steps 1-2 confirmed exactly as this file predicted.** `mvn -B -DskipTests test-compile` on
fastjson at the pinned commit: `BUILD SUCCESS` in 3:41, 172 main + 2,496 test sources, no source
changes afterward (`git status` clean). Victim alone ×10: 10/10 PASS. `[known polluter,
victim]` ×10: 10/10 FAIL, `junit.framework.AssertionFailedError` at
`MaxBufSizeTest.test_max_buf:20` — exactly the signature this file names. Timezone/locale
pinned explicitly via `JAVA_TOOL_OPTIONS=-Duser.timezone=UTC -Duser.language=en
-Duser.country=US` (recorded here since this file's own Environment table requires it).

**Step 3 found a real tool gap, not just a protocol detail.** "The package's discovered order"
is supposed to come from `runner.discovery.discover_order()`, scoped to
`com.alibaba.json.bvt.serializer`. That function's `is_surefire_test_class()` hardcodes
Surefire's *default* include pattern. fastjson's `pom.xml` overrides Surefire entirely
(`<includes><include>**/bvt/**/*.java</include></includes>` — every class under any `bvt/`
folder, no naming convention at all), so our discovery silently misses real test classes,
**including the known polluter `SerializeWriterTest_14`** (and `_15`; neither matches
`Test*`/`*Test`/`*Tests`/`*TestCase`). A workaround (enumerate every class in the package by
file, let the harness's own JUnit reflection decide which have test methods) found exactly
525 real test methods — matching the POC's own 524-candidate count (+1 victim) exactly, so the
workaround's correctness is itself confirmed. The *product's own CLI* has the identical gap:
`py -m runner diagnose --order eval/real-cases/fj03/order.txt ...` refuses the case with
`"1 test(s) in the given order are not among the project's tests"`. This blocks steps 6-9 until
`runner/discovery.py` reads the project's actual Surefire configuration instead of assuming the
default — see [[00-Meta/risk-register]] for the registered risk and what the fix needs.

**Step 4 found a second real, honest result — not a dead end.** The package's discovered order
(workaround-corrected, 525 methods, cut after the victim at 261 entries) does not fail, run for
real: confirmed (`PASS`). Per this file's own rule, that's a reportable `NOT_REPRODUCED` for the
natural order. The ADR-008 shuffled-order fallback (31 distinct shuffles, real
`runner.orders.distinct_shuffles`/`search_orders`, same workaround-corrected candidate pool) was
then run for real: **none of the 31 reproduced the failure**, even though several shuffles
placed all 6 of the known-relevant candidate methods before the victim. Inspected one in detail
(seed 0, 513 tests, all 6 relevant methods before the victim): many *other*
`SerializeWriterTest_N` variant classes also run between the last relevant candidate and the
victim (`_19`, `_7`, `_12`, `_BrowserSecure_4_script`, ...) — these almost certainly also touch
`SerializeWriter`'s shared buffer-size state and undo the pollution before the victim runs. This
is a genuine, real-world finding distinct from our clean synthetic fixture: **a dense real test
suite can have other tests that silently cancel the very pollution a random shuffle is trying to
expose**, which a purely random full-suite shuffle search cannot reliably see through, even
though the underlying bug is 100% real and trivially reproducible with the *exact* pair. This is
direct, real-world motivation for why a targeted, evidence-ranked search (W25) — which tries one
candidate immediately before the victim, the same shape that already works in step 2 — matters
more than broad random shuffling on a project of this density.

**Step 5.** This file is frozen with the above findings. The known-pair order is committed at
`eval/real-cases/fj03/order.txt` (SHA-256 `8c9b208ac5c970138a37679fc3f91156e467c7701d6b91e2e49dc4b66234be1e`)
as the starting order for steps 6-9, since neither the natural discovered order nor the 31-shuffle
search found a different one, and this is the one directly confirmed in step 2. Steps 6-9
themselves wait on the discovery.py fix (and, for 6-8, the budget ledger, ADR-014/W24, already
not yet built).

**Steps 6-8 (2026-11-21, M3, real runs — discovery.py's gap fixed by M2 2026-11-20).** Because
`--order` fixes the starting order to exactly the known pair (step 5), the order truncated at the
victim has a single entry before it: the search has exactly **one** candidate to try, regardless
of policy. `original`, `ranked` and `random` (seeds 0-4) were all run for real, `--n 20
--budget-invocations 100` (stated budget: the Interface 6 B2 minimum for this case is `3×20 + 2 +
2 = 64`; 100 leaves headroom above it without being unlimited). All seven real runs gave the
identical verdict at the identical cost: `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`, reproduced
20/20, search tried 1 of 1 candidates, 64 of 100 invocations spent (reserve 60 + 2 reproduce + 2
search). `ranked` deepened through depths 2→5, found no evidence at any depth, and fell back to
the original order. Seven bundles committed under `eval/bundles/` (the real
`original`/`ranked`/`random×5` runs), all `python -m eval.bundle verify` clean.

**Correction, 2026-11-21 (M2's review of PR #152/#153, M3 verified for real):** the sentence
above originally said this "confirms end to end, with real JVM runs" that ranked finds no
saving on FJ-03. That overclaimed what steps 6-8 actually tested: `--order` fixes the run to the
known pair, so the search has exactly **one** candidate regardless of policy — a 1-candidate
search cannot demonstrate a *saving*, only that none of the three policies costs more than the
others (which they don't). It does not test the real, 524-candidate search a policy comparison
needs. **Checked for real, not just by reading the code**: running the *actual* package-scope
search (524 candidates, no `--order`, the natural discovered order plus all 31 ADR-008 shuffles,
`--n 20`, no budget limit) through the product's own CLI gives, for real, `UNRESOLVED
(NOT_REPRODUCED)` — 12,817 real invocations (reproduce 5,220 + shuffle 7,577 + alone 20), the
discovered order and every one of the 31 shuffles never fails, and the single-polluter search
phase (where policy would matter) **never runs** — "search tried 0 of 260 candidates". This is
not a budget-sizing problem: the search is architecturally gated on `reproduce`/`shuffle`
establishing a reference signature first, and neither does, for real, on this dense suite
(matching step 4's original finding, now reconfirmed end to end through the fixed CLI rather
than the workaround script). **So there is no way to run a live, 524-candidate ranked-vs-original
comparison on FJ-03** — not with `--order`, not with `--scope package` — regardless of budget.
The genuine source of "no evidence, no saving" on this case remains the offline comparison (item
5: `rank_candidates` position = original position, 368 of 524, no JVM runs needed). Bundled as
`eval/bundles/20261121T205558Z-...` ([[evidence-m3]]).

**Step 9 — not yet done.** The independent repeat (M1 or M2, on another machine) is the one
piece of steps 6-9 left. **Note for whoever runs it:** a repeat of the package-scope search
above (step 4's `NOT_REPRODUCED` reconfirmed through the real CLI) is a legitimate, different
check from repeating the trivial 1-candidate `--order` runs — but it will not produce a
ranked-vs-original comparison either, for the structural reason above. Worth doing for the
reconfirmation; not a substitute for the still-missing live comparison, which this case cannot
supply.

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

**Fetched and built for real 2026-11-19** (M3) — see Findings above. It builds and the premise
reproduces exactly as predicted; the blocker found is in our own discovery, not in fastjson.

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
