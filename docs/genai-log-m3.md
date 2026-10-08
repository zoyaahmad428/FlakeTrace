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
