# GenAI usage log — Member 1 (Resource Evidence)

Each entry covers one working session with a GenAI coding assistant (Claude
Code). "Retained" means kept as generated after my review; "changed" means I
altered it before accepting; "rejected" means discarded.

## 2026-10-09 — Phase 0 (inspection), repo housekeeping, Phase 1 (output contract)

**Assistance level:** L2 (Assisted): the contract text and the check script were
generated; I chose the approach and must review the contract before it goes
to Member 3. No extraction code yet.

**What I asked:**
- Phase 0: inspect the repo (tree, git log, existing POC extractor and
  manifests, Member 3's fixture and report schema) and recommend javap
  (extend POC) vs ASM, without writing anything.
- Housekeeping: remove the Windows `Zone.Identifier` files and
  `POC/.claude/settings.local.json` that were committed with the POC.
- Phase 1: draft `docs/contracts/resource-evidence.md` with one JSON example,
  aligned with Member 3's report schema, before any extraction code.

**What was retained:**
- Phase 0 findings: the POC extractor `POC/src/extract_static.py` (javap
  based, static fields only, `test*`-prefixed methods only, `setUp`/`tearDown`/
  `<clinit>` by name, no system properties, POC `FT_HOPS=1` = depth 2) and the
  case manifest `POC/manifest/cases.csv` (fastjson pinned at
  `e05e9c5e4be580691cc55a59f3256595393203a1`; DateFieldTest8 pair = case FJ-01).
- Decision (mine): approach (a): extend the POC javap approach in a **new**
  file of my component, leaving `POC/src/extract_static.py` unchanged so the
  POC's recorded results stay reproducible.
- Housekeeping commit (local, not yet pushed: GitHub push access returned 403).
- Contract draft `docs/contracts/resource-evidence.md`.

**What I changed / what the assistant corrected during the session:**
- The assistant first estimated 46 `Zone.Identifier` files; the real count was
  44.
- First `.gitignore` rules were wrong and were caught by testing with real
  file names: `*:Zone.Identifier` did not match (the files use U+F03A, WSL's
  substitute for `:`), and `.claude/settings.local.json` only matched at the
  repo root. Final rules: `*Zone.Identifier`, `**/.claude/settings.local.json`.
- The brief's field `declaring_class` was renamed to `class` in the contract
  to match Member 3's `codeLocation`.
- `Long.getLong` added as a system-property READ alongside
  `Integer.getInteger` (flagged in the contract as removable).

**How it was verified:**
- Fixture compiled unmodified with `mvn -B -q test-compile` in the POC-frozen
  image `maven@sha256:15522857…` (JDK 1.8.0_502), exit 0. Classes
  disassembled with that JDK's `javap -c -p`. Output saved at
  `evidence/javap-dumps/phase1-f1-f2.txt`.
- A script checked that every offset/call frame in the contract example
  resolves to the expected instruction in that javap output, that the example
  JSON parses, and that the projected `shared_resource` / `codeLocation`
  values validate against `eval/schema/report.schema.json` (jsonschema 4.26.0).

**Errors found:**
- Member 3's illustrative F1 example uses offsets 3/5; real JDK 8 offsets are
  1/1 (noted as open question 5 in the contract, not edited).
- POC records disagree on FJ-01's resource (`decision_record.md`:
  `JSON.defaultTimeZone`; `cause_classification.csv`: `JSON.defaultLocale`).
  To be settled by real output in Phase 5.2.

**Environment issues (not code errors):** Docker daemon was not running
(started it); Docker Hub returned 429 (pulled the same frozen digest through
`mirror.gcr.io`); Maven inside the container needed the session proxy and
truststore (passed via a scratch `settings.xml` and `MAVEN_OPTS`, nothing in
the repo changed).

**Rejections:** Option (b) (Java + ASM) rejected because it would replace
working POC code, and ASM does not expose bytecode offsets directly.

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-09 — Contract revision: consumers and invocation

**Assistance level:** L2 (Assisted): the section text was generated from my
instructions; I chose the command shape and decide the default depth.

