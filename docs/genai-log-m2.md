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

## 2026-10-09 — W6 design: order runner (ADR-003) and implementation plan

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** propose at least two designs for `OrderRunner.run_ordered` (JUnit 4, one
fresh JVM per call, exact order), with trade-offs, classpath without new dependencies, and
portability on Windows/WSL/CI; stop for my choice; then write the plan.

**What was retained:** option A — Python `OrderRunner` + JUnitCore harness (ADR-003); the
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

## 2026-10-09 — W6 hand-over 1: harness + F1 proof

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** implement Task 1 of the W6 plan — the JUnitCore harness, the Python
`OrderRunner`, and tests that prove F1's victim passes alone and fails after its polluter in
one JVM.

**What was retained:** `runner/harness/FtHarness.java`, `runner/order_runner.py`,
`runner/tests/test_order_runner.py`, `docs/04-Implementation/sandbox-runner.md`.

**How it was verified:** test written first and seen failing (`ModuleNotFoundError`); then
`py -m unittest -v runner.tests.test_order_runner` → 8 tests OK; the F1 test was deliberately
broken (order reversed) and failed, then restored and passed. `git status --short fixtures/`
empty — fixture source untouched.

**Errors found:** Member 1 had merged their own ADR-002 first; ours was renumbered to ADR-003
and every reference updated. During the merge of `main`, a local merge commit kept conflict
markers in `genai-register.md`; fixed by taking the clean GitHub resolution.

**What I changed:** *fill after reading the diff.*

## 2026-10-09 — W6 hand-over 2: every test always reported

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** implement Task 2 of the W6 plan — a crash, timeout, skipped test, misspelt
test or duplicate must never make a test disappear from the result.

**What was retained:** the new `parse_results` (incomplete lines ignored, `SKIP` →
`flaketrace.NotExecuted`, missing tests filled in) and `run_ordered` (duplicate check, empty
order, timeout → `flaketrace.Timeout`, early exit → `flaketrace.JvmCrash`); 9 new tests; claims
ledger row E8.

**How it was verified:** the 9 tests were added first: 5 failed for the predicted reasons and
4 already passed because the harness handled them (recorded in [[evidence-m2]]). After the
change: `py -m unittest -v runner.tests.test_order_runner` → 17 tests OK.

**Errors found:** none in the code. Gap stated honestly: a real JVM crash and a real `@Ignore`
are only tested through hand-written result lines, because the fixture has no such test.

**What I changed:** *fill after reading the diff.*

## 2026-10-09 — W6 hand-over 3: runner tests in CI

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** add the runner's tests to CI on JDK 8 so they can never be skipped silently,
then record the real CI result and close W6.

**What was retained:** the `runner` job in `.github/workflows/ci.yml` with
`FLAKETRACE_REQUIRE_JVM=1`; the test command in `README.md` and `CLAUDE.md` section 8.

**How it was verified:** locally, with java/mvn hidden from PATH the tests skip without the
switch and fail with it. On GitHub Actions run `37957537495` (PR #10) all three jobs passed;
job `runner` on JDK 8: `Ran 17 tests in 16.911s — OK` (I copied this line from the job log,
which needs a signed-in account; Claude read the job/step status from the public API).

**Errors found:** none. Noted for Member 1: `evidence/tests/` is not yet run by CI.

**What I changed:** *fill after reading the diff.*

## 2026-10-09 — W6 final review and fixes

**Tool:** Claude Opus 5.5 (Claude Code) — a separate reviewer agent read the whole branch;
the session that wrote the code fixed the findings · **Level:** L2

**What was found:** no critical issues; important: (1) form-feed in a message misreported as a
JVM crash, (2) a cut-off result line could still be parsed, (3) tests ran in the caller's
directory, (4) docs overclaimed JDK-independent signatures. Five minor items deferred (listed
in [[evidence-m2]]).

**What was retained:** fixes for 1–3 with a failing test first for each; `ProbeTest.java` test
asset; reworded docs for 4.

**How it was verified:** 3 new tests failed before the fix, as predicted; 22 tests OK after.

**What I changed:** *fill after reading the diff.*

## 2026-10-09 — W7 design: ADR-004 and implementation plan

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** design W7 (victim-alone check, polluter search, repeated-run counts, source
hash, execution record) with options, then write the spec and plan.

**What I decided:** the original order is discovered like Surefire with an explicit-order
override; one-by-one polluter search with a priority hook (multi-polluter cases go to W10);
default n = 20 (proposed answer to I3, needs M3); small single-purpose modules with a
recording wrapper.

**What was retained:** ADR-004, `docs/superpowers/plans/2026-10-09-w7-diagnosis-runs.md`.

**How it was verified:** a throwaway spike (not committed) ran the full design on the
fixture: F1 and F2 found the ground-truth polluter, F3 ended NO_SINGLE_POLLUTER after 12
candidates, N1 and N2 ended VICTIM_FAILS_ALONE; 55 tests passed in the spike. Wilson bounds in
the ADR computed with `eval.stats.wilson_interval`.

**Errors found:** I first assumed N2 fails ~50% of the time; measured 18/60 on Windows
(`System.nanoTime()` has 100-ns steps there). The N2 test uses n = 40 so it cannot flake.

**What I changed:** *fill after reviewing the ADR.*

## 2026-10-09 — W7 Task 1: source-integrity check

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** implement Task 1 of the W7 plan — hash the project's files before and after
a diagnosis and name any difference.

**What was retained:** `runner/integrity.py`, `runner/tests/test_integrity.py` (code identical to
the plan, which was tested in the design spike).

**How it was verified:** tests run first and failed (`ModuleNotFoundError`); after the code,
`py -m unittest -v runner.tests.test_integrity` → 4 tests OK.

**Errors found:** none. Limitation noted: only the top-level `target/` is excluded (multi-module
projects).

**What I changed:** *fill after reading the diff.*

## 2026-10-09 — W7 Task 2: execution record

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** implement Task 2 — a wrapper that logs every JVM run to a JSON-lines file.

**What was retained:** `runner/recording.py`, `runner/tests/test_recording.py`, the
`.gitignore` entry.

**How it was verified:** tests failed first (`ModuleNotFoundError`); then 2 tests OK.

**Errors found:** none.

**What I changed:** *fill after reading the diff.*

## 2026-10-09 — W7 Task 3: discover the original order

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** implement Task 3 — list test classes like Surefire and ask JUnit for each
class's methods through a new `FtHarness --list` mode.

**What was retained:** the `--list` mode, `OrderRunner.list_methods`, `java_version`,
`runner/discovery.py`, `runner/tests/test_discovery.py`.

**How it was verified:** tests failed first (`ModuleNotFoundError`); then 28 tests OK (6 new +
22 W6 tests still passing). Printed the real fixture order (13 methods) into [[evidence-m2]].

**Errors found:** none; noted that JUnit's method order inside a class is neither source nor
alphabetical.

**What I changed:** *fill after reading the diff.*

## 2026-10-09 — W7 Task 4: reproduce, polluter search, repeat

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** implement Task 4 — reproduce the original failure, search for one polluter,
count repeated runs.

**What was retained:** `runner/search.py`, `runner/verify.py`, `runner/tests/test_search.py`.

**How it was verified:** tests failed first (`ModuleNotFoundError`); then 9 OK; mutation check
on the "a crash is never the reference" rule made its test fail, restored → OK.

**Errors found:** none.

**What I changed:** *fill after reading the diff.*
