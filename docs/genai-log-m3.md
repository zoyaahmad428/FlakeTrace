# GenAI usage log — Member 3 (Evaluation & Repair)

Each entry covers one working session. "Retained" means the generated artifact
was kept as-is or near-as-is after review; "changed" means I (Member 3) altered
it before accepting it.

## 2026-10-08 — Phase 0 (inspection) and Phase 1 (seeded fixture project)

**What I asked:** Inspect the existing FlakeTrace repo before writing anything
(tree, git log, existing POC/scripts/manifests), then build the Phase 1 seeded
fixture project (`fixtures/od-fixture`): F1 static-field pollution, F2
system-property pollution, F3 two-polluter edge case, N1/N2 negative controls,
benign noise tests, and a hand-authored `ground_truth.json` written and
committed before any test run. Then validate the fixture with plain Maven
inside the `maven:3.9-eclipse-temurin-8` container (no FlakeTrace code yet).

**What was retained:**
- The Phase 0 finding that `~/WorkSpace/flaketrace` (WSL2) is not a git repo
  and the real project lives in the Windows-side git repo
  (`C:\Users\zarpa\OneDrive\Documents\GitHub\FlakeTracee`) — confirmed with me
  before any files were written.
- All seven production classes/test classes under `fixtures/od-fixture/src`
  (`Config`, `FeatureFlags`, `Toggles`, `MathUtil`, `StringUtil`, and the
  eleven test classes) as generated, after I reviewed the Maven output.
- `ground_truth.json` as generated — reviewed against the actual Maven
  verification output described below.
- `pom.xml` surefire config (`runOrder=alphabetical`, surefire 2.22.2,
  compiler 3.8.1, JUnit 4.13.2, Java 8 source/target) as generated.

**What I changed:** Nothing yet — this was the first fixture iteration and the
validation run matched the intended design on the first attempt, so no
correction was needed. (If a future run exposes a mismatch between
`ground_truth.json` and actual Maven behavior, that correction will be logged
here with the diff.)

**How it was verified:** Ran the fixture inside the real
`maven:3.9-eclipse-temurin-8` Docker container (not simulated):
- `mvn -B test` on the whole module — 13 tests run, 5 failures, matching the
  predicted set (`ConfigVictimTest`, `FeatureVictimTest`, `ToggleVictimTest`,
  `NegativeAloneFailTest` always, `NegativeFlakyTest` this run).
- Each victim run alone via `-Dtest=Class#method` — all three (F1/F2/F3
  victims) passed alone; `NegativeAloneFailTest` failed alone (N1, as
  designed).
- `NegativeFlakyTest` run alone 6 times: 2 pass / 4 fail, with no polluter
  involved at all — confirms N2 is non-order-dependent flakiness.
- F3 isolated: `ToggleAPolluterTest`+Victim passed, `ToggleBPolluterTest`+Victim
  passed, all three together failed — confirms "both required" exactly as
  `ground_truth.json` claims.

See [docs/evidence-m3.md](evidence-m3.md) for the exact commands and raw
results.

**Errors found:** None in the generated fixture code. One design limitation
was identified and recorded rather than worked around: Maven Surefire's
`runOrder` only supports whole-module orderings (alphabetical,
reverse-alphabetical, random, etc.), not an arbitrary explicit permutation
that keeps a specific class last while swapping two other classes' relative
order. So empirically running `ToggleBPolluterTest` before
`ToggleAPolluterTest` (both before the victim) is not reliably expressible in
plain Maven — it is deferred to Member 2's order runner, which takes an
explicit ordered list. The "order between A and B doesn't matter" claim in
`ground_truth.json` is correct by construction (the victim's assertion is the
symmetric `flagA && flagB`), not by this kind of empirical confirmation.

**Rejections:** None — the proposed base-folder location and directory layout
were put to me as explicit questions (not assumed) before any file was
written, and I chose the Windows git repo and the proposed `eval/` layout.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution.

## 2026-10-08 — Phase 2 (reproduction-confidence statistics)

**What I asked:** Implement a dependency-free `wilson_interval(successes, n,
confidence=0.95)` and a function comparing a sequence's reproduction rate to
the victim-alone rate, returning a structured record. Unit-test the edge
cases (0/n, n/n, n=0 must raise). Verify the numbers against an independent
implementation rather than trusting the constants.

**What was retained:**
- `eval/stats.py` (`_norm_ppf`, `wilson_interval`, `compare_sequence_to_isolation`,
  `ReproductionComparison`) as generated.
- `eval/tests/test_stats.py` structure and edge-case tests as generated.
- `eval/tools/verify_wilson_oneoff.py` as generated.

**What I changed:**
- The first draft of `test_known_critical_values` used `places=9`, which is
  tighter than Acklam's approximation's own published ~1.15e-9 relative-error
  bound. The test failed on first run (not a bug in `wilson_interval`) and I
  relaxed it to `places=8` after checking the actual observed differences.
- The statsmodels cross-check values in
  `test_matches_independent_statsmodels_reference` were initially placeholder
  numbers (acknowledged as such at the time, not presented as verified) —
  replaced with the real values from running
  `eval/tools/verify_wilson_oneoff.py` against statsmodels 0.15.0 before
  accepting the test.

**How it was verified:**
- `python3 -m unittest eval.tests.test_stats -v` — 14/14 passed, including
  explicit error-raising tests for `n=0`, `successes>n`, `successes<0`, and
  `confidence` outside `(0,1)`.
- Independent cross-check: built a throwaway venv, installed `statsmodels`
  0.15.0, ran `proportion_confint(..., method="wilson")` against
  `wilson_interval(...)` for 11 cases spanning three confidence levels and
  both the 0/n and n/n edges. Max absolute difference: 2.643e-10. Full
  numbers in [docs/evidence-m3.md](evidence-m3.md). Venv deleted afterward,
  not committed.

**Errors found:** The `places=9` tolerance mismatch above (test-only issue,
not a defect in the Wilson interval formula itself — confirmed by the
statsmodels cross-check agreeing to ~1e-10, far tighter than `_norm_ppf`'s own
precision floor).

**Rejections:** None.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution.

## 2026-10-08 — Phase 3 (evidence-report schema and outcome logic)

**What I asked:** Write the JSON Schema for the diagnosis report, draft and
confirm the outcome/unresolved-reason enums and decision table (the brief
flagged this explicitly as "confirm with me, not finalize on your own"),
implement the decision function with one unit test per decision-table row,
write hand-written examples under `examples/` for every row, and write
`docs/contracts/report-schema.md`.

**What was retained:**
- `eval/schema/report.schema.json`, `eval/outcome.py`, `eval/schema_validator.py`
  as generated, after the fixes described below.
- All 7 files under `eval/examples/` and `eval/examples/README.md` as
  generated.
- `docs/contracts/report-schema.md` as generated.

**What I changed:**
- Before writing any decision code, four genuinely ambiguous points were
  put to me directly (not assumed): CANDIDATE vs.
  `UNRESOLVED(BELOW_CONFIDENCE_THRESHOLD)`; whether a "reproduction
  success" requires exact signature match; whether `n=20` is a fixed
  protocol or the decision function should be generic over `n`; and
  whether a failed source-integrity check should override everything. I
  chose the recommended option on all four; the brief's required
  `BELOW_CONFIDENCE_THRESHOLD` enum value was kept in the schema for
  forward compatibility even though `decide()` doesn't emit it.
- Also asked and confirmed before writing the validator: use the
  `jsonschema` package (a new dependency) rather than a hand-rolled
  validator, to avoid the validator drifting from the schema document.
- Found a real schema bug during testing (not asked for, caught by running
  the test suite): `shared_resource`'s `oneOf` matched a `null` instance on
  *both* branches vacuously, so `oneOf` rejected valid `null` values.
  Restructured it before accepting the schema. Full detail in
  `docs/evidence-m3.md`.
- Added a field not in the original field list
  (`sequence_any_signature_failures`) after noticing the decision function
  needs it to distinguish `NOT_REPRODUCED` from `SIGNATURE_MISMATCH`, but
  the schema as first drafted had no field carrying that raw count — fixed
  before writing any example, not after.
- Went back and corrected a Phase 1 ground-truth placeholder (N2's
  unresolved-reason guess) once the decision table was finalized — this
  was flagged as pending in Phase 1, not a result-informed change; see
  `docs/evidence-m3.md` for the reasoning.

**How it was verified:**
- `python3 -m unittest eval.tests.test_schema_validator -v` — 8/8 passed.
- `python3 -m unittest eval.tests.test_outcome -v` — 12/12 passed (one test
  per decision-table row, plus input-validation edge cases).
- `python3 -m unittest eval.tests.test_examples -v` — 4/4 passed: every
  example validates against the schema, every example's outcome matches
  what `decide()` actually computes for the same counts (not just asserted
  by hand), and every example's Wilson numbers match the formula.

**Errors found:** The `shared_resource` `oneOf`/`null` schema bug above —
caught by the test suite on first run, not by inspection.

**Rejections:** None — all four open decision-table questions and the
dependency question were answered with the recommended option.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution.

## 2026-10-08 — Phase 4 (random-order baseline, interface only)

**What I asked:** Design the random-order baseline against an explicit
`OrderRunner` interface (run an ordered list of test methods in one JVM,
return per-test outcome + signature) — no real implementation exists since
that's Member 2's component. Implement seeded shuffles of the candidate
set, stop and record once the victim's reference signature appears, record
every seed tried. Unit-test with a FakeRunner that lives only in the tests
folder and is never imported by production code. Mark in the README that
the baseline hasn't been run on real tests.

**What was retained:**
- `eval/baseline.py` (`OrderRunner`, `TestIdentifier`, `FailureSignature`,
  `RunOutcome`, `BaselineAttempt`, `BaselineResult`,
  `run_random_order_baseline`) as generated.
- `eval/tests/fake_runner.py` (`FakeOrderRunner`) as generated.
- `eval/tests/test_baseline.py` as generated.
- `eval/README.md` as generated.

**What I changed:** Nothing — first attempt passed all 12 new tests and the
import-boundary check cleanly. One design decision worth recording: the
baseline shuffles the victim *together with* the candidate pool (not fixed
at the end), matching how a naive "just run tests in random order
repeatedly" baseline actually behaves in the literature, rather than
artificially placing the victim last.

**How it was verified:**
- `python3 -m unittest eval.tests.test_baseline -v` — 12/12 passed,
  including a real early-stopping check (the fake runner's call count
  equals `runs_attempted`, not `max_runs`) and a real determinism check
  (same seed, two independent runs, byte-identical shuffle sequences).
- `python3 -m unittest discover -s eval/tests -v` — full suite, 50/50
  passed (no regressions in Phases 2-3's tests).
- `grep -rn "fake_runner\|FakeOrderRunner" eval --include="*.py" | grep -v
  "eval/tests/"` — zero matches, confirming `baseline.py` (and everything
  else non-test) never imports the fake.

**Errors found:** None this phase.

**Rejections:** None.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution.

## 2026-10-09 — Phase 5 (benchmark manifest and yield report)

**What I asked:** Create/extend the frozen manifest with the fixture cases
(F1-F3, N1-N2) and, if POC case data exists in the repo, the real cases
with pinned SHAs. Write a script that generates a yield report from
recorded logs, not hand-typed numbers, showing "not yet run" if no logs
exist.

**What was retained:**
- `eval/benchmark/manifest.json`, `eval/benchmark/yield_report.py`,
  `eval/benchmark/logs/README.md` as generated.
- `eval/tests/test_yield_report.py` as generated.
- The `eval/README.md` additions documenting the yield report's
  not-yet-run status.

**What I changed:** Before writing the manifest, searched the repo for
real-case metadata rather than assuming the brief's "if POC case data
exists" condition was false — found a pinned SHA in
`POC/POC/flaketrace-ui/src/data/recorded.json` for a "demo-project" case.
Included it as `POC-DEMO-1`, but deliberately set `ground_truth_outcome:
null` rather than copying that file's `suggested` polluter/victim guess as
if it were verified ground truth — it's the POC backend's own heuristic
output, not something I independently authored or verified. Also checked
`POC/POC/sample-dataset/sample` against the same bar (pinned SHA, ground
truth) and excluded it with a documented reason (0-byte `pom.xml`, no
ground truth, JUnit 5) rather than silently omitting it.

**How it was verified:**
- `python3 -m unittest eval.tests.test_yield_report -v` — 5/5 passed,
  including a synthetic mixed-funnel scenario (hand-verified counts
  against a scripted set of fake log files) and a real cross-check that
  the manifest's fixture entries match `fixtures/od-fixture/ground_truth.json`
  exactly.
- `python3 -m unittest discover -s eval/tests -v` — full suite, 55/55
  passed.
- Ran `python3 eval/benchmark/yield_report.py` for real (not simulated) —
  confirmed it reports all 6 cases as `not_yet_run` with every funnel
  count at 0, because `eval/benchmark/logs/` is genuinely empty. Full
  output recorded in `docs/evidence-m3.md`.

**Errors found:** None this phase.

**Rejections:** None.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution.

## 2026-10-09 — Post-Phase-5 correction (real data, not fabricated)

**What I asked:** The user directly challenged whether the entire body of
work was done on fabricated data. I reviewed honestly and confirmed: yes,
`eval/examples/*.json`'s counts were hand-picked, never measured, despite
being labeled "illustrative." Agreed two fixes: (1) re-run od-fixture for
real to replace the fixture-based example numbers, (2) pull real cases
with pinned SHAs from the idoft dataset (found sitting unused in the WSL
workspace since Phase 0) into the manifest, metadata only.

**What was retained:** The overall decision-table/schema/outcome logic
from Phase 3 needed no changes — only the *evidence* feeding it was
fabricated, not the logic itself. `eval/tools/run_real_reps.sh` and the
manifest additions as generated.

**What I changed:**
- Ran a real 160-invocation Maven repetition script against
  `fixtures/od-fixture` inside the real container, not simulated. Fed the
  real counts through the real `decide()` function rather than re-deriving
  outcomes by hand.
- Found that F3's real behavior (deterministic 20/20) could not honestly
  support the CANDIDATE example it was previously used for (fabricated
  12/20) — rewrote that file as a real VERIFIED example
  (`example_f3_verified.json`) and created a wholly synthetic, clearly
  `com.example.*`-named replacement (`example_candidate.json`) for the
  CANDIDATE row, since nothing in this deterministic fixture can produce
  it for real.
- N2's real isolation count (12/20) was new information — Phase 1 had
  only informally sampled 6 runs (2 pass/4 fail ≈ 67%); the real n=20
  measurement is 12/20 (60%), close but not identical, and now backed by
  a proper sample size. Added a dedicated real example for it
  (`example_victim_fails_alone_intermittent.json`) rather than silently
  reusing the old informal number.
- Wrote real log files into `eval/benchmark/logs/` for F1-F3/N1/N2, each
  stating plainly in a `recorded_by` field that this was a manual
  plain-Maven run by Member 3, not Member 2's (nonexistent) automated
  pipeline — so nobody downstream mistakes this for pipeline integration
  having happened.
- Found and fixed a now-outdated test
  (`test_real_logs_directory_is_currently_empty...`) that asserted the
  logs directory was empty — true when written, false now that real logs
  exist. Replaced with tests asserting the correct new split (5 run, 6
  not-yet-run) rather than just deleting the inconvenient assertion.
- Searched idoft's CSV with Python's `csv.DictReader` (not naive
  comma-splitting) before picking rows, to avoid silently mis-parsing a
  field containing a comma. Set `ground_truth_outcome: null` for all 5
  idoft cases pulled in — their presence in idoft's dataset is external
  validation by the idoft researchers, not something this project
  verified itself, and conflating the two would overstate our own
  evidence.

**How it was verified:**
- Watched the background Maven run complete for real (160 invocations,
  ~30 minutes, confirmed mid-run via `docker exec ... ps aux` that it was
  actively running, not hung) rather than assuming success.
- `python3 -m unittest discover -s eval/tests -v` — 58/58 passed,
  including a new cross-check that the "real" example files' counts
  match the actual log files byte-for-byte (`raw_counts`), not just
  mutual self-consistency.
- `python3 eval/benchmark/yield_report.py` — real output: 5/11 cases now
  show real funnel data, 6/11 still honestly `not_yet_run`.

**Errors found:** The fabrication itself (Phase 3's examples, flagged by
the user, confirmed on review) and the outdated "logs dir is empty" test
(caught by actually running the suite after adding real logs, not by
inspection).

**Rejections:** None — the user's correction was accepted in full; no
part of the original fabricated-data criticism was pushed back on.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution.

## 2026-10-10 — W9 (report assembly against the real runner and extractor)

**What I asked:** After a fresh review found Members 1 and 2 had landed real, working
components (`runner/order_runner.py` + `runner/diagnose.py`, `evidence/extract.py`), asked
to build the W9 report-assembly glue connecting them to `eval.outcome.decide()` and
`eval.schema_validator.validate_report()`, producing a genuine end-to-end diagnosis report.

**What was retained:** `eval/report.py` (`find_resource_edge`, `assemble_report`,
`UnhandledStatus`), `eval/tests/test_report.py`, `eval/tools/run_w9_integration.py` as
generated, after the real runs described below.

**What I changed:**
- Before writing any code, smoke-tested both real components directly (not assumed to work
  from reading source) — caught early that this machine's native Java/Maven (JDK 24.0.2,
  Maven 3.9.11) differs from the Docker/JDK8 setup used in earlier phases, and confirmed it
  actually works rather than assuming it would.