**What I asked:**
- Remove the claim that Member 2 consumes nothing from the contract, because
  Member 2's CLI calls the extractor end-to-end.
- Add an "Invocation" section (command, flags, JSON on stdout, exit codes) and
  fill the language/entry-point line under Interface 2 in `interfaces.md`.
- Explain the trade-off of defaulting `--depth` to 2, and stop for my decision.

**What was retained:** the corrected status paragraph; the Invocation section
with pair mode (`--polluter` + `--victim`) and single mode (`--test`); exit
code 1 for internal errors (`javap` missing or failing), added beside 0 and 2;
the `interfaces.md` line marked "planned, not yet implemented", because that
line says to record it "when implemented".

**What I changed:** No edits to the generated text; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). My part: the instructions above (remove the "Member 2 consumes nothing" claim, the Invocation section, the depth trade-off) and the command shape; I applied, committed and pushed it in PR #8. In that PR I also committed a stray pager file by mistake (a `git status` typed into `less`) and removed it in commit `b2d72b9`.

**How it was verified:** see `docs/evidence-m1.md`, "Contract revision": the
example still matches the javap dump, the projections validate against the
schema, the anchors resolve, `interfaces.md` has exactly one changed line, and
the 58 eval tests are OK.

**Errors found / corrected during the session:**
- My first staging simulation for the cleanup PR set `GIT_INDEX_FILE` before
  resolving the real index path, so it ran on an empty index and printed
  meaningless numbers. It was noticed and redone correctly before handing over.
- The claim "the team's repo-hygiene CI check rejects them" was left out of the
  cleanup commit: no such check exists on `main` or in any open PR.
- The claim "CLAUDE.md §6 forbids committing .class files and dumps" was wrong.
  §6 is about GenAI records. The real rule broken by `chore/repo-restructure`
  is `POC/.gitignore`, which ignores `runner/`, `*.class` and
  `results/resources_*.json`.

**Rejections:** none this session.

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-09 — Phase 0 re-check, extractor approach and default depth

**Assistance level:** L2 (Assisted): the decision record text was generated; the
two decisions are mine.

**What I asked:** re-run Phase 0 on the current repo, then record my
decisions: (a1) write `evidence/extract.py` fresh, with the POC as a reference
only; default `--depth 2`.

**What was retained:** ADR-002 (PROPOSED); the default-2 wording in the
contract; the numbering note; open question 5 marked resolved.

**What I changed:** The two decisions are mine: write the extractor fresh with the POC as reference only (a1), and default depth 2; I rejected (a2), ASM, and depths 1 and 3. No edits to the generated ADR text; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). Committed and pushed in PR #8.

**How it was verified:** the depth-numbering claim was checked against the POC
source (`extract_static.py` lines 29 and 132) and `depth_sweep.csv`; see
`docs/evidence-m1.md`.

**Errors found:** the vault's depth wording (`depth-configurable.md`, claims
C6/C7) uses the POC's hop numbering, so its "depth 2" is depth 3 in our
contract. Flagged in ADR-002 for a wording check; those docs were not edited.

**Rejections:** (a2) copying POC code; (b) ASM; default depth 1 and 3.
Reasons in ADR-002.

## 2026-10-09 — Phase 2: depth-1 extraction with lifecycle attribution

**Assistance level:** L3 (Core-assist): the extractor module and its tests were generated.
I must be able to explain what was produced, what I added, why it works, and its limits.

**What I asked:** start Phase 2 on `m1/static-extraction`: depth-1 extraction of static
fields and constant-key system properties for one test method, including JUnit 4/3
lifecycle methods, `<clinit>` and inherited lifecycle methods. Build my own tiny test
class first, with one static write, one static read, one setProperty and one
getProperty, and cross-check the offsets against `javap -c -p`.

**What was retained:** `evidence/extract.py` (fresh code per ADR-002, standard library
only); `evidence/tests/test_extract.py` (9 tests); the self-test Maven project
`evidence/tests/resources/m1-selftest/` (acceptance, lifecycle, JUnit 3 and unsupported
cases); `docs/04-Implementation/evidence-collector.md`; the README, iteration-plan,
members, demo-plan and register updates.

