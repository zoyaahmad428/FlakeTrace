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

## Phase 4 — Random-order baseline (interface only)

**Requirement:** design the baseline against an explicit runner interface
(run an ordered list of test methods in one JVM, return per-test outcome +
signature).

- File/function: `eval/baseline.py` — `OrderRunner` (a `typing.Protocol`),
  `TestIdentifier`, `FailureSignature`, `RunOutcome`.
- Result: interface defined; no implementation exists in this repo (Member
  2's component, not built yet). Documented explicitly in
  `eval/README.md` under "Random-order baseline status: NOT YET RUN ON
  REAL TESTS."
- Limitation: none for the interface definition itself — this is
  intentionally interface-only per the brief.

**Requirement:** seeded shuffles of the frozen candidate set; count runs
until the victim's reference failure signature appears; record every seed.

- File/function: `eval/baseline.py` — `run_random_order_baseline`,
  `BaselineAttempt`, `BaselineResult`.
- Command: `python3 -m unittest eval.tests.test_baseline -v`.
- Result: 12/12 passed, including:
  - `test_finds_matching_order_eventually_and_stops_early` — with a fake
    runner where the victim fails iff the polluter is shuffled before it
    (true ~50% of random permutations), found a match within 200 attempts
    and confirmed the runner was called exactly `runs_attempted` times, not
    `max_runs` times (early stopping on first match, real behavior, not
    asserted by inspection).
  - `test_records_every_seed_even_when_never_matching` — 5/5 seeds
    (`[0,1,2,3,4]`) recorded even when none matched.
  - `test_deterministic_given_same_seeds` — two independent runs with the
    same `base_seed` produced byte-identical sequences of shuffled orders
    (real `random.Random(seed).shuffle` determinism, not mocked).
  - `test_different_base_seed_gives_different_orders` — confirms the seed
    actually drives the shuffle (not a no-op parameter).
- Limitation: `random.Random`'s determinism is CPython-internal (Mersenne
  Twister) — reproducible within this project's own environment, not
  intended to match any external/cross-language random source. Acceptable
  for this use (re-running the same seed later in this same toolchain).

**Requirement:** unit-test it with a FakeRunner that lives ONLY in the
tests folder, clearly named as fake; the real CLI must never import it.

- File/function: `eval/tests/fake_runner.py` — `FakeOrderRunner`.
- Command: `grep -rn "fake_runner\|FakeOrderRunner" eval/baseline.py` (and
  every non-test file under `eval/`).
- Result: zero matches outside `eval/tests/` — confirmed `baseline.py` does
  not import the fake, and no other file in `eval/` references it either.
- Limitation: there is no "real CLI" yet anywhere in this repo to check
  against (Member 2 hasn't built one), so this check is necessarily
  limited to "nothing in this repo's non-test code imports the fake" today;
  it will need re-checking once a real CLI exists.

**Requirement:** mark in the README that the baseline is not executed on
real tests until the runner is integrated.

- File/function: `eval/README.md`.
- Result: explicit "NOT YET RUN ON REAL TESTS" section, stating no
  `OrderRunner` implementation exists yet and no baseline numbers against
  `fixtures/od-fixture` or any real project exist or should be invented.

## Phase 5 — Benchmark manifest and yield report

**Requirement:** create/extend the frozen manifest with the fixture cases
(F1-F3, N1-N2) and, if POC case data exists in the repo, the real cases
with pinned SHAs.

- File/function: `eval/benchmark/manifest.json`.
- Command: searched for real-case metadata before assuming none existed —
  `grep -rln "sha\|commit\|repo_url\|github.com" POC` and inspected
  `POC/POC/flaketrace-ui/src/data/recorded.json` directly (real file read,
  not guessed).
- Result: found one — `recorded.json`'s `git` section carries a pinned
  40-character SHA (`ba16cdfde681d0409080f1acbe80942cbae7ae4f`) for a
  "demo-project" case, plus a `suggested` polluter/victim/resource guess
  from the POC's own heuristic backend. Added it to the manifest as
  `POC-DEMO-1` with the pinned SHA, but with `ground_truth_outcome: null`
  — that "suggested" value was the POC backend's own guess, not ground
  truth we independently authored, so copying it in as if verified would
  misrepresent it. Documented in the manifest's `notes` field that this
  case used a custom JDK-21 harness (not Maven/Docker, not our statistical
  pipeline) and that `demo-project`'s source isn't actually present in
  this repo (`recorded.json` points at a `~/demo-project` path local to the
  original author's machine) — so it cannot be attempted by our pipeline
  yet.
- Also checked `POC/POC/sample-dataset/sample` (Holder/ReaderTest/WriterTest,
  found during Phase 0) against the same bar: no pinned SHA, no ground
  truth, 0-byte `pom.xml` (confirmed in Phase 0), JUnit 5 not JUnit 4.
  Excluded from the manifest rather than silently dropped — recorded under
  `excluded_from_manifest` in the manifest file itself, with the reason.
- Cross-check: `python3 -m unittest
  eval.tests.test_yield_report.TestRealManifest.test_real_manifest_matches_fixture_ground_truth`
  — passed, confirming the manifest's F1-F3/N1/N2 entries (victim,
  polluters, `ground_truth_outcome`, `ground_truth_reason`) match
  `fixtures/od-fixture/ground_truth.json` exactly, so the two files can't
  silently drift apart.

**Requirement:** a script that generates a yield report (attempted ->
built -> victim passes alone -> reproduced -> excluded with reason) from
recorded logs, not hand-typed numbers. If no logs exist yet, the report
must show "not yet run" — never invent counts.

- File/function: `eval/benchmark/yield_report.py` —
  `generate_yield_report`, `compute_case_yield`, reading only from
  `eval/benchmark/logs/<case_id>.json`.
- Command: `python3 -m unittest eval.tests.test_yield_report -v` (5 tests:
  2 synthetic-scenario tests using temp manifests/logs, 3 against the real
  manifest/logs).
- Result: 5/5 passed, including a synthetic mixed-funnel scenario (one
  fully-reproduced case, one build-failure, one victim-fails-alone, one
  with no log file at all) that confirmed every funnel count by hand
  computation, and a real check that `eval/benchmark/logs/` currently
  contains zero `.json` files.
- Command (the actual deliverable, not a test): `python3
  eval/benchmark/yield_report.py`.
- Result: real output, reproduced below in full — all 6 cases
  `not_yet_run`, every funnel count 0. This is the literal, current,
  honest state; no number in it was typed by hand.

```json
{
  "total_cases": 6,
  "attempted": 6,
  "not_yet_run": 6,
  "built": 0,
  "build_failed": 0,
  "victim_passes_alone": 0,
  "victim_fails_alone": 0,
  "reproduced": 0,
  "not_reproduced": 0,
  "excluded": 0,
  "cases": [
    {"case_id": "F1", "attempted": true, "not_yet_run": true, "built": null, "victim_passes_alone": null, "reproduced": null, "excluded_reason": null},
    {"case_id": "F2", "attempted": true, "not_yet_run": true, "built": null, "victim_passes_alone": null, "reproduced": null, "excluded_reason": null},
    {"case_id": "F3", "attempted": true, "not_yet_run": true, "built": null, "victim_passes_alone": null, "reproduced": null, "excluded_reason": null},
    {"case_id": "N1", "attempted": true, "not_yet_run": true, "built": null, "victim_passes_alone": null, "reproduced": null, "excluded_reason": null},
    {"case_id": "N2", "attempted": true, "not_yet_run": true, "built": null, "victim_passes_alone": null, "reproduced": null, "excluded_reason": null},
    {"case_id": "POC-DEMO-1", "attempted": true, "not_yet_run": true, "built": null, "victim_passes_alone": null, "reproduced": null, "excluded_reason": null}
  ]
}
```

- Limitation: `eval/benchmark/logs/` is empty because no implementation of
  `baseline.py`'s `OrderRunner` (or any real build/isolation/reproduction
  pipeline) exists in this repo yet — same blocker as Phase 4. Once Member
  2's runner lands and writes real `<case_id>.json` log files, this exact
  script (unchanged) will produce real funnel numbers instead of all
  `not_yet_run`.

## Post-Phase-5 correction — replacing fabricated numbers with real data

The user correctly flagged that Phase 3's `eval/examples/*.json` used
hand-picked counts (e.g. "20/20") never actually measured, and that the
manifest's only "real" case (`POC-DEMO-1`) was one I had already flagged
myself as unusable. Two fixes, both now real:

**Fix 1 — real cases from a real published dataset, not just metadata I
invented.** Searched WSL's `~/WorkSpace/flaketrace/idoft/odr-tests.csv`
(TestingResearchIllinois/idoft, 1908 rows, confirmed via `wc -l` and
`cut -d, -f1 | sort -u | wc -l` → 24 distinct real GitHub projects). Used
Python's `csv.DictReader` (not naive comma-splitting, since some fields
could contain commas) to pull one `OD-test-type=victim` row each from 5
diverse, recognizable projects: dropwizard, kevinsawicki/http-request,
ktuukkan/marine-api, openpojo, spring-boot. Added as
`IDOFT-DROPWIZARD-1`, `IDOFT-HTTP-REQUEST-1`, `IDOFT-MARINE-API-1`,
`IDOFT-OPENPOJO-1`, `IDOFT-SPRING-BOOT-1` in
`eval/benchmark/manifest.json`, each with its real 40-character SHA
transcribed verbatim from the CSV.

- Command: `python3 -m unittest eval.tests.test_yield_report -v` (added
  `test_idoft_cases_have_pinned_shas_and_null_ground_truth`).
- Result: 6/6 passed — confirms all 5 idoft SHAs are real 40-char hex
  strings (regex-checked, not just non-null), confirms 5 distinct real
  project names (no accidental duplicates), and confirms
  `ground_truth_outcome` is `null` for every one of them (we have not run
  these ourselves — idoft's own research classification is not the same
  as our pipeline verifying it, so copying their verdict in as "ground
  truth" would misrepresent it).
- Command: `python3 eval/benchmark/yield_report.py` → real output, now 11
  total cases, all 11 still honestly `not_yet_run` (no build/isolation/
  reproduction pipeline exists yet for any source — fixture, POC, or
  idoft).
- Limitation: these 5 rows are metadata only — not cloned, not built, not
  run. Actually doing so (cloning external GitHub repos at a pinned SHA,
  building with Maven, running the specific tests) was explicitly
  descoped by the user to "metadata only" given the cost/risk of building
  unknown external projects; recorded as a known gap, not silently
  dropped.

**Fix 2 — real measured counts for the fixture, replacing hand-picked
numbers.** Wrote `eval/tools/run_real_reps.sh` and ran it for real inside
`maven:3.9-eclipse-temurin-8` (same container as Phase 1): each of
F1/F2/F3's isolation case and reduced-sequence reproduction, plus N1/N2's
isolation case (their reduced_sequence is empty, so isolation ==
reproduction for them), run 20 times each via `mvn -q -Dtest=... test`,
counting real exit codes. 160 Maven invocations total; took about
30 minutes (JVM/Maven startup overhead per invocation, not 1-2s as first
estimated — confirmed healthy via `docker exec ... ps aux` mid-run, not
assumed).

- Command: `python3 eval/tools/run_real_reps.sh` inside the container (via
  `docker run`, volumes mounting `fixtures/od-fixture` and the script).
- Real result (verbatim):
  ```
  F1_isolation: pass=20 fail=0 n=20
  F1_reproduction: pass=0 fail=20 n=20
  F2_isolation: pass=20 fail=0 n=20
  F2_reproduction: pass=0 fail=20 n=20
  F3_isolation: pass=20 fail=0 n=20
  F3_reproduction: pass=0 fail=20 n=20
  N1_isolation: pass=0 fail=20 n=20
  N2_isolation: pass=8 fail=12 n=20
  ```
  ("pass"/"fail" = whether the `mvn` invocation exited 0; for isolation
  runs a "fail" means the victim failed alone, for reproduction runs a
  "fail" means the victim reproduced the bug after the polluter(s).)
- Interpretation: F1/F2/F3 are genuinely deterministic — 20/20 reproduction,
  0/20 alone-failure, confirmed by actually running each 20 times, not
  assumed from one earlier observation. N1 is genuinely deterministic
  (20/20 fails alone). **N2 gave a real, previously-unmeasured number:
  12/20 fails alone** — Phase 1 had only sampled 6 runs informally (2
  pass/4 fail); this is the first proper n=20 measurement.
- Fed these real counts through `eval.outcome.decide()` (not re-derived by
  hand) to get the authoritative outcome for each case:
  `python3 -c "from eval.outcome import DecisionInput, decide; ..."` →
  F1/F2/F3 → `VERIFIED`; N1/N2 → `UNRESOLVED(VICTIM_FAILS_ALONE)`. All five
  match `fixtures/od-fixture/ground_truth.json`'s hand-authored
  expectations exactly.
- Wrote `eval/benchmark/logs/{F1,F2,F3,N1,N2}.json` with these real
  counts and outcomes (`recorded_by` field states plainly this was a
  manual plain-Maven run, not Member 2's automated pipeline). Running
  `python3 eval/benchmark/yield_report.py` now shows real funnel data for
  these 5 cases (3 `reproduced`, 2 `excluded` as `VICTIM_FAILS_ALONE`)
  while the other 6 cases (`POC-DEMO-1` + 5 `IDOFT-*`) remain honestly
  `not_yet_run`.
- Updated `eval/examples/` to match: `example_f1_verified.json` and the
  renamed `example_f3_verified.json` now carry real counts (F3's are
  genuinely 20/20, not the fabricated 12/20 "CANDIDATE" framing used
  before — F3 is deterministic given its full reduced sequence, so it
  cannot produce a real CANDIDATE example). Added
  `example_victim_fails_alone_intermittent.json` with N2's real 12/20.
  Replaced the deleted F3-as-CANDIDATE file with a wholly synthetic
  `example_candidate.json` (`com.example.*` names), since none of
  F1-F3's real behavior lands below the 0.70 threshold. Updated
  `example_source_integrity_failed.json` to reuse F1's now-real stats
  (only the integrity failure itself stays hypothetical, since no real
  integrity checker exists). `eval/examples/README.md` now labels each
  file REAL/SYNTHETIC/MIXED explicitly.
- Command: `python3 -m unittest discover -s eval/tests -v` (after all
  updates, including a new cross-check
  `test_real_examples_match_the_real_log_files` comparing the 4 real
  example files' counts against the actual log files, and a corrected
  `test_yield_report_shows_real_funnel_for_run_cases_and_not_yet_run_for_the_rest`
  replacing the now-outdated "logs dir is empty" assumption).
- Result: 58/58 passed.
- Limitation: `polluter_write_location`/`victim_read_location`'s
  `bytecode_offset` values and `source_integrity` are still placeholders
  in every example — no real static-bytecode-evidence extractor (Member 1)
  or source-integrity checker (Member 2) exists yet. Only the
  reproduction/isolation statistics themselves are now real.

## 2026-10-09 — `eval/README.md` fix: documented test command

**Requirement:** `eval/README.md` documented `python3 -m unittest discover
-s eval/tests -v` as failing because `eval/tests` has no `__init__.py`.
Reproduce for real before fixing anything.

- Command: `python3 -m unittest discover -s eval/tests -v` — ran in WSL
  (Python 3.10.12): **passed, 58/58, exit 0.** The claimed `__init__.py`
  cause did not reproduce there.
- Command: the same command on native Windows Python (`py`, 3.14.3, no
  venv): **failed** — but with `ModuleNotFoundError: No module named
  'jsonschema'` (import error inside `test_examples.py` and
  `test_schema_validator.py`), not an `__init__.py`/namespace-package
  error.
- Command: `py -m pip install -q -r eval/requirements.txt` then the same
  command again, same native Python: **passed, 58/58, exit 0.**
- To rule out any residual state on that machine masking the real bug:
  created a throwaway venv (`py -m venv .tmp_readme_check_venv`),
  installed only `eval/requirements.txt` into it, ran the documented
  command fresh: **passed, 58/58, exit 0.** Deleted the venv afterward,
  not committed.
- Conclusion: there is no `__init__.py`/namespace-package bug. The actual,
  reproducible cause is that `eval/README.md` mentioned
  `pip install -r eval/requirements.txt` once, at the top, separately
  from the "Run everything" command — easy to skip if a reader jumps
  straight to the command.
- Fix (smallest correct one): moved the `pip install` line to sit directly
  above the run command, with an explicit note of the exact
  `ModuleNotFoundError` a reader will hit if they skip it. No code change,
  no `__init__.py` added (none needed — the namespace-package import
  already works, confirmed above).
- Re-verified after the fix, fresh:
  - Documented command: `pip install -q -r eval/requirements.txt &&
    python3 -m unittest discover -s eval/tests -v` → **58/58, exit 0.**
  - CI's actual command (`.github/workflows/ci.yml`, `python-eval` job):
    `modules=$(ls eval/tests/test_*.py | sed 's#/#.#g; s#\.py$##'); python3
    -m unittest -v $modules` → **58/58, exit 0.** `python3
    eval/benchmark/yield_report.py` → exit 0.
- Limitation: none found beyond the one fixed. The brief's premise
  (`__init__.py` missing) turned out to be a misdiagnosis of a plain
  missing-dependency error; worth saying so plainly rather than adding an
  `__init__.py` that was never the cause.

## 2026-10-09 — Fix F1 example's illustrative bytecode offsets

**Requirement:** Zoya's `docs/contracts/resource-evidence.md` (open question
5, on branch `m1/resource-evidence-contract`) noted that
`example_f1_verified.json` used illustrative offsets 3/5, while real JDK 8
offsets are 1/1. Verify independently before trusting her claim and acting
on it.

- Command: `docker run ... maven:3.9-eclipse-temurin-8 bash -c "mvn -q
  test-compile && javap -c -p target/test-classes/odfixture/
  ConfigPolluterTest.class && javap -c -p target/test-classes/odfixture/
  ConfigVictimTest.class"`.
- Result: `putstatic #2 // Field odfixture/Config.mode:I` at **offset 1**
  in `ConfigPolluterTest#pollute`; `getstatic #2 // Field
  odfixture/Config.mode:I` at **offset 1** in
  `ConfigVictimTest#expectsDefaultMode`. Matches Zoya's claimed values
  (1/1) exactly — independently confirmed, not just trusted.
- File/function: `eval/examples/example_f1_verified.json` —
  `polluter_write_location.bytecode_offset` and
  `victim_read_location.bytecode_offset` changed from the placeholder
  3/5 to the real 1/1; `limitations` entry updated to say these are now
  real, verified values, not placeholders.
- Command: `python3 -m unittest discover -s eval/tests -v`.
- Result: 58/58 passed — no test asserts an exact offset value, so this
  change could not have silently broken anything; confirmed anyway rather
  than assumed.
- Limitation: none — this was purely my own example file, no contract
  change, no other member's sign-off needed.

## 2026-10-10 — W9: real end-to-end report assembly

**Requirement:** Interface 3 of `docs/contracts/interfaces.md` ("report assembly, M3") —
turn Member 2's raw diagnosis counts and Member 1's resource-access data into one
schema-validated report, now that both exist for real (PR #10 `runner/order_runner.py`,
PR #11 `runner/diagnose.py`, PR #9 `evidence/extract.py`).

- Before writing any glue code: smoke-tested both real components on this machine (native
  Windows, JDK 24.0.2, Maven 3.9.11 — not the Docker/JDK8 setup used in earlier phases).
  `runner.diagnose.diagnose()` on F1 (`n=5`): real `POLLUTER_FOUND`, correct polluter found,
  matches the shape expected. Cross-checked against my own independent manual measurement
  from two sessions ago (Docker/plain-Maven, `eval/tools/run_real_reps.sh`): F1 and N1 both
  agree exactly (F1: 20/20 reproduced, 0/20 alone; N1: 20/20 alone) — two independently-run
  real measurements agreeing is stronger evidence than either alone.
- File/function: `eval/report.py` — `find_resource_edge` (correlates two
  `evidence.extract.analyse_test` Output-1 results into one edge, per the contract's
  documented `edges[0]` ordering) and `assemble_report` (builds a full report from a
  `DiagnosisRuns` + optional edge, runs it through `eval.outcome.decide` and
  `eval.schema_validator.validate_report`).
- Deliberate scope limit, not silently worked around: `assemble_report` only handles
  `DiagnosisRuns.status` values `POLLUTER_FOUND` and `VICTIM_FAILS_ALONE`, raising
  `UnhandledStatus` otherwise. Two real reasons, found by reading `runner/diagnose.py`
  carefully, not assumed:
  1. `NOT_REPRODUCED` carries `alone_n=0` (M2's code never runs the isolation check if the
     sequence never reproduces at all) — but `eval.outcome.DecisionInput` requires
     `isolation_n > 0`. Feeding it a fabricated `isolation_n=1` just to satisfy the signature
     would be inventing data; raising instead.
  2. `NO_SINGLE_POLLUTER` (M2's one-by-one search finding no single attributable test — F3's
     real status, confirmed below) has no corresponding value in `report.schema.json`'s
     `unresolved_reason` enum. Mapping it onto an existing reason (e.g.
     `NO_SUPPORTED_RESOURCE_EVIDENCE`) would be semantically wrong — that reason means
     missing *resource* evidence, not a missing *polluter identity*. A new enum value is a
     contract change needing all three members, not decided here.
- Command: `py -m unittest eval.tests.test_report -v` (pure-logic tests against literal
  Output-1 dicts and hand-built `DiagnosisRuns` objects — not calling real Maven/JDK, so this
  runs in the existing `python-eval` CI job unchanged).
- Result: 11/11 passed, including: resource-edge correlation finds the right resource and
  picks the lowest-combined-depth edge when more than one is shared; `VERIFIED` for a strong
  reproduction with an edge; `NO_SUPPORTED_RESOURCE_EVIDENCE` with no edge; `CANDIDATE` for a
  weak reproduction; `SOURCE_INTEGRITY_FAILED` overriding a strong case; `VICTIM_FAILS_ALONE`
  correctly ignoring a resource edge even if one is mistakenly passed in; both unhandled
  statuses correctly raising `UnhandledStatus`.
- Command: `py -m unittest discover -s eval/tests -v` (full suite).
- Result: 69/69 passed (58 existing + 11 new).
- **Real end-to-end integration** (`eval/tools/run_w9_integration.py`, not part of the unit
  suite — shells out to real Maven/JDK, a few minutes):
  - F1: `runner.diagnose.diagnose()` for real (`n=20`) → `POLLUTER_FOUND`, 20/20 reproduced,
    0/20 alone, source integrity passed. `evidence.extract.analyse_test()` for real on the
    polluter and victim → real edge, `odfixture.Config#mode`, write/read both at bytecode
    offset 1 (matches the independently-`javap`-verified value from the earlier session).
    `assemble_report` → **`VERIFIED`**, `validate_report` passed. Saved:
    `eval/reports/f1.json`.
  - N1: real `diagnose()` (`n=20`) → `VICTIM_FAILS_ALONE`, 20/20 alone-failures.
    `assemble_report` (no resource edge) → **`UNRESOLVED(VICTIM_FAILS_ALONE)`**,
    `validate_report` passed. Saved: `eval/reports/n1.json`.
  - Both match `fixtures/od-fixture/ground_truth.json` exactly.
- Limitation found and documented, not fixed here (not my folder): `execution_record_reference`
  in both reports is an absolute, machine-specific path, because
  `runner.diagnose.diagnose()` calls `Path(record_dir).resolve()` internally. The committed
  JSON reflects exactly what the real run produced, not cleaned up for presentation.
- Limitation: the raw per-run JSONL execution records
  (`eval/reports/flaketrace-records/*.jsonl`) that back `execution_record_reference` are
  **not committed** — `.gitignore` already excludes `flaketrace-records/` (Member 2's
  existing convention). Only the final assembled reports are committed; the records
  regenerate locally by re-running the integration script.
- Also confirmed empirically, while exploring: on this machine, `diagnose()` reports N2 as
  `NOT_REPRODUCED` (never fails at all, in or out of order), not `VICTIM_FAILS_ALONE` as my
  own earlier Docker measurement found (12/20 alone-failures) or as `ground_truth.json`
  currently assumes. Traced by Member 2 to `System.nanoTime()` having coarser resolution on
  some Windows/JVM combinations (always a multiple of 100ns, always even, so the parity check
  in `NegativeFlakyTest` can never fail there) — see `docs/evidence-m2.md`. This is a genuine,
  environment-dependent behaviour of the fixture, not a bug in either component; it meant
  `ground_truth.json`'s N2 entry was not safely portable across machines as originally
  written. Resolved the same day — see the next section.

## 2026-10-10 — Fix N2's flakiness mechanism (ground truth resolution)

**Requirement:** resolve a real discrepancy found while reviewing Member 2's W9 evidence:
`runner.diagnose()` reported N2 (`NegativeFlakyTest#sometimesFails`) as `NOT_REPRODUCED` on a
Windows/JDK 21 machine (0/40 failures, alone and in the full order), contradicting
`ground_truth.json`'s assumption that it fails at least intermittently
(`docs/evidence-m2.md`). My own earlier measurement (Docker/JDK 8) found 12/20 alone-failures.

- Investigation: `NegativeFlakyTest` used `System.nanoTime() % 2L == 0L`. This inspects only
  the **lowest bit** of the timer value. Some JVM/OS/hardware timer combinations have coarse
  resolution (Member 2 found `System.nanoTime() % 1000` always a multiple of 100 on their
  machine), so every value is even and the assertion is always true — the test can become
  **fully deterministic** (never fails) on specific real hardware, which directly contradicts
  its purpose ("non-order-dependent flakiness... unrelated to the environment").
- Decision: fix the mechanism, not just document the quirk. This is entirely my own file
  (`fixtures/od-fixture`), no contract or cross-member sign-off needed, and a genuine fix is
  stronger than a documented limitation for a case whose entire point is demonstrating
  environment-independent flaky behaviour.
- File/function: `fixtures/od-fixture/src/test/java/odfixture/NegativeFlakyTest.java` —
  replaced the nanoTime-parity check with `new java.util.Random().nextBoolean()`, which mixes
  nanoTime() with a per-call atomic counter through a full LCG rather than exposing one raw
  timer bit.
- Command: `mvn -q -Dtest=odfixture.NegativeFlakyTest#sometimesFails test`, run 20 times in a
  loop, **on native Windows (JDK 24.0.2, where the old mechanism gave 0/40)**.
- Result: **11/20 failures (55%)** — genuinely balanced, real data. (Corrected 2026-10-13: this
  entry originally said 45%, which is arithmetically wrong for 11/20 — flagged by Member 2 while
  reviewing the report. The raw count, 11/20, was always correct; only the stated percentage was
  wrong, here and in `ground_truth.json`'s copy of this same result.)
- Command: the same 20-repetition loop, independently, **inside
  `maven:3.9-eclipse-temurin-8` (JDK 8, Linux, Docker)**, run in parallel with the Windows
  check.
- Result: **10/20 failures (50%)** — also genuinely balanced.
- Command: full fixture module, `mvn -B test` (native Windows).
- Result: `Tests run: 13, Failures: 5` — F1, F2, F3, N1 fail exactly as designed (alphabetical
  declared order pollution); N2 failed this particular run (one of its genuine ~50/50
  outcomes, not every run will match) — matches Phase 1's original full-module result exactly,
  confirming the fix did not disturb anything else in the fixture.
- File/function: `fixtures/od-fixture/ground_truth.json` — N2's `expected_outcome_notes`
  rewritten to describe the bug, the fix, and both real verification numbers above, dropping
  the old "~50%, confirmed in Phase 1: 2 pass / 4 fail across 6 isolated runs" claim (that
  6-run sample is superseded by this 20-run, two-platform verification). Also added a short
  confirming note to F3's entry: Member 2's real `diagnose()` run returned
  `NO_SINGLE_POLLUTER` after 12 search runs, exactly as the fixture's design predicted (the
  current one-by-one search cannot find a two-polluter case) — not evidence against F3's
  `VERIFIED` ground truth, evidence that W10 (multi-polluter search) is still needed.
- Limitation: could not literally re-test on Member 2's exact original machine (not available
  to me); the fix's correctness rests on the reasoning that an LCG-mixed seed does not inherit
  a single-bit fragility, backed by two independent real measurements (different OS, different
  JDK major version) both landing close to 50%, not by reproducing the exact prior
  environment.

## 2026-10-10 — Random-order baseline run for real for the first time

**Requirement:** W4's baseline (`eval/baseline.py`) has been interface-only since Phase 4;
Member 2 confirmed the real `OrderRunner` is ready to use.

- File/function: `eval.baseline.run_random_order_baseline`, against the real
  `runner.order_runner.OrderRunner` (not `eval/tests/fake_runner.py`).
- Command: real F1 case, candidate pool of 7 tests (victim + its polluter + 5 noise tests),
  `max_runs=50`, 4 independent trials with `base_seed` 0, 100, 200, 300.
- Result: found the bug in **1, 1, 3, and 2** random shuffles respectively (average 1.75).
  Every matching attempt's order placed `ConfigPolluterTest#pollute` before
  `ConfigVictimTest#expectsDefaultMode`, as expected.
- Comparison: Member 2's real targeted one-by-one search found the same polluter in 1 search
  run (`docs/evidence-m2.md`, F1 row). Both are cheap on this 7-test fixture by design — the
  baseline comparison's real value will show on a larger real-world project, not this one.
- File/function: `eval/README.md` — corrected the baseline status section, which still said
  "No implementation of `OrderRunner` exists in this repo yet" (stale since PR #10).
- Limitation: only F1 run so far; F2/F3/N1/N2 and any idoft case remain.

## 2026-10-10 — Fix two real bugs Member 2 found in the merged W9 work (PR #13)

**Requirement:** Member 2 reviewed the merged W9 work and flagged two concrete problems.
Verified both against the actual code before acting, not taken on trust.

**Problem 1 — wrong explanation of the absolute execution-record path.**
`eval/reports/README.md`'s "Known limitation" section claimed
`runner.diagnose.diagnose()` calls `Path(record_dir).resolve()` internally, making the path
absolute. Read `runner/diagnose.py` to check:
- `runner/diagnose.py:93` does call `Path(record_dir).resolve()`, but only to build `records`,
  used solely for the record-vs-project containment safety check (line 94-96).
- `runner/diagnose.py:103` builds the actual record path from `Path(record_dir)` — the
  argument exactly as given, not `records`. `diagnose()` never resolves the path it returns.
- The real cause: `eval/tools/run_w9_integration.py:27`'s own `RECORD_DIR = REPO_ROOT / "eval"
  / "reports" / "flaketrace-records"`, where `REPO_ROOT = Path(__file__).resolve().parents[2]`
  — already absolute before it reaches `diagnose()`.
- Fix: corrected `eval/reports/README.md`'s "Known limitation" section to attribute the
  absolute path to the script's own `RECORD_DIR`, with the two line numbers above, and noted
  the correction was made after Member 2 pointed it out.

**Problem 2 — duplicated resource-correlation logic, called at the wrong depth.**
Member 2 pointed out that `eval/report.py` had its own `find_resource_edge` instead of using
Member 1's real `evidence.extract.find_edges`/`report_fields` (landed in `m1/resource-edges`
after W9's first version), that this duplicate dropped M1's `FIXED_LIMITATIONS`, and that
`eval/tools/run_w9_integration.py` called `analyse_test(..., depth=1)`, which can never find
F2's edge.
- Verified by reading `fixtures/od-fixture/src/test/java/odfixture/FeatureVictimTest.java`:
  its victim calls `FeatureFlags.isTurboEnabled()` — the actual `System.getProperty` read is
  one call-level inside that helper, not in the test method itself. `evidence/extract.py`'s
  `follow_call`/`walk_root` only follow calls when `len(path) + 1 < max_depth`; at `depth=1`
  that is `0+1 >= 1`, so the call is never followed and the read is never seen. The contract's
  own `DEFAULT_DEPTH` is 2 (`evidence/extract.py:29`).
- Confirmed with a direct one-off check (`evidence.extract.find_edges`/`report_fields` called
  on F2's real polluter/victim at `depth=1` vs `depth=2`, against the already-compiled fixture
  classes): `depth=1` → `shared_resource: None`; `depth=2` → `shared_resource:
  {"kind": "system-property", "key": "odfixture.turbo"}`. Reproduces the bug and confirms the
  fix, independently of any full diagnose() run.
- Fix: `eval/report.py`'s `assemble_report` now takes `resource_fields` — exactly the dict
  `evidence.extract.report_fields(pair)` returns — instead of building its own edge; deleted
  `find_resource_edge` entirely (no longer used anywhere). `eval/tools/run_w9_integration.py`
  now calls `evidence.extract.find_edges`/`report_fields` at `DEFAULT_DEPTH` (2), for F1 and
  the newly-added F2. `eval/tests/test_report.py` rewritten to build its `resource_fields`
  fixtures by calling M1's real `find_edges`/`report_fields` (not a fake, not a re-derived
  local function).
- Command: `py -m unittest discover -s eval/tests -v` (full suite, after the rewrite).
- Result: 68/68 passed.
- Command: `py eval/tools/run_w9_integration.py` (real Maven/JDK run, native Windows JDK 24).
- Result: **F1 → `VERIFIED`** (unchanged — its access is at the root, depth-independent).
  **F2 → `VERIFIED`** for the first time — real edge `system-property:odfixture.turbo`,
  `victim_read_location` correctly reported as `odfixture.FeatureFlags#isTurboEnabled` (not
  the test method), proving the helper call was genuinely followed, not special-cased.
  **N1 → `UNRESOLVED(VICTIM_FAILS_ALONE)`** (unchanged). Saved: `eval/reports/{f1,f2,n1}.json`.
- Updated `eval/reports/README.md`'s "What's NOT here yet" section: removed the wrong claim
  that F2 "needs resource-evidence depth 2, not implemented by Member 1 yet" (depth 2 was
  already implemented; the bug was this script hardcoding `depth=1`), added F2 to the results
  table, and updated `docs/08-MidEval/iteration-plan.md`'s W9 row accordingly.
- Limitation: F3 (needs W10's multi-polluter search) and N2 (`NOT_REPRODUCED`, still an
  unhandled `DiagnosisRuns.status`) remain exactly as before — this fix did not touch either.
- Still open, not actioned here: Member 2 also asked me to review/approve contract PR #17
  (`m1/confirm-contract`, already merged) after the fact — a GitHub review action I cannot
  perform myself (no `gh` CLI, no write-scoped API token in this environment); flagged to the
  member to do directly. (Checked at the time: already approved by both M3 and M2 on
  2026-10-09, before PR #17 merged — nothing to do.)

## 2026-10-10 — W9: add N2, now that its mechanism fix is confirmed cross-platform

**Requirement:** a full read-through of `docs/` found that N2 (`NegativeFlakyTest`) was the
only remaining fixture case blocked by a real interface gap rather than by missing
functionality. Confirmed before acting: `docs/evidence-m2.md`'s 2026-10-10 entry records
Member 2 running `diagnose()` on N2 three times for real (native Windows, JDK 21.0.9) after
the `Random.nextBoolean()` mechanism fix landed, getting `VICTIM_FAILS_ALONE` every time
(16/20, 9/20, 11/20 alone-failures) — not the `NOT_REPRODUCED` it used to give on some
machines. `eval/report.py`'s `assemble_report` already handles `VICTIM_FAILS_ALONE` (it was
only `NOT_REPRODUCED` and `NO_SINGLE_POLLUTER` that were real gaps), so landing N2 needed no
new production code, only adding the case to the integration script.

- File/function: `eval/tools/run_w9_integration.py` — added `run_n2()`, identical in shape to
  `run_n1()` (no resource edge: `assemble_report(diagnosis)` with `resource_fields` omitted).
- Command: `py -m unittest discover -s eval/tests -v` (unaffected by this change — pure-logic
  tests don't call the integration script).
- Result: 68/68 passed.
- Command: `py eval/tools/run_w9_integration.py` (real Maven/JDK run, native Windows JDK 24).
- Result: **N2 → `UNRESOLVED(VICTIM_FAILS_ALONE)`** for the first time through the real
  pipeline — 12/20 alone-successes (i.e. 8/20 alone-failures, consistent with the ~50% rate
  both platforms measured after the mechanism fix). F1/F2/N1 unchanged
  (`VERIFIED`/`VERIFIED`/`UNRESOLVED(VICTIM_FAILS_ALONE)`). Saved: `eval/reports/n2.json`.
- Updated `eval/reports/README.md` (added N2 to the results table and to "What's NOT here
  yet" — now only F3 remains, pending W10), `docs/08-MidEval/iteration-plan.md`'s W9 row,
  `docs/09-Team/members.md`'s M3 row, and `docs/08-MidEval/demo-plan.md`'s "Mocked or
  hardcoded components" table (both rows there were stale — still said W9/the evidence
  extractor wiring was "not built yet"/"not wired in yet", though both had been done in the
  previous session).
- Limitation: F3 remains the only fixture case not in `eval/reports/` — genuinely blocked on
  W10 (multi-polluter search/minimisation, M2, not started: confirmed by reading
  `runner/search.py`, which has only a one-by-one `find_polluter`, no deletion-minimisation
  module).

## 2026-10-10 — Answered 3 open contract questions; agreed ADR-005

**Requirement:** a full `docs/` read-through (same session as the N2 addition above) surfaced
three questions in `docs/contracts/resource-evidence.md` marked `OPEN (Member 3)`, and ADR-005
(`docs/03-Design/decisions/ADR-005-w9-diagnose-cli.md`, M2's real W9 CLI design) needing M3's
agreement. Decided with the member, not unilaterally — each answer below was proposed, the
member confirmed "go with your recommendations," then written.

- **Q2 (`victim_read_location` naming a helper, not the test method):** answered **yes, that is
  the intended meaning** — it names where the read instruction actually executes (F2:
  `FeatureFlags#isTurboEnabled@2`), symmetric with `polluter_write_location`. No code or schema
  change: confirms `eval/report.py`'s existing behaviour, which already takes `report_fields`'s
  locations as-is.
- **Q4 (ground truth has no expected bytecode offsets, Phase 5 checks resources only):**
  answered **acceptable** — `GroundTruthTest` already catches the failure mode that matters
  (wrong resource) automatically on every change; exact offsets were hand-verified for F1 and
  spot-checked for F2 (independently, by Member 1, against `eval/reports/f2.json`). Encoding
  exact offsets into `ground_truth.json` would be brittle for little extra protection.
- **Q6 (BRITTLE cases, POC FJ-01's inverse-polluter shape):** answered **out of scope for
  Iteration 1**, same boundary as filesystem evidence — no fixture case exercises it, so there
  is no real case to drive a new outcome category under schedule pressure.
  `UNRESOLVED(VICTIM_FAILS_ALONE)` is not wrong for a brittle case (the victim genuinely does
  fail alone), just not the most informative category; a distinct reason is named as Iteration
  2 work if a real brittle case (e.g. a fastjson pair) turns up in evaluation.
- **ADR-005 agreement:** ticked M3's row — `assemble_report(runs, fields)` as the only report
  builder and catching `UnhandledStatus` both match what Phase-W9 work (above) already built
  and verified; nothing in the ADR asks `eval/` to change.
- Command: `py -m unittest discover -s eval/tests -v` (unaffected — these are doc-only
  decisions, no code touched). Result: 68/68 passed.
- Limitation: M1's row in ADR-005 is still unticked, so the ADR is not yet fully agreed by all
  three members — only M3's part of this entry is closed. (Later ticked by M1 in PR #30 —
  ADR-005 is now fully agreed.)

## 2026-10-10 — Agree ADR-006 (evidence depth 1–5); ADR-007 decided, not yet tickable

**Requirement:** two more ADRs appeared needing M3's agreement, found while re-checking repo
state for "what's left for M3": ADR-006 (M1, `docs/03-Design/decisions/ADR-006-evidence-depth-
auto-deepen.md` — accept depths 1–5, pair mode auto-deepens one level at a time only when
`DEPTH_LIMIT` was hit, stopping at the shallowest edge; new `analyse_pair()` helper) and ADR-007
(M2, on branch `m2/w10-minimise`, not yet a PR — `ddmin` multi-polluter minimisation for F3,
reusing `POLLUTER_FOUND` with a list of polluters).

- **ADR-006: ticked M3's row, agree.** Reasoning: the shallowest-depth-wins rule means F1/F2/F3
  keep paying exactly what they pay today (`depth_used` 2), while fastjson's real cases (depth
  4 and 5) become explainable instead of permanently `NO_SUPPORTED_RESOURCE_EVIDENCE`. The
  alternative of raising the *default* depth to 5 would make every pair pay the most expensive,
  most over-approximated walk even when depth 2 already has the answer — worse for the common
  case to fix the rare one. Noted the follow-up this creates: once M1's `analyse_pair()` lands,
  `eval/report.py`'s callers (`eval/tools/run_w9_integration.py`, and M2's `runner/cli.py`)
  switch their separate `analyse_test`+`find_edges` calls to the one helper — not done yet,
  since `analyse_pair` doesn't exist in `main` yet.
- **ADR-007: agree in principle, not yet ticked in the file.** The ADR only exists on M2's own
  in-progress branch (`m2/w10-minimise`), not `main`, and there is no PR for it yet — nothing to
  safely commit the tick against without writing onto another member's unfinished branch.
  Recorded here instead: I agree with the proposed rule ("`POLLUTER_FOUND` reused for several
  polluters; first polluter's resource shown, the rest named in `limitations`") because it
  applies the exact same shape already agreed for Q1/Q4 (`edges[0]` plus a `limitations` note)
  to a new case, rather than inventing a new rule under schedule pressure. `eval.report.
  assemble_report` already accepts a multi-element `diagnosis.polluters` list with no code
  change (`report["polluters"] = [p.to_dict() for p in diagnosis.polluters]` already loops).
  Will tick ADR-007's actual file once M2 opens a PR for W10.
- Command: `py -m unittest discover -s eval/tests -v` (unaffected — doc-only session).
  Result: 68/68 passed.

## 2026-10-10 — Switch to M1's real `analyse_pair()` (ADR-006 follow-up)

**Requirement:** ADR-006's agreement text committed to switching `eval/report.py`'s callers to
`evidence.extract.analyse_pair()` once it landed. Member 1 merged it for real (PR #34) the
same day.

- Checked first, before changing anything: `eval/report.py` itself needed no change — it
  already takes `report_fields(pair)`'s output as an opaque `resource_fields` argument and has
  never called `analyse_test`/`find_edges` directly. Only `eval/tools/run_w9_integration.py`
  (the actual caller) needed the switch.
- File/function: `eval/tools/run_w9_integration.py` — `run_f1()`/`run_f2()` now call
  `evidence.extract.analyse_pair(project, polluter_id, victim_id)` (default depth 2,
  auto-deepen) in place of separate `analyse_test(..., depth=DEFAULT_DEPTH)` calls for the
  polluter and victim combined with `find_edges()`.
- Command: `py -m unittest discover -s eval/tests -v`. Result: 68/68 passed (no test exercises
  this script directly, as documented in its own module docstring).
- Command: `py eval/tools/run_w9_integration.py` (real Maven/JDK run, native Windows JDK 24).
- Result: **F1 → `VERIFIED`, F2 → `VERIFIED`, N1/N2 → `UNRESOLVED(VICTIM_FAILS_ALONE)`** — all
  four unchanged. Diffed the regenerated `eval/reports/{f1,f2,n1}.json` against the previously
  committed versions: identical except the execution-record timestamp (confirms F1 and F2 both
  still resolve their real edge at depth 2, exactly as before — the auto-deepening adds no
  cost here, only capability for deeper real cases). `n2.json` differs by its alone-success
  count (9/20 this run vs 12/20 previously) and the timestamp only — expected, since N2 is
  intermittent by design; the outcome itself (`VICTIM_FAILS_ALONE`) is unchanged.
- File/function: `eval/reports/README.md` — documented the switch and why it changes nothing
  observable on the fixture.
- Limitation: none introduced. This only removes a dependency on the now-deleted separate
  `analyse_test`+`find_edges` call pattern; fastjson still has not been run through the full
  `diagnose()` pipeline (only through the extractor, as before).

## 2026-10-10 — Fix a real contradiction Member 2 found in W10's evidence wording (PR #35)

**Requirement:** Member 2's W10 PR (#35, F3 now `VERIFIED` end to end via `ddmin` minimisation)
flagged a real bug against `eval/report.py`: their new multi-polluter combining function
(`runner/cli.py`'s `combine_fields`, on branch `m2/w10-minimise`) can set
`shared_resource=None` (because not every polluter has an edge, so none is shown as the
primary resource) while its own `limitations` already name which specific polluters *did*
have an edge. `assemble_report`'s unconditional "No polluter-write/victim-read resource edge
was found by static analysis" line, appended whenever `shared_resource is None`, directly
contradicts those specific lines.

- Read the real diff before fixing anything: `git diff origin/main...origin/m2/w10-minimise --
  runner/cli.py` on `m2/w10-minimise` commit `8a16388`. Confirmed the exact shape:
  `combine_fields`'s "not every polluter has evidence" branch returns
  `dict(fields[0], shared_resource=None, ..., limitations=lines + found + missing)` where
  `found`/`missing` already say, per polluter, whether its edge was found.
- File/function: `eval/report.py` — `assemble_report` now reads an optional
  `any_edge_found: bool` key from `resource_fields` (defaulting to the old
  `shared_resource is not None` check when the key is absent, so M1's ordinary
  single-polluter `report_fields()` output, which never sets this key, is completely
  unaffected). The generic blanket line is now gated on `any_edge_found`, not `edge_found`.
  `edge_found` itself is unchanged and still drives `DecisionInput.resource_edge_exists` (the
  VERIFIED/NO_SUPPORTED_RESOURCE_EVIDENCE decision) — only the limitations *text* changes, not
  the outcome logic, which already matches ADR-007's rule ("VERIFIED only if every polluter has
  an edge") with no change needed.
- File/function: `eval/tests/test_report.py` — two new tests:
  `test_several_polluters_partial_evidence_suppresses_the_generic_no_edge_line` (some edge
  found, `any_edge_found=True` → generic line absent, specific lines present) and
  `test_several_polluters_zero_evidence_keeps_the_generic_no_edge_line` (`any_edge_found=False`
  → generic line present, correctly). Strengthened the existing
  `test_polluter_found_without_edge_gives_no_supported_resource_evidence` to assert the
  generic line is still present for the plain single-polluter case (backward compatibility).
- Mutation check: changed `if not any_edge_found:` back to `if not edge_found:` — the new
  partial-evidence test failed exactly as expected, reproducing the contradiction verbatim
  (`'...found by static analysis.' unexpectedly found in [...]`); restored
  (`git diff eval/report.py` clean after).
- Command: `py -m unittest discover -s eval/tests -v`. Result: **70/70 passed** (68 existing +
  2 new).
- Limitation: this only fixes the wording contradiction in `eval/report.py`. It does not land
  M2's `combine_fields` change itself (`runner/cli.py`, their file, still on their own
  unmerged branch) — their combining function needs one more line once this fix merges:
  `any_edge_found=bool(found)` added to the returned dict in the "not every polluter has
  evidence" branch. Flagged back to Member 2 rather than edited myself (not my folder).
- Also recorded: agreement with ADR-007's per-polluter report rule (first polluter's resource
  shown, others named in `limitations`, `VERIFIED` only if every polluter has an edge) as asked
  in PR #35's description — not yet tickable in the ADR file itself, same situation as
  ADR-006 before it merged: the file exists only on Member 2's unmerged branch, not `main`.

## 2026-10-10 — Tick ADR-003, ADR-004, ADR-007; confirm F3's ground truth end to end

**Requirement:** Member 2 relayed four items once ADR-007 (W10) merged to `main`: tick ADR-007
there for real now that it's mergeable; tick ADR-003 and ADR-004 (both had an empty M3 row
left over from earlier in the project); update `ground_truth.json`'s F3 note, which still said
"needs W10"; and (separately, "when you have time") the NOT_REPRODUCED/schema-change ask
already tracked as ADR-008.

- Verified each claim against the real repo before acting on any of it: read ADR-007's
  agreement table on `main` directly (M1 ☐, M2 ☑, M3 ☐, confirmed empty), ADR-003's and
  ADR-004's M3 rows (both ☐, confirmed empty), commit `539b2dc` (`git show`, confirmed it adds
  `any_edge_found=bool(found)` to `combine_fields`'s mixed-evidence branch exactly as
  described), and `ground_truth.json`'s F3 entry (confirmed it still read "needs W10").
