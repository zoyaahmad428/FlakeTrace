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
  environment-dependent behaviour of the fixture, not a bug in either component; it means
  `ground_truth.json`'s N2 entry is not safely portable across machines as currently written,
  which I have not yet resolved (my call to make, as the fixture's owner — recorded as an
  open item, not silently patched over).
