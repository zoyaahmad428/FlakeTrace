# Iteration 2 — plan to the FYP-1 Final

*v1 · 2026-11-13 · Status: `AGREED` — work packages, owners and verifiers agreed by M1, M2 and M3
in person on 2026-11-13 ([[06-Meetings/2026-11-13-post-mid-planning]]; confirmed by approving
PR #101). **Dates stay estimates** until the cohort dates are confirmed.*

**Iteration objective.** By the FYP-1 Final, FlakeTrace diagnoses one **real** fastjson failure
and the fixture under a stated execution budget; every report states exactly what was established
and what was not; another member can verify and replay any report from its bundle; and evidence-
ranked search is compared with unranked search at the same endpoint.

**Order of priority** (the supervisor's, kept): truthful certification → auditable evidence →
budget and ranking → one real case. Paperwork with hard dates runs alongside.

> ⚠ **Dates are estimates.** The poster is probably due **16–20 November** and the Final probably
> falls **30 November – 4 December**, from the handbook's week numbers. Confirm both. If the Final
> is earlier than assumed, use the cut order at the end of this file.

---

## Work packages

Numbers continue from Iteration 1 (W1–W15). **Verifier** is the member who independently
reproduces the result — the supervisor's closure rule. The verifier never does the owner's work
for them.

### Sprint A — tell the truth · Sat 14 – Fri 20 November

| WP | Work | Owner | Verifier | Needs | Done when |
| --- | --- | --- | --- | --- | --- |
| **W16** ✅ | Qualify the claims we cannot yet support, everywhere they appear: CLI summary, `eval/outcome.py` rationale text, UI labels, READMEs, claims ledger. Pass-alone, "1-minimal", resource "mechanism", "never modified". *M2's part merged (`9a05788`, verified by M3 2026-11-18 — already correct). M1's part (`evidence/`, its `04-Implementation` note) merged 2026-11-18 (PR #105, `m1/w16-evidence-wording`). **M3's part done 2026-11-18**: `eval/`'s own rationale text already used only the approved phrasing; one inconsistency fixed for product-wide consistency. **Fully verified done 2026-11-20 (A2)**: repo-wide search for the retired phrases (1-minimal, never modified, sandboxed, found mechanism, root cause, caused by, explains the failure, passes alone) against `evidence/`, `eval/`, `runner/`, `ui/`, `docs/` now that M1's PR #105 has landed. Every hit is either the approved, correctly-qualified wording; a literature description of another tool's own property (not our claim); or inside a frozen historical record (`docs/08-MidEval/`, dated evidence-log entries) that correctly describes what was claimed at the time rather than being "corrected" retroactively — same closed-record principle as the Mid report chapters (2026-11-20 merge-resolution entry, `evidence-m3.md`). No violation found anywhere* | Each in their own folder; M3 checks consistency | M3 | — | A search for the retired phrases (ADR-010 §2, ADR-011 §5, ADR-012 §1) finds none outside historical notes |
| **W17** ✅ | Agree ADR-010 and ADR-011 and the `RunTally` shape. ~~Draft schema v2~~ — moved into W19 with the other contract changes | M3 leads; M2, M1 | — | Supervisor's view on what `VERIFIED` means, if available | **Done 2026-11-13:** ADR-010 to ADR-014 accepted and ADR-015 accepted as a spike, three ticks each; Q1 option A, Q2 no retries, Q3 keep `VERIFIED` with its qualifier until the supervisor decides ([[06-Meetings/2026-11-13-post-mid-planning]]) |
| **W18** ✅ | Outcome categories and tallies in the runner: `repeat()`, `run_steps()`, `DiagnosisRuns`. *Built 2026-11-14 (PR #104); **verified by M1 2026-11-20** (PR #108: tests pass after, fail on the pre-W18 code). The old count fields were removed on 2026-11-20 (A4, M3 agreed), so the tallies are the only counts; the verdicts came with W19* | M2 | M1 | W17 | ADR-010 tests T1–T4 fail on `7cf453d` (output kept), then pass |
| **W19** ✅ | Decision table v2, schema v2, report assembly, a report for `INCONSISTENT`, fixture case N4, the seven reports regenerated. *Step 1 (`RunTally`/classifier, M2, PR #103) reviewed by M3, matches ADR-010 exactly. **Built 2026-11-18**: `eval/outcome.py`/`eval/report.py` rewritten for the full 13-row table, `candidate_reasons`, `resource_edges`, `assurance`; fixture N4 added and confirmed `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)` through the real `diagnose` command (T5); F1–F4/N1–N3 regenerated under schema v2, verdicts unchanged (T6); eight real reports at `eval/reports/`. 119/119 `eval/tests`, 63/63 `runner/tests/test_cli` green. **Superseded in part 2026-11-19 (A1 fail-safe fix)**: row 12's `deletion_status=None` no longer satisfies S3 — F3's verdict is *not* unchanged after all; it now reports `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]`, the real, honest state until W20 builds F3's multi-test deletion check. F1/F2/F4 still verified unchanged (single kept polluter gets a free deletion check, ADR-011 §2). 120/120 `eval/tests` green. Awaiting M1's reproduction (T1–T5, below) and M2's `ui/web/` update (consequences section). 2026-11-20: M1 checked schema v2 against `report_fields`. Every field validates, and `ReportSchemaContractTest` now checks this in CI ([[evidence-m1]])* | M3 (step 1: M2) | M1 (step 1: M3 reviews) | W17; with W18 | ADR-010 T1–T6 green; N4's ground truth written before its first run; the command never exits 3 |
| **W30** | Poster, to the handbook's specification | M1 leads; all supply content | M2 checks claims against the ledger | Poster date | Supervisor-approved; source file and JPEG submitted |
| **W31** | Supervisor meeting: decisions, dates, panel wording. Action register kept current. *Agenda v2 and action register v2 prepared 2026-11-21 (M2): statuses moved only where built and reproduced; a new question on ranking for the real case (FJ-03 has no static edge). Meeting not yet held* | M2 compiles; all attend | — | — | Every row of [[10-Final1/supervisor-agenda]] has an answer or a date for one |
| **W29a** *(FT015 found and fixed)* | Signatures on the report. Each member's own declarations. Reconcile GenAI levels | Each member; M3 the register | A different member checks consistency | — | FT013, FT014, FT015 evidence exists |
*FT015's register half done 2026-11-21 (M3): the register and the frozen Mid report's own Table 9 already agreed for M3 (L2 x18, L1 x1) -- the real inconsistency was a single transcription error inside the *worksheet itself* (its summary table said "L3 (18 rows), L2 (1)" for M3, contradicting M3's own declaration a few pages later in the same document). Produced and validated a corrected, editable `.docx` (diff-confirmed as the only change) ([[evidence-m3]]). **Open:** FT013/FT014 (signatures, handing the corrected worksheet to the supervisor) -- each member's own, not M3's to do.*

### Sprint B — auditable and budgeted · Sat 21 – Fri 27 November

| WP | Work | Owner | Verifier | Needs | Done when |
| --- | --- | --- | --- | --- | --- |
| **W20** ✅ | Deletion checks: runs and record lines (M2); acceptance rule and report fields (M3). *Interface agreed 2026-11-20 (Interface 4, PR #119). Runner half built 2026-11-20 on `m2/w20-deletion-checks` (merged PR #121): `DiagnosisRuns.deletion_checks`, T1 (FT004 counterexample keeps only P), T2, T4 (F1: one `alone-check`, no extra runs); F3 gives two `NEEDED` checks at the runner level. T5 waits for the W24 budget. **Report half built 2026-11-20 (M3)**: `eval/report.py` reads `deletion_checks` (highest round only) for any polluter count, replacing A1's single-polluter-only fail-safe; schema bumped for the new field. **T3 confirmed for real**: F3's real repeated-removal check (40 JVM runs) gives both `setFlagA`/`setFlagB` `NEEDED`, 20/20 each -- F3 reaches `VERIFIED`, matching ground truth. **M1's independent reproduction done 2026-11-20** on her laptop at `0467ec2`: 25 scripted tests OK (T1, T2, T5); real F3 `VERIFIED`, both kept tests `NEEDED` 20/20 (T3); real F1 one `alone-check`, no deletion runs (T4) ([[evidence-m1]]). G2 for M2 and M3 to settle* | M2, M3 | M1 | W18, W19 | ADR-011 T1–T5; F3 shows two `NEEDED` checks |
| **W21** ✅ | All edges in the output, static-overlap wording, two controls: write-then-restore and unrelated overlap. *Part 1 (`resource_edges` from `report_fields`, test-first) and part 2 (the two controls, `evidence/tests/resources/ft005-controls/`) built 2026-11-18 on `m1/w16-evidence-wording`; **verified by M2 2026-11-20** (A2: 6 tests OK, failing before `5199ef8`, both controls run for real; one stale "not shown" line each in M1's and M2's code; both fixed 2026-11-20, M1's test-first ([[evidence-m1]])). Both controls end `VERIFIED (sequence)` with the resource labelled a static overlap, not the cause. The report shows the full `resource_edges` list only after W19 (schema v2); CI needs one compile line in `ci.yml` (M2)* | M1 | M2 | W19 for the report fields | Neither control gets a causal label; the extra edges are visible in the report |
| **W22** ✅ | Environment fields in the record. Spike, then class-grouped execution with the lifecycle control. Reset boundary in the docs. Disposable-copy mode. *Job 1 (environment fields) built 2026-11-14 on `m2/w22-record-env`; job 2 (spike) done — JUnit 4 class-grouped works, JUnit 3 stays per-method (ADR-012 §2); job 3 (`--lifecycle class-grouped`, lifecycle control) built 2026-11-14, awaiting M1's control run; job 4 (`--workspace copy`, the CLI default) built 2026-11-14. All four jobs built (PR #104); **verified by M1 2026-11-20** (PR #108: control table matches Surefire; disposable copy wrote no `target/`). Default lifecycle flipped to `class-grouped` on 2026-11-20* | M2 | M1 runs the control under Surefire and both harness modes | — | ADR-012 §3 table recorded by M1 on her machine |
| **W23** | Evidence bundle, `verify-bundle` recount, `replay`. Fixture bundles committed. One peer reproduction. *Interface 8 (bundle files, manifest, redaction, replay R1–R7) agreed by M1, M2, M3 2026-11-21; the runner writes and replays (M2), `eval.bundle verify` checks (M3). **M2's half built 2026-11-21** (`m2/w23-replay-code`): `--bundle`, `replay`; real F1 and F3 bundles replayed `same`, no personal path in any file ([[evidence-m2]]). **M3's half merged 2026-11-21 (PR #146)**: `eval.bundle verify` recounts against `runner.bundle.read_bundle`'s format, including `kind: "replay"`. Committed fixture bundles: M3's F1 and M2's F1 from a clean `main` (`tool.dirty false`; also the W32 case). `.gitattributes` (M2, 2026-11-21) keeps their bytes: before it, a Windows checkout gave CRLF and the checksums failed. **F2-F4/N1-N4 bundled 2026-11-21** ([[evidence-m3]]): all 9 committed bundles `verify` clean; found and fixed a real recount bug on N3 (shuffle lines wrongly folded into a reproduce-only tally). `eval/reports/*.json` not yet replaced. M1's reproduction next* | M3 bundle and recount; M2 replay | **M1 on her own machine, alone** | W19, W20, W22 header fields | ADR-013 tests; M1's reproduction record in [[evidence-m1]], including what was unclear |
| **W24** ✅ | Budget ledger, verification reserve, `BUDGET_EXHAUSTED`, budget account in the report. ***Interface 6 step 3 recorded 2026-11-21 (M2):** real F2 at the B2 minimum (70): `original` stops in search (`BUDGET_EXHAUSTED`, report with budget account), `ranked` reaches `VERIFIED` using exactly 70 (the reserve paid the full sequence check) ([[evidence-m2]]); M3's item-2 run at 72 in PR #139; M1's reproduction (step 4) pending. Interface agreed 2026-11-20 (Interface 6, [[contracts/interfaces]]: rules B1–B8, `BudgetAccount`, five points ADR-014 left open). **Runner half built 2026-11-20** (M2, `m2/w24-budget-ledger`): `runner/budget.py`, `BUDGET_EXHAUSTED`, `NOT_RUN` deletion checks, `--budget-invocations`/`--budget-seconds`; ADR-014's scripted tests and a real F2 run stopped at its limit ([[evidence-m2]]). **Report half built 2026-11-20** (M3, `m3/w24-report-budget`): `eval/outcome.py`'s `DecisionInput.verification_budget_exhausted` (CANDIDATE [BUDGET_EXHAUSTED], never VERIFIED, for a found polluter whose verification the budget cut short); `eval/report.py` now handles status `BUDGET_EXHAUSTED` (-> `UNRESOLVED(BUDGET_EXHAUSTED)`, same reference-may-be-null shape as `NOT_REPRODUCED`) and emits the optional `budget` field; schema bumped (`eval/schema/report.schema.json`'s `budgetAccount`, `candidates` nested as `{total, tried}`). Test-first, 7 new tests, 136/136 OK ([[evidence-m3]]). **Merged into `main` 2026-11-20 (PR #135)**, both merge conflicts with M1's/M2's newer PRs resolved; the one blocking `runner` CI failure was M2's own stale W24 placeholder test, fixed with his agreement. **ADR-014 evidence item 2 confirmed for real, both halves together, 2026-11-20**: real F2 (`--budget-invocations 72`, 2 above B2's minimum of 70) now gives `UNRESOLVED(BUDGET_EXHAUSTED)` with exit 0 and a real, schema-valid `budget` field -- M2's own earlier run at the same scenario (limit 70, before this PR merged) got exit 3 and no report. The no-limit comparison run matches M2's earlier numbers exactly (spent 82, search tried 7 of 7) ([[evidence-m3]]). Items 1/3 of that table are M2's, already covered by his own runs. **M1's independent reproduction done 2026-11-20** (Interface 6 step 4) on her laptop at `9a6392f`: limit 69 refused (exit 2, minimum 70); limit 70 `UNRESOLVED (BUDGET_EXHAUSTED)`, exit 0, spent 30 of 70, 1 of 7 candidates tried; no limit `VERIFIED`, 82 ([[evidence-m1]])* | M2; M3 the report fields | M3 | W18–W20 | ADR-014 evidence items 1–3 |
| **W26a** ✅ | Real case, steps 1–5 of the protocol: fetch, build, confirm the premise, fix the order, freeze. *Done 2026-11-19 (M3), with a real runner problem found for M2: fastjson FJ-03 fetched and built for real (real JDK 8, portable Temurin download, no Docker needed); premise confirmed 10/10 both ways through the real runner. `runner/discovery.py` cannot discover or validate the known polluter (custom Surefire `**/bvt/**/*.java` includes, not the hardcoded default pattern) — the real CLI refuses the case outright; flagged for M2 ([[00-Meta/risk-register]]). The 31-shuffle search also cannot reproduce the bug on this dense real suite (other tests undo the pollution) — a genuine result, not a defect; real-world motivation for W25. Protocol frozen at `FROZEN FOR STEPS 1-5` with the known pair as the starting order ([[05-Testing/real-case-protocol]]). **Steps 6-9 blocked on M2's discovery.py fix*** *Discovery gap fixed by M2 2026-11-20 (A1, PR #110): steps 6–9 unblocked. **Premise verified by M2 2026-11-20** (A3): Temurin 8u502, fastjson `e05e9c5`, build 172 + 2,496 sources; alone 10/10 pass, after the polluter 10/10 `AssertionFailedError` at `MaxBufSizeTest.test_max_buf:20`; the real CLI now accepts the frozen order: polluter found, 20/20, `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`. Two runner quirks found and fixed* | M3; M2 for runner problems | M2 | W22 lifecycle control, for step 2 | Protocol frozen and committed, or the case replaced with the reason recorded |
| **W29b** | Worksheet: clipped table recovered, editable file, stale status | M1 the table; chapter owners | M3 checks every page | — | FT016, FT017 evidence |

### Sprint C — the real case and the Final · Sat 28 November – Fri 4 December

| WP | Work | Owner | Verifier | Needs | Done when |
| --- | --- | --- | --- | --- | --- |
| **W25** | `rank_candidates` with a per-test cache (M1). `--policy`, candidate scope option (M2). Offline and live comparison tool (M3). ***Interface 7 (search policy: `--policy`, `--scope`, P1–P6, ADR-014 §6 deepening) agreed by M1, M2, M3 2026-11-20. M2's runner half built 2026-11-20** (`m2/w25-policy-code`): `runner/policy.py`, `--policy`, `--scope package`, deepening; real F1–F4 ranked give the same verdicts ([[evidence-m2]]); measurement is M3's. M1's part 1 built 2026-11-20 on `m1/w25-rank-rule`: the rule (most shared resources, then shallowest edge, then original position) and `AnalysisCache`, test-first on M1's own classes only. No fixture or real case has been ranked. Merged 2026-11-20 (PR #112). **M2 reviewed the rule 2026-11-20, before any measurement**: no deepening inside ranking, an unanalysable victim raises and the runner falls back to the original order, and the cache is enough for the ledger. Interface 5 in [[contracts/interfaces]] proposed by M1 at M2's request ([[evidence-m1]]). M2's runner half merged (PR #136); **M1 reviewed `EvidenceRanker` against Interfaces 2, 5 and 7 on 2026-11-20 (Interface 7 step 3): conforms**; Interface 5 now names `AnalysisCache.get` ([[evidence-m1]]). **Note for M3's measurement, recorded 2026-11-21**: on FJ-03, `ranked` keeps the original order by design -- the pollution is a JDK `ThreadLocal.set()` call static analysis does not follow, so there is no edge to rank by (M1, PR #145, [[evidence-m1]]). Report it that way in the W26b measurement -- "ranked = original, no edge found" -- not as a ranking result or a ranking defect. **M3's measurement done 2026-11-21 ([[evidence-m3]]): both ADR-014 evidence items 4 and 5.** Item 5 (offline): real fastjson built at the pinned commit, the real `rank_candidates` run against all 524 real FJ-03 candidates (static analysis only, no JVM test runs) -- confirms M1's finding independently: zero evidence found, ranked position equals original position (368 of 524) exactly. Item 4 (fixture, real invocations, both policies, no limit): F1 67→65, F2 82→70 (independently matches M2's own real run), F3 264→264 (zero saving -- `ddmin` dominates its cost, not the search order), F4 166→146; same verdict every time, `ranked` never costs more. **Not yet done**: item 4's real-case half (FJ-03 under both policies with real JVM runs) -- W26b's work, not blocked on anything technical now* | M1, M2, M3 | M3 measures; M2 reviews the ranking rule **before** it meets ground truth | W24 | ADR-014 evidence items 4–5; the rule's commit predates its first measured run |
| **W26b** ✅ *(steps 6-8)* | Real case, steps 6–9: `original`, `ranked`, `random` under one budget; independent repeat | M3 | M1 or M2 | W23, W24, W25, W26a | Bundles for every run, favourable or not; the yield table |
*Steps 6-8 run for real 2026-11-21 (M3): discovery.py's gap fixed by M2 2026-11-20 unblocked this. `--order` fixes the frozen known pair as the starting order (step 5), so truncated at the victim there is exactly 1 candidate before it -- policy cannot matter. `--n 20 --budget-invocations 100` (B2 minimum is 64). All seven real runs (`original`, `ranked`, `random` seeds 0-4) gave the identical verdict, `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`, at the identical cost, 64 of 100 -- showing the three policies cost the same on this case (a 1-candidate search cannot demonstrate a saving). **Corrected 2026-11-21 after M2's review (PR #152/#153)**: checked for real whether the actual 524-candidate package-scope search can run -- it cannot, structurally, not for a budget reason: `UNRESOLVED (NOT_REPRODUCED)` in 12,817 real invocations through the product's own CLI, search tried 0 of 260 candidates, because `reproduce`/`shuffle` never establish a reference on this dense real suite (reconfirms step 4's finding end to end through the fixed CLI). FJ-03 cannot supply a live ranked-vs-original comparison at all; the offline comparison (item 5, 368 of 524 both orders) remains the real source of "no evidence, no saving" on this case. 8 bundles committed under `eval/bundles/` (7 original + the new package-scope result), all `eval.bundle verify` clean ([[05-Testing/real-case-protocol]], [[evidence-m3]]). **Step 9 (independent repeat, M1 or M2) is the one piece left** -- a repeat of the package-scope run is legitimate but will not produce a ranking comparison either, for the same structural reason.*
| **W27** *(built; M1's second-machine run pending)* | Pinned container image and one documented command | M3, M2 reviews *(see note)* | M1 runs it | W23 | A fixture diagnosis runs in the container on a second machine |
*Built and run for real 2026-11-21 (M3): `Dockerfile` at the repo root pins `maven:3.9.9-eclipse-temurin-8` + Python; scoped to reproducibility, not the full hardened sandbox profile in `docs/02-Requirements/non-functional.md` (a later target, noted as such). Real F1 fixture diagnosis run entirely inside the built image matches ground truth exactly (`VERIFIED (sequence)`, 67 invocations); bundle `verify` clean; the bundle's own recorded environment (different Linux kernel, different JDK 8 patch than this host) confirms it ran somewhere genuinely independent. One documented command in `README.md` and `CLAUDE.md` §8 (with the Windows/Git-Bash volume-mount caveat found while testing it). **Not done: M1 (or M2) actually running it on a second machine** -- that is what "done when" asks for and this session cannot supply ([[evidence-m3]]).*
| **W28** | Report v2.0 | Chapter owners; M2 compiles | M3 checks status against code; M1 the abstract | W19–W26 results | [[10-Final1/report-v2-plan]] checklist |
| **W32** | One Java/Maven practitioner workflow check. *Protocol, consent text and record template drafted by M1 2026-11-20 ([[10-Final1/practitioner-check]]); no participant contacted yet; the case (M2) supplied 2026-11-21 as the F1 bundle `eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/` (M2's own "The case" section of the protocol still needs writing up). **The acceptance task (M3) supplied 2026-11-21**: 3 written questions against the real F1 report, fixed pass criteria (Q2 -- "does this prove cause?" -- fails the whole task if wrong, regardless of Q1/Q3), a named FJ-03 variant if M2's case changes* | M1; M2 supplies the case, M3 the acceptance task | M3 | A stable demo | A dated, consented record, or the blocker and an agreed substitute |
| **W33** | Tag `final1-v1`. Deck. Demo rehearsed on the demo machine. Each member rehearses their own viva | M2 the tag; all | Each rehearses with another member asking | Everything above | [[10-Final1/demo-plan]] steps marked rehearsed; [[10-Final1/ownership-prep]] tasks done without AI |
| **W35** | Pair mode (ADR-016, revised): `--search pairs` diagnoses a known victim from `[candidate, victim]` pairs when no order makes it fail; order mode's `NOT_REPRODUCED` names it as the next step; `reproduced_by` in the report. *ADR-016 revised 2026-11-22 (its first, automatic version was over-built); revision and Interface 9 await M1's and M3's agreement. A real case that fails in a recorded failing order (order mode on real code) is next iteration* | M2 (runner); M3 (report field, measurement) | M1 reproduces the FJ-03 pair-mode diagnosis | W24, W25, ADR-016 | ADR-016's evidence items 1–4: FJ-03 diagnosed from the victim alone with a bundle; the live `original`/`ranked`/`random` comparison on FJ-03; a one-off pair failure not adopted; order-mode cases unchanged |
| **W34** | *Stretch:* resource intervention spike (ADR-015) | M1, M2 | M3 | W16–W26 on track | Go / no-go written up |

**Note on W27.** Container security is Member 2's by the defended ownership map and stays so. W27
is a reproducibility image, which fits Member 3's "one-command reproducibility bundle" and takes
load off the member the supervisor identified as the integration bottleneck. If the team prefers
Member 2 to keep it, change this row — and record the choice either way, because the handbook
asks for ownership changes to be recorded when they happen. **Recorded 2026-11-13: the team agreed
that Member 3 owns W27** ([[06-Meetings/2026-11-13-post-mid-planning]]).

## The critical path

```
W17 agree contract ─► W18 + W19 tallies, decision ─► W20 deletion ─► W23 bundle ─┐
                                              └────► W24 budget ─► W25 ranking ──┼─► W26b real case ─► W28 report
W22 lifecycle control ─► W26a real case builds, order frozen ────────────────────┘
```

**W17 is one meeting and almost every later package waits on it. Hold it first.**
**W26a starts in Sprint B regardless** — whether fastjson still builds is the largest unknown in
the plan, and it needs nothing new.

## Who carries what

| Member | Owns | Verifies |
| --- | --- | --- |
| **M1 — Zoya** | W21, W25 (ranking), W30, W32, W29b (table) | W18, W19, W20, W22 control, **W23 reproduction**, W27 |
| **M2 — Raffay** | W18, W19 step 1 (`RunTally`, for M3), W20 (runs), W22, W24, W25 (integration), W23 (replay), W31, W33 (tag), W28 (compile) | W21, W26a, W30 (claims) |
| **M3 — Zarpash** | W17 (lead), W19, W20 (rule), W23, W26, W27, W29a (register), W25 (measurement) | W16, W24, W28, W29b, W32 |

Member 1 is the reproduction backup and Member 3 the report and schema backup, as the supervisor
proposed (FT020).

## Rules for this iteration

1. **Test first for every defect.** The failing run on `7cf453d` is recorded before the fix.
2. **A correction names its commit.** The Mid baseline (`mid-eval-v1`) is never moved.
3. **Contract changes land together.** ADR-010, 011, 013 and 014 all touch the schema; Member 3
   makes one schema v2, not four.
4. **The ranking rule is committed before it meets ground truth.**
5. **Every real-project run is kept**, including builds that fail.
6. Everything in root `CLAUDE.md` — members commit, no invented results, each member can explain
   their own work without AI.

## Cut order, if the Final is earlier or work slips

Cut from the top. Record each cut in the variance table and tell the supervisor **before** the
Final, not at it.

| # | Cut | What is said instead |
| --- | --- | --- |
| 1 | W34 intervention spike | Static overlap remains the stated resource evidence |
| 2 | W27 container | Versions are pinned in the bundle; container is the first FYP-2 task |
| 3 | W22's disposable-copy mode | Reset boundary documented; the lifecycle control and fix stay |
| 4 | W26b second case and second project | One real case |
| 5 | W25 live ranked runs | The offline comparison on stored scan tables is kept — it needs no JVM |
| 6 | W32 practitioner check | Blocker recorded, substitute agreed with the supervisor |

**Never cut:** W16–W19 (a truthful report), W20, W23 (an auditable one), W24 (a budget that
stops), W26a plus one real whole-pipeline run, W28–W31 and W33.

## Variance and recovery

| Variance | Cause | Recovery | Owner | Revised date |
| --- | --- | --- | --- | --- |
| No commits on `main` from 15 October to 13 November | *To be filled in by the team.* The committee's feedback reached us on 13 November | This plan; W17 within two days | All | 15 Nov |
| Review proposed by the supervisor for 23 October: no record in the repository of whether it was held | — | Ask at the next meeting; record the answer | M2 | Next meeting |
| *add as they occur* | | | | |

## After the Final — first FYP-2 increments, in proposed order

1. Brittle tests and state-setters, if the supervisor agrees
   ([[05-Testing/real-case-protocol]])
2. Resource intervention check, if the spike says go
3. The adaptive cost-aware policy and its two ablations
4. Filesystem resource family
5. Published comparators (iFixFlakies, RankF) on the overlapping cases; the held-out run
6. Container hardening and the clean-machine install
