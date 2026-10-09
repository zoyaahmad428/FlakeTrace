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
