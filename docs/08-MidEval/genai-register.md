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
| 2026-10-09 | M2 | Claude Opus 5.5 | L2 | ADR-003 (order-runner design), W6 implementation plan | Design alternatives, ADR text, plan | Chose option A; reviewed ADR | Spike on F1 (not committed): alone PASS, after polluter FAIL | ADR `--release 8` corrected to `-source 8 -target 8` | [[genai-log-m2]] |
| 2026-10-09 | M2 | Claude Opus 5.5 | L2 | `runner/harness/FtHarness.java`, `runner/order_runner.py`, `runner/tests/test_order_runner.py` (W6 hand-over 1) | Harness, runner and tests from the ADR-003 plan | Chose the design; *add your edits after review* | `py -m unittest -v runner.tests.test_order_runner` → 8 OK; mutation check failed as expected | ADR numbering clash with M1's ADR-002 found and renumbered to ADR-003 | [[genai-log-m2]], [[evidence-m2]] |
| 2026-10-09 | M2 | Claude Opus 5.5 | L2 | `runner/order_runner.py` failure paths, 9 tests (W6 hand-over 2) | Crash/timeout/skip/duplicate handling and tests | *add your edits after review* | Tests seen failing first (5 failed, 4 already passed); then 17 OK | Real JVM crash and @Ignore only tested via hand-written result lines (fixture has none) | [[genai-log-m2]], [[evidence-m2]] |
| 2026-10-09 | M2 | Claude Opus 5.5 | L2 | `runner` CI job (W6 hand-over 3) | Workflow job, docs | *add your edits after review* | Local skip-vs-fail switch check; GitHub Actions run `37957537495`: runner job 17 tests OK on JDK 8 | — | [[genai-log-m2]], [[evidence-m2]] |
| 2026-10-09 | M2 | Claude Opus 5.5 (reviewer agent + author session) | L2 | W6 final review; fixes in `runner/order_runner.py`, `runner/tests/` | Review findings, 3 fixes, probe tests | *add your edits after review* | 3 new tests failed first; 22 OK after | Docs overclaim on JDK-independent signatures corrected; 5 minors deferred | [[genai-log-m2]], [[evidence-m2]] |
| 2026-10-09 | M2 | Claude Opus 5.5 | L2 | ADR-004 (W7 design), W7 implementation plan | Design options, ADR text, plan | Chose discovery+override, one-by-one search, n = 20, module layout | Spike on fixture (not committed): all five cases matched ground truth | N2 rate assumption (~50%) corrected to measured 18/60 on Windows | [[genai-log-m2]] |
| 2026-10-09 | M1 | Claude (Claude Code) | L2 | `docs/contracts/resource-evidence.md` (Phase 1 contract + invocation), `evidence/javap-dumps/phase1-f1-f2.txt`, POC junk-file cleanup | Contract text, check scripts, cleanup commands | Chose javap over ASM and the command shape; decides default depth; *add your edits after review* | Fixture compiled in JDK 8 image; example offsets checked against javap; projections validated against schema; cleanup count 45 → 0 | First commits were authored as "Claude" (fixed: member commits only); a broken staging simulation was redone; two unsupported claims removed | [[genai-log-m1]], [[evidence-m1]] |
| 2026-10-09 | M1 | Claude (Claude Code) | L3 | `evidence/extract.py`, `evidence/tests/` (Phase 2: depth-1 extraction, lifecycle attribution) | Extractor and tests generated | Chose fresh code (a1), default depth 2, the self-test cases; *add your edits after review* | 9 unit tests OK on JDK 8 and JDK 21 javap; offsets cross-checked by hand against JDK 8 `javap -c -p`; mutation check | Annotation constant-pool padding bug found on JDK 8 and fixed | [[genai-log-m1]], [[evidence-m1]] |

## Prompt journal — significant interactions only

Keep cases where a suggestion was **challenged, rejected or corrected** — a journal where
everything was accepted suggests unverified use.

| Date | Member | Task | Prompt summary or transcript link | Output retained | Review / modification / rejection |
| --- | --- | --- | --- | --- | --- |
| 2026-10-09 | M2 | Plan Mid Eval and team structure | Asked Claude to read Mid Eval documents and both repos, propose structure | Repo layout, rules, Mid Eval docs | Repo-owner question was unclear and left undecided; *add more* |

## Per-member detail

Detailed session logs live in `docs/genai-log-m<N>.md`. This register is the summary the
supervisor reads.
