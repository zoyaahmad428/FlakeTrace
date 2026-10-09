# GenAI usage log — Member 2 (Search & Verification)

Format follows [[genai-log-m3]]: what was asked, what was retained, what I changed, how it was
verified, errors found, rejections.

## 2026-10-09 — Repository restructure and Mid Eval set-up

**Tool:** Claude Opus 5.5 (claude.ai, with repository access) · **Level:** L2

**What I asked:** Read the Mid Eval documents (rubric, protocol, worksheet, GenAI guide, GCR
announcement), the defence decision and both repositories; then merge the vault into the code
repo, write team rules for three members using AI agents, set up CI, and update the vault for
the post-defence and Mid Eval stage.

**What was retained:** single-repo layout with history preserved (`git subtree`), `CLAUDE.md`,
`CONTRIBUTING.md`, PR template, CODEOWNERS, `.github/workflows/ci.yml`,
`docs/contracts/interfaces.md`, `docs/08-MidEval/*`, `docs/09-Team/*`, ADR-001, folder READMEs.

**What I changed:** *fill after reviewing the PR with the team.*

**How it was verified:**
- Python CI steps run locally: 55 unit tests pass; `yield_report.py` runs on the real manifest.
- Workflow YAML parses; two jobs (`python-eval`, `fixture-build`).
- The `fixture-build` job could not run where Claude worked (Maven Central blocked); it
  first ran on GitHub Actions on PR #1 (run `37926797625`) and every step passed.

**Errors found:**
- `eval/README.md` documents `python3 -m unittest discover -s eval/tests`, which fails because
  `eval/tests` has no `__init__.py`. CI uses explicit module names instead. Reported to M3
  rather than edited, since `eval/` is M3's folder.
- Member numbers for Zoya and Zarpash were inferred, not stated — flagged for confirmation in
  `docs/09-Team/members.md`.

**Rejections:** Claude's question about moving the repo to a GitHub organisation was unclear;
deferred.

Ownership checkpoint: I must be able to explain the CI workflow line by line, the branch
protection rules, and the `OrderRunner` contract before the evaluation.

## 2026-10-09 — Commit protocol: members commit, agents hand over

**Tool:** Claude Opus 5.5 · **Level:** L2

**What I asked:** a hard rule that AI agents never commit or push; after each finished piece
of work the agent updates every affected doc and gives the member the exact commit commands
with a meaningful title and body.

**What was retained:** `CLAUDE.md` §3 (hard rule, when to hand over, message format) and new
§5 (which docs to update for which kind of change); matching sections in `CONTRIBUTING.md`,
`docs/09-Team/claude-guide.md` and the PR template.

**Why:** two problems found today — Zoya's PR #2 commits were authored as "Claude", and my
own restructure commits used an email not on my GitHub account, so neither was credited to
a member. A member running the commit after reading the diff is ownership evidence; an agent
commit is not.

**How it was verified:** read through the changed files; section numbers and cross-references
checked (`grep` for `§` in `CLAUDE.md`). No code changed, so no tests apply.

**What I changed:** *fill after review.*

**Note:** this change was handed to me as a patch to apply and commit myself — the first use
of the new rule.

## 2026-10-09 — W6 design: order runner (ADR-002) and implementation plan

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** propose at least two designs for `OrderRunner.run_ordered` (JUnit 4, one
fresh JVM per call, exact order), with trade-offs, classpath without new dependencies, and
portability on Windows/WSL/CI; stop for my choice; then write the plan.

**What was retained:** option A — Python `OrderRunner` + JUnitCore harness (ADR-002); the
implementation plan in `docs/superpowers/plans/2026-10-09-order-runner.md`.

**What I decided:** chose A over Maven Surefire (cannot honour a method-level order across
classes) and an all-Java runner (second language boundary with `eval/`).

**How it was verified:** a throwaway spike (not committed) compiled the harness against the
fixture's own classpath and ran F1 on my laptop (JDK 21): victim alone PASS; polluter then
victim FAIL `java.lang.AssertionError`; reversed order PASS.

**Errors found:** the ADR first said `javac --release 8`; the spike showed `-source 8 -target 8`
works on both JDK 8 and 21, so the ADR was corrected. Maven was not installed on my laptop —
installed 3.10.0 and added to user PATH.

**What I changed:** *fill after reviewing the ADR.*
