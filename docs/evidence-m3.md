# Evidence log — Member 3 (Evaluation & Repair)

Each row: requirement addressed, file/function, test, command, result,
limitation discovered. Commands were run for real against the
`maven:3.9-eclipse-temurin-8` container; no numbers in this file are invented.

## Phase 1 — Seeded fixture project

**Requirement:** F1 static-field pollution case exists, victim passes alone,
fails after its polluter.

- File/function: `fixtures/od-fixture/src/main/java/odfixture/Config.java`;
  `ConfigPolluterTest#pollute`, `ConfigVictimTest#expectsDefaultMode`.
- Command: `mvn -B test` (full module, container working dir `/workspace`
  mounted from `fixtures/od-fixture`).
- Result: `ConfigPolluterTest` passed; `ConfigVictimTest` failed —
  `java.lang.AssertionError: expected:<0> but was:<1>` at
  `ConfigVictimTest.java:10`.
- Command: `mvn -q -Dtest=odfixture.ConfigVictimTest#expectsDefaultMode test`.
- Result: passed alone (no error output, exit 0).
- Limitation: none observed; matches `ground_truth.json` F1 exactly.

**Requirement:** F2 system-property pollution case exists, victim passes
alone, fails after its polluter.

- File/function:
  `fixtures/od-fixture/src/main/java/odfixture/FeatureFlags.java`;
  `FeaturePolluterTest#enableTurbo`, `FeatureVictimTest#expectsTurboDisabled`.
- Command: `mvn -B test` (same full-module run as above).
- Result: `FeaturePolluterTest` passed; `FeatureVictimTest` failed —
  `java.lang.AssertionError` at `FeatureVictimTest.java:10`.
- Command: `mvn -q -Dtest=odfixture.FeatureVictimTest#expectsTurboDisabled test`.
- Result: passed alone (no error output, exit 0).
- Limitation: none observed; matches `ground_truth.json` F2 exactly.

**Requirement:** F3 two-polluter edge case — victim fails only when BOTH
polluters have run, order between them should not matter.

- File/function: `fixtures/od-fixture/src/main/java/odfixture/Toggles.java`;
  `ToggleAPolluterTest#setFlagA`, `ToggleBPolluterTest#setFlagB`,
  `ToggleVictimTest#expectsNotBothFlagsSet`.
- Command: `mvn -q -Dtest=odfixture.ToggleAPolluterTest,odfixture.ToggleVictimTest test`.
- Result: passed (single polluter A insufficient, as designed).
- Command: `mvn -q -Dtest=odfixture.ToggleBPolluterTest,odfixture.ToggleVictimTest test`.
- Result: passed (single polluter B insufficient, as designed).
- Command: `mvn -q -Dtest=odfixture.ToggleAPolluterTest,odfixture.ToggleBPolluterTest,odfixture.ToggleVictimTest test`.
- Result: failed — `Tests run: 3, Failures: 1` ,
  `ToggleVictimTest.expectsNotBothFlagsSet:14`. Matches `ground_truth.json` F3
  exactly ("both required").
- Limitation discovered: Maven Surefire's `runOrder` setting
  (`<runOrder>alphabetical</runOrder>` in `pom.xml`) only supports whole-module
  orderings (alphabetical / reverse-alphabetical / random / filesystem /
  hourly / failedfirst / balanced), not an arbitrary explicit permutation that
  runs `ToggleBPolluterTest` before `ToggleAPolluterTest` while still running
  `ToggleVictimTest` last. I could not empirically force the reverse polluter
  order (B then A) through plain Maven alone. The claim that "order between A
  and B does not matter" holds by code inspection — the victim's assertion is
  the symmetric `flagA && flagB` — but empirical confirmation of the reversed
  temporal order is deferred to Member 2's order runner, which accepts an
  explicit ordered list of test methods in one JVM. Recorded here rather than
  faked.

**Requirement:** N1 negative control fails even when run alone.

- File/function:
  `fixtures/od-fixture/src/test/java/odfixture/NegativeAloneFailTest.java`,
  `alwaysFails`.
- Command: `mvn -q -Dtest=odfixture.NegativeAloneFailTest#alwaysFails test`.
- Result: failed alone — `expected:<2> but was:<1>`. Matches
  `ground_truth.json` N1.
