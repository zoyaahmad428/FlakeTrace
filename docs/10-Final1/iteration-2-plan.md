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
| **W16** | Qualify the claims we cannot yet support, everywhere they appear: CLI summary, `eval/outcome.py` rationale text, UI labels, READMEs, claims ledger. Pass-alone, "1-minimal", resource "mechanism", "never modified". *M2's part (`runner/`, `ui/`, its `04-Implementation` notes): built 2026-11-14 on `m2/w16-retire-claims`, awaiting verification by M3. M1's (`evidence/`) and M3's (`eval/`) parts not started* | Each in their own folder; M3 checks consistency | M3 | — | A search for the retired phrases (ADR-010 §2, ADR-011 §5, ADR-012 §1) finds none outside historical notes |
| **W17** ✅ | Agree ADR-010 and ADR-011 and the `RunTally` shape. ~~Draft schema v2~~ — moved into W19 with the other contract changes | M3 leads; M2, M1 | — | Supervisor's view on what `VERIFIED` means, if available | **Done 2026-11-13:** ADR-010 to ADR-014 accepted and ADR-015 accepted as a spike, three ticks each; Q1 option A, Q2 no retries, Q3 keep `VERIFIED` with its qualifier until the supervisor decides ([[06-Meetings/2026-11-13-post-mid-planning]]) |
| **W18** | Outcome categories and tallies in the runner: `repeat()`, `run_steps()`, `DiagnosisRuns`. *Built 2026-11-14 on `m2/w18-tallies`, awaiting verification by M1. Tallies sit beside the old count fields until W19 reads them; T1–T4 are green at the runner level, the verdicts need W19* | M2 | M1 | W17 | ADR-010 tests T1–T4 fail on `7cf453d` (output kept), then pass |
| **W19** | Decision table v2, schema v2, report assembly, a report for `INCONSISTENT`, fixture case N4, the seven reports regenerated. *Step 1 — `RunTally` and the classifier in `eval/baseline.py` — written by M2 while M3 has no laptop; M3 reviews (agreed 2026-11-13). Built 2026-11-14 on `m2/w19-runtally`, awaiting review by M3* | M3 (step 1: M2) | M1 (step 1: M3 reviews) | W17; with W18 | ADR-010 T1–T6 green; N4's ground truth written before its first run; the command never exits 3 |
| **W30** | Poster, to the handbook's specification | M1 leads; all supply content | M2 checks claims against the ledger | Poster date | Supervisor-approved; source file and JPEG submitted |
| **W31** | Supervisor meeting: decisions, dates, panel wording. Action register kept current | M2 compiles; all attend | — | — | Every row of [[10-Final1/supervisor-agenda]] has an answer or a date for one |
| **W29a** | Signatures on the report. Each member's own declarations. Reconcile GenAI levels | Each member; M3 the register | A different member checks consistency | — | FT013, FT014, FT015 evidence exists |

### Sprint B — auditable and budgeted · Sat 21 – Fri 27 November

| WP | Work | Owner | Verifier | Needs | Done when |
| --- | --- | --- | --- | --- | --- |
| **W20** | Deletion checks: runs and record lines (M2); acceptance rule and report fields (M3) | M2, M3 | M1 | W18, W19 | ADR-011 T1–T5; F3 shows two `NEEDED` checks |
| **W21** | All edges in the output, static-overlap wording, two controls: write-then-restore and unrelated overlap | M1 | M2 | W19 for the report fields | Neither control gets a causal label; the extra edges are visible in the report |
| **W22** | Environment fields in the record. Spike, then class-grouped execution with the lifecycle control. Reset boundary in the docs. Disposable-copy mode | M2 | M1 runs the control under Surefire and both harness modes | — | ADR-012 §3 table recorded by M1 on her machine |
| **W23** | Evidence bundle, `verify-bundle` recount, `replay`. Fixture bundles committed. One peer reproduction | M3 bundle and recount; M2 replay | **M1 on her own machine, alone** | W19, W20, W22 header fields | ADR-013 tests; M1's reproduction record in [[evidence-m1]], including what was unclear |
| **W24** | Budget ledger, verification reserve, `BUDGET_EXHAUSTED`, budget account in the report | M2; M3 the report fields | M3 | W18–W20 | ADR-014 evidence items 1–3 |
| **W26a** | Real case, steps 1–5 of the protocol: fetch, build, confirm the premise, fix the order, freeze | M3; M2 for runner problems | M2 | W22 lifecycle control, for step 2 | Protocol frozen and committed, or the case replaced with the reason recorded |
| **W29b** | Worksheet: clipped table recovered, editable file, stale status | M1 the table; chapter owners | M3 checks every page | — | FT016, FT017 evidence |

### Sprint C — the real case and the Final · Sat 28 November – Fri 4 December

| WP | Work | Owner | Verifier | Needs | Done when |
| --- | --- | --- | --- | --- | --- |
| **W25** | `rank_candidates` with a per-test cache (M1). `--policy`, candidate scope option (M2). Offline and live comparison tool (M3) | M1, M2, M3 | M3 measures; M2 reviews the ranking rule **before** it meets ground truth | W24 | ADR-014 evidence items 4–5; the rule's commit predates its first measured run |
| **W26b** | Real case, steps 6–9: `original`, `ranked`, `random` under one budget; independent repeat | M3 | M1 or M2 | W23, W24, W25, W26a | Bundles for every run, favourable or not; the yield table |
| **W27** | Pinned container image and one documented command | M3, M2 reviews *(see note)* | M1 runs it | W23 | A fixture diagnosis runs in the container on a second machine |
| **W28** | Report v2.0 | Chapter owners; M2 compiles | M3 checks status against code; M1 the abstract | W19–W26 results | [[10-Final1/report-v2-plan]] checklist |
| **W32** | One Java/Maven practitioner workflow check | M1; M2 supplies the case, M3 the acceptance task | M3 | A stable demo | A dated, consented record, or the blocker and an agreed substitute |
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
