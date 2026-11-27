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

**What I changed:** Reviewed the restructure with Zoya and Zarpash; left the GitHub-organisation question deferred because it was unclear; had M1 and M3 confirm their member rows.

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

**What I changed:** Asked for the "agents never commit" rule myself after spotting Zoya's commits authored as "Claude" and my own commits under the wrong email; applied this change and committed it myself, the first use of the rule.

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

**What I changed:** Chose option A (Python + JUnitCore harness) over Maven Surefire and an all-Java runner; installed Maven 3.10.0 and added it to PATH.

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

**What I changed:** Read the diff and accepted it as written; confirmed the fixture source was untouched.

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

**What I changed:** Accepted; agreed to state openly that real JVM crashes and `@Ignore` are only tested with hand-written lines.

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

**What I changed:** Copied the CI result line (`Ran 17 tests ... OK`) from the GitHub job log myself, since Claude could not read it.

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

**What I changed:** Accepted the fixes for the three important findings and the doc rewording; agreed to defer the five minors.

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

**What I changed:** Chose discovered order with an override, one-by-one search with a priority hook, n = 20, and small single-purpose modules.

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

**What I changed:** Read the diff; accepted.

## 2026-10-09 — W7 Task 2: execution record

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** implement Task 2 — a wrapper that logs every JVM run to a JSON-lines file.

**What was retained:** `runner/recording.py`, `runner/tests/test_recording.py`, the
`.gitignore` entry.

**How it was verified:** tests failed first (`ModuleNotFoundError`); then 2 tests OK.

**Errors found:** none.

**What I changed:** Read the diff; accepted.

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

**What I changed:** Read the diff; accepted; noted that JUnit's method order is not alphabetical.

## 2026-10-09 — W7 Task 4: reproduce, polluter search, repeat

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** implement Task 4 — reproduce the original failure, search for one polluter,
count repeated runs.

**What was retained:** `runner/search.py`, `runner/verify.py`, `runner/tests/test_search.py`.

**How it was verified:** tests failed first (`ModuleNotFoundError`); then 9 OK; mutation check
on the "a crash is never the reference" rule made its test fail, restored → OK.

**Errors found:** none.

**What I changed:** Read the diff; accepted.

## 2026-10-09 — W7 Task 5: diagnose() end to end

**Tool:** Claude Opus 5.5 (Claude Code, local) · **Level:** L2

**What I asked:** implement Task 5 — `diagnose()` and its tests on all five fixture cases.

**What was retained:** `runner/diagnose.py`, `runner/tests/test_diagnose.py` (with the N2 test
rewritten), `docs/04-Implementation/diagnosis-runs.md`, ADR-004 updates.

**How it was verified:** tests failed first (`ModuleNotFoundError`); the first real run failed on
N2; after investigation 12 tests OK and the full runner suite 55 OK; every case's real numbers
recorded in [[evidence-m2]]; mutation check on the alone-stop.

**Errors found:** the plan's N2 test assumed N2 fails on Windows at ~30% (from the spike). It
then failed 0/80: `System.nanoTime()` was a multiple of 100 (10 MHz timer). The test assumption
was wrong, not the code; the test now checks that no polluter is blamed. Also found and
documented: a rarely-failing flaky victim can produce a spurious polluter (exposed by low
verify counts).

**What I changed:** Accepted rewriting the N2 test after it failed 0/80 on my Windows laptop (timer precision).

## 2026-10-09 — W7 final review and fixes

**Tool:** Claude Opus 5.5 — separate reviewer agent on the whole branch; this session fixed
the findings · **Level:** L2

**What was found:** no critical issues; important: `NOT_REPRODUCED` counts disagreed with the
ADR; a record folder inside the project broke the integrity check; docs said CI was pending
after it had passed. Seven minor items deferred (listed in [[evidence-m2]]).

**What was retained:** a `record_dir` guard in `diagnose()` with a test that failed first; a
test pinning the crash-only `NOT_REPRODUCED` counts; ADR/README/note wording made to match the
code; CI run `37971869749` recorded.

**How it was verified:** the record-folder test failed before the guard and passed after; full
runner suite 57 OK.

**What I changed:** Accepted the `record_dir` guard and wording fixes; agreed to defer seven minors.

## 2026-10-10 — CI job for Member 1's evidence tests

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** read the PRs merged since W7 (#12–#18) and the M1/M3 answers, then add the
`evidence` CI job Member 1 asked for, and tick ADR-001 and ADR-002.

**What was retained:** the job as Member 1 specified it (JDK 8, compile fixture and self-test,
`FLAKETRACE_REQUIRE_JVM=1`), plus pip caching as in `python-eval`.

**How it was verified:** the job's commands run locally: 27 OK, none skipped (22 skipped
before). With javap pointed at a missing file the run fails (4 failures, 4 errors), so the job
cannot pass by skipping. CI on JDK 8 not yet run.