- Limitation: none observed.

**Requirement:** N2 negative control fails intermittently regardless of
order (non-order-dependent flakiness).

- File/function:
  `fixtures/od-fixture/src/test/java/odfixture/NegativeFlakyTest.java`,
  `sometimesFails`.
- Command: `mvn -q -Dtest=odfixture.NegativeFlakyTest#sometimesFails test`,
  run 6 times in a row, alone, no polluter present.
- Result: 2 passes / 4 fails out of 6 runs (`System.nanoTime()`-driven,
  genuinely nondeterministic — real counts, not simulated).
- Limitation: 6 runs is a small sample; this only needs to demonstrate that
  the failure is NOT tied to any polluter or ordering, which it does. A larger
  sample would be needed if this fixture were later used to validate the
  random-order baseline's false-positive rate (Phase 4/5), not for Phase 1.

**Requirement:** Benign noise tests touch no shared state.

- File/function: `MathUtilTest`, `StringUtilTest`.
- Command: included in the full `mvn -B test` run above.
- Result: both passed, 0 failures, in every run observed (they do not
  reference `Config`, `FeatureFlags`, or `Toggles`).
- Limitation: none observed.

**Requirement:** `mvn -q test` builds the project inside the JDK 8 container.

- Command: `mvn -B test` inside `maven:3.9-eclipse-temurin-8`
  (image pulled and verified via `docker pull` / `docker info` before use).
- Result: compiled successfully; the reported `BUILD FAILURE` at the end is
  from the five expected test failures (see above), not a compile error —
  `mvn -q -Dtest=...` runs on the same sources passed independently.
- Limitation: none observed.

## Phase 2 — Reproduction-confidence statistics

**Requirement:** `wilson_interval(successes, n, confidence=0.95)` computes a
correct Wilson score confidence interval, dependency-free, and rejects bad
edge inputs with a clear error.

- File/function: `eval/stats.py`, `wilson_interval`, `_norm_ppf`.
- Command: `python3 -m unittest eval.tests.test_stats -v` (14 tests).
- Result: all 14 passed, including explicit edge cases: `n=0` raises
  `ValueError` ("n > 0" in the message), `successes > n` raises,
  `successes < 0` raises, `confidence` outside `(0, 1)` raises; `0/n` gives
  an exact `lower == 0.0`; `n/n` gives an exact `upper == 1.0`.
- Limitation: `_norm_ppf` (Acklam's rational approximation to the inverse
  normal CDF, used to get the z critical value for an arbitrary confidence
  level) has ~1.15e-9 *relative* error per its own published accuracy — for
  z in the 1.6-2.6 range that is up to ~3e-9 *absolute* error. My first
  unit-test tolerance (`places=9`, i.e. <0.5e-9) was tighter than the
  algorithm's real precision and failed on first run; not a bug in
  `wilson_interval` itself, just a mismatched test tolerance. Corrected to
  `places=8` after checking the actual observed differences
  (1.58e-9 to 2.90e-9 across the three published critical values tested).

**Requirement:** verify the numbers against an independent implementation,
not just my own constants.

- File/function: `eval/tools/verify_wilson_oneoff.py` (one-off script, not
  part of the test suite — requires `statsmodels`, which is intentionally
  not a project dependency).
- Command: created a throwaway venv (`/tmp/ft_verify_venv`), `pip install
  statsmodels` (0.15.0), then ran the script comparing
  `wilson_interval(...)` against
  `statsmodels.stats.proportion.proportion_confint(..., method="wilson")`
  for 11 (successes, n, confidence) combinations including both 0/n and n/n
  edges and three confidence levels (0.90, 0.95, 0.99).
- Result: maximum absolute difference across all 11 cases was
  **2.643e-10** — agreement to about 9-10 decimal places. Full per-case
  output recorded below. The venv was deleted after the check; it is not
  committed and is not needed again unless the Wilson formula changes.
- Limitation: none — this was the strongest evidence available
  (statsmodels is a widely-used, independently-maintained statistics
  library) short of a hand-derived closed-form check, which the unit tests
  also do separately (exact 0/n and n/n bounds).