**What I changed:** No edits to the generated code or tests; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). My part: the specification above (static fields and constant-key properties, JUnit 4/3 lifecycle, `<clinit>`, inherited methods) and asking for my own self-test class with offsets cross-checked against `javap -c -p`; I applied, committed and pushed it in PR #9.

**How it was verified:** see `docs/evidence-m1.md` Phase 2: the four acceptance offsets
cross-checked by hand against JDK 8 `javap -c -p`; 9 tests OK on JDK 8 and JDK 21 javap; a
mutation check showed the lifecycle test catches the bug below.

**Errors found:**
- Annotation names were not recognised on JDK 8 javap (regex kept javap's padding), so
  every `@Before/@After/@BeforeClass/@AfterClass` method was missed. It was found by running
  on real JDK 8 output and fixed; the test now guards it.
- Choices to review, not errors: when depth 2 is requested, the CLI refuses rather than
  silently falling back to depth 1; `external_calls_not_followed` lists `java.lang.System`
  for non-property calls such as `nanoTime`.

**Rejections:** none this session.

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-09 — Phase 3: configurable call depth

**Assistance level:** L3 (Core-assist): the depth walk, tests and measurement script were
generated.

**What I asked:** add `--depth N` (default 2; 1–3) following project calls only, handle
cycles, record `call_path`, report virtual dispatch and reflection as unsupported, and
measure what each depth adds on the fixture (real numbers only).

**What was retained:** breadth-first `walk_root` (shortest call path, each method once per
root); `follow_call` with `VIRTUAL_DISPATCH`, `DEPTH_LIMIT` and `UNRESOLVED_CALL`;
`IMPLICIT_CLINIT` also on `new`; 5 new tests; `evidence/tools/measure_depth.py`; doc updates.

**What I changed:** No edits to the generated code, tests or script; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). My part: the specification above (`--depth` with default 2, project calls only, cycles, `call_path`, virtual dispatch and reflection reported, real measurements only); I applied, committed and pushed it in PR #12.

**How it was verified:** expected paths and offsets read by hand from JDK 8 javap
(`evidence/javap-dumps/phase3-depth-selftest.txt`); 15 tests OK on JDK 8 and JDK 21 javap;
fixture measurement with 5 (host) and 3 (Docker JDK 8) repeats per depth. See
`docs/evidence-m1.md`.

**Errors found:** the first JDK 8 measurement run failed (relative paths through the Docker
javap wrapper). This was a tooling problem and was re-run with absolute paths.
The honest result is that the fixture cannot show the time cost of depth.

**Rejections:** following subclass overrides (would need every project class loaded;
recorded as `VIRTUAL_DISPATCH` instead).

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-09 — Phase 4: polluter→victim resource edges

**Assistance level:** L3 (Core-assist): the edge computation, projection and tests were generated.

**What I asked:** given `--polluter` and `--victim`, compute the resources written by the
polluter (including its lifecycle code) and read by the victim, with both locations. If there
are none, output an empty list with `no_supported_resource_evidence`; never invent an edge, and
never claim "no dependency".

**What was retained:** `find_edges` (contract Output 2: ordering, side tags, 7 fixed
limitations), `report_fields` (contract projection into Member 3's three fields; extra edges and
locations named in `limitations`), pair-mode CLI with clear input errors, 11 new tests (26 total).

**What I changed:** No edits to the generated code or tests; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). My part: the rules above (never invent an edge, never claim "no dependency", empty list plus `no_supported_resource_evidence`); I applied, committed and pushed it in PR #15.

**How it was verified:** see `docs/evidence-m1.md` Phase 4. The fixture pairs F1/F2/F3 and two
no-resource pairs were run with JDK 8 javap, and the F3 offsets were checked by hand. 26 tests OK
on JDK 8 and JDK 21 javap. The projection was validated against Member 3's schema.

**Errors found:** none this phase. One test skips under Python 3.11 here (no jsonschema); this is
recorded, not hidden.

