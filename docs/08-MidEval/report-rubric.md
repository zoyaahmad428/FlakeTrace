# Mid Report — what it is graded on

*Status: summary of the official PDFs, written 2026-10-11 so Claude Code sessions (which cannot
open the claude.ai project) know the rubric. The PDFs are the authority — if this note and a PDF
disagree, the PDF wins. Sources (claude.ai project, `Mid Eval/`):
`FYP-1-Mid-Assessment-Guidelines-and-Rubrics.pdf`, `FYP_GenAI_Use_and_Assessment_Student_Guide.pdf`.*

Rules for writing: [mid-eval-report/CLAUDE.md](../../mid-eval-report/CLAUDE.md) ·
Deliverables and Form 2: [[08-MidEval/README]]

## Form 3 — report evaluation (100 marks)

Bands for every criterion: Exemplary 85–100 % · Good 70–84 % · Developing 50–69 % ·
Marginal 30–49 % · Unsatisfactory 0–29 %.

| # | Criterion (CLO) | Marks | What the supervisor looks for at the top band | Gate when weak | Our chapters | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Report format & artefacts (CLO2) | 5 | Template followed strictly; every mandatory section, signature and artefact present | Section marks capped if formatting fails | All, front matter, appendices | M2 |
| 2 | Problem formulation, R&D, gap analysis (CLO1) | 15 | Rigorous literature *synthesis* that isolates the research gap and the complex computing problem | **Mandatory R&D rewrite** if the review is weak or reads as AI-summarised | Ch 1–2 | M1 |
| 3 | Vision, scope, success criteria (CLO2) | 10 | Very clear scope, modular breakdown, testable success metrics, consistent with the proposal | **Scope table must be resubmitted** if scope is vague | Ch 1, Ch 10 | M1 (+ M3 for Ch 10) |
| 4 | Requirements & acceptance criteria (CLO2) | 15 | FRs/NFRs each with a verifiable acceptance check | Generic acceptance criteria drop to Developing; untestable requirements to Unsatisfactory | Ch 4, App. B | M3 |
| 5 | Architecture & component/interface design (CLO3) | 15 | Detailed architecture diagrams with layer separation and interface contracts | **Design marks capped** if diagrams are purely auto-generated, decorative or unjustified | Ch 5.1–5.5 | M2 |
| 6 | Data / process / behaviour design (CLO3) | 10 | Project-specific ERD/schema, data flow, activity, sequence or state diagrams, each explained in text | **Project-specific artefacts must be resubmitted** if diagrams are generic (e.g. a template ERD) | Ch 5.6–5.8 | M1 |
| 7 | Implementation documentation (CLO4) | 15 | Setup, main files/classes/functions, algorithms and trade-offs all clear; reproducible | **Implementation docs capped** if setup is not reproducible | Ch 6 | M2 frame, each member's module |
| 8 | Testing plan & tool/risk disclosure (CLO5) | 15 | Thorough test plan, early results, full disclosure of external and GenAI tools, risks and privacy | **Tool-use item scores 0 until full disclosure is submitted** | Ch 7 (file `chapter8_testing`), Ch 9 | M3, M2 |

## Red flags the supervisor is told to probe

| Red flag | How it is probed | Consequence |
| --- | --- | --- |
| Polished but generic report text | Supervisor picks one R&D paragraph and asks the member to explain it in their own words without reading | Classed as GenAI synthesis without understanding; mandatory rewrite from project evidence |
| Sudden large code volume | Line-by-line walk-through of new code; "what if this function is removed?" | Implementation marks capped; re-demo before FYP-1 Final |
| One member answers everything | 1-on-1 with the quieter member about their own module | Individual Contribution Adjustment (Form 11) |
| Milestones marked done but demo unchanged | Live output demanded for every claimed milestone | Recorded as dishonest milestone reporting; Form 10 action |
| Proposal panel actions missing or without evidence links | Panel action register opened and checked item by item | Form 2 criterion 1 capped |

## GenAI guide — what applies to the report

- GenAI is **allowed** for report drafting; using it does not by itself reduce marks.
  Concealment, uncritical acceptance and inability to explain do.
- Classify **per artefact** (L1 supportive · L2 assisted · L3 core-assist · L4 substituted).
  Report sections drafted with Claude and then reviewed and edited by the member are **L2**.
  L4 (cannot explain or modify) can cap affected marks at 50 %.
- A polished report does **not** establish ownership; each member must defend their own chapters.
- **Citations:** a source must not appear in the report until a student has opened and checked the
  original. Students are responsible for fabricated citations even when the AI produced them.
- Strongest evidence of critical use: cases where the member rejected or corrected an AI suggestion.
  Mention one or two in the Chapter 9 disclosure.
