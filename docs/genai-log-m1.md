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

**What I changed:** *fill after review.*

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

**What I changed:** *fill after review.*

**How it was verified:** the depth-numbering claim was checked against the POC
source (`extract_static.py` lines 29 and 132) and `depth_sweep.csv`; see
`docs/evidence-m1.md`.

**Errors found:** the vault's depth wording (`depth-configurable.md`, claims
C6/C7) uses the POC's hop numbering, so its "depth 2" is depth 3 in our
contract. Flagged in ADR-002 for a wording check; those docs were not edited.

**Rejections:** (a2) copying POC code; (b) ASM; default depth 1 and 3.
Reasons in ADR-002.
