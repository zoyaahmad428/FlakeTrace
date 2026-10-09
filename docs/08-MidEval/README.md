# FYP-1 Mid Evaluation

**Meeting:** between 12 and 16 October 2026 — ⚠ *exact date and time: fill in*
**Submission deadline:** report + evidence worksheet **48 hours before the meeting**
**Weight:** 20% of FYP-1 · supervisor-only · formative but graded

Sources (in the claude.ai project, folder `Mid Eval/`): GCR announcement, *FYP-1 Mid Assessment
Guidelines and Rubrics*, *Presentation, Demo and Evidence Protocol*, *Pre-Evaluation Student
Worksheet*, *GenAI Use and Assessment Student Guide*.

---

## What is actually required

| # | Deliverable | Graded by | Notes |
| --- | --- | --- | --- |
| 1 | **Core module working live** with an edge/failure case | Form 2 #3 (25 marks — the largest) | Not video, not screenshots, not the recorded POC UI |
| 2 | **CI/CD on GitHub** — meaningful branches, automated tests | GCR requirement; Form 2 #6 | `.github/workflows/ci.yml` |
| 3 | **Mid report** in the prescribed LaTeX template | Form 3 (100) | Template: `F26_FYP1_Mid_Report_LaTeX_Complete` |
| 4 | **Student evidence worksheet** | Supports Forms 2 and 3 | Submitted with the report |
| 5 | **Panel action register** — every defence comment, status, evidence link | Form 2 #1 | [[08-MidEval/panel-action-register]] |
| 6 | **Evaluation tag** `mid-eval-v1` | Form 2 #6 | Created by M2 before submission |
| 7 | **GenAI register + prompt journal** | Form 3 #8 — *scored 0 until disclosed* | [[08-MidEval/genai-register]] |
| 8 | **7-slide, 7-minute deck** | Form 2 #8 | Structure below |
| 9 | Each member: individual section, 3 growth questions, ready for a no-AI task | Form 2 #8 / Form 11 risk | Worksheet §11 |

## Form 2 — presentation and demo (100)

| Criterion | Max | Our evidence | Owner |
| --- | --- | --- | --- |
| Previous proposal actions addressed | 10 | [[08-MidEval/panel-action-register]] | All |
| Iteration plan and progress | 10 | [[08-MidEval/iteration-plan]] | M2 |
| **Live prototype with core module** | **25** | [[08-MidEval/demo-plan]] | M2 drives, all present |
| Requirements and acceptance criteria | 10 | `02-Requirements/` + report ch. 4 | M3 |
| Design artefacts and evolution | 15 | `03-Design/` + ADR-001 + report ch. 5 | M1 |
| Repository, milestone, member evidence | 10 | Commits, PRs, reviews, tag, [[09-Team/members]] | M2 |
| Testing and early validation | 10 | CI runs, `eval/tests`, fixture premise checks | M3 |
| Presentation, Q&A, team and tool ownership | 10 | Each member's own explanation | All |

**Gates that cap marks:** diagrams that don't match code → design capped at 50% · no live
demo → implementation capped · ignored panel actions → progress capped · one member answering
everything → Form 11 contribution adjustment.

## Form 3 — report (100)

| Criterion | Max | Report chapter | Owner |
| --- | --- | --- | --- |
| Format and required artefacts | 5 | All | M2 (compiles it) |
| Problem, R&D, gap analysis | 15 | 1–2 | M1 |
| Vision, scope, success criteria | 10 | 1 | M1 |
| Requirements and acceptance criteria | 15 | 4 | M3 |
| Architecture, component/interface design | 15 | 5 | M2 |
| Data/process/behaviour design | 10 | 5 | M1 |
| Implementation documentation of completed module | 15 | 6 | M2 (+ each owner's section) |
| Testing plan, tool and risk disclosure | 15 | 7–8 | M3 |

*Chapter owners are a proposal — confirm at the meeting.*

## 35-minute session (from the protocol)

| Time | Stage |
| --- | --- |
| 0–7 | 7-slide presentation |
| 7–15 | Live demo: normal case, then edge/failure case, then the evidence (log, test, report) |
| 15–20 | Repository walkthrough: action register → tag → history → tasks → member evidence → design↔code → tests → tool disclosure |
| 20–32 | Individual questions, ~4 min each, may include a small change without AI |
| 32–35 | Supervisor closure |

## The seven slides

1. Identity, evaluation version, one-sentence iteration outcome
2. Panel actions — status and evidence
3. Iteration plan vs actual, delays and recovery
4. Requirements: scope, one user flow, FR/NFR, acceptance check
5. Design evolution: current architecture + one behaviour artefact; what changed since proposal
6. Core module: input → processing → output, tests, result, known limitation
7. Repo, ownership, GenAI disclosure, next iteration → hand over to live demo

## Submission checklist

- [ ] Report PDF compiled from the template
- [ ] Worksheet filled (all sections, all three member sections)
- [ ] Panel action register complete — including open items
- [ ] `mid-eval-v1` tag created; full SHA recorded in the worksheet
- [ ] Supervisor has read access to the repo
- [ ] GenAI register and prompt journal current for all three members
- [ ] Demo rehearsed on the actual laptop, with offline fallback