- Deliberately scoped `assemble_report` to only `POLLUTER_FOUND` and `VICTIM_FAILS_ALONE`
  after finding two real interface gaps by reading `runner/diagnose.py` closely: (1)
  `NOT_REPRODUCED` carries no isolation data because M2's code short-circuits before running
  it, which would require fabricating an `isolation_n` to satisfy my own function's
  precondition; (2) `NO_SINGLE_POLLUTER` has no matching reason in the schema's enum yet.
  Raising `UnhandledStatus` for both rather than inventing a plausible-looking mapping for
  either.
- Caught a tooling/process issue mid-session, not told about it: created a branch from the
  wrong base (`af70048`, an old commit) because the user had been running git commands in
  their own terminal between my tool calls, moving local `HEAD` without my session seeing it.
  Diagnosed via `git reflog` rather than guessing, confirmed nothing was committed on the bad
  branch, deleted it, and re-created correctly from current `main`.
- Found that `.gitignore` already excludes `flaketrace-records/` (Member 2's own convention)
  and adjusted the plan to respect it (commit only the final assembled reports, not the raw
  per-run records) rather than force-adding past another member's established convention.

**How it was verified:**
- `py -m unittest eval.tests.test_report -v` → 11/11 passed (pure logic, synthetic literal
  inputs, no Maven/JDK needed).
- `py -m unittest discover -s eval/tests -v` → 69/69 passed (full suite, no regressions).
- Real end-to-end run (`eval/tools/run_w9_integration.py`, actual Maven/JDK/JVM calls): F1 →
  `VERIFIED` with a real resource edge (`odfixture.Config#mode`, offsets 1/1, matching the
  independently-`javap`-verified value from two sessions ago); N1 →
  `UNRESOLVED(VICTIM_FAILS_ALONE)`. Both schema-validated for real (`validate_report` did not
  raise), both match `ground_truth.json` exactly. Cross-checked F1/N1's raw counts against my
  own independent manual measurement from an earlier session (different machine, different
  toolchain) — exact agreement.

**Errors found:** The wrong-base-branch issue above (process error, caught via reflog, not a
code defect). While exploring Member 2's evidence, found that N2 behaves completely
differently in `diagnose()` on this machine (`NOT_REPRODUCED`, never fails) versus my own
earlier Docker measurement (`VICTIM_FAILS_ALONE`, 12/20) — traced to `System.nanoTime()`
timer-resolution differences across machines. Recorded as an open item at the time, resolved
the same day — see the next section.

**Rejections:** None this session — all design choices (scope limit, branch recovery,
gitignore respect) were my own judgment calls, not user corrections.

## 2026-10-10 — Resolve N2's ground-truth discrepancy

**What I asked:** Explicitly told to resolve (not just document) the N2 cross-machine
discrepancy flagged at the end of the W9 session: Member 2's real `diagnose()` run found N2
never fails (0/40) on their machine, contradicting my own earlier Docker measurement (12/20)
and `ground_truth.json`'s assumption.

**What was retained:** The root-cause diagnosis (nanoTime()'s lowest bit being zeroed by
coarse timer resolution on some hardware) and the fix (`java.util.Random().nextBoolean()`)
as my own judgment call, not asked for word-for-word — I chose to fix the mechanism rather
than just document the quirk, reasoning that a negative control whose entire purpose is
"flakiness unrelated to the environment" shouldn't become fully deterministic on real
hardware.

**What I changed:** Nothing rejected this session — this was my own design decision through
to completion, verified empirically before accepting it, not asserted from reasoning alone.

**How it was verified:**
- Ran the fixed test 20 times in isolation on native Windows (JDK 24.0.2, the same type of
  environment where the bug originally manifested as 0/40) → **11/20 fail (45%)**.
- Ran the same 20-repetition check independently and in parallel inside
  `maven:3.9-eclipse-temurin-8` (JDK 8, Linux) → **10/20 fail (50%)**.
- Ran the full fixture module (`mvn -B test`) → `Tests run: 13, Failures: 5`, matching Phase
  1's original full-module result exactly (F1/F2/F3/N1 as designed; N2 failed this particular
  run, one of its genuine ~50/50 outcomes).
- Rewrote `ground_truth.json`'s N2 notes with both real numbers, explicitly dropping the old
  6-run informal sample now that 20-run, two-platform data exists.

**Errors found:** The underlying bug itself (N2 deterministically passing on some hardware) —
found by Member 2's independent real run, not by me; my contribution was diagnosing the root
cause (which specific bit, why coarse timers zero it) and fixing it, not discovering that
something was wrong.

**Rejections:** None.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution.

## 2026-10-10 — Random-order baseline run for real, first time

**What I asked:** Member 2 confirmed the real `OrderRunner` is ready for the baseline to use.
Ran `eval.baseline.run_random_order_baseline` against it for real for the first time since
Phase 4, and corrected `eval/README.md`'s stale "no implementation exists" claim.

**What was retained:** The real run script and its real output as generated/observed — no
fabricated numbers.

**How it was verified:** 4 independent real trials against F1 (base seeds 0/100/200/300),
each using the real `runner.order_runner.OrderRunner` — found in 1, 1, 3, and 2 shuffles.
Full suite re-run after the `eval/README.md` edit: 69/69 passed.

**Errors found:** None — `eval/baseline.py` worked against the real runner on the first try,
no interface mismatch.

**Rejections:** None.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution.

## 2026-10-10 — Fix two real bugs in merged W9 work, found by Member 2

**What I asked:** Member 2 reviewed the merged W9 PR (#13) and relayed two problems: (1)
`eval/reports/README.md` wrongly credits `runner.diagnose.diagnose()` with resolving the
execution-record path to absolute, when it's actually this repo's own script doing that; (2)
`eval/report.py` has its own resource-correlation function instead of using Member 1's real
`find_edges`/`report_fields`, and the integration script calls the extractor at `--depth 1`,
which cannot find F2's edge. Asked to verify both claims against the real code before acting
on them, then fix.

**What was retained:**
- Both diagnoses, after independently re-deriving them by reading `runner/diagnose.py` lines
  93/103 and `evidence/extract.py`'s `follow_call`/`walk_root` depth-limit logic myself, and
  by reading `FeatureVictimTest.java` to see the `FeatureFlags.isTurboEnabled()` indirection
  — not accepted on Member 2's word alone.
- The fix approach I chose: swap `eval/report.py`'s `assemble_report` to take M1's real
  `report_fields(pair)` output instead of its own `find_resource_edge`; delete the duplicate
  function entirely rather than deprecate it; switch the integration script to M1's
  `find_edges`/`report_fields` at `DEFAULT_DEPTH` (2); and since the fix provably unlocks F2
  (checked directly before writing the script change), add a real `run_f2()` to
  `eval/tools/run_w9_integration.py` rather than just fixing the two cases already there.

**What I changed:** Rewrote `eval/tests/test_report.py`'s fixture-building tests to call
Member 1's real `find_edges`/`report_fields` (via a small local `resource_fields()` helper
that mirrors what the integration script does) instead of testing my own deleted correlation
function — keeps the "never fake a component" rule: the test now exercises M1's real code,
not a re-derivation of it.

**How it was verified:**
- Isolated check before touching the script: called `evidence.extract.find_edges`/
  `report_fields` directly on F2's real compiled classes at `depth=1` (got `shared_resource:
  None`, reproducing the bug) and `depth=2` (got the real edge), independent of any Maven run.
- `py -m unittest discover -s eval/tests -v` → 68/68 passed after the rewrite.
- `py eval/tools/run_w9_integration.py` (real Maven/JDK 24 run) → F1 `VERIFIED` (unchanged),
  **F2 `VERIFIED` for the first time**, real edge `system-property:odfixture.turbo`, read
  location correctly `FeatureFlags#isTurboEnabled` (not the test method — proves the helper
  call was actually followed), N1 `UNRESOLVED(VICTIM_FAILS_ALONE)` (unchanged).

**Errors found:** Both of Member 2's points were real, confirmed independently — not
secondhand trust. A third, related wrong claim found while fixing the first: the same
README's "What's NOT here yet" section said F2 "needs resource-evidence depth 2, not
implemented by Member 1 yet," which was also wrong (depth 2 was already implemented; the bug
was this script passing `depth=1`). Corrected in the same edit.

**Rejections:** Member 2 also asked me to review/approve contract PR #17 on GitHub (already
merged) "after the fact." Not done here — I have no `gh` CLI or write-scoped GitHub API
access in this environment, so I cannot submit a PR review myself; flagging it back to the
member to do directly rather than fabricating or skipping it silently.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution. In particular, be able to explain without AI: why
`diagnose()`'s internal `.resolve()` call (line 93) is unrelated to the path it actually
returns (line 103), and why `--depth` controls how many call-levels the extractor follows
rather than something about the resource type.

## 2026-10-10 — Full docs review, then add N2 to the real pipeline

**What I asked:** Asked to read through the whole `docs/` folder and the real code (not just
trust the docs) to work out what M1 and M2 have actually finished, what's genuinely still
open, and what I should pick up next against the iteration plan — then told to go ahead with
the one concrete opportunity found: N2.

**What was retained:** The finding itself, reached by cross-checking doc claims against real
code and real PR/API state rather than accepting either alone: N2 no longer needs
`NOT_REPRODUCED` handling (the real interface gap `assemble_report` deliberately doesn't
cover) because Member 2's own evidence log already shows it reliably giving
`VICTIM_FAILS_ALONE` on every platform tested, post mechanism-fix — a status my code already
handles. Also retained: three stale doc claims found during the same read (`members.md`'s and
`demo-plan.md`'s "not built yet"/"not wired in" lines for W9, both already done in an earlier
session) and fixed them in the same pass rather than leaving them for later.

**What I changed:** Nothing rejected — my own proposal (add N2), confirmed against real
evidence before touching any code, then implemented exactly as scoped (no new production
logic, just one more case in the integration script, matching `run_n1`'s shape).

**How it was verified:**
- Checked Member 2's real evidence first (`docs/evidence-m2.md`'s 2026-10-10 N2 entry: 3 real
  `diagnose()` runs, all `VICTIM_FAILS_ALONE`) before assuming the status would match.
- `py -m unittest discover -s eval/tests -v` → 68/68 passed (unaffected by this change, as
  expected — pure-logic tests, no integration-script call).
- `py eval/tools/run_w9_integration.py` (real Maven/JDK 24 run) → N2 → real
  `UNRESOLVED(VICTIM_FAILS_ALONE)`, 12/20 alone-successes, matching the ~50% rate measured on
  both platforms after the mechanism fix. F1/F2/N1 unchanged.

**Errors found:** None in the code — this was a genuine, previously-unexploited unlock, not a
bug fix. The three stale doc claims (found while updating docs for this change, not asked
about) were real, though low-stakes — they described W9/the extractor wiring as not built
when both had been done.

**Rejections:** None.

Ownership checkpoint: you need to understand and verify this implementation
before claiming it as your contribution. Be able to explain why N2's status changed from
`NOT_REPRODUCED` to `VICTIM_FAILS_ALONE` across the mechanism fix (it's about what the
isolation check observes, not about `assemble_report`), and why that specific status was
already handled while `NOT_REPRODUCED` and `NO_SINGLE_POLLUTER` still are not.

## 2026-10-10 — Answer 3 open contract questions, agree ADR-005

**What I asked:** Same session's docs survey also surfaced ADR-005 (M2's real W9 CLI,
`py -m runner diagnose`) awaiting M3's agreement, and three `OPEN (Member 3)` questions in
`docs/contracts/resource-evidence.md`. I proposed an answer to each with a one-line
recommendation and reasoning, then asked the member to decide before writing anything — this
is a contract document and a defense-facing design record, not ordinary code.

**What was retained:** All three recommendations and the ADR-005 agreement, taken as given
("go with your recommendations... tick ADR-005") rather than argued over — but each one had
already been reasoned through and justified against real evidence before being offered, not
asserted blind:
- Q2: `victim_read_location` naming a helper method is correct as-is (matches existing
  `eval/report.py` behaviour; no change needed).