**What was found while reading the merged PRs:** `eval/reports/README.md` says `diagnose()`
makes `execution_record_reference` absolute; it does not (`runner/diagnose.py:103` uses
`record_dir` as given; the integration script passes an absolute folder). `eval/report.py`
duplicates Member 1's `find_edges`/`report_fields`. Claim E1 as rewritten in PR #18 says Surefire
is used for compiling, which is wrong. Raised with the members, not edited (not M2's folders).

**What I changed:** Added the job exactly as Member 1 specified; ticked ADR-001 and ADR-002; raised three problems in M1's and M3's areas with them instead of editing their folders.

## 2026-10-10 — N2 test back to `VICTIM_FAILS_ALONE`

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** bring the N2 test and docs in line with Member 3's N2 fix (PR #14).

**What was retained:** the tightened N2 test; ADR-004, implementation note, demo plan and claim E9
wording.

**How it was verified:** three real N2 diagnoses first (all `VICTIM_FAILS_ALONE`); the new test
passed; a mutation of the alone rule made it fail (`POLLUTER_FOUND`); full runner suite 57 OK.

**What was wrong:** to undo the mutation the agent ran `git checkout -- runner/diagnose.py`,
which CLAUDE.md forbids agents to run. It discarded only the agent's own one-line edit; reported
to the member at the time.

**What I changed:** Accepted; was told the agent had run a forbidden `git checkout`, and confirmed it only undid its own one-line edit.

## 2026-10-10 — W9 CLI design (ADR-005)

**Tool:** Claude Opus 5.5 (brainstorming) · **Level:** L2

**What was asked:** design the W9 end-to-end command after Member 3 built report assembly
(PR #13, #21).

**Decisions made by Member 2:** one victim per run, for the demo and real use (A); no report and
exit 3 when `assemble_report` cannot build one (A); a Python module `py -m runner diagnose` now,
the installable `flaketrace` command deferred to a later iteration (M2 wants it).

**What was retained:** ADR-005 — flow, options, exit codes 0/1/2/3, tests, and the `runner` CI job
needing `eval/requirements.txt`.

**What was argued:** Member 2 questioned whether `py -m runner` is "production". Agreed that the
launch method is not, but behaviour is; a proper install needs a team-wide package rename and the
container decision, so it is recorded as deferred with its constraints.

**What I changed:** Chose one victim per run, exit code 3 when no report can be built, and `py -m runner` now with the install later; questioned whether `py -m runner` counts as "production".

## 2026-10-10 — W9 Task 1: the diagnose command

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** implement Task 1 of `docs/superpowers/plans/2026-10-10-w9-diagnose-cli.md`.

**What was retained:** `runner/cli.py`, `runner/__main__.py`, 11 fast tests, the `runner` CI job's
install step, as planned.

**How it was verified:** tests failed first (module missing), then 11 OK; mutation of the evidence
condition made the report tests fail; full runner suite 68 OK.

**What I changed:** Read the diff; accepted.

## 2026-10-10 — W9 Task 2: real runs and docs

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** Task 2 of the W9 plan — real fixture tests for the command, docs.

**What was retained:** 5 real-run tests; `runner/README.md` command section;
[[04-Implementation/diagnose-cli]]; README/CLAUDE.md command line; demo plan, iteration plan,
members, claim E12 (numbered E10 until merging main, where M1 had added E10 and E11).

**How it was verified:** 5 real runs OK; removing the evidence step made the F2 test fail; full
suite 73 OK; F1 run by hand.

**What was wrong:** a Python escape (`\2…` in a string) wrote a control character into the
README's sample paths; found by reading the file back, fixed, and every edited file scanned.

**What I changed:** Accepted; ran F1 through the new command by hand.

## 2026-10-10 — W9 final review and fix

**Tool:** Claude Opus 5.5 (author session) + a separate reviewer agent · **Level:** L2

**What was found:** one important issue — broad `ValueError`/`RuntimeError` catching could hide
internal bugs as user errors; six minors deferred (listed in [[evidence-m2]]).

**What was retained:** `DiagnoseInputError` and `ToolError`; the CLI catches only those; a test
that failed first on behaviour; ADR-005 and notes updated.

**What was wrong:** another string-escape slip wrote a non-ASCII byte into a test; caught by the
import error and fixed with `bytes([0xFF])`.

**What I changed:** Accepted narrowing the error catching; then asked for every deferred minor to be fixed too.

## 2026-10-10 — W9 review minors fixed

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** Member 2 asked to fix every deferred review minor that could cause a problem later.

**What was retained:** records-is-a-file refused before Maven; victim checked before any record is
written; Java-name check on `--victim`; discovery timeout → exit 1; `summary()` guard; two summary
tests. Schema `ValidationError` left as a traceback on purpose (a pipeline bug), recorded in ADR-005.

**How it was verified:** each new test failed first (or, for the leftover-record check, failed when
the new check was removed); fast tests 25 OK; full runner suite 78 OK.

**What was wrong:** a `\n` escape in generated test code became a real line break (syntax error);
fixed by editing the file directly. An old stray form-feed character in this log (W6 entry) was
replaced with the text `\f`.

## 2026-10-10 — Claim E1 and a JUnit 3 test

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** fix claim E1's wording (Member 1's suggestion) and back its JUnit 3 part with a
test through our own harness.

**What was retained:** `LegacyJUnit3Test.java`, two tests in `TestOrderRunnerOnProbes`, the E1 and
scope-boundary wording, the README limitation line.

**How it was verified:** a scratchpad probe first; the tests passed (existing behaviour); a reversed
order made the pollution test fail; full runner suite 59 OK.

**What I changed:** Used Member 1's suggested wording for E1; accepted the JUnit 3 test.

## 2026-10-10 — W10 design (ADR-007)

**Tool:** Claude Opus 5.5 (brainstorming) · **Level:** L2

**What was asked:** design W10 (deletion minimisation, F3's two polluters).

**Decisions made by Member 2** (asking each time for what is best for the product as a whole):
produce a real F3 report with the agreed "first edge shown, rest in limitations" rule (A); `ddmin`
over bisection and one-at-a-time deletion; reuse `POLLUTER_FOUND` for several polluters; require
evidence for every polluter before `VERIFIED`.

**What was retained:** ADR-007 — flow, `ddmin` rules, evidence rule, limitations (single-run
checks, no budget, 1-minimal only), verification plan.

**What I changed:** Chose a real F3 report, `ddmin` over bisection, reusing `POLLUTER_FOUND`, and evidence for every polluter before `VERIFIED`.

## 2026-10-10 — W10 Task 1: `ddmin`

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** Task 1 of `docs/superpowers/plans/2026-10-10-w10-ddmin.md`.

**What was retained:** `runner/minimise.py` and 11 fake-runner tests, as planned.

**How it was verified:** tests failed first (module missing), then 11 OK; removing the complement
step made 7 fail; full runner suite 91 OK.

**What was wrong:** the brainstorming estimate of 10–15 runs for F3's shape was low; the real count
on the fake is 25 (recorded, not the guess).

**What I changed:** Read the diff; accepted; noted the real run count (25) was higher than the estimate.

## 2026-10-10 — W10 Task 2: minimise in `run_steps`

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** Task 2 of the W10 plan.

**What was retained:** step 4 in `run_steps`, `minimise_runs`, the `"minimise"` record step, three
`run_steps` tests, the real F3 test, docs (README status table, diagnosis-runs note).

**How it was verified:** tests failed first on behaviour; real F3 found exactly the ground-truth
polluters (9 minimise runs); full suite 93 OK.

**What was wrong:** the plan updated the CLI's F3 test only in Task 3, so Task 2 broke it; caught by
predicting the full-suite result, fixed in Task 2 (ruling in the ledger).

**What I changed:** Accepted fixing the CLI's F3 test in this task instead of the next.

## 2026-10-10 — W10 Task 3: several polluters in the report

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** Task 3 of the W10 plan.

**What was retained:** `combine_fields`, per-polluter evidence in `resource_fields`, four combining
tests, the F3 report checks, docs and claim E14 (first numbered E13).

**How it was verified:** tests failed first; the real F3 command is `VERIFIED` with `flagB` in
`limitations`; evidence for the first polluter only made the F3 test fail; full suite 97 OK.

**What I changed:** Read the diff; accepted.

## 2026-10-10 — W10 final review and fixes

**Tool:** Claude Opus 5.5 (author session) + a separate reviewer agent · **Level:** L2

**What was found:** important: a one-off flaky failure blamed every earlier test; a resource written
by both polluters was called "not shown"; mixed-evidence wording conflicts with M3's generic line.
Minors: a resource named twice, a cost claim stronger than measured, E14 (then E13) marked SETTLED too early,
a missing one-test-prefix test, `minimise_runs` not in the report, an incomplete exit-3 message.

**What was retained:** re-check of the full order before `ddmin`; `combine_fields` de-duplication;
four tests that failed first; ADR-007, E14 and the note corrected; the exit-3 message rewritten.

**What was rejected:** changing M3's generic limitation line (eval/ is M3's) — raised with M3 instead.

**What was wrong (session):** one long shell command with a quote in its text failed to parse; nothing
was applied, checked with grep, redone from a script file.

**What I changed:** Rejected changing M3's limitation line in `eval/`; raised it with M3 instead.

## 2026-10-10 — W10: `analyse_pair` per polluter

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** analyse Member 1's and Member 3's messages and new PRs (#29–#38) for what is best
for the product, then switch the command to `analyse_pair` (ADR-006 follow-up).

**What was retained:** `analyse_pair` once per polluter; the depth note on named edges; the
`any_edge_found` flag for M3's PR #38; three tests that failed first; F3 offsets checked with `javap`.

**What was rejected:** Member 1's suggested one-line swap as written: it predates W10's several
polluters and would have let a deep edge on a second polluter go unmarked in the report.

**What I changed:** Rejected Member 1's one-line swap as written, because it would hide a deep edge on a second polluter.

## 2026-10-10 — W10 follow-up: minimisation in the summary

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** fix the deferred review minor (`minimise_runs` not shown), if it helps the product.

**What was retained:** one summary line when `ddmin` found the polluters, stating the shrink and
"1-minimal, not necessarily the minimum"; two tests that failed first; the F3 test checks it.

**What was rejected:** a new report field — the schema is Member 3's contract and the number does not
change the verdict.

## 2026-10-10 — Panel action A7: commit and OS in the execution record

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** make panel action A7 true before marking it complete.

**What was retained:** `environment(project)` and its use in the record header; two tests plus the F1
header check, all failing first; two mutation checks.

**What was rejected:** recording a dummy seed or container — neither exists, so the docs say so.

**What I changed:** Rejected recording a fake seed or container; the docs say they do not exist yet.

## 2026-10-10 — Panel actions A1, A3, A4, A7 marked complete

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** update the panel action register for Member 2's actions now that W7–W10 and the
A7 record change are done.

**What was retained:** A1, A3, A4 (M2's part; M1's was done) and A7 set to COMPLETE, each with evidence
links to merged PRs and recorded runs in [[evidence-m2]]; the summary rows updated. A5 (Member 3) and
A6 (Member 1) left open — not ours to close.

**How it was verified:** every cited test, file and PR checked to exist; A7 marked complete only after
the commit and OS were really recorded (previous commit).

**What I changed:** Left A5 and A6 open because they belong to M3 and M1.

## 2026-10-10 — ADR-008 design (NOT_REPRODUCED and order search)

**Tool:** Claude Opus 5.5 (brainstorming) · **Level:** L2

**What was asked:** a research-based design for failures that do not reproduce, "not because it is
simple".

**Decisions made by Member 2:** accept the real failing order (`--order`) plus valid shuffled orders as
fallback (C); 31 shuffles (Gruber et al.) over 10 or 20; one diagnosis flow over a separate command or
reusing the evaluation baseline.

**What was retained:** ADR-008 — flow, class-first shuffling, distinct-order counting, the schema
proposal for Member 3, fixture requests F4/N3, order of work.

**What was found while checking:** reference [12] (the 31-order figure) studies Python projects; the
ADR states its transfer to JUnit as an assumption instead of a finding.

**What I changed:** Asked for a research-based design, not the simplest one; chose `--order` plus shuffled orders, 31 shuffles over 10 or 20, and one diagnosis flow; accepted labelling the Python-study figure as an assumption.

## 2026-10-10 — Record agreed ADRs (I1, I3, I4, E14, ADR-007 wording)

**Tool:** Claude Opus 5.5 · **Level:** L1

**What was asked:** record what M1's and M3's ticks (PRs #43, #44) settled.

**What was retained:** `docs/contracts/interfaces.md` I1, I3, I4 marked answered with links to ADR-003,
-004, -005 (each agreed by all three); claim E14 SETTLED; ADR-007's evidence sentence corrected to
`analyse_pair` (stale text found by Member 1). I2 left to Member 1.

**How it was verified:** every ADR's agreement table read on `main`; the quoted Wilson bounds recomputed
(20/20 → 0.839, 19/20 → 0.764); the ADR links resolve.

**What I changed:** Left I2 for Member 1 to answer.

## 2026-10-11 — Runner tests independent of the fixture's size

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** fix our tests so Member 3's new fixture cases (F4, N3) do not break CI.

**What was retained:** three real-run tests now derive their counts from the real order or the fixture
sources; the failures reproduced first on M3's branch; full suite green on both fixtures.

**What was wrong:** (1) the first rewrite of the discovery test reused the include rule under test, so a
mutation failed only on an empty set — rewritten to read the sources independently. (2) The agent ran a
stray `git checkout --` with no path (forbidden for agents by CLAUDE.md; it changed nothing, the listed
modified files proved the edits were intact). (3) Restoring `runner/discovery.py` after a mutation wrote
LF endings; content was identical (empty diff) and the CRLF endings were put back.

**What I changed:** Accepted; checked that the agent's stray `git checkout` changed nothing.

## 2026-10-11 — ADR-008 Task 1: shuffled orders

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** Task 1 of `docs/superpowers/plans/2026-10-11-adr-008-runner-side.md`.

**What was retained:** `runner/orders.py` and 9 tests as planned.

**What was wrong:** one planned test sorted `TestIdentifier` tuples (a `TypeError`); fixed to a set
comparison with the same meaning (ruling in the plan ledger).

**How it was verified:** tests failed first; flat shuffling made the class-grouping test fail; full suite
117 OK.

**What I changed:** Read the diff; accepted.

## 2026-10-11 — ADR-008 Task 2: diagnosis tries shuffled orders

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** Task 2 of the ADR-008 runner-side plan.

**What was retained:** the shuffle phase, the always-run alone check, the six fields Member 3's report
code reads, given-order validation, seeds in the execution record; 10 tests that failed first; real F4
and N3 runs.

**How it was verified:** two mutation checks failed the right tests; full suite 127 OK.

**What I changed:** Read the diff; accepted.

## 2026-10-11 — ADR-008 Task 3: command options and F4/N3 reports

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** Task 3 of the ADR-008 runner-side plan.

**What was retained:** `read_order`, `--order/--shuffles/--seed`, the summary lines, 11 tests (incl.
real F4 and N3 through the command); docs, demo plan step 6b, W14, claim E15 (OPEN until CI).

**What was wrong:** (1) the summary said "given order" when the order was discovered — caught by
reading the real N3 output, fixed test-first; (2) a generated test contained a real BOM character
instead of the `\ufeff` escape — replaced with the visible escape.

**What I changed:** Accepted; the "given" vs "discovered" wording fix came from reading the real N3 output.

## 2026-10-11 — ADR-008 final review and fixes

**Tool:** Claude Opus 5.5 (author session) + a separate reviewer agent · **Level:** L2

**What was found:** important — crash-only runs summarised as "never failed"; UTF-16 order files
crashed; the unknown-test check untested. Re-graded to important for honesty: the starting order counted
as a shuffle, "(all possible)" claimed without proof, a never-failing order reported as the failing one.

**What was retained:** six fixes, each with a test that failed first; ADR-008 clarified; README row.

**What was wrong (session):** generated test code again turned `\r\n` escapes and `\` line
continuations into real line breaks; found by reading the file back and fixed before running.

**What I changed:** Agreed to treat three minors as important for honesty; deferred one minor.

## 2026-10-11 — Quadratic duplicate check in `read_order`

**Tool:** Claude Opus 5.5 · **Level:** L1

**What was asked:** fix the one deferred review minor too.

**What was retained:** a set for the duplicate check; a test with a 20,001-line order file.

**What was wrong:** the agent had called the minor "fine even for thousands of lines"; the new test
measured 33 s for 20,001 lines. After the fix: 0.094 s.

**What I changed:** Asked for the deferred minor to be fixed; the new test showed 33 s, so it was not cosmetic.
## 2026-10-11 — Docs sync after ADR-008 merged

**Tool:** Claude Opus 5.5 · **Level:** L1

**What was asked:** list what is left for each member, then prepare a docs-only PR fixing stale status text.

**What was retained:** ADR status lines set to `ACCEPTED` with the PRs that carried each tick; W14, W9, A1, A5, A7,
demo-plan, members and architecture status text matched to the merged code; F4 and N3 re-run on main to back the text.

**What was wrong:** panel action A7 said the seed was "not applicable — the runner never shuffles", false since PR #49;
the architecture status line still said the runner, collector, minimiser and CLI were not implemented.

**What I changed:** Ran both merges with M3's PRs (#52, #54) myself and agreed which version of each row to keep; asked Zarpash to review.

## 2026-10-11 — CDR wording audit (claim E6)

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** audit how the docs describe CDR (claim E6), then fix the inconsistencies.

**What was retained:** one sentence for CDR (suggested patch, checked on a disposable copy, a developer
applies, source never changed) used in the decision doc, weak points, claim E5, one-minute answers and
architecture; the exclusion named one way; "automated repair" removed from RQ7; the CDR gate now uses the
development benchmark, so the roadmap's CDR V1 timing is possible; E6 stays OPEN for the three documents
outside the repo.

**What was wrong:** nothing found wrong in the audit itself; the proposal, Rev 2 and the original deck could
not be checked because they are not in the repo.

**What I changed:** Decided to drop "held-out projects" from the CDR gate so the roadmap holds; asked Zarpash to confirm.

## 2026-10-11 — "What I changed" lines filled

**Tool:** Claude Opus 5.5 · **Level:** L2

**What was asked:** suggest a "What I changed" line for every entry, based only on what this log and the
repository record, then write them in.

**What was retained:** all 39 lines and 34 register cells, as suggested; one unconfirmed clause (whether I
changed my git email) left out.

**What I changed:** read all 39 suggested lines and confirmed each matches what I did before allowing them
to be written in.

## 2026-10-14 — Design of a web UI over the CLI (Iteration 2)

**Tool:** Claude Opus 5.5 in Claude Code · **Level:** L3

**What was asked:** whether the proposal-stage UI in `POC/` can show the current project, what it can and
cannot show screen by screen, and a design for connecting it to the real tool.

**What was retained:** the spec [[03-Design/specs/2026-10-14-ui-design]] and
[[03-Design/decisions/ADR-009-ui-over-cli]]: a Python backend that runs `py -m runner diagnose` and shows
only the report file it writes; live and open-report modes; all nine POC screens kept, with unbuilt parts
labelled "NOT BUILT YET — PLANNED FOR X" or "NOT BUILT — NOT IN CURRENT PLAN"; the POC's simulated data
(`sim.ts`, `recorded.json`, `flakyReproduces`) to be deleted.

**What was wrong:** Claude first said a live run takes minutes; the recorded timings in [[evidence-m2]] are
20–40 s. One label cited report Chapter 9 where the wording is in the Conclusion.

**What I changed:** chose both modes, the backend option, keeping every screen with labels, and building it
after the Mid; approved each of the five design sections and the written spec.

## 2026-10-14 — UI backend (ADR-009, plan Tasks 1–4)

**Tool:** Claude Opus 5.5 in Claude Code · **Level:** L3

**What was asked:** build the backend in `docs/03-Design/plans/2026-10-14-ui-plan.md` Tasks 1–4, test first.

**What was retained:** `ui/server.py` (job results from the CLI's exit code and report file only; one job at a
time; process-tree kill on timeout; HTTP API on 127.0.0.1), `ui/tests/fake_cli.py`, `ui/tests/test_server.py`
(27 tests, one real F1 run), the `ui` CI job.

**What was wrong:** the spec credited a 37.0 s run to F1; it was F3 (corrected). The plan's "20–40 s" estimate for
a live run was low: the real F1 run through the backend took about 50 s.

**What I changed:** reviewed and committed each task (`1ff0cca`, `7ba9765`, `5433c0b`, and Task 4's commit).

## 2026-10-15 — UI frontend and start script (ADR-009, plan Tasks 5–7)

**Tool:** Claude Opus 5.5 in Claude Code · **Level:** L3

**What was asked:** build the web app in `docs/03-Design/plans/2026-10-14-ui-plan.md` Tasks 5–7: the POC's look,
the report-to-screen mapping, the nine screens with open-report and live mode, `ui\start.cmd` and the docs.

**What was retained:** `ui/web/` (only the POC's styles and shared components copied; new state, API client and
screens), `src/lib/report.ts`, `labels.ts`, 26 frontend tests, `ui/start.cmd`, `ui/README.md`, doc updates.

**What was wrong:** the copied POC drawing said a polluter "writes, never restores", which the extractor does not
check (changed to "writes"); Vite listened only on IPv6 `localhost`, so `127.0.0.1:5174` did not answer (now bound
to 127.0.0.1); the "20–40 s" run estimate was low (50–66 s measured; text changed); `npm audit` flagged a build-time
package inherited from the POC lock file (fixed with `npm audit fix`).

**What I changed:** checked the screens in the browser (F3, N1, the NOT BUILT screens) and ran the live end-to-end
check from `ui\start.cmd` (F1 VERIFIED in about a minute, busy and missing-pom messages, N1); committed each task.

## 2026-11-13 — After the Mid: feedback read, vault updated, Iteration 2 designed

**Tool:** Claude Fable 5.2 (claude.ai, with a cloud copy of the repository) · **Level:** L3 —
the six design proposals and the plan below were drafted by the tool.

**What I asked:** read the official Mid result, the supervisor's five review documents and the
handbook's 3rd Edition; compare them with the repository; then update the vault so the team can
start executing — including improving the architecture and design where the review requires it.

**What was retained (all documentation; no code, no contract file changed):**
- `docs/10-Final1/` — README, Mid outcome, feedback register (FT001–FT022), action register in
  the handbook's Form 10 layout, Iteration 2 plan (W16–W34), scope inventory, supervisor agenda,
  ownership preparation, report v2 plan, demo plan.
- `docs/03-Design/decisions/ADR-010` to `ADR-015` — verdict contract v2, deletion evidence,
  execution semantics and reset boundary, evidence bundle with recount and replay, budget ledger
  and ranked search, resource intervention spike. All `PROPOSED`.
- `docs/05-Testing/real-case-protocol.md`; the meeting note of 2026-11-13.
- Updates to the vault README, status, roadmap, risk register, requirements, scope boundary,
  architecture, certificate contract, evaluation plan, fixture suite, claims ledger (section G),
  members, Claude guide, root `README.md` and `CLAUDE.md`; closed-record banners on `08-MidEval/`.

**How it was verified:**
- Both certification defects reproduced by the tool against `main` `7cf453d` with a scratch
  script (output and script in [[evidence-m2]]).
- Every code statement in the new documents was read from the source at `7cf453d`, with file and
  line; every POC number was read from the files under `POC/` (`alone.csv`, `scan_*.csv`,
  `replay.csv`, `decision_record_v3.md`).
- All wiki links and relative links in the changed files resolve (checked by script).

**Errors the tool made and corrected during the session:**
- It first assumed the fastjson cases FJ-01 and FJ-02 were *victims* and planned FJ-01 as the
  first real case. `POC/results/alone.csv` shows both fail alone 10/10 — they are *brittle*, which
  the product does not diagnose. The protocol now uses FJ-03, a true victim.
- Its first scope count was 41% and 66%; recounting the table gave 43% and 68%.
- It wrote that the synthetic-failure prefix was "duplicated"; it is one constant plus three string
  literals. Corrected in ADR-010.
- It wrote "eight of eleven held-out cases are brittle"; the file says nine.
- A demo row said turning off auto-deepening removes F2's edge; F2's edge is at the default depth,
  so only analysing at depth 1 removes it.

**Not verified, and marked so in the documents:** the poster and Final dates (estimated from the
handbook's week numbers); the scope weights; whether fastjson still builds; whether JUnit's class
request can be filtered and ordered as ADR-012 needs (a spike is planned); what "missing abstract"
refers to — our submitted PDF contains one.

**What I changed:** *to fill in after I and the team have reviewed the PR.*

Ownership checkpoint: before building, I must be able to explain without the page — the four
outcome categories and why two overlapping counts failed; what `ddmin` guarantees and what the
deletion check adds; what a fresh JVM does and does not reset; how the reserve is computed.

## 2026-11-14 — W16: qualify the retired claims in `runner/` and `ui/`

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L3 · **Branch:** `m2/w16-retire-claims`

**Asked:** build my Iteration 2 task list, then do W16 test-first: remove or qualify "1-minimal",
"mechanism"/"cause" for a static edge, "never modified"/"sandbox" and the unqualified alone count
in my folders, using the replacements in claims ledger section G.

**Kept:** the new test assertions (written and seen failing first), the `summary()` changes, the
`outcomeLabel()` helper, the Certificate and Graph sentences, and the docstring, README and
`04-Implementation` corrections.

**How it was verified:** see [[evidence-m2]] "W16": 5 CLI and 4 UI tests failed on the old code
for the expected reason, then the full runner (147), eval (85), UI backend (30) and UI (29)
suites passed, and the real F1 command printed the new wording.

**Errors found and corrected:** `docs/04-Implementation/diagnosis-runs.md` said a bystander kept by
a flaky `ddmin` trial is exposed by verify ×n. FT004 shows it is not — the longer sequence still
fails. Corrected. Test-first was knowingly skipped for the UI's fixed sentences, because a unit
test would only repeat a constant; they were checked by build and phrase search instead.

**What I changed:** *to fill in after reading the diff.*

Ownership checkpoint: why "alone 0/20" was misleading (it counts only same-signature failures);
why `VERIFIED (sequence)` and not plain `VERIFIED`; where the qualifier is added (one helper on each
side, `summary()` and `outcomeLabel()`), and how to change it.

## 2026-11-14 — W19 step 1: `RunTally` and the classifier in `eval/baseline.py`

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L3 · **Branch:** `m2/w19-runtally`

**Asked:** implement ADR-010 §1 in M3's `eval/baseline.py` (agreed with M3 on 2026-11-13), test
first, and make the runner use the one synthetic prefix.

**Decided by me** when Claude showed the options: tests go in `eval/tests/test_baseline.py`; a real
failure without a reference raises `ValueError` rather than counting as `OTHER`; add a `tally()`
helper so W18 and the recount checker share the counting rule.

**Kept:** `SYNTHETIC_PREFIX`, `PASS/MATCH/OTHER/INFRA`, `classify`, `RunTally`, `tally`, 14 tests,
and the import changes in four runner files.

**How it was verified:** tests failed first (import error), then 27 OK; three deliberate mutations
each caught by the intended tests; all runner (147), eval (99) and UI backend (30) tests OK. See
[[evidence-m2]].

**Errors found and corrected:** the first mutation script missed its target because
`eval/baseline.py` has CRLF line endings; the file was restored by the script and the check rerun.

**What I changed:** *to fill in after reading the diff.*

Ownership checkpoint: why `INFRA` is checked before the reference; why a tally must add up to `n`;
how `tally([20 different failures])` shows the FT003 defect that `repeat()` hid.

## 2026-11-14 — W18: tallies in the runner

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L3 · **Branch:** `m2/w18-tallies`

**Asked:** switch `repeat()`, `run_steps()` and `DiagnosisRuns` to ADR-010 tallies and rename the
inconclusive status, test first, without breaking M3's `eval/` code while M3 has no laptop.

**Decided by me:** of three options (tallies beside the old fields; replace and edit M3's files;
replace and wait for M3), I chose the first. Claude proposed the names `alone_tally` /
`sequence_tally` because `DiagnosisRuns.sequence` is already the test list.

**Kept:** `repeat()` and `repeat_without_reference()` returning tallies, `_runs()` filling the old
fields from the tallies, `INCONSISTENT` with the old name as an alias, eight new runner tests and
three updated ones, the ADR-010 implementation note.

**How it was verified:** see [[evidence-m2]] "W18": the tests failed first for the expected
reasons; afterwards runner 155, eval 99 and UI backend 30 tests OK; the scripted T1–T3 and a real
F1 run show the tallies.

**Errors found and corrected:** a first draft of `repeat_without_reference` chose the reference
with `classify(o, None)`, which raises on a real failure and, as written, always gave `None`; it was
rewritten before any test ran. One new test was wrong (its order `[V]` let the reproduce step
consume the scripted alone outcomes); fixed before the code was written.

**What I changed:** *to fill in after reading the diff.*

Ownership checkpoint: why the tallies sit beside the old fields for now and when they go; why the
runner still searches after `alone.other > 0`; why T1 is still `VERIFIED` end to end until W19.

## 2026-11-14 — W22 job 1: environment fields in the execution record

**Tool:** Claude Code (Claude Opus 5.5), superpowers brainstorming → writing-plans →
executing-plans (native) with test-driven-development · **Level:** L3 · **Branch:** `m2/w22-record-env`

**Asked:** brainstorm W22, then design, plan and build its first job (ADR-012 §6).

**Decided by me:** split W22 into four jobs in ADR-012's order; approved the short design and the
two-task plan; chose native execution. I left the probe choice to Claude, which chose asking the
test JVM (`FtHarness --env`) over Python's own values, because replay compares what the tests ran
under.

**Kept:** `FtHarness --env`, `parse_env`, `OrderRunner.jvm_environment()`, `git_state`,
`maven_version`, `tool_environment`, the new header keys, `command` passed from the CLI, 8 new tests.

**How it was verified:** see [[evidence-m2]] "W22 job 1": each new test failed first; runner 164,
eval and UI backend suites OK; a real F1 run's header shown in full.

**Errors found and corrected:** none in the code during this job. The design notes that the header
holds absolute paths, which ADR-013 must redact.

**What I changed:** *to fill in after reading the diff.*

Ownership checkpoint: why the timezone is asked of the JVM and how the `JAVA_TOOL_OPTIONS` test
proves it; why a failed probe gives `null` instead of stopping; where to add a new header field.

## 2026-11-14 — W22 job 2: JUnit spike (throwaway)

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L3 · **Branch:** `m2/w22-record-env` (docs only)

**Asked:** run ADR-012 §2's spike and record what it shows. **Kept:** only the findings, in ADR-012
§2 and [[evidence-m2]]; the spike code stayed in a scratch folder, as the ADR requires.
**Errors:** the first compile failed because Git Bash passed `/c/...` paths to Windows `javac`;
fixed with Windows paths — a command error, not a finding. **What I changed:** *to fill in.*

Ownership checkpoint: why JUnit 3 stays per-method (sorting silently ignored, and no class-level
lifecycle to lose); what the harness must do when `@BeforeClass` throws.

## 2026-11-14 — W22 job 3: class-grouped execution and the lifecycle control

**Tool:** Claude Code (Claude Opus 5.5), superpowers brainstorming → writing-plans →
executing-plans (native) → fresh review · **Level:** L3 · **Branch:** `m2/w22-record-env`

**Asked:** build ADR-012 §2–§3 on the spike's findings, and document it so M1 can run the control
when she has her laptop. **Decided by me:** approved the design and plan; left the default mode to
Claude, which kept `per-method` until M1's control run (ADR-012's own rule).

**Kept:** the harness `class-grouped` mode (`runBlock`), `OrderRunner(lifecycle=)`, `LIFECYCLES`,
`--lifecycle` through `diagnose` and the CLI, the lifecycle control as a Maven project, two probe
classes, 15 new tests, a CI step running the control under Surefire, M1's steps in the handover.

**How it was verified:** see [[evidence-m2]] "W22 job 3": tests failed first; two mutations each
caught; the control's three rows observed; runner 178, eval 99, UI backend 30 OK; real F1 run.

**Errors found and corrected:** Claude found that ADR-012 asked for a Surefire run of a class that
was not in any Maven project, and made the control its own small Maven project. It also renamed a
confusing variable it had introduced in job 1 (`command` reused in `cli.main`).

**What I changed:** *to fill in after reading the diff.*

Ownership checkpoint: how `runBlock` groups, filters and sorts; why JUnit 3 is excluded; what
happens when `@BeforeClass` throws; how the control proves the difference.

## 2026-11-14 — W22 job 3 follow-up: deferred review minors

**Tool:** Claude Code (Claude Opus 5.5), test-driven-development · **Level:** L3 ·
**Branch:** `m2/w22-record-env`

**Asked:** fix the four minors the job 3 review deferred. **Kept:** four tests (each seen failing
first) and four small harness fixes. **How verified:** [[evidence-m2]] "W22 job 3 follow-up":
runner 184, eval 99, UI backend 30 OK. **Errors:** the first insert of the tests turned `
`
escapes into real newlines (a script error), fixed before running. **What I changed:** *to fill in.*

## 2026-11-14 — W22 job 4: diagnose on a disposable copy

**Tool:** Claude Code (Claude Opus 5.5), superpowers brainstorming → writing-plans →
executing-plans (native) → fresh review · **Level:** L3 · **Branch:** `m2/w22-record-env`

**Asked:** build ADR-012 §4. **Decided by me:** approved the design. Claude made two calls on my
delegation: the CLI owns the copy (because evidence extraction needs the copy's compiled classes
after `diagnose()` returns) and `copy` is the CLI default (no change to how tests run).

**Kept:** `runner/workspace.py`, `integrity_of`, `diagnose(workspace=, origin=)`, `--workspace`,
13 new tests, doc and claims-ledger updates.

**How it was verified:** see [[evidence-m2]] "W22 job 4": tests failed first; runner 199, eval 99,
UI backend 30 OK; a real run left the project folder without `target/`.

**Found:** the Mid build wrote `target/` into the user's project — hidden because the integrity
check skips `target/`. **Review fixes:** multi-module hint, `--copy-parent` with UI clean-up after a
timeout, a warning for an undeletable copy, the missing `diagnose()`-level tests, no temp path in
errors, no traceback on a failed copy. **Errors:** Claude's own new test leaked two temp copies;
found by checking `%TEMP%`, fixed. **What I changed:** *to fill in after reading the diff.*

Ownership checkpoint: why the copy lives in the CLI and not in `diagnose()`; what `origin` is for;
what the two-part integrity line means; what the copy does not protect against.

## 2026-11-19 — PR #106 integration (M3's W19) and the CI line for PR #107

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L3 · **Branch:** `m3/w19-verdict-contract-v2`
(with M3's permission)

**Asked:** check what M1 and M3 pushed, then make both open PRs mergeable: merge `main` into #106,
resolve the two doc tables, use M1's `resource_edges`, answer `VERIFIED` without deletion checks,
and add the CI line #107 needs. **Decided by me:** the deletion answer Claude proposed (ADR-011 §2:
one polluter is deletion-verified by the alone check; two or more are `CANDIDATE` until W20); to do
the UI and Mid-report fixes on the same branch.

**Kept:** the merge resolution, `ci.yml` guarded compile line, `eval/report.py` edges and deletion
status, the schema's optional `depth`, `combine_fields` edges, `ui/web` schema v2 mapping and
Certificate text, `json_to_tex.py --reports`, `report.yml` reading the tag, regenerated reports,
updated tests.

**Errors found and corrected:** a JSON rewrite of the schema reformatted the whole file (498-line
diff) — restored and redone as a 5-line text edit; an unconditional CI line would have broken #106's
own `evidence` job — guarded; two test expectations were wrong (case of "Deletion"; the extra
`DELETION_EVIDENCE_INCOMPLETE` reason is the intended change).

**What I changed:** *to fill in after reading the diff.*

Ownership checkpoint: why one polluter's alone check counts as its deletion check; why F3 is
`CANDIDATE` now and becomes `VERIFIED` with W20; why the Mid report reads the tag.

## 2026-11-20 — A1: discovery reads the project's own Surefire includes

**Tool:** Claude Code (Claude Opus 5.5), superpowers brainstorming → writing-plans →
executing-plans (native) with test-driven-development · **Level:** L3 · **Branch:** `m2/a1-discovery-includes`

**Asked:** fix the discovery gap M3 found on fastjson (my standing prompt, item A1). **Decided by
me:** approved the design (approach A, read the effective POM via Maven, over parsing `pom.xml` or
dropping the name filter). **Kept:** the selection layer in `runner/discovery.py`,
`maven_test_classpath(effective_pom=)`, the wiring in `diagnose()`, the custom-includes test
project, 13 new tests. **Errors found and corrected:** two of Claude's own test expectations were
wrong (default excludes still apply when only includes are set; JUnit's method order is not
alphabetical); a Javadoc comment containing `**/` would have closed itself and broken the build —
caught before compiling. The fresh review found a critical bug Claude had written — the first
surefire `<plugin>` anywhere was read, so `pluginManagement` could win — and four important gaps;
all fixed test-first. I then asked for the seven minors to be fixed as well, not deferred; done
test-first. **What I changed:** *to fill in after reading the diff.*

Ownership checkpoint: why the effective POM and not `pom.xml`; why only `build/plugins` counts; how a pattern becomes a regex;
why unset excludes keep `**/*$*`; why unsupported settings are refused.

## 2026-11-20 — Follow-ups from M1's verification and M3's PR #109

**Tool:** Claude Code (Claude Opus 5.5), test-driven-development · **Level:** L3 · **Branch:**
`m2/after-verification`

**Asked:** review M1's PR #108 and M3's PR #109 against the iteration's goals, then act on their
notes to me. **Kept:** N2's expected rate read from its report; `class-grouped` as the default
lifecycle; README/CLAUDE.md Python floor and first-run download note; corrected handover step;
claim E14 qualified. **Checked rather than assumed:** the README already stated Python 3.11+ (M1's
note was half right); the real floor (3.10) was read from PyPI, not guessed; the pre-fetch command
was run before documenting it. **What I changed:** *to fill in after reading the diff.*

Ownership checkpoint: why N2 alone reads its rate from the report; why the default could flip only
after M1's independent control run.

## 2026-11-20 — CLI "other failure" count; N4 under class-grouped

**Tool:** Claude Code (Claude Opus 5.5), test-driven-development · **Level:** L3 · **Branch:** `m2/alone-summary`

**Asked:** act on M3's message (M1's W19 finding: the CLI alone line hides `other`) and M1's notes
(N4 not run under the new default; FT006 to `Partly`). **Kept:** one extra count on the existing
line, always printed so the two cases differ even at 0; test fixtures completed rather than the
code made lenient, since schema v2 requires `other`. **Checked rather than assumed:** the UI already
showed `other` (CLI-only gap); real N4 and F1 runs under the default. **What I changed:** *to fill in.*

Ownership checkpoint: why `other` is printed even when 0; why the fixtures, not `summary()`, were fixed.

## 2026-11-20 — CI: retry setup-java once

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L2 · **Branch:** `m2/ci-setup-java-retry`

**Asked:** stop the repeated `setup-java` tar failures. **Kept:** one retry per Java job and
`setup-java@v5`. **Rejected:** dropping `cache: maven` — unproven, since the log that would say
whether the cache or the JDK download failed was not readable. **What I changed:** *to fill in.*

Ownership checkpoint: why a retry is acceptable here (the failure is GitHub's, before our code runs)
and what would show the real cause (the step's log lines before the tar error).

## 2026-11-20 — W20 runner half: deletion checks

**Tool:** Claude Code (Claude Opus 5.5), brainstorming → writing-plans → executing-plans, test-driven
development · **Level:** L3 · **Branch:** `m2/w20-deletion-checks` · **Spec/plan:**
`docs/superpowers/specs/2026-11-20-w20-deletion-checks-design.md`, `docs/superpowers/plans/2026-11-20-w20-deletion-checks.md`

**Asked:** build the runner half of W20 against the agreed Interface 4. **Kept:** a separate
`runner/deletion.py`; labels from M3's `wilson_interval` and threshold, not a copy; drop only the
first `NOT_NEEDED` per round; verify the final set. **Rejected:** checks inside `run_steps` (too long to
test); repeating `ddmin` trials (ADR-011 §6). **Wrong and caught by the fresh review:** my design
named the record step `delete`, contradicting ADR-011 and ADR-014 (`deletion`, with the removed
test); the CLI and UI would have said things the new checks made false. All fixed test-first. **Also fixed:** `members.md` had duplicate rows for M1 and
M2 from an earlier merge — the stale ones were removed. **What I changed:** *to fill in.*

Ownership checkpoint: why only the first `NOT_NEEDED` test is dropped per round; why one polluter needs
no deletion runs; why F3 is still `CANDIDATE` today.

## 2026-11-20 — A2: verify M1's W21; stale "not shown" wording

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L2 · **Branch:** `m2/a2-verify-w21`

**Asked:** independently verify M1's W21 on this machine. **Kept:** reproduction from a clean `main`
worktree, including running M1's tests on the pre-change code to see them fail; a search of both
reports for causal wording. **Found:** a line in M1's code and one in mine that became false once
schema v2 showed every edge; fixed mine test-first, M1's sent to M1. **What I changed:** *to fill in.*

Ownership checkpoint: why a verifier runs the tests on the old code too; why "not shown" was false.

## 2026-11-20 — A3: M3's W26a premise on real fastjson; two runner fixes

**Tool:** Claude Code (Claude Opus 5.5), test-driven-development · **Level:** L3 · **Branch:** `m2/a3-fastjson-findings`

**Asked:** verify M3's fastjson premise independently. **Kept:** a checksum-verified portable JDK 8 in
the scratchpad (with permission); the real runner, pinned locale and timezone; a real CLI run of the
case A1 unblocked. **Wrong at first (mine):** the first run used JDK 21 because of a `PATH` mistake —
which exposed fix 1. **Found and fixed test-first:** the harness compile ran the project's annotation
processors; `java_version()` recorded the `JAVA_TOOL_OPTIONS` banner. **What I changed:** *to fill in.*

Ownership checkpoint: why fastjson needs JDK 8; why `-proc:none` is safe for FtHarness; why the
banner broke only `java_version`, not `jvm`.

## 2026-11-20 — A4: remove the old count fields and the alias

**Tool:** Claude Code (Claude Opus 5.5), test-driven-development · **Level:** L2 · **Branch:** `m2/a4-remove-old-counts`

**Asked:** remove the five count fields and `NO_SINGLE_POLLUTER` once `eval/` reads the tallies.
**Kept:** a search of every reader first; M3 asked before touching `eval/`; tallies made required.
**Rejected:** a three-step migration (defaults first, then M3, then removal) — one PR with M3's
agreement is simpler and leaves no half-state. **What I changed:** *to fill in.*

Ownership checkpoint: why both sides had to change in one PR; why the tallies are now required.

## 2026-11-20 — review of PR #129; deletion-status order; F3 docs

**Tool:** Claude Code (Claude Opus 5.5), test-driven-development · **Level:** L2 · **Branch:** `m2/f3-verified-followups`

**Asked:** analyse the merged PRs #125–#129. **Found:** #129 checked a short run count before
`INCONCLUSIVE`, against Interface 4's own ranking. **Kept:** M3's reading that a short run never gives
`VERIFIED`; only the order changed, test-first, with M3's agreement. Stale "F3 is `CANDIDATE`" lines in my
docs fixed; dated hand-over notes left as history. **What I changed:** *to fill in.*

Ownership checkpoint: why evidence against outranks missing evidence; why `-n 5` makes every check short.

## 2026-11-20 — W24 runner half: budget ledger

**Tool:** Claude Code (Claude Opus 5.5), brainstorming → writing-plans → executing-plans → TDD, one
fresh reviewer at the end · **Level:** L3 · **Branch:** `m2/w24-budget-ledger`

**Asked:** build W24's runner half. **Kept:** Interface 6 written first and agreed by M1 and M3 before
any code; the ledger as a wrapper around the runner (ADR-014 §1), so the search code does not count;
checks either run in full or are `NOT_RUN`. **Found:** the CLI summary would have crashed on a
`NOT_RUN` check. **What I changed:** *to fill in.*

Ownership checkpoint: why the reserve is `3 × n`; why a seconds limit cannot stop verification; why a
refused run must leave no `run` line (the recount).

## 2026-11-20 — W25 runner half: search policy

**Tool:** Claude Code (Claude Opus 5.5), brainstorming → writing-plans → executing-plans → TDD, one fresh
reviewer at the end · **Level:** L3 · **Branch:** `m2/w25-policy-code`

**Asked:** build W25's runner half, including ADR-014 §6 deepening (M2's choice, checked against FT007, ADR-014
and the real-case protocol first). **Kept:** Interface 7 agreed before code; the policy chosen once and passed into
the existing `priority` hook, so every step after the candidate order is the same (the review showed the blamed test can still differ when several tests pollute alone); the deepening loop tested on a fake ranker.
**What I changed:** *to fill in.*

Ownership checkpoint: why the policies reach the same endpoint; when deepening stops; why a fixture result is not
a contribution claim.

## 2026-11-20 — CLI follow-ups after #135 and #137

**Tool:** Claude Code (Claude Opus 5.5), test-driven-development · **Level:** L2 · **Branch:** `m2/w24-followups`

**Asked:** analyse M3's #135 and M1's #137 and do the follow-ups. **Kept:** two summary wordings, each test-first;
the dead "no report yet" text removed. **Left:** G2's status, which needs M3's agreement. **What I changed:** *to fill in.*

Ownership checkpoint: why a `BUDGET_EXHAUSTED` report's `reproduced:` numbers are not a verified sequence.

## 2026-11-21 — ranking-line notes, G2, Interface 6 step 3

**Tool:** Claude Code (Claude Opus 5.5), test-driven-development · **Level:** L2 · **Branch:** `m2/ranking-notes`

**Asked:** act on M1's and M3's merged PRs and M1's message. **Kept:** M1's per-candidate note carried into the
ranking line (agreed by M3); G2 settled with its scope; a real F2 pair at the same limit for items 1–3. **Declined:**
skipping ranking once the seconds limit is spent (saves little, needs another contract change). **What I changed:**
*to fill in.*

Ownership checkpoint: why "could not analyse" must not look like "no evidence"; why ranked fits in 70 and original does not.

## 2026-11-21 — W23, M2's half: bundle writer and replay

**Tool:** Claude Code (Claude Opus 5.5), brainstorming (with a builder check) → writing-plans → executing-plans → TDD,
one fresh reviewer at the end · **Level:** L3 · **Branch:** `m2/w23-replay-code`

**Asked:** start W23 without waiting for M3. **Kept:** Interface 8 written first and agreed (two clarifications from
the builder check); the runner writes bundles and M3 verifies; redaction refuses rather than leaks; replay never
searches. **Wrong at first (found by review):** the written comparison disagreed with the printed one; replay trusted
the unchecksummed manifest. **What I changed:** *to fill in.*

Ownership checkpoint: why the user name is matched only as a path part; why replay reads `n` from the record; why
"same" needs the same polluters.

## 2026-11-21 — F1 bundle, Interface 7 wording, G8

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L2 · **Branch:** `m2/interface7-g8-bundle`

**Asked:** act on M1's #144/#145 and her message. **Kept:** G8 settled only with its scope; the bundle made from a
clean checkout and with relative folders. **Found:** `core.autocrlf` would have broken every committed bundle's
checksum; `.gitattributes` added and a test that reads every committed bundle back. **What I changed:** *to fill in.*

Ownership checkpoint: why a committed bundle needs `-text`; why G8 is scoped.

## 2026-11-21 — A8/W31: supervisor agenda v2, action register v2, plan rows

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L2 · **Branch:** `m2/a8-supervisor-agenda`

**Asked:** prepare W31. **Kept:** every status checked against the feedback register's closing rule — moved to
`Partly` only where the work is built and reproduced by another member, never `Done` (that needs the supervisor);
the real-case ranking gap (FJ-03, M1's #145) put to the supervisor as a question rather than hidden; the agenda's
commitments ticked only where the item exists. Plan: the duplicate W18/W19 rows a merge had left removed, ✅ only where
the row's own "Done when" is met. **What I changed:** *to fill in.*

Ownership checkpoint: why nothing is `Done`; why §9 is on the agenda.

## 2026-11-21 — FT021 reset-sensitive control

**Tool:** Claude Code (Claude Opus 5.5), brainstorming → plan → TDD · **Level:** L2 · **Branch:** `m2/ft021-reset-control`

**Asked:** build the missing FT021 control, the best way for the long run. **Kept:** a separate control project
(the lifecycle control's Surefire run must keep passing); expectations as one table mirroring ADR-012 §1, so the
hardened container in FYP-2 changes one row; two file locations (temp folder, working directory) because that is
what `--workspace copy` does and does not cover; a same-JVM check so no reader passes vacuously. **Not done, on
purpose:** detecting leftover state during a diagnosis (needs the filesystem family, FYP-2). **What I changed:**
*to fill in.*

Ownership checkpoint: why a new JVM resets statics but not files; what `--workspace copy` does not protect.

## 2026-11-22 — ADR-016 revision, Interface 9, W35 pair mode

**Tool:** Claude Code (Claude Opus 5.5), brainstorming → plan → TDD · **Level:** L3 · **Branches:** `m2/adr-016`,
`m2/w35-pair-mode`

**Asked:** step back and judge ADR-016 without bias; then build what the team agreed. **Kept:** pair mode as an
explicit `--search pairs` (the first, automatic version was over-built); victim-only input with `--order` refused;
one re-run before a failing pair is adopted; one certification path for both modes (`_certify`); a `next:` line with
a time estimate measured from the run. **Rejected:** the automatic fallback and "all before" orders (FYP-2); a new
`runner/pairs.py` (`find_pair` sits beside `find_polluter`). **Wrong at first:** Interface 9 named a field `search`
that W25 already uses; a `tally()` with no reference cannot hold a real failure; a parameter named `runs` clashed with
a local. **What I changed:** *to fill in.*

Ownership checkpoint: why pair mode refuses `--order`; why a failing pair is re-run before it is adopted; what
`reproduced_by` tells a reader; why the `next:` estimate is only for the pairs.

## 2026-11-22 — W23 replay gaps from M1's reproduction

**Tool:** Claude Code (Claude Opus 5.5), brainstorming → plan → TDD · **Level:** L2 · **Branch:** `m2/w23-replay-gaps`

**Asked:** fix M1's findings 1, 2, 5, 6. **Kept:** real, quoted paths; "any FlakeTrace with eval/bundle.py" instead of
a second recorded commit (no contract change); `--project` from the subject; the OS row compares the Windows build.
**Rejected:** rewriting the committed bundles (evidence after the fact). **Wrong at first:** the assistant started
writing tests before the design was approved; the member stopped it, and the design was agreed first.
**What I changed:** *to fill in.*

Ownership checkpoint: why an absolute output folder is not written into `replay.md`; why the committed bundles keep
their old text.

## 2026-11-22 — W26b step 9; the test-output decoding bug

**Tool:** Claude Code (Claude Opus 5.5), systematic debugging → TDD · **Level:** L2 · **Branch:** `m2/w23-replay-gaps`

**Asked:** run step 9; then fix the decoding bug it surfaced. **Kept:** stop capturing output nobody reads (the
root cause) instead of a tolerant decoding (a symptom patch); a one-file probe like the others in
`runner/tests/resources/`; a test that sees the reader thread's failure through `threading.excepthook`, so it fails
on Windows too. **Not claimed:** the Linux behaviour was reasoned, not run. **What I changed:** *to fill in.*

Ownership checkpoint: why the outcomes were still right; why DEVNULL is the fix and `errors="replace"` would not be.

## 2026-11-22 — W35 follow-up: replay keeps the mode; agreed wording

**Tool:** Claude Code (Claude Opus 5.5), brainstorming → plan → TDD · **Level:** L2 · **Branch:** `m2/w35-followup`

**Asked:** fix M3's replay finding; record the two agreed Interface 9 wordings; settle E16. **Kept:** the mode read
from the checksummed record header, not `manifest.json`; a victim that now fails alone is `"order"`. **Rejected:**
inferring pair mode in `eval/report.py` (M3's file, and a guess where the record already says). **What I changed:**
*to fill in.*

Ownership checkpoint: why the record header, not the manifest; what a replay of a pair bundle now reports.

## 2026-11-24 — Replay takes the mode from the record

**Tool:** Claude Code (Claude Opus 5.5), systematic debugging → brainstorming → plan → TDD · **Level:** L2 ·
**Branch:** `m2/replay-old-pair-bundles`

**Asked:** fix M1's replay finding, the most logical way, not the easiest. **Kept:** design B — one source (the
checksummed header), a disagreeing report refused like `n`/`lifecycle`. **Rejected:** design A (trust the report,
fall back to the header), the assistant's first proposal: two sources with a precedence rule, a disagreement silently
believed; the member asked for the most logical design and B was chosen. **What I changed:** *to fill in.*

Ownership checkpoint: why `reproduced_by` follows from `search_mode` for every replayable bundle.

## 2026-11-24 — Every committed bundle verified by a test

**Tool:** Claude Code (Claude Opus 5.5), brainstorming → plan → TDD · **Level:** L2 · **Branch:** `m2/ci-verify-bundles`

**Asked:** a guard so a schema change can never silently break committed evidence again. **Kept:** the test in
`eval/tests/` beside the schema and verifier (M3 agreed), so the person changing them sees it fail locally.
**Rejected:** extending the runner test (M3 does not run it) or a CI-only step. **Wrong at first:** the re-enactment
validated v2 reports against v3, which also rejected newer bundles; rewritten to re-enact #164 exactly.
**What I changed:** *to fill in.*

Ownership checkpoint: why a test that re-enacts the incident proves the guard is not vacuous.

## 2026-11-27 — The web UI as the Final demo

**Tool:** Claude Code (Claude Opus 5.5), brainstorming (with a builder check) → plan → TDD, native · **Level:** L3 ·
**Branch:** `m2/ui-demo`

**Asked:** the UI is the demo; make it run what the demo shows and label only what is true. **Kept:** approach B
(run options + committed bundles with a fresh verify) and step 6 option A (check a folder by path), both the member's
choices; the CLI's names, defaults and refusals in the server; one rule (`reproducedKind`) for the Diagnosis step and
the evidence table; a UI run's bundle never in the repository. **Found by the builder check:** the seven 21-Nov FJ-03
bundles ran with a given two-test order — labelled "given order", not order mode reproducing FJ-03. **Rejected:**
presets (hide parameters); a UI button that tampers (looks staged). **What I changed:** *to fill in.*

Ownership checkpoint: why a committed bundle is labelled "pre-run, not run now"; why the checksum, not the recount,
catches a changed number; what the UI cannot do (replay, live FJ-03).

## 2026-11-27 — Vault close-out after the supervisor's 23 Nov review

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L3 · **Branch:** `docs/post-review-closeout`

**Asked:** read the supervisor's review and the vault, then update the vault so all three members can start the
remaining work; tell me first what would change. **Kept:** a review note from the student action plan only (the
rest of the package is marked private and is not quoted); close-out packages W36–W40; register rows A4–A6, A10,
M-2, M-3, FT007, FT008, FT009, FT010 each with "Completes when"; agenda v3; claims ledger four-vs-five fix;
`architecture.md` status and naming (order runner now; sandbox planned for FYP-2 Iteration 3); handover items.
**Rejected:** editing M3's frozen protocol and evidence log (left as W37 items for him); a first draft that quoted
scores and probe results from the private part of the package (removed). **Wrong at first:** none recorded beyond
that. **What I changed:** *to fill in.*

Ownership checkpoint: why "order runner" and not "sandbox runner"; what each W36–W40 package needs to be Done.

## 2026-11-27 — W39: FJ-03 under a stated budget

**Tool:** Claude Code (Claude Opus 5.5) · **Level:** L2 · **Branch:** `m2/w39-budgeted-fj03`

**Asked:** run FJ-03 pair mode under one stated limit, record the real output, commit the bundles. **Kept:** the
prediction written before the runs; a clean local clone so the bundles are `tool.dirty: false`; records outside the
clone. **Found:** the demo plan's "certified polluter" (flagged by M3), corrected. **What I changed:** *to fill in.*

Ownership checkpoint: why 400 invocations leave 340 for the pairs; why `original` blames nothing when it stops.
