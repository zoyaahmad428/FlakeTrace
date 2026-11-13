# Carried action register — handbook Form 10

*v1 · 2026-11-13 · Status: live register. Updated before every evaluation.*

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
| A1 | Proposal | Detect without application logs | M2 | Final | Partly | No fixture test logs anything; verdicts come from order, outcomes and bytecode. **Open:** a portable record another person can audit (FT009) | |
| A2 | Proposal | Say whether trace instructions are injected | M1 | Final | Partly | No: `javap` on compiled classes, ADR-001. **Open:** explain the approved runtime fallback, and label static evidence as potential overlap (FT005) | |
| A3 | Proposal | Say whether code is modified | M2 | Final | Partly | Project files hashed before and after, `runner/integrity.py`. **Open:** state the limits honestly — endpoint equality only, `target/` and `.git/` excluded, no sandbox (FT021) | |
| A4 | Proposal | Explain how the code block is isolated | M2, M1 | Final | Partly | Sequence reduction and resource localisation both exist. **Open:** pass-alone defect (FT003), unverified deletions (FT004), overlap is not cause (FT005) | |
| A5 | Proposal | Show diverse applicable scenarios | M3 | Final | Partly | Seven fixture cases end to end. **Open:** scope confirmation and one real project (FT008) | |
| A6 | Proposal | More research to improve the solution | M1 | Final | Partly | Minimisation note, ADR research sections. **Open:** each member explains the nearest baseline; a measured comparison plan (FT008) | |
| A7 | Supervisor plan | Record the execution environment of every run | M2 | Final | Partly | JDK, OS, commit, order, seed in every record. **Open:** tool commit, dependency versions, timezone, reset assumptions (FT009, FT021) | |
| A8 | Supervisor plan | Reproduction confidence with uncertainty | M3 | Final | Partly | Wilson intervals on real counts. **Open:** the acceptance logic around them (FT003, FT004) | |
| A9 | Supervisor plan | Evidence report | M3, all | Final | Partly | Schema-validated reports for seven cases. **Open:** portable records, a replay command, a report for every status (FT009, FT010) | |
| A10 | Supervisor plan | Bounded resource decision | Supervisor, all | Next meeting | Open | Our position: static fields and system properties now, filesystem committed for FYP-2, the rest reported as unsupported ([[07-Defense/decisions/resource-family-boundaries]]). **Needs the supervisor's recorded decision** | |

## Raised at the Mid Evaluation

M-1 to M-5 are the FYP Committee's official comments. The rest are the supervisor's findings,
grouped; each keeps its FT identifier.

| ID | Raised at | Required action | Owner | Due by | Status | Evidence | Panel status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M-1 | Mid, official | Correct verification defects | M2, M3, M1 | Final | Open | Both defects reproduced on `7cf453d` ([[evidence-m2]]). Design: ADR-010, ADR-011 | |
| M-2 | Mid, official | Complete budget-aware planning | M2, M1, M3 | Final | Open | Design: ADR-014 | |
| M-3 | Mid, official | Real-project validation | M3, M2, M1 | Final | Open | Protocol: [[05-Testing/real-case-protocol]] | |
| M-4 | Mid, official | Restore the missing abstract | M2, all | Report v2.0 | Open | Our source and the submitted PDF contain a 188-word abstract; meaning of "missing" to be confirmed | |
| M-5 | Mid, official | Align the report with the template | M2, all | Report v2.0 | Open | [[10-Final1/report-v2-plan]] | |
| FT003 | Mid | No `VERIFIED` when the victim fails alone differently | M2, M3 | Sprint A | Open | — | |
| FT004 | Mid | Deletion evidence under repetition | M2, M3 | Sprint B | Open | — | |
| FT005 | Mid | Separate sequence assurance from resource evidence | M1, M3 | Wording: Sprint A · controls: Sprint B | Open | — | |
| FT006, FT021 | Mid | Lifecycle semantics and the reset boundary | M2 | Sprint B | Open | — | |
| FT009 | Mid | Portable, auditable evidence bundle | M3, M2 | Sprint B | Open | — | |
| FT010 | Mid | A typed report for an inconclusive search | M2, M3 | Sprint A | Open | — | |
| FT007, FT012 | Mid | Budget and ranking increment; one dated schedule | All | Plan: next meeting · build: Final | Partly | Schedule: [[10-Final1/iteration-2-plan]], [[00-Meta/roadmap]] | |
| FT008 | Mid | One real case with a task-matched comparator | M3 | Protocol: next meeting · run: Final | Partly | Protocol drafted | |
| FT011, FT022 | Mid | Scope authority and honest panel statuses | Supervisor, all | Next meeting | Partly | This register; [[10-Final1/supervisor-agenda]] | |
| FT013, FT014 | Mid | Signatures and personal confirmations | Each member | Before report acceptance | Open | — | |
| FT015 | Mid | Reconcile GenAI levels | M3, each | Before ownership assessment | Open | — | |
| FT016, FT017 | Mid | Clipped table; stale status text | M1, chapter owners | Report v2.0 | Open | — | |
| FT018 | Mid | One Java practitioner check | M1 | Before the Final | Open | — | |
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