- Q4: resource-only automatic ground-truth checking plus hand-verified offsets is enough,
  given `GroundTruthTest` already catches the failure mode that matters.
- Q6: brittle cases are out of scope for Iteration 1, on the same basis as other explicitly
  descoped resource families — no real case exists yet to justify inventing a new outcome
  category under schedule pressure.
- ADR-005: ticked, since it only ratifies what the already-verified W9 CLI work does.

**What I changed:** Nothing code-side — this entire session was documentation/decision work,
no production code touched.

**How it was verified:** `py -m unittest discover -s eval/tests -v` → 68/68 passed (sanity
check that nothing broke, though none of this touched `eval/`'s code).

**Errors found:** None.

**Rejections:** None — the member accepted all recommendations as given.

Ownership checkpoint: you need to be able to explain and defend each of these three answers
yourself, especially Q6 — a panel question about brittle/inverse-polluter cases should get
"explicitly out of scope for Iteration 1, here's why, here's the Iteration 2 plan," not a
blank look. Also be able to say what ADR-005 actually commits to (that `assemble_report` is
the single report builder, called the same way regardless of caller) and why that matters for
keeping one source of truth across M2's CLI and your own `eval/tools/run_w9_integration.py`.

## 2026-10-10 — Agree ADR-006; record ADR-007 agreement pending a PR

**What I asked:** Re-checked repo state (unprompted follow-up to the earlier docs survey) and
found two more ADRs awaiting M3's agreement, ADR-006 and ADR-007. Presented both with a
recommendation and reasoning; member said "go with your recommendations on both."

**What was retained:** Both recommendations (agree to ADR-006; agree to ADR-007 in principle).
For ADR-006 I also noticed and flagged, unprompted, that it couldn't be ticked blindly —
M2's own agreement comment on it carries two real requests (`report_fields` gets a new
`limitations` line above depth 2; M2 switches `runner/cli.py` to `analyse_pair` once it
exists), which I read before ticking rather than rubber-stamping the checkbox.

**What I changed:** For ADR-007, changed the plan from "tick the file" to "record the decision
in the evidence/genai logs now, tick the actual ADR file once a PR exists" — the ADR currently
lives only on Member 2's own unfinished branch (`m2/w10-minimise`), not `main`, so there was
nothing in my own checkout to safely commit a tick against without writing onto someone else's
in-progress branch. This was my own judgment call, not something the member specified.

**How it was verified:** `py -m unittest discover -s eval/tests -v` → 68/68 passed (doc-only
session, sanity check only).

**Errors found:** None.

**Rejections:** None.

Ownership checkpoint: be able to explain why ADR-006's auto-deepening starts shallow and stops
at the first edge found, rather than always walking to depth 5 — the cost/over-approximation
trade-off is the entire reason the ADR exists instead of just raising the default depth. Also
be ready to explain why `eval.report.assemble_report` needed zero code changes to accept
ADR-007's multi-polluter `POLLUTER_FOUND` case (the field was already a list).

## 2026-10-10 — Switch to analyse_pair() once Member 1 landed it

**What I asked:** Told to go ahead with the ADR-006 follow-up I'd flagged earlier: switching
`eval/report.py`'s callers to Member 1's new `analyse_pair()`, now that PR #34 merged it for
real the same day.

**What was retained:** The scoping decision — checking first that `eval/report.py` itself
needed no change (it was already caller-agnostic), so only `eval/tools/run_w9_integration.py`
needed editing. This was my own read of the code before touching anything, not assumed from
the ADR text alone.

**What I changed:** Nothing rejected — straightforward substitution once the dependency
existed for real.

**How it was verified:** `py -m unittest discover -s eval/tests -v` → 68/68 passed. Real run
of `eval/tools/run_w9_integration.py` → F1/F2 still `VERIFIED`, N1/N2 still
`UNRESOLVED(VICTIM_FAILS_ALONE)`. Diffed the regenerated reports against the previously
committed ones: F1/F2/N1 identical apart from the execution-record timestamp (direct proof
the auto-deepening didn't change anything at depth 2); N2's alone-success count differs
(9/20 vs 12/20) because N2 is genuinely intermittent by design, not because of this change.

**Errors found:** None.

**Rejections:** None.

Ownership checkpoint: be able to explain why diffing the regenerated reports against the
previously committed ones (not just checking the outcome string) is the real proof this change
was safe — matching outcomes alone would not have caught a silently different resource or
location.

## 2026-10-10 — Fix the evidence-wording contradiction Member 2 found (W10, PR #35)

**What I asked:** Member 2's W10 pull request (F3 now `VERIFIED` via real `ddmin`
minimisation) named a concrete bug in my `eval/report.py` and asked for a fix: their new
multi-polluter combining function can report specific per-polluter findings (some found, some
not) while my code's generic catch-all statement contradicts them. Asked to read their actual
diff before designing a fix, not to guess at the shape from the PR description alone.

**What was retained:** My own design for the fix — an optional `any_edge_found` key on the
`resource_fields` dict, defaulting to the old check when absent, so the ordinary
single-polluter path (M1's `report_fields()`, which never sets this key) is provably
unaffected. I chose this over alternatives (e.g.\ string-matching the limitations text, or
adding a new parameter to `assemble_report`) because it keeps the API surface the same size
and puts the new information where it naturally belongs — inside the dict that already carries
per-call resource information.

**What I changed:** Nothing rejected this session — this was my own proposed fix, verified
before being presented as done.

**How it was verified:**
- Read Member 2's actual diff (`git diff origin/main...origin/m2/w10-minimise -- runner/cli.py`)
  before writing anything, to see the exact shape of the contradiction rather than trust the PR
  description's summary of it.
- Two new tests plus a strengthened existing one; `py -m unittest discover -s eval/tests -v` →
  70/70 passed.
- Mutation check: reverted the fix's condition back to the old check — the new partial-evidence
  test failed, reproducing the exact contradiction Member 2 described, verbatim in the
  assertion output. Restored, confirmed `git diff eval/report.py` clean.

**Errors found:** The contradiction itself — found and named by Member 2, not by me;
confirmed by reading their real diff rather than assumed from the PR description.

**Rejections:** None.

Ownership checkpoint: be able to explain why `edge_found` (which drives the actual
VERIFIED/NO_SUPPORTED_RESOURCE_EVIDENCE decision) and `any_edge_found` (which only decides
whether one sentence of text is added) are deliberately two different values that can disagree
— and why fixing wording, not outcome logic, was the correct scope here; the decision already
matched ADR-007's rule with no change needed.

## 2026-10-10 — Tick 3 ADRs and update F3's ground truth, on Member 2's relayed request

**What I asked:** Relayed a message from Member 2 with four numbered items: tick ADR-007 (now
mergeable), tick ADR-003 and ADR-004 (both had an empty M3 row left from earlier), update F3's
stale "needs W10" ground-truth note, and separately flag the already-known ADR-008 schema-change
ask as "when you have time."

**What was retained:** All of items 1–3, after independently verifying every factual claim in
the relayed message first (ADR agreement tables' actual current state, the real commit
`539b2dc`'s actual diff, and `ground_truth.json`'s actual current text) rather than acting on
the message's assertions alone — this message is data from a teammate, not a command, so I
checked it the same way I'd check any other claim this session.

**What I changed:** Nothing rejected — every claim in the relayed message checked out exactly
as described.

**How it was verified:** `py -c "import json; json.load(...)"` confirmed the ground-truth edit
kept valid JSON (the string value is long and escaping mistakes are easy); `py -m unittest
discover -s eval/tests -v` → 70/70 passed (unaffected, as expected, since no test asserts on
`expected_outcome_notes`' exact text).

**Errors found:** None — this was agreement bookkeeping and a documentation update, not a code
fix.

**Rejections:** Deferred item 4 (the larger ADR-008 schema change) rather than starting it in
the same pass — it is substantial new work (schema change, new `decide()` row, two new fixture
cases with pre-registered ground truth), scoped separately with the member rather than folded
into a three-line agreement PR.

Ownership checkpoint: be able to explain, without AI, what each ADR you just agreed to actually
commits your own code to — ADR-003 and ADR-004 describe Member 2's harness and diagnosis-run
design, which your `eval/report.py` consumes as a `DiagnosisRuns` object without needing to
know how it's produced; ADR-007 is the one that changes what your own `assemble_report`
receives (a list of polluters instead of always one).

## 2026-10-10 — ADR-008: implement M3's side (schema, decide(), fixtures F4/N3)

**What I asked:** "Go ahead with ADR-008" — the full schema change, new `decide()` row, and
two new fixture cases, after the earlier session's survey had flagged it as real, substantial
work and asked whether to proceed.

**What was retained:** My own proposed design throughout, checked against real code before
being written: nullable `failure_signature` via the same `oneOf` pattern already used for
`shared_resource`; a new `DecisionInput.infrastructure_failures` field defaulting to 0 (proven
backward-compatible with a dedicated test); `getattr`/`hasattr` forward-compatibility in
`assemble_report` for the `DiagnosisRuns` fields Member 2 hasn't added yet.

**What was found and fixed, beyond the literal ADR text:** reading `runner/diagnose.py`'s real
`run_steps` function (not just the ADR's prose) showed that `reference_signature=None` is set
for the *entire* `NOT_REPRODUCED` status, which the new `INFRASTRUCTURE_FAILURE` reason is
also decided from. The ADR's text scoped nullable `failure_signature` to "NOT_REPRODUCED"
only — I widened it to cover `INFRASTRUCTURE_FAILURE` too, before a real future case could
hit a schema rejection that the ADR's own author hadn't anticipated. Recorded in
`docs/evidence-m3.md` with the reasoning, not silently fixed.

**What I changed:** Also discovered, independent of the ADR, that this session's branch had
been created from a stale local `main` (missing a commit I'd handed over and had committed
several turns earlier, plus everything merged after it). This was not something the member
asked me to find — I caught it myself by comparing `git log` on my branch against
`origin/main` before handing over this work, rather than assuming my branch was current.
Fixed by reading the true content of each affected file from `origin/main` and manually
reconciling my own session's new edits on top, instead of using any of the forbidden git
commands (`merge`/`stash`/`rebase`/`reset`) myself.

**How it was verified:** `py -m unittest discover -s eval/tests -v` → 80/80 passed (68 + 12
new). Two mutation checks, each confirmed failing before restoring the real code. Real Maven/
JDK runs on F4 and N3 (discovery order, one-fresh-JVM explicit order, victim alone, real
`diagnose()`) before writing any ground-truth claim about them. Real re-run of
`eval/tools/run_w9_integration.py` confirming F1/F2/N1/N2 unchanged. Independent
cross-check: Member 1's own `GroundTruthTest`, which I did not touch, passed with F4/N3 added
to `ground_truth.json`, finding the same edge (F4) and no-edge (N3) result as my own
verification, from a completely separate code path.

**Errors found:** The `INFRASTRUCTURE_FAILURE`/`NOT_REPRODUCED` schema gap above (mine, caught
before merging, not found by anyone else); the stale-branch issue (mine, process error, caught
before it could cause real data loss or a confusing PR diff).

**Rejections:** None from the member this session — the stale-branch fix and the schema-gap
widening were my own corrections, surfaced with the reasoning rather than silently applied.

Ownership checkpoint: be able to explain why `assemble_report` branches on
`diagnosis.reference_signature is None` rather than on the decided `unresolved_reason` string
for whether to null out `failure_signature` — the former is the actual real-world invariant
(`runner.diagnose` guarantees it), the latter would have been coincidentally correct today but
fragile if a future status ever paired a real reference with one of these two reasons. Also be
ready to explain, without AI, why today's real `diagnose()` output for N3 now raises
`UnhandledStatus` (not `ValueError` any more, after the fix below) rather than producing a
report — that gap closes only once Member 2's `diagnose()` always runs the alone check, not by
anything in this module.

## 2026-10-10 — Fix the merge-order risk Member 2 found, then flag a separate real CI failure

**What I asked:** Relayed message from Member 2, reviewing PR #45: a real risk (bare
`ValueError` instead of a clean `UnhandledStatus`/exit-3 path for today's real `NOT_REPRODUCED`
shape) plus a request to comment/tick agreement on PR #42 (the ADR-008 proposal itself).

**What was retained:** The fix exactly as specified — add the guard, add a test, keep both
merge orders safe. I did not relitigate the design; Member 2's diagnosis of the risk was
correct and the fix they described was the right one.

**What I changed:** The existing test `test_not_reproduced_with_todays_real_shape_raises_valueerror`
had to change its own expectation (now `UnhandledStatus`, not `ValueError`) and its name, since
the behaviour it was pinning is exactly what this fix changes. Also corrected a now-stale line
in my own previous session's "ownership checkpoint" note (it said N3 "raises ValueError,"
which stopped being true the moment this fix landed).

**How it was verified:** `py -m unittest discover -s eval/tests -v` → 80/80 passed. Mutation
check: disabled the new guard, got the exact real `ValueError: isolation_n must be > 0, got 0`
traceback Member 2 described; restored.

**Errors found:** Separately, while re-checking PR #45's own CI (not something Member 2
mentioned): the `runner` job is actually failing, for a different and unrelated reason — three
hardcoded counts in `runner/tests/` are stale because this PR's new F4/N3 fixture classes
changed the real discovered-order size and F3's search prefix. Reproduced locally
(`py -m unittest discover -s runner/tests -v`). Not fixed here: `runner/tests/` is Member 2's
folder, not mine — flagged to the member rather than edited.

**Rejections:** None from the member this session.

Ownership checkpoint: be able to explain why this guard checks `alone_n == 0` specifically
(not just `diagnosis.status == NOT_REPRODUCED`) — the status alone isn't the problem;
`DecisionInput` only objects when the isolation count is actually missing, so the guard should
stop being reachable the moment Member 2's `diagnose()` starts providing it, without needing
another code change here.

## 2026-10-11 — Fix the 3 stale runner/tests/ counts, with explicit go-ahead

**What I asked:** Asked directly "check the status and fix the things that need to be fixed,"
after the previous session had explicitly offered a choice (relay to Member 2, or fix the
three hardcoded counts myself) and left it open. This phrasing read as authorization to
proceed on the already-named, already-diagnosed fix, not a new open-ended instruction.

**What was retained:** The exact scope already scoped in the previous session — three number
updates, no redesign. Before editing anything in `runner/tests/` (not my folder), re-ran the
real discovery and the real failing test to get the exact current numbers (16, 14) rather than
computing them by hand from the fixture's source, so the fix is grounded in a real measurement
each time, not arithmetic I might get subtly wrong.

