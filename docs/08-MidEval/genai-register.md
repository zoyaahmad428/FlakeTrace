# GenAI register and prompt journal

Required by the *FYP GenAI Use and Assessment* guide and Form 3 criterion 8 — **the tool-use
item scores 0 until full disclosure is submitted.** Using AI does not reduce marks;
concealment, uncritical acceptance and inability to explain do.

Policy context and the four-point ownership standard: [[00-Meta/ai-usage-log]].

## Levels (classify per artefact, not per project)

| Level | Meaning | What the member must show |
| --- | --- | --- |
| L1 Supportive | Grammar, formatting, brainstorming, minor debugging hints | Led the work, can explain it |
| L2 Assisted | Significant code, tests, diagrams or report text generated | Reviewed, modified, tested, can fully explain |
| L3 Core-assist | AI produced a major module or core feature | What AI produced, what you added, why it works, its limits |
| L4 Substituted | AI effectively did it and you cannot explain or modify it | Must never be presented as own work — marks may be capped at 50% |

## Register — one row per materially assisted artefact

| Date | Member | Tool / model | Level | Artefact | Output used | Student contribution | Verification | Rejected / corrected | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-09-08 | M2 | Claude | L2 | `docs/` vault structure and notes (built from project documents) | Note structure and summaries | Selected sources, organised structure, corrected slide structure | Read against source documents | Slide structure corrected (commit `3ec7d7d`) | Vault commits `cad960b`–`3ec7d7d` |
| 2026-10-08 | M3 | Claude Sonnet 5 | L2 | `fixtures/od-fixture`, `eval/` phases 0–5 | See per-session log | See per-session log | Real Maven runs in Docker; statsmodels cross-check | Wilson test tolerance corrected; schema `oneOf` bug fixed | [[genai-log-m3]], [[evidence-m3]] |
| 2026-10-09 | M2 | Claude Opus 5.5 | L2 | Single-repo restructure, CI workflow, CLAUDE.md, CONTRIBUTING, `docs/08-MidEval/`, `docs/09-Team/`, ADR-001 | Drafts of all listed files | Chose single-repo and PR+1 review; *add your edits after review* | Python CI steps run locally (55 tests pass); both CI jobs passed on GitHub Actions, run `37926797625` on PR #1 | *record any changes you make* | This PR |
| 2026-10-09 | M2 | Claude Opus 5.5 | L2 | ADR-002 (order-runner design), W6 implementation plan | Design alternatives, ADR text, plan | Chose option A; reviewed ADR | Spike on F1 (not committed): alone PASS, after polluter FAIL | ADR `--release 8` corrected to `-source 8 -target 8` | [[genai-log-m2]] |

## Prompt journal — significant interactions only

Keep cases where a suggestion was **challenged, rejected or corrected** — a journal where
everything was accepted suggests unverified use.

| Date | Member | Task | Prompt summary or transcript link | Output retained | Review / modification / rejection |
| --- | --- | --- | --- | --- | --- |
| 2026-10-09 | M2 | Plan Mid Eval and team structure | Asked Claude to read Mid Eval documents and both repos, propose structure | Repo layout, rules, Mid Eval docs | Repo-owner question was unclear and left undecided; *add more* |

## Per-member detail

Detailed session logs live in `docs/genai-log-m<N>.md`. This register is the summary the
supervisor reads.
