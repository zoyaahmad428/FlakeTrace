# Evidence log — Member 1 (Resource Evidence)

Each entry: requirement addressed, file/function, test, command, result,
limitation discovered. Commands were run for real; no number in this file is
invented.

## Phase 1 — Output contract

**Requirement:** agree the resource-evidence output format (per-test accesses
and per-pair edges) before writing extraction code, aligned with Member 3's
report schema.

- File: `docs/contracts/resource-evidence.md` (status: DRAFT, awaiting
  Member 3's confirmation).
- Input evidence: `evidence/javap-dumps/phase1-f1-f2.txt`.
- Command (fixture build, unmodified `fixtures/od-fixture`, image
  `maven@sha256:15522857a08bc468b05f4284d4a5a6c49eff7af7abfe16dc7770609484a67b8b`):
  `mvn -B -q test-compile` → exit 0.
- Command: `javap -c -p -cp classes:test-classes odfixture.ConfigPolluterTest
  odfixture.ConfigVictimTest odfixture.FeaturePolluterTest
  odfixture.FeatureVictimTest odfixture.FeatureFlags odfixture.Config`
  (JDK 1.8.0_502) → exit 0.
- Result (real offsets):
  - F1 write: `ConfigPolluterTest.pollute@1` (`putstatic odfixture/Config.mode`).
  - F1 read: `ConfigVictimTest.expectsDefaultMode@1` (`getstatic`).
  - F2 write: `FeaturePolluterTest.enableTurbo@4` (`System.setProperty`, key from `ldc` at offset 0).
  - F2 read: `FeatureFlags.isTurboEnabled@2` (`System.getProperty`), reached from
    `FeatureVictimTest.expectsTurboDisabled@0`, i.e. depth 2.
- Test: inline Python check that the contract's example JSON parses, every
  offset/call frame resolves to the expected instruction in the saved javap
  output, and the projected fields validate against
  `eval/schema/report.schema.json` `$defs/sharedResource` and
  `$defs/codeLocation`. Result: all passed. An extra key (`depth`) in a
  `codeLocation` is rejected by the schema, as expected (so projection must
  copy only `class`, `method`, `bytecode_offset`).
- Limitations discovered:
  - F2's victim read is only visible at depth ≥ 2. At the default depth 1
    the F2 pair will have no edge.
  - `Config.<clinit>` writes `Config.mode` (offset 1) and runs implicitly. It is
    not reachable by following calls and is reported as `IMPLICIT_CLINIT`.
  - Member 3's report has singular location fields. Multi-edge information is
    lost on projection (open question 1 in the contract).

## Contract revision — consumers and invocation (2026-10-09)

**Requirement:** the contract must name all its consumers (Member 2's CLI calls
the extractor end-to-end) and define how the extractor is invoked, so Member 2
can code against it. Also record the language and entry point in
`docs/contracts/interfaces.md` Interface 2.

- File: `docs/contracts/resource-evidence.md`. Status paragraph corrected (Member
  2 is a consumer, so later changes need all three members). New section
  "Invocation": command, flags, pair and single modes, JSON on stdout, exit
  codes 0/1/2. Status: **planned, not yet implemented**.
- File: `docs/contracts/interfaces.md`, the one line under Interface 2 about
  function name and language, now points to the Invocation section. No other
  line changed.
- Check (inline Python script, run in the scratch checkout): the example JSON
  still parses; its 3 `call_path` frames still resolve to `invokestatic` in
  `evidence/javap-dumps/phase1-f1-f2.txt`; the projected `codeLocation`s
  validate against `eval/schema/report.schema.json`; every in-document link
  anchor (`#invocation`, `#terms`, `#example--fixture-f2-at---depth-2`) exists.
  Result: all passed.
- Command: `git diff --numstat -- docs/contracts/interfaces.md` → `1 1`
  (exactly one line changed).
- Command: `python3 -m unittest` over every `eval/tests/test_*.py` → `Ran 58
  tests ... OK` (docs-only change; run to confirm nothing else broke).
- Not yet run: the extractor itself (no code exists yet).
- Limitations / open items:
  - Default `--depth` decided as **2** (Member 1, 2026-10-09; ADR-002). At
    depth 1, fixture F2 has no edge (its read sits one call below the test
    method).
  - Phase 1 cleanup (`.gitignore` and the removal of 45 junk files) was merged
    separately as PR #4 (`dfcaa88`). Its check: 45 matching files before, `git
    ls-files` count 0 after, status showed 45 deletions plus `.gitignore`.

## Decision record — extractor approach and default depth (2026-10-09)

**Requirement:** record Member 1's two design decisions (fresh Python/javap
extractor, default `--depth 2`) where the team can agree to them.

- Files: `docs/03-Design/decisions/ADR-002-evidence-extractor-implementation.md`
  (new, PROPOSED); `docs/contracts/resource-evidence.md` (default 2 in Terms
  and the Invocation table; numbering note; open question 5 marked resolved).
- Check: `git show origin/main:POC/src/extract_static.py`, lines 29 and 132:
  `HOPS = int(os.environ.get("FT_HOPS", "1"))` and `for _depth in range(HOPS + 1):`.
  The POC explores the root plus HOPS levels of callees, so POC depth N =
  contract depth N + 1. `POC/results/depth_sweep.csv` uses the POC numbering.
- Limitation discovered: POC records disagree on FJ-02. `ranking.csv` gives
  first rank 39 at the frozen scope, but `depth_sweep.csv` gives rank 1 at POC
  depth 1 (W_R). Not resolved here; Phase 5 re-measures with this extractor.
- Open question 5 (F1 offsets) resolved by Member 3 in PR #7 (`af70048`),
  verified independently with `javap -c -p`: offsets 1/1.

## Phase 2 — Depth-1 extraction with lifecycle attribution (2026-10-09)

**Requirement:** given compiled classes and one test method, report its static-field and
constant-key system-property accesses, from the test method **and** its lifecycle code
(JUnit 4 `@Before/@After/@BeforeClass/@AfterClass`, JUnit 3 `setUp/tearDown`, the test
class's `<clinit>`, inherited lifecycle methods), with the lifecycle method each came from.

- Files: `evidence/extract.py` (`parse_class`, `find_roots`, `scan_method`, `scan_call`,
  `constant_key`, `analyse_test`, `main`); `evidence/tests/test_extract.py`; Member 1's own
  test input `evidence/tests/resources/m1-selftest/` (not a project fixture).
- Build (POC-frozen JDK 8 image `maven@sha256:15522857…`):
  `mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile` → exit 0.
- Manual cross-check, acceptance case `m1selftest.M1SelfTest#writesAndReads`
  (JDK 8 `javap -c -p`, saved in `evidence/javap-dumps/phase2-m1selftest.txt`):

  | javap -c -p (JDK 1.8.0_502) | extractor output (`--depth 1`, JDK 8 javap) |
  | --- | --- |
  | `1: putstatic … SelfTestState.counter:I` | `WRITE m1selftest.SelfTestState#counter @1 via=TEST_METHOD` |
  | `4: getstatic … SelfTestState.counter:I` | `READ  m1selftest.SelfTestState#counter @4` |
  | `8: ldc "m1.selftest.key"`, `12: invokestatic System.setProperty` | `WRITE sysprop:m1.selftest.key @12` |
  | `16: ldc "m1.selftest.key"`, `18: invokestatic System.getProperty` | `READ  sysprop:m1.selftest.key @18` |

  Exactly these 4 accesses, no unsupported observations.
- Lifecycle (`M1LifecycleSelfTest#emptyBody`, empty test body): CLINIT `<clinit>@4`
  (setProperty), BEFORE_CLASS `beforeAll@1`, BEFORE `M1LifecycleBase.baseBefore@1`
  (inherited), AFTER `after@2` (clearProperty), AFTER_CLASS `afterAll@0`. All offsets match
  the JDK 8 javap dump. JUnit 3 (`M1Junit3SelfTest#testNothing`): SETUP `setUp@1`,
  TEARDOWN `tearDown@2` (`Boolean.getBoolean`).
- Unsupported (`M1UnsupportedSelfTest#tricky`): `SYSPROP_NON_CONSTANT_KEY@23`,
  `REFLECTION@37` (`Field.setInt`), `DEPTH_LIMIT@40` (`helper()` not followed); no accesses
  reported. Offsets match the dump.
- Command: `python3 -m unittest evidence.tests.test_extract -v` → `Ran 9 tests … OK` with
  host javap 21.0.12.1, and `Ran 9 tests … OK` with JDK 8 javap
  (`FLAKETRACE_JAVAP` pointing at the JDK 8 image's javap).
- Fixture sanity run (`--depth 1`, JDK 8 javap, fixture compiled unmodified):
  `ConfigPolluterTest#pollute` WRITE `odfixture.Config#mode @1`; `ConfigVictimTest#expectsDefaultMode`
  READ `@1`; `FeaturePolluterTest#enableTurbo` WRITE `sysprop:odfixture.turbo @4`;
  `FeatureVictimTest#expectsTurboDisabled` no access, `DEPTH_LIMIT @0`
  (`FeatureFlags#isTurboEnabled`). Both F1 tests also get `IMPLICIT_CLINIT` (`Config.<clinit>`).
  This matches the Phase 1 javap evidence. It is not the Phase 5 validation.
- Error found and fixed: on JDK 8 javap, the lifecycle case first returned only the CLINIT
  access. Cause: `RX_CONSTANT` captured javap's padding before the annotation descriptor
  (`'              Lorg/junit/BeforeClass;'`), so no annotation matched. Fix: `\s?` → `\s*`.
  Mutation check: restoring the old regex makes
  `test_junit4_lifecycle_and_inherited_before_are_attributed` fail (1 failure).
- Limitations discovered:
  - Depth 1 only: F2's victim read is invisible until Phase 3.
  - Running without `--depth 1` exits 2 ("not implemented yet") because the contract default is 2.
  - The test class **constructor and instance-field initialisers** run for every JUnit test
    but are not roots in the contract (`via` has no value for them), so they are not analysed.
    This needs a contract decision.
  - The unit tests are not in CI yet: `.github/` is Member 2's area. CI needs a step that
    compiles the self-test project and runs `python3 -m unittest evidence.tests.test_extract`.

## Phase 3 — Configurable call depth (2026-10-09)

**Requirement:** `--depth N` (default 2; 1, 2, 3 supported) follows calls into the
project's own classes only, never the JDK or third-party jars. Handles recursion and
cycles. Records `call_path` for every access. Reports virtual dispatch and reflection as
unsupported. Measures what each depth adds on the fixture.

- Files: `evidence/extract.py` (`walk_root`, `scan_method`, `scan_call`, `follow_call`,
  `may_be_overridden`, `Project.resolve_method`); `evidence/tests/test_extract.py` (class
  `CallDepthTest` and CLI tests); new self-test input `M1DepthSelfTest`, `SelfTestBase`,
  `SelfTestChild` (javap dump: `evidence/javap-dumps/phase3-depth-selftest.txt`);
  `evidence/tools/measure_depth.py`.
- Expected results read by hand from the JDK 8 javap dump, then matched by the extractor (JDK 8 javap):
  - `M1DepthSelfTest#callsDown`: depth 1 none (`DEPTH_LIMIT @callsDown@0`); depth 2 counter
    WRITE `callsDown@0 > level2@2`; depth 3 adds property WRITE
    `callsDown@0 > level2@5 > level3@4`. level4's READ (depth 4) is never reported
    (`DEPTH_LIMIT @level3@8`).
  - `#recursion` (ping/pong cycle): depth 3 gives counter WRITE
    `recursion@1 > ping@7 > pong@1`, and the walk terminates.
  - `#dispatch`: only the named target is followed, so counter WRITE `dispatch@9 > SelfTestBase.work@2`
    plus `VIRTUAL_DISPATCH @dispatch@9`. `SelfTestChild.work`'s `setProperty`, which is what
    really runs, is **not** claimed.
- Command: `python3 -m unittest evidence.tests.test_extract -v` → `Ran 15 tests … OK` with host
  javap 21.0.12.1, and `Ran 15 tests … OK` with JDK 8 javap.
- Command (fixture compiled unmodified, JDK 8 image, `mvn -B -q test-compile` exit 0):
  `python3 -m evidence.tools.measure_depth --classes fixtures/od-fixture/target/classes --test-classes fixtures/od-fixture/target/test-classes --repeats 5`

  13 test methods, every repeat with an empty class cache:

  | depth | accesses | unsupported | javap calls | median s (javap 21.0.12.1, 5 runs) | median s (javap 1.8.0_502 via Docker, 3 runs) |
  | --- | --- | --- | --- | --- | --- |
  | 1 | 7 | 10 (5 IMPLICIT_CLINIT, 5 DEPTH_LIMIT) | 16 | 5.349 (min 5.138, max 5.963) | 10.933 (10.417–11.072) |
  | 2 | 8 | 6 (5 IMPLICIT_CLINIT, 1 DEPTH_LIMIT) | 16 | 5.124 (5.047–5.565) | 10.825 (10.759–11.121) |
  | 3 | 8 | 5 (5 IMPLICIT_CLINIT) | 16 | 5.378 (5.252–5.641) | 10.507 (10.473–10.600) |

  The only access added by depth 2: `FeatureVictimTest#expectsTurboDisabled` READ
  `sysprop:odfixture.turbo` (F2's victim read). Depth 3 adds no access on the fixture.
- Limitations discovered:
  - **On the fixture, depth adds no measurable time.** All depths load the same 16 classes, and the time is
    almost all `javap` JVM start-up (about 0.33 s per call on the host, about 0.68 s per call through Docker).
    The time differences between depths are within run-to-run noise. The fixture is too small
    to show the cost of depth; a real project (Phase 5) is needed for that.
  - One `javap` process per class. That is acceptable here; for large projects, batching classes
    per call would cut start-up cost (not done).
  - Overrides are not followed (only `VIRTUAL_DISPATCH` is recorded). Finding subclasses
    would need every project class loaded.
  - Measurement-tool error (not an extractor bug): the first JDK 8 run failed with "class not
    found" because the Docker javap wrapper runs in a different working directory and
    relative class paths did not resolve. Re-run with absolute paths.

## Phase 4 — Polluter→victim resource edges (2026-10-09)

**Requirement:** given `--polluter` and `--victim`, report every resource the polluter
WRITES (including its lifecycle code) that the victim READS, with both locations. An empty
edge list carries `no_supported_resource_evidence: true` and never means "no dependency".

- Files: `evidence/extract.py` (`find_edges`, `report_fields`, pair mode in `main`);
  `evidence/tests/test_extract.py` (`PairSelfTest`, `FixturePairTest`, CLI pair tests).
- Fixture compiled unmodified (JDK 8 image, `mvn -B -q test-compile` exit 0). Command per pair:
  `python3 -m evidence.extract --classes fixtures/od-fixture/target/classes --test-classes fixtures/od-fixture/target/test-classes --polluter … --victim …`
  (JDK 8 javap, default depth 2):

  | pair | edges | `no_supported_resource_evidence` |
  | --- | --- | --- |
  | F1 `ConfigPolluterTest#pollute` → `ConfigVictimTest#expectsDefaultMode` | `odfixture.Config#mode`: write `pollute@1`, read `expectsDefaultMode@1` | false |
  | F2 `FeaturePolluterTest#enableTurbo` → `FeatureVictimTest#expectsTurboDisabled` | `sysprop:odfixture.turbo`: write `enableTurbo@4`, read `FeatureFlags.isTurboEnabled@2` (depth 2) | false |
  | F2 at `--depth 1` | none (victim side `DEPTH_LIMIT`) | true |
  | F3 `ToggleAPolluterTest#setFlagA` → `ToggleVictimTest#expectsNotBothFlagsSet` | `odfixture.Toggles#flagA`: write `setFlagA@1`, read `@0` | false |
  | F3 `ToggleBPolluterTest#setFlagB` → same victim | `odfixture.Toggles#flagB`: write `setFlagB@1`, read `@6` | false |
  | `MathUtilTest#addsTwoNumbers` → `NegativeAloneFailTest#alwaysFails` | none | true |
  | `ConfigPolluterTest#pollute` → `FeatureVictimTest#expectsTurboDisabled` | none | true |

  The F3 offsets were checked by hand in JDK 8 `javap -c -p` (`putstatic flagA@1`, `putstatic flagB@1`,
  `getstatic flagA@0`, `getstatic flagB@6`). The F1/F2 offsets are the ones in
  `evidence/javap-dumps/phase1-f1-f2.txt`.
- `report_fields` for F2: `shared_resource = {kind: system-property, key: odfixture.turbo}`,
  `victim_read_location = {class: odfixture.FeatureFlags, method: isTurboEnabled, bytecode_offset: 2}`.
  It and the no-edge case (all `null`) validate against `eval/schema/report.schema.json`.
- Command: `python3 -m unittest evidence.tests.test_extract -v` → `Ran 26 tests … OK` with javap
  21.0.12.1 and with JDK 8 javap (Python 3.13). Under Python 3.11: `Ran 26 … OK (skipped=1)`. The
  skipped test is `test_report_fields_fit_member3_schema`, because jsonschema is not installed for
  3.11 here. It ran and passed under 3.13.
- Limitations discovered:
  - F3 needs **both** polluters, but this component is pairwise. It reports one edge per
    polluter (flagA, flagB). Combining them is Member 2's minimisation (W10).
  - The contract's Invocation section and `interfaces.md` still say "planned, not yet
    implemented". That wording was not edited, because contracts change only with all three members.
  - A CI job for these tests must install `eval/requirements.txt` (for jsonschema) and compile both
    the self-test project and the fixture.

## Test guard and in-process default depth (2026-10-09)

**Requirement:** (1) Member 2's CI job must not pass if the evidence tests silently skip. (2) Calling
`analyse_test` in-process without a depth must use the contract default (2), like the CLI.

- Files: `evidence/tests/test_extract.py` (`needs`, `need_javap`, `REQUIRE_JVM`; new test
  `test_in_process_default_depth_is_2`); `evidence/extract.py` (`analyse_test(..., depth=DEFAULT_DEPTH)`,
  previously `depth=1`).
- Commands and real results (fresh checkout of main `eeb5ba1` plus this change):
  - Nothing compiled, no guard: `python3 -m unittest evidence.tests.test_extract` → `Ran 27 tests … OK (skipped=27)`.
  - Nothing compiled, `FLAKETRACE_REQUIRE_JVM=1` → `FAILED (errors=5)`, each error saying which build is missing.
  - After `mvn -B -q test-compile` of the fixture and the self-test project (both exit 0), with
    `FLAKETRACE_REQUIRE_JVM=1` → `Ran 27 tests … OK` with javap 21.0.12.1, and `Ran 27 tests … OK` with JDK 8 javap.
  - Compiled but javap missing (`FLAKETRACE_JAVAP=/no/such/javap`): with the guard → `FAILED (failures=4, errors=4)`;
    without it → `OK (skipped=23)`.
- Limitation discovered: before this fix, `analyse_test(project, test_id)` defaulted to depth 1 in-process
  while the CLI defaulted to 2. An in-process caller leaving out the depth would have missed F2's edge.

## Contract confirmation and ADR agreement (2026-10-09)

**Requirement:** answer Member 2's integration questions. Confirm the resource-evidence contract,
fix which edge goes into the report, define how Member 2 calls the extractor, and record Member 1's
agreement on ADR-001 to ADR-004.

- Files: `docs/contracts/resource-evidence.md` (status: confirmed by M1 and M2, M3 pending; Invocation
  marked implemented, plus "Calling it from another component"; open questions 1 and 3 answered,
  2/4/6 marked open for M3); `docs/contracts/interfaces.md` (Interface 2 line: implemented);
  M1 rows ticked in ADR-001, ADR-002, ADR-003, ADR-004.
- Check (inline Python): every name the contract now lists exists in `evidence/extract.py` on main
  `eeb5ba1` (`Project`, `analyse_test`, `find_edges`, `report_fields`, `ExtractError.exit_code`,
  `FLAKETRACE_JAVAP` in `javap_command`); the example JSON parses; all anchors resolve. Result: passed.
- Limitation: ADR status lines stay `PROPOSED` until Member 3 ticks. The contract is confirmed by all
  three only when Member 3 approves this PR.

## Phase 5 (part 1): fixture validated against ground truth (2026-10-09)

**Requirement:** check the extractor's edges against Member 3's
`fixtures/od-fixture/ground_truth.json` automatically, not by eye. The file is read only and
never edited.

- Files: `evidence/tests/test_extract.py`, new class `GroundTruthTest` with 3 tests.
  - Every fixture test named in the ground truth (the 5 cases plus the 4 noise tests, 13 tests)
    is tried as polluter against every other one as victim, at the default depth (2). That makes
    156 ordered pairs.
  - The set of pairs with an edge must equal the ground-truth polluter→victim pairs exactly.
  - Each edge must be on the ground-truth `shared_resource`.
  - N1 and N2 (no polluters, `shared_resource: null`) must get no edge from any test.
- Exploratory run first (scratch script, all 156 pairs at depths 1, 2 and 3, javap 21.0.12.1).
  Real result:
  - Depth 1: 3 edges. F1 (`Config#mode`), F3-A (`Toggles#flagA`), F3-B (`Toggles#flagB`). F2 has
    none, because its read is one call down.
  - Depths 2 and 3: 4 edges, the three above plus F2 (`sysprop:odfixture.turbo`).
  - No other pair had an edge at any depth. N1, N2 and the four noise tests have no supported
    accesses at all.
- Commands (classes from `mvn -B -q test-compile` of the fixture and the self-test project, host
  JDK 21 compiling to Java 8, both exit 0):
  - `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest -v evidence.tests.test_extract.GroundTruthTest`
    → `Ran 3 tests in 6.173s … OK` (javap 21.0.12.1).
  - Full suite, same guard → `Ran 30 tests in 38.421s … OK`.
  - With JDK 8 javap (`FLAKETRACE_JAVAP` pointing at the `ft-jdk8` Docker image):
    `GroundTruthTest` + `FixturePairTest` → `Ran 8 tests in 31.881s … OK`.
- Mutation check (scratch script, nothing in the repo changed). Real results:
  - Depth forced to 1: `FAILED (failures=2)`. Both failures name the missing F2 pair.
  - In-memory ground truth altered (F1 field renamed, a fake N1 polluter added):
    `FAILED (failures=2, errors=1)`. The tests caught both.
- Limitations discovered:
  - F3's ground truth gives the field as free text (`"flagA and flagB (both required)"`). The test
    matches kind and class exactly and only checks that the edge's field is one of the words in
    that text. A machine-readable list would be firmer; that is Member 3's file, so it is noted, not
    changed.
  - This shows the extractor agrees with the ground truth on 5 hand-made cases. It does not show
    accuracy on real projects; that is the fastjson step (Phase 5 part 2, not yet run).
  - CI: Member 2's `evidence` job (PR #20) runs the whole `evidence.tests.test_extract` module,
    so `GroundTruthTest` runs there with no CI change. Ran in CI on PR #23 (JDK 8.0.504):
    `Ran 30 tests in 24.716s … OK`, no skips.
  - N1 and N2 being edge-free is expected, since neither touches a supported resource. The
    extractor's "no supported evidence" never means "no dependency".

## Phase 5 (part 2): real fastjson cases FJ-01 and FJ-02 (2026-10-09)

**Requirement:** run the extractor on a real project, not only the hand-made fixture: fastjson
at the POC's pinned commit, case FJ-01 at depths 1 and 2 (and 3), and settle whether FJ-01's
resource is `JSON.defaultTimeZone` or `JSON.defaultLocale`.

**Setup.**
- fastjson `https://github.com/alibaba/fastjson` @ `e05e9c5e4be580691cc55a59f3256595393203a1`,
  from `POC/manifest/cases.csv`. Fetched into a scratch folder outside the repository.
- Built unmodified in the `ft-jdk8` image (openjdk 1.8.0_502): `mvn -B -DskipTests test-compile`
  → `BUILD SUCCESS` in 1 min 12 s (172 main and 2,496 test sources compiled). `git status` in the
  fastjson checkout showed no source changes afterwards. No fastjson test was run.
- Pairs come from the POC's own records, not memory:
  - FJ-01: `POC/results/replay.csv` names `DateFieldFormatTest#test_format_` → `DateTest#test_date`,
    direction BRITTLE (the victim fails alone and passes after this test sets state). So the
    "polluter" here is a state-setter. The edge rule is the same: it writes, the victim reads.
    `DateFieldTest8#test_0` was also run, because the original Phase 5 brief named it.
  - FJ-02: `DateParserTest#test_date_0` → `DefaultExtJSONParser_parseArray#test_7` (BRITTLE).
- javap excerpt for every method on the paths below: `evidence/javap-dumps/phase5-fastjson.txt` (JDK 8 javap).

**Results with the real CLI** (FJ-01, `python3 -m evidence.extract --classes <fj>/target/classes
--test-classes <fj>/target/test-classes --polluter com.alibaba.json.bvt.date.DateFieldFormatTest#test_format_
--victim com.alibaba.json.bvt.date.DateTest#test_date --depth N`, javap 21.0.12.1, one run each):

| `--depth` | exit | edges | `no_supported_resource_evidence` | victim `DEPTH_LIMIT` observations | wall time |
| --- | --- | --- | --- | --- | --- |
| 1 | 0 | none | true | 5 | 2.71 s |
| 2 | 0 | none | true | 3 | 3.33 s |
| 3 | 0 | none | true | 15 | 6.23 s |

- The same through the in-process API gives the same result, for both state-setters, with javap
  21.0.12.1 and with JDK 8 javap 1.8.0_502 (outputs identical apart from timing).
  - javap calls per depth: 7, 8, 12.
  - The writes are found at every depth: `setUp` writes `JSON.defaultTimeZone` and
    `JSON.defaultLocale` (`DateFieldFormatTest.setUp@5` and `@11`, attributed `via SETUP`).
  - The victim's reads of those fields are deeper than 3. So the result is "no supported evidence",
    with `DEPTH_LIMIT` saying where the walk stopped, never "independent".
- FJ-02, same API, depths 1–3, both javaps: no edge at any depth.

**Exploration only — depth cap lifted in memory by a scratch script; the code and the contract
still accept only depths 1–3:**
- FJ-01: the edge appears at **depth 4**, on both fields. The read path is
  `DateTest.test_date@69 > JSON.toJSONStringWithDateFormat@10 > JSON.toJSONString@21 >
  JSONSerializer.<init>@21` (`defaultTimeZone`; `defaultLocale` is `@28`). Every offset matches the
  JDK 8 javap excerpt. 7.5 s.
- FJ-02: no edge at depth 4 (12.9 s). The edge appears at **depth 5** (26.3 s), victim accesses
  75. The read path is `DefaultExtJSONParser_parseArray.test_7@6 > DefaultJSONParser.<init>@8 >
  DefaultJSONParser.<init>@8 > JSONScanner.<init>@2 > JSONLexerBase.<init>@10`
  (`defaultTimeZone`; `defaultLocale` is `@17`). The write is `DateParserTest.setUp@5 via SETUP`.
  At the same depth the walk also reaches the read named in claim C6, by a second path:
  `test_7@28 > DefaultJSONParser.parseArray@3 > DefaultJSONParser.parseArray@464 >
  DefaultJSONParser.parseObject@1280 > TypeUtils.cast@536` (also `TypeUtils.cast@625`).

**defaultTimeZone or defaultLocale?** Static analysis cannot tell. Both state-setters write both
fields in the same `setUp`, and the victims read both. Reasoning from the test's own constants
(no test was run):
- `DateTest` expects `"2011-12-18 00:23:07"` for `1324138987429` ms. Computed: that is
  Asia/Shanghai time (+8); UTC gives `2011-12-17 16:23:07`.
- The pattern `yyyy-MM-dd HH:mm:ss` is all digits, so the locale cannot change it.
- So FJ-01's failure follows `defaultTimeZone`. The POC's `cause_classification.csv` label
  `JSON.defaultLocale` names the other field written in the same `setUp`.
- Not yet confirmed by a run (that would be Member 2's runner).

**Limitations discovered:**
- **Depth 1–3 does not reach either real fastjson case.** FJ-01 needs depth 4 and FJ-02 depth 5.
  The default depth 2 (ADR-002) is enough for the fixture, not for these. Raising the accepted
  range changes the contract (all three members).
- **POC claim C6's location is confirmed, its depth is not.** C6 says FJ-02's victim reads
  `JSON.defaultTimeZone` at `TypeUtils.cast@536`, "two hops down" (POC hops 2 = our depth 3).
  Following calls from the victim, this extractor reaches that same read only at depth 5, four
  calls below the test method (path above). The POC counted reachability differently (ADR-002
  already flagged the numbering). C6 is a joint row, so it is flagged here, not edited.
- Both fields come out as edges. The extractor reports every shared resource and cannot rank
  them; picking the causal one needs the runner.

**Integration check (Member 3's PR #21, merged):** `eval/report.py` now calls `find_edges` +
`report_fields` instead of its own copy, and `run_w9_integration.py` uses `DEFAULT_DEPTH`.
Member 3's recorded `eval/reports/f2.json` (`VERIFIED`) was compared with a live run of this
extractor on the F2 pair: `shared_resource`, `polluter_write_location` (`enableTurbo@4`) and
`victim_read_location` (`FeatureFlags.isTurboEnabled@2`) are identical, and the report carries the
7 fixed limitation lines. The end-to-end run itself is Member 3's ([[evidence-m3]]).

## Depth decision data for ADR-006 (2026-10-10)

**Requirement:** decide whether depth 1–3 is enough, using measurements rather than the two
fastjson pairs alone. The yardstick is the POC's real runs: `od_relevant` in
`POC/results/scan_FJ-01.csv` and `scan_FJ-02.csv`. It is `YES` when running that candidate before
the victim changed the victim's result.

**Exploration only.** A scratch script (`depth_yield.py`) lifts the depth cap in memory. For every
POC candidate it runs `analyse_test` + `find_edges` against the victim and counts the candidates
with at least one edge, split by `od_relevant`. Same fastjson build as Phase 5 part 2, javap
21.0.12.1, one run.

| Case | Depth | Real (`YES`) with edge | Not real (`NO`) with edge | Seconds (all candidates) |
| --- | --- | --- | --- | --- |
| FJ-01 | 1 / 2 / 3 | 0/42 · 0/42 · 0/42 | 0/30 · 0/30 · 0/30 | 22.4 · 25.9 · 30.2 |
| FJ-01 | 4 | **42/42** | 1/30 | 34.8 |
| FJ-01 | 5 | 42/42 | 1/30 | 45.8 |
| FJ-02 | 1 / 2 / 3 | 0/24 · 0/24 · 0/24 | 0/698 · 0/698 · 0/698 | 143.3 · 148.3 · 156.1 |
| FJ-02 | 4 | 1/24 | 0/698 | 163.2 |
| FJ-02 | 5 | **24/24** | 0/698 | 180.7 |

No candidate failed to analyse (errors 0 in every row).

- **The one false edge** (FJ-01, depths 4 and 5) is `DateTest2#test_date`. It writes
  `JSON.defaultTimeZone` at `DateTest2.test_date@5`, but sets America/Chicago (source line 22) and
  restores the old value in `tearDown` (line 18). In the POC's run the victim still failed after
  it. This is the contract limitation "written values are not modelled".
- **Fixture at depths 2–5** (all 156 ordered pairs, same scratch matrix as Phase 5 part 1, main
  `6b5e065`): exactly the 4 ground-truth edges at every depth, nothing else.
- **Limitation:** two cases from one project. The data shows depth 4–5 is needed and cheap in
  false edges here; it does not show the bound 5 is right elsewhere.
- Decision proposed from this: [[03-Design/decisions/ADR-006-evidence-depth-auto-deepen]]. Not
  implemented.

## Phase 6: lifecycle writes as polluter edges, pair-mode input error (2026-10-10)

**Requirement (Phase 6 list):**
- F1 has exactly one edge.
- A write in `setUp` or `<clinit>` is still attributed.
- An access found only at depth 2.
- No shared resource gives an empty edge list plus the flag.
- A nonexistent test or a missing directory gives an error and a non-zero exit.

Already covered before this phase: F1, depth-2-only, the empty list plus flag, the missing
directory and unknown method. `setUp`/`<clinit>` attribution was tested only in single-test
mode, never as the polluter side of a pair edge.

- Files:
  - `evidence/tests/test_extract.py`: `PairSelfTest.test_polluter_write_in_junit3_setup_is_an_edge`,
    `PairSelfTest.test_polluter_write_in_test_class_clinit_is_an_edge`, and
    `CommandLineTest.test_unknown_victim_in_pair_mode_is_an_input_error`.
  - New self-test input `evidence/tests/resources/m1-selftest/src/test/java/m1selftest/M1ClinitReaderSelfTest.java`.
    It reads `m1.selftest.clinit`, which `M1LifecycleSelfTest`'s static initialiser writes. Before
    this, nothing read that property, so a `<clinit>` edge could not occur.
- Expected offsets read by hand from JDK 8 javap (`javap -c -p`, 1.8.0_502):
  - `M1Junit3SelfTest.setUp`: `1: putstatic … SelfTestState.counter`.
  - `M1SelfTest.writesAndReads`: `4: getstatic … SelfTestState.counter`.
  - `M1LifecycleSelfTest.<clinit>`: `4: invokestatic … System.setProperty` (key `m1.selftest.clinit`).
  - `M1ClinitReaderSelfTest.readsClinitProperty`: `2: invokestatic … System.getProperty`.
- FR-3 check: the contract already settles it. A test class's own `<clinit>` is a root
  (`via CLINIT`); another class's `<clinit>` is reported as `IMPLICIT_CLINIT` and never
  attributed to the next test. No design change was needed.
- Commands and real results (`mvn -B -q test-compile` of both projects, exit 0):
  - `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest -v evidence.tests.test_extract` → `Ran 33 tests … OK`
    (javap 21.0.12.1).
  - Same with JDK 8 javap (`FLAKETRACE_JAVAP` → `ft-jdk8` image) → `Ran 33 tests in 74.368s … OK`.
  - The CLI with an unknown victim class prints `error: test class not found in project classes:
    m1selftest.NoSuchTest` and exits 2.
- Mutation check (scratch script, roots filtered in memory):
  - `SETUP` roots dropped → only the `setUp` test fails.
  - `CLINIT` roots dropped → only the `<clinit>` test fails.
  - Nothing dropped → both pass.
  - The first version of the script filtered the wrong value (`find_roots` returns
    `(chain, roots)`) and so changed nothing. It was fixed before these results.
- Limitation: a test class's `<clinit>` runs once per JVM, on first use, but its writes are
  attributed to every test of that class. Whether it has already run is execution timing, which
  is not modelled (contract limitation 6).

## ADR-006 implemented: depth 1–5 and pair-mode auto-deepening (2026-10-10)

**Requirement:** ADR-006, accepted by all three members (PRs #28, #29, #33). Accept depths 1–5.
Pair mode deepens one level at a time while there is no edge and a walk hit `DEPTH_LIMIT`, and
records `depth_requested`/`depth_used`. Member 2's request: `report_fields` adds a `limitations`
line when the reported evidence is deeper than depth 2.

- **Code** (`evidence/extract.py`):
  - `MAX_DEPTH = 5`.
  - `analyse_pair(project, polluter_id, victim_id, depth=2, deepen=True)` (loop in `_analyse_pair`).
  - The CLI's pair mode uses it, and `--no-deepen` is added.
  - `report_fields` adds the depth line.
  - `analyse_test`/`find_edges` are unchanged, so callers that have not switched keep today's
    behaviour.
- **Contract** (`docs/contracts/resource-evidence.md`): edited exactly as ADR-006's "Proposed
  contract change" says. Depth range 1–5 and deepening in Terms; `--no-deepen`; `depth_requested`
  and `depth_used` in Output 2; `analyse_pair` in "Calling it from another component"; the depth
  line in the projection table.
- **Tests** (`evidence/tests/test_extract.py`, 6 new):
  - `DeepeningTest`: deepens 2 → 4 to the first edge; `deepen=False` stays at 2 with `DEPTH_LIMIT`;
    a pair with nothing cut off does not deepen; the report names evidence deeper than 2.
  - `GroundTruthTest.test_ground_truth_pairs_are_found_without_deepening`: all fixture pairs stay
    at `depth_used` 2 with no depth line.
  - `CommandLineTest.test_pair_mode_deepens_and_no_deepen_stops_it`.
  - Changed: `test_unsupported_depth_is_an_input_error` now uses `--depth 6`.
- **Expected values** read by hand from JDK 8 javap: `M1DepthSelfTest.level4` is
  `0: getstatic … SelfTestState.counter`; `M1SelfTest.writesAndReads` is `1: putstatic …`.
- **Commands and real results** (both projects compiled with `mvn -B -q test-compile`, exit 0):
  - `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest -v evidence.tests.test_extract` →
    `Ran 39 tests in 51.710s … OK` (javap 21.0.12.1).
  - Same with JDK 8 javap → `Ran 39 tests in 96.183s … OK`.
  - Member 3's tests: `python3 -m unittest discover -s eval/tests` → `Ran 68 tests … OK`.
  - Member 2's CLI tests, which call this extractor end to end:
    `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest runner.tests.test_cli` → `Ran 20 tests … OK`.
- **Mutation check** (scratch script; extractor source mutated in memory only):
  - Never deepen → the deepening and depth-line tests fail.
  - Ignore the "cut off" condition → only the no-cut-off test fails.
  - Drop the depth line → only the depth-line test fails.
  - The CLI test runs the unmutated file in a subprocess, so it is not affected by design.
- **fastjson through the real CLI**, default settings (start at 2, deepen), same build as Phase 5
  part 2, javap 21, one run each:

  | Case | `depth_requested` | `depth_used` | Edges | Wall time |
  | --- | --- | --- | --- | --- |
  | FJ-01 (`DateFieldFormatTest#test_format_` → `DateTest#test_date`) | 2 | 4 | `JSON#defaultLocale`, `JSON#defaultTimeZone` | 7.73 s |
  | FJ-02 (`DateParserTest#test_date_0` → `DefaultExtJSONParser_parseArray#test_7`) | 2 | 5 | same two | 24.99 s |

  The report fields for FJ-01 are: write `DateFieldFormatTest.setUp@11`, read
  `JSONSerializer.<init>@28`, plus the lines "This evidence is 3 calls deep (depth 4, above the
  default 2)…" and "Another shared resource is not shown in this report:
  com.alibaba.fastjson.JSON#defaultTimeZone".
- **Limitations:**
  - **The report's single resource is not the causal one on FJ-01/FJ-02.** Both fields are equally
    shallow, and the contract's tie-break (`resource_id`) puts `defaultLocale` first. The real
    cause, `defaultTimeZone` (Phase 5 part 2), is named only in `limitations`. Static evidence
    cannot rank causes; this is documented, not changed.
  - FJ-01/FJ-02 are BRITTLE cases, out of scope for Iteration 1 outcomes (contract Q6, Member 3),
    so this changes their evidence, not their outcome.

## ADR-007 check: several polluters on fixture F3 (2026-10-10)

**Requirement:** before agreeing to ADR-007, confirm that the merged W10 code combines this
component's pair evidence as the ADR says, using `analyse_pair` per polluter.

- Code read on main `2a40f58`: `runner/cli.py` `resource_fields` calls `analyse_pair(classes,
  polluter, victim)` once per polluter; `combine_fields` applies the three cases of ADR-007.
- Command (fixture compiled with `mvn -B -q test-compile`, exit 0):
  `python3 -m runner diagnose --project fixtures/od-fixture --victim odfixture.ToggleVictimTest#expectsNotBothFlagsSet --records <scratch>`
  → exit 0 in 26 s. Real output: `VERIFIED`; polluters `setFlagA`, `setFlagB`; "12 earlier
  tests -> 2 polluters in 10 runs"; reproduced 20/20 (lower bound 0.839), alone 0/20.
- Report: `shared_resource` = `odfixture.Toggles` `flagA` (write `ToggleAPolluterTest#setFlagA@1`,
  read `ToggleVictimTest#expectsNotBothFlagsSet@0`), and the `limitations` line "Polluter
  odfixture.ToggleBPolluterTest#setFlagB: shared resource odfixture.Toggles#flagB is not shown in
  this report".
- Limitation: the report shows one resource; `flagB` is only named until the schema allows one
  edge per polluter (ADR-007, long-term shape).

## ADR-008 check: fixture cases F4 and N3, and F4 end to end (2026-10-11)

**Requirement:** before ticking ADR-008 (M1 row "for information"), confirm that M3's new fixture
cases and M2's runner side leave this component correct. No change to `evidence/`.

- **Fixture with F4/N3** (M3's PR #45, merged; main `9dcd439`). Both projects compiled with
  `mvn -B -q test-compile` (exit 0). Command:
  `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest evidence.tests.test_extract` → `Ran 39 tests … OK`
  (javap 21.0.12.1, Python 3.13). `GroundTruthTest` now covers the 16 fixture tests, 240 ordered
  pairs, and still finds exactly the ground-truth edges. The same suite was also OK on M3's branch
  before the merge (commits `50a8bd8` and `e0cb904`).
- **F4 pair** (`analyse_pair` + `report_fields`, scratch script): `depth_used` 2,
  `odfixture.LateFlag#isSet`, write `ZzzLatePolluterTest.setLateFlag@1`, read
  `AlwaysEarlyVictimTest.expectsLateFlagUnset@0`.
- **N3** (`EnvDependentNegativeTest#onlyFailsUnderCI`): no accesses and no unsupported observations;
  `java.lang.System` is listed in `external_calls_not_followed` (its `System.getenv` call).
  Environment variables are not a modelled resource (fixed limitation 4), and a Java test cannot set
  one, so it cannot be a polluter channel.
- **Other members' suites on main `9dcd439`** (same machine, run as CI does):
  eval `Ran 80 tests … OK`; runner (`FLAKETRACE_REQUIRE_JVM=1`) `Ran 108 tests … OK`.
- **M2's PR #49** (runner side of ADR-008, commit `fa621af`, not merged at the time): it does not change
  how `runner/cli.py` calls `analyse_pair`/`report_fields`. Evidence 39 OK, eval 80 OK, runner 144 OK.
  Real command `python3 -m runner diagnose --project fixtures/od-fixture --victim
  odfixture.AlwaysEarlyVictimTest#expectsLateFlagUnset --records <scratch>` → exit 0 in 17 s:
  `VERIFIED`, "reproduced in shuffled order (seed 1) after 2 shuffled orders", resource
  `odfixture.LateFlag isSet` (write `@1`, read `@0`, as above), reproduced 20/20 (lower bound 0.839),
  alone 0/20.
- **F3 on main `39b2dff`** (for panel action A6): the same command for
  `odfixture.ToggleVictimTest#expectsNotBothFlagsSet` → exit 0 in 18 s, `VERIFIED`, "14 earlier
  tests -> 2 polluters in 10 runs". Execution record step counts: search 14, minimise 10 (1 re-check
  + 9 `ddmin`), verify 20, alone 20.
- **Limitations:** all runs on javap 21 here; CI's evidence job runs the suite on JDK 8 for each PR.
  The F4 end-to-end run used PR #49 before review and merge.

## Mid Report chapter 6 (module section): test suite and F2 command re-run (2026-10-12)

**Requirement:** the module section of the Mid Report (`chapter6_module_m1.tex`) must give a setup
that can be reproduced and a real result for it. No change to `evidence/`.

- **Where:** run with Claude in the team's cloud environment, not on Member 1's own machine
  (Linux 6.18, Apache Maven 3.9.11, OpenJDK and javap 21.0.12.1, Python 3.13.16), on main `82df9fa`.
  Member 1's Windows machine did not have Maven on `PATH` at the time, so the run could not be
  repeated there yet.
- **Commands and results:**
  - `mvn -B -q -f fixtures/od-fixture/pom.xml test-compile` → exit 0.
  - `mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile` → exit 0.
  - `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest -v evidence.tests.test_extract`
    → `Ran 39 tests in 60.392s … OK` (exit 0), all seven test classes passing.
  - `python3 -m evidence.extract --classes fixtures/od-fixture/target/classes --test-classes
    fixtures/od-fixture/target/test-classes --polluter odfixture.FeaturePolluterTest#enableTurbo
    --victim odfixture.FeatureVictimTest#expectsTurboDisabled` → exit 0; `pair` has one edge,
    `sysprop:odfixture.turbo`, write `FeaturePolluterTest.enableTurbo@4` (depth 1), read
    `FeatureFlags.isTurboEnabled@2` (depth 2), `depth_used` 2. Same as Phase 5 part 1 and
    `eval/reports/f2.json`.
- **Limitation:** javap 21 only; CI's `evidence` job runs the same suite on JDK 8 for each PR. A
  run on Member 1's own machine is still to be done once Maven is installed there.

## W16: retired claims in `evidence/` and its note (2026-11-18)

**Requirement:** W16 (FT005, claims ledger G3 and G4): no retired claim in M1's folder or note.
Only wording changed; no code, test, contract or report field changed.

- **Search before the change** (main `0d66ff3`, run in the team's cloud environment with Claude):
  `git grep -n -i -E "1-minimal|never modified|sandboxed|found mechanism|root cause|caused by|explains the failure|passes alone|real cause|the cause" -- evidence docs/04-Implementation/evidence-collector.md`
  → two hits: `evidence/README.md:6` ("the target project's source is never modified", G4) and
  `docs/04-Implementation/evidence-collector.md:51` (`JSON.defaultTimeZone` "the real cause", G3).
- **Change:** the README's opening and §1 of the note now call an edge "a static overlap — a
  possible mechanism, not confirmed as the cause" (G3's wording). The README says only what the
  extractor does to the project (reads `.class` files, writes nothing), not a whole-tool claim.
  The FJ-01 line says the test's constants point to the time zone, but no run has confirmed it.
- **Search after the change**, same command → two hits, both the G3 replacement phrase itself
  ("…not confirmed as the cause"): `evidence/README.md:6` and
  `docs/04-Implementation/evidence-collector.md:23`. No retired claim remains.
- `evidence/extract.py` already had no "cause" or "mechanism" (M2's search, handover note).
- **Not changed, on purpose:** `FIXED_LIMITATIONS` in `evidence/extract.py`. It is the contract's
  fixed list (`docs/contracts/resource-evidence.md`, "Fixed limitations"), so adding the G3
  sentence there is a contract change for all three members; proposed in the PR, not made.
- **Limitation:** a phrase search finds only the words searched for; M3 checks consistency (W16
  verifier).

## W21 part 1: `report_fields` lists every edge (2026-11-18)

**Requirement:** W21 / FT005 / ADR-010: the extra edges must be visible, not only the first.
`report_fields` now also returns `resource_edges`: one entry per edge in the contract's order
(combined depth, then `resource_id`), each `{shared_resource, polluter_write_location,
victim_read_location, depth}`. `shared_resource` and the two locations are unchanged.

- **Test first:** `evidence/tests/test_extract.py`, new class `ResourceEdgesTest` (3 tests; a
  hand-built two-edge pair, so no javap is needed).
  On the unchanged code (main `0d66ff3` + the W16 wording commit), run in the team's cloud
  environment with Claude: `python3 -m unittest evidence.tests.test_extract.ResourceEdgesTest`
  → `Ran 3 tests … FAILED (errors=3)`, each `KeyError: 'resource_edges'`.
- **After the change**, same command → `Ran 3 tests … OK`.
- **Whole suites after the change** (same environment: Linux, Maven 3.9.11, OpenJDK and javap
  21.0.12.1, Python 3.13.16; fixture and self-test compiled with `mvn -B -q … test-compile`, exit 0):
  - `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest evidence.tests.test_extract` → `Ran 42 tests … OK`.
  - Every `eval/tests/test_*.py`, as CI runs them → `Ran 99 tests … OK`.
  - `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest runner.tests.test_cli` → `Ran 63 tests … OK`.
- **Contract:** the projection table in `docs/contracts/resource-evidence.md` gains the
  `resource_edges` row, as ADR-010 (agreed by M1, M2, M3, PR #101) specifies. The PR needs M2's
  and M3's approval.
- **Limitations:**
  - The report does not show `resource_edges` yet: the schema has `additionalProperties: false`,
    and `eval/report.py` builds the report from named keys, so the field is ignored until M3's W19
    (schema v2) copies it.
  - With several polluters, `runner/cli.py`'s `combine_fields` (M2) keeps the first polluter's
    fields, so only that polluter's `resource_edges` would reach the report. Noted for M2.
  - Not run on my own machine yet; M2 verifies W21.

## W21 part 2: the two FT005 controls (2026-11-18)

**Requirement:** W21 / FT005 / ADR-015's control table: two cases where static analysis finds an
edge that is **not** why the victim fails, and FlakeTrace must not call it the cause.

- **Where:** `evidence/tests/resources/ft005-controls/` (a Maven project in M1's folder; M1 chose
  this over adding cases to M3's fixture). Expected results were written in its `EXPECTED.md`
  **before** the project was first compiled or run.
  - Control 1, write-then-restore: `RestoringPolluterTest#pollute` writes `State.restored` and puts
    the old value back, and sets `State.hidden` through reflection; `RestoringVictimTest#check`
    fails only because of `State.hidden`.
  - Control 2, unrelated overlap: `TwoFieldPolluterTest#pollute` writes `State.a` and `State.b`;
    `TwoFieldVictimTest#check` reads both but fails only because of `State.b`.
- **Tests first:** `Ft005ControlsTest` (3 tests) in `evidence/tests/test_extract.py`. Run in the
  team's cloud environment with Claude, before the project was compiled:
  `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest -v evidence.tests.test_extract.Ft005ControlsTest`
  → `FAILED (errors=1)`, "FT005 controls not compiled" (the guard CI relies on).
- **After** `mvn -B -q -f evidence/tests/resources/ft005-controls/pom.xml test-compile` (exit 0),
  same command → `Ran 3 tests … OK`. Real extractor output (javap 21.0.12.1, `depth_used` 2):
  - Control 1: one edge, `controls.State#restored`, writes `pollute@6` and `pollute@10`, read
    `check@1`; observations include `REFLECTION` on the polluter side. No edge on `State#hidden`.
  - Control 2: two edges, `controls.State#a` (write `pollute@1`, read `check@0`) then
    `controls.State#b` (write `pollute@5`, read `check@15`); `shared_resource` is `State#a`.
  All as `EXPECTED.md` predicted.
- **Full diagnosis**, same environment, main `0d66ff3` + this branch's commits:
  `python3 -m runner diagnose --project evidence/tests/resources/ft005-controls --victim controls.RestoringVictimTest#check --records <scratch>`
  → exit 0, `VERIFIED (sequence)`, polluter `controls.RestoringPolluterTest#pollute`, resource
  `State restored` with the line "static overlap: a possible mechanism, not confirmed as the cause",
  reproduced 20/20 (lower bound 0.839), alone (same failure) 0/20. The report's `limitations` carry
  "Written values are not modelled…".
  Same for `controls.TwoFieldVictimTest#check` → exit 0, `VERIFIED (sequence)`, polluter
  `controls.TwoFieldPolluterTest#pollute`, resource `State a` with the same static-overlap line,
  20/20, alone 0/20; `limitations` names "Another shared resource is not shown in this report:
  controls.State#b".
- **Whole evidence suite:** `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest evidence.tests.test_extract`
  (fixture, self-test and controls compiled) → `Ran 45 tests … OK`.
- **What this shows:** in both controls the reruns find the right polluter, but the static edge
  points at a field that is not why the victim fails; neither report calls it the cause.
- **Limitations:**
  - The report lists the extra edge only in `limitations` until M3's W19 copies `resource_edges`.
  - CI compiles only the fixture and the self-test project, so `Ft005ControlsTest` will fail in CI
    until M2 adds `mvn -B -q -f evidence/tests/resources/ft005-controls/pom.xml test-compile` to
    the evidence job's compile step in `.github/workflows/ci.yml` (M2's file).
  - Both controls are hand-made; they show the wording is honest, not how often this happens in
    real projects. Run in the cloud, not yet on my own machine; M2 verifies W21.

## W22 verification: the lifecycle control on my own machine (2026-11-20)

**Requirement:** FT006 / ADR-012 §3: compare normal execution (Maven Surefire) with FlakeTrace's
harness on the lifecycle control, independently of M2 (I am W22's verifier). Run by me on my own
laptop, following "W22 job 3" and "job 4" in [[10-Final1/handover-m1-m3]].

- **Machine:** Windows 11 (64-bit), Oracle JDK 25.0.1, Apache Maven 3.9.9, Python 3.11.9
  (`jsonschema` 4.26.0), repository at `b1843c2` (main, which contains W22). Command Prompt.
- **Surefire:** `mvn -B -q -f runner/tests/resources/lifecycle-control/pom.xml test` → exit 0;
  `TEST-LifecycleControlTest.xml`: `tests="2" errors="0" skipped="0" failures="0"`.
- **Harness, both modes:** `py -3.11 -m unittest -v runner.tests.test_order_runner.TestLifecycleControl`
  → `Ran 3 tests in 5.304s … OK` (`test_class_grouped_runs_class_setup_once`,
  `test_per_method_runs_class_setup_per_test`, `test_unknown_lifecycle_is_refused`).
- **Real command, class-grouped:** `py -3.11 -m runner diagnose --project fixtures/od-fixture
  --victim odfixture.ConfigVictimTest#expectsDefaultMode --lifecycle class-grouped
  --records %TEMP%\ft-records` → `VERIFIED (sequence)`, polluter
  `odfixture.ConfigPolluterTest#pollute`, resource `odfixture.Config mode` (write `pollute@1`,
  read `expectsDefaultMode@1`) with "static overlap: a possible mechanism, not confirmed as the
  cause", reproduced 20/20 (lower bound 0.839), alone (same failure) 0/20.
- **Disposable copy (job 4):** copied `fixtures/od-fixture` without `target\` to
  `%TEMP%\fixture-copy` (`robocopy … /E /XD target`, 23 files), ran the default
  `diagnose` on it → the same `VERIFIED (sequence)` result; afterwards `dir %TEMP%\fixture-copy\target`
  → `File Not Found`: the diagnosis created no `target\` in the project it analysed.

| Path | `first` | `second` | `@BeforeClass` runs |
| --- | --- | --- | --- |
| Maven Surefire | pass | pass | once (both pass) |
| FlakeTrace `per-method` | pass | fail (`AssertionError`, as the test asserts) | once per test |
| FlakeTrace `class-grouped` | pass | pass | once, as under Surefire |

The `per-method` and `class-grouped` rows are what the three harness tests assert; I did not print
the harness output separately. Result: matches the handover's expectations on every step, so
`class-grouped` agrees with Surefire on the control.

**Differences and unclear steps** (for M2):
1. **First harness run failed on my network, not in the code.** The first
   `TestLifecycleControl` run took about 33 minutes and ended `Ran 0 tests … FAILED (errors=1)`:
   `maven_test_classpath` runs `mvn -q … dependency:build-classpath`, and Maven could not download
   `maven-dependency-plugin` 3.7.0's dependencies from `repo.maven.apache.org` (connect/read
   timeouts). `-q` hides the download, so it looked stuck. Fixed by pre-fetching once without `-q`
   and with longer timeouts (`-Daether.connector.connectTimeout=60000
   -Daether.connector.requestTimeout=180000 -Daether.connector.http.retryHandler.count=5`); then
   3 tests OK in 5 s. The handover does not say the first run downloads this plugin.
2. **Python 3.9 does not work.** On my default Python 3.9.13, `pip install -r eval/requirements.txt`
   fails (`No matching distribution found for jsonschema==4.26.0`; 4.25.1 is the newest for 3.9),
   and `diagnose` then stops with `ModuleNotFoundError: No module named 'jsonschema'`. With Python
   3.11.9 everything worked. The README says CI uses 3.11 but gives no minimum version.
3. JDK 25 makes Maven print `WARNING:` lines about restricted and deprecated methods inside Maven's
   own libraries; they did not affect any result.

**Limitation:** one run of each command, on one machine. The diagnoses used `%TEMP%` records, which
are not committed.

## W18 verification: outcome tallies on my own machine (2026-11-20)

**Requirement:** FT003 / ADR-010: the runner counts every repeated phase as a tally (passed,
matched, other, infra), so a victim that fails alone with a *different* failure is no longer
counted as passing alone. I am W18's verifier. Run by me on my own laptop (Windows 11, Python
3.11.9), following "W18" in [[10-Final1/handover-m1-m3]].

- **After the fix**, main `f47b503`:
  - `py -3.11 -m unittest -v runner.tests.test_diagnose.TestTallies runner.tests.test_search.TestRepeat`
    → `Ran 9 tests in 0.004s … OK`: T1 (victim failing alone differently counted as `other`),
    T2 (three different failures in twenty alone runs), T3 (two timeouts alone are `infra`, not
    passes), T4 (a failure seen once and never again is `INCONSISTENT`), the old count fields
    agreeing with the tallies, and `repeat()` tallying each run once.
  - `py -3.11 -m unittest eval.tests.test_report` → `Ran 23 tests in 1.301s … OK` (M3's report
    tests unchanged).
- **Before the fix**, in a throwaway worktree: `git worktree add %TEMP%\ft-w18check e49fa13` (the
  W18 commit, so the new tests are present), then
  `git checkout d1e4d4f -- runner/diagnose.py runner/verify.py runner/cli.py` (only the three code
  files W18 changed, put back to their pre-W18 version), same test command →
  `Ran 2 tests … FAILED (failures=1, errors=1)`:
  - `TestRepeat.test_tallies_each_run_once`: `AssertionError: (2, 4) != RunTally(n=5, passed=1,
    matched=2, other=1, infra=1)`: the old `repeat()` returned two overlapping counts.
  - `TestTallies`: `ImportError: cannot import name 'INCONSISTENT' from 'runner.diagnose'`: the
    old runner had no status for a failure seen once and never again.
  The worktree was then removed (`git worktree remove --force %TEMP%\ft-w18check`).
- **Result:** the tallies behave as ADR-010 specifies, and the tests fail on the code before W18.

**Differences and unclear steps** (for M2):
1. The handover's "before" step, `git checkout d1e4d4f -- runner`, also restores the old *tests*,
   which do not contain `TestTallies`, so it cannot show the defect. Checking out only the three
   changed code files at the W18 commit (above) does what was intended.
2. The handover says to run from `m2/w18-tallies`; it is merged, so I ran from main.

**Limitation:** these are scripted unit tests (no JVM); they show the counting, not a real
diagnosis. `decide()` reading the tallies is W19 (M3), verified separately.

## W19 verification: verdict contract v2 on my own machine (2026-11-20)

**Requirement:** FT003 / ADR-010. A victim that fails alone with a *different* failure must not
be `VERIFIED`, and the other alone cases (some runs differ, infrastructure failure, a failure that
never comes back) must behave as agreed. I am W19's verifier (ADR-010 tests T1–T6). Run by me on
my own laptop (Windows 11, Oracle JDK 25.0.1, Maven 3.9.9, Python 3.11.9), on `main` at `03c9b30`.

- **CI's eval tests** (the same module list as `ci.yml`): `py -3.11 -m unittest
  eval.tests.test_baseline eval.tests.test_examples eval.tests.test_outcome eval.tests.test_report
  eval.tests.test_schema_validator eval.tests.test_stats eval.tests.test_yield_report` → `Ran 122
  tests in 2.810s … OK`. M3 recorded 119 when W19 was built; later merges added tests.
- **T1–T4, scripted:** `py -3.11 -m unittest -v eval.tests.test_report.TestAssembleReport` → `Ran 18
  tests in 1.153s … OK`, including:
  - `test_victim_fails_alone_differently_blames_no_test` (T1);
  - `test_victim_fails_alone_differently_intermittently_blames_no_test` (T2);
  - `test_alone_infrastructure_failure_blames_no_test` (T3);
  - `test_inconsistent_gives_a_real_report_not_unhandled` (T4).
- **T5, fixture N4 through the real command:** `py -3.11 -m runner diagnose --project
  fixtures/od-fixture --victim odfixture.DualFailureVictimTest#expectsStateTwo --records
  %TEMP%\ft-n4` printed `UNRESOLVED (VICTIM_FAILS_ALONE_DIFFERENTLY)`, `reproduced: 20/20 (lower
  bound 0.839)`, `alone (same failure): 0/20`, with no polluter named. `echo exit %ERRORLEVEL%` →
  `exit 0`, not 3. This matches N4's ground truth, which M3 wrote before its first run.
- **T6, an existing case unchanged:** the same command on F1
  (`odfixture.ConfigVictimTest#expectsDefaultMode`, `--records %TEMP%\ft-f1`) printed `VERIFIED
  (sequence)`, polluter `odfixture.ConfigPolluterTest#pollute`, resource `static-field
  odfixture.Config mode (write …ConfigPolluterTest#pollute@1 -> read
  …ConfigVictimTest#expectsDefaultMode@1)` with `static overlap: a possible mechanism, not confirmed
  as the cause`, `reproduced: 20/20 (lower bound 0.839)`, `alone (same failure): 0/20` → `exit 0`.
- **Source left unchanged:** `git status --short` after both runs showed no change under
  `fixtures/` (diagnose works on a disposable copy).

**Result:** the FT003 regression (N4) cannot get `VERIFIED` through the real command, and the
scripted T1–T4 behave as ADR-010 says. Together with my W18 verification, FT003's fix has now
been independently reproduced. It still needs the supervisor's acceptance.

**Differences and unclear steps** (for M3):
1. "Alone (same failure): 0/20" is the same line for N4 and F1. It is the reason, not the alone
   count, that tells them apart. The report's `victim_alone` tally shows the different failures
   (`other`), but the one-line summary does not. A reader of the CLI alone could miss why N4 is
   `UNRESOLVED`. Worth a summary line, e.g. `alone (other failure): 20/20` (M2's CLI).
   *M3 confirmed this on PR #114 (2026-11-20). In M3's own rerun, N4's report has `victim_alone`
   `{n: 20, passed: 0, matched: 0, other: 20}`, so the data is right and the gap is presentation
   only: `runner/cli.py` prints only `matched/n`. M3 has raised it with M2.*
2. I did not copy the N4 `.report.json` fields into this entry; the summary lines above are
   what I recorded.
3. The T1–T6 names are not in the test names, only in their docstrings, so finding them needs
   `-v`.

**Limitation:** T1–T4 are scripted unit tests. Only T5 (N4) and T6 (F1) went through the real
runner and JVM. T6 is covered on all seven earlier cases by the integration run below.

**T6 on every fixture case: M3's integration tool, rerun by me** (same laptop, same day). The
tool overwrites `eval/reports/*.json` and calls `diagnose()` in place, so I ran it in a throwaway
worktree, not in my checkout:
- `git worktree add --detach %TEMP%\ft-w9 origin/main` → `HEAD is now at 03c9b30`.
- `py -3.11 eval\tools\run_w9_integration.py > %TEMP%\ft-w9.log 2>&1` → `exit 0`.
- `findstr /C:"outcome:" %TEMP%\ft-w9.log`:

  | Case | My run | M3's committed report |
  | --- | --- | --- |
  | F1 | `VERIFIED None` | `VERIFIED` |
  | F2 | `VERIFIED None` | `VERIFIED` |
  | F3 | `CANDIDATE None` | `CANDIDATE` (`DELETION_EVIDENCE_INCOMPLETE`) |
  | F4 | `VERIFIED None` | `VERIFIED` |
  | N1 | `UNRESOLVED VICTIM_FAILS_ALONE` | same |
  | N2 | `UNRESOLVED VICTIM_FAILS_ALONE` | same |
  | N3 | `UNRESOLVED NOT_REPRODUCED` | same |
  | N4 | `UNRESOLVED VICTIM_FAILS_ALONE_DIFFERENTLY` | same |

- `findstr /C:"Traceback"` found nothing. "Error" matched only `AssertionError` in the printed
  diagnoses.
- Details from the log:
  - every case: `source_integrity … 26 files hashed (SHA-256) before and after; all identical`;
  - F3: `minimise_runs=9`;
  - F4: reproduced through `reproducing_seed=6` after `shuffled_orders=7`;
  - N2, random by design: `alone_tally` `passed=9, matched=11`.
- `git status --short` in the worktree listed the eight rewritten `eval/reports/*.json`, as
  expected. `git worktree remove --force %TEMP%\ft-w9` deleted the worktree, and my own checkout
  showed no change.
- **N4 detail:** the runner's own status for N4 is still `POLLUTER_FOUND`, naming
  `DualFailurePolluterTest#setState`, with `alone_tally=RunTally(n=20, passed=0, matched=0,
  other=20, infra=0)`. The report is `UNRESOLVED (VICTIM_FAILS_ALONE_DIFFERENTLY)` and blames no
  test. So the FT003 protection sits in W19's decision step, which reads the alone tally, not in
  the runner's search. This matches the W18 handover note ("in T1 the runner still names P").

This run used `per-method`, the default at `03c9b30`, which is the same setting as M3's committed
reports. The verdicts under the new `class-grouped` default (PR #113) have not yet been rerun by
me.

## PR #106 check: the report schema v2 against `report_fields` (2026-11-20)

**Requirement:** PR #106 (W19, schema v2) changed the report contract, and contract changes need
all three members (CONTRIBUTING). I approved it on 2026-11-18 with no written check. This records
the check behind that approval: every field my `report_fields` hands to Member 3's report must be
valid under `eval/schema/report.schema.json`, including M2's new optional `depth` on
`resourceEdge` (minimum 1).

**File/function:** `evidence/tests/test_extract.py`, new `ReportSchemaContractTest`, which reads
the schema (it does not edit it) and runs `report_fields` on eight pairs:
- the first polluter of F1 to F4;
- both FT005 controls (the two-field control has 2 edges);
- one self-test pair with an edge;
- one self-test pair with no edge, so `shared_resource` and both locations are `null`.

For each pair, every returned key must be a schema property and must validate against it.

**Run 1, in the assistant's Linux cloud container, not my laptop** (OpenJDK 21.0.13, Maven 3.9.11,
Python 3.13, `jsonschema` 4.26.0), at `188e1ec` plus this test:
- `mvn -B -q -f fixtures/od-fixture/pom.xml test-compile`, the same for `m1-selftest` and
  `ft005-controls` → exit 0 each.
- `python3 -m unittest -v evidence.tests.test_extract.ReportSchemaContractTest` → `Ran 1 test …
  OK`.
- To check that the test can fail, `depth` was set to `-1` in `report_fields` for one run, at
  `f47b503`, whose `extract.py` is identical (not kept) → `AssertionError: Lists differ: ['-1 is less than the minimum of 1'] != []`. The file was
  then restored.
- `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest evidence.tests.test_extract` → `Ran 46 tests …
  OK`.
- A one-off script (not committed) also compared each report's `resource_edges` with the
  extractor's output for the same pair. F1, F2 and F4 are identical. F3's report holds 2 edges,
  which is the union of both polluters' edges (one each), as M2's `combine_fields` builds it.

**Run 2, on my laptop, by me** (Windows 11, Oracle JDK 25.0.1, Maven 3.9.9, Python 3.11.9), at
`188e1ec` plus this test:
- the three `mvn -B -q … test-compile` commands above → `exit 0` each (checked with
  `echo %ERRORLEVEL%`);
- `py -3.11 -m unittest -v evidence.tests.test_extract.ReportSchemaContractTest` → `Ran 1 test in
  7.728s … OK`;
- with `set FLAKETRACE_REQUIRE_JVM=1`, `py -3.11 -m unittest evidence.tests.test_extract` → `Ran 46
  tests in 56.034s … OK`.

Maven printed JDK 25 warnings ("restricted method", "sun.misc.Unsafe") from its own jars (jansi,
guava). They come from Maven itself, not from FlakeTrace, and did not change any exit code. The
same tests pass on JDK 21 (container) and JDK 25 (my laptop); CI uses JDK 8.

**Result:** schema v2 accepts everything `evidence/` produces, with no change to the contract or
to `extract.py`. CI's `evidence` job already installs `jsonschema` and compiles all three class
sets, so the check now runs on every PR. A future change on either side of this boundary fails CI
instead of breaking reports.

**Limitation:** this test checks the fields' **shape**, not their meaning. Whether a static
overlap is the right edge is still covered by `FixturePairTest` and `Ft005ControlsTest`. It also
does not run `eval/report.py`; that file belongs to M3.

## W25 part 1: `rank_candidates`, the ranking rule, written test-first (2026-11-20)

**Requirement:** ADR-014 §5 and FT007. Rank candidate polluters by static evidence, using a fixed
tuple with no weights:
1. the number of resources the candidate writes and the victim reads;
2. the shallowest such edge;
3. the original position.

No candidate is ever dropped, and a per-test cache makes ranking cost N + 1 analyses. Plan rule 4
says the rule must be committed **before** it meets any ground truth. So these tests use only my
own classes: hand-built analyses, and the FT005 controls. No fixture pair and no fastjson case
was ranked.

**File/function:** `evidence/extract.py`: `AnalysisCache`, `RankedCandidate`, `rank_candidates`.
Tests in `evidence/tests/test_extract.py`:
- `RankCandidatesTest`, 6 tests, no JVM. They cover ADR-014's scripted "candidate 9 of 10 is the
  only one with an edge", no evidence giving exactly the original order, more resources before
  shallower before earlier, edge depth taken as the deeper side, the candidate set unchanged, and
  reasons in the `resource_edges` shape.
- `RankCandidatesControlsTest`, 4 tests, on `ft005-controls`. They cover the restoring polluter
  ranking first, N + 1 analyses with none repeated on a second ranking, an unanalysable
  candidate kept with a note, and an unanalysable victim raising an error.

**Runs, in the assistant's Linux cloud container, not my laptop** (OpenJDK 21.0.13, Maven 3.9.11,
Python 3.13), at `188e1ec` plus the PR #106 check:
- **Before the code (test-first):** `python3 -m unittest evidence.tests.test_extract.RankCandidatesTest
  evidence.tests.test_extract.RankCandidatesControlsTest` → `Ran 10 tests … FAILED (errors=10)`,
  with 7 × `AttributeError: module 'evidence.extract' has no attribute 'AnalysisCache'` and 3 ×
  `… has no attribute 'rank_candidates'`.
- **After:** the same command → `Ran 10 tests … OK`.
- `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest evidence.tests.test_extract` → `Ran 56 tests … OK`.

**On my laptop, by me** (Windows 11, Oracle JDK 25.0.1, Maven 3.9.9, Python 3.11.9), on
`m1/w25-rank-rule` (based on `0071d9c`), with the class sets compiled as in the PR #106 entry:
- **Before the code:** the patch was applied, its `evidence/extract.py` change saved to a file
  (`git diff evidence/extract.py > %TEMP%\rank-code.diff`), and only that file put back to the
  committed version (`git checkout -- evidence/extract.py`). The same two-class command then gave
  `Ran 10 tests in 0.006s … FAILED (errors=10)`, with 7 × `AttributeError: module
  'evidence.extract' has no attribute 'AnalysisCache'` and 3 × `… has no attribute
  'rank_candidates'`.
- **Code put back:** `git apply %TEMP%\rank-code.diff`. Then `git diff --stat evidence/extract.py`
  showed `72 insertions(+)`, the same as the patch.
- **After:** `py -3.11 -m unittest -v evidence.tests.test_extract.RankCandidatesTest
  evidence.tests.test_extract.RankCandidatesControlsTest` → `Ran 10 tests in 3.898s … OK`.
- With `set FLAKETRACE_REQUIRE_JVM=1`, `py -3.11 -m unittest evidence.tests.test_extract` → `Ran 56
  tests in 70.644s … OK`.

**Result:** the rule exists, is tested on non-ground-truth classes, and is fixed by this commit.
That commit must come before any ranked run on F1–F4, N1–N4 or FJ-03 (ADR-014 evidence items 4–5,
measured by M3). M2 is asked to review the rule before any measurement.

**Limitations:**
- The rule has **not yet been measured** on any case. Whether `ranked` reaches a polluter sooner
  than `original` is unknown until M3's comparison.
- It inherits the extractor's blind spots: reflection, libraries and virtual dispatch give no
  edge, so such a polluter keeps its original position.
- A restoring polluter still ranks first, because values are not modelled.
- `rank_candidates` does not deepen. Deepening is the planner's decision (ADR-014 §6, M2).
- `docs/contracts/interfaces.md` does not yet list `rank_candidates`. ADR-014 §5 defines its
  signature, and I added an optional `cache` argument. Adding it to the contract needs all three
  members, so it is proposed in the PR, not edited here.

## Fix: the second-edge limitation said "not shown" for a listed edge (2026-11-20)

**Requirement:** FT005 and ledger G3: a report must say exactly what it shows. M2's independent
verification of W21 ([[evidence-m2]], "A2", 2026-11-20) found that `report_fields` still wrote
"Another shared resource is not shown in this report: controls.State#b" for control 2. Since
schema v2, `State#b` **is** in `resource_edges`, so that line was false. M2 fixed the same wording
in `runner/cli.py`; this is my half.

**File/function:** `evidence/extract.py` `report_fields`. The line now reads "Shared resource
`<id>` is not the headline resource; it is listed in resource_edges", the same wording as M2's
CLI line. "N further write/read location(s) … are not shown in this report" is unchanged,
because it is still true: `resource_edges` keeps only the first location of each edge.

**Test-first, in the assistant's Linux cloud container** (OpenJDK 21, Maven 3.9.11, Python 3.13),
on `main` at `69cf36f`:
- New test `ResourceEdgesTest.test_a_second_edge_is_named_as_listed_not_as_hidden` (no JVM), and
  `Ft005ControlsTest.test_unrelated_overlap_…` changed to expect the new line.
- **Before the fix:** `python3 -m unittest evidence.tests.test_extract.ResourceEdgesTest
  evidence.tests.test_extract.Ft005ControlsTest` → `Ran 7 tests … FAILED (failures=2)`. Both
  failures were `AssertionError: 'Shared resource … is not the headline resource; it is listed in
  resource_edges' not found in [...]`.
- **After:** the same command → `OK`.
- `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest evidence.tests.test_extract` → `Ran 57 tests … OK`.
- M2's and M3's consumers still pass: `python3 -m unittest runner.tests.test_cli.TestCombineFields
  eval.tests.test_report` → `Ran 34 tests … OK`.
- A search of `*.py`, `*.ts`, `*.tsx` and `*.json` files for "Another shared resource" finds
  nothing.

**On my laptop, by me** (Windows 11, Oracle JDK 25.0.1, Maven 3.9.9, Python 3.11.9), on
`m1/fix-listed-edge-wording` based on `a8f2ab0`:
- Fix taken out: the patch was applied, its `evidence/extract.py` change saved
  (`git diff evidence/extract.py > %TEMP%\wording-fix.diff`), then only that file put back
  (`git checkout -- evidence/extract.py`). `py -3.11 -m unittest
  evidence.tests.test_extract.ResourceEdgesTest evidence.tests.test_extract.Ft005ControlsTest` →
  `Ran 7 tests in 2.678s … FAILED (failures=2)`. The old limitations list held `'Another shared
  resource is not shown in this report: p.State#b'` and `'… controls.State#b'`.
- Fix put back: `git apply %TEMP%\wording-fix.diff`, then `git diff --stat` → `evidence/extract.py |
  6 ++++--`. The same command → `Ran 7 tests in 2.755s … OK`.
- With `set FLAKETRACE_REQUIRE_JVM=1`, `py -3.11 -m unittest evidence.tests.test_extract` → `Ran 57
  tests in 63.044s … OK`.

**Limitation:** M3's committed `eval/reports/f3.json` still holds M2's old CLI line until M3
regenerates the reports (noted by M2). No committed report holds my old line; I checked by the
search above.

## W25: M2's review of the ranking rule, and Interface 5 (2026-11-20)

**Requirement:** plan rule 4 and ADR-014 §5. The ranking rule must be reviewed by M2 before it
meets ground truth. M2 also asked for the rule to be written into the contract.

**M2's review** (message to me on 2026-11-20, answering the three questions in PR #112; quoted in
substance):
1. Ranking does not deepen: "that's the split I want". The planner decides and charges deepening
   to the ledger (ADR-014 §6).
2. An unanalysable candidate kept with a note, and an unanalysable victim raising `ExtractError`:
   "both right". Under `--policy ranked` the runner will catch the error, keep the original
   order, and record a limitation.
3. "The cache is enough": the ledger reads `cache.seconds` and `cache.analysed`, and his deeper
   analyses will go through the same cache.

No ranked run on any fixture or fastjson case has been made by anyone, as far as `main` and the
evidence logs show at `69cf36f`. So the review came before any measurement.

**Contract:** I drafted "Interface 5 — candidate ranking" in `docs/contracts/interfaces.md`. It
describes the merged code (signature, `RankedCandidate`, the rule, never-drops, victim-raises,
the cache and its cost, no deepening, wording) and who does what. It changes no code. It is a
contract change, so it is agreed only when M2 and M3 approve the PR.

**Checked against the code:** every statement in the section was compared with
`evidence/extract.py` at `69cf36f`: `AnalysisCache` (line 677), `RankedCandidate` (line 710),
`rank_candidates` (line 713), and the 10 `RankCandidates*` tests. Nothing was run for this entry.

## W20 verification: deletion checks on my own machine, ADR-011 T1–T5 (2026-11-20)

**Requirement:** FT004 / ADR-011 / Interface 4, step 4: "M1 reproduces T3 independently on
their machine". Every kept test must be shown to be needed by repeated removal, not by ddmin's
single trial. Claim G2 was left `OPEN` pending this reproduction. Run by me on my own laptop
(Windows 11, Oracle JDK 25.0.1, Maven 3.9.9, Python 3.11.9), on `main` at `0467ec2`, with the
default `class-grouped` lifecycle and `--workspace copy`.

- **Scripted, T1, T2 and T5:** `py -3.11 -m unittest -v runner.tests.test_deletion
  runner.tests.test_diagnose.TestDeletionChecks eval.tests.test_report.TestDeletionChecksW20` →
  `Ran 25 tests in 0.493s … OK`, including:
  - T1, `test_ft004_counterexample_drops_the_unneeded_test`, and its shape in
    `test_not_needed_test_is_dropped_and_the_rest_rechecked`;
  - T2, `test_inconclusive_keeps_both_tests` (9 of 20 without Q);
  - T5, `TestDeletionBudget` (4 tests) and `test_a_not_run_check_is_incomplete`;
  - M3's aggregation, including `INCONCLUSIVE` ranking above a short run count.
- **T3, real F3, two polluters:** `py -3.11 -m runner diagnose --project fixtures/od-fixture
  --victim odfixture.ToggleVictimTest#expectsNotBothFlagsSet --records %TEMP%\ft-w20-f3` printed:
  - `VERIFIED (sequence)`, polluters `ToggleAPolluterTest#setFlagA` and
    `ToggleBPolluterTest#setFlagB`;
  - `minimised: 16 earlier tests -> 2 polluters in 9 runs (reduced by single-trial delta
    debugging)`;
  - `deletion: kept tests removed one at a time, 20 runs each (40 runs): 0 dropped as not needed,
    0 inconclusive`;
  - the static-overlap line, `reproduced: 20/20`, `alone (same failure): 0/20, other failure:
    0/20`;
  - `budget: spent 264 invocations, no limit (reserve 60)`, and `exit 0`.

  The report's `deletion_checks`: `setFlagA` `NEEDED` `deletion-run` round 1 `{n: 20, passed: 20,
  matched: 0, other: 0, infra: 0}`; `setFlagB` the same. Outcome `VERIFIED`,
  `candidate_reasons` `[]`. Record step counts: `reproduce 1, alone 20, search 16, minimise 9,
  deletion 40, verify 20`.
- **T4, real F1, one polluter:** the same command for `odfixture.ConfigVictimTest#expectsDefaultMode`
  (`--records %TEMP%\ft-w20-f1`) printed `VERIFIED (sequence)`, polluter `ConfigPolluterTest#pollute`,
  no `deletion:` line, `budget: spent 67 invocations, no limit (reserve 60)`, `exit 0`. Report:
  one check, `pollute` `NEEDED` `alone-check` round 1. Record step counts: `reproduce 1, alone 20,
  search 2, verify 20`, with **no `deletion` step**, so no extra JVM runs (ADR-011 T4).
- **Source:** `git status --short` afterwards showed no change under `fixtures/`.

**Result:** ADR-011 T1–T5 reproduced: T3 and T4 with real runs, T1, T2 and T5 scripted. F3's two
kept tests are each needed in 20 of 20 repeated removals.

**Limitations:**
- One real multi-polluter case (F3). No real case where a kept test is `NOT_NEEDED` or
  `INCONCLUSIVE`; those paths are scripted only.
- "Needed" here means: removing it alone made the victim pass in 20 of 20 runs. It does not test
  every subset.
- T5 (budget ends mid-check) is scripted. I did not run a real diagnosis with a budget limit.

**Unclear steps:** none in the commands. The `minimised:` line still says "reduced by single-trial
delta debugging" even when the deletion line beneath it confirms both tests. This is correct but
easy to misread as a weaker claim. The deletion line is the one that carries G2.

## W25 part 2: my review of M2's `EvidenceRanker` and `choose_order` (2026-11-20)

**Requirement:** Interface 7, step 3: "M1 reviews that P2 and P4 use `rank_candidates` and the
`DEPTH_LIMIT` kind as Interface 2 and 5 define them". The code is M2's `runner/policy.py`
(PR #136), on `main` at `f30d0b7`.

**What I checked, by reading:**
- **P2.** `EvidenceRanker.rank` calls `rank_candidates(project, "Class#method" victim, the
  candidates as "Class#method", depth, one AnalysisCache)`. `TestIdentifier.__str__` gives
  `Class#method`, as Interface 5 needs. The order comes back as Interface 5's `score` tuples, and
  `choose_order` refuses any result that is not the same set (a `Counter` check) and falls back to
  the original order.
- **P3.** An `ExtractError` at the first depth leads to the original order with a note; at a
  deeper depth, the last ranking that worked is kept.
- **P4.** `cut_off` reads each test's Output 1 through `AnalysisCache.get` and looks for
  `unsupported_observations` of kind `DEPTH_LIMIT`, the shape `resource-evidence.md` defines. It
  deepens only when no candidate has `score[0] > 0`, a walk was cut off, depth < 5, and (with a
  seconds limit) analysis time is under 20% of it.

**What I ran, in the assistant's Linux cloud container** (OpenJDK 21, Maven 3.9.11, Python 3.13),
at `f30d0b7`, after compiling the fixture, `m1-selftest` and `ft005-controls`:
- `FLAKETRACE_REQUIRE_JVM=1 python3 -m unittest -v runner.tests.test_policy` → `Ran 19 tests …
  OK`, M2's tests, including the real F1 adapter test.
- **An independent check on my own classes**, which M2's tests do not use: `choose_order("ranked",
  …, ranker=EvidenceRanker(m1-selftest))` for victim `M1DepthSelfTest#callsDown`, candidates
  `M1Junit3SelfTest#testNothing` and `M1SelfTest#writesAndReads`. Result:
  - `depths [2, 3, 4]`: no edge at 2 or 3, and `cut_off(2)` and `cut_off(3)` were both `True`;
  - scores `[(1, 4, 0), (1, 4, 1)]`, both edges at depth 4, `candidates_with_evidence 2`,
    `note None`;
  - `cache.analysed 9`, which is 3 tests × 3 depths, so N + 1 per depth;
  - with an unknown victim (`m1selftest.NoSuch#x`), the original order was kept, with the note
    "ranking fell back to the original order: the victim could not be analysed …".

**On my laptop, by me** (Windows 11, Oracle JDK 25.0.1, Maven 3.9.9, Python 3.11.9), on `main` at
`f30d0b7`, after `mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile`:
- the same probe, run from a copy in `%TEMP%` with `set PYTHONPATH=D:\FlakeTrace` and
  `py -3.11 %TEMP%\p4_probe.py`, gave identical output: `depths: [2, 3, 4] with evidence: 2 note:
  None`, `scores: [(1, 4, 0), (1, 4, 1)]`, `analysed: 9`, `cut_off at 2 = True`, `cut_off at 3 =
  True`, `fallback order kept: True`;
- with `set FLAKETRACE_REQUIRE_JVM=1`, `py -3.11 -m unittest runner.tests.test_policy` → `Ran 19
  tests in 1.224s … OK`.

The probe script is not committed; it lived only in `%TEMP%`. Its code is the
`EvidenceRanker`/`choose_order` call described above.

**Result:** P2, P3 and P4 use my code as Interfaces 2, 5 and 7 define it.

**Findings:**
1. **Contract wording (mine, fixed here).** M2 reads `DEPTH_LIMIT` through `AnalysisCache.get`,
   which is public but was not named in Interface 5. Interface 5 now names `get` and what it
   returns. No code changed. This replaces my earlier idea of a new `depth_limited` method, which
   is not needed.
2. **Minor, M2's call.** `EvidenceRanker.rank` keeps only `test` and `score`. A candidate that
   could not be analysed (Interface 5's `note`) is recorded the same as one with no evidence. The
   `ranking` record line could carry those notes, so M3's measurement can tell the two apart.
3. **Cost, as designed.** Each deeper depth analyses all N + 1 tests again (9 analyses for 3 depths
   here). This is counted in `analysis_seconds`, and it is what Interface 7's 20% share limits.

**Limitation:** my check used fixture-free classes and two candidates only. It shows the rules
work; it says nothing about whether ranking saves runs (M3's measurement).

## W24 verification: ADR-014 evidence item 2 on my own machine (2026-11-20)

**Requirement:** FT007 / ADR-014 / Interface 6, step 4: "M1 reproduces item 2 (a budget too
small to finish gives `UNRESOLVED(BUDGET_EXHAUSTED)` with an account) on their own machine". G8
was left `OPEN` pending this. Run by me on my own laptop (Windows 11, Oracle JDK 25.0.1, Maven
3.9.9, Python 3.11.9), on `main` at `9a6392f`, defaults (`--policy original`, `class-grouped`,
`--workspace copy`). Victim F2, `odfixture.FeatureVictimTest#expectsTurboDisabled`.

M3 used a limit of 72, two above the minimum ([[evidence-m3]]). I used the two boundary values,
69 and exactly 70, so the two runs check different points.

- **Below the minimum, `--budget-invocations 69`:** `error: an invocation limit of 69 is below the
  minimum 70 for n=20: the verification reserve 60, one run of the starting order (8 tests) and
  one candidate pair` → `exit 2`. No run was started.
- **At the minimum, `--budget-invocations 70`:**
  - `UNRESOLVED (BUDGET_EXHAUSTED)`, `reproduced: 1/1 (lower bound 0.207)`, `alone (same
    failure): 0/20, other failure: 0/20`, `search: original order`;
  - `budget: spent 30 of 70 invocations (reserve 60); search tried 1 of 7 candidates; stopped in
    search` → **`exit 0`**, with a report. M2's run of the same command before M3's half merged
    gave exit 3 and no report.
  - The report: `outcome UNRESOLVED`, `unresolved_reason BUDGET_EXHAUSTED`, `candidate_reasons
    []`, and `budget`:
    - `limit_invocations 70`, `limit_seconds null`, `reserve_invocations 60`;
    - `spent {reproduce 8, shuffle 0, alone 20, search 2, minimise 0, deletion 0, verify 0}`;
    - `launches 22`, `wall_seconds 5.0`, `analysis_seconds null`, `policy original`;
    - `exhausted true`, `exhausted_phase search`, `candidates {total 7, tried 1}`.
  - Record lines: `header 1, reproduce 1, alone 20, ranking 1, search 1, budget-stop 1`.
- **No limit (comparison):** `VERIFIED (sequence)`, polluter `FeaturePolluterTest#enableTurbo`,
  static-overlap line, `reproduced: 20/20`, `budget: spent 82 invocations, no limit (reserve 60);
  search tried 7 of 7 candidates` → `exit 0`. These are the same 82 and 7 of 7 that M2 and M3
  recorded.
- **Source:** `git status --short` after the runs showed no change under `fixtures/`.

**The arithmetic checks out.** With a limit of 70 and a reserve of 60, exploration may spend 10:
the reproduce run of the starting order (8) and one candidate pair (2). That is exactly what was
spent (8 + 2), plus the alone check (20), which comes out of the reserve. The next pair would have
crossed the limit, so it was refused and recorded as `budget-stop`. This also shows ADR-014's
item 1 (a limit stops the run before it is crossed) in a real run, although item 1 is M2's.

**Result:** item 2 reproduced independently at the boundary. It agrees with M3's run at 72 (spent
32, 2 of 7 tried): each extra pair the limit allows costs 2 invocations.

**Limitations:**
- Only `--budget-invocations`, only F2, only `--policy original`. `--budget-seconds` was not run.
- I did not run the schema validator on my report. M3 validated hers.
- Item 3 (the reserve holds when the search is exhausted) is M2's and was not re-run by me,
  although the alone check (20) ran in full here.
## FJ-03: why the extractor finds no edge on the real fastjson case (2026-11-20)

**Question (from M2, 2026-11-20):** on FJ-03, `SerializeWriterTest_14#test_writer_1` →
`MaxBufSizeTest#test_max_buf`, the sequence reproduces 20/20, but `resource_edges` is `[]` even
after deepening (`CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`). So `--policy ranked` keeps the
original order on this case. Why?

**Answer: a known blind spot, and the extractor behaved to its specification.**

**From the fastjson source** at `e05e9c5`:
- `SerializeWriter` holds `private final static ThreadLocal<char[]> bufLocal`. The polluter builds
  `new SerializeWriter(strOut, 1)`, a 1-character buffer, and its `close()` stores that buffer with
  `bufLocal.set(buf)` (`buf.length <= 128 KiB`).
- The victim's `new SerializeWriter()` takes it back with `bufLocal.get()`. So `setMaxBufSize(1)`
  no longer throws (`1 < buf.length` is false), and `assertNotNull(error)` fails.

This is a reading of the source, consistent with the premise. It was not confirmed by a run that
changes the code.

**What the extractor reports** (in the assistant's Linux cloud container):
- fastjson was fetched at `e05e9c5`, unmodified (`git status` clean). It was built with OpenJDK
  `1.8.0_514` from Ubuntu's packages (`mvn -B -q test-compile` → exit 0); JDK 21 cannot build it,
  because it lacks `javax.xml.bind`.
- `FLAKETRACE_JAVAP` was set to the JDK 8 `javap`. The extractor is `main` at `2ade4c0`, and a
  one-off script (not committed) called `analyse_pair` and `analyse_test`.
- `analyse_pair`: `depth_requested 2, depth_used 5, edges 0`. Unsupported observations:
  - polluter: `DEPTH_LIMIT` 55, `IMPLICIT_CLINIT` 27, `VIRTUAL_DISPATCH` 6, `REFLECTION` 1;
  - victim: `IMPLICIT_CLINIT` 3, `UNRESOLVED_CALL` 1.
- `analyse_test` at depth 5:
  - polluter: `bufLocal` **READ** at depth 2 in `SerializeWriter.close`, and `java.lang.ThreadLocal`
    in `external_calls_not_followed` (60 accesses, 7 writes, none of them to `bufLocal`);
  - victim: `bufLocal` **READ** twice at depth 4 in `SerializeWriter.<init>`, and
    `java.lang.ThreadLocal` not followed (16 accesses, 0 writes).
- At depth 2 the victim has no access at all; the read is first reached at depth 4.

**Why there is no edge:** an edge needs a polluter WRITE and a victim READ of the same resource.
Here both sides only READ `bufLocal`. The real change is a method call (`ThreadLocal.set`) on the
object the field refers to, inside the JDK, which is not followed. Two fixed limitations cover
this: "Calls into JDK classes and third-party jars are not followed" and "Only static fields and
constant-key system properties are modelled".

**What this means:**
- On FJ-03, ranking keeps the original order **by design**. It is not a ranking defect, and M3's
  measurement should report it as it is.
- A READ on both sides of the same static field is ADR-014 §5's deferred **co-touch** term. It
  would put this polluter first, but **I am not adding it now**: the rule was fixed before ground
  truth (plan rule 4), and FJ-03 is ground truth. Any co-touch rule must be a new, separately
  committed rule, reviewed by M2, and measured on cases other than FJ-03.
- I added this case to the "What breaks" section of [[04-Implementation/evidence-collector]].

**Not run on my laptop:** building fastjson needs JDK 8, and my laptop has JDK 25. M3 reproduced
the build with a portable Temurin 8 on Windows.

**Limitations:** one case; source reading plus static analysis, no runtime observation of
`bufLocal`.

## W23 verification: my independent bundle reproduction, ADR-013 §5 (2026-11-22)

**Requirement:** FT009 / ADR-013 §5 / Interface 8, step 3: "M1, on her own machine, without
Member 2 or 3 at the keyboard: clone at the recorded tool commit · `verify-bundle` · `replay`.
Record: date, machine, JDK, both commands' output, every difference, every step that was unclear.
If it fails, the failure is the finding." Claim G7 and FT009 were left open pending this.

**Who and how:** me, alone. Neither M2 nor M3 was asked anything during the run. The assistant
read the written instructions with me and, after my first attempts failed, turned them into
commands. Those commands and my interpretations are marked below.

**Machine:** my laptop, Windows 11 (build 26300), Oracle JDK 25.0.1, Apache Maven 3.9.9, Python
3.11.9 (`python` and `py -3.11` both 3.11.9). The bundle is M2's F1 bundle, made on JDK 21.0.9,
Maven 3.10.0. The bundle is `eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/`.

### Part 1: following the written instructions alone

- `git clone https://github.com/zoyaahmad428/FlakeTrace.git ft-b2` → `Receiving objects: 100%
  (5382/5382), 14.58 MiB`, `Resolving deltas: 100% (3753/3753), done`.
- From `D:\ft-b2`, the command exactly as the bundle's `replay.md` step 2 writes it:
  `python -m eval.bundle verify 20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode` → `… is not a readable bundle: [Errno 2] No such file
  or directory: '…\\manifest.json'`.
- `python -m runner diagnose --project <project> --victim <Class#method> --bundle eval/bundles`
  (the first line of the README's "Making and checking a bundle") → `The system cannot find the
  file specified.` The same happened with the real victim name in place of `<Class#method>`.

### Part 2: with the instructions interpreted (commands from the assistant)

- **Deviation from `replay.md` step 1.** I did *not* check out the recorded commit `03ada56`. At
  that commit neither the verifier nor the bundle exists:
  - `git ls-tree 03ada56 eval/bundle.py` printed nothing;
  - `git ls-tree 03ada56 "eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/manifest.json"` printed nothing.

  The code replay uses is identical: `git diff --stat 03ada56 HEAD -- fixtures/od-fixture
  runner/replay.py runner/bundle.py runner/order_runner.py runner/diagnose.py
  evidence/extract.py` printed nothing. So I stayed on `main` at `dd3235f`.
- `py -3.11 -m pip install -r eval/requirements.txt` → every requirement already satisfied
  (`jsonschema==4.26.0`).
- **Verify:** `py -3.11 -m eval.bundle verify "eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode"` → `OK: eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode`,
  `exit 0`.
- **Replay** (my interpretation: `<checkout of the subject>` = `fixtures/od-fixture` in this
  clone): `py -3.11 -m runner replay "eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode" --project fixtures/od-fixture
  --bundle %TEMP%\b2-bundle --records %TEMP%\b2-records` → `exit 0`:

  | Row | Bundle → my run |
  | --- | --- |
  | verdict | `VERIFIED -> VERIFIED` **same** |
  | polluters | `odfixture.ConfigPolluterTest#pollute` → the same, **same** |
  | sequence | `20/20 matched -> 20/20 matched` |
  | alone | `20/20 passed -> 20/20 passed` |
  | deletion | `ConfigPolluterTest#pollute NEEDED -> NEEDED` |
  | subject, tool | `03ada56… -> dd3235f…` DIFFERENT (expected: I stayed on `main`; see the deviation above) |
  | JDK | `21.0.9 -> 25.0.1` DIFFERENT |
  | OS | `Windows-11-10.0.26300-SP0 -> Windows-10-10.0.26300-SP0` DIFFERENT (see finding 5) |
  | Maven | `3.10.0 -> 3.9.9` DIFFERENT |
  | timezone, locale, encoding, lifecycle | `Asia/Karachi`, `en_US`, `UTF-8`, `class-grouped`: **same** |

- **My replay's own bundle:** `%TEMP%\b2-bundle\20261122T060836Z-odfixture.ConfigVictimTest#expectsDefaultMode`
  → `py -3.11 -m eval.bundle verify "<that folder>"` → `OK`.
- **Clone unchanged:** `git status --short` showed one untracked file, `ion`, and no tracked file
  changed (nothing under `fixtures/`). `ion` is most likely a by-product of the `<…>` redirections
  in part 1; it is not FlakeTrace output.

**Result:** the F1 bundle **verifies and replays to the same verdict on a second machine**, with a
different JDK (25 vs 21) and Maven (3.9.9 vs 3.10.0). That is FT009's and G7's closing evidence:
someone other than the authors checked a report from its bundle.

### Findings: every step that was unclear (for M2 and M3)

1. **`replay.md` gives the bundle's bare name** (`… verify 20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode`). That fails from the repo
   root, and from inside `eval/bundles` `python -m eval.bundle` cannot be imported. No folder makes
   the line work as written. It should give the path (`eval/bundles/<name>`). (M2, `runner/bundle.py`
   writes `replay.md`.)
2. **`replay.md` step 1 contradicts step 2.** "Check out FlakeTrace at the commit above" (`03ada56`)
   leaves no `eval/bundle.py` and no bundle to verify, because both were committed later. It
   should say which commit to verify with, or record the verifier's commit as well. (M2, M3.)
3. **The README mixes making and reproducing.** "Making and checking a bundle" puts `diagnose
   --bundle` first. A reproducer needs only verify and replay, and nothing says so. (M3.)
4. **`<…>` placeholders break in Windows cmd.** `<` and `>` are redirections, so the README line
   gives `The system cannot find the file specified.` and may leave stray files (finding: `ion`).
   A Windows example with real values is needed. (M3.)
5. **The OS row reports a false difference.** Both machines are Windows 11 build 26300, but the
   bundle says `Windows-11` and my run `Windows-10`. Python's `platform` names Windows 11 differently
   across versions (M2 recorded Python 3.14; I ran 3.11). (M2, `runner/replay.py`.)
6. **"`--project <checkout of the subject>`" is ambiguous.** It could be the repo root or
   `fixtures/od-fixture`. For a fixture bundle the manifest's `subject.module_path` says
   `fixtures/od-fixture`; the instructions could say "the checkout's `module_path`". (M2.)

**Limitations:** one bundle (F1); one second machine (mine); the subject and tool commits were
`main`, not the recorded `03ada56` (deviation above, with the diff showing the code is identical).