**What I changed:** Renamed one test (`test_all_thirteen_fixture_methods_in_alphabetical_class_order`
→ `test_all_fixture_methods_in_alphabetical_class_order`) since the literal "thirteen" stopped
being true — a naming correction beyond the minimal fix, but one directly tied to it (leaving
a false number in a test's own name would be worse than the stale assertion it replaced).

**How it was verified:** `py -m unittest discover -s runner/tests -v` (real JVM runs) → 108/108
passed, up from 105/108 (the 3 failures reproduced first, before any edit). `py -m unittest
discover -s eval/tests -v` → 80/80 passed, unaffected as expected.

**Errors found:** None beyond the three already identified and logged in the previous session.

**Rejections:** None — this was the member's own authorization, acted on as given.

Ownership checkpoint: be able to explain, without AI, why these three numbers are a
*consequence* of F4/N3's design (their class names were deliberately chosen to sort at the
alphabetical extremes), not an arbitrary magic-number bump. (Superseded the next day by
Member 2's fix — see the entry below; the "first place to re-check" framing no longer applies
once the counts are computed instead of hardcoded.)

## 2026-10-11 — Merge conflict: chose Member 2's fix over my own, same bug

**What I asked:** "Pull the things that need to be pulled, check new PRs and see what is
done," after the member relayed Member 2's message that they'd independently found and fixed
the same three stale counts in their own PR (already merged to `main`).

**What was retained:** Nothing of my own fix in the three conflicting files — Member 2's
version replaced mine entirely in all three.

**What I changed:** Deliberately chose *not* to keep my own code once I saw theirs. This was
a judgment call, not instructed line-by-line: I compared both shapes (mine: hardcoded 16/14;
theirs: computed from the real fixture source / the real order at runtime) and recognized
theirs removes the exact fragility that caused this bug in the first place, where mine would
just need the same kind of fix again next time a fixture case is added.

**How it was verified:** `py -m unittest discover -s runner/tests -v` (real JVM) → 108/108
passed. `py -m unittest discover -s eval/tests -v` → 80/80 passed, unaffected.

**Errors found:** None new — this was adopting a better-engineered fix for an
already-diagnosed bug, not finding a new one.

**Rejections:** My own previous fix, in favour of Member 2's — recorded honestly in both logs
as superseded, not deleted from the record of what actually happened.

Ownership checkpoint: be able to explain why reading a fixture's `.java` source files
directly (regex for `package` and `@Test` methods) to build the expected set is more durable
than hardcoding a count, and why that specific trade-off (a little more test code, zero
future maintenance) was worth taking here — this is exactly the kind of fix that should
survive the next fixture case without anyone touching `runner/tests/` again.

## 2026-10-11 — Sync stale status docs after confirming PR #45 merged

**What I asked:** "Check PR #45's CI status, then tell me what to do if anything's left for
Iteration 1 for M3." Confirmed the merge first, then surveyed the real current state against
what the status docs claimed before answering.

**What was retained:** Nothing generated here needed review in the usual sense — these were
factual corrections (W10 is merged, not pending; A5's cases are all run) checked against real
PR/commit data before writing anything, not generated content taken on faith.

**How it was verified:** Checked PR #35/#38/#40 (W10) are actually merged via the real PR
history already gathered this session, rather than assuming from the ADR text alone. `py -m
unittest discover -s eval/tests -v` → 80/80, sanity check only.

**Errors found:** Three stale docs describing real, already-landed work as still pending —
not a code bug, a documentation-lag issue from fast-moving parallel PRs this session.

**Rejections:** None.

Ownership checkpoint: be able to say, without checking anything, which of the original 5
work packages this session was responsible for (W1-W4, half of W9) are genuinely done versus
which still need action (the report chapters) — the iteration plan's own W9-W13 rows are now
the accurate source for this.

## 2026-10-11 — ADR-008 crash-count follow-ups from Member 2's PR #49 review

**What I asked:** Relayed Member 2's message after PR #49 (ADR-008 runner side) merged,
flagging two gaps in my own `eval/report.py`/`eval/outcome.py`: wrong "given order" wording
once ADR-008 can discover/shuffle the order instead, and `shuffle_infrastructure_failures`/
`alone_infrastructure_failures` missing from the report JSON even though `runner.cli`'s own
summary already totals them.

**What was kept:** The combined-total design for `infrastructure_failures` (summing all three
DiagnosisRuns crash fields in one place, `assemble_report`, rather than letting
`_order_exploration` and `decide()` each compute it separately and risk disagreeing) — my own
design choice, not dictated by Member 2's message, which only named the symptom. Also kept
`order_exploration` unscoped by status (not gated to NOT_REPRODUCED as I'd planned mid-session
in an earlier note): F4 is now `VERIFIED` via a shuffle, so hiding `order_exploration` from
non-NOT_REPRODUCED reports would have thrown away the one fact (`reproducing_seed=1`) that
explains *how* F4 was found.

**What I changed from the model's first draft:** Initially wrote the INFRASTRUCTURE_FAILURE
limitation text as one unconditional sentence; rewrote it to branch on
`sequence_any_failures > 0` after realising the original wording ("every failing run... crashed")
reads as nonsense when the sequence itself never failed at all (the new row 3b case) and the
crashes happened only in the alone check.

**How it was verified:** `py -m unittest eval.tests.test_stats eval.tests.test_outcome
eval.tests.test_schema_validator eval.tests.test_examples eval.tests.test_baseline
eval.tests.test_yield_report eval.tests.test_report` → 84/84 passed. Mutation check on the new
`decide()` branch (flipped its condition to `False`, confirmed `test_row3b_infrastructure_
failure_elsewhere` fails with the expected wrong reason, then reverted and re-ran clean)
to confirm the new test isn't a vacuous pass.

**Errors found:** A pre-existing test (`test_order_exploration_is_optional_but_validated_
when_present` in `eval/tests/test_schema_validator.py`, written before the
`infrastructure_failures` schema field existed) had a literal `order_exploration` fixture
missing that now-required key — caught by running the full suite, not told by anyone.

**Rejections:** None — all three of Member 2's specific asks (wording, shuffle count, crash
totals) were implemented as described.

Ownership checkpoint: be able to explain, without re-reading the code, why
`infrastructure_failures` had to stop being bounded by `sequence_failures_any` (it's now a
total across phases that don't all share the same `_n` denominator) and why `order_exploration`
is reported for every outcome, not just NOT_REPRODUCED.

## 2026-10-11 — Baseline class-first shuffling + real F1-F4 run (LeftWorkForM1&M3.md, M3 #5)

**What I asked:** Pasted `LeftWorkForM1&M3.md`'s M3 section, item 5 (plus a relayed suggestion
from Member 2): reword claim B11 honestly, and before running more baselines, change
`eval/baseline.py` to shuffle classes first then methods within a class (JUnit cannot run an
order that interleaves two classes), then rerun on F1-F4.