```
successes=17 n=20 confidence=0.95  mine=(0.6395811350648312, 0.9476312541456368)  statsmodels=(0.6395811352592431, 0.9476312541037835)  max_abs_diff=1.944e-10
successes= 0 n=20 confidence=0.95  mine=(0.0, 0.16112515827076002)  statsmodels=(0.0, 0.16112515805281938)  max_abs_diff=2.179e-10
successes=20 n=20 confidence=0.95  mine=(0.83887484172924, 1.0)  statsmodels=(0.8388748419471806, 1.0)  max_abs_diff=2.179e-10
successes=10 n=20 confidence=0.95  mine=(0.2992980080624758, 0.7007019919375241)  statsmodels=(0.2992980081982123, 0.7007019918017877)  max_abs_diff=1.357e-10
successes= 1 n=20 confidence=0.95  mine=(0.008881448790731947, 0.23613119365295204)  statsmodels=(0.008881448800795402, 0.23613119344674205)  max_abs_diff=2.062e-10
successes=19 n=20 confidence=0.95  mine=(0.7638688063470479, 0.9911185512092681)  statsmodels=(0.763868806553258, 0.9911185511992047)  max_abs_diff=2.062e-10
successes=10 n=20 confidence=0.9   mine=(0.32740376805316856, 0.6725962319468314)  statsmodels=(0.3274037678851559, 0.6725962321148441)  max_abs_diff=1.680e-10
successes=10 n=20 confidence=0.99  mine=(0.250447700111171, 0.749552299888829)  statsmodels=(0.25044770032177954, 0.7495522996782205)  max_abs_diff=2.106e-10
successes= 0 n= 1 confidence=0.95  mine=(0.0, 0.7934506858870164)  statsmodels=(0.0, 0.7934506856227626)  max_abs_diff=2.643e-10
successes= 1 n= 1 confidence=0.95  mine=(0.20654931411298352, 1.0)  statsmodels=(0.20654931437723745, 1.0)  max_abs_diff=2.643e-10
successes= 3 n=20 confidence=0.95  mine=(0.052368745854363144, 0.36041886493516884)  statsmodels=(0.052368745896216595, 0.36041886474075696)  max_abs_diff=1.944e-10

Overall max absolute difference across 11 cases: 2.643e-10
```

**Requirement:** a function that compares a sequence result against an
isolation result and returns a structured record.

- File/function: `eval/stats.py`, `compare_sequence_to_isolation`,
  `ReproductionComparison`.
- Command: `python3 -m unittest eval.tests.test_stats -v`
  (`TestCompareSequenceToIsolation`, 3 tests).
- Result: all passed — confirms the `summary` text reads exactly
  `"sequence reproduced 17/20, victim alone 0/20"` for that input, both
  sides carry their own Wilson interval, and `isolation_n=0` /
  `sequence_n=0` each raise a clear `ValueError` (delegated straight from
  `wilson_interval`).
- Limitation: this function only produces the structured comparison; it
  does not decide VERIFIED/CANDIDATE/UNRESOLVED — that decision table is
  Phase 3, and several of its thresholds are explicitly open questions for
  me to confirm before it is finalized.

## Phase 3 — Evidence-report schema and outcome logic

**Requirement:** JSON Schema for the diagnosis report with the specified
fields, and a validator.

- File/function: `eval/schema/report.schema.json`, `eval/schema_validator.py`
  (`validate_report`, `validate_report_file`), using the `jsonschema` package
  (pinned in `eval/requirements.txt`).
- Command: `python3 -m unittest eval.tests.test_schema_validator -v`.
- Result: 8/8 passed, including that the schema document itself is a valid
  JSON Schema (`Draft202012Validator.check_schema`), a valid report passes,
  a missing required field fails, an unknown `outcome` value fails, and the
  `outcome`/`unresolved_reason` conditional is enforced both directions
  (UNRESOLVED without a reason fails; VERIFIED with a reason fails).
- Bug found and fixed during testing: the first draft of the
  `shared_resource` field used `"type": ["object", "null"]` with a sibling
  `"oneOf"` of two object sub-schemas. For a `null` instance, neither
  sub-schema's `properties`/`required` keywords apply (they're no-ops on
  `null`), so **both** branches matched vacuously and `oneOf` correctly
  rejected it for matching more than once. Fixed by restructuring to
  `oneOf: [{"type":"null"}, {"type":"object", "oneOf": [...]}]`, confirmed
  by re-running the two example files that have `shared_resource: null`
  (`example_victim_fails_alone.json`, `example_no_resource_evidence.json`).
