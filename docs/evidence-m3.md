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