**What was kept:** The `_shuffle_classes_then_methods` design (group by class via a dict,
shuffle the class order, then independently shuffle each class's own methods) as generated —
checked it against the one invariant that matters (no class's methods appear non-contiguously)
with a synthetic multi-method-class test, since the real fixture's classes are all
single-method and couldn't have caught a bug here.

**What I changed:** Wrote `eval/tools/run_baseline_real.py` as a new committed tool (the
2026-10-10 F1-only run was an uncommitted one-off script, per that entry's own evidence log) so
this run is reproducible, not ad hoc, and captures each case's reference signature by running
`[polluters..., victim]` once for real rather than reusing stored report JSON (keeps the same
mechanism across all 4 cases instead of mixing "read from a file" and "run fresh").

**How it was verified:** `py -m unittest eval.tests.test_baseline -v` → 13/13 passed. Mutation
check: reverted the new shuffle function to the old plain whole-pool shuffle, re-ran the new
test alone — failed immediately with a class split across a non-contiguous run, confirming the
test isn't vacuous; restored, re-ran clean. Real run via `py eval/tools/run_baseline_real.py`
(native Windows, JDK 24, real Maven classpath, real JVMs): found the bug in every one of 16
trials (4 cases × 4 seeds); F1's numbers (1, 1, 3, 2) came back byte-for-byte identical to the
2026-10-10 entry's, which is itself a form of verification (same inputs, same seeded RNG, same
real runner → same result).

**Errors found:** The 2026-10-10 evidence entry's F1 pool description ("7 tests, 5 noise
tests") doesn't match `ground_truth.json`'s real `benign_noise_tests` (4 noise tests, pool of
6) — a documentation miscount from that earlier session, not a code bug (the actual candidate
set, and therefore the result, never changed). Found by recounting against the real fixture
file while writing this run's own pool description, not told by anyone.

**Rejections:** None.

Ownership checkpoint: be able to explain why a plain `rng.shuffle()` over the whole candidate
pool was wrong (it can produce an order no single JVM run of JUnitCore can execute) and why the
synthetic multi-method-class test, not the real fixture, is what actually exercises that fix.

## 2026-10-11 — Close ADR-002, C6/C7 wording, stale register rows (LeftWorkForM1&M3.md, M3 #2/#4/#6)

**What I asked:** Same `LeftWorkForM1&M3.md`, items 2 (tick ADR-002), 4 (stale A5/A8/A9
register text) and 6 (claim E5's contradiction note, and the C6/C7 "two hops" vs. depth
wording M1 asked for).

**What was retained:** The specific numeric correction for C6/C7 (depth 5, not depth 3) came
from re-reading claim E11's own already-recorded real measurement, not generated fresh — I
checked the ADR-002 N+1 conversion formula against E11's number myself before writing anything,
rather than trusting the formula or guessing a number.

**What I decided not to do:** Did not touch ADR-002's own top-level `Status: PROPOSED` line
(the task list only asked that of Member 1, for ADR-001, which they own; ADR-002 is also
Member-1-owned, and ADR-007/ADR-008 are left the same way in this repo despite full agreement).
Did not act further on claim E5/E6: read `docs/07-Defense/decisions/cdr-gated-module.md` in
full and found the "contradiction note" it points to already resolves the apparent
contradiction with a ready panel answer — nothing to fix in this repository; E6's remaining
work (auditing the slide deck and proposal document) is outside it.

**How it was verified:** `py -m unittest discover -s eval/tests -v` → 85/85 passed (a sanity
check; this session's changes here are documentation only, verified by re-reading the exact
claim/ADR text being corrected against the real evidence it cites, not by running code).

**Errors found:** None new in this entry — these were documentation corrections against
already-recorded real evidence (E11), not new bugs.

**Rejections:** None.

Ownership checkpoint: be able to say, without checking anything, which Mid-Eval status docs
were stale before this session (A8/A9, W4/W9/W14) and why — each had a "pending X" note that
was already resolved weeks or days earlier by a merged PR, not an ongoing gap.

## 2026-10-11 — Real F3/F4/N3 reports; fix stale eval/reports/README.md and members.md

**What I asked:** Relayed Member 2 message: `eval/reports/` still only has f1/f2/n1/n2.json
even though F3/F4/N3 have been real, reproducible outcomes since PR #49/#52 landed, and its
README still says "F3 needs W10, not implemented yet"; also `members.md`'s M3 row still said
a branch (PR #54) was unpushed after it had merged.

**What was kept:** Used `runner.cli.resource_fields()` (Member 2's own public function) for
F3/F4's resource evidence rather than writing a second combination function in my own script —
checked it existed and did exactly what I needed (ADR-007's multi-polluter combine, already
exercised by the real CLI) before using it, rather than re-deriving the logic myself.

**How it was verified:** Real run, `py eval/tools/run_w9_integration.py` (native JDK 24, all 7
cases): every outcome matched `ground_truth.json`'s `expected_outcome` exactly (F1-F4
`VERIFIED`, N1/N2 `VICTIM_FAILS_ALONE`, N3 `NOT_REPRODUCED`). Specifically checked F3's two
required polluters both appear (one shown, one named per ADR-007), F4's `reproducing_seed=1`,
and N3's limitation text reads "discovered order (plus 31 shuffled order(s))" — the exact
wording PR #52 fixed, now confirmed against a real `diagnose()` run rather than only the
hand-built `DiagnosisRuns` objects that fix's own tests used. `py -m unittest discover -s
eval/tests -v` -> 85/85, unaffected (sanity check).

**Errors found:** Both gaps Member 2 named were real: `eval/reports/` was genuinely missing 3
files, and `eval/reports/README.md`'s "What's NOT here yet" section was genuinely stale (said
F3 was blocked on Member 2, when it had been unblocked for weeks — the committed files just
hadn't been produced from the real run yet).

**Rejections:** None.

Ownership checkpoint: be able to explain why F3/F4's resource-evidence call goes through
`runner.cli.resource_fields()` rather than a second hand-rolled combination here, and what
`order_exploration.reproducing_seed=1` on F4's real report actually means (the discovered
order alone never finds the bug; the first shuffle tried, seed 1, does).

## 2026-11-18 — W19: verdict contract v2 (ADR-010), schema v2, fixture N4

**What I asked:** Pick up Iteration 2 and start M3's own work. Reviewed the current state
(pulled `main`, read ADR-010/011, `docs/10-Final1/iteration-2-plan.md`, `members.md`) and
identified W19 as the right starting point: M3's biggest owned package, with its only
prerequisite (W17) already done and step 1 (M2's `RunTally`/`classify`) already merged and
waiting on my review. Asked for: review step 1 first, then build M3's part — `decide()`, the
schema, `assemble_report()`, and fixture N4 — to the ADR-010 decision table.

**What was retained:**
- `eval/outcome.py` — the full rewrite (13-row decision table, `DecisionInput` on `RunTally`s,
  `candidate_reasons`). Reviewed row by row against the ADR-010 table text before accepting.
- `eval/report.py` — the full rewrite (reads tallies directly, handles `INCONSISTENT`, the
  "no test is blamed" rule, `resource_edges`/`assurance`/`candidate_reasons` in the report).
- `eval/schema/report.schema.json` v2, and the matching rewrites of `eval/tests/test_outcome.py`,
  `test_report.py`, `test_examples.py`, `test_schema_validator.py`, plus the 9 example JSON
  files under `eval/examples/` (one new: `example_victim_fails_alone_differently.json`).
- `fixtures/od-fixture/src/main/java/odfixture/DualFailureState.java` and the two N4 test
  classes, `ground_truth.json`'s N4 entry, `eval/benchmark/manifest.json`'s N4 row, and
  `eval/tools/run_w9_integration.py`'s `run_n4()`.
- `docs/contracts/report-schema.md` (rewritten for v2) and `docs/03-Design/certificate-contract.md`
  (updated to say what's now built vs. still accepted-but-pending, ADR-011/W20).

**What I changed / pushed back on before accepting:**
- The first draft of `eval/outcome.py` derived rows 4/5 ("no real failure anywhere") from the
  `alone`/`sequence` `RunTally`s alone. I caught this myself by writing `test_outcome.py`'s
  row-by-row tests and reasoning about which rows could actually be reached given the earlier
  rows' preconditions — rows 10/11 turned out to be mathematically dead code under that
  derivation, since by the time row 11's precondition holds, rows 4/5 would already have fired.
  Required adding `reference_established`/`infrastructure_failures_anywhere` as their own
  `DecisionInput` fields (computed in `eval/report.py` from `diagnosis.reference_signature is
  not None` and the existing cross-phase infra count respectively) rather than deriving
  everything from two tallies.
- `assurance.sequence.deletion`'s `"NOT_YET_CHECKED"` value is not in ADR-011's own four-value
  table. I considered reusing `NOT_APPLICABLE` but rejected it myself (that value means "no
  polluter was found" in ADR-011 — a different, false claim here) and added the new value
  instead, explicitly flagged in code, `docs/evidence-m3.md`, and the register as my own
  addition for the team to confirm, not something I decided unilaterally belongs in the shared
  contract.
- Deliberately did **not** build ADR-011 §2's "free" single-polluter deletion check in this
  session, even though the data to do it already exists (the alone tally) — it's explicitly
  one of ADR-011's own tests (T4), which is W20's work, not W19's. Left as a note for W20
  rather than quietly finishing part of another work package early.
- A real schema bug surfaced only when running against the real fixture (not caught by any
  hand-built test): `failure_signature`'s null-vs-non-null rule was tied strictly to
  `unresolved_reason`, but `SOURCE_INTEGRITY_FAILED` can legitimately co-occur with a
  never-established reference (null signature) too — the rule couldn't see that. Loosened the
  schema rule and moved the real invariant into `eval/report.py`'s own tests.
- Found that `runner/cli.py` (two lines) and `runner/tests/test_cli.py` (its shared `runs()`
  helper, 11 call sites, plus one behavioural assertion and one whole test) would break on
  schema v2 — a cross-member-boundary issue. **Did not fix this myself without asking**: used
  `AskUserQuestion` twice, once for the 2-line `cli.py` rename and once for the larger
  `test_cli.py` fix, and only touched either file after Zarpash said yes both times. Both edits
  are flagged in code comments and `docs/evidence-m3.md` as things for Member 2 to actually
  review, not things Member 2 agreed to — that distinction matters and is stated explicitly,
  not glossed over.

**How it was verified:**
- `py -m unittest discover -s eval/tests` → **119/119 passed** (up from 85 before this session).
- `py -m unittest runner.tests.test_cli -v` → **63/63 passed**, confirmed on a clean rerun. The
  first run (backgrounded while I was still writing N4's `.java` files) showed 3 failures, all
  traced to the source-integrity checker correctly catching my own concurrent file writes mid-
  diagnosis — not a bug in the change itself; rerunning cleanly after the files had settled
  confirmed this.
- `py -m unittest discover -s evidence/tests` → 39/39 passed (sanity check; nothing in
  `evidence/` touched).
- `mvn -B -q -f fixtures/od-fixture/pom.xml test-compile` → clean compile of the new N4 classes.
- `py -m eval.tools.run_w9_integration` (real `diagnose()` + `evidence.extract` +
  `assemble_report()`, all 8 cases) → F1–F4 → `VERIFIED`, N1/N2 → `UNRESOLVED(VICTIM_FAILS_ALONE)`,
  N3 → `UNRESOLVED(NOT_REPRODUCED)`, **N4 → `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)`** —
  every one matches `ground_truth.json`, and F1–F4/N1–N3 are byte-for-byte unchanged in verdict
  from before this session (ADR-010 test T6). The 8 real reports are committed at
  `eval/reports/{f1,f2,f3,f4,n1,n2,n3,n4}.json`.

**Rejected / not done:**
- `ui/web/src/lib/report.ts` still reads v1 field names — explicitly Member 2's follow-up per
  ADR-010's own Consequences section; not touched (TypeScript, outside this session, and
  explicitly assigned elsewhere).
- `runner/diagnose.py`'s old scalar `DiagnosisRuns` fields and the `NO_SINGLE_POLLUTER` alias
  are still there, even though ADR-010's "order of work" says they're removed "when W19 reads
  the tallies" — removing them would mean rewriting ~20 lines across `runner/tests/
  test_diagnose.py`, which I did not do without a specific ask; flagged as a follow-up instead.
- M1's independent reproduction of T1–T5 (FT003's acceptance criterion) is not done here — it
  is explicitly her verification step, not mine.

Ownership checkpoint: be able to explain why `decide()` checks `reference_established` as its
own input rather than deriving it from the `alone`/`sequence` tallies (the ADR-011 motivating
case: a reference found during the search does not guarantee the final re-verified sequence
still shows it), why `assurance.sequence.deletion` can say `"NOT_YET_CHECKED"` — a value not in
ADR-011's own table — and why `polluters`/`shared_resource` are both suppressed together (not
just `polluters`) whenever a verdict is withheld.

## 2026-11-18 — W16: verify M2's retire-claims work, finish M3's own part

**What I asked:** Continue Iteration 2 after W19; picked W16 next because both M1 and M2 had
just pushed their parts (M2's already merged, M1's on an open branch) and M3's own part
(`eval/`) plus the overall "checks consistency" role were the only pieces left undone.

**What was retained:** The one real fix found — `eval/report.py`'s deletion-check limitation
text reworded to reuse `runner/cli.py`'s exact approved phrase ("reduced by single-trial delta
debugging; not deletion-verified") instead of my own paraphrase from W19, plus the matching two
example JSON files, plus the reports regenerated so the committed files stay consistent with
the code.

**What I changed:** Nothing generated needed correcting here — this was mostly verification
(reading M2's already-merged code, confirming it matches ADR-010/011's exact wording) rather
than new generation. The one thing I pushed back on myself: my first instinct from the grep
output was to start "fixing" dozens of hits across `docs/01-Literature/`, `claims-ledger.md`
etc. before actually reading each one in context — stopped and read every hit first, which
showed almost all of them were already-correct approved wording, historical notes, or another
paper's own terminology, not FlakeTrace claims. Only the one real inconsistency (above) needed
a change.

**How it was verified:** `py -m unittest discover -s eval/tests` → 119/119 OK (wording-only
change, no behaviour change expected or found); real `py -m eval.tools.run_w9_integration`
re-run → all 8 verdicts unchanged, confirming the fix only touched `limitations` text.

**Rejected / not done:** M1's `evidence/` wording branch not reviewed in depth — it's not
merged to `main` yet, so there is nothing yet to check for consistency against; flagged to
re-check once it lands, since her branch and this session's doc edits (`members.md`,
`iteration-2-plan.md`, `genai-register.md`) touch some of the same files and could conflict.

Ownership checkpoint: be able to explain why `runner/cli.py` already had the correct wording
before this session (M2's own earlier, separate work) and what exactly W16 added on top of
that (only a product-wide consistency check plus one small text fix in `eval/report.py`).

## 2026-11-19 — W26a: the first real case (fastjson FJ-03), steps 1-5

**What I asked:** Continue to W26a next (the real-case protocol), since it was flagged as
startable without anything new per the critical path. Asked to actually fetch, build and run
the case for real, not just read the protocol document.

**What was retained:** `eval/real-cases/fj03/order.txt` and `premise.json` (the real step-2
tallies), the protocol document's Findings section, the new risk-register entry, and every
status-doc update above.

**What I changed / decisions I surfaced rather than made myself:** This session had three real
forks where I stopped and asked rather than deciding alone:
1. fastjson needs real JDK 8; this machine has none. Asked whether to download a portable
   Temurin 8 zip or start Docker Desktop (M1's earlier fastjson work used a container) — the
   member chose the download, which needed explicit permission anyway (downloading a file).
2. The real shuffle search found something genuinely surprising (0/31 reproduced, even with
   the known polluter's methods placed before the victim in several shuffles) before I
   understood why. Investigated it myself first (checked which shuffles actually had the
   polluter before the victim, then inspected one in full detail) rather than asking the
   member to interpret a result I hadn't explained yet — found the real mechanism (other
   `SerializeWriterTest_N` variants reset the same state) before presenting it.
3. Two real forks needed the member's call, not mine: how to frame the shuffle-search result
   (accept it as a finding, or spend more JVM time on a bigger budget first), and how to
   handle the `runner/discovery.py` blocker (ask M2 to fix it, switch cases, or stop). Both
   times I laid out the real trade-off with what I'd already found, not a vague "what should I
   do?" — the member chose: accept the finding, and flag `discovery.py` for M2 rather than
   patch it myself or avoid it by switching cases.

**How it was verified:** Every number in this session is from a real run, not inferred: the
build (`BUILD SUCCESS`, exact file counts matching [[evidence-m1]]'s own Phase 5 count), the
10/10 premise tallies, the natural-order PASS, the 31-shuffle search's real outcome, and the
one-shuffle inspection's actual intervening test list — all re-checked against
`POC/results/scan_FJ-03.csv`'s pre-existing real data (its 524-candidate count, its 6
`od_relevant` rows, all `SerializeWriterTest_14`/`_15`) rather than asserted from memory.

**Rejected / not done:** Did not patch `runner/discovery.py` myself — flagged it instead,
twice (risk register, evidence log), since reading a project's actual Surefire configuration is
a real design decision belonging to M2's file, not a 2-line mechanical fix like this session's
earlier `runner/cli.py` rename. Did not try FJ-04 or the ormlite-core fallback case — reasoned
(not just guessed) that FJ-04, being in the same fastjson package, would very likely hit the
identical gap, so trying it would not add information the discovery.py finding doesn't already
cover.

Ownership checkpoint: be able to explain why the natural discovered order doesn't reproduce the
bug (alphabetical: M before S), why 31 random shuffles still didn't find it even when some
placed the right class first (other tests in between reset the state), and why that is a
genuine result about search quality, not a bug in the fixture or a reason to doubt step 2's
premise confirmation.

## 2026-11-19 — A1 fail-safe fix: F3 now honestly `CANDIDATE`, not `VERIFIED`

**What was asked:** reverse my own W19 design choice (made and flagged for review on
2026-11-18) where `deletion_status=None` satisfied claim S3 to avoid regressing F1–F4 to
`CANDIDATE`. The member's explicit instruction: make it fail-safe — an unestablished claim
should never count as established, even though it changes F3's reported outcome from
`VERIFIED` to `CANDIDATE`.

**What I kept:** the 13-row decision table's structure and all other rows unchanged — this is a
one-line guard change (dropped `is not None` from row 12's check) plus one new, real computation
in `eval/report.py` (ADR-011 §2's free deletion check for a single kept polluter), not a
redesign.

**What the member changed / decided:** nothing code-level — this was my fix on explicit
instruction, written test-first (new test asserted CANDIDATE, confirmed it failed against the
unfixed `VERIFIED`-producing code first, then fixed). The member will decide, when reviewing
`git diff --staged`, whether the three mid-eval-report chapter edits (below) read right in their
own words.

**How it was verified:** test-first (ran the new assertions against the unfixed code, saw them
fail with the wrong outcome, then fixed and reran green); full `eval/tests` suite 120/120; real
`eval/tools/run_w9_integration.py` rerun confirms F1/F2/F4 stay `VERIFIED` and F3 now reports
`CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]`, matching `eval/outcome.decide()`'s own table exactly
— not asserted, checked against the actual real-run output.

**What I rejected / flagged rather than did myself:** did not edit M1's or M2's mid-eval-report
chapters or `docs/07-Defense/claims-ledger.md` row E14, even though both now contain a stale
"F3 ... VERIFIED" claim this same fix makes wrong — flagged both in `docs/evidence-m3.md`
for the owning members, per `mid-eval-report/CLAUDE.md` §2 and root CLAUDE.md §1. Did fix the
same issue in my own three owned files (`chapter8_testing.tex`, `chapter4_requirements.tex`,
`appendix_test_cases.tex`) since leaving a known-false claim in my own graded chapter would be
a bigger honesty problem than a narrow correction.

Ownership checkpoint: be able to explain, without this log, exactly why F1/F2/F4 get a *free*
deletion check (the alone run, already clean, already proves "removing the only kept polluter
makes the victim pass" — that is ADR-011 §2's rule) while F3 does not (two required polluters
means removing either one alone still isn't the full removal-check ADR-011 asks for — no JVM
runs exist yet that check "remove both together", only the `ddmin` search that *found* them),
and why that is a real gap (W20), not a bug in `ddmin` or in the fixture.

## 2026-11-20 — Merge with M2's PR #106, and a self-caught mistake about the Mid report

**What was asked:** the member's `git push` was rejected (branch diverged); their own `git pull`
surfaced that M2 had pushed real, overlapping work to the same shared branch. Resolve the
conflicts without running `git merge`/`git checkout --theirs`/`git add` myself.

**What I kept vs. changed:** kept M2's `eval/report.py` implementation of the same fail-safe
over my own (theirs was more complete — real ADR-011 vocabulary, M1's W21 edges, a defensive
re-check rather than relying on `decide()`'s row order), compared deliberately rather than
defaulting to "mine wins" or "theirs wins". Kept my own `eval/outcome.py` guard as harmless
defense-in-depth since it didn't conflict.

**A mistake I caught myself, by testing rather than trusting the diff:** M2's commit also made
the Mid report's generated table a closed record checked against tag `mid-eval-v1`, not live
data — I only found this by actually running the new CI step locally
(`git archive mid-eval-v1 eval/reports`, then the generator against it), which crashed with
`KeyError: 'matched'` because my own earlier schema-rename fix assumed every report would move
to schema v2. Fixing that crash made me realize my entire premise for touching the Mid report's
chapters *at all* this session — both today's F3/N2 edits and yesterday's N4-driven ones — was
wrong: the chapter's own text ("regenerated... so it is current") misled me into treating a
closed, graded, tagged document as a living one. Reverted all four touched chapters to
byte-identical with the tag, verified by `git diff mid-eval-v1 -- <file>` printing nothing.

**How it was verified:** reproduced M2's new CI check locally before and after the `rate()`
fix (crash, then clean run); `git diff mid-eval-v1 --` on every touched Mid-report chapter
prints nothing after the revert; `eval/tests` 123/123, `runner.tests.test_cli` 64/64 (real JVM)
on the merge-resolved code.

**What I rejected:** did not try to "fix" the Mid report's prose to describe current, honest
behaviour anywhere in these four chapters — the correct place for that is the Iteration-2 docs
(`evidence-m3.md`, `members.md`) and the future report v2 (W28), not a closed record.

Ownership checkpoint: be able to explain why the Mid report's generated table reads from the
`mid-eval-v1` *tag* in CI rather than the live `eval/reports/` directory, and why that is a
correctness requirement (a graded, submitted PDF cannot retroactively change what it reported)
rather than a stylistic choice — and why my own three earlier attempts to "keep it in sync with
live data" were a real mistake, not a harmless extra effort.

## 2026-11-20 — W20: the real deletion check lands, F3 reaches VERIFIED for real

**What was asked:** M2 (relayed by the member) landed W20's runner half (PR #121,
`DiagnosisRuns.deletion_checks`, Interface 4) and asked me to build the report half: read the
real checks, set `deletion_status` accordingly. He noted real F3 gives both polluters `NEEDED`,
so F3 should reach `VERIFIED` once my half reads it, and flagged two specific things to fix:
the now-false "W20, not yet landed" limitation text, and the new per-run `removed`/`round`
fields on the record.

**What I kept vs. built new:** kept A1's overall shape (compute `deletion_status`, feed it to
`decide()`) but replaced its single-polluter-only logic entirely with Interface 4's real rule —
read every check, use only the highest round, map to VERIFIED/INCONCLUSIVE/INCOMPLETE by the
contract's own priority table. Test-first throughout: wrote `FakeDeletionCheck` and a new test
class before touching `eval/report.py`, confirmed the real failures, then implemented.

**A judgment call I flagged rather than guessed past:** Interface 4's table lists "all NEEDED"
before the "any `runs.n < 10`" row, which read literally lets an all-NEEDED set with too few
trials still reach VERIFIED. I implemented the stricter reading (short-run disqualifies
VERIFIED regardless of label) since that matches the statistical reasoning ADR-011 itself gives
for why `m` matters — but this is my own interpretation of an ambiguous contract, not something
M2 or M1 confirmed, so I wrote it into both the code comment and `docs/evidence-m3.md`
explicitly as open for correction, rather than silently picking one reading and moving on.

**A real bug I found and fixed in my own tooling, not anyone else's:** regenerating the real
reports, I noticed `execution_record_reference` was an absolute path with my own Windows
username in it. Checked `git show HEAD:eval/reports/f1.json` before assuming it was new —
it was already committed, from my own earlier regenerations this session. Traced it to
`eval/tools/run_w9_integration.py`'s `RECORD_DIR` (always absolute by construction) and
confirmed `runner.diagnose.diagnose()` itself never relativises it either (correctly, for a
real end-user installation — the bug is specific to a script that commits its output to a
shared repo). Fixed with a small wrapper, re-ran, confirmed clean with a repo-wide grep for the
username rather than trusting the fix by inspection alone.

**What I rejected / left for others:** did not fix `runner/tests/test_cli.py`'s now-failing F3
test or claims-ledger row E14 (both now stale, both M2's) — asked the member each time rather
than deciding for myself whether a cross-boundary fix was "small enough"; both times the answer
was to leave it for M2, so I documented the exact break instead of guessing at the fix. Did not
close claims-ledger row G2 despite the real check now existing — Interface 4's own plan names
M1's independent reproduction as the last step, which hasn't happened.

Ownership checkpoint: be able to explain, without this log, exactly why `eval/report.py` reads
only the checks at the *highest round* (not every check ever recorded) — a dropped test's own
`NOT_NEEDED` entry from an earlier round stays in `deletion_checks` for visibility, but the
final kept polluters' last word is what decides the verdict — and why a kept polluter with *no*
check at all must never be read as VERIFIED, even though that never happens in the real
pipeline today (every found-polluter diagnosis always produces at least one check per kept
test). That fail-safe is for a caller that predates W20 or a future budget cutting a check off
entirely, not a case you can currently trigger through the CLI.

## 2026-11-20 — W24 budget ledger, report half

**What I asked for:** implement M3's half of Interface 6 (`docs/contracts/interfaces.md`) —
the two report rules and the schema's `budget` field — against M2's already-merged
`runner/budget.py`, test-first, same as W20.

**What I kept vs. built new:** kept the established shape entirely (a new `DecisionInput`
field read only in `decide()`'s S1/S3/R1 block; an optional report field that mirrors
`_order_exploration`'s "omitted when the producing data doesn't exist yet" pattern). Nothing
here is a new design — it is W20's own pattern applied to a second contract.

**A naming decision I made that the contract leaves implicit:** Interface 6 describes the rule
in prose ("status `POLLUTER_FOUND` with `exhausted = True` adds `BUDGET_EXHAUSTED` to
`candidate_reasons`") but does not name the `DecisionInput` field that should carry it. I named
it `verification_budget_exhausted`, deliberately distinct from the existing `budget_exhausted`
field (which is for a search that found no polluter at all and short-circuits to `UNRESOLVED`
at row 3) — reusing one field for both would have made a polluter-found-but-unverified
diagnosis wrongly route to `UNRESOLVED` instead of `CANDIDATE`. Flagged this naming choice in
both the code's own docstring and `docs/evidence-m3.md` rather than silently picking it, since
it is a new symbol the other two members have not seen or agreed to by name (only the
*behaviour* was agreed, in the WhatsApp thread M2 recorded).

**What I verified rather than assumed:** read M2's actual, already-merged `runner/budget.py`
and `runner/diagnose.py` before writing anything, to confirm `run_steps` really does attach a
`BudgetAccount` to *every* diagnosis now (not only one made with an explicit `--budget-
invocations`) — the contract's own line "without a limit nothing changes ... with
`budget.exhausted = false`" depends on that. Also confirmed, by reading `_steps`' two call
sites of its `budget_exhausted()` helper, that a `BUDGET_EXHAUSTED` diagnosis can carry either
a null or a real failure signature (the cut can happen before or after a reference was
established during `reproduce`/`shuffle`) — the same row-5-vs-row-11 shape `NOT_REPRODUCED`
already has — and wrote a test for both, rather than assuming only one shape occurs.

**What I deliberately left out:** did not add the `budget` field to the ui/web TypeScript
`Report` type or its tests (M2's folder, `ui/`) — out of scope for the report half, and the
field is optional/additive so the existing UI keeps working unchanged against it. Did not run
a real F2 diagnosis under a budget limit — Interface 6's own ordering puts that step after
both halves are merged ("together, once merged"), not before.

Ownership checkpoint: be able to explain, without this log, why `verification_budget_exhausted`
is checked only inside `decide()`'s `reasons = []` block and never as an early return like
`budget_exhausted` — a polluter that WAS found with incomplete verification is a *weaker*
result than one never found at all, not a different category of failure, so it has to compete
with S1/S3/R1 for CANDIDATE the same way a missing deletion check does, rather than overriding
every other check the way row 1-3 do.

## 2026-11-20 — merging W24, fixing the CI break, and the real evidence run

**What happened:** after handing off the W24 commit, the member reported the `runner` CI check
failing on the pushed PR. Diagnosed it against the real GitHub API (check-run annotations, job
step list) rather than guessing, then reproduced the exact failing CI step locally with a
portable JDK 8 found from an earlier session's scratchpad extraction. The failure was a stale
placeholder test of M2's own (`runner/tests/test_cli.py`, docstring literally said "Until M3's
W24 half"), asked and was told to fix it. Two merge conflicts followed (two newer PRs landed on
`main` meanwhile); resolved both by keeping both sides' table rows, verified with a
programmatic (not manual, to avoid transcription error on very long lines) row-level Python
edit for one of them, confirmed no conflict markers remained repo-wide, and had the member
commit and push. PR merged; all 5 CI checks green.

**What I did once merged, without being asked step-by-step:** the member said "complete the
rest of the work" — read that against Interface 6's own ordering ("together, once merged: a
real F2 run with a limit just above B2's minimum, and one with no limit") rather than guessing
at a bigger scope. Computed B2's minimum for F2 by hand from the real committed report's
`original_failing_order` length (8) and `reserve(20)=60`, rather than asking the member for it
or assuming a round number. Ran both diagnoses for real, read the written `.report.json` files
back and validated them against the schema explicitly (not just trusting `assemble_report`
didn't raise), and cross-checked the no-limit run's numbers against M2's own earlier recorded
numbers for the same victim — matched exactly, which is real evidence of determinism, not an
assumption.

**What I deliberately did not do:** did not overwrite the committed `eval/reports/f2.json`
with either new run — that file has fixed downstream readers (`ui/web` tests, the Mid report's
frozen-tag table) unrelated to this change, and nobody asked for it to be regenerated. The two
new reports stayed in a scratch records folder, referenced only from the evidence doc.

Ownership checkpoint: be able to explain why a budget limit of 72 for F2 gives
`UNRESOLVED(BUDGET_EXHAUSTED)` at all — the reserve (60, for the alone check plus one
candidate-pair check) plus the one reproduce run (8) already leaves only 4 invocations for
search, which buys exactly 2 of the 7 candidate pairs before the ledger refuses the third — not
a bug, the exact B3/B5 arithmetic Interface 6 specifies.

## 2026-11-20 — W23 evidence bundle and recount checker

**What I asked for:** after a status review showed W23 (ADR-013's bundle format + recount
checker) as fully unblocked M3 work, with nothing of mine waiting on another member, the
member said "start working" — I picked W23 over W25's measurement tool because it's listed
first on the critical path into W26b and nothing had been built for it at all yet (checked
`eval/` and `runner/` on `main` before starting, not assumed).

**What I read before writing anything:** the full ADR-013 text, then `runner/recording.py`,
`runner/diagnose.py`'s header-building code, `runner/search.py`, `runner/verify.py` and
`runner/deletion.py` — specifically to find the *exact* rule each tally in a report comes from
(which record lines, in what order, classified against which reference), rather than
approximating it. Found, by reading `runner/deletion.py`'s own comment, that M2 had *already*
added the `removed`/`round` note fields ADR-013 asks for to deletion-run lines — the capture
side was further along than the plan doc's prose suggested, so I didn't need to ask for
anything there.

**A scope decision I made and documented rather than silently expanding:** faithfully
replicating every status branch of `runner.diagnose._steps()` (including INCONSISTENT and
BUDGET_EXHAUSTED, which have no "verify" phase at all) would have meant reimplementing a large
share of the runner's own internal control flow inside `eval/`, for two statuses that don't
appear in any of the real committed example reports. I built exact recount coverage for the
three shapes that do (POLLUTER_FOUND/CANDIDATE/VERIFIED, VICTIM_FAILS_ALONE/_DIFFERENTLY,
NOT_REPRODUCED-with-no-reference), and made `verify_bundle` say explicitly that the other two
aren't covered yet, rather than quietly producing a possibly-wrong recount for them. Also
decided to redact by trying both path environments (`eval.outcome`'s own `deletion_status`
priority rule is duplicated here, not imported, because this module works from recounted
record data, not a `runner.diagnose.DiagnosisRuns` — flagged in the code as a drift risk if
Interface 4's rule ever changes).

**A real bug I only found by actually inspecting the real output, not by reasoning about the
code:** my first redaction pass looked clean in every unit test (which all use a hand-built,
backslash-only header), but bundling a real diagnosis's real record left the home directory
username sitting in the bundle's `manifest.json` and `record.jsonl`, in the `command` list's
`--records` path — written with forward slashes by this machine's bash-like shell, which a
plain string-replace against `Path.home()` (backslash-style) never matches. Caught it only by
running `grep -c zarpa` on the real bundle's own files after creating it, the same way the
checksum/recount design itself insists on checking the actual artefact rather than trusting the
code that produced it. Fixed, added a permanent regression test, re-ran the real bundle and
confirmed zero hits before calling this done.

**What I deliberately left out:** did not migrate `eval/reports/*.json` to bundles for F2-F4 or
N1-N4, and did not touch `ui/web` or `mid-eval-report/`'s generated table (both still read
`eval/reports/*.json` directly) — that migration is ADR-013's own "Consequences" list, a
separate, larger, cross-cutting change with other members' dependents, not part of W23's own
"done when". Did not attempt `python -m runner replay` (M2's half of ADR-013, explicitly) or
full `java -version`/`mvn -v` banner capture (would need a runner-side change to the record
header, also M2's territory) — `replay.md` and `environment.txt` are honest about using only
what the record header already carries today.

Ownership checkpoint: be able to explain, without this log, why `verify_bundle` recomputes the
reference signature *twice*, in two different ways, depending on whether a real failure ever
showed up in the "reproduce"/"shuffle" phase at all — and why that split exactly mirrors
`runner.search.reproduce()` versus `runner.verify.repeat_without_reference()`, not an
arbitrary choice of mine. Also be able to explain why deleting one "alone" line and then
*fixing the checksum to match* still gets caught: the checksum only proves the file wasn't
tampered with after bundling, while the recount independently re-derives the numbers from
whatever the file actually contains now — two different guarantees, not a redundant pair.

## 2026-11-21 — the format moved out from under a half-built PR

**What happened:** the member said there were merge conflicts on the W23 branch again.
Checking `main` before touching anything (the established habit by this point) showed more
than the usual append-only-doc conflicts: M2 had built and merged a real bundle writer and
replay command (`runner/bundle.py`, `runner/replay.py`) against a new, more detailed **Interface
8** that the team agreed the day after I built my own `eval/bundle.py` from ADR-013 directly.
My manifest shape, folder-naming rule and redaction approach were all different from the real,
already-merged one — not a text conflict at all (no file I touched and no file M2 touched
overlapped), a design one that a line-based merge would never surface.

**What I did, not what I was told to do:** nobody asked me to notice this — the task was "fix
the merge conflicts," and the three actual conflicts (the usual append-only docs) would have
resolved in five minutes with no further action. I kept reading past them because the git log
itself (`m2/w23-replay-code`, `m2/w23-replay`) named the same work package I was mid-PR on,
which was reason enough to go look at what landed before assuming three doc conflicts were the
whole story. Read `runner/bundle.py` and `runner/replay.py` in full before changing anything of
mine, specifically to find the one new, unsignposted-in-the-docs detail that mattered most for
correctness: a replay bundle's reference signature lives in the record header, not re-derived
from a search phase that does not exist for a replay (I would have silently mis-recounted every
replay bundle without having read `runner/replay.py`'s `replay_steps` directly).

**A judgement call on scope, made and stated, not quietly decided:** rather than patching my
old `create_bundle` to also emit Interface 8's shape (keeping two writers alive, which the
interface itself says not to do), I deleted it outright and rebuilt `verify_bundle` purely as a
*reader* of `runner.bundle`'s real format — matching the ownership split ("one writer") the
team had just agreed, not my own earlier, now-overtaken reading of ADR-013.

**What I verified rather than assumed:** rewrote every unit test to build its bundles through
the real `runner.bundle.write_bundle`, specifically so this module's tests are structurally
unable to drift from the real contract the way the first version's hand-rolled fixtures could
have. Then went one step further and ran the real CLI (`runner diagnose --bundle`) for real,
checked the new bundle's manifest.json by eye against Interface 8's own example, grepped all
five files for the machine username, and tampered a copy to confirm the failure mode too —
not just "the unit tests pass," which could still hide a format mismatch if the tests
themselves were wrong about the contract.

**A tooling mistake along the way, caught before it reached a commit:** tried to patch one of
the merge-conflict resolutions with an inline `python -c "..."` script containing backticks for
markdown code spans; bash command-substituted several of them inside the double-quoted string
before Python ever saw it (one, `` `eval/bundle.py` ``, was interpreted as "run this file as a
shell script," which is why the terminal filled with Python-syntax-as-shell-syntax errors).
Caught it by re-reading the file afterward rather than trusting the script's reported success,
found exactly one damaged fragment, fixed it directly. Lesson for next time: write content with
backticks to a script *file* and run that, never inline in a shell `-c` argument.

Ownership checkpoint: be able to explain why `eval/bundle.py` no longer writes anything at all,
and why that is a *better* design than the first version, not a downgrade — one writer means
the format has exactly one place in code that can drift from the contract, and `verify_bundle`
staying a pure reader is what makes it credible as an independent check in the first place (a
checker that can also write the thing it checks is not independent).

## 2026-11-21 — pulling main, answering two teammates, writing W32's task

**What I did without being told step by step:** the member relayed two real messages from M2
and M1, each with several items mixed together (status updates, a question, requests). Sorted
them before acting: some needed no action (G8 was already settled by the time I checked --
both messages' questions about it were already moot), one needed a real engineering decision
(keep or remove a duplicate bundle), one was a direct, explicit ask with a deadline implication
("I still need your acceptance task, written before any session") that I just did rather than
acknowledging and deferring.

**The duplicate-bundle decision, made and justified, not just picked:** M2 explicitly handed
me the call ("your folder, your call"). The easy, tidy-looking answer is to delete the "dirty"
one and keep a single clean bundle. I didn't take it — a `tool.dirty: true` bundle isn't a
mistake to clean up, it's an honest record of what actually ran, and having the *same* verdict
survive under two different JDKs and tool states is free corroborating evidence a reviewer
would otherwise have to ask for. Wrote the reasoning into the README itself, not just a commit
message, since the next person to find two F1 bundles needs to see it was a decision, not an
oversight.

**The acceptance task: designed against the real artefact, not written in the abstract.** Read
the actual committed `report.json` and the CLI's literal source line before writing a single
question, specifically so Q2's pass criterion ("points to the exact line or field") names text
that genuinely exists verbatim in the product, not a paraphrase I made up that a participant
could never actually find on screen. Made Q2 the one question that fails the whole task by
itself if wrong — a deliberate asymmetry, because FT018 exists to catch exactly one failure
mode (a practitioner reading `VERIFIED` as proof of cause), and a task that let two easy
questions outvote that one would defeat its own purpose.

**What I verified rather than assumed:** re-ran `eval.bundle verify` against both committed
bundles only after actually pulling `main` locally — not from reading the diff, since a
checker claiming to check a writer it has never actually been run against proves nothing. Both
exited 0 for real, which is the first time this session the two halves of Interface 8 have
checked each other without me controlling both sides.

**What I deliberately left alone:** M2's own "The case" section of `practitioner-check.md` is
still unwritten even though his bundle exists; I flagged it rather than filling it in myself —
it's recorded against his name in the protocol, and the honest-ownership rule in root
`CLAUDE.md` matters more here than finishing the document for him.

Ownership checkpoint: be able to explain why Q2 of the acceptance task is weighted the way it
is — not "all three questions matter equally" but "this one question is the actual thing FT018
is for," and why that asymmetry has to be decided and written down *before* the session, not
noticed afterward while scoring it.

## 2026-11-21 — W25 measurement, and a four-hour bug of my own making

**What happened, honestly:** built a one-off script to run the product's real
`rank_candidates` against all 524 real FJ-03 candidates (ADR-014 evidence item 5). It hung for
almost four hours. I did not just wait blindly — checked the process's actual CPU time against
wall-clock time repeatedly to confirm it was genuinely busy, not stuck, investigated OneDrive
and Windows Defender as plausible causes of slowness, and only found the real cause by doing
the arithmetic properly: timed one real candidate analysis in isolation (about two seconds) and
multiplied by 524 — the four hours did not remotely match that, which is what actually forced
me to go looking for a bug in my own code rather than accepting "JVM spawns are just slow" as
the explanation. The bug: my script auto-discovered the FlakeTrace repo root by walking up from
its own directory, which lived in a scratch folder *outside* the repo entirely — the walk-up
hit the drive root and spun forever, since `Path("C:\\").parent == Path("C:\\")`. The entire
first run, start to finish, did zero real analysis.

**What I told the user, and when:** as soon as I'd confirmed it with real evidence (the timing
math, not a hunch), not before and not after sitting on it. Also told them plainly that the
~4 hours of waiting was my own mistake, not an unavoidably slow computation — the honest
account, not a softened one.

**What I verified before trusting the fix:** ran the corrected version on a single real
candidate first and confirmed the timing matched my own prediction (~2s) before committing to
the full 524-candidate run again. Only let the full run proceed once the arithmetic actually
closed.

**A design choice under real time pressure:** added progress logging (flushed every 10
candidates) specifically so this class of problem — real work that happens to be slow vs. a
hang — would be distinguishable without another multi-hour guessing game. Structured the fixed
version to warm the `AnalysisCache` with a plain loop (so I control the progress printing) and
then call the real, unmodified `rank_candidates` on the warm cache for the actual scoring —
deliberately avoided reimplementing `rank_candidates`'s own scoring/sorting logic by hand a
second time, which would have risked a silent, undetected drift from the product's real
behaviour just to get a progress bar.

**What I did once the real numbers came back:** reported FJ-03's real result exactly as it
came out — zero evidence found, ranking changed nothing — rather than treating a "ranking
didn't help" result as a disappointment to soften. Then, before writing anything up, checked
whether M2 had already run the fixture-level comparison for real (he had, on F2) and
independently re-ran it myself rather than just citing his number — it matched exactly, which
is real corroboration, not an assumption that his report was correct. Ran F1, F3 and F4 myself
too, since item 4 asks for "the fixture," not one case, and F3's result (zero saving, because
`ddmin` dominates its cost, not the search order) is exactly the kind of inconvenient real
finding the honesty rules exist to protect — reported in full, not trimmed to the three cases
that look good.

Ownership checkpoint: be able to explain, without digging through this log, exactly why
`Path("C:\\").parent` equals `Path("C:\\")` and why that makes a naive "walk up until you find
the repo" loop unsafe for a script that does not actually live inside the repo — and why F3
showing zero benefit from ranking is not a bug in the ranking rule, but a correct consequence
of where F3's cost actually comes from (`ddmin`, not the pair search).

## 2026-11-21 — W23 finished, and my own tool caught its own bug

**What I did, briefly, since the member asked to move fast on real work:** bundled the
remaining 7 fixture cases for real, then ran `verify` against every one of them — not because
a checklist said to, but because that is the entire point of building an independent checker:
it is only worth anything if it actually gets pointed at real output, not just at the
synthetic fixtures I built it against.

**What I did when it found something:** `verify` flagged a real mismatch on N3 —
`reproduction.n` 20 vs. 51. I did not assume my own tool was right and the report was wrong, or
the reverse; read N3's real record first, counted the "reproduce" and "shuffle" lines by hand
(20 and 31), and only then went to `runner.diagnose._steps`'s own code to see which one of the
two numbers it actually produces for this case. The report's 20 was right; my recount's 51 was
the bug — a case where my own "independent recount" had quietly drifted from the thing it was
supposed to be checking, caught only because I ran it for real rather than trusting the
synthetic test suite's coverage. Wrote the regression test with the exact real shape (both
phases present) before touching the fix, confirmed it failed first.

**What I didn't do:** didn't treat the Windows permission error on N4's bundle write as a
reason to dig into `runner/bundle.py` (M2's file) — checked that no partial bundle was left
behind (confirming the existing cleanup logic already handles this case correctly), retried the
identical command, got the identical real result, and moved on. Not every failure is a bug to
chase; this one had a textbook signature (transient file lock, clean rollback already in
place) that didn't warrant treating M2's code as suspect.

Ownership checkpoint: be able to explain why `test_not_reproduced_shape`, which was already
passing, never caught this — it's not that the test was wrong, it's that it tested a real but
narrower shape (zero shuffle attempts) than the one N3's real diagnosis actually produced, and
a passing test only proves the shapes it covers, never the ones it doesn't.

## 2026-11-21 — W26b: running the real case instead of reasoning about it

**What I did, and why I didn't shortcut it:** once M2's `discovery.py` fix landed, I worked out
from the CLI's own code (`runner/diagnose.py`'s `_steps`) exactly what would happen if I ran the
real pipeline with `--order` pointing at the frozen known-pair file: the order truncates to one
candidate before the victim, so the single-polluter search has nothing to choose between across
policies, and I could have predicted the result and written it up without running anything. I
ran all seven real JVM invocations anyway — the member and ADR-014 both ask for real numbers,
not derivations from reading the code, and "I worked out what it would do" is exactly the kind
of claim the honesty rules exist to stop me from substituting for a real command.

**What I caught before trusting the first result:** every one of the first seven bundles came
back `tool.dirty: true`, breaking the clean-bundle precedent from W23. I didn't shrug past it —
traced it to a leftover `HANDOFF-M3-report.md` from October sitting untracked in the working
tree, confirmed from its own header that it was meant to be deleted once the Mid report was done
(it was), asked the member before deleting it since the delete itself needed permission, and
re-ran the whole matrix from a clean tree rather than keeping the first, dirtier batch.

**What I didn't do:** didn't treat the six remaining `tool.dirty: true` manifests (after the
first bundle in the clean re-run) as a second bug — checked the already-committed F1/F2-F4/N1-N4
bundles first and found the identical pattern there (only ever the *first* bundle of a batch is
clean, because every bundle after it is itself an untracked file sitting in the tree when the
next one runs). Recognising "this matches existing, accepted behaviour" instead of re-diagnosing
it from scratch saved real time without lowering the bar — I checked it was the same shape, not
just hoped so.

Ownership checkpoint: be able to explain, without re-deriving it live, why `--order` with a
2-entry file collapses the single-polluter search to exactly one candidate regardless of
`--policy` — and why that makes "ranked = original" on FJ-03 the mathematically forced outcome
of this case's search space, not a property of M1's ranking rule.

## 2026-11-21 — W27: the container had to actually run, not just build

**What I scoped out, and why:** `docs/02-Requirements/non-functional.md` describes a fully
hardened sandbox (rootless, no socket mount, network disabled, resource limits, read-only
base). W27's actual "done when" is just "a fixture diagnosis runs in the container on a second
machine" — a reproducibility image, not that sandbox. Building the full hardened profile when
only the pinned-toolchain version was asked for would have been scope creep dressed up as
thoroughness, so I built the smaller thing and said in the Dockerfile's own comment and in the
evidence log that the hardened profile is still a later target, rather than letting the two get
conflated.

**What I didn't skip:** a build that succeeds is not evidence the image works — I ran a real
fixture diagnosis inside it and checked the result against known ground truth (F1,
`VERIFIED (sequence)`, 67 invocations) before writing anything up. The bundle's own recorded
environment (a different Linux kernel, a different JDK 8 patch number than this host) is what
actually proves this ran somewhere independent, not just "docker build exited 0."

**A bug I caught by checking state, not by trusting a clean exit:** my first `docker run` with a
bind mount printed a normal, successful-looking report and exited 0 — but the bundle it claimed
to write was never on the host. Checking the mounted folder afterward (not just the container's
own stdout) is what caught it; a silent no-op mount is exactly the kind of failure that looks
identical to success until you check the actual file. Isolated it with a one-line throwaway
probe (`touch` inside a disposable container) before touching the real command again, rather
than guessing at the fix.

**What I left for M2 rather than fixing myself:** the bundle's `container_image` field is
always `null` — traced it to a hardcoded `None` in `runner/diagnose.py`, which is M2's file.
Recorded it as a known gap in the evidence log instead of patching his module myself.

Ownership checkpoint: be able to explain why `$(pwd)` works fine as the host side of a Docker
volume mount on Linux/macOS but not from Git Bash on Windows, and why a successful-looking
`docker run` output is not enough evidence that a bind mount actually worked.

## 2026-11-21 — W29a/FT015: didn't trust the finding's own framing, checked it from scratch

**What I didn't do:** FT015 says "L3 in one worksheet table and L2 in another, in the report and
in the register" — reads like the report and the register might be two of the inconsistent
sources. I didn't start editing either of them on that assumption. I counted the actual M3 rows
in the register dated up to the Mid cutoff first, then read the frozen report's own table — they
already agreed exactly (L2×18, L1×1). Editing either of the two sources that already agreed
would have been pure risk for a worksheet-only bug, including risking the frozen, tagged Mid
report, which must never be touched.

**What finding the worksheet took:** the worksheet itself isn't in the repository — "submitted
as PDF only" per FT013. It wasn't something to give up on; I searched the member's own Downloads
folder for it and found both the submitted `.docx` and its PDF, timestamped the morning of the
deadline. Reading its raw XML (no `pandoc` or LibreOffice on this machine) is what actually
found the bug: one cell in the worksheet's own summary table said "L3 (18 rows), L2 (1)" for me,
directly contradicting my own declaration a few hundred lines later in the *same file*. The
register and the report were never the mismatched pair — the worksheet was inconsistent with
itself, and FT015's wording just described it from the outside.

**What I fixed, and what I deliberately didn't touch:** edited only the one wrong cell in a
copy of the worksheet, verified byte-for-byte that nothing else changed (diffed extracted text,
validated paragraph counts with the skill's own tool), and left the actually-submitted `.docx`/
`.pdf` alone — that's a historical record of what was handed in, not mine to rewrite. Handing a
corrected worksheet to the supervisor and the signatures FT013/FT014 ask for are explicitly
outside what I can do from here; said so rather than treating the fixed file as "done."

Ownership checkpoint: be able to explain, without re-reading this log, why the register and the
frozen Mid report were never actually the inconsistent pair, and where in the worksheet itself
the real, self-contradicting cell was.

## 2026-11-21 — M2's review: the one I could have argued my way out of, and didn't

**What I didn't do:** M2's central point was that my FJ-03 runs couldn't test ranking because
`--order` collapsed the search to one candidate. I could see from the code alone (`_steps` only
reaches `search` after `reproduce`/`shuffle` establishes a reference, and step 4 already found
neither does for FJ-03) that his suggested re-run would almost certainly just reconfirm
`NOT_REPRODUCED` without exercising policy — and I was tempted to write exactly that reasoning
back to him instead of running anything. I didn't send that reply. A correct-sounding argument
from reading the code is still an argument, not the real evidence this project's own rules ask
for, and M2's whole review was itself grounded in rerunning `verify` for real rather than
reading my PR description — matching that standard back was the only honest response.

**What changed my cost estimate, and why I re-ran rather than trusted my first number:**
I initially assumed each test invocation meant a separate JVM launch and estimated hours. The
first real probe (281 invocations in 27.6 real seconds) contradicted that by 10x — one JVM
session runs many test methods, so the real cost is ~0.1s/invocation. I didn't just accept the
cheaper number and extrapolate either; I ran the *actual* full experiment (12,817 invocations,
~12.5 minutes) rather than present an extrapolation as a measured result.

**What I didn't dismiss as noise:** the full run crashed with a real JVM native-memory failure
on the first attempt, leaving crash-dump files in the repo root. Checked real free memory
(`Get-CimInstance Win32_OperatingSystem`, ~690MB of 8GB) before deciding it was a genuine
resource issue rather than a product bug, freed memory by stopping a process I no longer
needed (Docker Desktop, already done with it for W27), cleaned up the stray files, and reran —
identical real result. Separately, a `UnicodeDecodeError` appeared in `subprocess`'s reader
threads on every real fastjson run (not the small fixture) — didn't patch M2's
`order_runner.py` to silence it; flagged it as a real, pre-existing gap since the run still
completed correctly both times.

**What I didn't do when fixing the Dockerfile:** M2 said `.git` exclusion breaks commit
tracking. I didn't just remove it from `.dockerignore` and call it fixed — rebuilt the image for
real and re-ran F1 inside it to confirm `tool.commit` actually changed from `null` to a real
hash before reporting the fix as done.

**What I didn't do when regenerating the 14 dirty bundles:** could have just regenerated them
in place and accepted more `tool.dirty: true` results, since that's the existing documented
convention for a multi-bundle batch. Instead, since M2 specifically asked whether they *could*
be clean, I generated every one into a scratch location outside the repo first, so the repo was
genuinely clean at the moment each one ran, then copied all 14 in at the end — the harder but
actually-answers-the-question version of the fix.

Ownership checkpoint: be able to explain, without re-deriving it live, why a 1-candidate search
space and the package-scope `NOT_REPRODUCED` result are two *different* real findings, not one
restated — and why the second one, despite costing nothing less than the first to explain, was
worth actually running rather than predicting.

## 2026-11-22 — M2's follow-up: five things in one message, and not treating them as one task

**What I did before touching any code:** M2's message bundled a quick fix (1a), two wording
corrections (1b/1c), a large feature half (W35), a docs gap (4), and two points that explicitly
needed all three members, not just me (5a/5b). I read ADR-016 and Interface 9 in full before
writing anything, and asked the member directly for agreement on 5a/5b rather than deciding a
contract change myself and presenting it as settled — "M2 proposed it and it sounds right" is
not the same as the agreement CLAUDE.md's contract rule actually asks for.

**What I didn't let slide on the schema change:** adding `reproduced_by` as *required* breaks
every example and test that doesn't carry it — not a hypothetical, it actually broke 7 tests
the first time I ran the suite. I didn't make the field optional to dodge that (Interface 9
says it's required), and I didn't hand-patch each failure individually without understanding
why — found the real cause (dozens of existing tests build `DiagnosisRuns` directly, predating
this field entirely) and fixed it at the source: `assemble_report` infers `"order"` for a
`None` `reproduced_by` with a real reference, which is actually true for every one of those
tests, not a workaround invented to make red tests green.

**What I fixed that nothing currently uses:** `eval/outcome.py`'s `decide()` had the exact
wrong rationale text M2 described, but grepping confirmed `.rationale` has no caller in
production — only tests read it. I still fixed it. Leaving a provably false string in a public
field because nothing happens to read it yet is exactly the kind of thing that becomes a real
bug the day someone does read it, and the honesty rules don't carve out an exception for dead
code.

**What I found and didn't fix:** `runner/replay.py` never sets `reproduced_by` on the
`DiagnosisRuns` it builds. My own backward-compatibility fallback in `report.py` would paper
over this by inferring `"order"` — technically making the schema pass, while actually mislabelling
a replayed pair-mode bundle. I checked whether my fallback was hiding a real gap rather than
assuming it made everything fine, found that it was, and flagged it for M2 instead of patching
his file to "fix" a test that would otherwise look green for the wrong reason.

**What I did about the two race conditions I hit:** redoing the package-scope bundle inside a
background shell while I was still editing `eval/schema/report.schema.json` live produced a
bundle that failed its own schema validation — the subprocess's already-imported `report.py`
lacked the new field, but the schema file it re-read from disk had already changed underneath
it. I didn't just shrug and re-run it hoping it would work; I understood why the mismatch
happened (module import vs. file read, different timing) before trusting the eventual correct
result, and made sure not to run real commands concurrently with further schema edits again.

Ownership checkpoint: be able to explain, without reading this log, why `reproduced_by` needed
a backward-compatible fallback in `report.py` but the pair-mode limitation wording didn't need
one — and why a field nothing in production reads yet is still worth getting right.

## 2026-11-22 — the ui check failure was mine, not another flake

**What I didn't do:** the `ui` check failed after I pushed, and the member asked me to fix it
twice before I actually looked closely. The first time, I was mid-way through checking whether
it was the already-known infra flake (same annotation-checking workflow as every previous CI
failure this session) when the member said to leave it. The second time, I checked for real —
different step failed this time (`Backend tests`, not `setup-java`), which should have been the
signal to stop pattern-matching on the familiar flake and actually look.

**What I found by reproducing locally, not reading the GitHub annotation alone:** the GitHub
API log endpoint needed admin rights I don't have, so I ran `ui.tests.test_server` on my own
machine instead of guessing from the one-line annotation. The real error —
`'reproduced_by' is a required property` — was mine: I had updated `eval/examples/*.json` for
the new required field but missed `eval/reports/*.json`, a second, separate set of real
fixtures `ui/server.py`'s own tests read directly. Both are in `eval/`, both mine — this was
never M2's bug to chase, even though his folder's test suite is what caught it.

**What I checked before calling it fixed:** ran the full backend suite (31/31, including a real
F1 end-to-end run) and the full frontend suite CI would have reached next had the backend step
not failed first (`npm test`, `npm run typecheck`, `npm run build` — all real commands, not an
assumption that TypeScript's structural typing would tolerate an extra JSON field).

Ownership checkpoint: be able to name, without looking it up, which two directories under
`eval/` both hold report fixtures that need updating whenever the schema gains a new required
field — and why `ui/`'s test failure was the symptom, not the cause.

## 2026-11-22 — the live pair-mode comparison: reporting a surprise instead of explaining it away

**What I didn't do when the result wasn't what the protocol expected:** every prior write-up
this session predicted (correctly) that `ranked` would equal `original` on FJ-03, since M1's
own extractor finding says there is no static edge. What I did not predict, and was tempted to
quietly reframe once I saw it, was that all five `random` seeds beat both by a wide margin.
"Random beats ranking" is the kind of headline that invites a defensive explanation before the
number is even written down. I wrote the real numbers first, then worked out *why* — six
independently real polluters spread through 524 candidates, with the fixed natural order
happening to reach its first one at position 368 — and said plainly that this is a property of
this one case's shape, not a general finding, rather than either hiding the surprise or
overclaiming it as a result about random search.

**What running all seven for real caught, that reasoning from M2's one documented run would
not have:** M2's own `original` run already existed, fully documented, with the same expected
position (368). I re-ran it myself anyway rather than citing his number — it matched exactly,
which is a real independent confirmation, but running it is also what surfaced that the other
four random seeds (which I had no way to predict in advance) each landed on a *different* real
test method as the adopted polluter. That fact — six real single-polluters, not one — only
exists because I ran the pairs and read which one got adopted each time, not something
derivable from the earlier static-analysis finding alone.

**What verifying all seven bundles actually tested:** this was the first time `eval/bundle.py`'s
pair-mode `verify()` code (written this session, tested only against hand-built fixtures until
now) ran against genuine pair-mode records from a real diagnosis. All seven passed — a real
check of code that had, until this point, only proven itself against data I had constructed
myself to match my own understanding of the format.

Ownership checkpoint: be able to explain, without re-deriving it, why "six independently-valid
polluters" is itself a real finding from this session (not something the earlier offline
ranking analysis could have told us), and why it is the reason random beat both ranked and
original here specifically, not evidence about random search in general.

## 2026-11-22 -- confirming the hand-off, then a stale-status check (L2)

Asked to confirm the previous commit (`614fc6d`, the live comparison above) was run and
land correctly. Checked via the GitHub API (no `gh` CLI in this shell) rather than assuming:
PR #165 merged, M2 approved, all five CI jobs green.

While looking for the next concrete task, re-read the two registers that track FT009's open
items (`docs/10-Final1/action-register.md`, `docs/07-Defense/claims-ledger.md`'s G7 row)
against what is actually in the repo, rather than trusting their own prose. Both still claimed
my README gaps (M1's numbered gaps 3 and 4) were open; `git log` showed they were fixed hours
earlier the same day, in a commit already merged (`570a05f`, PR #164). Kept and checked by me:
the exact commit and PR for the fix, and a second staleness in the same ledger row ("only
F1/F3 bundled") against the W23 entry that shows all nine were bundled on 2026-11-21. Rejected:
nothing to reject here — this was a documentation-accuracy pass, not new engineering; the
correction is small and traceable to real commits, not an invented status.

Verified: no command run (docs-only edit); the claim rests on `git log`/`git show` output and
the GitHub API responses quoted in `docs/evidence-m3.md`'s matching entry.

Ownership checkpoint: be able to say which two files had the stale status, what the actual
fix commit was (`570a05f`), and why neither row was marked `Done` even after the correction
(M1 has not re-run her reproduction against the fixed instructions; supervisor acceptance is
separate from any of this).

## 2026-11-22 -- FT021's verifier check (L2)

Asked to do real work, not another documentation pass. Picked FT021 because it was the one
open, unblocked, M3-owned item left after re-surveying the plan and registers that required
an actual check, not a build: M2's row names M3 as the verifier, and the row was still open.

Read `runner/integrity.py` myself before trusting the claim it backs (only top-level `target/`
and `.git/` excluded -- checked the `os.walk` filter only fires `if Path(folder) == root`, so
a nested module's own `target/` is not excluded, matching the stated claim rather than a
broader one I might have assumed). Then ran the real control test myself rather than accepting
M2's evidence log: a different JDK (24.0.2 vs. his 21.0.9), different Maven (3.9.11 vs. 3.10.0)
and different Python (3.14.3) -- a genuinely independent run, not a repeat under the same
toolchain. Kept: the exact commands and real output in `docs/evidence-m3.md`. Rejected:
writing the check up as "already verified, no need to re-run" -- the whole point of being
named verifier is running it myself.

Verified: `FLAKETRACE_REQUIRE_JVM=1 py -3 -m unittest runner.tests.test_order_runner.TestResetControl -v`
-> 2/2 OK; full `runner.tests.test_order_runner` -> 51/51 OK; `git status --short` clean after
(no stray marker).

Ownership checkpoint: be able to explain why the hash-exclusion check (`os.walk`'s subfolder
filter firing only at `root`) means a nested `target/` is *not* excluded, and why that matters
for keeping the "top-level target/ and .git/" wording honest rather than overstating it.

## 2026-11-22 -- M2's review of #164/#165 addressed (L3)

Asked explicitly to do real work, not another documentation pass, in response to M2's review
message. Four concrete items plus a question. **Kept:** the member's own insistence (via the
task) on retrying the bundle regeneration for real rather than accepting a dirty tree as good
enough, which is what actually surfaced the untracked-file dirty-check quirk -- that would
never have been found by reasoning about the code alone. **Rejected:** my own first attempt at
avoiding the test JVMs' heap being constrained by setting `-Xmx` only in `MAVEN_OPTS`, not
`JAVA_TOOL_OPTIONS` -- caught before wasting a full run, by noticing `JAVA_TOOL_OPTIONS` affects
every java invocation including the ones under test, not just Maven's own build step.

**What I didn't do:** continue retrying blindly once the OOMs stopped looking transient (three
in a row with falling free memory, then PowerShell itself failing to start) -- stopped and
asked the member rather than treating "keep trying" as license to hammer an unstable machine.
Also did not touch `.github/pull_request_template.md` for M2's PR-template point -- noted as a
process reminder for my own future PRs, not a repo change.

**Real bug fixed, test-first:** `eval.bundle verify`'s zero-pairs recount bug. First test
attempt used the wrong fixture (`_victim_outcome()`'s own `matched` parameter defaults `True`,
not `False` -- caught by reading the actual recount output rather than assuming my test's
intent matched what I'd written) before it exercised the real bug path at all.

Verified: `py -3 -m unittest eval.tests.test_bundle` -> 15/15 OK; full `eval/tests` -> 159/159
OK; all 7 real FJ-03 pair-mode comparison bundles `tool.dirty: false` and `eval.bundle verify`
clean after the regeneration.

Ownership checkpoint: be able to explain why `git status --porcelain` counting an untracked
file means sequential bundle regeneration into the same folder can never all come out clean
without moving each one out between runs, and why the zero-pairs fix checks the record
header's `search_mode` rather than only the presence of "pair" lines.

## 2026-11-24 -- schema v3, versioned validation (L3)

A real contract/schema decision, not mine to make alone even though M2 deferred the choice to
me: asked the member which of M2's two options to build before writing any code, since this is
exactly the kind of call the project's own rules say needs agreement, not an AI picking for
convenience.

**Kept:** my own instinct that "just make it optional" would quietly weaken a real check going
forward -- confirmed by the member's choice, not assumed. **Rejected, before building either of
M2's two options:** my own third idea (backfill the missing field into the 16 old committed
`report.json` files, since the value is unambiguous for all of them). Caught myself on this one
specifically because it would require recomputing checksums to match edited content -- the
precise "fix the checksum after tampering" shape this project's own bundle tests exist to
reject. Not a close call once named correctly; worth recording because it looked reasonable for
a few seconds first.

Verified: the 16 previously-failing bundles confirmed failing first (`'reproduced_by' is a
required property`, matching M2's count exactly), then confirmed fixed, not assumed; full
`eval/tests` 163/163 and `ui.tests.test_server` 31/31 OK; the 16 old bundles' own files
untouched (same bytes -- did not re-hash or re-verify them against themselves, just confirmed
`git status` showed no diff on any of their files after the fix).

Ownership checkpoint: be able to explain why an *unrecognized* schema_version needs no special
error-handling branch (it falls through to the current schema and fails on that schema's own
`const` mismatch), and why bumping `eval/report.py`'s `SCHEMA_VERSION` to 3 was necessary, not
just the schema file -- a report built today must actually be checked by the stricter schema,
or the whole point of choosing v3 over "optional" is lost.
