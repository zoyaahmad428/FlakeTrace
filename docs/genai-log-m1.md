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

## 2026-11-18 — W16: retired claims in `evidence/` wording

**Assistance level:** L3 (Core-assist): the assistant ran the phrase search, proposed the wording
from claims ledger G3 and drafted the evidence entry; I read the diff and committed it.

**What I asked:** do my part of W16: remove retired claims from `evidence/` and its note.

**What was retained:** the new opening of `evidence/README.md`, the G3 sentence in §1 of
`docs/04-Implementation/evidence-collector.md`, and the corrected FJ-01 line.

**What I changed:** Read every changed line against ledger G3 and G4 before committing.

**How it was verified:** the same phrase search before (two retired hits) and after (only the G3
replacement phrase), recorded in [[evidence-m1]]. No code changed, so no test was re-run.

**Errors found:** the note called `JSON.defaultTimeZone` "the real cause"; that was reasoned from
the test's constants, never confirmed by a run.

**Rejections:** editing `FIXED_LIMITATIONS` without the other two members, because it is part of
the resource-evidence contract.

## 2026-11-18 — W21 part 1: `resource_edges` in `report_fields`

**Assistance level:** L3 (Core-assist): the assistant wrote the test and the change from ADR-010's
`resource_edges` field, ran the suites and drafted the docs; I chose the plan (controls in my own
folder, reflection as the hidden cause) and committed after reading the diff.

**What I asked:** start W21: all edges in the output, test-first.

**What was retained:** `ResourceEdgesTest` (3 tests), the `resource_edges` list in
`report_fields`, the contract row, the README sentence.

**What I changed:** Chose where the controls live and what the hidden cause is; read the test,
the code and the contract row before committing.

**How it was verified:** the 3 tests failed first (`KeyError`), then passed; evidence 42, eval 99
and runner CLI 63 tests OK ([[evidence-m1]]).

**Errors found:** none in the code. A gap recorded instead: with several polluters, M2's
`combine_fields` would pass on only the first polluter's edges.