**Rejections:** editing the contract's "planned, not yet implemented" wording myself (needs all
three members; proposed in the PR instead).

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-09 — CI guard for the evidence tests; in-process default depth

**Assistance level:** L2 (Assisted): the guard helper and test were generated; the need came from
Member 2's CI question.

**What I asked:** make sure Member 2's CI job for `evidence/tests/` cannot pass by skipping.

**What was retained:** `FLAKETRACE_REQUIRE_JVM=1` turns the "classes not compiled" and "javap not
found" skips into failures (the same name Member 2's runner job uses); `analyse_test` now defaults
to depth 2 like the CLI; 1 new test (27 total).

**What I changed:** No edits to the generated helper or test; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). My part: asking for Member 2's CI job to be unable to pass by skipping; I applied, committed and pushed it in PR #16.

**How it was verified:** skip, fail and pass behaviour each run for real; see `docs/evidence-m1.md`.

**Errors found:** `analyse_test`'s in-process default was depth 1 while the CLI and the contract
said 2. It was found while checking the contract's API notes against the code, and is fixed and
tested.

**Rejections:** none.

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-09 — Answers to Member 2's integration questions

**Assistance level:** L1 (Supportive): the wording was drafted by the assistant; the decisions
(confirm the contract, first-edge projection, ADR agreement) are mine.

**What I asked:** answer Member 2's seven questions. Confirm the contract, choose the edge for the
report, confirm the CLI call and exit codes, give agreement on ADR-003 and ADR-004, and confirm the
CI command.

**What was retained:** the contract status and open-question answers; the "Calling it from another
component" notes (run from the repo root or import in-process); ticks on ADR-001 to ADR-004.

**What I changed:** The decisions are mine: confirm the contract, the first-edge projection, the CLI call and exit codes, and my ticks on ADR-001 to ADR-004. No edits to the drafted wording; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). Committed and pushed in PR #17.

**How it was verified:** see `docs/evidence-m1.md` (API names checked against main, example and
anchors validated).

**Errors found:** Member 2's planned call (`python -m evidence.extract` with the target project as
working directory) would fail with "No module named evidence". This is now documented: run it from
the repo root or set `PYTHONPATH`.

**Rejections:** editing claims-ledger row E1 myself. It is a joint row raised by Member 2; I
proposed wording in my reply instead.

## 2026-10-09 — Phase 5 part 1: automatic ground-truth check on the fixture

**Assistance level:** L3 (Substantial): the test class was generated; I chose to compare against
Member 3's ground truth file directly rather than copying its values into the test.

**What I asked:** start Phase 5. Compare F1, F2, F3, N1 and N2 against `ground_truth.json`
automatically.

**What was retained:** `GroundTruthTest` (3 tests): exact set of edge pairs over all 156 ordered
pairs, resource per edge, no edge for N1/N2 from any test.

**What I changed:** I chose to compare against Member 3's `ground_truth.json` directly instead of copying its values into the test. No edits to the generated test class; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). Applied, committed and pushed in PR #23.

**How it was verified:** see `docs/evidence-m1.md`. 30 tests OK on javap 21; fixture tests OK on
JDK 8 javap; a mutation check showed the tests fail when depth is 1 or the ground truth is altered.

**Errors found:** none in the extractor. F3's ground-truth field is free text, so the test can
only check its words (noted as a limitation for Member 3).

**Rejections:** editing `fixtures/od-fixture/ground_truth.json` to make F3 machine-readable. It is
Member 3's file.

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-09 — Phase 5 part 2: fastjson FJ-01 and FJ-02

**Assistance level:** L2 (Moderate): the assistant built fastjson and ran my extractor on it; no
extractor code changed. The evidence write-up and javap excerpt were drafted by the assistant.

**What I asked:** run the extractor on real fastjson (FJ-01 at depths 1 and 2) and settle
`defaultTimeZone` vs `defaultLocale`.

**What was retained:** the run results, the javap excerpt
(`evidence/javap-dumps/phase5-fastjson.txt`), the evidence entry and claims-ledger rows E10/E11.

