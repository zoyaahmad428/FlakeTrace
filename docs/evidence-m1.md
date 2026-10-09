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