**Rejections:** changing `eval/report.py` or the schema (M3's W19) or `runner/cli.py` (M2).

## 2026-11-18 — W21 part 2: the two FT005 controls

**Assistance level:** L3 (Core-assist): the assistant wrote the control project, the expected
results, the tests and the docs, and ran the extractor and two full diagnoses; I chose where the
controls live and that reflection hides the real cause, and committed after reading the diff.

**What I asked:** build W21's two controls (write-then-restore, unrelated overlap) in my folder.

**What was retained:** `evidence/tests/resources/ft005-controls/` (pom, `State`, four test
classes, `EXPECTED.md`), `Ft005ControlsTest` (3 tests), README and command lines.

**What I changed:** Chose option 1 (my own folder) and reflection as the hidden cause; read the
Java, the tests and `EXPECTED.md` before committing.

**How it was verified:** the tests failed first (not compiled), then passed; both diagnoses ended
`VERIFIED (sequence)` with the static-overlap wording; 45 evidence tests OK ([[evidence-m1]]).

**Errors found:** none. Gaps recorded: CI needs one compile line (M2's `ci.yml`); the extra edge
is only in `limitations` until W19.

**Rejections:** editing `.github/workflows/ci.yml` (M2's) or adding cases to `fixtures/` (M3's).

## 2026-11-20 — W22 verification (lifecycle control) on my own machine

**Assistance level:** L3 (Core-assist): the assistant gave me the commands from M2's handover, diagnosed
the two setup failures (Maven download timeouts, Python 3.9 too old for `jsonschema` 4.26.0) and
drafted this evidence entry from the output I pasted; I ran every command myself on my laptop.

**What I asked:** run the W22 verification on my laptop and record it.

**What was retained:** the evidence entry in [[evidence-m1]], including the three-row table and the
differences for M2.

**What I changed:** Ran every command; fixed my setup (pre-fetched the Maven plugin, installed
Python 3.11); read the entry against my terminal output before committing.

**How it was verified:** every number in the entry is copied from my own terminal output.

**Errors found:** the first instructions did not install the Python dependencies before `diagnose`
(the assistant's omission); found when `diagnose` failed on `jsonschema`.

**Rejections:** loosening the pinned `jsonschema` version (M3's file) to make Python 3.9 work.

## 2026-11-20 — W18 verification (outcome tallies) on my own machine

**Assistance level:** L3 (Core-assist): the assistant gave me the commands, found that the handover's
"before" step would restore the old tests too, tried the corrected step in the cloud first, and
drafted this entry from my output; I ran every command myself on my laptop.

**What I asked:** run the W18 verification and record it.

**What was retained:** the W18 entry in [[evidence-m1]].

**What I changed:** Ran every command; checked the entry against my terminal output before
committing.

**How it was verified:** every number is copied from my own terminal output.

**Errors found:** the handover's `git checkout d1e4d4f -- runner` cannot show the defect (it
restores the old tests); recorded for M2.

**Rejections:** none.

## 2026-11-20 — W19 verification (verdict contract v2) on my own machine

**Assistance level:** L3 (Core-assist): the assistant rebuilt the section C commands from the
repo (CI's eval module list, the T1–T4 test names, N4's victim), and drafted this entry and the
register update from my output; I ran every command myself on my laptop.

**What I asked:** give me the W19 verification commands and record the result.

**What was retained:** the W19 entry in [[evidence-m1]], including my rerun of M3's integration
tool on all eight fixture cases (T6), and the FT003 row in [[10-Final1/action-register]]. The
assistant spotted that the tool overwrites M3's committed reports and had me run it in a
throwaway worktree.

**What I changed:** ran every command; checked the entry against my terminal output before
committing.

**How it was verified:** every number is copied from my own terminal output.

**Errors found:** none in W19. The first version of these commands from an earlier session was
lost, so they were rebuilt from the repo.

**Rejections:** marking FT003 `Done`. It needs the supervisor's acceptance, so it is `Partly`.

## 2026-11-20 — PR #106 check: report schema v2 against `report_fields` (A4)

**Assistance level:** L3 (Core-assist): the assistant wrote the contract test and a one-off
comparison script, ran both in its cloud container, broke `depth` once to show the test can fail,
and drafted this entry and my PR #106 comment.

**What I asked:** check PR #106's schema change against `evidence/extract.py` output and draft my
approval comment.

**What was retained:** `ReportSchemaContractTest` in `evidence/tests/test_extract.py`, the entry
in [[evidence-m1]], and the comment on PR #106.

**What I changed:** ran the test and the full suite myself on my laptop; read the test and the
diff before committing.

**How it was verified:** test OK and the full evidence suite at 46 OK, both in the container and on
my laptop (JDK 25, Python 3.11.9); the deliberate `depth = -1` run (container only) failed as
expected.

**Errors found:** the first draft of the test guessed the edge counts for two self-test pairs, and
both guesses were wrong (`0 != 1`, `1 != 0`). They were replaced with pairs whose edges
`PairSelfTest` already asserts.

**Rejections:** editing the schema or `eval/report.py`, which are not mine. A committed comparison
script, because the unit test covers what needs to stay checked.

## 2026-11-20 — W25 part 1: `rank_candidates` (ranking rule, test-first)

**Assistance level:** L3 (Core-assist): the assistant designed `AnalysisCache` and
`rank_candidates` from ADR-014 §5, wrote the 10 tests first, ran them failing, wrote the code, ran
them passing, and drafted the docs.

**What I asked:** build W25 part 1 test-first, on my own classes only, so the rule is committed
before it meets any ground truth.

**What was retained:** the code in `evidence/extract.py`; `RankCandidatesTest` and
`RankCandidatesControlsTest`; the `evidence/README.md` and `04-Implementation` notes; the entry in
[[evidence-m1]].

**What I changed:** ran the test-first check myself on my laptop (code taken out, 10 errors; code
put back, 10 OK); read the rule, the tests and the diff before committing.

**How it was verified:** test-first failure (`FAILED (errors=10)`), then 10 OK and the full suite
at 56 OK, in the container and again on my laptop (before: `FAILED (errors=10)`; after: 10 OK;
suite 56 OK).

**Errors found:** none in the tests. One sentence in the implementation note overstated what the
rule guarantees, and was rewritten to say that only measurement can show an improvement.

**Rejections:**
- The POC's class-initialiser and co-touch terms, which ADR-014 says to add only with a measured
  comparison.
- Deepening inside `rank_candidates` (the planner's decision, M2).
- Running the rule on any fixture or fastjson case before it is committed and reviewed.
- Editing `docs/contracts/interfaces.md`.

## 2026-11-20 — Fix: second-edge limitation wording (found by M2 in W21 verification)

**Assistance level:** L3 (Core-assist): the assistant read M2's A2 finding, wrote the regression
test and changed the assertion first, ran them failing, made the one-line fix, ran the suites, and
drafted the docs.

**What I asked:** continue Iteration 2 from where it stood.

**What was retained:** the fix in `evidence/extract.py`, the two test changes, the
`04-Implementation` note bullet, and the entry in [[evidence-m1]].

**What I changed:** ran the test-first check myself on my laptop, and read the diff before
committing.

**How it was verified:** test-first `FAILED (failures=2)`, then OK, and the evidence suite at 57 OK,
both in the container and on my laptop; M2's and M3's consumer tests at 34 OK (container).

**Errors found:** the old line itself, my W21 part 1 leftover. When I added `resource_edges` I
kept the "not shown" limitation, and it stopped being true.

**Rejections:** removing the line entirely. The headline fields still show only one resource, so
naming the others stays useful.

## 2026-11-20 — W20 verification (deletion checks, ADR-011 T1–T5) on my own machine

**Assistance level:** L3 (Core-assist): the assistant found the W20 tests that cover T1, T2 and
T5, gave me the real F1 and F3 commands with two one-line checks (report `deletion_checks`,
record step counts), and drafted this entry and the register updates from my output; I ran
every command myself on my laptop.

**What I asked:** verify W20 now that both halves are merged.

**What was retained:** the W20 entry in [[evidence-m1]]; the FT004 row in
[[10-Final1/action-register]]; the G2 row in [[07-Defense/claims-ledger]]; the W20 plan row.

**What I changed:** ran every command; checked the entry against my terminal output before
committing.

**How it was verified:** every number is copied from my own terminal output.

**Errors found:** none in W20. I typed a test name as a command once; the rerun is the one
recorded.

**Rejections:** marking G2 `SETTLED` or FT004 `Done` myself. G2 belongs to M2 and M3, and FT004
also needs the supervisor's acceptance.

## 2026-11-20 — W25: Interface 5 (rank_candidates) contract proposal

**Assistance level:** L3 (Core-assist): the assistant drafted the Interface 5 section from the
merged code and M2's review, checked each statement against `evidence/extract.py`, and drafted
the plan row and this entry.

**What I asked:** continue Iteration 2. M2 asked me to add `rank_candidates` to the contract.

**What was retained:** the Interface 5 section, the W25 plan row update, and the entry in
[[evidence-m1]].

**What I changed:** read the section against my code before committing.

**How it was verified:** each statement was compared with the code at `69cf36f`. Nothing was run.

**Errors found:** the first draft stated a depth range (1–5) that `rank_candidates` does not
check, and described the runner's fallback as built. Both were corrected: "the analysis depth
(default 2)", and "M2, when built".

**Rejections:** editing the contract without the other two members. The section is a proposal
until M2 and M3 approve the PR.

## 2026-11-20 — W32: practitioner-check protocol (FT018)

**Assistance level:** L3 (Core-assist): the assistant drafted
[[10-Final1/practitioner-check]] (purpose, roles, who qualifies, consent text, a 30-minute
session mapped to FT018's four items, the record template, the blocker path and the attempt log)
from FT018, [[00-Meta/stakeholder-evidence]] and [[07-Defense/weak-points]] §1.

**What I asked:** continue Iteration 2 with unblocked work.

**What was retained:** the protocol, its links from the Final1 README, the W32 plan row, the FT018
action-register row and my members row.

**What I changed:** read the protocol and the consent text before committing.

**How it was verified:** nothing was run. The links to the four notes it cites were checked to
exist on `main` at `adc63ee`.

**Errors found:** none recorded.

**Rejections:**
- Writing the case and the acceptance task myself: they are M2's and M3's parts, so they are
  left marked "to be supplied".
- Choosing a substitute: that is the supervisor's decision, so options are listed for them.

## 2026-11-20 — W25 part 2: review of M2's `EvidenceRanker` (Interface 7, step 3)

**Assistance level:** L3 (Core-assist): the assistant read `runner/policy.py` against Interfaces 2,
5 and 7, ran M2's policy tests and an independent probe on my self-test classes in its container,
drafted the one-line Interface 5 clarification, and drafted this entry and my review comment.

**What I asked:** continue Iteration 2. The review is my step in Interface 7.

**What was retained:** the review entry in [[evidence-m1]], the `get` line in Interface 5, the
W25 plan row and my members row.

**What I changed:** ran the probe and M2's policy tests myself on my laptop; read the review and
the contract line before committing.

**How it was verified:** M2's 19 policy tests OK, and the independent probe on my classes, with
identical results in the container and on my laptop.

**Errors found:** my earlier proposal (a new `depth_limited` method) was unnecessary.
`AnalysisCache.get` already gives M2 what P4 needs. The proposal was withdrawn.

**Rejections:** editing `runner/policy.py` (M2's) for the `note` point. It is left as a
suggestion for him.

## 2026-11-20 — W24 verification (ADR-014 evidence item 2) on my own machine

**Assistance level:** L3 (Core-assist): the assistant gave me the boundary commands (69, 70, and
no limit) with two one-line checks (the report's `budget`, the record line counts), and drafted
this entry and the register updates from my output; I ran every command myself on my laptop.

**What I asked:** my next step after the W25 review: Interface 6 step 4.

**What was retained:** the W24 entry in [[evidence-m1]], the W24 plan row, and the G8 row in
[[07-Defense/claims-ledger]].

**What I changed:** ran every command; checked the entry against my terminal output before
committing.

**How it was verified:** every number is copied from my own terminal output.

**Errors found:** none.

**Rejections:** marking G8 `SETTLED` alone. I co-own it with M2 and M3, so I left it for all three
to agree.
## 2026-11-20 — FJ-03: why the extractor finds no edge

**Assistance level:** L3 (Core-assist): the assistant fetched fastjson at the pinned commit in its
container, installed JDK 8 from Ubuntu's packages to build it unmodified, read `SerializeWriter`,
ran my extractor on the pair with a one-off script, and drafted the explanation and the
`04-Implementation` bullet.

**What I asked:** look into M2's finding that FJ-03 has no resource edge.

**What was retained:** the entry in [[evidence-m1]] and the new "What breaks" bullet.

**What I changed:** read the explanation against the source and the extractor output before
committing.

**How it was verified:** the extractor output quoted in the entry. Nothing in `evidence/` changed.

**Errors found:** the first two builds failed (JDK 21: "Source option 5 is no longer supported",
then `javax.xml.bind` missing). JDK 8 built it.

**Rejections:** adding a co-touch term to the ranking rule now. FJ-03 is ground truth, and plan
rule 4 forbids tuning the rule on it.

## 2026-11-22 — W32: the case section filled from M2's F1 bundle

**Assistance level:** L3 (Core-assist): the assistant read M2's committed F1 bundle
(`report.json`) and wrote the protocol's "The case" section and status line from it, and
updated the W32 plan row.

**What I asked:** link M2's F1 bundle from the protocol, as he asked.

**What was retained:** the case section, the status line (`READY EXCEPT PARTICIPANT`) and the W32
plan row.

**What I changed:** read the section against the bundle's report before committing.

**How it was verified:** the facts in the section were copied from the bundle's `report.json`:
`VERIFIED`, polluter `ConfigPolluterTest#pollute`, `AssertionError`, alone 20/20 passed. Nothing
was run.

**Errors found:** the first draft said the victim "passes when run alone", a retired-claim
phrasing. It was replaced with the measured tally ("in the report's 20 alone runs it never
failed").

**Rejections:** none.

## 2026-11-22 — W23 verification: independent bundle reproduction (ADR-013 §5)

**Assistance level:** L3 (Core-assist): I ran every command myself on my laptop, and neither M2
nor M3 was involved. The assistant read the README and `replay.md` with me, explained why my
first three attempts failed, gave me the part 2 commands (including checking that `03ada56`
lacks the verifier), and drafted this entry and the register updates from my output.

**What I asked:** do B2, the W23 reproduction, alone from the written instructions; then, after
they failed, for the commands.

**What was retained:** the W23 entry in [[evidence-m1]], with six findings for M2 and M3; the W23
plan row; the FT009 row in [[10-Final1/action-register]]; the G7 row in [[07-Defense/claims-ledger]].

**What I changed:** ran every command; checked the entry against my terminal output before
committing.

**How it was verified:** every number is copied from my own terminal output.

**Errors found:** the assistant first assumed my plain `python` was 3.9. It is 3.11.9 in that
folder, so that was not a finding.

**Rejections:** closing FT009 or G7 myself. G7 belongs to M3 and M2, and FT009 also needs the
supervisor's acceptance.

## 2026-11-22 — W35 verification: FJ-03 pair mode on my own machine

**Assistance level:** L3 (Core-assist): the assistant read M2's W35 entry for the expected
numbers, gave me the JDK 8 installer settings (no PATH, JAVA_HOME or registry change), the
fastjson fetch and build commands and M2's exact `diagnose` command, and drafted this entry from
my output; I ran every command myself on my laptop.

**What I asked:** help with W35, my verification of FJ-03 pair mode.

**What was retained:** the W35 entry in [[evidence-m1]] and the W35 plan row.

**What I changed:** installed Temurin 8 myself after the zip download would not extract; ran every command;
checked the entry against my terminal output before committing.

**How it was verified:** every number is copied from my own terminal output.

**Errors found:** the zip download would not extract ("Unrecognized archive format"). The
Adoptium installer worked.

**Rejections:** changing my system `java` to JDK 8. It stays 25.0.1; JDK 8 is set only in one window.

## 2026-11-22 — W35 follow-up: old bundle against the new `verify`, and a replay

**Assistance level:** L3 (Core-assist): the assistant gave me the `verify` and `replay` commands,
read `eval/bundle.py`, `runner/replay.py` and `eval/report.py` to explain both results, and drafted
this entry and the two findings; I ran every command myself.

**What I asked:** verify my W35 bundle with the new code, then replay it.

**What was retained:** the follow-up entry in [[evidence-m1]], and one corrected limitation in my
W35 entry (`wall_seconds` *is* in the report).

**What I changed:** ran every command; checked the entry against my output before committing.

**How it was verified:** the outputs are copied from my terminal. The two causes come from reading
the code, with line numbers.

**Errors found:**
- My earlier W35 entry said wall time was not recorded, but the report has `wall_seconds 167.438`.
  Corrected.
- One pasted one-liner was cut short (`SyntaxError`); the rerun is the one recorded.

**Rejections:** editing `runner/replay.py` or `eval/schema` myself. They are M2's and M3's; the
fixes are described for them.

## 2026-11-25 — #169 findings closed (re-check after #170 and #171)

**Assistance level:** L3 (Core-assist): the assistant gave me the commands and drafted this entry
from my output; I ran every command myself on my laptop.

**What I asked:** re-run my #169 checks after M2's and M3's fixes (M2's request).

**What was retained:** the entry in [[evidence-m1]].

**What I changed:** ran every command; checked the entry against my output before committing.

**How it was verified:** every result is copied from my own terminal output.

**Errors found:**
- My `set PATH` line had a typo (`sset`), so `javap` came from JDK 25; the test JVM was JDK 8 via
  `JAVA_HOME`.
- I interrupted the first replay; the second completed.

**Rejections:** none.

## 2026-11-25 — FT006 on a real project (FJ-03, Surefire vs FlakeTrace)

**Assistance level:** L3 (Core-assist): the assistant chose the comparison (Surefire's own
`runOrder` on the two FJ-03 tests), tested the commands first on fastjson in its container, gave
them to me, and drafted the entry from my output; I ran every command myself on my laptop.

**What I asked:** do what the FT006 row still needs from me (M2's request).

**What was retained:** the FT006 entry in [[evidence-m1]] and the FT006 row in
[[10-Final1/action-register]].

**What I changed:** ran every command; checked the entry against my output before committing.

**How it was verified:** every result is copied from my own terminal output.

**Errors found:** none.

**Rejections:** none.

## 2026-11-25 — A2: the runtime-fallback explanation

**Assistance level:** L3 (Core-assist): the assistant read ADR-001, ADR-015 and my code's
limitation text, checked `evidence/` and my note for causal wording (none found outside the
"not the cause" phrasing), and drafted section 3a and the A2 row.

**What I asked:** write the A2 explanation (M2's request).

**What was retained:** section 3a of [[04-Implementation/evidence-collector]] and the A2 row in
[[10-Final1/action-register]].

**What I changed:** read the section before committing.

**How it was verified:** each statement was checked against ADR-001, ADR-015,
`evidence/extract.py`'s `FIXED_LIMITATIONS` and my FJ-03 entry. Nothing was run.

**Errors found:** none.

**Rejections:** saying the fallback is built or scheduled for the Final. It is not.

## 2026-11-25 — W27: the container on my laptop

**Assistance level:** L3 (Core-assist): the assistant gave the build, run and check commands
(fresh clone, Windows volume form from the README), read the first build failure, suggested an
unchanged retry, and drafted the entry and the doc rows from my output.

**What I asked:** run M3's pinned container on my machine (M2's item 2).

**What was retained:** the W27 entry in [[evidence-m1]]; the W27 row in
[[10-Final1/iteration-2-plan]], the FT006/FT021 row in [[10-Final1/action-register]] and my row
in [[09-Team/members]].

**What I changed:** ran every command; checked the entry against my output before committing.

**How it was verified:** every result is copied from my own terminal output.

**Errors found:** the assistant's first `verify` command kept a `<folder from dir /b>`
placeholder, which `cmd` passed literally (`not a readable bundle`); re-run with the real folder
name → `OK`.

**Rejections:** editing the `Dockerfile` to add a pip retry. It is M3's file; noted for her
instead.

## 2026-11-26 — A2 section 3a corrected after M2's review

**Assistance level:** L3 (Core-assist): the assistant checked M2's three points against ADR-001,
ADR-015, the action register's status rule and the supervisor agenda, and redrafted the two
bullets of section 3a and the A2 row.

**What I asked:** apply M2's three fixes to section 3a.

**What was retained:** the corrected section 3a of [[04-Implementation/evidence-collector]] and
the A2 row in [[10-Final1/action-register]].

**What I changed:** read the corrected section before committing.

**How it was verified:** each point checked against the source. ADR-001 calls the Java agent "the
Iteration 2 fallback" and gives skill and perturbation risk as reasons against an agent "from the
start"; ADR-015 resets the named resource `r`, which FJ-03 does not have; the register's header
says none is `Done` without the supervisor's acceptance; agenda item 2 asks whether causal
certification remains a promise. Nothing was run.

**Errors found:** three in the assistant's 2026-11-25 draft, all found by M2: it gave ADR-001's
reasons against starting with an agent as the reason the fallback is unbuilt; it said "an
intervention" could name the resource on FJ-03, which ADR-015 as designed cannot; and it set A2 to
`Done`, which the register's rule does not allow.

**Rejections:** none.

## 2026-11-27 — W37: checking M3's FJ-03 interpretation wording

**Assistance level:** L3 (Core-assist): the assistant read M3's protocol change and W37 entry,
recounted the polluters from the seven committed bundles, compared the wording with my FJ-03
entry and evidence-collector §3, and drafted the review and requests.

**What I asked:** do the W37 interpretation check from M2's task list.

**What was retained:** the W37 entry in [[evidence-m1]] and the W37 row in
[[10-Final1/iteration-2-plan]].

**What I changed:** read the entry and the requests before committing.

**How it was verified:** the recount reads `report.json` of the seven committed bundles; each
finding quotes the protocol or M3's log. No JVM was run. On 2026-11-28 the assistant read M3's
fix (PR #191) and updated the entry: all four points addressed.

**Errors found:** none.

**Rejections:** editing M3's protocol myself; it is her file.
