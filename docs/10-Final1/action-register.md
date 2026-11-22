# Carried action register — handbook Form 10

*v2 · 2026-11-21 · Status: live register. Updated before every evaluation. v2 (M2, W31): statuses moved only
where the work is built **and** reproduced by another member; none is `Done` — that needs the supervisor's
acceptance (the feedback register's rule).*

The handbook's rule for this form: *"Students update it before every evaluation. Panel only checks
status and evidence link, not long explanations."* Later forms score **whether this register was
addressed with evidence**: 10 marks on Form 4.

Long explanations live in [[10-Final1/feedback-register]]. The register submitted at the Mid is
kept unchanged as a record in [[08-MidEval/panel-action-register]].

**Status:** `Open` · `Partly` · `Done` · `Rejected` (with reason) — the handbook's four values.
**Panel status** (`Accepted` / `Carry forward`) is filled in by the panel or supervisor, never by us.

> **Why most proposal actions moved from "Complete" back to "Partly".** At the Mid we marked A1–A9
> complete. The supervisor's review found that the work behind them is real but that closure had
> been claimed too early: certification gaps, missing portable evidence and unconfirmed approval
> still affect them. The supervisor's reassessment is the status shown here.

---

## Raised at the proposal defence

A1–A6 are the panel's own questions, as we transcribed them. The original result sheet with exact
wording and due dates has not been supplied to us; we have asked for it
([[10-Final1/supervisor-agenda]]). A7–A10 come from the supervisor's post-defence plan.

| ID | Raised at | Required action | Owner | Due by | Status | Evidence | Panel status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Proposal | Detect without application logs | M2 | Final | Partly | No fixture test logs anything; verdicts come from order, outcomes and bytecode. Portable record built: evidence bundles (W23, PRs #143, #146, #147), committed F1 bundle verified by M3's recount. **Open:** M1's independent reproduction (FT009) | |
| A2 | Proposal | Say whether trace instructions are injected | M1 | Final | Partly | No: `javap` on compiled classes, ADR-001. **Open:** explain the approved runtime fallback, and label static evidence as potential overlap (FT005) | |
| A3 | Proposal | Say whether code is modified | M2 | Final | Partly | Project files hashed before and after, `runner/integrity.py`. Limits stated (ADR-012 §1) and now measured by the reset control (FT021, 2026-11-21). **Open:** M3's check; the supervisor accepting "trusted projects only" until the hardened container (FYP-2) | |
| A4 | Proposal | Explain how the code block is isolated | M2, M1 | Final | Partly | Sequence reduction and resource localisation both exist. **Open:** pass-alone defect (FT003), unverified deletions (FT004), overlap is not cause (FT005) | |
| A5 | Proposal | Show diverse applicable scenarios | M3 | Final | Partly | Seven fixture cases end to end. **Open:** scope confirmation and one real project (FT008) | |
| A6 | Proposal | More research to improve the solution | M1 | Final | Partly | Minimisation note, ADR research sections. **Open:** each member explains the nearest baseline; a measured comparison plan (FT008) | |
| A7 | Supervisor plan | Record the execution environment of every run | M2 | Final | Partly | Every record now also holds the tool commit, Maven, Python, JUnit, JVM timezone, locale and encoding, lifecycle and workspace (W22, PR #104, reproduced by M1 #108); every bundle states the reset assumptions (ADR-012) and checksums (W23). **Open:** the reproduced bundle (FT009) | |
| A8 | Supervisor plan | Reproduction confidence with uncertainty | M3 | Final | Partly | Wilson intervals on real counts. **Open:** the acceptance logic around them (FT003, FT004) | |
| A9 | Supervisor plan | Evidence report | M3, all | Final | Partly | Schema-validated reports; a report for every status, including `INCONSISTENT` (W19) and `BUDGET_EXHAUSTED` (W24); bundles, `verify` and `replay` (W23). **Open:** M1's bundle reproduction (FT009) | |
| A10 | Supervisor plan | Bounded resource decision | Supervisor, all | Next meeting | Open | Our position: static fields and system properties now, filesystem committed for FYP-2, the rest reported as unsupported ([[07-Defense/decisions/resource-family-boundaries]]). **Needs the supervisor's recorded decision** | |

## Raised at the Mid Evaluation

M-1 to M-5 are the FYP Committee's official comments. The rest are the supervisor's findings,
grouped; each keeps its FT identifier.

| ID | Raised at | Required action | Owner | Due by | Status | Evidence | Panel status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M-1 | Mid, official | Correct verification defects | M2, M3, M1 | Final | Partly | Both defects fixed and reproduced by another member: FT003 (W18/W19) and FT004 (W20), see their rows. Awaiting supervisor acceptance | |
| M-2 | Mid, official | Complete budget-aware planning | M2, M1, M3 | Final | Partly | Budget ledger with a verification reserve (W24, PR #132/#135; claim G8 settled, reproduced by M1 #144) and ranked search (W25, PR #136). **Open:** the measured ranked-vs-original comparison (FT007, ADR-014 items 4–5) | |
| M-3 | Mid, official | Real-project validation | M3, M2, M1 | Final | Partly | fastjson FJ-03 built and its premise confirmed 10/10 both ways (W26a, M3; reproduced by M2); the real command accepts the case. **Open:** the whole-pipeline runs under one budget (W26b) | |
| M-4 | Mid, official | Restore the missing abstract | M2, all | Report v2.0 | Open | Our source and the submitted PDF contain a 188-word abstract; meaning of "missing" to be confirmed | |
| M-5 | Mid, official | Align the report with the template | M2, all | Report v2.0 | Open | [[10-Final1/report-v2-plan]] | |
| FT003 | Mid | No `VERIFIED` when the victim fails alone differently | M2, M3 | Sprint A | Partly | Fixed in W18 (`e49fa13`) and W19 (PR #106); reproduced by M1 2026-11-20: T1–T4 OK, N4 `UNRESOLVED (VICTIM_FAILS_ALONE_DIFFERENTLY)` ([[evidence-m1]]). Awaiting supervisor acceptance | |
| FT004 | Mid | Deletion evidence under repetition | M2, M3 | Sprint B | Partly | W20 (M2 PR #121, M3 PRs #129, #130); reproduced by M1 2026-11-20: ADR-011 T1–T5, real F3 both kept tests `NEEDED` 20/20 ([[evidence-m1]]). Awaiting supervisor acceptance | |
| FT005 | Mid | Separate sequence assurance from resource evidence | M1, M3 | Wording: Sprint A · controls: Sprint B | Partly | W16 + W21 (M1, PRs #105, #107) with schema v2 (M3, W19); **reproduced by M2 2026-11-20** ([[evidence-m2]]): both controls `VERIFIED (sequence)`, resource `STATIC_OVERLAP`, mechanism `NOT_ASSESSED`, no causal wording; control 2's report lists both edges in `resource_edges`. Two "not shown in this report" lines that became false once `resource_edges` showed every edge are both fixed: M2's (A2, PR #122) and M1's, test-first (PR #125, [[evidence-m1]]). Evidence for "Closes when" complete; **awaiting supervisor acceptance** | |
| FT006, FT021 | Mid | Lifecycle semantics and the reset boundary | M2 | Sprint B | Partly | W22 (PR #104), reproduced by M1 2026-11-20 (PR #108): lifecycle control matches Surefire under `class-grouped`, now the default; JUnit 3, `@RunWith` and `suite()` named as per-method (ADR-012 §2); `--workspace copy` wrote no `target/` in the project. FT021's reset-sensitive control built 2026-11-21 (M2): real runs show static fields and system properties reset between orders, files in the temp folder and the working directory not ([[evidence-m2]]). **Open:** M3 checks it (FT021's verifier); FT006 on a real project; the container plan (W27) | |
| FT009 | Mid | Portable, auditable evidence bundle | M3, M2 | Sprint B | Partly | Built: the writer and `replay` (M2, PR #143), `verify` (M3, PR #146), the first fixture bundles committed with `.gitattributes` (PR #147); M3's recount accepts both F1 bundles and they replay `same`. **Reproduced by M1 2026-11-22** on her own machine: F1 `verify` OK, `replay` `VERIFIED -> VERIFIED same`; six instruction gaps recorded ([[evidence-m1]]). Awaiting the gaps' fixes and supervisor acceptance. **M2's gaps (1, 2, 5, 6) fixed 2026-11-22** (`m2/w23-replay-gaps`): new bundles' `replay.md` commands run verbatim in cmd; M3's README gaps (3, 4) open | |
| FT010 | Mid | A typed report for an inconclusive search | M2, M3 | Sprint A | Partly | `INCONSISTENT` gives a schema-valid `UNRESOLVED (INCONSISTENT_OUTCOMES)` report with the counts and a next step, exit 0, never a polluter (W19, PR #106; `test_inconsistent_writes_a_real_report_now`). **Open:** M1 exercises it | |
| FT007, FT012 | Mid | Budget and ranking increment; one dated schedule | All | Plan: next meeting · build: Final | Partly | Built: budget (W24) and ranked search (W25); on fixture F2 at one budget, `ranked` reached `VERIFIED` in 70 invocations where `original` stopped at the limit ([[evidence-m2]]). **Open:** the measured comparison; on the real case FJ-03 ranking has no evidence to use (M1, #145). Schedule: [[10-Final1/iteration-2-plan]] | |
| FT008 | Mid | One real case with a task-matched comparator | M3 | Protocol: next meeting · run: Final | Partly | Protocol frozen; FJ-03 builds and its premise holds (W26a, reproduced by M2). **Open:** the runs and the yield table (W26b) | |
| FT011, FT022 | Mid | Scope authority and honest panel statuses | Supervisor, all | Next meeting | Partly | This register; [[10-Final1/supervisor-agenda]] | |
| FT013, FT014 | Mid | Signatures and personal confirmations | Each member | Before report acceptance | Open | — | |
| FT015 | Mid | Reconcile GenAI levels | M3, each | Before ownership assessment | Partly | Found the real, exact cause 2026-11-21 (M3): the register (docs/08-MidEval/genai-register.md) and the frozen Mid report's Table 9 already agree for M3 (L2 x18, L1 x1, as of the 11 October cutoff) -- the inconsistency was one transcription error inside the submitted worksheet's own "GenAI artefact register" table (M3's row said "L3 (18 rows), L2 (1)", contradicting M3's own declaration a few pages later in the *same* worksheet, which correctly says "L2 ... 18 register rows L2, 1 L1"). Corrected `.docx` produced and validated (diff against the original confirms this is the only change) ([[evidence-m3]]). **Open:** handing the corrected, editable worksheet to the supervisor -- ties into FT013's "supply the editable worksheet" | |
| FT016, FT017 | Mid | Clipped table; stale status text | M1, chapter owners | Report v2.0 | Open | — | |
| FT018 | Mid | One Java practitioner check | M1 | Before the Final | Open | Protocol drafted 2026-11-20 ([[10-Final1/practitioner-check]]); no session held | |
| FT019 | Mid | Template and abstract interpretation | Supervisor | Next meeting | Open | — | |
| FT020 | Mid | Cross-member handover | All | Sprint B | Open | — | |

Sprint dates are in [[10-Final1/iteration-2-plan]]. They are proposals until the cohort dates are
confirmed.

## Controlled change requests — handbook Form 12

None has been issued to us. If the supervisor or panel issues one, record it here with its
acceptance test.

## How to update a row

1. Change the status only when the evidence in [[10-Final1/feedback-register]]'s "Closes when"
   column exists.
2. Put the commit, PR or file in **Evidence**. One line.
3. Leave **Panel status** empty.
4. A row that reopens keeps its history: add the date and why.