- Limitation: `jsonschema` is a new dependency (confirmed with Member 3
  before adding it) — recorded in `eval/requirements.txt`, not yet wired
  into any CI/build step since none exists yet in this repo.

**Requirement:** outcome enum, unresolved-reason enum, and the decision
table — drafted as a starting point, confirmed with Member 3 before
finalizing (per the brief).

- File/function: `eval/outcome.py` (`decide`, `DecisionInput`, `Decision`).
- Four open questions from the brief were put to Member 3 directly before
  any decision code was written (see `docs/contracts/report-schema.md` for
  the resolutions): CANDIDATE vs. `BELOW_CONFIDENCE_THRESHOLD` → CANDIDATE;
  signature-gated success counting → yes; fixed `n=20` vs. generic Wilson
  threshold → generic; source-integrity override → yes, added as a new
  `SOURCE_INTEGRITY_FAILED` reason.
- Command: `python3 -m unittest eval.tests.test_outcome -v` (12 tests: one
  per decision-table row, plus `DecisionInput` validation edge cases).
- Result: 12/12 passed — each of the 7 decision-table rows (source
  integrity failed; victim fails alone; not reproduced; signature mismatch;
  no resource evidence; verified; candidate) produces exactly the outcome
  and reason the table specifies, confirmed with real calls into
  `eval.stats.wilson_interval` (not mocked).
- Limitation: `BELOW_CONFIDENCE_THRESHOLD` stays in the schema's enum (the
  brief requires the five reasons "at least") but `decide()` never emits
  it — documented in both the schema's field description and
  `docs/contracts/report-schema.md` so this isn't mistaken for an omission
  later.

**Requirement:** example JSON files under `examples/`, labelled as
hand-written, not results.

- File/function: `eval/examples/*.json` (7 files, one per decision-table
  row), `eval/examples/README.md`, `eval/tests/test_examples.py`.
- Command: `python3 -m unittest eval.tests.test_examples -v`.
- Result: 4/4 passed — every example file validates against the schema,
  every example's hand-picked counts reproduce the *same* outcome and
  reason when run through `eval.outcome.decide()` (not just asserted by
  hand), and every example's `lower`/`upper` Wilson numbers match the
  formula to 9 decimal places (computed, not typed from guesswork — see
  Phase 2 evidence for the verification of the formula itself).
- Limitation found and documented in the example itself: the schema's
  singular `polluter_write_location` field cannot represent
  `example_f3_candidate.json`'s two required writes (`flagA` and `flagB`
  both set by separate tests); only one is shown, with a note in that
  file's `limitations` array and in `report-schema.md`.

**Requirement:** `docs/contracts/report-schema.md` explaining each field
and which member produces it.

- File/function: `docs/contracts/report-schema.md`.
- Result: field-by-field table with producing member, outcome/reason enum
  tables, the finalized decision table, and an explicit record of the four
  decisions confirmed with Member 3 on 2026-10-08.
- Limitation: none — this is documentation, not executable, so "verification"
  here is that it accurately describes what `eval/outcome.py` and
  `eval/schema/report.schema.json` actually do (checked by re-reading both
  against the table after writing it).

**Correction to Phase 1 ground truth, made in Phase 3 (not based on any run
output):** `fixtures/od-fixture/ground_truth.json`'s N2 case was originally
guessed as `UNRESOLVED(NOT_REPRODUCED)`, flagged at the time as "to be
confirmed against the Phase 3 decision table." Under the finalized table,
any isolation run that reproduces the reference signature at all — even
intermittently — trips `VICTIM_FAILS_ALONE` before reproduction counting is
ever consulted. Phase 1's own evidence (N2 run alone 6 times: 2 pass / 4
fail, same signature each failure) confirms N2 belongs in that category, not
`NOT_REPRODUCED`. Updated the ground truth entry and its notes accordingly;
N1 was already correctly `VICTIM_FAILS_ALONE` and is unchanged.
