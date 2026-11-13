# Agenda for the next supervision meeting

*v1 · 2026-11-13 · Status: questions prepared, **no answers yet**. Write each answer here with the
date, in the supervisor's words where possible. An answer recorded here is the approval record the
handbook's change control asks for.*

**Bring:** [[10-Final1/feedback-register]] · [[10-Final1/action-register]] ·
[[10-Final1/iteration-2-plan]] · [[10-Final1/scope-inventory]] · the unsigned signature page.

---

## 1. Dates

| Question | Answer | Date |
| --- | --- | --- |
| When is the poster due, and to whom? | | |
| When is our FYP-1 Final slot? When is the report due before it? | | |
| Was the review proposed for 23 October meant to be held? What is the next review date? | | |
| Proposal defence date for the record: 9 or 11 September? | | |

## 2. What `VERIFIED` means

We propose (ADR-010): `VERIFIED` asserts exactly four things — the sequence reproduces above the
threshold, the victim passed alone in every run, every kept test was shown to be needed by
repeated removal, and a static write/read overlap exists. It does **not** assert that the named
resource is the cause, and it is displayed as `VERIFIED (sequence)`.

| Question | Answer | Date |
| --- | --- | --- |
| Is that meaning acceptable? | | |
| A sequence that replays reliably but has **no** static edge: `CANDIDATE` (our proposal, matching the certificate contract) or `UNRESOLVED` (today's code)? | | |
| Does causal certification of the resource remain a promise? If yes, is the intervention check of ADR-015 an acceptable way to establish it, and by which milestone? | | |

## 3. Approved scope

| Question | Answer | Date |
| --- | --- | --- |
| Panel action A10: is the boundary "static fields and system properties now; filesystem in FYP-2; everything else reported as unsupported" approved? | | |
| Is the static-only evidence of Iteration 1 (ADR-001) an approved refinement, or does it need the committee? | | |
| Is the three-member roster confirmed on the committee's side? | | |
| Runtime collection, the graph, the adaptive policy and security hardening are scheduled for FYP-2, as in the roadmap. Does any of them need a recorded change request? | | |

## 4. Panel actions

| Question | Answer | Date |
| --- | --- | --- |
| May we have the original panel result sheet, with the exact wording and due dates of A1–A6? | | |
| Are the "Partly" statuses in [[10-Final1/action-register]] the right reading? | | |
| Has a controlled change request (Form 12) been issued to us? | | |

## 5. The 60% rule

| Question | Answer | Date |
| --- | --- | --- |
| Is [[10-Final1/scope-inventory]] the right list of committed items? | | |
| How should they be weighted? | | |
| Our unweighted count is about 43% at the Mid and about 68% if the plan holds. Is that a fair basis for Form 4's progress criterion? | | |

## 6. Real project

| Question | Answer | Date |
| --- | --- | --- |
| Is one fastjson victim case (FJ-03) through the whole pipeline, with ranked against unranked search at one budget, the right target for the Final? | | |
| Most reproducible fastjson cases are **brittle** (fail alone, pass after a state-setter). Should supporting them be the first FYP-2 increment? | | |
| Is comparison against published tools (iFixFlakies, RankF) acceptable as FYP-2 work? | | |

## 7. Report and worksheet

| Question | Answer | Date |
| --- | --- | --- |
| The official comment says the abstract is **missing**. Our submitted PDF has a 188-word abstract on page vii. What should be restored? | | |
| Abstract length: the handbook's 50–125 words, or the template's 150–200? | | |
| "Align the report properly with the template": which parts are out of line? | | |
| Which handbook governs — the 3rd Edition we were given, or the draft? | | |
| How should the corrected worksheet and the signed report be submitted? | | |

## 8. Individual ownership

| Question | Answer | Date |
| --- | --- | --- |
| Is the current allocation — M1 evidence, M2 runner and integration, M3 evaluation — the agreed workload? | | |
| When will each member's explanation and small task be observed? | | |

---

## Our commitments for the meeting

What we bring, per the supervisor's "what must be brought" list. Tick only what exists.

- [ ] The baseline commit and every correction commit
- [ ] The FT003 regression and its output, before and after
- [ ] The agreed verdict contract (ADR-010, ADR-011) with three ticks
- [ ] Member 1's static-evidence wording and control design
- [ ] One portable bundle, with an independent reproduction record
- [ ] The corrected GenAI register, the editable worksheet, the signed report
- [ ] The budget and ranking plan, and the real-case protocol
- [ ] Each member: one completed personal change they can explain and modify
