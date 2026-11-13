# FYP-1 Final — what it needs and where we stand

*v1 · 2026-11-13 · drafted by M2 with Claude ([[genai-log-m2]]) · Status: `PROPOSED` — for M1 and
M3 to review, and for the supervisor to confirm the dates and decisions in
[[10-Final1/supervisor-agenda]].*

This folder is the working plan from the Mid Evaluation to the FYP-1 Final. It replaces
`08-MidEval/` as the place to look first. `08-MidEval/` stays as the record of what was submitted
at the Mid.

| If you want to… | Open |
| --- | --- |
| Read what the Mid said about us | [[10-Final1/mid-eval-outcome]] |
| See every correction asked for, its owner and how it closes | [[10-Final1/feedback-register]] |
| See the carried action register (handbook Form 10) | [[10-Final1/action-register]] |
| Know what to build, in what order, and who checks it | [[10-Final1/iteration-2-plan]] |
| Know how much of the committed scope is built | [[10-Final1/scope-inventory]] |
| Prepare the questions only the supervisor can answer | [[10-Final1/supervisor-agenda]] |
| Prepare your own viva | [[10-Final1/ownership-prep]] |
| Fix the report and worksheet | [[10-Final1/report-v2-plan]] |
| Plan the Final demo | [[10-Final1/demo-plan]] |
| Read the design changes | ADR-010 to ADR-015 in `03-Design/decisions/` |

---

## The official result of the Mid

> **Presentation:** An integrated core pipeline and substantial early testing are evident. Correct
> verification defects, and complete budget-aware planning alongside real-project validation.
>
> **Report:** The report provides clear requirements, design diagrams, and implementation
> traceability. Please restore the missing abstract and align the report properly with the
> template.

*(FYP Committee feedback, `MidResult-Comments-Result.txt`, received 2026-11-13.)*

That is five instructions. Everything in this folder serves one of them.

| # | Instruction | Where it is planned |
| --- | --- | --- |
| M-1 | Correct the verification defects | ADR-010, ADR-011 · work packages W17–W21 |
| M-2 | Complete budget-aware planning | ADR-014 · W24, W25 |
| M-3 | Validate on a real project | [[05-Testing/real-case-protocol]] · ADR-012 · W22, W26 |
| M-4 | Restore the missing abstract | [[10-Final1/report-v2-plan]] · W28 |
| M-5 | Align the report with the template | [[10-Final1/report-v2-plan]] · W28 |

## What the FYP-1 Final is

Source: *FYP Handbook 2026, 3rd Edition* (claude.ai project, `FYP-Handbook-2026.pdf`), Appendix A
"Stage 2" and Forms 4 and 5.

| | |
| --- | --- |
| **Who evaluates** | A faculty **panel** plus the supervisor judge the presentation and demo. The supervisor or an examiner reviews the report |
| **Length** | 15 minutes of presentation and demo, then the report review outside that time |
| **Weight** | 50 marks, half of FYP-1: 42.5 for the demo and defence, 7.5 for the report |
| **When** | The handbook says week 15, with the poster submitted in week 13. **Our exact dates are not confirmed** — see below |
| **Its purpose** | An *integration readiness gate*: is the FYP-1 work good enough, understood enough and sound enough to build FYP-2 on? |
| **The handbook's rule of thumb** | At least **60% of the committed scope** implemented, modular, readable and *buildable without the original developer present* |

> ⚠ **Dates.** The Mid was held on 16 October. If that was the handbook's week 8, the poster is due
> around **16–20 November** and the Final falls around **30 November – 4 December**. This is an
> estimate from the handbook's week numbers, not an announcement. **Confirm both dates from the FYP
> Committee's notice before relying on the schedule in [[10-Final1/iteration-2-plan]].**

### Form 4 — presentation and demo (100, scaled to 42.5)

| Criterion | Max | What the panel looks for | Our evidence | Lead |
| --- | --- | --- | --- | --- |
| Poster | 10 | Format, layout, style, contents | Poster (section below) | M1 |
| Previous mid/proposal actions addressed | 10 | Required changes addressed or formally justified. If not: progress is capped | [[10-Final1/action-register]] | M2 |
| Implementation progress against approved scope | **25** | At least 60% of committed work meaningfully implemented, unless scope was formally revised | [[10-Final1/scope-inventory]] | All |
| Quality and robustness of live demo | 15 | Works beyond the happy path. Demo-only or hardcoded behaviour is capped | [[10-Final1/demo-plan]] | M2 |
| Testing on completed modules | 10 | Functional, edge and integration tests executed **and explained** | CI, regression tests for FT003/FT004/FT010, controls | M3 |
| Design evolution and updated artefacts | 10 | Changes since the Mid are justified and shown in the artefacts. Outdated artefacts are capped | ADR-010 to ADR-015, updated [[03-Design/architecture]] | M1 |
| Code quality, modularity, integration readiness | 10 | Structured, readable, buildable, ready for FYP-2 | Contracts, container run, evidence bundle | M2 |
| Responsible tool / API / GenAI ownership defence | 5 | Each student explains what the tool did, what they added, how they verified it | [[08-MidEval/genai-register]], Form 13 | Each |
| Presentation, Q&A, team coordination | 5 | Short, clear, balanced. A weak member triggers the contribution adjustment (Form 11) | [[10-Final1/ownership-prep]] | Each |

