# Mid Evaluation outcome

*v1 · 2026-11-13 · Status: record of what was received. Nothing here is our own judgement unless
marked.*

**Sources** (claude.ai project "FlakeTrace - FYP"):

| Document | What it is |
| --- | --- |
| `MidResult-Comments-Result.txt` | The FYP Committee's official feedback. Two short comments |
| `Post Mid - Analysis by Supervisor/FlakeTrace_Mid_Evaluation_Feedback_and_Improvement_Report` | The supervisor's detailed findings, FT003 to FT022, with owners and acceptance evidence. Prepared 16 October from a 14 October review |
| `…/FlakeTrace_Supervisor_Meeting_Briefing` | The supervisor's meeting sheet, with provisional ratings and the questions for each member |
| `…/FlakeTrace_Running_Mid_Evaluation_Review_Log` | The review log: every issue with its evidence, and what the reviewer executed |
| `…/FlakeTrace_Contribution_and_Progress_Review` | Per-member evidence and viva questions |
| `…/FlakeTrace_Student_Worksheet_Coverage_Audit` | Block-by-block audit of our worksheet: 27 full, 16 partial, 8 missing |

The supervisor's documents call themselves *supporting supervisory feedback* and *provisional*.
They state that final marks, live findings and official decisions remain with the supervisor.
We have **not** been given marks.

---

## Official comments

> **Presentation:** An integrated core pipeline and substantial early testing are evident. Correct
> verification defects, and complete budget-aware planning alongside real-project validation.
>
> **Report:** The report provides clear requirements, design diagrams, and implementation
> traceability. Please restore the missing abstract and align the report properly with the
> template.

## The supervisor's verdict

**Provisional: Proceed with required corrections.**

> You have implemented an integrated diagnosis pipeline … These are substantive parts of the
> project. The defining complex computing contribution — choosing search and verification actions
> within one finite execution budget using incomplete evidence — is still planned.

**What to keep:** the three connected packages, explicit interfaces, fixture ground truth,
meaningful tests and recorded limitations.

**The reviewed version:** tag `mid-eval-v1`, commit `86d8355c022e63ffbd7a84f02aecf0185c5a2b49`.
Every correction must name its own commit and leave this baseline intact.

**What the reviewer ran:** all 268 existing tests (85 evaluation, 39 extractor, 144 runner) passed.
F1 and F3 gave `VERIFIED`, N1 and N3 gave their typed `UNRESOLVED`. Two scripted counterexamples
written by the reviewer both returned a schema-valid `VERIFIED` that should not have been issued.

## The supervisor's three priorities

1. **Make certification truthful.** Repair the pass-alone defect. Qualify the minimality and
   resource-cause claims now, while stronger checks are built (FT003, FT004, FT005).
2. **Make a diagnosis independently auditable.** Keep a report together with its raw record,
   define what is reset between runs, and reproduce one case on another member's machine
   (FT006, FT009, FT021).
3. **Protect the approved contribution and a feasible schedule.** Agree the resource boundary and
   dated budget, ranking and real-project checkpoints. Do not replace them with more fixture
   features (FT007, FT008, FT011, FT012, FT022).

## Provisional rating suggestions

From the meeting briefing. These are the reviewer's documentary suggestions, **not marks**. Two
criteria were deferred because they need live observation.

**Presentation and demo (Form 2)**

| Criterion | Weight | Suggestion | Issues behind it |
| --- | --- | --- | --- |
| Previous proposal actions addressed | 10 | 6/10 | FT011, FT022 |
| Iteration plan and progress | 10 | 6/10 | FT007, FT012 |
| Live prototype with core module | 25 | deferred to the live demo | FT003–FT008 |
| Requirements and acceptance criteria | 10 | 6/10 | FT003–FT005, FT017 |
| Design artefacts and evolution | 15 | 12/15 | FT005, FT006 |
| Repository, milestone, member evidence | 10 | 8/10 | FT009, FT020 |
| Testing and early validation | 10 | 8/10 | FT002–FT006 |
| Presentation, Q&A, tool ownership | 10 | deferred to the live meeting | FT015, FT020 |

**Report (Form 3)**

| Criterion | Weight | Suggestion | Issues behind it |
| --- | --- | --- | --- |
| Format and required artefacts | 5 | 3/5 | FT013, FT019 |
| Problem, R&D, existing solutions | 15 | 12/15 | FT005, FT008, FT018 |
| Vision, scope, success criteria | 10 | 6/10 | FT007, FT011, FT012 |
| Requirements and acceptance criteria | 15 | 9/15 | FT003, FT004, FT017 |
| Architecture and interfaces | 15 | 12/15 | FT005–FT007 |
| Data, process, behaviour design | 10 | 8/10 | FT003, FT004, FT009 |
| Implementation documentation | 15 | 12/15 | FT002, FT006, FT010 |
| Testing, tool and risk disclosure | 15 | 9/15 | FT003–FT005, FT008, FT015 |

**Reading this:** design and implementation documentation scored well. The marks were lost on
**what the certificate claims**, **dates and scope approval**, and **paperwork** (signatures,
GenAI levels, a clipped table).

## Individual contribution

For all three members the reviewer wrote the same provisional judgement:

> Insufficient evidence for a reliable overall contribution judgment.

This is **not** a finding against anyone. The reviewer found substantive, attributable technical
work from each member, and wrote that no ranking, percentage or below-expectation finding is
justified. What is missing is **observed understanding**: each member explaining and changing their
own work without AI. The questions the supervisor prepared are in [[10-Final1/ownership-prep]].

One structural note: integration knowledge is concentrated in Member 2. The supervisor proposes
Member 1 as the reproduction backup and Member 3 as the report and schema backup (FT020).

## A contradiction we must clear up with the supervisor

The official comment says the abstract is **missing**. The supervisor's own audit says the
submitted abstract is **about 190 words** and should be shortened towards the handbook's 50–125.
Our source has a 188-word abstract (`mid-eval-report/chapters/04_abstract.tex`) and the submitted
PDF's table of contents lists it on page vii.

We do not know which is meant. It is the first item in [[10-Final1/supervisor-agenda]].

## What we do not have

- Marks, or the supervisor's final ratings
- The original panel result sheet with the exact wording and due dates of panel actions A1–A6
- A record of whether the review proposed for **23 October** took place, and what was agreed
- Confirmed dates for the poster and the FYP-1 Final
- The supervisor's decision on the resource boundary (panel action A10)
