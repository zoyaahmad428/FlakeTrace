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
| **W18** | Outcome categories and tallies in the runner: `repeat()`, `run_steps()`, `DiagnosisRuns`. *Built 2026-11-14 on `m2/w18-tallies`, awaiting verification by M1. Tallies sit beside the old count fields until W19 reads them; T1–T4 are green at the runner level, the verdicts need W19* | M2 | M1 | W17 | ADR-010 tests T1–T4 fail on `7cf453d` (output kept), then pass |
| **W19** | Decision table v2, schema v2, report assembly, a report for `INCONSISTENT`, fixture case N4, the seven reports regenerated. *Step 1 (`RunTally`/classifier, M2, PR #103) reviewed by M3, matches ADR-010 exactly. **Built 2026-11-18**: `eval/outcome.py`/`eval/report.py` rewritten for the full 13-row table, `candidate_reasons`, `resource_edges`, `assurance`; fixture N4 added and confirmed `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)` through the real `diagnose` command (T5); F1–F4/N1–N3 regenerated under schema v2, verdicts unchanged (T6); eight real reports at `eval/reports/`. 119/119 `eval/tests`, 63/63 `runner/tests/test_cli` green. M1's reproduction done 2026-11-20 on her laptop at `03c9b30`: eval tests 122 OK, T1–T4 OK, N4 `UNRESOLVED (VICTIM_FAILS_ALONE_DIFFERENTLY)` exit 0, F1 unchanged ([[evidence-m1]]). Awaiting M2's `ui/web/` update (consequences section). 2026-11-20: M1 checked schema v2 against `report_fields`. Every field validates, and `ReportSchemaContractTest` now checks this in CI ([[evidence-m1]])* | M3 (step 1: M2) | M1 (step 1: M3 reviews) | W17; with W18 | ADR-010 T1–T6 green; N4's ground truth written before its first run; the command never exits 3 |
| **W18** | Outcome categories and tallies in the runner: `repeat()`, `run_steps()`, `DiagnosisRuns`. *Built 2026-11-14 (PR #104); **verified by M1 2026-11-20** (PR #108: tests pass after, fail on the pre-W18 code). The old count fields were removed on 2026-11-20 (A4, M3 agreed), so the tallies are the only counts; the verdicts came with W19* | M2 | M1 | W17 | ADR-010 tests T1–T4 fail on `7cf453d` (output kept), then pass |
| **W19** | Decision table v2, schema v2, report assembly, a report for `INCONSISTENT`, fixture case N4, the seven reports regenerated. *Step 1 (`RunTally`/classifier, M2, PR #103) reviewed by M3, matches ADR-010 exactly. **Built 2026-11-18**: `eval/outcome.py`/`eval/report.py` rewritten for the full 13-row table, `candidate_reasons`, `resource_edges`, `assurance`; fixture N4 added and confirmed `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)` through the real `diagnose` command (T5); F1–F4/N1–N3 regenerated under schema v2, verdicts unchanged (T6); eight real reports at `eval/reports/`. 119/119 `eval/tests`, 63/63 `runner/tests/test_cli` green. **Superseded in part 2026-11-19 (A1 fail-safe fix)**: row 12's `deletion_status=None` no longer satisfies S3 — F3's verdict is *not* unchanged after all; it now reports `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]`, the real, honest state until W20 builds F3's multi-test deletion check. F1/F2/F4 still verified unchanged (single kept polluter gets a free deletion check, ADR-011 §2). 120/120 `eval/tests` green. Awaiting M1's reproduction (T1–T5, below) and M2's `ui/web/` update (consequences section). 2026-11-20: M1 checked schema v2 against `report_fields`. Every field validates, and `ReportSchemaContractTest` now checks this in CI ([[evidence-m1]])* | M3 (step 1: M2) | M1 (step 1: M3 reviews) | W17; with W18 | ADR-010 T1–T6 green; N4's ground truth written before its first run; the command never exits 3 |
| **W30** | Poster, to the handbook's specification | M1 leads; all supply content | M2 checks claims against the ledger | Poster date | Supervisor-approved; source file and JPEG submitted |
| **W31** | Supervisor meeting: decisions, dates, panel wording. Action register kept current | M2 compiles; all attend | — | — | Every row of [[10-Final1/supervisor-agenda]] has an answer or a date for one |
| **W29a** | Signatures on the report. Each member's own declarations. Reconcile GenAI levels | Each member; M3 the register | A different member checks consistency | — | FT013, FT014, FT015 evidence exists |

### Sprint B — auditable and budgeted · Sat 21 – Fri 27 November

| WP | Work | Owner | Verifier | Needs | Done when |
| --- | --- | --- | --- | --- | --- |
| **W20** | Deletion checks: runs and record lines (M2); acceptance rule and report fields (M3). *Interface agreed 2026-11-20 (Interface 4, PR #119). Runner half built 2026-11-20 on `m2/w20-deletion-checks` (merged PR #121): `DiagnosisRuns.deletion_checks`, T1 (FT004 counterexample keeps only P), T2, T4 (F1: one `alone-check`, no extra runs); F3 gives two `NEEDED` checks at the runner level. T5 waits for the W24 budget. **Report half built 2026-11-20 (M3)**: `eval/report.py` reads `deletion_checks` (highest round only) for any polluter count, replacing A1's single-polluter-only fail-safe; schema bumped for the new field. **T3 confirmed for real**: F3's real repeated-removal check (40 JVM runs) gives both `setFlagA`/`setFlagB` `NEEDED`, 20/20 each -- F3 reaches `VERIFIED`, matching ground truth. Awaiting M1's independent reproduction of T3 (Interface 4's own step 4) before G2 (claims-ledger) can close* | M2, M3 | M1 | W18, W19 | ADR-011 T1–T5; F3 shows two `NEEDED` checks |
| **W21** | All edges in the output, static-overlap wording, two controls: write-then-restore and unrelated overlap. *Part 1 (`resource_edges` from `report_fields`, test-first) and part 2 (the two controls, `evidence/tests/resources/ft005-controls/`) built 2026-11-18 on `m1/w16-evidence-wording`; **verified by M2 2026-11-20** (A2: 6 tests OK, failing before `5199ef8`, both controls run for real; one stale "not shown" line each in M1's and M2's code; both fixed 2026-11-20, M1's test-first ([[evidence-m1]])). Both controls end `VERIFIED (sequence)` with the resource labelled a static overlap, not the cause. The report shows the full `resource_edges` list only after W19 (schema v2); CI needs one compile line in `ci.yml` (M2)* | M1 | M2 | W19 for the report fields | Neither control gets a causal label; the extra edges are visible in the report |
| **W22** | Environment fields in the record. Spike, then class-grouped execution with the lifecycle control. Reset boundary in the docs. Disposable-copy mode. *Job 1 (environment fields) built 2026-11-14 on `m2/w22-record-env`; job 2 (spike) done — JUnit 4 class-grouped works, JUnit 3 stays per-method (ADR-012 §2); job 3 (`--lifecycle class-grouped`, lifecycle control) built 2026-11-14, awaiting M1's control run; job 4 (`--workspace copy`, the CLI default) built 2026-11-14. All four jobs built (PR #104); **verified by M1 2026-11-20** (PR #108: control table matches Surefire; disposable copy wrote no `target/`). Default lifecycle flipped to `class-grouped` on 2026-11-20* | M2 | M1 runs the control under Surefire and both harness modes | — | ADR-012 §3 table recorded by M1 on her machine |
| **W23** | Evidence bundle, `verify-bundle` recount, `replay`. Fixture bundles committed. One peer reproduction | M3 bundle and recount; M2 replay | **M1 on her own machine, alone** | W19, W20, W22 header fields | ADR-013 tests; M1's reproduction record in [[evidence-m1]], including what was unclear |
| **W24** | Budget ledger, verification reserve, `BUDGET_EXHAUSTED`, budget account in the report. *Interface agreed 2026-11-20 (Interface 6, [[contracts/interfaces]]: rules B1–B8, `BudgetAccount`, five points ADR-014 left open). **Runner half built 2026-11-20** (M2, `m2/w24-budget-ledger`): `runner/budget.py`, `BUDGET_EXHAUSTED`, `NOT_RUN` deletion checks, `--budget-invocations`/`--budget-seconds`; ADR-014's scripted tests and a real F2 run stopped at its limit ([[evidence-m2]]). Report half: M3* | M2; M3 the report fields | M3 | W18–W20 | ADR-014 evidence items 1–3 |
| **W26a** | Real case, steps 1–5 of the protocol: fetch, build, confirm the premise, fix the order, freeze. *Done 2026-11-19 (M3), with a real runner problem found for M2: fastjson FJ-03 fetched and built for real (real JDK 8, portable Temurin download, no Docker needed); premise confirmed 10/10 both ways through the real runner. `runner/discovery.py` cannot discover or validate the known polluter (custom Surefire `**/bvt/**/*.java` includes, not the hardcoded default pattern) — the real CLI refuses the case outright; flagged for M2 ([[00-Meta/risk-register]]). The 31-shuffle search also cannot reproduce the bug on this dense real suite (other tests undo the pollution) — a genuine result, not a defect; real-world motivation for W25. Protocol frozen at `FROZEN FOR STEPS 1-5` with the known pair as the starting order ([[05-Testing/real-case-protocol]]). **Steps 6-9 blocked on M2's discovery.py fix*** *Discovery gap fixed by M2 2026-11-20 (A1, PR #110): steps 6–9 unblocked. **Premise verified by M2 2026-11-20** (A3): Temurin 8u502, fastjson `e05e9c5`, build 172 + 2,496 sources; alone 10/10 pass, after the polluter 10/10 `AssertionFailedError` at `MaxBufSizeTest.test_max_buf:20`; the real CLI now accepts the frozen order: polluter found, 20/20, `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`. Two runner quirks found and fixed* | M3; M2 for runner problems | M2 | W22 lifecycle control, for step 2 | Protocol frozen and committed, or the case replaced with the reason recorded |
| **W29b** | Worksheet: clipped table recovered, editable file, stale status | M1 the table; chapter owners | M3 checks every page | — | FT016, FT017 evidence |

### Sprint C — the real case and the Final · Sat 28 November – Fri 4 December

| WP | Work | Owner | Verifier | Needs | Done when |
| --- | --- | --- | --- | --- | --- |
| **W25** | `rank_candidates` with a per-test cache (M1). `--policy`, candidate scope option (M2). Offline and live comparison tool (M3). ***Interface 7 (search policy: `--policy`, `--scope`, P1–P6, ADR-014 §6 deepening) agreed by M1, M2, M3 2026-11-20. M2's runner half built 2026-11-20** (`m2/w25-policy-code`): `runner/policy.py`, `--policy`, `--scope package`, deepening; real F1–F4 ranked give the same verdicts ([[evidence-m2]]); measurement is M3's. M1's part 1 built 2026-11-20 on `m1/w25-rank-rule`: the rule (most shared resources, then shallowest edge, then original position) and `AnalysisCache`, test-first on M1's own classes only. No fixture or real case has been ranked. Merged 2026-11-20 (PR #112). **M2 reviewed the rule 2026-11-20, before any measurement**: no deepening inside ranking, an unanalysable victim raises and the runner falls back to the original order, and the cache is enough for the ledger. Interface 5 in [[contracts/interfaces]] proposed by M1 at M2's request ([[evidence-m1]])* | M1, M2, M3 | M3 measures; M2 reviews the ranking rule **before** it meets ground truth | W24 | ADR-014 evidence items 4–5; the rule's commit predates its first measured run |
| **W26b** | Real case, steps 6–9: `original`, `ranked`, `random` under one budget; independent repeat | M3 | M1 or M2 | W23, W24, W25, W26a | Bundles for every run, favourable or not; the yield table |
| **W27** | Pinned container image and one documented command | M3, M2 reviews *(see note)* | M1 runs it | W23 | A fixture diagnosis runs in the container on a second machine |
| **W28** | Report v2.0 | Chapter owners; M2 compiles | M3 checks status against code; M1 the abstract | W19–W26 results | [[10-Final1/report-v2-plan]] checklist |
| **W32** | One Java/Maven practitioner workflow check. *Protocol, consent text and record template drafted by M1 2026-11-20 ([[10-Final1/practitioner-check]]); no participant contacted yet; the case (M2) and the acceptance task (M3) still to be supplied* | M1; M2 supplies the case, M3 the acceptance task | M3 | A stable demo | A dated, consented record, or the blocker and an agreed substitute |
| **W33** | Tag `final1-v1`. Deck. Demo rehearsed on the demo machine. Each member rehearses their own viva | M2 the tag; all | Each rehearses with another member asking | Everything above | [[10-Final1/demo-plan]] steps marked rehearsed; [[10-Final1/ownership-prep]] tasks done without AI |
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
