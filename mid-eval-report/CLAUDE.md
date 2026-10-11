# mid-eval-report/CLAUDE.md — rules for writing the FYP-1 Mid Report

You are helping one member of FlakeTrace (F26-214) write the **FYP-1 Mid Report** in the
prescribed FAST LaTeX template. The root [CLAUDE.md](../CLAUDE.md) still applies — especially
"the member commits, never the agent" and the honesty rules. This file adds what is specific to
the report.

**Deadline:** report PDF + evidence worksheet due **Wednesday 14 October 2026, 8:30 AM**
(48 hours before the Mid meeting on Friday 16 October, 8:30 AM).

## 1. First, ask which member you are working for

| Member | Name | Reg. no. | Owns in the code |
| --- | --- | --- | --- |
| M1 | Zoya Ahmad | 23i-0805 | `evidence/` |
| M2 | Abdul Raffay | 23i-0587 | `runner/`, `.github/`, integration, **compiles the report** |
| M3 | Zarpash Nasim | 23i-0027 | `eval/`, `fixtures/` |

## 2. Who writes which file

**Only edit the files your member owns.** Every `.tex` file starts with an `OWNER:` header —
read it before touching the file. To change someone else's file, write the suggestion in your
PR description or a GitHub issue instead.

| File (`chapters/`) | Owner | Graded by (Form 3 unless noted) |
| --- | --- | --- |
| `01`–`03`, `05`, `07` front matter | M2 | #1 Format (5) |
| `04_abstract`, `06_executive_summary` | Joint — written **last**, M2 assembles | #1–#3 |
| `chapter1_introduction` | M1 | #3 Vision, scope, success criteria (10) |
| `chapter2_research` | M1 | #2 Problem, R&D, gap analysis (15) |
| `chapter3_iteration_plan` | M2 | Form 2 #1–#2 |
| `chapter4_requirements` | M3 | #4 Requirements & acceptance criteria (15) |
| `chapter5_design` (5.1–5.5) | M2 | #5 Architecture & interfaces (15) |
| `chapter5_data_behaviour` (5.6–5.8) | M1 | #6 Data / process / behaviour design (10) |
| `chapter6_iteration1` (frame) | M2 | #7 Implementation documentation (15) |
| `chapter6_module_m1` / `_m2` / `_m3` | M1 / M2 / M3 | #7 |
| `chapter8_testing` (prints as Chapter 7) | M3 | #8 Testing, tool & risk disclosure (15) |
| `chapter9_development_evidence` (frame) | M2 | Form 2 #6, Form 3 #8 |
| `chapter9_contribution_m1` / `_m2` / `_m3` | M1 / M2 / M3 | Form 2 #6, #8 |
| `chapter10_fyp2_plan` | Joint — lead M3 | #3 |
| `conclusion` | Joint — lead M1 | #1 |
| `appendix_action_register`, `appendix_repository` | M2 | Form 2 #1, #6 |
| `appendix_requirements`, `appendix_test_cases` | M3 | #4, #8 |
| `appendix_meetings` | M1 | #1 |
| `appendix_diagrams` | each owner adds their own; lead M1 | #5–#6 |
| `main.tex`, `fast-nuces-bs.cls`, `tikz-uml.sty` | M2 only | #1 |
| `references/refs-m<N>.bib` | that member | — |

The full rubric, summarised: [docs/08-MidEval/report-rubric.md](../docs/08-MidEval/report-rubric.md).
Read the rows for the chapter you are writing before drafting it.

## 3. Writing rules — these protect marks

1. **Draft only from the repository.** Each file's `DRAW FROM:` header lists its sources
   (`docs/`, folder READMEs, ADRs, `docs/evidence-m<N>.md`, `eval/reports/*.json`). Read them
   first. Do not write from general knowledge about flaky tests — the rubric's red flag is text
   that is "grammatically polished but factually generic without project-specific depth", and
   the supervisor will pick a paragraph and ask the member to explain it without the page.
2. **No invented numbers.** Every count, rate, interval, timing or "works" claim must come
   from a committed evidence file or report JSON, and the sentence should say which. If there
   is no evidence, write `\todo{no evidence yet: ...}` — never a plausible-looking number.
3. **Results tables are generated, never typed.** Run
   `python3 mid-eval-report/scripts/json_to_tex.py` from the repo root; it writes
   `tables/generated/*.tex` from `eval/reports/*.json`. Add a new generated table by extending
   that script, not by hand-copying numbers.
4. **Citations:** add a BibTeX entry to your own `references/refs-m<N>.bib` only after the
   member has opened the original paper. Candidate sources are in
   `docs/01-Literature/references.md` with notes in `docs/01-Literature/per-paper/`.
5. **Match the code.** Diagrams and design text describe what is implemented on `main` now,
   not the proposal. The rubric caps design marks when diagrams don't match code or look
   auto-generated and unjustified. Where the design changed, say so in 5.5 Design Evolution and
   name the ADR (`docs/03-Design/decisions/ADR-00N-*.md`).
6. **State what is mocked or missing** (see `docs/08-MidEval/demo-plan.md`) and give each
   module at least one real limitation and one failure case.
7. **Scope** in chapters 1 and 10 must agree with the approved proposal and the post-defence
   narrowing in `docs/07-Defense/decisions/` — do not reintroduce dropped features.
8. **Write in the member's voice and keep it short.** Prefer one concrete sentence with a file
   name or number over three general ones. The member must be able to defend every line.

## 4. LaTeX conventions (so three people never collide)