**What I changed:** No edits to the generated write-up or javap excerpt; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). My part: the brief (run FJ-01 at depths 1 and 2, settle `defaultTimeZone` vs `defaultLocale`). My brief named the wrong FJ-01 polluter and resource (see Errors found). Applied, committed and pushed in PR #24.

**How it was verified:** real runs only, see `docs/evidence-m1.md`. CLI and in-process API agree.
JDK 8 and JDK 21 javap agree. Every offset on the depth-4 path was checked against the JDK 8 javap
excerpt.

**Errors found:**
- My original brief named `DateFieldTest8` as FJ-01's polluter and `defaultTimeZone` as its
  resource; the POC records name `DateFieldFormatTest` and `defaultLocale`. Both state-setters were
  run; the time-zone question was settled by arithmetic on the test's constants.
- POC claim C6 (FJ-02 read at `TypeUtils.cast@536`, two hops): the location was reproduced, but
  at depth 5, not depth 3. The first draft of this entry wrongly said `TypeUtils.cast` was not
  reached; a check run before hand-over showed it is, and the text was corrected.
- Two scratch-script slips (wrong output key, a missing `time` binary, a javap filter that skipped
  `throws` methods) were caught and rerun. None touched the repository.

**Rejections:** raising the depth cap in the code. It changes the contract's accepted values, so
it is a team decision. The depth-4/5 results are labelled exploration.

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-10 — Depth measurements and ADR-006 (proposed)

**Assistance level:** L2 (Moderate): the assistant ran the measurements and drafted the ADR; I
chose the option.

**What I asked:** draft a note for the team on the depth range before Phase 6.

**What was retained:** the per-depth yield tables (`docs/evidence-m1.md`) and ADR-006. I chose
"auto-deepen": accept 1–5, keep default 2, and have pair mode go deeper only when there is no
edge and the walk was cut off.

**What I changed:** I chose the option: auto-deepening, range 1–5, default kept at 2, deepening only when there is no edge and the walk was cut off. No edits to the generated ADR text or tables; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). I asked Member 2 and Member 3 to review it and committed it in PR #28.

**How it was verified:** real exploration runs over every POC candidate for FJ-01 (72) and
FJ-02 (722) at depths 1–5, and the fixture matrix at depths 2–5. See `docs/evidence-m1.md`.

**Errors found:** the first ADR draft said "nothing changes for callers". That is wrong:
`find_edges` receives tests that are already analysed, so deepening needs a new helper that Member
2 and Member 3 would switch to. Corrected before hand-over. The ADR number moved from 005 to 006
because Member 2's ADR-005 (W9 command) merged first.

**Rejections:** editing the contract. The change is written as a proposal in ADR-006 for M2 and
M3 to agree.

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-10 — Phase 6: lifecycle writes as polluter edges

**Assistance level:** L3 (Substantial): the tests and the self-test class were generated.

**What I asked:** start Phase 6 (the required-test list from the brief).

**What was retained:** two pair tests (a `setUp` write and a test-class `<clinit>` write as the
polluter side of an edge), one CLI test (unknown victim in pair mode exits 2), and
`M1ClinitReaderSelfTest.java`.

**What I changed:** No edits to the generated tests or self-test class; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). My part: the required-test list from my brief; applied, committed and pushed in PR #28.

**How it was verified:** 33 tests OK on javap 21 and JDK 8 javap; expected offsets read by hand
from JDK 8 javap; mutation check. See `docs/evidence-m1.md`.

**Errors found:** the first mutation script changed nothing (it filtered the wrong return value),
which made the tests look unbreakable. It was fixed, and the tests then failed as expected.

**Rejections:** changing how `<clinit>` is attributed. The contract already covers FR-3.

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-10 — ADR-006 implementation: depth 1–5 and pair-mode auto-deepening

**Assistance level:** L3 (Substantial): the code, tests and contract text were generated from the
agreed ADR.

**What I asked:** implement ADR-006 now that M2 and M3 agreed.