### Form 5 — report (100, scaled to 7.5)

| Criterion | Max | What is checked | Chapter owner |
| --- | --- | --- | --- |
| Report matches demonstrated system | 5 | Reflects what was actually built. If not, implementation documentation is capped | M2 (compiles) |
| Updated requirements and traceability | 15 | Requirements map to implemented features, pending features and acceptance criteria | M3 |
| Updated design artefacts with rationale | 20 | Architecture, data, process and behaviour artefacts match the real system | M2, M1 |
| Implementation details and reproducibility | 20 | Setup, dependencies, configuration and technical flow clear enough to reproduce | Each module owner |
| Testing evidence and early validation | 20 | Inputs, expected and actual results, bugs and fixes, edge cases | M3 |
| R&D continuation and FYP-2 evaluation plan | 10 | Baseline, benchmark, metric or comparison planned for FYP-2 | M3 with M1 |
| Tool / API / GenAI disclosure, risks, limitations | 10 | Scored **0 until submitted** | Each, M3 compiles |

### What the handbook says must exist at this gate

From the handbook's stage table (C.5.1, "Final-1 — core build accepted"). The handbook itself
marks that table as "proposed for review", and says the forms take precedence where they differ.

| The project | The written record |
| --- | --- |
| A working core system covering the primary scenario end to end, built against the approved design | Traceability matrix for all committed requirements: requirement → design → test |
| Integration path proven, not assumed | Test, deployment, rollback and handover plan drafted, with defect severity definitions |
| **The comparison baseline measured** | Timeline revised against actual progress |
| Deployment target selected and **a first deployment attempted** | Any scope change processed through change control, not made silently |

## Where we stand on 13 November

**Built and demonstrated at the Mid** (tag `mid-eval-v1`, commit `86d8355`): ordered single-JVM
execution, one-by-one polluter search, delta debugging, shuffled-order search, static resource
extraction with call depth, repeated-run statistics, typed reports, one command, CI on JDK 8.
268 tests passed in the supervisor's own run. After the tag, the web UI over the CLI was merged
(PR #99, 15 October). `main` has had no commits since then.

**The supervisor's provisional verdict:** *Proceed with required corrections.*

**The three things that matter most** (from
[[10-Final1/mid-eval-outcome]]):

1. **Two reports that say `VERIFIED` when they should not.** Reproduced on `main` `7cf453d` on
   13 November ([[evidence-m2]]): a victim that always fails alone with a *different* exception,
   and a two-test sequence where one test is not needed. Fixing these comes before everything else.
2. **A diagnosis nobody else can audit.** The committed reports point at files on one laptop.
3. **The contribution the project was approved for is not built yet.** There is no execution
   budget, and resource evidence is collected only *after* the search, so it cannot guide it.

**Scope built:** about 43% of the committed scope by our own unweighted count, against the
handbook's 60%. The plan reaches about 68% if it is carried out
([[10-Final1/scope-inventory]]). The weights need the supervisor's agreement.

## Priorities, in order

| Tier | What | Why first |
| --- | --- | --- |
| **P0 — tell the truth** | Qualify the claims we cannot yet support. Fix the pass-alone defect. Give every diagnosis a typed report. Sign the report. Submit the poster | A wrong `VERIFIED` is the worst thing this product can produce, and the paperwork has hard dates |
| **P1 — make it auditable and budgeted** | Outcome tallies, deletion checks, evidence bundle with an independent recount, execution budget with a verification reserve, class-level lifecycle fidelity | Without these, a real-project result could not be trusted or reproduced |
| **P2 — show it on a real project** | One fastjson victim case through the whole pipeline, ranked search against unranked search under the same budget | This is the approved contribution and the official instruction |
| **P3 — after the Final** | Resource intervention check, brittle tests, adaptive policy, filesystem family, runtime evidence, security hardening | Staged against FYP-2 gates, not dropped |

## The poster

10 marks on Form 4. Handbook section 7:

- Size **22.5 × 34.5 inches**, **portrait**
- Top left: title, members, supervisor. Top right: project goals. Bottom: project plan and the
  deliverables for the Final
- Little text, bullets, large fonts readable from one metre, diagrams over words
- Submit the editable source file **and** a JPEG. Photoshop or CorelDRAW recommended. With any
  other tool the group prints it itself
- Submitted to the FYP Committee after supervisor approval

**Suggested content, all from material we already hold:** the problem in one sentence · the
pipeline as a five-box diagram · one real report, shown as "what it claims and what it does not"
· the three outcome classes · the numbers we have (fixture cases, tests, the POC's held-out
ranking result with its limits) · what the Final will show. Nothing on the poster may be a claim
that is not in [[07-Defense/claims-ledger]].

## Rules that carry over

Root `CLAUDE.md` still governs: members commit, never agents; no invented results; contracts change
only with all three members; each member can explain and modify their own work without AI.
