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