- **Labels:** `ch<N>:<kind>:<name>`, e.g. `ch5:fig:arch`, `ch4:tab:fr`, `ch6:sec:ddmin`.
  Kinds: `fig`, `tab`, `sec`, `eq`, `lst`.
- **Figures:** put images in `figures/m<N>/`; shared ones in `figures/shared/`. Proposal-time
  figures already there: `proposal_block_diagram.png`, `proposal_gantt.jpeg`.
- **Placeholders:** `\placeholderfig{label}{caption}{owner}` reserves a figure that others can
  already `\ref`. Replace it with a real figure, keeping the same label and caption.
- **Unfinished text:** `\todo{...}` prints in red. Before submission
  `grep -rn '\\todo{' mid-eval-report/chapters` must print nothing.
- **Code listings:** `lstlisting` (the `listings` package is loaded). Keep them short — show
  the key lines and point to the file.
- **Abbreviations:** ask M2 to add them to `07_abbreviations.tex` (list them in your PR).
- **Packages:** do not add packages in a chapter. Ask M2 to add them to `main.tex`.

## 5. Diagrams

Write diagrams as PlantUML in `diagrams/m<N>/<name>.puml`, render to PNG, commit both, and
include the PNG. PlantUML text shows up in diffs and in the member's own history.

```bash
# needs Java; download plantuml.jar once from plantuml.com
java -jar plantuml.jar -tpng mid-eval-report/diagrams/m2/architecture.puml \
     -o ../../figures/m2
```

Put `skinparam dpi 200` at the top of each `.puml` so the PNG is sharp in the PDF.

| Diagram | Slot label | Owner | Draw from |
| --- | --- | --- | --- |
| Use case diagram | `ch4:fig:usecases` | M3 | `docs/02-Requirements/` |
| Architecture / components (current) | `ch5:fig:arch` | M2 | `docs/contracts/interfaces.md`, the three folders |
| Proposal block diagram (before) | `ch5:fig:proposal-arch` | M2 | already included |
| Report data model | `ch5:fig:datamodel` | M1 | `eval/schema/report.schema.json` |
| Evidence extraction data flow | `ch5:fig:evidence-dfd` | M1 | `evidence/extract.py`, `docs/contracts/resource-evidence.md` |
| `diagnose` sequence | `ch5:fig:diagnose-seq` | M2 | `runner/cli.py`, `runner/diagnose.py` |
| Reproduce → search → ddmin → verify activity | `ch5:fig:search-activity` | M2 | `runner/search.py`, `minimise.py`, `verify.py` |
| Outcome decision | `ch5:fig:outcome` | M3 | `eval/outcome.py`, `docs/contracts/report-schema.md` |
| Iteration plan vs actual (Gantt) | `ch3:fig:gantt` | M2 | `docs/08-MidEval/iteration-plan.md` |

After drawing, check every box and arrow against the code it claims to show.

## 6. Building

```bash
cd mid-eval-report
latexmk -pdf main.tex          # pdflatex + bibtex + reruns
latexmk -c                     # clean auxiliary files
```

CI (`.github/workflows/report.yml`) builds the PDF on every PR touching `mid-eval-report/`
and uploads it as an artifact — download it from the PR's Checks tab to see the whole report.

Known template quirks (kept, because the template must be followed):
- The class's `\maketitle` already prints a table of contents and lists of figures/tables
  right after the title page, and `main.tex` prints them again after the front matter.
  M2 decides before submission whether to keep both (as the official template PDF does).
- Until the first `\cite{}` exists, BibTeX reports "I found no \citation commands". The PDF
  still builds; the message disappears once anyone cites a source.

Overleaf: M2 uploads `mid-eval-report/` as a zip for a final visual check. The repository is
the master copy — never edit in Overleaf and forget to bring the change back.

## 7. GenAI and the report

Team decision: report-writing sessions are **not** logged per session in
`docs/genai-log-m<N>.md` (root CLAUDE.md §6 does not apply inside `mid-eval-report/`).

The report must still **disclose** AI use — Form 3 #8 scores the tool-use item 0 until
disclosure is submitted. That disclosure lives in Chapter 9, "Tools and Tool-Assisted
Development": per artefact (code modules, tests, diagrams, report text), the level L1–L4, what
the member changed, and how it was verified. Draw it from `docs/08-MidEval/genai-register.md`,
and list the report text itself as an assisted artefact.

## 8. Hand-over at the end of each unit of work

Same as root CLAUDE.md §3: one chapter section (or one diagram) per commit, the member reads
`git diff --staged` and commits. Title format: `[M<N>] report: <what changed>`, e.g.
`[M3] report: write requirements acceptance criteria table`. Branch: `docs/report-<topic>`
or `m<N>/report-<topic>`. The reviewer of a report PR must be a member who does **not** own
that chapter.

Before handing over, compile (`latexmk -pdf main.tex`) and say whether it built. A PR that
breaks the build blocks the other two members.

## 9. Timeline

| When | Milestone |
| --- | --- |
| Sun 11 Oct | Skeleton merged, ownership agreed, diagram list agreed |
| Mon 12 Oct | Every owner drafts their chapters; diagrams in parallel |
| Tue 13 Oct | Cross-review PRs; abstract, executive summary, conclusion; no `\todo{}` left |
| Tue 13 Oct night | Freeze; full compile; Overleaf visual check; `mid-eval-v1` tag |
| Wed 14 Oct, 8:30 AM | Submit report PDF + worksheet |