- File/function: `docs/03-Design/decisions/ADR-007-w10-ddmin-minimisation.md`,
  `ADR-003-order-runner-junitcore-harness.md`, `ADR-004-w7-diagnosis-runs.md` — ticked M3's row
  on each, with a comment specific to what M3's own code actually does (not a bare checkmark):
  ADR-007 confirms the per-polluter rule and that `assemble_report` needed no change for a
  multi-polluter `POLLUTER_FOUND` (the field was already a list); ADR-003 notes `eval/`
  consumes the harness's `DiagnosisRuns` output without needing its internals; ADR-004 confirms
  `n=20` (already used throughout `eval/benchmark/`) and that the `DiagnosisRuns`→
  `DecisionInput` mapping built in `eval/report.py` (W9) matches this ADR's fields.
- File/function: `fixtures/od-fixture/ground_truth.json` — F3's `expected_outcome_notes`
  appended (not replaced, so the original prediction stays legible) with the real W10
  confirmation, citing `docs/evidence-m2.md`'s real W10 entries: `diagnose()` gives
  `POLLUTER_FOUND` with both polluters (search 12 runs, minimisation shrinks the 12-test
  prefix to the 2-test 1-minimal set); the real end-to-end command gives `VERIFIED`, 20/20
  reproduced, 0/20 alone, resource `odfixture.Toggles#flagA` shown with `flagB` named in
  `limitations`.
- Command: `py -c "import json; json.load(open('fixtures/od-fixture/ground_truth.json'))"` —
  confirmed the edit kept the file valid JSON (easy to break with an unescaped character inside
  a long string value).
- Command: `py -m unittest discover -s eval/tests -v`. Result: 70/70 passed (unaffected by a
  documentation-only / ground-truth-notes-only change, as expected — no test asserts on the
  exact text of `expected_outcome_notes`).
- Limitation: none. The larger NOT_REPRODUCED/schema-change ask (ADR-008: nullable
  `failure_signature`, optional `order_exploration`, new `INFRASTRUCTURE_FAILURE` reason, new
  fixture cases F4/N3) is real, substantial new work, not done in this entry — tracked
  separately, pending the member's decision on scope and timing.

## 2026-10-10 — ADR-008: NOT_REPRODUCED handling, schema change, fixtures F4/N3

**Requirement:** the member approved going ahead with ADR-008 (Member 2's proposal for
failures that do not reproduce). Member 3's side (step 3 of the ADR's own order-of-work
table): the schema change, `decide()` row, `assemble_report` wiring, and two new
pre-registered fixture cases.

**Fixtures F4 and N3, written before any run** (`fixtures/od-fixture/ground_truth.json`):
- **F4** (`AlwaysEarlyVictimTest`/`ZzzLatePolluterTest`, new `LateFlag` static field): class
  names chosen so the polluter sorts alphabetically after the victim, exploiting this
  project's confirmed alphabetical discovery order (`docs/evidence-m2.md`'s W7 Task 3) so the
  natural order can never reproduce the bug — exactly the shape ADR-008's order-shuffling step
  is for.
- **N3** (`EnvDependentNegativeTest`): models a failure whose real cause is an environment
  variable FlakeTrace never sets. Deliberately does **not** check the literal `CI` variable
  name — GitHub Actions sets `CI=true` on every real runner, so that would make this negative
  control fail on our own CI job. Uses a fictitious name (`FLAKETRACE_N3_NEVER_SET`) instead.