**What was retained:**
- `MAX_DEPTH`, `analyse_pair` / `_analyse_pair`, `--no-deepen` and the depth `limitations` line
  (Member 2's request).
- 6 new tests.
- The contract edit exactly as the ADR proposed; README, implementation note, demo plan and ADR
  status updated.

**What I changed:** No edits to the generated code, tests or contract text; what was merged is the handed-over patch unchanged (checked on 2026-10-11 by comparing each patch with the merged diff). My part: starting the implementation only after Member 2 and Member 3 had agreed to ADR-006 (PRs #29, #33); applied, committed and pushed in PR #34.

**How it was verified:**
- 39 tests OK on JDK 21 and JDK 8 javap.
- Member 3's 68 eval tests and Member 2's 20 CLI tests OK.
- Mutation check.
- fastjson FJ-01/FJ-02 through the real CLI. See `docs/evidence-m1.md`.

**Errors found:** none in the code. A finding was recorded instead: on FJ-01 the report's single
resource is `defaultLocale` (tie-break by name), not the causal `defaultTimeZone`.

**Rejections:** changing the edge ordering to favour the "right" field. Static evidence cannot
know which field is causal, and the ordering is part of the agreed contract.

Ownership checkpoint: you need to understand and verify this implementation before claiming it as your contribution.

## 2026-10-11 — ADR-008 tick, I2, ADR-001 status, panel action A6

**Assistance level:** L2 (Moderate): checks run and text drafted by the assistant; the list of
open items and the decision to close them came from the team's status review.

**What I asked:** make one patch for what is left for Member 1: tick ADR-008, answer I2, close
panel action A6 (a note on minimisation), and set ADR-001's status.

**What was retained:**
- ADR-008 M1 row ticked (for information), after re-running the evidence tests with F4/N3.
- I2 answered from ADR-006 (per pair, `analyse_pair` once per polluter).
- ADR-001 `ACCEPTED` (PRs #17, #18, #20), plus a research-basis section.
- New note `docs/01-Literature/minimisation-ddmin-vs-one-by-one.md`; A6 `COMPLETE`.
- Claim E10 and the W8 line updated from 156 to 240 pairs.

**What I changed:** I resolved the merge conflict with Member 2's PR #49 in `genai-register.md` myself, keeping both sides' rows. I left two marker lines in by mistake and removed them in PR #51. Otherwise the merged content is the handed-over patch unchanged (checked by comparing the patch with the merged diff). Committed and pushed in PR #50.

**How it was verified:** evidence 39 OK on main `9dcd439` and on PR #49; M2's and M3's suites OK;
real F4 and F3 runs (see `docs/evidence-m1.md`). Each literature statement in the note was checked
against the team's existing notes.

**Errors found:** the first draft of the note said iFixFlakies' Minimizer falls back to OBO; the
note on iFixFlakies says that of cleaner discovery. Corrected before handing over.

**Rejections:** no new references. Sources [4] and [11] are listed in the note for the citing
member to open before the report cites them.

Ownership checkpoint: you need to understand and verify this before claiming it as your contribution.

## 2026-10-11 — GenAI disclosures and ADR-002 status

**Assistance level:** L1 (Supportive): the assistant drafted the 13 "What I changed" lines and the
10 register cells from the repository record; I read and confirmed each before committing.

**What I asked:** fill in my GenAI disclosures, mark ADR-002 accepted and update my members row,
and tick the source check in the A6 note after I had opened [4] and [11].

**What was retained:** the disclosure lines, ADR-002 `ACCEPTED` (PRs #17, #20, #54), the members row.

**What I changed:** Read every disclosure line against my PRs before committing; corrected any
line that did not match what I did.

**How it was verified:** each handed-over patch was compared with what was merged in the matching
PR. Every PR's merged content came from the patches, except the two leftover conflict lines in
PR #50 (removed in #51). Recorded choices were checked against the ADR agreement rows.

**Errors found:** a stray pager file had been committed in PR #8 and was removed in `b2d72b9`;
it is now named in that entry.

**Rejections:** claiming edits or checks that the record does not show.