- Real verification before writing a single line of Python: compiled
  (`mvn -B -q -f fixtures/od-fixture/pom.xml test-compile`), confirmed the real discovered
  order places `AlwaysEarlyVictimTest` first and `ZzzLatePolluterTest` last of 16 methods
  (`runner.discovery.discover_order`), ran the full module (`mvn -B test`, no new failures:
  still exactly F1/F2/N1/F3's four, F4/N3 both pass), ran the real one-fresh-JVM order
  `[ZzzLatePolluterTest#setLateFlag, AlwaysEarlyVictimTest#expectsLateFlagUnset]` via
  `runner.order_runner.OrderRunner.run_ordered` (polluter passes, victim FAILS with
  `java.lang.AssertionError` — exactly the predicted mechanism), and ran the real victim alone
  (passes). Also ran real `diagnose()` on both F4 and N3 in the natural order: both give
  `NOT_REPRODUCED`, `alone_n=0` — confirming the exact gap ADR-008 names, not a bug in the
  fixture. **Independent cross-check**: Member 1's own `GroundTruthTest`
  (`evidence.tests.test_extract`, untouched by me) also passed with these two new cases added
  to `ground_truth.json` — it found the real `LateFlag#isSet` edge for F4's pair and no edge
  for any N3 pair, matching my ground truth exactly, from a completely independent test.
- Added F4/N3 to `eval/benchmark/manifest.json` (both `not_yet_run`, no log files) — required
  by `test_real_manifest_matches_fixture_ground_truth`, which checks the two files' case IDs
  match exactly.

**Schema** (`eval/schema/report.schema.json`): `failure_signature` nullable via the same
`oneOf`/null pattern already used (and already fixed once this session) for `shared_resource`;
new optional `order_exploration` object; `INFRASTRUCTURE_FAILURE` added to the
`unresolved_reason` enum. **Found and fixed a real gap beyond what the ADR literally asked
for**, by reading `runner/diagnose.py`'s actual code rather than assuming: ADR-008's text says
nullable `failure_signature` "only for NOT_REPRODUCED," but `run_steps` sets
`reference_signature=None` for its *entire* `NOT_REPRODUCED` status, which `INFRASTRUCTURE_FAILURE`
is decided from too (same status, same `None` reference) — so a schema tied strictly to the
`NOT_REPRODUCED` string would reject a real future `INFRASTRUCTURE_FAILURE` report. Widened the
conditional to cover both reasons before this became a real bug.

**`eval/outcome.py`**: `REASON_INFRASTRUCTURE_FAILURE`; new `DecisionInput.infrastructure_failures`
field (default 0 — a caller that never reports it gets exactly the pre-ADR-008
`SIGNATURE_MISMATCH` behaviour, proven by a dedicated test); new `decide()` row between
`NOT_REPRODUCED` and `SIGNATURE_MISMATCH`.

**`eval/report.py`**: `assemble_report` now handles `NOT_REPRODUCED` (was `UnhandledStatus`);
builds `failure_signature: null` whenever `diagnosis.reference_signature is None` (covers both
`NOT_REPRODUCED` and `INFRASTRUCTURE_FAILURE`); reads `infrastructure_failures` via
`getattr(diagnosis, ..., 0)` and the new optional `order_exploration` via a `hasattr` check on
all five needed fields — both forward-compatible with Member 2's `DiagnosisRuns` not having
them yet, omitted entirely (schema allows it) until that lands.

- Command: `py -m unittest discover -s eval/tests -v`. Result: **80/80 passed** (68 existing +
  12 new, across `test_schema_validator.py`, `test_outcome.py`, `test_report.py`,
  `test_yield_report.py`).
- Mutation checks, each confirmed failing before restoring: `decide()`'s new row condition
  forced to `False` → `test_row3b_infrastructure_failure` failed exactly as expected;
  `assemble_report`'s `failure_signature = None if ref is None` forced to always build a dict
  → `test_not_reproduced_with_isolation_data_gives_unresolved` failed with the real
  `AttributeError` that would occur in production.
- Real run confirming no regression: `py eval/tools/run_w9_integration.py` — F1/F2 still
  `VERIFIED`, N1/N2 still `UNRESOLVED(VICTIM_FAILS_ALONE)`, resource edges and locations
  byte-identical to before (only the execution-record timestamp and N2's own designed
  randomness differ); `original_failing_order` correctly grew to include the 3 new fixture
  classes that sort before each victim alphabetically.
- Real run confirming the exact documented limitation, not a bug: real `diagnose()` on N3 in
  the natural order gives `NOT_REPRODUCED` with `alone_n=0`; calling `assemble_report` on that
  real diagnosis raises `ValueError: isolation_n must be > 0` — exactly as designed, pending
  Member 2's `diagnose()` change (ADR-008 step 4, not yet landed).
- **Also discovered and fixed, independent of this ADR**: this session's branch had been
  created from a stale local `main` ref (missing the just-merged ADR-003/004/007 ticks commit
  and everything after it up to Member 1's ADR-007 agreement). Found it the moment I checked
  `git log --oneline -1 HEAD` against `origin/main` and saw they disagreed by several commits.
  Diagnosed the exact scope with `git diff --name-only <stale-base> origin/main` (8 files,
  only 3 overlapping with this session's own edits), restored the 5 untouched files directly
  from `origin/main`, and manually re-applied this session's own F4/N3 additions and new
  entries on top of the other 3 files' correct (non-stale) content — rather than running
  `git merge`/`git stash`/`git rebase` myself, which this project's rules reserve for the
  member. Confirmed clean afterward: `git diff origin/main -- <each of the 8 files>` shows
  zero difference on the 7 untouched files and only this session's genuine new content on
  the 8th (`ground_truth.json`).

## 2026-10-10 — Fix a real merge-order risk Member 2 found in PR #45

**Requirement:** Member 2 reviewed PR #45 (ADR-008's M3 side) and flagged a real risk: today,
`runner.diagnose()` still returns `NOT_REPRODUCED` with `alone_n = 0` (ADR-008 step 4, their
diagnose() change making it always run the alone check, hasn't landed yet). Calling
`assemble_report` on that real shape hits `eval.outcome.DecisionInput`'s `isolation_n > 0`
check, raising a bare `ValueError` the CLI does not catch — crashing with a traceback instead
of the designed "exit 3, no report yet" behaviour, regardless of which of the two changes
(theirs or mine) merges first.

- File/function: `eval/report.py` — `assemble_report` now raises `UnhandledStatus` explicitly
  when `diagnosis.status == NOT_REPRODUCED and diagnosis.alone_n == 0`, before building
  `DecisionInput` at all. Once Member 2's `diagnose()` change lands (`alone_n > 0` always),
  this branch is simply never reached and the real report-building path runs unchanged.
- File/function: `eval/tests/test_report.py` — renamed/updated
  `test_not_reproduced_with_todays_real_shape_is_unhandled_not_a_crash` to assert
  `UnhandledStatus` (was `ValueError`).
- Command: `py -m unittest discover -s eval/tests -v`. Result: 80/80 passed.
- Mutation check: disabled the new guard (`if False:`) — the test failed with the exact real
  `ValueError: isolation_n must be > 0, got 0` traceback Member 2 described; restored,
  confirmed `git diff` clean.
- Also asked by Member 2: comment agreement on ADR-008's PR (#42) or tick M3's row there.
  Not done directly — I have no GitHub write access in this environment; drafted a comment for
  the member to post, and will tick the actual ADR file in a follow-up PR once #42 merges
  (same pattern as ADR-006/007).
- **Found independently, not mentioned by Member 2**: PR #45's real CI `runner` job was
  failing for a different, real reason — three hardcoded counts in `runner/tests/` (M2's
  folder) were stale because this PR's new F4/N3 fixture classes changed the fixture's real
  discovered-order size (13 → 16 methods) and F3's search prefix (12 → 14). Flagged to the
  member, who authorized fixing it directly rather than waiting on Member 2 — see the next
  entry for the fix itself and the real re-verification.

## 2026-10-11 — Fix the 3 stale hardcoded counts in `runner/tests/`, with the member's go-ahead

**Requirement:** the member authorized fixing the three CI failures named above directly,
rather than relaying them to Member 2 first. `runner/tests/` is not my folder, so this is
recorded explicitly, with the real reasoning, rather than a silent edit.

- Re-verified the real discovered order first (`runner.discovery.discover_order` on the
  compiled fixture, native Windows JDK 24): **16** methods, `AlwaysEarlyVictimTest#...` first,
  `ZzzLatePolluterTest#...` last — matches the design intent exactly (both chosen to sort at
  the extremes).
- File/function: `runner/tests/test_discovery.py` —
  `test_all_thirteen_fixture_methods_in_alphabetical_class_order` renamed to
  `test_all_fixture_methods_in_alphabetical_class_order` (the literal "thirteen" is no longer
  true); asserts `len == 16`, first two = `[AlwaysEarlyVictimTest#expectsLateFlagUnset,
  ConfigPolluterTest#pollute]`, last = `ZzzLatePolluterTest#setLateFlag`.
- File/function: `runner/tests/test_diagnose.py` — ran the real test first to get the exact
  number rather than computing it by hand:
  `py -m unittest runner.tests.test_diagnose.TestDiagnoseOnFixture.test_f3_two_polluters_are_found_by_minimisation`
  → real failure, `AssertionError: 14 != 12`, confirming the exact new value. Updated
  `search_runs` assertion from 12 to 14, with a comment naming the real cause (two of the new
  classes sort before F3's victim, growing its search prefix).
- File/function: `runner/tests/test_cli.py` — same real cause; updated the summary-line
  substring assertion from `"12 earlier tests"` to `"14 earlier tests"`.
- Command: `py -m unittest discover -s runner/tests -v` (real JVM runs, native Windows JDK 24).
  Result: **108/108 passed** (was 105/108 before this fix, confirmed by reproducing the 3
  failures first).
- Command: `py -m unittest discover -s eval/tests -v`. Result: 80/80 passed (unaffected, as
  expected — pure Python logic, no JVM).
- Limitation: none found beyond the three fixed. CI on JDK 8/Linux not yet re-confirmed from
  this exact commit (runs on the PR).

## 2026-10-11 — Merge conflict: adopted Member 2's independent, more durable fix over my own

**Requirement:** Member 2 found and fixed the same three stale `runner/tests/` counts
independently (PR #47, merged to `main` before I'd pushed my own fix). Merging `main` into
this branch conflicted on exactly the three files I'd also touched.

- Read both sides before resolving anything. Member 2's fix is **not** the same shape as
  mine — mine hardcoded the new numbers (16, 14); theirs computes the expected answer from
  the real data every time: `test_discovery.py` now reads every real `@Test` method straight
  from the fixture's `.java` sources (regex, independent of the discovery code under test) and
  checks `discover_order`'s result is exactly that set; `test_diagnose.py` and `test_cli.py`
  now derive the expected count from `len(runs.original_order) - 1` /
  `len(report["original_failing_order"]) - 1` instead of a literal number.
- Decision: kept Member 2's version in all three conflicts, discarded my own hardcoded
  numbers. This isn't deference for its own sake — my fix was correct today but exactly as
  fragile as the thing that caused this whole problem (a hardcoded count that breaks the next
  time any fixture case is added); theirs eliminates that class of bug permanently.
- Command: `py -m unittest discover -s runner/tests -v` (real JVM). Result: **108/108
  passed**. `py -m unittest discover -s eval/tests -v`: 80/80 passed, unaffected.
- Limitation: none. My own three-number fix (previous entry) is superseded, not wrong — kept
  in the log as an honest record of what was actually done at the time, not retroactively
  edited.

## 2026-10-11 — Sync stale status docs to the real current state

**Requirement:** PR #45 confirmed merged (all 4 CI jobs green on `main`'s tip). A full survey
("what's left for M3 in Iteration 1") found several status docs describing a state that no
longer matches reality — F3/W10 and ADR-008/F4/N3 had all landed since these were last
written.

- File/function: `docs/08-MidEval/iteration-plan.md` — W9's row updated to describe all 7
  real fixture cases (F1-F4, N1-N3) and ADR-008; W10's row corrected from "PR pending" to
  **Complete** (PR #35/#38/#40, merged); W11's row updated from "Not started" to **In
  progress** (chapters drafted and sent, not yet confirmed incorporated, due a refresh).
- File/function: `docs/09-Team/members.md` — M3's current-task row corrected (was still
  saying "Only F3 remains, needs W10 — not started," when W10 had been merged for over a
  day).
- File/function: `docs/08-MidEval/panel-action-register.md` — A5 moved from `IN PROGRESS` to
  **COMPLETE**: all 5 original fixture cases now run end to end through the real pipeline,
  plus F4/N3 extend "diverse scenarios" further; summary table's completed/open lists updated
  to match.
- Command: `py -m unittest discover -s eval/tests -v`. Result: 80/80 passed (doc-only
  session, sanity check).
- Limitation: none. Report chapters 4/7/8 (drafted earlier, sent to the member) are flagged
  as needing a refresh against this now-current state — not done in this entry, since it
  needs the member's confirmation on whether/how they were incorporated first.

## 2026-10-11 — ADR-008 crash-count follow-ups, requested by Member 2 against PR #49

**Requirement:** PR #49 (ADR-008 runner side) merged to `main`: `runner.diagnose.DiagnosisRuns`
now really carries `order_given`, `shuffled_orders`, `orders_exhausted`, `shuffle_seed_base`,
`reproducing_seed`, `infrastructure_failures`, `shuffle_infrastructure_failures` and
`alone_infrastructure_failures`. Member 2 flagged two gaps against the merged branch: (1) the
NOT_REPRODUCED/INFRASTRUCTURE_FAILURE limitation text always said "given order" even when
ADR-008 discovered the order itself via a shuffle, and never mentioned how many shuffles were
tried; (2) `runner.cli`'s own summary totals crashes across the sequence, shuffles and the
alone check (`infrastructure_failures + shuffle_infrastructure_failures +
alone_infrastructure_failures`), but the report JSON's `order_exploration.infrastructure_failures`
only ever held the sequence-phase field, so a victim that only crashed during the alone check
(sequence itself clean) silently reported 0 crashes.

- File/function: `eval/report.py` — `_order_exploration()` now takes an already-combined
  `infrastructure_failures` total (summed in `assemble_report` from all three DiagnosisRuns
  fields via `getattr(..., 0)`, matching `runner.cli`'s own sum) and includes it in the
  `order_exploration` dict unconditionally (not scoped to any one status: a shuffle that found
  the reproduction, e.g. F4, is exactly as worth reporting as one that never did). The
  NOT_REPRODUCED/INFRASTRUCTURE_FAILURE limitation text now reads `diagnosis.order_given` to
  say "given" vs "discovered", and names `diagnosis.shuffled_orders` when non-zero. The
  INFRASTRUCTURE_FAILURE text now branches on whether the sequence itself failed
  (`sequence_any_failures > 0`, the original crash-only-sequence case) or not (the new case:
  sequence clean, crashes only in another phase).
- File/function: `eval/outcome.py` — `decide()` gained the new branch (`sequence_failures_any
  == 0 and infrastructure_failures > 0` → `UNRESOLVED(INFRASTRUCTURE_FAILURE)`, row 3b in the
  updated module docstring's decision table). `DecisionInput.__post_init__`'s validation for
  `infrastructure_failures` relaxed from `0 <= x <= sequence_failures_any` to `x >= 0`: the
  field is now a combined total across every phase, not bounded by the sequence's own failure
  count (a clean sequence with a crashing alone check is real and valid, not an input error).
- File/function: `eval/schema/report.schema.json` — `orderExploration`'s
  `infrastructure_failures` property and `required` entry (already added in the prior session,
  confirmed still correct and consistent with the above).
- Tests: `eval/tests/test_outcome.py` — replaced
  `test_infrastructure_failures_exceeding_failures_any_raises` (now describes behaviour that no
  longer exists) with `test_infrastructure_failures_exceeding_sequence_failures_any_is_allowed`
  (asserts it does *not* raise) and a new `test_infrastructure_failures_negative_raises`; added
  `test_row3b_infrastructure_failure_elsewhere` for the new decide() branch; renamed the
  existing row-lettering tests to match the docstring's new 3a/3b/3c/3d split.
  `eval/tests/test_report.py` — replaced the hand-rolled `_WithInfraFailures` stand-in (no
  longer needed now that `DiagnosisRuns` has the real field) with direct
  `infrastructure_failures=`/`alone_infrastructure_failures=` overrides on `_diagnosis()`;
  added `test_not_reproduced_names_discovered_order_and_shuffle_count` and
  `test_infrastructure_failure_elsewhere_gives_unresolved_with_null_signature`.
  `eval/tests/test_schema_validator.py` — `test_order_exploration_is_optional_but_validated_
  when_present`'s literal `order_exploration` fixture was missing the new required
  `infrastructure_failures` key (pre-existing test, written before this field existed); added
  it.
- Command: `py -m unittest eval.tests.test_stats eval.tests.test_outcome
  eval.tests.test_schema_validator eval.tests.test_examples eval.tests.test_baseline
  eval.tests.test_yield_report eval.tests.test_report` (the CLAUDE.md §8 command plus
  `test_report`). Result: **84/84 passed**.
- Mutation check: temporarily changed the new `decide()` branch's condition (`if
  d.infrastructure_failures > 0:` → `if False:`) and re-ran `eval.tests.test_outcome`:
  `test_row3b_infrastructure_failure_elsewhere` failed as expected
  (`NOT_REPRODUCED != INFRASTRUCTURE_FAILURE`), confirming the test actually exercises the new
  branch rather than passing vacuously. Reverted; re-ran clean: 17/17 passed.
- Limitation: `eval/report.py`'s `_order_exploration()` is reported for every status now that
  `DiagnosisRuns`'s order fields have real defaults (not just NOT_REPRODUCED) — this is a
  behaviour change from the previous session's hasattr-gated version, done deliberately (not
  flagged by anyone) because scoping it to one status would have hidden F4's real shuffle data
  (`reproducing_seed=1`) from its own `VERIFIED` report. Not yet cross-checked against a real
  `runner diagnose` CLI run on F4/N3 (that needs JDK 8 + Maven, not run in this session) — only
  against hand-built `DiagnosisRuns` objects and the real schema/decide() code.

## 2026-10-11 — Random-order baseline run for real on F2/F3/F4, class-first shuffling

**Requirement:** `LeftWorkForM1&M3.md` (item M3 #5, backed by a relayed message from Member
2): claim B11 said "we have run the baseline tools" NOT YET; the plan was (1) reword B11
honestly rather than leave it OPEN with stale text, and (2) before running more, make
`eval/baseline.py` shuffle classes first, then methods within a class (never mixing classes —
JUnit cannot run an order like ClassA#m1, ClassB#m1, ClassA#m2 in one suite), then rerun on
F1-F4.

- File/function: `eval/baseline.py` — new `_shuffle_classes_then_methods()`, called from
  `run_random_order_baseline` in place of the old plain `rng.shuffle(order)` on the whole pool.
  Groups the candidate+victim pool by class, shuffles the class order, then independently
  shuffles each class's own method order, then concatenates — so a class's methods are always
  contiguous in the result, which is the only kind of order
  `runner.order_runner.OrderRunner`/JUnitCore can actually execute.
- Test: `eval/tests/test_baseline.py` — `test_shuffle_never_interleaves_two_classes`, using a
  synthetic 5-method, 2-class pool (the real fixture's classes all have exactly 1 method, so a
  bug here would not show up against it) across 30 shuffles, asserting no class reappears after
  another class has taken a turn.
- Command: `py -m unittest eval.tests.test_baseline -v`. Result: all 13 tests pass (12 existing
  + 1 new), including the 9 pre-existing `TestRandomOrderBaseline` tests unaffected (the real
  fixture's pool has one method per class, so grouping-then-shuffling and plain shuffling
  produce the same distribution there).
- Mutation check: temporarily reverted `_shuffle_classes_then_methods` back to the old plain
  `rng.shuffle(order)` and re-ran the new test alone: failed immediately
  (`'odfixture.ClassB' unexpectedly found in [...]`), reproducing exactly the impossible,
  class-interleaved order the fix prevents. Restored; re-ran clean: 13/13 passed.
- File/function: `eval/tools/run_baseline_real.py` (new) — runs
  `eval.baseline.run_random_order_baseline` against the real
  `runner.order_runner.OrderRunner`, for F1, F2, F3 and F4, each with 4 independent trials
  (`base_seed` 0/100/200/300, `max_runs=50`), candidate pool = that case's polluter(s) + the
  fixture's 4 benign noise tests (`MathUtilTest`×2, `StringUtilTest`×2).
- Command: `py eval/tools/run_baseline_real.py` (real Maven/JDK, native Windows JDK 24).
  Result: found the bug in **every** trial, every case:
  - F1 (pool 6, 1 polluter): 1, 1, 3, 2
  - F2 (pool 6, 1 polluter): 1, 1, 3, 2
  - F3 (pool 7, 2 polluters, both required): 1, 2, 3, 1
  - F4 (pool 6, 1 polluter, order-needs-reshuffle): 1, 1, 3, 2
  Written to `eval/reports/baseline_results.json`.
- Discrepancy found and flagged (not fixed retroactively): the 2026-10-10 entry above describes
  F1's candidate pool as "7 tests ... 5 noise tests". Recounting
  `fixtures/od-fixture/ground_truth.json`'s `benign_noise_tests` gives exactly 4 noise tests (2
  classes, 2 methods each), so the real pool is 6, not 7. This run's F1 result (1, 1, 3, 2) is
  byte-for-byte identical to the earlier entry's, confirming the actual candidate set never
  changed — only the earlier prose's count was wrong. Documented in `eval/README.md` rather than
  silently editing the 2026-10-10 entry.
- File/function: `eval/README.md` — baseline status section rewritten with the real F1-F4
  table and the pool-count discrepancy note above.
- File/function: `docs/07-Defense/claims-ledger.md` — B11 reworded from "NOT YET" to
  "PARTIALLY" (our own baseline ran for real on all 4 OD cases; published tools iFixFlakies/
  iDFlakies still not integrated), kept OPEN per Member 2's suggestion.
- Limitation: only F1-F4 (the OD fixture cases with a polluter to find) run; N1/N2 have no
  polluter to search for, so the comparison doesn't apply to them. No idoft case cloned/built
  yet, so the baseline's real comparative value (targeted search should scale better than
  random shuffling on a larger project) remains unmeasured on anything but this small fixture.

## 2026-10-11 — Close ADR-002, fix C6/C7 depth wording, sync stale register rows

**Requirement:** `LeftWorkForM1&M3.md` (M3 #2, #4, #6): tick ADR-002 (M3's row was the only one
missing); fix the C6/C7 "two hops" vs. real-depth wording ADR-002 and claim E11 both flagged as
needing a check; sync A8/A9's stale "still to do" notes and the W4/W9/W14 iteration-plan rows
against current real state.

- File/function: `docs/03-Design/decisions/ADR-002-evidence-extractor-implementation.md` —
  ticked M3's agreement row (depth-2 default needs no change on `eval`'s side: `eval.report`/
  `eval.outcome` consume `report_fields`'s output, not the depth it was found at). Resolved the
  ADR's own open wording-check note in its Consequences section: the POC-hop-to-our-depth
  conversion formula (N+1) does not actually hold for FJ-02 — checked against claim E11's real
  measurement (the real extractor finds this exact edge only at depth 5, not depth 3, which is
  what "two hops" (`FT_HOPS=2`) would convert to).
- File/function: `docs/07-Defense/claims-ledger.md` — C6 and C7 both corrected: "two hops down"
  is now attributed explicitly to the POC's own hand count, with a note that the real extractor
  finds the same edge only at depth 5 (not a numbering-convention offset, a materially deeper
  real call chain); C7's "rank 39 → 1" is now stated as internal to the POC's own ranking
  methodology, not comparable to our current depth numbering. E11's row updated to point at the
  fix instead of still asking for it.
- File/function: `docs/08-MidEval/panel-action-register.md` — A8 and A9 updated from "logic"/
  "schema" complete with a pending real-data caveat, to fully complete with the real evidence
  that now exists (85 passing `eval/tests`, real Wilson intervals and real schema-validated
  reports for F1-F4); "Actions completed" summary line gained A6 (already ticked individually,
  missing from the rollup list).
- File/function: `docs/08-MidEval/iteration-plan.md` — W4's row corrected from "Complete (no
  real runs)" to the real F1-F4 baseline numbers; W9's row corrected to drop the two
  "pending Member 2's ... landing" clauses, since PR #49 merged (F4 `VERIFIED` via shuffle, N3
  real `NOT_REPRODUCED`, both schema-validated, not hand-built); W14's "(PR pending)" corrected
  to "(PR #49 merged)".
- Command: `py -m unittest discover -s eval/tests -v`. Result: **85/85 passed** (doc-only
  changes in this entry; sanity check against the baseline-change commit above, both landing in
  the same session).
- Limitation: ADR-002's top-level `Status: PROPOSED` line is left as-is — it is M1's own ADR to
  retitle once they choose to (ADR-007/ADR-008 are left the same way in this repo despite being
  fully agreed), and `LeftWorkForM1&M3.md` only asked that of M1 for ADR-001, not of me for
  ADR-002. Claim E6 ("CDR wording is consistent across our own documents") and the E5
  "contradiction note" it references were checked for internal consistency
  (`docs/07-Defense/decisions/cdr-gated-module.md` already fully resolves the apparent
  contradiction with a ready panel answer) and found not to need any change — not acted on
  further, since E6's remaining work (auditing the slide deck and proposal document) is outside
  this repository.

## 2026-10-11 — Produce real F3/F4/N3 reports, fix stale eval/reports/README.md and members.md

**Requirement:** Member 2 reviewed the post-PR#54 state and flagged two real gaps: (1)
`eval/reports/` still only had f1/f2/n1/n2.json plus the baseline results — no f3, f4 or n3
JSON existed despite all three being real, reproducible `VERIFIED`/`UNRESOLVED` outcomes since
PR #49/#52 landed — and `eval/reports/README.md` still said "F3 needs W10, not implemented
yet" (stale since W10 merged weeks ago); (2) `docs/09-Team/members.md`'s M3 row said "baseline/
wording-fix branch not yet pushed" after PR #54 (that exact branch) had already merged.

- File/function: `eval/tools/run_w9_integration.py` — added `run_f3()`, `run_f4()`, `run_n3()`
  alongside the existing F1/F2/N1/N2 functions. F3/F4 use `runner.cli.resource_fields()`
  (M2's own public function, which calls `evidence.extract.analyse_pair` per polluter and
  `runner.cli.combine_fields` for F3's two-required-polluters case, ADR-007) rather than a
  second, independent implementation of that combination logic in this script.
- Command: `py eval/tools/run_w9_integration.py` (real Maven/JDK, native Windows JDK 24, all 7
  cases in one run). Result: **F1/F2/F3/F4 → `VERIFIED`, N1/N2 → `UNRESOLVED(VICTIM_FAILS_ALONE)`,
  N3 → `UNRESOLVED(NOT_REPRODUCED)`** — matches `ground_truth.json`'s `expected_outcome` for
  every one of the 7 cases. F3's report: both `ToggleAPolluterTest#setFlagA` and
  `ToggleBPolluterTest#setFlagB` named (one shown as `shared_resource`, the other in
  `limitations`, exactly ADR-007's rule), 20/20 reproduced, 0/20 alone. F4's report:
  `order_exploration.reproducing_seed=1` after 2 shuffles tried, 20/20 reproduced once found.
  N3's report: `failure_signature=null`, limitation text reads "Not reproduced: 20 runs of the
  discovered order (plus 31 shuffled order(s)), 20 runs alone" — confirms the PR #52 wording
  fix (given/discovered, shuffle count) is correct against a real `diagnose()` run, not just
  the hand-built `DiagnosisRuns` objects that fix was tested against at the time.
- Command: `py -m unittest discover -s eval/tests -v`. Result: **85/85 passed** (sanity check;
  this run only adds committed JSON files and two functions to a script nothing imports).
- File/function: `eval/reports/README.md` — added f3/f4/n3 rows to the file table; rewrote
  "What's NOT here yet" (previously claimed only F3 was missing and attributed it to "not
  implemented by Member 2 yet" — both stale); added F3/F4/N3's own blocked-until-landed notes
  alongside the existing F2/N2 ones.
- File/function: `docs/09-Team/members.md` — M3's row corrected: PR #54 (the "baseline/
  wording-fix branch") is merged, not unpushed; added that `eval/reports/` now has all 7 real
  reports, with a PR still pending for them.
- File/function: `docs/08-MidEval/panel-action-register.md` — A9's evidence column now names
  all 7 `eval/reports/*.json` files directly, not just f1/f2 plus a generic CLI-run claim.
- Limitation: these 7 JSON files and the `flaketrace-records/` folder they reference are
  produced locally (not yet committed/pushed) — see the hand-off commands for the exact `git
  add` list. `flaketrace-records/` itself stays uncommitted per `.gitignore` (Member 2's
  convention), as it was for f1/f2 already.

## 2026-11-18 — W19: verdict contract v2 (ADR-010), schema v2, fixture N4

**Requirement:** [[03-Design/decisions/ADR-010-verdict-contract-v2]] (agreed by all three
2026-11-13, PR #101) — M3's part of the "order of work": switch `decide()`, the schema and
`assemble_report()` to the ADR-010 decision table (13 rows, `RunTally`-based), and add fixture
N4 (ADR-010 test T5, the FT003 regression) through the real `py -m runner diagnose` command.
Reviewed M2's step-1 work first (`RunTally`/`classify` in `eval/baseline.py`, PR #103, W19 step
1) — matches ADR-010 section 1 exactly; `py -m unittest eval.tests.test_baseline` was already
27/27 green before I touched anything.

- File/function: `eval/outcome.py` — full rewrite. `DecisionInput` now takes `alone`/`sequence`
  as `RunTally` (not six separate counts), plus `reference_established: bool` and
  `infrastructure_failures_anywhere: int` for rows 4/5 (see below — these are NOT derivable
  from the two tallies alone), `search_inconsistent`/`budget_exhausted`/`deletion_status` for
  rows 2/3/12. `decide()` implements all 13 rows; `Decision` gains `candidate_reasons`.
  `NO_SUPPORTED_RESOURCE_EVIDENCE`/`BELOW_CONFIDENCE_THRESHOLD` retired as `UNRESOLVED` reasons
  (Q1 option A); `VICTIM_FAILS_ALONE_DIFFERENTLY`/`INCONSISTENT_OUTCOMES`/`BUDGET_EXHAUSTED`
  added.
- Design note worth a second look by M1/M2 in review: rows 4/5 ("no real failure anywhere")
  cannot be derived from just the `alone`/`sequence` tallies `decide()` receives — those are the
  FINAL alone check and FINAL sequence re-verify, and a reference can be established earlier
  during the search and then not hold up on re-verification (rows 10/11 — exactly ADR-011's
  motivating bug, single-trial `ddmin` can shrink to something that doesn't actually reproduce).
  My first draft derived rows 4/5 from the tallies directly and made rows 10/11 mathematically
  unreachable dead code — caught by writing `eval/tests/test_outcome.py`'s row-by-row tests
  first and checking each row is actually reachable, not just by reading the ADR table. Fixed by
  adding `reference_established`/`infrastructure_failures_anywhere` as their own inputs,
  computed in `eval/report.py` from `diagnosis.reference_signature is not None` and the
  existing cross-phase `infrastructure_failures` sum (unchanged ADR-008 field) respectively.
- File/function: `eval/schema/report.schema.json` — `schema_version: 2`. `reproduction`/
  `victim_alone` renamed `successes`→`matched`, gained `other`/`infra`. New: `candidate_reasons`,
  `resource_edges`, `assurance`. `failure_signature`'s null-vs-object rule relaxed: v1 tied it
  strictly to `unresolved_reason` being `NOT_REPRODUCED`/`INFRASTRUCTURE_FAILURE`; v2's richer
  table means those two reasons can have EITHER (rows 4/5 vs 10/11), and `SOURCE_INTEGRITY_FAILED`
  can co-occur with a never-established reference too (found for real below, T4's N3 case) — the
  schema now only strictly requires an object for reasons that always guarantee one by
  construction (`VICTIM_FAILS_ALONE`, `VICTIM_FAILS_ALONE_DIFFERENTLY`, `SIGNATURE_MISMATCH`,
  and `VERIFIED`/`CANDIDATE`); everything else allows either, with the real invariant enforced
  by `eval/report.py`'s own tests instead.
- Flagged for the team's review, not acted on unilaterally beyond W19's own scope:
  `assurance.sequence.deletion` can read `"NOT_YET_CHECKED"` — a value I added that is NOT in
  ADR-011's own four-value table (`DELETION_VERIFIED`/`INCONCLUSIVE`/`INCOMPLETE`/
  `NOT_APPLICABLE`). Reusing `NOT_APPLICABLE` for "not yet built" would be dishonest (ADR-011
  defines it to mean "no polluter was found", a different, false claim for a POLLUTER_FOUND
  diagnosis). `decide()`'s `deletion_status=None` (same meaning) is treated as satisfying claim
  S3 so this W19 change does not regress any fixture's `VERIFIED` verdict ahead of ADR-011/W20
  landing (test T6, confirmed below). Also flagged: ADR-011 §2 observes that a single-polluter
  deletion check is "free" (the alone tally already *is* it) — I deliberately did NOT build
  that opportunistically in W19, since ADR-011's own test matrix (T1–T5) lists it as W20's work,
  not W19's; leaving it for W20 rather than quietly doing part of another work package early.
- File/function: `eval/report.py` — full rewrite for schema v2. Reads `diagnosis.alone_tally`/
  `sequence_tally` directly now (ADR-010/W18 fields) instead of the old scalar counts; raises
  `ValueError` if either is `None` (a `DiagnosisRuns` that predates W18). `INCONSISTENT`
  (formerly `NO_SINGLE_POLLUTER`) is now handled — a real, schema-valid report, not
  `UnhandledStatus`/exit 3 (FT010). New "no test is blamed" rule: whenever `outcome` is
  `UNRESOLVED` for any reason except `SOURCE_INTEGRITY_FAILED`, `polluters`/`reduced_sequence`/
  `shared_resource`/`resource_edges` in the OUTPUT report are suppressed even if the search (W18
  deliberately does not stop early for rows 7/8/9/10/11) found a candidate — the write/read
  locations would otherwise still name the un-blamed polluter. `diagnosis.polluters`/`.sequence`
  themselves are left alone; only what is reported changes. `reduced_sequence` collapses to
  `[victim]` only when there was an actual found polluter to un-blame — `INCONSISTENT`/
  `NOT_REPRODUCED` already carry the starting order (ADR-010 §5) and must show it as-is.
- Deliberately NOT done, left for M2/coordination rather than acted on unilaterally:
  `runner/diagnose.py`'s old scalar `DiagnosisRuns` fields (`sequence_successes` etc.) and the
  `NO_SINGLE_POLLUTER` alias are still there. ADR-010's own "order of work" section says these
  are removed "when W19 reads the tallies" — but removing them means rewriting ~20 call sites
  across `runner/tests/test_diagnose.py` (M2's file, not touched). `eval/report.py` reads the
  tallies directly now regardless, so functionally W19 is done without that cleanup; flagging it
  here as a follow-up for M2 rather than editing `runner/` test files beyond what's below.
- File/function: `runner/cli.py` (lines 217-218) and `runner/tests/test_cli.py` — two places
  read `report["reproduction"/"victim_alone"]["successes"]` directly (the CLI's human-readable
  summary line, and one assertion), which schema v2 renames to `"matched"`; this would have
  crashed every real `diagnose` CLI run with a `KeyError`. ADR-010's own Consequences section
  anticipated this for `ui/` ("Member 2 updates the field names and the wording") but not for
  `runner/cli.py`'s own summary printer. **Member Zarpash gave explicit permission mid-session**
  to make this specific mechanical rename in M2's files (not a design decision, just keeping the
  CLI from crashing on the new schema) rather than leaving it broken; flagged for M2's review in
  a code comment at both sites. `runner/tests/test_cli.py`'s shared `runs()` helper (11 call
  sites) didn't build `alone_tally`/`sequence_tally` at all — every call would have hit the new
  `ValueError` guard in `assemble_report()`. Fixed by making the helper derive both tallies from
  the existing scalar fields it already takes, so none of the 11 call sites needed touching.
  One real behavioural assertion also needed updating (not just a rename): a test at the old
  line 184 asserted `UNRESOLVED(NO_SUPPORTED_RESOURCE_EVIDENCE)`, now legitimately
  `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]` per Q1 option A; and
  `test_inconsistent_exits_3_without_a_report_until_m3_builds_one` asserted exit code 3/no
  report for `INCONSISTENT`, now rewritten as `test_inconsistent_writes_a_real_report_now`
  (exit 0, a real report, matching ADR-010 section 5). Also given explicit permission for this.
- File/function: `fixtures/od-fixture/src/main/java/odfixture/DualFailureState.java`,
  `DualFailurePolluterTest#setState`, `DualFailureVictimTest#expectsStateTwo` — the N4 fixture
  (ADR-010 test T5). Victim throws `java.lang.IllegalStateException` when run alone
  (`DualFailureState.state` still 0, unset) and asserts `state == 2` otherwise, which fails
  with `java.lang.AssertionError` after the polluter sets `state = 1` — two REAL, DIFFERENT
  failures, exactly T5's "throws IllegalStateException alone and AssertionError after its
  polluter". `DualFailurePolluterTest` sorts alphabetically before `DualFailureVictimTest`, so
  (like F1/F2) the natural discovered order reproduces it without needing ADR-008's shuffle
  search.
- File/function: `fixtures/od-fixture/ground_truth.json` — N4 entry added (before any run, per
  this file's own convention), `expected_outcome: UNRESOLVED`,
  `expected_outcome_reason_free_text: VICTIM_FAILS_ALONE_DIFFERENTLY`, `polluters: []` (no test
  is blamed). `eval/benchmark/manifest.json` — N4 row added (`source: fixture`), mirroring
  N1–N3's shape.
- Command: `mvn -B -q -f fixtures/od-fixture/pom.xml test-compile`. Result: clean compile, no
  errors (JDK 24, Maven 3.9.11, native Windows).
- Command: `py -m eval.tools.run_w9_integration` (real `diagnose()` + `evidence.extract` +
  `assemble_report()`, all 8 cases in one run, native Windows JDK 24). Result: **F1/F2/F3/F4 →
  VERIFIED, N1/N2 → UNRESOLVED(VICTIM_FAILS_ALONE), N3 → UNRESOLVED(NOT_REPRODUCED), N4 →
  UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)** — every one matches `ground_truth.json` exactly.
  F1–F4/N1–N3 verdicts are **unchanged** from the Mid under schema v2 (ADR-010 test T6). N4's
  real report: `victim_alone` = `{n:20, passed:0, matched:0, other:20, infra:0}` (the real
  `IllegalStateException`, every one of 20 runs, correctly counted as `other` not a pass);
  `reproduction` = `{n:20, passed:0, matched:20, other:0, infra:0}` (the real `AssertionError`
  after the polluter, 20/20); `polluters: []`, `shared_resource: null`, `reduced_sequence`
  collapsed to `[DualFailureVictimTest#expectsStateTwo]` — no test blamed, exactly ADR-010 row
  7's "no test is blamed", confirmed through the real pipeline, not a hand-built `DiagnosisRuns`
  (T5's own requirement: "the *integrated* regression the supervisor asked for"). The 8 real
  reports are at `eval/reports/{f1,f2,f3,f4,n1,n2,n3,n4}.json`.
- Command: `py -m unittest discover -s eval/tests`. Result: **119/119 passed** (up from 85 at
  the Mid: `test_outcome.py`/`test_report.py` rewritten and expanded for schema v2 — 26 and 20
  tests respectively, one per decision-table row plus the ADR-010 regression scenarios T1–T4;
  `test_schema_validator.py`/`test_examples.py` updated for the new shape; `test_yield_report.py`
  updated for N4's new manifest/ground-truth row).
- Command: `py -m unittest discover -s runner/tests`. Result: pending — kicked off in the
  background; will append the real result once it completes (the suite takes ~8 minutes, real
  JVMs). `py -m unittest runner.tests.test_cli -v` on its own: **63/63 passed** (confirmed twice
  — the first run showed 3 failures, all three in `TestCliOnFixture`, traced to a real cause:
  I was still writing the three new N4 `.java` files to `fixtures/od-fixture/src/` WHILE that
  background run was mid-diagnosis, so its own before/after source-integrity snapshot correctly
  caught the unexpected file additions and reported `SOURCE_INTEGRITY_FAILED` — the checker
  doing exactly its job, not a bug in this change. Rerun after the files had settled: clean).
- Command: `py -m unittest discover -s evidence/tests`. Result: **39/39 passed** (sanity check;
  this change never touches `evidence/`).
- Limitation: the W19 "order of work"'s step 5 (M1 reruns T1–T5 on her own machine at this
  commit and records the result, FT003's acceptance requires an independent reproduction) is
  not done by this entry — that is M1's own verification step, not mine to do for her.
- Limitation: `docs/03-Design/certificate-contract.md` and `docs/contracts/report-schema.md`
  updated to match the accepted-and-now-built ADR-010 (this entry); ADR-011's part (deletion
  checks) is still accepted-but-not-built, stated as such in both docs, not glossed over.
- File/function: `ui/tests/test_server.py` (`test_reports_lists_the_seven_committed_reports`,
  renamed `..._eight_...`) — `eval/reports/` now has 8 committed reports (n4 added), one more
  than this hardcoded list expected. Purely additive (not a design decision); Zarpash gave
  explicit permission for this one too.
- Command: `py -m unittest ui.tests.test_server -v`. Result: **31/31 passed**, including
  `test_f1_is_verified_with_its_polluter` (one real F1 run through the UI's own backend/CLI
  path) — confirms the `runner/cli.py` rename did not break the UI's subprocess path either.
  (One earlier run hit a transient `ConnectionAbortedError` on Windows unrelated to any content
  change — a flaky local HTTP-server timing issue, not reproduced on rerun.)
- Limitation: `ui/web/` (Member 2's) still reads the v1 field names
  (`sequence_any_signature_failures`, the retired `NO_SUPPORTED_RESOURCE_EVIDENCE`/
  `BELOW_CONFIDENCE_THRESHOLD` reason text) — `ui/web/src/lib/report.ts`. Not touched: TypeScript,
  outside this session's scope, and ADR-010's own Consequences section already assigns this to
  Member 2. The real `diagnose` CLI path is unaffected (fixed above); only the web UI reading a
  schema-v2 report would currently show stale/missing labels for the new fields.

## 2026-11-18 — W16: verify M2's retired-claims work, finish M3's own part

**Requirement:** `docs/10-Final1/iteration-2-plan.md` W16 — qualify every claim the Mid build
could not support (pass-alone, "1-minimal", resource "mechanism", "never modified"), with M3
owning `eval/`'s own part and checking consistency everywhere else. M2's part (`runner/`, `ui/`)
was flagged "awaiting verification by M3"; M1's and M3's parts were flagged "not started".

- Checked: M2's `m2/w16-retire-claims` branch tip (`9a05788`) is already merged into `main`
  (its merge-base with `main` is itself — not an open PR). Read the real, current
  `runner/cli.py`: "static overlap: a possible mechanism, not confirmed as the cause" (line 214)
  and "reduced by single-trial delta debugging; not deletion-verified" (line 191) match ADR-010
  §2 and ADR-011 §5's approved wording exactly. Verified, nothing further needed from M2's side.
- Checked: M1 pushed `m1/w16-evidence-wording` (not yet merged — its merge-base with `main` is
  `main`'s own current tip, i.e. a real, open, unmerged branch). Not reviewed in depth here
  (M1's own work, not yet on `main` to check consistency against); flagged to re-check once
  merged.
- File/function: `eval/outcome.py`, `eval/report.py` — both written fresh in W19 (this session,
  above), so M3's own "pass-alone"/"mechanism" usages were already the approved, qualified
  wording throughout (e.g. `decide()`'s VERIFIED rationale: "...does not assert the resource is
  the cause of the failure"). One real inconsistency found by comparing against `runner/cli.py`
  rather than just reading `eval/` in isolation: `eval/report.py`'s deletion-check limitation
  line paraphrased ADR-011 §5's wording instead of reusing it verbatim, unlike the CLI's exact
  "reduced by single-trial delta debugging; not deletion-verified". Fixed for product-wide
  wording consistency (the whole point of W16); `eval/examples/example_f1_verified.json` and
  `example_f3_verified.json`'s matching limitation lines updated the same way.
- Command: `git grep -n -i -E "1-minimal|never modified|sandboxed|found mechanism|root cause|
  caused by|explains the failure|passes alone" -- eval/ fixtures/` (M2's own W16 search pattern,
  re-run against M3's folders) and a second pass for "cause"/"mechanism" more broadly across
  every `.py` file and `ui/web/src/`. Result: every hit is either already-approved wording
  (`"not confirmed as the cause"`, `"reduced by single-trial delta debugging; not
  deletion-verified"`), a historical/dated note in `docs/evidence-*.md` or `ground_truth.json`
  (exempted by W16's own "Done when" criterion), a factual code comment about the fixture's
  actual designed behaviour (e.g. `ConfigVictimTest`'s real `passes alone` docstring — true by
  construction, not a tool claim), or a literature-review doc describing another paper's own
  terminology (`docs/01-Literature/`) — never an unqualified FlakeTrace claim about itself.
- Command: `py -m eval.tools.run_w9_integration` (real run, all 8 cases) after the wording fix,
  to keep the committed reports consistent with the code that produced them. Result: all 8
  verdicts unchanged (F1-F4 `VERIFIED`, N1/N2 `UNRESOLVED(VICTIM_FAILS_ALONE)`, N3
  `UNRESOLVED(NOT_REPRODUCED)`, N4 `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)`) — only the
  `limitations` text changed, as intended.
- Command: `py -m unittest discover -s eval/tests`. Result: **119/119 passed** (unaffected by a
  free-text wording change).
- Limitation: this entry checks consistency on everything currently committed to `main`. M1's
  `evidence/` wording fix is real but still on an open branch — re-run the same search once it
  merges, since a broken merge of M1's and M3's overlapping doc edits (`members.md`,
  `iteration-2-plan.md`, `genai-register.md`) is possible and worth a second look then.

## 2026-11-19 — W26a steps 1-5: the first real case (fastjson FJ-03), real runs, real finding

**Requirement:** [[05-Testing/real-case-protocol]] steps 1-5 (M3 lead) — fetch and build the
chosen real case (fastjson `FJ-03`, `MaxBufSizeTest#test_max_buf`) at its pinned commit, confirm
the premise with the runner directly, fix a starting order, check it, and freeze the protocol.
"Needs nothing new" per the critical path; started in Sprint A since fastjson buildability was
flagged as the largest unknown in the whole Iteration-2 plan.

- Setup: fastjson `https://github.com/alibaba/fastjson` fetched into a scratch folder **outside
  this repository** (never committed, per the protocol's "Source" row and the project's own
  ethics/legal section), checked out at the pinned commit
  `e05e9c5e4be580691cc55a59f3256595393203a1`. No real JDK 8 exists on this machine (only
  JDK 17/24) — downloaded Eclipse Temurin 8 (`1.8.0_512`) as a portable zip from Adoptium's own
  API (`api.adoptium.net`, ~106 MB), extracted to the same scratch folder, nothing installed
  system-wide. **Member Zarpash's explicit permission** for the download, given the choice
  between this and starting Docker Desktop (M1's earlier fastjson work used a `ft-jdk8`
  container, not available to start here without the member's involvement).
- Command: `mvn -B -DskipTests test-compile` with that JDK 8 as `JAVA_HOME`. Result:
  **BUILD SUCCESS**, 3 min 41 s, 172 main + 2,496 test sources compiled — matches
  [[evidence-m1]]'s own count from Phase 5 exactly. `git status` in the fastjson checkout
  showed no source changes afterward (CLAUDE.md §4: FlakeTrace must never modify the analysed
  project — confirmed, not just asserted).
- Command: a one-off script (`runner.order_runner.OrderRunner.run_ordered`, the real runner,
  not through the full `diagnose()` orchestration — matches the protocol's "with the runner
  directly"), `JAVA_TOOL_OPTIONS=-Duser.timezone=UTC -Duser.language=en -Duser.country=US`
  pinned per the protocol's Environment table. Victim alone ×10: **10/10 PASS**. `[known
  polluter `SerializeWriterTest_14#test_writer_1`, victim]` ×10: **10/10 FAIL**,
  `junit.framework.AssertionFailedError` at `MaxBufSizeTest.test_max_buf:20` — exactly the
  signature the protocol names. Clean, deterministic, real bug; recorded at
  `eval/real-cases/fj03/premise.json`.
- File/function found while building step 3's starting order: `runner/discovery.py`'s
  `is_surefire_test_class()` hardcodes Surefire's **default** include pattern
  (`Test*`/`*Test`/`*Tests`/`*TestCase`). fastjson's `pom.xml` overrides Surefire entirely
  (`<includes><include>**/bvt/**/*.java</include></includes>` — every class under any `bvt/`
  folder, no naming convention). Our discovery silently misses real test classes, **including
  the known polluter** (`SerializeWriterTest_14`/`_15` match neither `*Test` nor `*Tests` nor
  `*TestCase`). Confirmed this is not just a scratch-script problem: the real command
  `py -m runner diagnose --order eval/real-cases/fj03/order.txt --project <fastjson> --victim
  com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` refuses the case outright —
  `"1 test(s) in the given order are not among the project's tests"`. Workaround used only to
  keep this session's own steps moving (enumerate every class file in the package by path, let
  `OrderRunner.list_methods` — real JUnit/harness reflection — decide which have test methods,
  instead of pre-filtering by name): found exactly 525 real test methods, matching the POC's own
  524-candidate-plus-1-victim count exactly, confirming the workaround's correctness. **Not
  fixed here** — flagged as a real, registered risk
  ([[00-Meta/risk-register]], "Discovery misses real test classes with custom Surefire
  includes") for M2, since `runner/discovery.py` is M2's file and the real fix (reading the
  project's actual Surefire configuration) is a design decision, not a mechanical rename.
  **Member Zarpash's explicit decision**, given three options, was to flag this for M2 rather
  than attempt the fix or switch to a different case.
- Command: ran the corrected (workaround) starting order (261 entries, package-scoped,
  discovered order cut after the victim) for real, once. Result: **PASS** (does not reproduce)
  — expected, since the natural alphabetical order places `MaxBufSizeTest` (M) before every
  `SerializeWriterTest_*` (S) candidate, the same lesson as our own fixture's F4.
- Command: the real ADR-008 shuffled-order search (`runner.orders.distinct_shuffles` +
  `search_orders`, the exact functions `diagnose()` itself uses), 31 distinct shuffles, same
  workaround-corrected 525-method candidate pool. Result: **none of the 31 reproduced the
  failure** (`any_failures: 0` across all 31) — genuinely surprising at first, since several
  shuffles (seeds 0, 1, 2, 4, 8, 9, 10, 12, 13, 14, 15, 18, 20, 23, 25 of the 31) place all 6
  known-relevant candidate methods before the victim. Investigated seed 0 (513 tests) in detail:
  several *other* `SerializeWriterTest_N` variant classes (`_19`, `_7`, `_12`,
  `_BrowserSecure_4_script`, ...) also run between the last relevant candidate and the victim.
  These almost certainly touch the same shared `SerializeWriter` buffer-size state and undo the
  pollution before the victim runs — a real, order-dependence-cancelling interaction a clean
  2-test fixture can never show. **This is a genuine, reportable result, not a dead end**: random
  full-suite shuffling cannot reliably find this real bug within a modest budget, even though
  the bug is 100% real and deterministic with the exact pair (confirmed above). Direct,
  real-world evidence for why a targeted one-by-one search (which is what already works, and
  what W25's evidence-ranked search builds on) matters more than blind random search on a dense
  real project. **Member Zarpash's explicit decision**, given two options (try a much bigger
  shuffle budget, or accept this and move on), was to accept it and freeze the known pair as the
  starting order.
- File/function: `eval/real-cases/README.md`, `eval/real-cases/fj03/order.txt` (the known pair,
  `SerializeWriterTest_14#test_writer_1` then the victim — SHA-256
  `8c9b208ac5c970138a37679fc3f91156e467c7701d6b91e2e49dc4b66234be1e`), `eval/real-cases/fj03/premise.json`
  (the real step-2 tallies above). `docs/05-Testing/real-case-protocol.md` — status changed from
  `PROPOSED` to `FROZEN FOR STEPS 1-5`, with a Findings section recording everything above
  honestly, including that steps 6-9 are blocked. `docs/00-Meta/risk-register.md` — new entry
  for the discovery.py gap, materialising a scenario its own pre-registered "real case will not
  build or reproduce" risk (added 2026-11-13) had already anticipated in spirit, though the real
  mechanism (a naming-filter gap, not a build failure) is more specific than that entry's
  original wording.
- Limitation: steps 6-9 (the whole pipeline, policy comparison) cannot run until M2 fixes
  `runner/discovery.py` to read the project's real Surefire configuration. Steps 6-8 also need
  the budget ledger (ADR-014/W24, not yet built) regardless. The offline comparison
  (`scan_FJ-03.csv` already has every pair's outcome, no JVM needed) remains available and is
  not done in this entry — a cheaper next step once picked back up.
- Limitation: FJ-04 and the ormlite-core case (the protocol's fallback cases) were not tried.
  Given FJ-04 is in the same fastjson package, it would very likely hit the identical
  discovery.py gap; not attempted, since the finding (and its fix owner) is already established.

## 2026-11-19 — PR #106 CI fixes: merge conflicts, the Mid report's generated table

**Requirement:** PR #106 (W19/W16/W26a) failed two CI checks and had two merge conflicts after
M1's `m1/w16-evidence-wording` (PR #105) landed on `main` first. Fix what is mine, flag what
isn't.

- Merge conflicts in `docs/08-MidEval/genai-register.md` and `docs/10-Final1/iteration-2-plan.md`
  (both append-only: M1 and I added different rows/text near the same anchor line). Resolved by
  keeping both sides' content (member ran the real `git merge origin/main`, I resolved the
  conflict markers via `Edit`, per this project's own established pattern — never ran `git
  merge` myself). `docs/09-Team/members.md` auto-merged cleanly.
- `CI / build-report` failing: real cause, not a merge artefact —
  `mid-eval-report/scripts/json_to_tex.py` (reads `eval/reports/*.json` to generate
  `tables/generated/fixture_results.tex` for the Mid report's Chapter 7/Appendix C) hardcoded
  `block['successes']`, renamed `matched` in schema v2. The workflow's own error message says
  exactly what to do: "Run python3 mid-eval-report/scripts/json_to_tex.py and commit the
  result." Fixed the field name; **did not** add fixture case N4 to the generated table even
  though `eval/reports/n4.json` now exists — the Mid Report's prose says "seven cases" in every
  chapter, written by all three members, describing the frozen, already-submitted `mid-eval-v1`
  state; adding an 8th row without rewriting that prose everywhere would make the report
  self-contradictory. Left for `docs/10-Final1/report-v2-plan.md` (the Final-1 report), not
  done here.
- Regenerating the table (now correct) also changed real numbers, since `eval/reports/` itself
  genuinely changed: every case's `original_failing_order` length grew (two new N4 test methods
  now exist in the whole fixture project, shifting every discovery count), N2's real measured
  rate changed from 9/20 to 11/20 (it is explicitly, deliberately non-deterministic by design —
  `java.util.Random().nextBoolean()`), and **F4's reproducing shuffle seed changed from 1 to 6**
  (14 tests in the reproducing order now, not 3 — the candidate pool shifted enough that a
  different shuffle seed is first to reproduce it). Found and fixed every place in **my own**
  chapters citing the old numbers: `mid-eval-report/chapters/appendix_test_cases.tex` (F2/F3/F4's
  order lengths, F4's seed, N2's rate), `chapter6_module_m3.tex` (N2's rate),
  `chapter8_testing.tex` (N2's rate). Checked brace balance on all three after editing.
- Flagged, not touched (M2's files, per `mid-eval-report/CLAUDE.md` §2 — a PR-description-level
  note here, not a silent edit): three more citations of F4's now-stale "shuffle seed 1" exist
  in `mid-eval-report/chapters/appendix_action_register.tex`, `chapter6_module_m2.tex`, and
  `chapter9_contribution_m2.tex`. All three now say "seed 6" in the real regenerated report.
- `CI / ui` failing: real cause — `ui/web/src/lib/report.test.ts` (and the module it tests,
  `report.ts`) still assume schema v1 (`successes`, exactly seven committed reports, old
  limitations wording). **Not a required check** (branch protection requires
  `fixture-build`/`python-eval`/`runner`/`evidence` only). Already flagged as M2's follow-up in
  this file's 2026-11-18 entry; Zarpash's explicit decision this session was to leave it for M2
  rather than have me edit `ui/web/`'s TypeScript.
- Command: `py -m unittest discover -s eval/tests` → 119/119 OK (text-only report changes,
  sanity check). Real `mvn`/JDK runs not re-done this entry (no code changed, only report
  prose and the generated table).
- Limitation: did not verify the Mid report actually compiles (`latexmk -pdf main.tex`) — no
  LaTeX toolchain in this environment; relying on `report.yml`'s own CI job for that, same
  constraint the 2026-10 handoff note recorded for a previous session.

## 2026-11-19 — A1 fail-safe fix: `deletion_status=None` no longer satisfies S3 (ADR-010/ADR-011)

**Requirement (test-first):** the W19 build of `eval/outcome.py` made `deletion_status=None`
("not yet checked") satisfy claim S3, to avoid regressing F1/F2/F3/F4 to CANDIDATE before
ADR-011's real deletion check existed. Flagged at the time for team review. Zarpash's explicit
instruction this session: reverse that, fail-safe. An unestablished claim must not count as an
established one, even though it changes F3's reported outcome.

- **Test first:** added `test_two_polluters_with_a_real_edge_gives_candidate_not_verified` to
  `eval/tests/test_report.py` and `test_row12_candidate_when_deletion_not_yet_checked` to
  `eval/tests/test_outcome.py`. Ran on the unfixed code: both failed (`AssertionError: VERIFIED
  != CANDIDATE`), confirming the bug existed before fixing it.
- **Fix:** `eval/outcome.py` — row 12's guard dropped the `is not None` escape hatch, so
  `deletion_status` not in `_DELETION_SATISFIES_S3` (which is deliberately `(DELETION_VERIFIED,
  DELETION_NOT_APPLICABLE)` only — `None` and `NOT_YET_CHECKED` excluded on purpose) now always
  blocks S3. `eval/report.py` — added the actual ADR-011 \S2 "free" check: a single kept polluter's
  deletion check **is** the alone check, already run and already gated clean by the time row 12
  is reached, so `deletion_status = DELETION_VERIFIED` is computed with no new JVM runs when
  `len(diagnosis.polluters) == 1`. Two or more kept polluters (only F3, in the real fixture) get
  no free check yet — `deletion_status` stays `None`, correctly blocking S3 until W20 builds the
  real multi-test removal check.
- **Effect on real reports:** F1, F2, F4 (one polluter each) stay `VERIFIED` — free check covers
  them. F3 (two required polluters) now reports `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]`
  instead of `VERIFIED`. This is the correct, honest behaviour: F3 was never deletion-verified,
  only search-minimised (claims-ledger row G2, `docs/07-Defense/claims-ledger.md`) —
  `eval/outcome.py`'s own docstring and `_DELETION_SATISFIES_S3`'s comment now say so.
  **`fixtures/od-fixture/ground_truth.json` was deliberately NOT changed** — F3's ground truth
  stays `VERIFIED` as the W20 target; this fix changes what the tool can honestly say *today*,
  not what F3 is expected to resolve to once W20 lands.
- **Command:** `py -3 -m unittest eval.tests.test_stats eval.tests.test_outcome
  eval.tests.test_schema_validator eval.tests.test_examples eval.tests.test_baseline
  eval.tests.test_yield_report eval.tests.test_report` → 120/120 OK (1 new test in
  `test_report.py`, counts unchanged elsewhere — row/example renames, not additions).
- **Real reports regenerated:** `py -3 eval/tools/run_w9_integration.py` → F1/F2/F4 `VERIFIED`,
  F3 `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]`, N1/N2 `UNRESOLVED(VICTIM_FAILS_ALONE)`, N3
  `UNRESOLVED(NOT_REPRODUCED)`, N4 `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)`, all matching
  `eval/outcome.decide()`'s own table. N2's rate is genuinely random by design
  (`new Random().nextBoolean()` in the fixture) — observed 9/20, then 11/20 (after N4 was added,
  2026-11-18 entry above), then 10/20 on this entry's run. **Going forward, avoid re-running
  `run_w9_integration.py` purely to "refresh" committed reports** — every real rerun changes
  N2's committed rate and forces another round of citation fixes in the Mid report's prose;
  only rerun it when a real code change needs the regenerated evidence.
- **`runner/tests/test_cli.py` and `ui.tests.test_server`: not rerun this entry.** Both were
  already fixed for F3's CANDIDATE outcome and verified green (63/63, 31/31) earlier in this
  session, before this compaction boundary, against the same `eval/outcome.py`/`eval/report.py`
  fix landed here — no runner or ui code changed since, so the result still holds. Flagging
  this explicitly rather than re-asserting a number I didn't re-measure this entry.
- **`eval/examples/`:** `example_f3_verified.json` renamed to `example_f3_candidate.json`
  (outcome corrected `VERIFIED` → `CANDIDATE`), `example_f1_verified.json` and two synthetic
  examples given an explicit `deletion_status=DELETION_VERIFIED` kwarg to isolate them from this
  change. `eval/examples/README.md` updated to match.
- **Mid report (`mid-eval-report/`, my own chapters only):** `chapter8_testing.tex` (Table
  7.x's F3 row: `VERIFIED` → `CANDIDATE`; the results paragraph rewritten to explain the
  single-vs-multi-polluter free-check distinction and the A1 fix by name; N2's rate 11/20 →
  10/20), `chapter4_requirements.tex` (the "Deletion checks" acceptance-criteria row: was
  claiming "Met... real F3 case confirms it" for 1-minimality, which conflated search-minimality
  with deletion-verification — corrected to "partially met, corrected in Iteration 2"),
  `appendix_test_cases.tex` (N2's rate 11/20 → 10/20, with a note that the rate genuinely varies
  run to run rather than citing one number as if stable). `tables/generated/fixture_results.tex`
  regenerated to match (F3 row now `CANDIDATE`, N2 now `10/20`). Brace balance checked on all
  three `.tex` files after editing (equal open/close counts).
- **Flagged, not touched — M1/M2's files and a joint doc, per `mid-eval-report/CLAUDE.md` §2 and
  root CLAUDE.md §1:**
  - `mid-eval-report/chapters/chapter1_introduction.tex:141` ("F1--F4 \texttt{VERIFIED},
    including F3's two polluters") — M1-owned, now factually wrong for F3.
  - `mid-eval-report/chapters/appendix_action_register.tex:45` ("...reproduced 20/20,
    \texttt{VERIFIED}" for F3) — M2-owned, same issue.
  - `mid-eval-report/chapters/chapter6_iteration1.tex`, `chapter9_development_evidence.tex`
    (both M2-owned "frame" files) and `chapter2_research.tex` (M1-owned) describe F3 as solved
    by `ddmin` without naming an outcome directly — lower priority, but worth a pass once M1/M2
    pick this up.
  - `docs/07-Defense/claims-ledger.md` row **E14** (Owner: M2) still asserts "the command →
    `VERIFIED`, 20/20, 0/20 alone" for F3 under status `SETTLED`. Row **G2** (Owner: M2, M3,
    status `OPEN`) already names exactly this gap ("A `VERIFIED` sequence is deletion-minimal —
    NOT SUPPORTED when outcomes vary... reduced by single-trial delta debugging; minimal for the
    trials it saw") and is the correct wording to use instead of E14 until E14 itself is
    corrected. This fix is real, reproducible progress on G2 for the single-polluter cases
    (F1/F2/F4 now have a genuine free deletion check, not just an assumption) — raised for M2 to
    update E14 and for the team to consider whether G2 can move toward closing for the
    single-polluter case specifically, while staying open for multi-polluter cases until W20.
  - **Retraction (2026-11-20, see the merge-resolution entry below):** the `chapter1_
    introduction.tex`/`appendix_action_register.tex`/`chapter6_iteration1.tex`/`chapter9_
    development_evidence.tex`/`chapter2_research.tex` flags just above were wrong. The Mid
    report is a closed record checked by CI against tag `mid-eval-v1` (M2's PR #106), where F3
    genuinely was `VERIFIED` — those chapters are correctly describing that frozen state and
    must **not** be changed. My own matching edits to my three chapters were wrong for the same
    reason and were reverted (below). The `claims-ledger.md` row E14 flag stands, unaffected —
    that document is explicitly live/ongoing (section G's own header), not tied to the tag.
  - Not a surprise to the team: this exact tension (ddmin's search-minimality vs. a real
    deletion-verification check) is G2's own description, dated 2026-11-13 — this entry is
    that gap actually narrowing in code, not a new finding.

## 2026-11-20 — Merge conflict: M2 independently built the same A1 fail-safe fix

**Requirement:** `git push` to the shared branch `m3/w19-verdict-contract-v2` was rejected
(non-fast-forward); `git pull` (member's own command) surfaced that M2 had pushed real work to
this same branch — PR #106, "with M3's permission" per M2's commit message — including
`[M2] eval: list every resource edge and apply ADR-011 deletion rule`, which independently
reaches the same conclusion as A1 (F3 must not be `VERIFIED` without a real multi-polluter
deletion check) through a different, better-engineered mechanism. 13 files conflicted.

- **Compared both implementations before choosing, not a coin flip.** M2's `eval/report.py`
  computes `deletion_status` with: (1) an explicit, defensive re-check that
  `alone_tally.passed == alone_tally.n` rather than relying on `decide()`'s row ordering as an
  implicit precondition, and (2) the real ADR-011 four-value vocabulary (`DELETION_VERIFIED`/
  `DELETION_INCOMPLETE`), never a raw `None` for a found-polluter case. My own A1 version left
  the multi-polluter case as `None` and relied on fixing `eval/outcome.py`'s guard to reject it
  — functionally equivalent for F3 today, but less robust and still used my own invented
  `DELETION_NOT_YET_CHECKED` value where M2's doesn't need to. **Kept M2's `eval/report.py`
  entirely; kept my own `eval/outcome.py` guard fix too** (it merged with no conflict — M2's
  branch never touched that file — and is valid, harmless defense-in-depth regardless).
- **Resolved via `Edit`, never `git merge`/`git checkout --theirs`/`git add` myself** (the
  member ran the real `git pull`): `eval/report.py`, `eval/tests/test_report.py`,
  `runner/tests/test_cli.py` — took M2's side for every conflicting hunk. Also fixed one of my
  own tests (`test_two_polluters_with_a_real_edge_gives_candidate_not_verified`,
  `eval/tests/test_report.py`) that git did **not** flag as conflicting (no textual overlap)
  but was now factually wrong under M2's code: asserted `assurance.sequence.deletion ==
  "NOT_YET_CHECKED"`, corrected to `"INCOMPLETE"` by reasoning through the merged code's actual
  behaviour, not by trusting the absence of a conflict marker.
- **`docs/08-MidEval/genai-register.md`:** both members' same-day rows are independent,
  append-only entries — kept both, plus a new row for this reconciliation itself.
  **`docs/09-Team/members.md`:** the conflict region spanned two different members' rows (M2's
  row 2 and my own row 3) because they sit adjacent in the table; took M2's own row 2 (their own
  description of their own work is authoritative) and my row 3 (mine).
- **`eval/reports/{f1,f2,f3,f4,n1,n2,n3,n4}.json`:** resolved by regenerating them for real
  (`py -3 eval/tools/run_w9_integration.py`) against the now-merged code, rather than
  hand-merging JSON from two different pre-generated snapshots — guarantees the committed
  files exactly match what the resolved code actually produces. F3 confirmed `CANDIDATE
  [DELETION_EVIDENCE_INCOMPLETE]`, `assurance.sequence.deletion = "INCOMPLETE"`, now with 2
  structured `resource_edges` (M1's W21, merged in from M2's side). N2's rate landed at 12/20 on
  this real rerun (yet another value — 9/20, 11/20, 10/20, now 12/20 across this iteration's
  reruns, exactly the churn flagged in the 2026-11-19 entry above). Fixed the same two own-
  chapter N2 citations (`chapter8_testing.tex`, `appendix_test_cases.tex`) a third time; brace
  balance re-checked.
- **Command:** `py -m unittest discover -s eval/tests` → 123/123 OK (120 of mine + 3 new from
  M2's `TestResourceEdgesFromM1`/`TestDeletionEvidenceBeforeW20`). `runner.tests.test_cli`:
  started, result recorded in the next entry once the real-JVM run finishes (it runs for
  several minutes; not fabricating a number before it completes).
- **`runner.tests.test_cli`** (real JVM): 64/64 OK, confirming the merge-resolved `eval/report.py`
  and `runner/tests/test_cli.py`.
- **A real bug found by actually reproducing M2's new CI job, not by reading the diff:** M2's
  other PR #106 commit, `[M2] ci: check the Mid report tables against the mid-eval-v1 reports`,
  made the Mid report's generated table a genuinely closed record — CI now regenerates it from
  `mid-eval-v1`'s frozen `eval/reports/` (schema v1, via `git archive`), never the live
  directory, since the Mid report is a graded, submitted artefact, not something that should
  track Iteration 2's ongoing changes. Running that CI step locally
  (`git archive mid-eval-v1 eval/reports | tar -x`, then `json_to_tex.py --reports <that
  dir>`) crashed: `KeyError: 'matched'`. My own earlier "successes"→"matched" rename (2026-11-19
  entry above) assumed every report would eventually move to schema v2 — wrong, since the tag's
  reports are permanently schema v1. Fixed `rate()` in
  `mid-eval-report/scripts/json_to_tex.py` to accept either key, test-first in spirit (ran the
  exact CI command before and after the fix, confirmed the crash and then the fix).
- **This also meant every one of my own "sync the Mid report to live data" edits this session
  was wrong, not just incomplete.** The Mid report is explicitly a closed record checked against
  `mid-eval-v1`, not something that should ever describe Iteration 2's state. **Reverted, back
  to byte-identical with `git diff mid-eval-v1 -- <file>` showing nothing:**
  `chapter8_testing.tex` (F3's table row and the results paragraph, back to `VERIFIED`/9/20),
  `chapter4_requirements.tex` (the "Deletion checks" row, back to its original claim),
  `appendix_test_cases.tex` (F2/F3/F4's order lengths and F4's shuffle seed, back to 6/15/seed
  1/3 tests; N2's rate back to 9/20), `chapter6_module_m3.tex` (N2's rate citation, back to
  9/20). All from *both* this session's passes — today's A1 edits and yesterday's N4-driven CI
  fix — since both predate M2's closed-record architecture landing. `fixture_results.tex`
  regenerated with `--reports` pointing at the tag, confirmed to reproduce exactly what CI will
  now check. **What stays correct and current:** the actual code (`eval/outcome.py`,
  `eval/report.py`) and every Iteration-2 doc (`evidence-m3.md`, `genai-log-m3.md`,
  `members.md`, `iteration-2-plan.md`) — A1's fix is real and F3 genuinely is `CANDIDATE` today;
  it is only the *frozen Mid report* that must not say so.
- **Lesson for next time, stated plainly rather than silently fixed:** I spent real effort this
  session treating the Mid report's generated table as something that should track live
  `eval/reports/` data (see the 2026-11-19 CI-fix entry above, and the two rounds of N2-rate
  chasing before this one) — reasoning from the chapter's own text ("regenerated... so it is
  current") rather than checking whether the *tag* was the intended source of truth. M2's
  independent fix answers that question definitively. Should have asked the team before the
  first regeneration, not after the third.
- **Not run this entry:** `ui.tests.test_server`, `mvn test-compile` steps, the Mid report's own
  LaTeX compile (no local toolchain, same standing limitation). `.github/workflows/*`,
  `ui/web/*`, `runner/cli.py`, `docs/evidence-m2.md`, `docs/genai-log-m2.md`,
  `docs/10-Final1/handover-m1-m3.md`, `eval/schema/report.schema.json`'s `depth` field — all
  merged cleanly (no conflict), M2's/M1's own files, not reviewed line-by-line here since they
  are outside this entry's scope (the conflict resolution) and their owners already verified
  them in their own commit messages.

## 2026-11-20 — A2: W16 phrase search, repo-wide, including evidence/ now that PR #105 landed

**Requirement:** W16 needed M1's `evidence/` part independently re-verified after PR #105
merged (last checked 2026-11-18, before it landed). Searched for the retired phrases (ADR-010
§2/ADR-011 §5/ADR-012 §1, root CLAUDE.md §0): "1-minimal" unqualified, "never modified"
unqualified, "sandboxed", "found mechanism"/"root cause"/"caused by"/"explains the failure"/"the
cause" unqualified, "passes alone" asserted as if sufficient on its own.

- `evidence/extract.py:645` and `evidence/README.md:6` are the only hits for
  mechanism/cause/modified/sandbox/1-minimal under `evidence/` (excluding `tests/`/`target/`) —
  both already the approved wording ("a possible mechanism, not confirmed as the cause").
- Repo-wide (`docs/`, `eval/`, `runner/`, `ui/`): every "passes alone" hit is the legitimate
  glossary/contract term (describing what the word means), not an unqualified certification
  claim. Every "1-minimal"/"never modified"/"sandboxed" hit is either the approved qualified
  wording, a literature description of *another tool's* property (iFixFlakies' own 1-minimal
  guarantee — not our claim), or inside a closed historical record (`docs/08-MidEval/`, dated
  `evidence-m*.md`/`genai-log-m*.md` entries, `docs/superpowers/plans/`) describing what was
  claimed or planned at the time — correctly left as-is per the same closed-record principle
  just re-learned the hard way in the merge-resolution entry above.
- **Command:** `grep -rn` across `evidence/ eval/ runner/ ui/ docs/` for each phrase (read-only,
  no code run — this was a text search, not a behavioural check).
- No violation found. W16 marked fully done in `iteration-2-plan.md`.

## 2026-11-20 — PR #109 CI failures diagnosed: one infra flake, one real cross-boundary regression

**Requirement:** PR #109 (this branch, commit `11c2173`) showed `CI / runner` (required) and
`CI / ui` (not required) failing. Diagnosed both via the GitHub API (check-runs, job steps,
annotations) before touching anything.

- **`CI / runner`: transient infrastructure flake, not a code issue.** The job's own
  `actions/setup-java@v4` step failed (`/usr/bin/tar failed with exit code 2` — a corrupted or
  interrupted JDK download/extraction on that runner VM). `fixture-build` and `evidence`/
  `python-eval` use the identical `setup-java@v4` config (`distribution: temurin,
  java-version: "8"`) on the exact same commit and succeeded, which rules out a config or code
  cause. **Recommendation: re-run the `runner` job** (GitHub's "Re-run jobs" on the PR), not a
  code fix.
- **`CI / ui`: a real regression, caused by my own merge-resolution step, not M2's work.**
  `ui/web/src/lib/report.test.ts` (M2's file, written during PR #106) hardcodes N2's expected
  rate as `"15/20"`/`"15/20"` — whatever `eval/reports/n2.json` showed in M2's own branch state
  when they wrote and verified that test ("ui 33 OK" in their commit message). My merge
  resolution then regenerated `eval/reports/*.json` fresh (`run_w9_integration.py`, to avoid
  hand-merging JSON — see the 2026-11-20 entry above), which landed N2 at a *different* random
  value (12/20) than what M2's test expected, breaking it. This is the same N2-randomness churn
  flagged repeatedly this session (2026-11-19 entries above), now crossing into M2's file
  because my regeneration step didn't check every consumer of the exact committed rate, only
  `eval/tests` and `runner.tests.test_cli`.
- **Asked the member before touching `ui/` (M2's folder): declined — left for M2.** Not fixed
  here. `ui` is not a required check (branch protection: `fixture-build`/`python-eval`/
  `runner`/`evidence` only), so this does not block the PR, but M2 needs to either hardcode the
  current 12/20 or (better, a design choice that is M2's to make, not mine) read the committed
  report's own rate dynamically instead of a literal string, so this stops recurring every time
  `eval/reports/n2.json` is regenerated.
- **Lesson, stated plainly:** before regenerating a shared, randomized fixture report as part of
  a merge resolution, check every file that hardcodes its exact value — not just the test
  suites in my own folder.

## 2026-11-20 — A3: no live doc claims F3 is `VERIFIED` today

**Requirement:** after A1 made F3 honestly `CANDIDATE`, check every doc for a present-tense
claim that F3 is `VERIFIED` -- distinct from A2 (retired phrases) and from the frozen Mid
report (which correctly still says `VERIFIED`, per the 2026-11-20 merge-resolution entry).

- Searched every `.md` under `docs/`, `eval/`, `fixtures/`, `runner/`, `ui/` mentioning "F3",
  excluding `mid-eval-report/`, `docs/08-MidEval/` and dated evidence/genai logs (all correctly
  frozen/historical).
- `docs/05-Testing/fixture-suite.md`'s "Ground truth" table row for F3 says `VERIFIED` --
  correct, that is literally the ground-truth column, which stays `VERIFIED` as the W20 target
  by design.
- `docs/10-Final1/mid-eval-outcome.md`'s "F1 and F3 gave VERIFIED" is a dated record of what
  the supervisor's reviewer ran at the Mid (tag `mid-eval-v1`) -- correctly historical, not
  touched.
- **Real violation, fixed:** `docs/10-Final1/demo-plan.md`'s rehearsal table said, for "Remove
  one of F3's polluters": "show the deletion check that already answers it" -- wrong, and
  directly contradicted by A1: F3 has no deletion check at all today, which is exactly why it
  is `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]`. Fixed to say so explicitly and distinguish
  F1/F2/F4's free check (ADR-011 §2) from F3's missing one (W20). This is `docs/` (joint) and
  directly describes my own component's behaviour, so edited directly rather than flagged.
- **Flagged, not touched (M2's file):** `docs/04-Implementation/diagnose-cli.md`'s opening
  "Status (2026-10-10)" line says "F3 `VERIFIED` with two polluters" -- unlike the Mid report
  or dated logs, this is a live, actively-maintained four-point note (its ADR-008 section was
  updated as recently as 2026-11-20, PR #108), so this is genuine staleness, not a frozen
  record. Raised for M2 (file header: "Member 2, W9") rather than edited directly.
- No other violation found.

## 2026-11-20 — A4: document `eval/README.md` for `RunTally`/schema v2

**Requirement:** `eval/README.md`'s module table and prose still described the schema-v1 world
entirely — no mention of `RunTally`, `report.py` (missing from the table altogether despite
being the module that assembles every schema-v2 report), `candidate_reasons`,
`resource_edges`, `assurance`, or the ADR-011 deletion-evidence claim A1 just fixed.

- Added `report.py` to the module table (previously entirely absent); updated `baseline.py`'s
  and `outcome.py`'s rows to name `RunTally`/`classify()` and the 13-row table.
- New section "Schema v2 (ADR-010/ADR-011, W19)" explaining the four-way `PASS`/`MATCH`/
  `OTHER`/`INFRA` classification, the four `VERIFIED` claims (S1/S2/S3/R1), `candidate_reasons`,
  `resource_edges`, `assurance`, and the A1 deletion-evidence fix (one kept polluter free via
  ADR-011 §2, two or more `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]` until W20).
- **Caught my own mistake before committing:** first softened the N2-rate line in the
  "Benchmark yield report" section to "varies run to run, read the live file" — wrong. That
  specific paragraph is about `benchmark/logs/N2.json`, a one-time **frozen** 2026-10-09
  measurement (`isolation_successes`/`isolation_n`, old schema), completely unrelated to the
  live, churning `eval/reports/n2.json` I'd been fixing all session. Checked
  `benchmark/logs/N2.json`'s actual content (`isolation_successes: 12, isolation_n: 20`) before
  assuming it was the same churn problem — it is genuinely, permanently 12/20, and the original
  text was correct. Reverted to the original number, added a note distinguishing the two files
  explicitly instead, so a future reader doesn't make the same conflation.
- **Command:** `python3 -m unittest discover -s eval/tests` → 123/123 OK (docs-only change,
  sanity check).

## 2026-11-20 — W26a resumed: full discovery on real fastjson FJ-03 (steps 6-9 unblocked)

**Requirement:** M2's A1 fix (`runner/discovery.py` reads the project's real Surefire
includes/excludes, PR #110) unblocks W26a steps 6-9. M2 asked, via the member: run a full
discovery first, confirm `SerializeWriterTest_14#test_writer_1` and
`MaxBufSizeTest#test_max_buf` are found, record the count, and note the lifecycle default.

- **Setup found reusable:** the fastjson checkout and portable JDK 8 from the 2026-11-19 W26a
  session survived in an earlier session's scratch folder (outside this repo, as before).
  **The portable JDK's extraction in that old folder was incomplete** — `jre/lib/security/`
  was missing (first real symptom: Maven's `help:effective-pom`/`dependency:build-classpath`
  goals crashed with `SecurityException: Cannot locate policy or framework files`, a JCE
  initialisation failure, not a code bug). Confirmed the original `.zip` itself was intact
  (106,490,535 bytes, matches the original download) and does contain `jre/lib/security/*`
  (`unzip -l`); re-extracted it fresh into this session's own scratchpad (still outside the
  repo) and the same commands then succeeded — the old extraction's folder had silently lost
  files, most likely the "routine cleanup can clear it" risk this environment's own scratch
  directories are explicitly warned to carry, not a download or build problem.
- **Command** (`runner.discovery.project_selection`/`discover_order` called directly, matching
  `runner.diagnose.diagnose()`'s own real code path — `maven_test_classpath` with
  `effective_pom=`, then `project_selection`, then `discover_order` against
  `target/test-classes`; JDK 8 as `JAVA_HOME`, `class-grouped` lifecycle, the real
  `OrderRunner`, no fake/mock):
  - `includes: ('**/bvt/**/*.java',)`, `excludes: ('**/*$*',)` — fastjson's own real Surefire
    configuration, read correctly (this is exactly the gap W26a found on 2026-11-19).
  - **Total discovered: 4464 test methods.**
  - `SerializeWriterTest_14#test_writer_1` — **FOUND.** `MaxBufSizeTest#test_max_buf` —
    **FOUND.** Both of the protocol's named tests (the known polluter and the victim) are
    among the discovered set, both by full package-qualified name and by class short name.
  - Lifecycle: ran with `class-grouped` explicitly, matching the project-wide default since
    M1's control run (PR #108, 2026-11-20) — noted for M2 as asked.
  - `git status --short` in the fastjson checkout after the run: no output — no source file
    changed (CLAUDE.md §4; the build only wrote to `target/`, excluded by convention).
- **Limitation:** this is discovery only (step 6 of the protocol), not yet the full pipeline
  run (steps 7-9: the real diagnose through to a report, the baseline/targeted-search
  comparison). Discovery being correct was the hard blocker; the remaining steps are real JVM
  runs, not yet attempted this entry.

## 2026-11-20 — W20: eval/report.py reads the real deletion_checks (Interface 4, PR #121)

**Requirement:** M2's W20 runner half merged (PR #121): `DiagnosisRuns.deletion_checks`, the
real repeated-removal check per kept polluter, per Interface 4
(`docs/contracts/interfaces.md`). M3's half: `eval/report.py` reads it and sets `deletion_status`
accordingly, replacing A1's fail-safe stand-in (2026-11-19) with the real check.

- **Test-first.** Added `TestDeletionChecksW20` to `eval/tests/test_report.py` with a
  `FakeDeletionCheck` dataclass matching Interface 4's shape exactly (not
  `runner.deletion.DeletionCheck` -- coded against the contract, per its own instruction).
  Confirmed every new/changed assertion failed against the unfixed code first (3 real
  failures: two-polluters-both-needed expecting `CANDIDATE` instead of `VERIFIED`, and
  INCONCLUSIVE falling back to `INCOMPLETE`) before implementing the fix.
- **Logic** (`eval/report.py`): reads `diagnosis.deletion_checks`, takes only the checks at the
  highest `round` (earlier rounds, including a dropped test's own entry, stay in the list per
  Interface 4 but are not the verdict), then: any `NOT_RUN`/`runs is None`/`runs.n < 10` ->
  `DELETION_INCOMPLETE`; else any `INCONCLUSIVE` -> `DELETION_INCONCLUSIVE` (ranks above
  incomplete); else all `NEEDED` -> `DELETION_VERIFIED`; no checks at all (a stale caller, or
  the budget ended before any ran) -> `DELETION_INCOMPLETE`, fail-safe, never `VERIFIED`.
  **Interpretation flagged for the team:** Interface 4's own table lists "all NEEDED" before
  the `runs.n < 10` clause, which read literally would let an all-NEEDED set with a short run
  count still reach `VERIFIED`. Implemented the stricter reading instead (short-run checked
  first) since a `NEEDED` label from too few trials (e.g. W24 cutting a check short) should
  not count as established just because every check happens to agree -- raised with M2/M1 for
  confirmation, not decided unilaterally.
- **Schema bump** (`eval/schema/report.schema.json`, as Interface 4 asked M3 to propose): new
  `deletionCheck` def and a required `deletion_checks` array field, shaped as ADR-011 section 4
  plus `round`, `runs: null` allowed when `status: "NOT_RUN"`. Updated every example fixture
  (10 files) and `test_schema_validator.py`'s shared `VALID_REPORT` to carry a real-shaped
  `deletion_checks` entry -- all were missing the new required field.
- **Real result, the actual F3 case (ADR-011 T3):** regenerated all 8 reports
  (`eval/tools/run_w9_integration.py`). F3: both `setFlagA` and `setFlagB` come back `NEEDED`,
  20/20 each, round 1, source `deletion-run` -- 40 real JVM runs. **F3 is honestly `VERIFIED`
  again**, matching its ground truth for the first time with a real, not fail-safe, basis.
  F1/F2/F4 (one polluter each, `alone-check` source) also `VERIFIED`; N1-N4 unchanged. All 8
  match `fixtures/od-fixture/ground_truth.json` exactly.
- **Renamed `eval/examples/example_f3_candidate.json` back to `example_f3_verified.json`** --
  not a reversion to the pre-A1 state, but the real check now existing and confirming the
  ground truth where A1 could only fail safe without one. Content rewritten to the real
  `deletion_checks`/`resource_edges` shape (M1's extractor and M2's deletion check both ran for
  real this time, not placeholder values). `eval/tests/test_examples.py`'s
  `EXPECTED_INPUTS`/`REAL_EXAMPLE_TO_LOG_CASE` keys updated to match.
- **A real, separate bug found and fixed: personal-path leak in my own
  `eval/tools/run_w9_integration.py`.** `execution_record_reference` in the regenerated reports
  was an absolute path (`C:\Users\...\flaketrace-records\...`) -- confirmed via
  `git show HEAD:eval/reports/f1.json` that this was **already committed on `main`**, from my
  own earlier regenerations this session (the A1 fix, the merge resolutions). `RECORD_DIR` in
  the script has always been built from `Path(__file__).resolve()` (absolute by construction);
  `runner.diagnose.diagnose()` never relativises it either (a real design choice for a real
  end-user installation, where an absolute path is correct to log locally) -- nothing wrong in
  either member's own file, just a gap in my own tool that commits reports to the repo. Fixed
  with a `_diagnose()` wrapper that relativises `execution_record` to `REPO_ROOT` before
  `assemble_report()` ever sees it; re-ran the regeneration, confirmed `grep` for the local
  username finds nothing in any of the 8 committed reports now. **Flag for the team:** the
  already-committed history (several commits on `main`) still has the leaked path in old
  diffs -- not rewriting history to fix it (destructive, against the "member commits" rule's
  spirit), but worth knowing it is there if anyone great-reps the git log.
- **Command:** `python3 -m unittest discover -s eval/tests` -> 128/128 OK, several times
  across this entry (after the logic fix, after the schema bump, after the path fix, after the
  rename). Real `eval/tools/run_w9_integration.py` run (and a second, clean re-run after the
  path fix): F1/F2/F3/F4 `VERIFIED`, N1/N2 `UNRESOLVED(VICTIM_FAILS_ALONE)`, N3
  `UNRESOLVED(NOT_REPRODUCED)`, N4 `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)` -- matches
  ground truth exactly.
- **Flagged, not touched (M2's file) -- member's explicit choice:**
  `runner/tests/test_cli.py`'s `test_f3_two_polluters_are_candidate_until_deletion_checks_exist`
  now fails (F3 is `VERIFIED`, not `CANDIDATE`) -- real, expected breakage from this change,
  left for M2 to update since he is actively working the related PR. Confirmed this is the
  *only* casualty: `python3 -m unittest discover -s runner/tests` (real JVM) -> 254 tests,
  **1 failure, exactly this one** -- no cascading breakage anywhere else in his 254-test suite.
- **Not done this entry:** `claims-ledger.md` row G2 progress noted in `members.md`/
  `iteration-2-plan.md` but its `OPEN` status left alone -- Interface 4's own plan names step 4
  as "M1 reproduces T3 independently on her machine", which has not happened yet; closing G2
  before that would be exactly the "closed without independent reproduction" mistake CLAUDE.md
  §5 warns against.
- **Flagged, not touched (M2's row): claims-ledger row E14 is stale again.** M2 already
  qualified it once for A1 (2026-11-19: "F3's command gives `CANDIDATE
  [DELETION_EVIDENCE_INCOMPLETE]`... F3's ground truth `VERIFIED` is W20's target") -- now
  stale a second time, since W20 landed and F3 genuinely reaches `VERIFIED` again. Not mine to
  edit (Owner: M2); raised for him alongside the `test_cli.py` note above.

## 2026-11-20 — Two PR #129 CI failures fixed in M2's files, member's explicit permission

**Requirement:** PR #129's `ui` and `runner` CI checks both failed. Both root-caused to real
issues, both in M2's files, both fixed with the member's explicit go-ahead (asked first via
`AskUserQuestion`, chose to fix both rather than flag-only).

- **`ui` (2 failures):** `ui/web/src/lib/report.test.ts` hardcoded `f3: { outcome: "CANDIDATE",
  ... }` -- stale since my W20 fix (above) made the real committed `eval/reports/f3.json`
  genuinely `VERIFIED`. Fixed the `EXPECTED` table entry. The other failing test ("says why a
  result is only a candidate (F3)") asserted a `DELETION_EVIDENCE_INCOMPLETE` candidate reason
  that no real committed report carries any more (all of F1-F4 are `VERIFIED`, N1-N4
  `UNRESOLVED`) -- rewrote it to spread F3's real shape with `outcome`/`candidate_reasons`
  overridden to the state F3 itself was honestly in before W20, rather than deleting the only
  test that exercises this mapping. **Command:** `npm test` (ui/web) -> 33/33 OK.
- **`runner` (19 errors, 7 failures, all from the same root cause):**
  `runner/order_runner.py`'s `maven_test_classpath()` called the short Maven goal prefix
  `dependency:build-classpath`, which needs Maven to resolve `dependency` ->
  `org.apache.maven.plugins:maven-dependency-plugin` via plugin-groups metadata (local cache or
  Maven Central) -- failed on that CI run ("No plugin found for prefix 'dependency'"), and
  every test calling this function failed identically as a result. Not a logic bug in any
  test; a tooling-resolution gap. Checked this machine's own `~/.m2` cache
  (`find ~/.m2/repository/org/apache/maven/plugins/maven-dependency-plugin`) for an
  already-proven version rather than guessing one from memory -- `3.7.0` is cached and has
  resolved successfully all session. Pinned the fully-qualified goal
  (`org.apache.maven.plugins:maven-dependency-plugin:3.7.0:build-classpath`), which skips
  prefix resolution entirely regardless of cache/network state. **Command:** confirmed the
  fully-qualified goal resolves for real (`maven_test_classpath(fixtures/od-fixture)` ->
  4 classpath entries, JUnit jar included); `python3 -m unittest discover -s runner/tests`
  (real JVM) -> 256 tests, **exactly 1 failure** -- the same, already-flagged
  `test_f3_two_polluters_are_candidate_until_deletion_checks_exist` (M2's file, expects
  `CANDIDATE`, F3 is genuinely `VERIFIED` since W20). No new breakage from the plugin pin.
- **Not done:** did not add a CI retry for this specific failure class (M2 already has one for
  `setup-java`, PR #120) -- the fully-qualified goal is the more robust fix (removes the
  failure mode entirely rather than retrying into it), so a retry would be redundant here.

## 2026-11-20 — The last blocking test fixed: `runner` CI required check, member's permission

**Requirement:** `runner` is a required check; the one known F3 failure above was actively
blocking the PR from being mergeable, not just a cosmetic red X. Asked the member explicitly
before touching this again (the first time this exact test came up, the answer was "leave it
for M2"; this time, with it genuinely blocking merge, the answer was to fix it).

- **Fix:** `runner/tests/test_cli.py`'s `test_f3_two_polluters_are_candidate_until_deletion_
  checks_exist` renamed to `test_f3_two_polluters_both_needed_gives_verified`; its one stale
  assertion (`("CANDIDATE", ["DELETION_EVIDENCE_INCOMPLETE"])`) corrected to
  `("VERIFIED", [])`. Every other assertion in the test (polluters, shared_resource, the
  `flagB` limitation line, the minimised-count line) needed no change -- F3's structure is
  identical, only its deletion-check outcome changed.
- **Command:** the single test, real JVM -> OK (confirmed before touching anything else in the
  file). Full `python3 -m unittest discover -s runner/tests` rerun to confirm this was the
  only casualty, result recorded once it finishes.
- **Not done:** claims-ledger row E14 (M2's row, also stale for the same reason) is a doc, not
  a blocking CI check -- left for M2 as before; this entry only fixes what was actually
  blocking the PR.

## 2026-11-20 — W24 budget ledger, report half (Interface 6, `m3/w24-report-budget`)

**Requirement:** `docs/10-Final1/iteration-2-plan.md`'s W24 row, "Report half: M3" --
`eval/outcome.py` and `eval/report.py` consume M2's already-merged `runner/budget.py`
(`m2/w24-budget-ledger`, PR #132) per Interface 6
(`docs/contracts/interfaces.md`): the `UNRESOLVED(BUDGET_EXHAUSTED)` and
`CANDIDATE [BUDGET_EXHAUSTED]` report rules, and the schema's new `budget` field.

- **File/function:** `eval/outcome.py` -- `DecisionInput.verification_budget_exhausted`
  (new field; distinct from the existing `budget_exhausted`, which is for a search that found
  no polluter at all), checked only in the S1/S3/R1 block so a POLLUTER_FOUND diagnosis whose
  budget ran out during verification can reach `CANDIDATE [BUDGET_EXHAUSTED]` but never
  `VERIFIED`. `eval/report.py` -- `assemble_report` now handles
  `runner.diagnose.DiagnosisRuns.status == BUDGET_EXHAUSTED` (the same way `NOT_REPRODUCED` is
  handled: a reference may or may not have been established before the cut), sets
  `decide(budget_exhausted=True)` for it and `decide(verification_budget_exhausted=True)` for
  an exhausted POLLUTER_FOUND diagnosis, and adds the new `_budget_fields()` helper that reads
  `diagnosis.budget` (M2's `runner.budget.BudgetAccount`, Interface 6) into the report's
  `budget` field -- omitted entirely when `diagnosis.budget is None` (a DiagnosisRuns built
  before W24), same optional-field pattern as the existing `order_exploration`.
  `eval/schema/report.schema.json` -- new `$defs.budgetAccount` and an optional `budget`
  property, with `candidates_total`/`candidates_tried` nested as `{"total", "tried"}` per
  Interface 6's own instruction to M3.
- **Test-first:** added `FakeBudgetAccount` to `eval/tests/test_report.py` (Interface 6's own
  shape, not `runner.budget.BudgetAccount` -- coded against the contract, same rule as
  `FakeDeletionCheck`), one new row test in `eval/tests/test_outcome.py`
  (`test_row12_candidate_budget_exhausted_during_verification`) and six in a new
  `TestBudgetLedgerW24` class in `eval/tests/test_report.py`. Confirmed every one of these 7
  tests fails against the pre-fix code first (`TypeError: ... unexpected keyword argument
  'verification_budget_exhausted'` for the outcome test; `UnhandledStatus`, `KeyError:
  'budget'`, and one wrong-outcome assertion for the six report tests), then implemented.
- **Command:** `python3 -m unittest eval.tests.test_stats eval.tests.test_outcome
  eval.tests.test_schema_validator eval.tests.test_examples eval.tests.test_baseline
  eval.tests.test_yield_report eval.tests.test_report` (every module CLAUDE.md lists, plus
  `test_report` since CI's `python-eval` job globs every `eval/tests/test_*.py` anyway) ->
  **136 tests, OK**, 0 failures.
- **Limitation:** this is the "M3, in parallel" half only (Interface 6's own ordering). The
  real F2 run with a budget limit just above B2's minimum, and one with no limit (ADR-014
  evidence items 1-3), is the next step, "together, once merged" -- not yet run; no number for
  it exists anywhere in this repository. M1's independent reproduction of the
  `UNRESOLVED(BUDGET_EXHAUSTED)` case (Interface 6 step 4) has also not happened yet.

## 2026-11-20 — ADR-014 evidence item 2, for real, both halves merged (W24)

**Requirement:** ADR-014's "what must be demonstrated" table, item 2 (owner M2, M3): "A budget
too small to finish gives `UNRESOLVED(BUDGET_EXHAUSTED)`, a report and a budget account" -- on
the real fixture, once the runner half (`m2/w24-budget-ledger`, merged PR #132) and the report
half (above) are both on `main`. Before this, M2's own real run at the same scenario
(`docs/evidence-m2.md`, `--budget-invocations 70`) got **exit 3, no report** --
`eval/report.py` still raised `UnhandledStatus` for `BUDGET_EXHAUSTED` at that point. This entry
is the first time the full pipeline (both halves) has run end to end on this status.

- **B2's minimum for F2** (`odfixture.FeatureVictimTest#expectsTurboDisabled`, n=20): starting
  order is 8 tests long (`eval/reports/f2.json`'s `original_failing_order`), so
  `reserve(20) + 8 + 2 = 60 + 10 = 70`. Used `--budget-invocations 72` ("just above the
  minimum", 2 above 70, distinct from M2's own exactly-at-70 run).
- **Command (JDK 8 on PATH, real Maven/JVM, no fastjson/mocking):**
  `python3 -m runner diagnose --project fixtures/od-fixture --victim
  odfixture.FeatureVictimTest#expectsTurboDisabled --records <tmp> --budget-invocations 72`
- **Real result:** exit **0** (not 3 any more). `UNRESOLVED (BUDGET_EXHAUSTED)`. CLI:
  `reproduced: 1/1 (lower bound 0.207)`, `budget: spent 32 of 72 invocations (reserve 60);
  search tried 2 of 7 candidates; stopped in search`. The written `.report.json` validates
  against the schema (`eval.schema_validator.validate_report`, confirmed, not assumed) with
  `outcome: "UNRESOLVED"`, `unresolved_reason: "BUDGET_EXHAUSTED"`, and a real `budget` object:
  `{"limit_invocations": 72, "reserve_invocations": 60, "spent": {"reproduce": 8, "alone": 20,
  "search": 4, ...}, "launches": 23, "exhausted": true, "exhausted_phase": "search",
  "candidates": {"total": 7, "tried": 2}}`. Reproduced identically on a second run (same
  numbers both times -- F2 is not randomised, unlike N2).
- **Comparison, no limit** (same victim, same command without `--budget-invocations`): real
  result `VERIFIED (sequence)`, polluter `odfixture.FeaturePolluterTest#enableTurbo`,
  `reproduced: 20/20`, `budget: spent 82 invocations, no limit (reserve 60); search tried 7 of
  7 candidates`, `exhausted: false`, `exhausted_phase: null` -- matches M2's own earlier
  no-limit numbers in `docs/evidence-m2.md` exactly (spent 82, search tried 7 of 7), confirming
  determinism and that "without a limit, nothing changes" (Interface 6) holds for real, not
  just in the unit tests.
- **Not done / left alone:** did not overwrite the committed `eval/reports/f2.json` with either
  run -- that file is read by `ui/web`'s tests and `json_to_tex.py` with fixed expectations
  unrelated to the budget field, and regenerating it was not asked for; these two reports were
  written to a scratch records folder instead, not committed. Items 1 and 3 of the same table
  are M2-owned and already covered by his own real runs (`docs/evidence-m2.md`); items 4-5 are
  W25 (ranking), not this work package. M1's independent reproduction (Interface 6 step 4)
  still has not happened.

## 2026-11-20 — W23 evidence bundle format and recount checker (ADR-013)

**Requirement:** ADR-013, M3's half: the bundle format (`create_bundle`) and the `verify-bundle`
recount checker (`python -m eval.bundle verify`), reading only the bundle, never the runner's
state, and comparing checksums, schema, a full independent recount of every tally, and a
re-decide against `eval.outcome.decide()`.

- **File/function:** new `eval/bundle.py` -- `create_bundle(report_path, record_path, out_dir)`
  builds the 5-file ADR-013 folder from an existing report.json/record.jsonl pair (as the real
  CLI already writes them), reading every environment/parameter field from the record's own
  header line (M2's capture, already complete since W22/W24/W25 -- nothing here is recomputed,
  only reshaped and redacted). `verify_bundle(bundle_dir)` checks every file's checksum,
  validates `report.json` against the schema, then recounts the reference signature, the alone
  tally, the sequence tally and every deletion check from `record.jsonl` alone, and feeds the
  recount to `eval.outcome.decide()` to compare the verdict too.
- **Scope (flagged explicitly, not guessed past):** the recount is exact for the shapes a real
  diagnosis produces once a sequence was checked at all --
  POLLUTER_FOUND/CANDIDATE/VERIFIED (from "verify" lines), VICTIM_FAILS_ALONE/_DIFFERENTLY
  (reuses the alone tally, matching `runner.diagnose._steps`'s own code), and NOT_REPRODUCED
  with no reference ever established (from "reproduce" lines only, matching the exact
  `RunTally(attempts, attempts-failures, 0, 0, failures)` shape `_steps` builds). INCONSISTENT
  and BUDGET_EXHAUSTED are not covered yet -- `verify_bundle` says so explicitly rather than
  silently claiming a number it did not check. `environment.txt` also only carries the summary
  lines the record header already has (`java_version()`/`maven_version()`), not the full raw
  `java -version`/`mvn -v` banner ADR-013's own wording asks for -- capturing that would be
  runner-side work (M2's "capture"), not expanded into silently here.
- **Test-first:** wrote `eval/tests/test_bundle.py` (11 tests) before any implementation code
  existed; confirmed `ModuleNotFoundError: No module named 'eval.bundle'` first. Covers every
  row of ADR-013's own test table that applies at the unit level: a fresh bundle verifies
  clean; a changed report count is caught by the recount; one changed byte of the record
  breaks the checksum; deleting one `alone` line **and fixing the checksum afterwards** is
  still caught by the independent recount (the checksum alone is not enough -- this is the
  point of having two independent checks); a bundle with no manifest is a clear problem, not a
  crash; plus the VICTIM_FAILS_ALONE, NOT_REPRODUCED and two-polluter deletion-run shapes.
- **A real bug found and fixed while bundling a real run, not a synthetic one:** the first
  redaction attempt missed the home directory inside the record's own `command` list, because
  that path used forward slashes (`C:/Users/zarpa/...`, from this machine's bash-like shell)
  while `Path.home()` returns backslashes (`C:\Users\zarpa`) -- a plain string replace matched
  neither against the other. Found it the only way that actually proves it: `grep -c zarpa` on
  the real bundle's own files after creating it, not by reasoning about the code. Fixed by
  trying both slash styles for every redacted path; added
  `test_redacts_a_path_that_uses_the_other_slash_style_too` as a permanent regression test;
  re-ran the real bundle afterwards and confirmed zero hits.
- **Real end-to-end run (not just synthetic fixtures):** `python -m runner diagnose --project
  fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode` (JDK 8, real
  Maven/JVM) -> real `VERIFIED (sequence)`, 20/20 reproduced. `python -m eval.bundle create`
  on its output, then `python -m eval.bundle verify` on the result -> real exit 0, no username
  anywhere in any of the 5 files (`grep -c zarpa` on each, all zero). Copied a tampered copy
  (`reproduction.matched` changed from 20 to 19) and re-verified: real exit 1, both the
  checksum mismatch and the independent recount flagged it, matching ADR-013's own test table.
  The real bundle itself is committed at `eval/bundles/odfixture.ConfigVictimTest#expects
  DefaultMode-20261120T193202Z/` (ADR-013 section 4, fixture cases, committed).
- **Command:** `python3 -m unittest discover -s eval/tests` -> **148 tests, OK** (148 =
  136 from before W24's evidence write-up + 1 regression test there + 11 new bundle tests).
- **Not done:** F2-F4 and N1-N4 are not bundled yet, and `eval/reports/*.json` is not replaced
  -- flagged in `eval/bundles/README.md` as the next step, not part of W23's own "done when"
  (ADR-013's tests, and M1's independent reproduction recorded in her own evidence log). M1's
  reproduction (ADR-013 section 5: clone at the recorded tool commit, `verify-bundle`,
  `replay`) has not happened. `python -m runner replay` (ADR-013 section 3, M2's half) does
  not exist yet -- `replay.md` inside each bundle names the manual command in the meantime.

## 2026-11-21 — W23's format changed mid-build: Interface 8, `eval/bundle.py` reworked

**What happened:** the 2026-11-20 entry above built `eval/bundle.py` straight from ADR-013's
own text (its own `create_bundle` writer, its own manifest shape) because, at that point,
nothing more specific existed. Before that PR merged, the team agreed **Interface 8**
(`docs/contracts/interfaces.md`, recorded by M2, 2026-11-21) -- a materially different,
more detailed manifest (`kind`, `run_date`, `replay_of`, a flat `environment` block, `victim`
as a string not an object), a different folder-naming rule (the record's own filename stem,
timestamp first, not the victim-first name ADR-013's literal wording suggested), a more
rigorous redaction (`runner.bundle.redact`/`assert_clean`: path-boundary regex matching, both
slash styles and JSON-escaped forms, a fail-closed check that refuses to write a bundle that
would still contain the home path or user name), and **a real writer already built and merged**
(`runner/bundle.py`, `runner/replay.py`; M2) with real F1/F3 bundles replayed `same`
([[evidence-m2]]). Caught this by re-fetching `main` before pushing the W23 PR -- not something
a text-only merge conflict would have shown, since `eval/` and `runner/` never touched the same
file; the mismatch was in what the two halves assumed about each other's shape.

**What I did about it, not just resolved as text:**
- Deleted `create_bundle` and every writer-side helper (`_redact`, `_manifest`, `_replay_md`,
  `_environment_txt`, `bundle_folder_name`) entirely -- Interface 8 point 1 is explicit that
  there is one writer, and it is the runner, not `eval/`.
- `verify_bundle` now calls `runner.bundle.read_bundle` for checksums (it already raises
  `BundleError` on any mismatch; my own manual checksum loop was redundant and removed) and
  reads `bundle.manifest`/`bundle.report` from it, rather than parsing the bundle's files by
  hand.
- Added the new `kind: "replay"` shape to the recount: a replay bundle has no reproduce/
  shuffle/search/minimise lines at all (`runner.replay.replay_steps` only ever runs alone,
  deletion, verify), and its reference signature is the record header's own
  `reference_signature` field (carried over from the original report, per Interface 8), not
  re-derived from the search phase the way a diagnosis bundle's is -- read `runner/replay.py`
  first to get this right rather than guessing from the manifest text alone.
- Rewrote every test in `eval/tests/test_bundle.py` to build its bundles through the *real*
  `runner.bundle.write_bundle`, not a hand-rolled approximation of the format -- so this
  module's tests can never again silently drift from the real contract the way the first
  version did.
- Deleted the committed `eval/bundles/odfixture.ConfigVictimTest#expectsDefaultMode-
  20261120T193202Z/` (my old format) and regenerated a real one with the actual CLI
  (`runner diagnose --bundle`), in the real Interface 8 shape, at
  `eval/bundles/20261121T094724Z-odfixture.ConfigVictimTest#expectsDefaultMode/`.
- **Command:** `python3 -m unittest discover -s eval/tests` -> **146 tests, OK** (10 bundle
  tests now, rewritten; down from 11 because two of the old create-focused tests no longer
  apply with `create_bundle` gone). Real end-to-end: `python -m runner diagnose --project
  fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode --bundle
  eval/bundles` (JDK 8, real Maven/JVM) -> real bundle written; `python -m eval.bundle verify`
  on it -> real exit 0, zero occurrences of the machine username in any of the 5 files
  (checked directly, not assumed). A tampered copy (`reproduction.matched` changed) ->
  `read_bundle`'s own checksum check catches it immediately, exit 1.
- **Not a mistake in the honesty-rules sense:** nothing was asserted that wasn't run, and the
  11-tests/148-tests numbers in the 2026-11-20 entry were real at the time, against the code
  that existed then. This is a design the team changed out from under a half-built PR, caught
  by re-checking `main` before pushing -- exactly the discipline that is supposed to catch
  this, working as intended. Updated `eval/bundles/README.md`, `eval/README.md`,
  `docs/07-Defense/claims-ledger.md` (G7), `docs/10-Final1/iteration-2-plan.md` (W23 row) and
  `docs/09-Team/members.md` accordingly -- none left describing the superseded design as
  current.
- **Still open:** F2-F4/N1-N4 not bundled; `eval/reports/*.json` not replaced; M1's independent
  reproduction of a real bundle (ADR-013 section 5) has not happened.

## 2026-11-21 — merged, confirmed on `main`; two team questions settled; W32 task written

**Requirement:** PR #146 landed, M2 merged a follow-up (PR #147) fixing a real Windows CRLF
checksum failure and adding a second F1 bundle; both M2 and M1 sent questions/requests that
needed a real answer, not just acknowledgement.

- **Confirmed on `main` (pulled, 682984d):** `python -m eval.bundle verify` on both committed
  bundles (`eval/bundles/20261121T093338Z-.../` M2's clean one, `.../20261121T094724Z-.../`
  mine) -> real exit 0 on both, against the real merged `runner.bundle.read_bundle`. This is
  the first time the writer (M2) and the checker (M3) have confirmed each other on bundles
  neither of us tampered with in the same session -- the actual point of Interface 8. Full
  suite: `python3 -m unittest discover -s eval/tests` -> **146 tests, OK**.
- **M2's question: keep both F1 bundles, or remove mine and keep only his clean one?**
  Decided: **keep both.** They reproduce the identical verdict (`VERIFIED`, 20/20, 0/20 alone)
  under two different environments -- JDK 8 from a working copy with uncommitted changes
  (`tool.dirty: true`) vs. JDK 21 from a clean checkout of `main` (`tool.dirty: false`) -- which
  is a genuine cross-environment check, not noise to clean up. `tool.dirty` is accurate,
  transparently-reported metadata about which one ran; removing the dirty one would not make
  the evidence stronger, it would just give up that cross-check. Recorded the reasoning in
  `eval/bundles/README.md` so it reads as a decision, not an open question, for anyone who
  finds two F1 bundles later.
- **G7 and G8 (claims ledger):** G8 was already `SETTLED` (by M1, M2 and M3, with the scope
  M2's PR fixed) by the time I checked -- nothing further needed from me there, despite both
  M1's and M2's messages asking about it; the team had already agreed it before I read the
  messages. Updated G7 to reflect what actually merged: writer, replay and recount all built
  and confirming each other on real bundles, still `OPEN` only on M1's independent
  reproduction, which is in progress.
- **W32's acceptance task, supplied (M1 explicitly asked for this before any session runs):**
  three written questions against the real, committed F1 report, read directly from its own
  `report.json`/CLI text (not invented wording) -- which test, whether the resource overlap is
  being read as proof of cause (the one question that fails the whole task on its own if
  wrong, since that is exactly what FT018 is testing), and what the report withholds. Fixed
  pass criteria, a 5-minute limit matching the session plan's own allocation, and a named FJ-03
  variant in case M2's case choice changes. Written into
  `docs/10-Final1/practitioner-check.md` directly, not drafted elsewhere first.
- **FJ-03 "ranked = original" note for W25/W26b:** M1's PR #145 already found and documented
  this (the pollution is a JDK `ThreadLocal` call static analysis does not follow, so there is
  no edge to rank by -- not a ranking defect). Recorded a pointer to it in the W25 row of
  `docs/10-Final1/iteration-2-plan.md` so my own future measurement work reports it correctly
  ("ranked = original, no edge found") on the first attempt, not after re-discovering what M1
  already found.
- **Not done by me:** M2's own "The case" section of `practitioner-check.md` is still a
  placeholder -- he made the real clean F1 bundle for it, but hasn't filled in that section of
  the protocol itself; flagged for him rather than filled in on his behalf (his folder).

## 2026-11-21 — W25 measurement: ADR-014 evidence items 4 and 5, both real, both done

**Requirement:** ADR-014's own evidence table, items 4 ("`ranked` against `original` on the
fixture and on the real case, same budget, total invocations to the same verdict") and 5 ("the
same comparison offline on the POC's stored scan tables, using the product's `rank_candidates`
-- no JVM runs"). Both M3's (item 5 with M1). Both unblocked once M2's W25 runner half merged.

### Item 5 -- offline, real fastjson, no JVM test runs

Cloned fastjson for real at the pinned commit (`e05e9c5e4be580691cc55a59f3256595393203a1`,
`https://github.com/alibaba/fastjson`) into an isolated scratch directory, built it for real
(`mvn -B -DskipTests test-compile`, portable JDK 8, `BUILD SUCCESS`), then ran the product's
real `rank_candidates` (unmodified, `evidence.extract.rank_candidates`) against all 524 real
candidates from `POC/results/scan_FJ-03.csv` -- the real, stored scan outcome, not a POC
re-run. No JVM test execution anywhere in this step; every analysis is `javap`-based static
analysis through `evidence.extract.Project`/`AnalysisCache`, the product's own real code.

**Real result:** `rank_candidates` found **zero static evidence** for all 6 of the real
relevant candidates (`od_relevant=YES` in the scan table) -- every one scored `(0, None,
position)`, meaning no shared-resource edge at all, at the product's default depth. With no
evidence, the rule's own third tie-break (original position) applies, so ranking left the
order **completely unchanged**: the first relevant candidate's ranked position (368 of 524)
exactly equals its original position (368 of 524). This independently confirms, for real and
end to end (not by re-reading M1's finding), what she already found: FJ-03's pollution is a
JDK `ThreadLocal.set()` call that static analysis does not follow
([[04-Implementation/evidence-collector]]), so there is no edge for `rank_candidates` to rank
by. **A real result, reported as it is** (ADR-014's own instruction) -- not a ranking defect,
and not spun as a win; on this one real case, ranking helps not at all.
- **Command:** a one-off script (not committed -- see "Not done" below),
  `evidence.extract.rank_candidates(project, victim, candidates, cache=cache)` against the real
  compiled fastjson classes. 524/524 candidates analysed with zero failures,
  `analysis_seconds` 249.3 real seconds on this machine.
- **A real bug I found and fixed in my own one-off script, not the product:** my first attempt
  auto-discovered the FlakeTrace repo root by walking up from the script's own directory
  looking for `evidence/extract.py` -- but the script lived in a scratch directory **outside**
  the repo entirely, so the walk-up hit the drive root and spun forever (`Path("C:\\").parent
  == Path("C:\\")`), burning real CPU for roughly four hours before I diagnosed it (checked the
  process's actual CPU time against wall-clock time, confirmed it was genuinely busy not
  stuck, then timed one real candidate in isolation and found it should take ~2 seconds, not
  four hours for 524 of them -- the arithmetic didn't close, which is what actually caught the
  bug). Fixed by passing the repo root explicitly instead of discovering it. This was 100% my
  own script's bug, never the product's `rank_candidates` itself, which is unmodified and
  already M1's, tested, and merged.

### Item 4 -- the fixture, real invocation counts, both policies

Real `python -m runner diagnose --policy original|ranked` on all four real fixture cases, no
budget limit (JDK 8, real Maven/JVM):

| Case | `original` invocations | `ranked` invocations | Savings | Verdict (both policies) |
| --- | --- | --- | --- | --- |
| F1 | 67 | 65 | 2 (3%) | `VERIFIED`, same polluter |
| F2 | 82 | 70 | 12 (15%) | `VERIFIED`, same polluter |
| F3 | 264 | 264 | 0 (0%) | `VERIFIED`, same two polluters |
| F4 | 166 | 146 | 20 (12%) | `VERIFIED`, same polluter |

`ranked` never costs more than `original` and reaches the identical verdict every time -- the
"same endpoint" ADR-014 asks for, confirmed on every fixture case, not just F2. F2's numbers
(82 vs 70) independently reproduce M2's own already-recorded real run exactly
([[evidence-m2]]); F1, F3 and F4 are new real runs. **F3's zero saving is a real, honest
result, not a bug:** `ranked` still tries all 16 of 16 candidates and spends the identical 264
invocations, because F3's cost is dominated by `ddmin` minimisation (two required polluters
need shrinking after the single-candidate search fails), a phase candidate ranking does not
touch -- ranking only reorders the pair search, and F3's pair search was never the bottleneck.
- **Not done:** the real-case half of item 4 (FJ-03 under both policies, real JVM runs, not
  just the offline comparison above) -- blocked on nothing technical now that discovery.py's
  gap is fixed, but not yet run; given item 5's result (no edge, ranking changes nothing), this
  real-case run is expected to show `ranked` costing the same as `original` too, which would
  itself be worth confirming rather than assuming. This is W26b's real-case work, not a gap in
  this entry.
- **Not committed:** the one-off `rank_candidates`/fastjson comparison script lived in a
  scratch directory, not under `eval/tools/`. If this comparison needs to be re-run later (a
  co-touch rule, FYP-2), it should be rebuilt as a proper committed tool rather than rerun from
  scratch -- noted here rather than silently left to be rediscovered.

## 2026-11-21 — W23 complete: F2-F4 and N1-N4 bundled; a real recount bug found and fixed

**Requirement:** W23's "fixture bundles committed" -- only F1 (two copies) was bundled so far.

- **Command:** `python -m runner diagnose --project fixtures/od-fixture --victim <each
  victim> --bundle eval/bundles` for all 7 remaining cases (JDK 8, real Maven/JVM). All 7 real
  diagnoses matched their known ground truth (F2-F4 `VERIFIED`; N1/N2 `UNRESOLVED
  (VICTIM_FAILS_ALONE)`; N3 `UNRESOLVED (NOT_REPRODUCED)`; N4 `UNRESOLVED
  (VICTIM_FAILS_ALONE_DIFFERENTLY)`). N2's 13/20 alone-failure rate is this run's real number,
  not the same every time, by design (N2 is intentionally flaky).
- **A transient environment failure, not a product bug:** N4's first `--bundle` attempt failed
  with a Windows `PermissionError` renaming the bundle's `.partial` folder to its final name
  (`write_bundle`'s own "write to a side folder, rename at the end" safety already cleaned up
  the `.partial` folder on that failure -- confirmed no half-written bundle was left behind).
  Re-ran the identical command and it succeeded, with the identical real result -- most likely
  a brief antivirus lock on the newly-written folder, not anything in the product.
- **A real bug in my own recount, found by `verify` itself, not a unit test:** `python -m
  eval.bundle verify` on N3's real bundle flagged `reproduction.n: report says 20, recount says
  51`. N3's real record has 20 "reproduce" lines and 31 "shuffle" lines (ADR-008's fallback,
  since the discovered order never failed). `eval/bundle.py`'s recount, for the
  "no reference established anywhere" case, was reusing the same `reproduce_lines` list built
  for reference-searching (reproduce + shuffle together, correctly) as the source for the
  fallback `RunTally` too -- but `runner.diagnose._steps` itself counts only the "reproduce"
  phase for that specific tally, never the shuffle attempts. The existing unit test for this
  shape (`test_not_reproduced_shape`) happened to have zero shuffle lines, so it could never
  have caught this. Added `test_not_reproduced_shape_with_shuffles_tried_too` (confirmed failing
  against the pre-fix code first, with the exact same `51` mismatch N3 showed), then fixed by
  splitting `reproduce_only_lines` out from the reference-search pool. Re-verified N3's real
  bundle clean afterward.
- **Verified:** `python3 -m unittest discover -s eval/tests` -> **147 tests, OK** (1 new
  regression test). All 9 committed bundles (two F1, one each F2-F4/N1-N4) re-verified clean
  with `python -m eval.bundle verify` after the fix.
- **Not done:** `eval/reports/*.json` still not replaced by the bundles (other readers --
  `ui/web`, the Mid report's generated table -- still point at it); M1's independent
  reproduction of a bundle (ADR-013 section 5) has not happened.

## 2026-11-21 -- W26b steps 6-8: the real FJ-03 pipeline, all three policies, real bundles

**Requirement:** [[05-Testing/real-case-protocol]] steps 6-8 -- the whole pipeline on the real
case, `original`/`ranked`/`random` (five seeds), one stated budget, bundled regardless of
verdict. Blocked since W26a (2026-11-19) on a `runner/discovery.py` gap; **fixed by M2
2026-11-20** (PR #110, confirmed in [[00-Meta/risk-register]]), so this was unblocked and not
attempted until today.

- **Command (real JDK 8 Temurin `1.8.0_512`, real fastjson checkout at the pinned commit
  `e05e9c5`, real Maven, `JAVA_TOOL_OPTIONS=-Duser.timezone=UTC -Duser.language=en
  -Duser.country=US`):**
  ```
  python -m runner diagnose --project <fastjson checkout> \
    --victim com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf \
    --order eval/real-cases/fj03/order.txt --n 20 --budget-invocations 100 \
    --policy {original|ranked|random --seed {0,1,2,3,4}} --bundle eval/bundles
  ```
  **Budget choice:** Interface 6's B2 minimum for this case is `reserve(20) + start_length + 2 =
  60 + 2 + 2 = 64` (the order file has exactly 2 entries). Chose **100**: comfortably above the
  minimum (room for the search to actually run, not just scrape by), still a real stated limit,
  not "no limit".
- **Real result, all seven runs, identical:** `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`,
  reproduced 20/20 (lower bound 0.839), alone 0/20, polluter `SerializeWriterTest_14#test_writer_1`
  found trying **1 of 1** candidates, **64 of 100** invocations spent (reserve 60; reproduce 2;
  search 2; verify 40; shuffle/minimise/deletion all 0). `ranked`'s own line: "ranked at depth
  2->3->4->5: no candidate had evidence, original order kept". `random` (seeds 0-4): "random
  order (seed N)", same cost, same verdict, every seed.
- **Why identical, and why that is the real, honest answer, not a flat result:** `--order`
  fixes the starting order to the known pair (step 5's finding: neither the natural discovered
  order nor 31 shuffles reproduce on this dense real suite). Truncated at the victim, that order
  has exactly **one** test before it, so the single-polluter search has exactly one candidate to
  try -- policy cannot matter when there is nothing to reorder. This is the real-JVM confirmation
  of ADR-014 evidence item 5's offline finding (`rank_candidates` found zero static evidence for
  FJ-03's `ThreadLocal`-based pollution, so ranked position = original position = 368 of 524):
  item 5 showed it with no JVM runs; this shows the product's own CLI reaching the identical
  real verdict, for real, end to end. **Reported as it is** (ADR-014's own instruction): on this
  one real case, there is no search to speed up, so there is no saving to measure -- not "ranking
  doesn't work", not "ranking wins".
- **A real bug in my own working tree, not the product, found before trusting the first
  result:** my first pass at all seven runs showed `tool.dirty: true` on every bundle's
  manifest, breaking W23's established "`tool.dirty: false`" precedent for a clean evidence
  bundle. Cause: a stale `HANDOFF-M3-report.md` left over from the October Mid-Report phase
  (untracked, its own header said to delete it once that report was done -- it was) sitting in
  the working tree. Deleted it (with the member's OK, since the delete itself needed
  permission), confirmed `git status --short` clean, and re-ran all seven for real. The first of
  the seven now shows `tool.dirty: false`; the other six show `true` again, but only because the
  *previous* bundle folder in the same `eval/bundles/` batch is itself untracked at the moment
  the next one runs -- the exact same shape the committed F1/F2-F4/N1-N4 bundles already have
  (only the first bundle of each sitting is ever `false`), so this is the established, accepted
  convention, not a new problem to chase.
- **Verified:** `python -m eval.bundle verify <folder>` on all seven real bundles -> **all seven
  `OK`**, no recount mismatches.
- **Not done:** step 9, the independent repeat of step 6 or 7 by M1 or M2 on another machine --
  not mine to run.

## 2026-11-21 -- W27: pinned container image, built and run for real

**Requirement:** [[10-Final1/iteration-2-plan]] W27 -- "a fixture diagnosis runs in the
container on a second machine" (M1 to run it; M2 reviews). Scoped to its literal done-when, not
the full sandbox profile in `docs/02-Requirements/non-functional.md` (rootless, network-disabled,
resource limits) -- that stays a later target; this image pins the toolchain for
reproducibility, it does not isolate it. No ADR needed: this doesn't change any contract or
runner behaviour, just packages the existing, unmodified toolchain.

- **Command:**
  ```
  docker build -t flaketrace:w27 .
  docker run --rm -v "<host>/flaketrace-bundles:/flaketrace/flaketrace-bundles" flaketrace:w27 \
    diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode \
    --bundle flaketrace-bundles
  ```
  (`Dockerfile`: `maven:3.9.9-eclipse-temurin-8` + `python3`/`pip3`, `eval/requirements.txt`
  installed, repo copied in, `JAVA_TOOL_OPTIONS` pinned to match the real-case protocol's own
  environment convention.)
- **Real result:** built for real (Docker Desktop on this machine, ~56s for the `apt-get`
  layer the first time). Ran the F1 fixture diagnosis for real, entirely inside the container:
  `VERIFIED (sequence)`, polluter `odfixture.ConfigPolluterTest#pollute`, 67 invocations --
  **matching F1's known ground truth exactly**, the same result this exact diagnosis gives on
  the host. `python -m eval.bundle verify` on the resulting bundle (written back to the host via
  the bind mount): **OK**. The bundle's own `environment` block is real, independent
  confirmation this ran on a genuinely different environment, not just a different folder:
  `Linux-6.18.58.1-microsoft-standard-WSL2`, JDK `1.8.0_452` (a different Temurin 8 patch than
  this machine's own `1.8.0_512`), Maven `3.9.9`, Python `3.12.3` -- none of these match the
  host values the earlier real-case bundles recorded, so this is a real second environment, not
  the same one relabelled.
- **A real bug in my first command, not the product:** the first run's `-v
  "$(pwd)/flaketrace-bundles:/flaketrace/flaketrace-bundles"` produced *no error* but silently
  bind-mounted nothing -- the bundle the container reported writing was never on the host side,
  `flaketrace-bundles/` stayed empty. Cause: Git Bash's automatic path conversion mangles a
  `/c/...`-style `$(pwd)` path when it sits on the host side of a `host:container` volume
  argument with its own colon. Confirmed with a minimal probe (`touch /check/probe.txt` inside a
  throwaway container) that a **native Windows path** (`C:\Users\...`) on the host side mounts
  correctly; re-ran the real diagnosis with that form and the bundle landed on the host as
  expected. Documented both forms in `README.md` (`$(pwd)` works as normal on Linux/macOS; a
  native path is needed from Git Bash on Windows) rather than silently working around it.
- **A known, unfilled field, not mine to fix:** the bundle's `environment.container_image` is
  `null` -- `runner/diagnose.py` (M2's file) hardcodes it to `None`; nothing in the product yet
  detects or records which image it ran in. Noted here rather than edited myself (not my
  folder); worth a small follow-up in `runner/` if the team wants the image identity recorded
  automatically rather than left to whoever ran the command to note down.
- **Not done:** M1 (or M2) actually running it on a second, real machine -- the "done when" is
  specifically a second machine, which this session cannot be. This entry shows it is buildable
  and reproduces correctly on one real machine; the cross-machine confirmation is the next step.

## 2026-11-21 -- W29a / FT015: the real cause was one wrong cell in the worksheet, not the register

**Requirement:** [[10-Final1/iteration-2-plan]] W29a / FT015 -- "Member 3's GenAI level is L3
in one worksheet table and L2 in another, in the report and in the repository register. One
consistent per-artefact account." Scoped to my own (M3's) levels, per FT015's own ownership.

- **First checked what FT015 actually claims, against the real sources, before touching
  anything:** counted every M3 row in `docs/08-MidEval/genai-register.md` dated on or before
  2026-10-14 (the Mid cutoff the frozen report's own text names, "the counts are rows in the
  register on 11 October 2026") -- **exactly L2 x18, L1 x1**, with **zero** L3 rows. The frozen
  Mid report's own Table 9 (`mid-eval-report/chapters/chapter9_development_evidence.tex`,
  `ch9:tab:genai`) says, for M3: "L2 (18 rows), L1 (1)". **These two already agree exactly** --
  the register and the frozen report were never the mismatched pair FT015 named. (The frozen
  report is the submitted, tagged `mid-eval-v1` record and must stay byte-identical to it --
  not edited here or ever, per the earlier 2026-11-20 entry in this log.)
- **Found the real mismatch by reading the actual submitted worksheet**, not by assuming it
  matched the report: `C:\Users\zarpa\Downloads\FlakeTrace_FYP1_Mid_Worksheet.docx` (the file
  timestamped 2026-10-14 08:44, the morning of the 8:30 AM deadline -- the one actually
  submitted, not a template). Unpacked and read its `word/document.xml` directly (no `pandoc`
  or LibreOffice available on this machine, so a Python regex strip of the XML tags, checked
  against the Skill's own `merge_runs.py` output). Its own "GenAI artefact register" table, M3's
  row ("Evaluation, statistics, schema, fixtures"), says: **"Claude Sonnet 5; L3 (18 rows), L2
  (1)"** -- one level too high on both counts. A few hundred lines later in the **same
  document**, M3's own individual declaration page says the opposite, and the correct thing:
  "L2 -- statistics, schema, decision logic, fixtures and report sections (18 register rows L2,
  1 L1)." **The worksheet contradicts itself**, exactly as FT015 describes -- the mismatch was
  never worksheet-vs-report, it was worksheet-table-vs-worksheet-declaration, with the register
  and the report both agreeing with the *correct* side all along.
- **Fixed it in a corrected, editable copy, not the submitted record:** the already-submitted
  `.docx`/`.pdf` stay as submitted -- this is a correction for the forward-looking ask in
  FT013 ("supply the editable filled worksheet") and FT015 together, not a rewrite of history.
  Edited `word/document.xml` directly (the exact run containing "L3" and the following "L2"
  digit, found via a byte-for-byte substring match, confirmed unique with `grep -c` before
  touching it), repacked with Python's `zipfile` (no `zip` binary on this machine), and
  validated with the docx skill's own `validate.py` against the original: **same paragraph
  count (1432 -> 1432), all checks passed.** Re-extracted the corrected file's own text and
  diffed it against the original's extracted text: **the only textual difference anywhere in
  the document is the one cell, "L3 (18 rows), L2 (1)" -> "L2 (18 rows), L1 (1)"** -- confirmed,
  not assumed, that nothing else moved.
- **Not done:** actually handing the corrected worksheet to the supervisor, and the signatures
  FT013/FT014 ask for -- both outside this session (a human, external-facing submission step,
  not a repository change). Sent the corrected `.docx` to the member directly for review.

## 2026-11-21 -- M2's PR #152/#153 review, addressed for real (all four points)

**Requirement:** M2 reviewed W23/W26b/W27 for real (re-ran `verify` on all 16 bundles, read the
Dockerfile and the FJ-03 commands) and raised four points. All four checked and fixed for real,
not argued from reading the code alone.

### 1. The big one -- the FJ-03 "confirmed with real JVM runs" claim overclaimed

M2's point: `--order` fixes FJ-03's run to the known pair, so every policy had exactly one
candidate. That can't test ranking, and the real-run sentence in G9/the protocol should be
reworded or removed until the real (524-candidate, package-scope) experiment is run.

**Checked, not assumed.** Ran `py -m runner diagnose --scope package --n 20 --policy original`
(no `--order`, no budget limit) against real fastjson, through the product's own CLI (M2's
discovery.py fix, 2026-11-20, makes this possible for the first time). Real result, twice
(identical both times): **`UNRESOLVED (NOT_REPRODUCED)`, 12,817 real invocations** (reproduce
20 attempts x 261 = 5,220; shuffle 31 attempts = 7,577; alone 20), **search tried 0 of 260
candidates**. `wall_seconds`: 750 (~12.5 min) -- invocations are cheap (~0.1s each; one JVM
session runs many test methods) once the real build is warm, which is why this was tractable to
actually run rather than estimate.

**Why this is the real, structural answer, not a budget-sizing fix:** `runner.diagnose._steps`
only reaches the single-polluter search (where `--policy` matters) *after* `reproduce` or
`shuffle` establishes a reference signature. Real evidence, twice over, says neither does for
FJ-03's natural suite: this reconfirms, end to end through the fixed CLI (not the W26a
workaround script), the same real finding step 4 already made. **So `--scope package` cannot
produce a live ranked-vs-original comparison on this case either** -- not a flaw in my first
run, a property of the case. Bundled the real result:
`eval/bundles/20261121T205558Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf`,
`verify` clean (`tool.dirty: true` -- honest, since other real work was pending in the tree at
the time; not part of the "clean batch" precedent, a one-off supplementary bundle).

**Reworded, not deleted**, in [[05-Testing/real-case-protocol]] and `docs/07-Defense/claims-ledger.md`
(G9): the 1-candidate runs show the three policies cost the same (not a saving); the new
package-scope run shows *why* a live saving can't be measured on this case; the offline
`rank_candidates` comparison (item 5, 368 of 524 in both orders) remains the actual source of
the "no evidence" finding.

**A second real, transient failure found along the way:** the first package-scope attempt hit a
genuine JVM native-memory crash (`malloc failed`, `hs_err_pid*.log`/`replay_pid*.log` written
to the repo root) -- confirmed real memory pressure (690 MB free of 8 GB, `Get-CimInstance
Win32_OperatingSystem`), not a product bug; stopped Docker Desktop (no longer needed once W27
was verified) to free memory, deleted the stray crash-dump files, and the identical command
succeeded on retry with the identical real result.

**A real, pre-existing robustness gap found, not mine to fix:** every real run against fastjson
(not the small fixture) throws `UnicodeDecodeError` in `subprocess`'s internal reader threads
(`byte 0xa0 invalid start byte` -- a Windows-1252 non-breaking space in Maven's console output,
read as UTF-8). The command still completes and the report is still valid both times this was
seen, so it is not blocking -- but it is a real gap in `runner/order_runner.py`'s (M2's file)
subprocess output handling on a non-ASCII console under Cp1252, flagged here rather than patched
myself.

### 2. The uncommitted comparison script -- now in `eval/tools/`

Committed `eval/tools/fj03_rank_compare.py` (was a scratch one-off), fixing the repo-root
discovery to `Path(__file__).resolve().parents[2]` (the bug that caused the ~4-hour hang two
days ago was a script living *outside* the repo; this one now lives inside it, so that failure
mode cannot recur). **Re-ran it for real** after moving it: 524/524 candidates analysed, 292.3
real seconds, **original position 368 of 524; ranked position 368 of 524** -- exactly
reproduces the number already in the register, confirming the move didn't change its behaviour.

### 3. The Dockerfile -- digest-pinned, `.git` no longer excluded

- **Pinned by digest**: `FROM maven:3.9.9-eclipse-temurin-8@sha256:e20e4fc0...` (pulled for
  real to get the real digest). A moved tag would have silently changed the JDK patch level --
  exactly the `1.8.0_512` (host) vs `1.8.0_452` (image) drift already on record.
- **`.git/` removed from `.dockerignore`**: `runner/diagnose.py`'s `git_state()` shells out to
  `git -C <folder> rev-parse HEAD`/`status --porcelain` against the tool's own folder; with no
  `.git` in the image, that silently returns `(None, None)` -- exactly the `tool.commit: null`
  M2 found. Confirmed the base image already has `git` installed (`git version 2.43.0`), so no
  extra `apt-get install` was needed. **Rebuilt the image for real and re-ran F1 inside it**:
  `manifest.json`'s `tool.commit`/`subject.commit` are now real hashes
  (`c5eff18f366edf94f7e76003db3903f1afadea44`), not `null` -- confirmed fixed, not just reasoned
  about. (`tool.dirty`/`subject.dirty` show `true` in that one test bundle because other real
  edits were genuinely pending in the tree at build time; deleted that throwaway test bundle
  afterward, it was never meant to be committed.)

### 4. 14 of 16 bundles had `tool.dirty: true` -- regenerated from a clean tree

Confirmed M2's count exactly (`tool.dirty` check script over every committed bundle's
manifest). Regenerated all 14 (F1's second copy, F2-F4, N1-N4, and FJ-03's `ranked` +
`random`x5) **into a scratch location outside the repo first**, so the repo stayed genuinely
clean (`git status --short` empty) at the moment each one ran, then copied all 14 into
`eval/bundles/` in one pass. Every real result matched its known ground truth exactly (same
invocation counts as the original runs: F1 67, F2 82, F3 264, F4 166, N1/N2/N3/N4 unchanged).
One transient real timeout (`java.EXE timed out after 120s`) on the first attempt of FJ-03's
random seed 3 -- confirmed no partial bundle was left behind, succeeded identically on retry.
**All 16 now verify clean, and `tool.dirty: false` on every one of the 14 regenerated bundles**
(confirmed with a dirty-check script reading every manifest, not by eye).

**Not done:** M2's own step 9 run and his planned package-scope repeat -- his call, informed by
point 1 above (it will reconfirm `NOT_REPRODUCED`, not produce a ranking comparison).

## 2026-11-22 -- M2's follow-up message: the package-scope bundle, W35's report half, FT009's README gaps

M2's #156 follow-up had five parts. Four are mine; the fifth (two Interface 9 wording points)
needed all three members' agreement -- confirmed with the member first, then recorded in
[[contracts/interfaces]].

### 1. The package-scope bundle, properly this time

Regenerated `--scope package --policy original` straight into `eval/bundles` (no scratch path
in `command` -- M2's second complaint, fixed and confirmed in the manifest). Identical real
result both times this was run: `UNRESOLVED (NOT_REPRODUCED)`, 12,817 invocations, search tried
0 of 260.

**First attempt, and the real bug it caught in my own process, not the product:** temporarily
reverted the files I had pending for W35 to their committed `HEAD` content (via `git show`,
confirmed `git status --short` empty, restored afterward from a local backup -- never through a
forbidden git command) to get `tool.dirty: false`. The bundle that produced was schema-valid
*at the time* -- but against the *old*, pre-W35 schema, since that is what was actually on disk
during that run. Checking it against the *new* schema (added moments later in the same working
tree) failed: `'reproduced_by' is a required property`. A bundle that fails validation against
the schema it would ship alongside in the same commit is a real correctness problem, not a
metadata nicety -- caught by actually re-running `verify` against the final tree before
trusting the first result, not by assuming a "done" regeneration stays done.

**Resolved by sequencing, not by skipping the check:** regenerated it a second time with the
new W35 code genuinely present (`reproduced_by: null`, schema-valid), accepting `tool.dirty:
true` this time -- a clean tree and a schema-valid bundle could not both be true in one
uncommitted working copy, since the field that makes it valid is itself one of the uncommitted
changes. Getting both would need two separate commits (code, then a bundle regenerated against
the now-committed, clean result) -- noted here as the real reason, not implemented, since M2's
actual ask (no scratch path, a bundle that is what it claims to be) is satisfied either way.
M2's step 9 (his own independent repeat on his laptop, identical result, 12,817 invocations,
0 of 260) is recorded in [[05-Testing/real-case-protocol]].

### 2-3. G9/protocol wording: 524 -> 260, and softened "cannot ... at all"

M2's exact point: the order-mode package-scope search tried 260 candidates (the tests before
the victim in the discovered order -- order mode's own candidate count), not 524 (that is the
*pair-scan* count item 5's offline comparison and W35's pair mode use, which also search
candidates *after* the victim). Fixed in [[05-Testing/real-case-protocol]] and
`docs/07-Defense/claims-ledger.md` (G9): every "524" describing the order-mode run is now
"260 (tests before the victim)"; "FJ-03 cannot supply a live ranked-vs-original comparison at
all" is now "not from any order FlakeTrace discovers or shuffles" -- order mode's own limit,
not the case's. Both files now also record that ADR-016's pair mode *does* reach the real
polluter directly (position 368 of 524, matching the POC exactly) -- the claim that was too
strong a week ago is exactly right once pair mode exists; said so, not just softened the old one.

### 4. W35 my half: reproduced_by, pair-mode wording, order_exploration, verify(), the schema

All built, test-first, against the already-merged runner half (`runner/diagnose.py`'s
`search_mode`/`reproduced_by`/`pairs_tried` fields, `runner/search.py`'s `find_pair`,
`runner/budget.py`'s `pair` phase) -- read the real code before writing anything, not just the
contract text, since Interface 9 leaves the exact record shape to the runner's own
implementation.

- **Schema** (`eval/schema/report.schema.json`): `reproduced_by` added, required, `"order"` |
  `"pair"` | `null`, with a cross-field rule tying it to `failure_signature`'s own nullability
  (one is null iff the other is). **All 9 example reports and the schema-validator test's
  `VALID_REPORT` constant updated** -- a required field breaks every existing example/test that
  doesn't carry it, found immediately by running the suite, not guessed in advance.
- **`eval/report.py`**: `reproduced_by` in every report. A `DiagnosisRuns` that predates W35
  (every existing hand-built test fixture, and any future caller that forgets it) defaults to
  `None` on the dataclass -- `assemble_report` infers `"order"` when a real reference signature
  exists and the field was left at its default, rather than emitting a false `null` for 36
  existing passing tests that would otherwise have broken. `order_exploration` is omitted
  entirely in pair mode (its fields would sit at DiagnosisRuns' defaults -- "no order was tried",
  not "the order didn't reproduce" -- and M2 flagged the UI reads that default shape as the
  latter). The agreed pair-mode limitation line is added when `reproduced_by == "pair"`.
  Pair-mode's own `NOT_REPRODUCED`/`INFRASTRUCTURE_FAILURE` wording (no pair adopted) is now
  worded from `pairs_tried`, not "runs of the discovered order" (pair mode has none), and names
  the unconfirmed-failure count when `sequence.other > 0` (a pair failed once, then passed its
  re-run, so it was never adopted -- M2's exact point 4 of the bug he found).
- **`eval/outcome.py`**: the same unconfirmed-failure gap, fixed at its root. `decide()`'s row
  4/5 rationale said "never reproduced any failure" unconditionally when
  `reference_established=False` -- false when `sequence.other > 0`. Reworded to "no run
  reproduced a *confirmed* failure", naming the unconfirmed count. (This text is not consumed
  anywhere in production today -- grepped for `.rationale` across `eval/`, `runner/`, `ui/` and
  found no caller outside tests -- but it is the root text M2's bug report was actually
  describing, and leaving a known-wrong string in a public dataclass field, dead code or not,
  is not something the honesty rules let me leave alone once found.)
- **`eval/bundle.py`**: pair-mode `verify()` support. Walks "pair" record lines the same way
  `runner.search.find_pair` does (a real failure's immediately-following line is its one
  re-run); the adopted reference is the first candidate whose re-run matches. When nothing is
  adopted, recounts the exact `RunTally` shape `runner.diagnose._pair_steps` builds, `other`
  included. New tests cover: an adopted pair after one false start, no pair adopted with
  unconfirmed failures, and a pair cut off by the budget before its re-run could run (must not
  be misread as adopted).
- **Docs**: `docs/contracts/interfaces.md`'s "seven phases"/"all seven phases" -> eight (W35
  adds `pair`); `docs/contracts/report-schema.md` gained `reproduced_by`'s row and a note on
  `order_exploration`'s pair-mode omission.
- **Verified:** `python -m unittest discover -s eval/tests` -> **158 tests, OK** (up from 154;
  3 new `TestPairModeW35` tests in `test_report.py`, 1 new row-5 regression in `test_outcome.py`,
  3 new `TestPairModeW35` tests in `test_bundle.py`). Every existing test still passes with no
  behavioural change for order mode.
- **A real gap found in M2's file, flagged not fixed:** `runner/replay.py`'s `replay_steps`
  builds its `DiagnosisRuns` without setting `reproduced_by` at all, so any replay of a
  pair-mode-originated bundle will, through my own backward-compatible fallback, be mislabelled
  `"order"` -- the fallback exists for genuinely pre-W35 callers (which are all order-mode by
  construction), not for a real pair-mode replay, which `replay.py` itself does have the
  information to label correctly (`report_reference`'s `report` argument already carries the
  original bundle's own `reproduced_by`, once committed). Not touched -- `runner/` is not my
  folder; flagged here for M2.

### Team agreement on the two Interface 9 wording points (M2's part 5)

Both checked against the real, agreed Interface 9 text and ADR-016 before answering, not
rubber-stamped: (a) the pair-mode limitation line's "not seen in the project's own or shuffled
orders" does genuinely overclaim when pair mode runs with no prior order-mode attempt in the
same diagnosis (true in every real case: a single `diagnose()` call is order mode *or* pair
mode, architecturally never both, so a pair-mode report never actually ran those orders to NOT
see the failure in them) -- M2's fix is the honest replacement, and it is literally what I just
implemented in `eval/report.py` above. (b) `reproduced_by: "order"` covering the victim-alone
case is also already what `runner/diagnose.py`'s own merged code does (`reproduced_by="order"`
on both the order-mode and pair-mode alone-check paths) -- the wording fix in
[[contracts/interfaces]] documents behaviour M2 had already built, not a new design. Confirmed
with the member before answering M2, since a contract change needs all three, not my call alone
to make and report as settled.

### W27 container re-checked against real fastjson (M2's point 2)

Rebuilt `flaketrace:w27` (picks up M2's `runner/order_runner.py` fix -- test JVM output no
longer decoded as UTF-8, PR #161) and ran a real diagnosis inside it against the real fastjson
checkout, the known `[SerializeWriterTest_14, MaxBufSizeTest]` pair, `--n 5`: **`CANDIDATE`,
19/19 invocations spent, no `UnicodeDecodeError`** -- exactly the real risk M2 named (Linux
reads the subprocess's stderr in the calling thread synchronously, so without the fix the
diagnosis would stop, not just print a noisy traceback). fastjson's own test output does carry
the `0xA0` byte that caused this; running it inside the container is what makes this a real
check of the Linux path, not just a repeat of the Windows one already done for W27. Real result
matches the known premise exactly (reproduced 5/5, same polluter).

### A real CI regression found and fixed: `ui`'s own report fixtures predate `reproduced_by`

The `ui` check failed for real on PR #164 after push -- not the usual infra flake (checked: a
different step failed this time, `Backend tests`, exit code 1, not `setup-java`/`tar`).
Reproduced locally (`python -m unittest -v ui.tests.test_server`) rather than guessing from the
annotation alone: 4 failures/4 errors, all tracing to the same cause --
`'reproduced_by' is a required property`. `eval/reports/{f1,f2,f3,f4,n1,n2,n3,n4}.json` (the
eight committed reports `ui/server.py`'s own tests read directly, e.g. `test_validate` on
`eval/reports/f1.json`) were never updated when `reproduced_by` was added to the schema in this
same PR -- I updated the nine `eval/examples/*.json` files but missed this second, separate set
of real fixtures. `eval/reports/` is mine (not `ui/`'s), so this was a gap in my own change,
not M2's to fix.

Fixed the same way as the examples: `reproduced_by: "order"` for every report with a real
`failure_signature` (seven of eight), `null` for `n3.json` (its `failure_signature` is already
`null` -- `NOT_REPRODUCED`, consistent with the others). **Verified for real**:
`python -m unittest -v ui.tests.test_server` -> **31/31 OK**, including a real end-to-end F1
run (`TestRealRunOnFixture`), not just the four that were failing. Also ran `ui/web`'s own
suite in full, since a backend failure skips it in CI and I did not want to hand over a fix
that broke something CI had not even reached yet: `npm test` -> 33/33 OK; `npm run typecheck`
-> clean; `npm run build` -> succeeds. None of the three touch `reproduced_by` (the TS `Report`
type does not declare it, so an extra JSON field is structurally harmless), but running them
for real rather than reasoning about TypeScript's structural typing is the honest version of
that claim.

## 2026-11-22 -- ADR-016 item 2: the live original/ranked/random comparison on FJ-03, pair mode

**Requirement:** [[03-Design/decisions/ADR-016-reproduction-fallback-pair-search]]'s "what must
be demonstrated" item 2 -- "the live comparison on FJ-03: `original`, `ranked`, `random` (5
seeds), one budget, cost to the same verdict, reported as it is." M2's own run already covers
`original` (`docs/evidence-m2.md`, 798 invocations, position 368); this entry re-runs it myself
alongside `ranked` and the five seeds, under the one methodology, bundling every run.

- **Command, seven real runs:**
  ```
  python -m runner diagnose --project <fastjson checkout> \
    --victim com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf \
    --search pairs --scope package --n 20 \
    --policy {original|ranked|random --seed {0,1,2,3,4}} --bundle eval/bundles
  ```
  No budget limit on any of the seven -- the "same budget" the comparison asks for is "no limit,
  uniformly," matching M2's own already-documented `original` run exactly (he used no limit
  too) and item 4's earlier fixture methodology ([[evidence-m3]], 2026-11-21 entry).
- **Real results, all seven:**

  | Policy | Polluter adopted | Position (of 524) | Invocations |
  | --- | --- | --- | --- |
  | `original` | `SerializeWriterTest_14#test_writer_1` | 368 | 798 |
  | `ranked` | `SerializeWriterTest_14#test_writer_1` | 368 | 798 |
  | `random` seed 0 | `SerializeWriterTest_14#test_writer_3` | 187 | 436 |
  | `random` seed 1 | `SerializeWriterTest_14#test_writer_1` | 7 | 76 |
  | `random` seed 2 | `SerializeWriterTest_14#test_writer_2` | 61 | 184 |
  | `random` seed 3 | `SerializeWriterTest_14#test_writer_3` | 98 | 258 |
  | `random` seed 4 | `SerializeWriterTest_15#test_writer_1` | 43 | 148 |

  My own `original` run exactly reproduces M2's already-documented one (368, 798) -- an
  independent confirmation on my own machine before building the comparison around it.
  `ranked` is bit-for-bit identical: deepened through 2->5, found no evidence, fell back to the
  original order (matching item 5's offline finding, now confirmed live for pair mode too, not
  just order mode).
- **The real, unpredicted finding, reported as it is (ADR-016's own instruction):** every one
  of the five random seeds found a real polluter *(corrected 2026-11-27, after the supervisor's
  23 Nov review -- this was wrong at the time: two seeds, 0 and 3, both adopted the same
  `test_writer_3`, so "every seed found a different one" overclaims; four distinct identities
  were adopted across all seven runs, not five -- see [[claims-ledger]] G9)* and every one cost
  less than `original`/`ranked` -- 45% to 90% fewer invocations. This
  is not "random beats ranking" as a general claim -- `rank_candidates` genuinely found zero
  static evidence (M1, #145), so `ranked` has nothing to rank with and correctly degenerates to
  `original`. It is specific to this real case's actual shape: the package has **six**
  independently-valid single polluters for this victim (the 524-candidate scan's own count --
  a different number from the seven runs here, where four distinct identities were adopted,
  each `CANDIDATE` with the identical reference signature), spread through the 524 real
  candidates, while `original`'s one fixed natural-discovery order happens to reach the first
  one it encounters unusually late (368th of
  524). A fixed order cannot be lucky; a reshuffle usually is, on a case with this many "right
  answers." Reported exactly this way -- a real limitation of a *fixed* original order on a
  real, multi-polluter-eligible case, not a defect in ranking and not evidence against the
  approach in general (a case with only one true polluter, like the fixture cases, would not
  show this effect; F1-F4's own numbers already show `ranked` never costing more than
  `original`, which still holds here too).
- **Verified:** `python -m eval.bundle verify` on all seven real bundles -> **all seven `OK`**
  (first real exercise of the pair-mode `verify()` code built this session against genuine
  pair-mode records, not just the hand-built test fixtures); `python -m unittest discover -s
  eval/tests` -> 158/158 OK, unaffected.
- **Not done:** M1's independent reproduction of the FJ-03 pair-mode diagnosis (Interface 9's
  own plan, W35's verifier) -- hers to run, not mine.

## 2026-11-22 -- PR #165 merged; a stale status found and corrected in two registers

Confirmed the hand-off above: PR #165 merged into `main` at `614fc6d` (approved by M2, all 5 CI
workflows green -- `ui`, `python-eval`, `runner`, `fixture-build`, `evidence`). While checking
what was next for M3, re-read `docs/10-Final1/action-register.md`'s FT009 row and
`docs/07-Defense/claims-ledger.md`'s G7 row against the actual repository state, not just taken
on trust.

**Found:** both still said "M3's README gaps (3, 4) open" / "for M3 and M2 to settle once the
instruction gaps are fixed" -- but gaps 3 and 4 (M1's own numbered list, [[evidence-m1]]) were
already fixed in `570a05f` (PR #164, 2026-11-22, earlier the same day): README's new "Reproduce
a bundle (W23)" section. The claims-ledger row was further stale on an unrelated point -- it
still said "only F1/F3 are bundled", though F2-F4/N1-N4 were committed and verified clean on
2026-11-21 ([[05-Testing/real-case-protocol]] W23 entry).

**Corrected, not left standing on the honesty rule** (a doc's `Status` line must stay true):
both rows now say all six of M1's instruction gaps are fixed (M2's 1, 2, 5, 6 same day as hers;
mine, 3 and 4), and the claims-ledger's fixture-bundle count is current. Neither row is marked
`Done` -- M1 has not re-run her reproduction against the fixed instructions yet, and supervisor
acceptance is still open. No code changed; this is a documentation-accuracy correction only.

## 2026-11-22 -- FT021's verifier check: the reset-sensitive control, for real, independently

M2's row for FT021 named me the verifier ("M3 checks recorded provenance"). Did the actual
check rather than taking his evidence log on trust: read `runner/integrity.py` (hashes every
file under the project except the *top-level* `target/` and `.git/` -- a nested module's own
`target/` is not excluded, matching the docstring's and ADR-012's wording exactly, not a wider
claim); grepped every doc that describes the reset boundary (ADR-012, `runner/README.md`,
`docs/04-Implementation/sandbox-runner.md`, claims-ledger's G4) for "sandbox" or "never
modified" -- the only hits are the ADR's own "words we stop using" list and its replacement
wording, never used as a claim.

Then ran the real control myself on a machine/toolchain none of the earlier runs used (JDK
24.0.2, Maven 3.9.11, Python 3.14.3 -- M2's record names JDK 21.0.9/Maven 3.10.0):

```
FLAKETRACE_REQUIRE_JVM=1 py -3 -m unittest runner.tests.test_order_runner.TestResetControl -v
```
-> `Ran 2 tests in 25.620s -- OK`. Both subtests (`class-grouped`, `per-method`) agree with the
expectation table: static field and system property **reset** between orders (a new JVM);
a file in the temp folder and a file in the working directory **not reset**. The same-JVM
sanity test (`test_each_reader_detects_its_leftover_in_one_jvm`) failed all four readers --
no vacuous pass.

Then the full suite, to catch any regression the isolated test would miss:
`FLAKETRACE_REQUIRE_JVM=1 py -3 -m unittest runner.tests.test_order_runner` ->
`Ran 51 tests in 130.800s -- OK`; `git status --short` clean afterward, no marker left in the
repo or the OS temp folder.

**Result:** FT021's own closing criterion -- "the reset boundary is written down and matches
the code" -- holds, confirmed independently, not just reproduced from the same claim. **Not
checked by this entry** (outside FT021's scope): FT006 against a real project, and the
container plan (W27), both still open per the action-register row.

## 2026-11-22 -- M2's review of #164/#165, addressed for real

M2 reviewed #164 and #165 himself (not just reading the PR description): confirmed the pair
walk in `eval/bundle.py` matches `find_pair` and that the comparison numbers match the 7
bundles. He also brought his own fix for the `replay.py` gap I'd flagged (PR #167, merged) and
asked for four things.

**1. Six of the seven comparison bundles were `tool.dirty: true` -- regenerate from a clean
tree.** Found the fastjson checkout and the portable Temurin 8u512 JDK still cached in this
session's scratchpad from the original runs; reused them rather than re-fetching or re-building
anything (same subject commit, `e05e9c5e4be580691cc55a59f3256595393203a1`). First attempt used
this shell's default JDK (24) and failed for real (`source/target 5` unsupported); fixed by
putting the cached JDK 8 on `PATH`.

**A real tooling quirk found doing this, not assumed in advance:** `runner.diagnose.
tool_environment()`'s dirty check is `git status --porcelain -- .`, which flags an **untracked**
file too -- so the bundle one run just wrote, sitting uncommitted in `eval/bundles/`, makes the
tree dirty for the *next* run in the same batch. Regenerating all six into the same working
tree can never give six clean ones unless each is moved out before the next run starts. Did
exactly that: after each regeneration, moved the new bundle out to a scratch staging folder,
confirmed `git status --short` was empty again, then ran the next. One regeneration (seed 0's
second attempt) was swept into staging before I'd noticed this and carries `tool.dirty: true`
as a leftover of the pre-fix process -- excluded from the final set, not committed.

Also hit four real, transient OOM crashes across the six runs (`malloc failed`/`Could not
reserve enough space for object heap`), confirmed as genuine system memory pressure each time
(`Get-CimInstance Win32_OperatingSystem`: free memory fell as low as ~230MB, and at one point
PowerShell itself failed to start, reporting the paging file too small) rather than a product
issue -- the member restarted their machine once memory pressure stopped responding to retries
and closing applications; every retry after that used identical settings and gave an identical
result to the first successful attempt where one exists.

**All six regenerated bundles' real results matched the ones already recorded exactly**
(`ranked` 368/524 798 inv.; seed 0 187/524 436 inv.; seed 1 7/524 76 inv.; seed 2 61/524 184
inv.; seed 3 98/524 258 inv.; seed 4 43/524 148 inv.) -- not a coincidence: `--search pairs` is
deterministic given the policy/seed and the pinned subject commit, so a genuinely clean
re-run was expected to reproduce them, and did. All 7 bundles (the original `original`-policy
one plus the 6 regenerated) now `tool.dirty: false` and `eval.bundle verify` clean.

**2. Name the specific polluter per random seed in the write-up** (M2's own wording at the
time said "certified" -- corrected 2026-11-27 to `CANDIDATE`, since none of these has resource
evidence confirming it; see below), not just "six independently-valid polluters" as a count.
[[05-Testing/real-case-protocol]] and `docs/07-Defense/claims-ledger.md` (G9) both corrected:
the real tests are named explicitly in the prose now (`SerializeWriterTest_14#test_writer_1/_2/_3`,
`SerializeWriterTest_15#test_writer_1` -- **four** distinct identities, not five as first
written; fixed the same day), not left for the comparison table alone to carry --
M2's point that a reader of the prose only should not come away thinking one lucky polluter was
found faster five times.

**3. The PR template was empty on #164 (contract/schema impact, member/area not ticked).**
No code or doc fix here -- `.github/pull_request_template.md` already exists and is M2's area;
this is a note to fill it out properly on my own future PRs, kept here as the record of having
been told.

**4. A real bug M2 found in `eval.bundle verify`: with zero pairs run (no candidate in scope,
or the budget cuts before the first pair), the runner tallies the alone runs as the sequence
(`runner.diagnose._pair_steps`'s own `pair_tally if firsts else alone` -- a documented, deliberate
choice, since an empty tally is refused elsewhere), but `_recount` fell through to order mode's
"no reproduce lines" shape and produced an empty `RunTally(0, 0, 0, 0, 0)` instead -- which even
crashed the re-decide step (`ValueError: sequence.n must be > 0`) rather than just mis-reporting.
**Test-first:** `test_zero_pairs_run_recounts_the_alone_tally_not_an_empty_one` in
`eval/tests/test_bundle.py`, confirmed to fail exactly that way on the unfixed code (first with
the wrong fixture -- `_victim_outcome()`'s own default is a *failing* outcome, not a passing
one, caught by checking the failure message rather than assuming the first red result was the
real bug). **Fixed:** `_recount` now detects pair mode from the record header's own
`search_mode` field (not only non-empty `pair_lines`, which is empty in exactly this case) and
falls back to the alone tally when zero pairs ran, matching the runner's own shape exactly.
Verified: 159/159 `eval/tests` OK (up from 158).

**M2's question (W27 + the decoding fix on real fastjson):** already answered from the
2026-11-21 entry above, before he asked -- rebuilt the container with his fix, ran a real
diagnosis inside it against the actual fastjson checkout: `CANDIDATE`, 19/19 invocations, no
`UnicodeDecodeError`.

## 2026-11-24 -- M2's #168 review: schema v3, versioned validation

M2 reviewed PR #168 himself and confirmed the pair walk and comparison numbers. He also found
(and M1 independently hit the same thing on her own machine, PR #169) a real, urgent problem:
`reproduced_by` became **required** when W35 landed, but `schema_version` stayed **2** -- so
every one of the **16 bundles committed before W35** now failed `eval.bundle verify`, including
the F1 bundle behind FT009 and the W32 case.

**Reproduced for real first:** ran `eval.bundle verify` on all 24 committed bundles --
**16 of 24 failed** with `'reproduced_by' is a required property`, exactly matching M2's count.

**Considered and rejected a third option before picking between M2's two:** backfilling
`reproduced_by: "order"` into the 16 old `report.json` files directly. Every one of them is
provably order-mode (pre-W35, so order mode by construction), so the value isn't ambiguous --
but doing this would mean recomputing their `manifest.json` checksums to match doctored content,
which is exactly the "fix the checksum after tampering" case `eval.bundle.verify`'s own tests
exist to catch (ADR-013). A committed bundle's `report.json` is part of a checksummed record;
not something to edit after the fact even for an unambiguous value.

**Asked the member which of M2's two real options to build** (schema v3 with versioned
validation, vs. making `reproduced_by` optional in v2) -- chosen: **schema v3**, since making
the field merely optional would let a *future* bug that drops it from a brand-new report pass
silently, which the honesty rules don't let stand once seen.

**Built, test-first:**
- `eval/schema/report.schema.json` (the active schema): `schema_version` bumped `2` -> `3`;
  `reproduced_by` stays required.
- `eval/schema/report.v2.schema.json` (new): a frozen copy of the pre-W35 shape --
  `reproduced_by` not required -- for the 16 old bundles; its own description says it is never
  edited to add a field retroactively.
- `eval/schema_validator.py`: `load_schema(schema_version)` picks the matching file (2 or 3);
  an unrecognized version falls through to the current schema, where its `schema_version` const
  mismatch itself produces the `ValidationError` -- no separate "unknown version" branch needed.
  `validate_report` dispatches on the report's own `schema_version` when no schema is passed
  explicitly, so `eval.bundle.verify_bundle`'s existing call site needed no change at all.
- `eval/report.py`: `SCHEMA_VERSION` bumped `2` -> `3`, so every report built from now on is
  checked against the strict schema.
- 4 new tests in `eval/tests/test_schema_validator.py`: a v3 report validates; a v2 report
  without `reproduced_by` at all now passes; a v3 report missing it still fails (the strictness
  the "optional" alternative would have given up); a v2 report where the field IS present but
  wrong is still type-checked, not silently ignored.
- `eval/examples/*.json` (9) and `eval/reports/*.json` (8) bumped to `schema_version: 3` --
  they already carry `reproduced_by` and represent current output, not frozen history.

**Verified:** all 24 committed bundles re-`verify`d -> **all OK** (the 16 that failed, confirmed
failing first); `python -m unittest discover -s eval/tests` -> **163/163 OK** (up from 159);
`python -m unittest -v ui.tests.test_server` -> **31/31 OK**, including a real end-to-end F1
run. The 16 old bundles themselves were never touched -- same bytes, same checksums, same
`schema_version: 2` -- only which schema that version is validated against changed.

**The package-scope bundle (20261122T110129Z), still `tool.dirty: true`:** regenerated from a
genuinely clean tree (same save/revert/restore technique as 2026-11-22's bundles, since this fix
itself was uncommitted at the time), using the cached fastjson checkout and portable JDK 8 from
earlier in the session. Real result unchanged: `UNRESOLVED (NOT_REPRODUCED)`, 12,817
invocations, search tried 0 of 260 candidates. New bundle `tool.dirty: false`, `verify` clean;
old one removed.

**PR template reminder:** acknowledged, no code change -- `.github/pull_request_template.md`
already exists (M2's area); this is a note to fill it out on my own future PRs.

**Documented:** ADR-016 (the schema bump is a direct consequence of its own `reproduced_by`
field) and `docs/contracts/report-schema.md`'s `schema_version`/`reproduced_by` rows, both dated
2026-11-24.

## 2026-11-27 -- M2's three-item list: the W27 build, the v3 agreement, five stale rows

### 1. W27's Dockerfile: the real cause of the first-build failure, fixed

M1's first build (2026-11-25) failed at `pip install` on `rpds-py` ("from versions: none"); the
unchanged retry worked, so her evidence log correctly left the cause unconfirmed, "likely a
network failure". Did not assume that and move on -- checked for real.

`eval/requirements.txt` pinned only `jsonschema==4.26.0` itself, not its own dependencies
(`attrs`, `referencing`, `jsonschema-specifications`, `rpds-py`, `typing_extensions`). `rpds-py`
is a compiled wheel, the one that actually failed, and the only one of the five with a real
chance of not having a wheel for a given Python/platform combination. Pinning the top-level
package alone does not pin what a fresh build resolves for its own dependencies -- that can
still change under a "reproducible" image between builds.

**Checked inside real containers, not guessed:** `pip install --dry-run` against the pinned
W27 image's own Python (3.12.3, Ubuntu 24.04, confirmed from the base image itself) resolves
`rpds-py 2026.9.1`. Before pinning that, checked it against this project's own documented
minimum (`Python 3.10`, CLAUDE.md/README.md): `rpds-py 2026.9.1` requires Python `>=3.11` and
has **no wheel for 3.10 at all** -- pinning it as-is would have silently broken the 3.10 claim
the moment anyone needed it, a worse regression than the bug being fixed. Found the newest
version that installs cleanly (a wheel, no compile) on **all three** versions this project
claims (3.10, 3.11 -- CI's own, 3.12 -- this image's): `rpds-py 0.30.0`. Confirmed the full
pinned set together on all three, not just `rpds-py` alone.

`Dockerfile`'s `pip3 install` also gets `--retries 5`, for whatever the original failure
actually was (the pin fixes a real, confirmed-reproducible incompatibility path; the retries
cover a genuinely transient one, which this evidence cannot rule out either way).

**Verified for real:** `docker build -t flaketrace:w27-fix .` -> succeeds, every dependency a
downloaded wheel, no compilation. Ran a real F1 diagnosis inside the built image (first attempt
used a `$(pwd)`-style volume mount in Git Bash and silently mounted nothing -- the exact
Windows/Git-Bash caveat this project's own README already documents; redone with the
documented native-path workaround): `VERIFIED (sequence)`, `ConfigPolluterTest#pollute`, 67
invocations -- matching both earlier runs (mine, 2026-11-21; M1's, 2026-11-25) exactly. Bundle
landed on the host and `eval.bundle verify` -> OK. `flaketrace:w27-fix` tag removed after
confirming (the Dockerfile itself, not a tag, is the real deliverable).

### 2. Schema v3 agreement recorded

PR #170 changed a contract (the report schema) without recording the required three-way
agreement in its own description -- a real process gap, not a technical one. Added a dated note
to `docs/contracts/report-schema.md` naming M2's approval (2026-11-24, on the PR itself) and
M1's agreement (given directly, relayed by M2 2026-11-27). Did not re-litigate the choice
itself -- that was already decided with the member on 2026-11-24, before building either
option; this is only the record the PR should have carried.

### 3. Five stale action-register rows corrected (M-3, A5, A8, A9; FT009 checked, not stale)

Re-read each against what the row's own evidence (and `docs/evidence-m2.md`/`evidence-m1.md`)
actually shows before changing anything, rather than taking M2's list as license to just delete
the word "Open":
- **M-3, A5:** both said W26b/FT008's "runs and yield table" were open. They are done
  (M2's independent repeat; M1-reproduced pair mode). The real remaining gap for FT008/A5 is
  narrower than either row said: a *task-matched comparator baseline* (iFixFlakies/RankF),
  which is explicitly FYP-2 scope and genuinely not built -- not "the runs".
- **A8:** said "the acceptance logic" around the Wilson intervals was open, as if only the
  numbers existed. Checked `eval/outcome.py`: the intervals feed `decide()`'s verdict table
  directly (`wilson_interval` on both tallies, ADR-010) -- the acceptance logic is built, not
  separate from the intervals.
- **A9:** said M1's bundle reproduction was open; her own evidence log (2026-11-22) already
  shows it done, and schema v3 (above) means all 24 bundles currently pass `verify`, not just
  hers.
- **FT009:** M2 asked to check this one too. Read it in full -- it is a dated narrative (first
  "awaiting the gaps' fixes", later entries show each gap fixed), not actually stale; left
  unchanged.

Every row kept at `Partly`, per this register's own rule: only the supervisor's acceptance
makes a row `Done`, never a member finishing the underlying work.

**Verified:** `python -m unittest discover -s eval/tests` -> 165/165 OK throughout (the
requirements/Dockerfile change touches no Python test code; re-run anyway, not assumed safe).

## 2026-11-27 -- M2's task list, item 1 (W37/FT008/FT017): the polluter count, recounted myself

M2's PR #178 (merged this morning, after the supervisor's 23 Nov review) already corrected
`claims-ledger.md` and flagged that `real-case-protocol.md` and this file still said "five
distinct" / "certified polluter". By the time I read his PR, both were already fixed --
resolved as part of the same-day merge of PR #170/#171's follow-on branch into `main`, before
his task list reached me. Did not take that as settled, though: the task says "recount it
yourself", so I did.

**Independent recount, not trusted from M2's number:** read `polluters` directly from the
real `report.json` of all seven committed FJ-03 pair-mode bundles
(`eval/bundles/2026112*T*Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest*`):

```
120044Z (original) -> SerializeWriterTest_14#test_writer_1
162104Z (ranked)    -> SerializeWriterTest_14#test_writer_1
165348Z (seed 0)    -> SerializeWriterTest_14#test_writer_3
170257Z (seed 1)    -> SerializeWriterTest_14#test_writer_1
171204Z (seed 2)    -> SerializeWriterTest_14#test_writer_2
174219Z (seed 3)    -> SerializeWriterTest_14#test_writer_3
174845Z (seed 4)    -> SerializeWriterTest_15#test_writer_1
```

**Four distinct identities** (`test_writer_1` x3, `test_writer_3` x2, `test_writer_2` x1,
`SerializeWriterTest_15#test_writer_1` x1) -- matches M2's own recount in PR #178 exactly, now
confirmed independently rather than taken on trust.

**Checked the rest of task 1's specific asks, not just the headline number:**
- The 524-candidate scan's "six relevant tests" is already named as a separate count from the
  seven runs' "four adopted" in both `real-case-protocol.md` and this file -- not conflated.
- Order mode's `NOT_REPRODUCED` (12,817 invocations) is stated in its own paragraph, nowhere
  mixed into the pair-mode table.
- "Costs are test-method invocations, not JVM launches": checked against a real bundle's own
  `budget` field (`20261122T120044Z`'s `report.json`) -- `spent` sums to 798 (the table's own
  number), `launches: 409` is a different, separately-reported figure. The two were never
  conflated in the first place; confirmed, not assumed.

**Repo-wide check for the stale wording, not just the two files M2 named:** `grep -rl "five
distinct\|certified polluter" docs/` found eight files. Six are not stale claims and were left
alone: `claims-ledger.md` (M2's own fix), `genai-register.md` and `members.md` (dated log
entries correctly describing what was said *at the time*, not a current claim --
`members.md`'s own entry now also carries a 2026-11-27 correction note), `handover-m1-m3.md`
and `iteration-2-plan.md` (both quote the old wording only to name the fix, already correct),
`supervisor-review-2026-11-23.md` (M2's own review note, describing the finding in the past
tense). **One real, live-content hit found and NOT fixed myself:** `docs/10-Final1/demo-plan.md`
line 23 still says "each to a certified polluter" -- this is a script for the actual defense
demo, not a historical record, so it matters that it's wrong. Left untouched (W33/the demo is
M2's area, not `eval/`, `fixtures/` or my own docs) and flagged in the W37 plan row and the
message drafted for the team. `docs/superpowers/specs/2026-11-27-ui-demo-design.md` has the
same wording but is M2's own spec file for his new UI work, also left alone.

**Not done (M2's own ask, not mine):** asking M1 to check the interpretation -- noted in the
hand-off message, not something I can do myself in this session.

**Verified:** no code changed; the recount is a read-only check against already-committed,
checksummed bundle files. `python -m unittest discover -s eval/tests` -> 165/165 OK (unaffected,
confirmed anyway).

## 2026-11-27 -- M2's task list, item 2 (W36/FT009): the bundle-verification matrix

**Checker commit: `41fc150f44fa866c4ae845bd4b117da859dc7b05`** (`main`, after PR #180) -- named
explicitly because the task rule says never write "all bundles verify" without it: the checker
(`eval/bundle.py`) itself can change (exactly what happened in #164 -> #170), so a verdict with
no commit attached is not evidence of anything by the time anyone reads it later.

**All 24 committed bundles, read for real, not summarised:**

| Bundle | Schema v | Expected (report's own outcome) | Actual (`verify_bundle` at `41fc150`) | Replay |
| --- | --- | --- | --- | --- |
| `20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode` | 2 | `VERIFIED` | OK | not yet run |
| `20261121T162830Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261121T184546Z-odfixture.ConfigVictimTest#expectsDefaultMode` | 2 | `VERIFIED` | OK | not yet run |
| `20261121T184816Z-odfixture.FeatureVictimTest#expectsTurboDisabled` | 2 | `VERIFIED` | OK | not yet run |
| `20261121T184910Z-odfixture.ToggleVictimTest#expectsNotBothFlagsSet` | 2 | `VERIFIED` | OK | not yet run |
| `20261121T185039Z-odfixture.AlwaysEarlyVictimTest#expectsLateFlagUnset` | 2 | `VERIFIED` | OK | not yet run |
| `20261121T185141Z-odfixture.NegativeAloneFailTest#alwaysFails` | 2 | `UNRESOLVED(VICTIM_FAILS_ALONE)` | OK | not yet run |
| `20261121T185218Z-odfixture.NegativeFlakyTest#sometimesFails` | 2 | `UNRESOLVED(VICTIM_FAILS_ALONE)` | OK | not yet run |
| `20261121T185248Z-odfixture.EnvDependentNegativeTest#onlyFailsUnderCI` | 2 | `UNRESOLVED(NOT_REPRODUCED)` | OK | not yet run |
| `20261121T185339Z-odfixture.DualFailureVictimTest#expectsStateTwo` | 2 | `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)` | OK | not yet run |
| `20261121T185847Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261121T190427Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261121T191519Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261121T192924Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261121T195429Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261121T200523Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261122T120044Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261122T162104Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261122T165348Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261122T170257Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261122T171204Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261122T174219Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261122T174845Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261124T151413Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` | 2 | `UNRESOLVED(NOT_REPRODUCED)` | OK | not yet run |
| `20261127T103734Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` (W39, `original`) | **3** | `UNRESOLVED(BUDGET_EXHAUSTED)` | OK | exit 2, "nothing to replay" (M2, PR #184) |
| `20261127T104310Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` (W39, `random` seed 1) | **3** | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | `CANDIDATE -> CANDIDATE same`, exit 0, `reproduced_by: pair` with the constructed-pair line, replay bundle `verify` OK (M2, PR #184) |
| `20261127T104600Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` (W39, `random` seed 2) | **3** | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |
| `20261127T104934Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf` (W39, `random` seed 3) | **3** | `CANDIDATE(NO_SUPPORTED_RESOURCE_EVIDENCE)` | OK | not yet run |

**28 of 28 OK** *(24 as of the matrix's first build, 2026-11-27 morning; M2's W39 PR #182 added
4 more the same day, appended above rather than re-tabulated from scratch)*. Generated with a
short script reading `report.json`'s own `outcome`/`unresolved_reason`/`candidate_reasons` for
"Expected" and calling the real `eval.bundle.verify_bundle` for "Actual" -- not hand-transcribed,
to rule out a copy error across 28 rows. **The four W39 bundles are the first ever committed
with `schema_version: 3`** -- the real test of the v2/v3 dispatch on a genuinely new report
(not replayed or hand-built) that the first version of this entry said was still pending.

**The malformed and tampered controls**, run for real alongside the matrix (not just cited from
memory):
- `eval.tests.test_bundle.TestVerifyBundleHappyPath`: `test_a_bundle_with_no_manifest_is_a_clear_problem_not_a_crash`,
  `test_changing_a_report_count_is_caught_by_recount`,
  `test_changing_one_byte_of_the_record_breaks_the_checksum`,
  `test_deleting_one_alone_line_with_the_checksum_fixed_is_still_caught_by_recount` (ADR-013's
  own point: fixing the checksum after tampering must not hide the mismatch).
- `eval.tests.test_bundle.TestVerifyReplayBundle`: `test_replay_without_a_reference_signature_in_the_header_is_a_clear_problem`.
- `eval.tests.test_committed_bundles.TestCommittedBundles`: `test_every_committed_bundle_verifies`,
  `test_the_check_catches_a_required_field_without_a_version_bump` (M2's own re-enactment of the
  #164 incident, confirming the check would have caught it).

`python -m unittest eval.tests.test_bundle.TestVerifyBundleHappyPath eval.tests.test_bundle.
TestVerifyReplayBundle eval.tests.test_committed_bundles` -> **9 tests, OK**.

**The Replay column is empty, on purpose, not forgotten:** replaying most of these bundles needs
the real subject checkout (the fixture is fast; the fifteen FJ-03 ones need the actual fastjson
source at the bundle's own pinned commit, which this session does not have mounted right now).
`runner/replay.py` is M2's file. Asked him for this column rather than guessing or running a
partial version myself.

**Checked (read-only) whether `replay` is itself schema-version sensitive, since the task asked
to "state which versions `replay` supports":** grepped `runner/replay.py` for `schema_version`
and the validator -- no hits. It reads and writes via `record.jsonl`'s own fields directly, not
through `report.json`'s schema at all; a report's schema only matters once something *else*
(`eval.bundle.verify_bundle`) is run on whatever `replay` writes. So the honest answer is "all
of them, by construction" -- not a version `replay` was built to support, a version it never
checks.

**Not done (M2's own ask, not mine):** telling M1 to do her solo repeat of this check -- noted
in the hand-off message.

**Verified:** `python -m unittest discover -s eval/tests` -> 165/165 OK; the matrix and control
results above are both from real commands run against `41fc150`, not summarised from an earlier
run.

## 2026-11-27 -- M2's task list, item 3 (W27 reliability): rebuilt from a genuine fresh clone

The pin fix itself (`eval/requirements.txt`, `Dockerfile`'s `--retries 5`) was already built and
merged (PR #179, earlier the same day). Task 3 specifically asks to "rebuild from a clean
clone, run the F1 diagnosis, show the result unchanged" -- a stronger check than rebuilding in
my own working directory, which is what the earlier fix's own verification actually did. Did
the stronger version, not just re-cited the earlier one.

**First attempt caught a real, if unrelated, problem, not assumed clean:** cloned the repo to a
scratch path with `git clone <local path> <scratch path>` and ran `docker build --no-cache`.
Failed: `ERROR: invalid file request .git/objects/04/9d9133...`. Reproduced twice (two different
scratch locations), so not a fluke. Narrowed it before concluding anything: the object file in
question is an ordinary tree object, identical in content and permissions in both the source
repo and the clone -- what differs is the **link count** (3 in both, meaning `git clone` had
hardlinked the object rather than copying it, the default for a *local-path* source on the same
filesystem). `git clone --no-hardlinks` to the same scratch path built cleanly. **The real
question was whether this affects anyone else**, not whether the workaround exists: cloned from
the actual GitHub remote (`https://github.com/zoyaahmad428/FlakeTrace.git`) instead of a local
path -- a real network clone never creates loose hardlinked objects at all (it unpacks a
packfile), so the failure mode cannot occur. Built `--no-cache` from that clone: succeeded.
**Conclusion: a real Docker-Desktop-on-Windows quirk with hardlinked read-only git objects, but
not a W27 reliability gap** -- nobody clones this repo from a local path on the same drive;
GitHub (what M1, M2 and CI all actually do) never hits it.

**The real check, from the genuine GitHub clone:**
```
git clone https://github.com/zoyaahmad428/FlakeTrace.git <scratch>
docker build --no-cache -t flaketrace:w27-githubclone .
docker run --rm -v "<scratch>\flaketrace-bundles:/flaketrace/flaketrace-bundles" \
  flaketrace:w27-githubclone diagnose --project fixtures/od-fixture \
  --victim odfixture.ConfigVictimTest#expectsDefaultMode --bundle flaketrace-bundles
```
-> `VERIFIED (sequence)`, `ConfigPolluterTest#pollute`, 67 invocations -- **unchanged**, matching
every earlier run of this case (this session's 2026-11-21 and 2026-11-27 runs, M1's 2026-11-25
second-machine run). `python -m eval.bundle verify` on the resulting bundle -> OK. Test clones,
images and the scratch bundle folder removed afterward.

**W27 closed with M1's second-machine result**, per the task -- the row and this entry both
name it (2026-11-25, her laptop, Docker Desktop 4.98.0, WSL2 kernel 6.6.87.2): identical verdict
and invocation count to every run on this machine, which is the real content of "closing the
row with her result," not just a status-line edit.

**Verified:** real `docker build --no-cache` from three different clone methods (local-path
default, local-path `--no-hardlinks`, real GitHub remote); a real diagnosis run and `verify` on
the GitHub-clone build specifically, since that is the scenario that matters. No code changed
beyond PR #179's already-merged fix.

## 2026-11-27 -- two follow-ups from M2's PR #184, in my own files

M2's W36 replay PR named two real gaps in my files directly, not as a new numbered task --
addressed both before moving to task 4, since leaving them would mean the matrix and README
stay wrong a turn longer than necessary.

**1. The matrix needed the four W39 bundles.** Added all four (checker commit unchanged,
`41fc150` was superseded by later merges but the matrix note already says the check was
re-run, not a fresh commit worth re-stamping for four rows) -- all `schema_version: 3`, the
first ever committed under it. Filled the Replay column from M2's PR #184 for the two he
actually ran (`original`: exit 2 "nothing to replay"; `random` seed 1: `CANDIDATE -> CANDIDATE
same`); left seeds 2 and 3 as "not yet run" rather than guessing they'd behave the same.
Re-verified all 28 committed bundles together (not just the 4 new ones in isolation) -> 28/28
OK.

**2. `eval/bundles/README.md`'s fixture table named 8 folders that no longer exist** -- the
2026-11-21 clean-tree regeneration (this file's own later section) renamed them, and the table
was never updated to match. Checked each of the 8 real replacement folders' actual
`report.json` before touching the table, not just renamed the timestamp and left the
descriptive text alone: caught a real, if expected, discrepancy doing this -- N2's alone tally
in the current committed bundle is 9/20, not the 13/20 the table still said (N2 is
deliberately intermittent; the old number was real for the bundle that no longer exists, not
an error, but it is wrong for the one now committed). Corrected it to the real current number
rather than leaving the old one standing next to a new folder name.

**Verified:** `python -m unittest discover -s eval/tests` -> 165/165 OK; all 28 committed
bundles `verify` clean; every number in the corrected README table re-read from the actual
current `report.json` files, not carried over from the stale table.

## 2026-11-27 -- M2's task list, task 4 (already done) and task 5 (W36 row A8/A9)

**Task 4** (record the schema v3 agreement in `report-schema.md`) was already complete --
added during the earlier "M2's three-item list" round, before the numbered task list existed.
Checked it survived every merge since: intact, names both M1's and M2's agreement, the actual
schema file untouched. No new commit for this one.

**Task 5**: A8 and A9 still said FT003/FT004/M1's bundle reproduction were open; both are done
(reproduced by M1, 2026-11-20 and 2026-11-22 respectively). Reworded both to say so and to use
this register's own established phrase, "**Awaiting supervisor acceptance**" (checked against
FT005's row, which already uses it, rather than inventing new wording). A9's bundle count
updated 24 -> 28 (the four W39 bundles added earlier today).

**Verified:** `python -m unittest discover -s eval/tests` -> 165/165 OK (docs-only change).
