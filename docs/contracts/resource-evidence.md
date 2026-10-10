# Resource evidence — output contract (Member 1)

**Status: CONFIRMED by Members 1, 2 and 3 (2026-10-09; approvals recorded on PR #17).**
Both other members consume it: Member 2's CLI calls the extractor end-to-end (see [Invocation](#invocation)),
and Member 3's report assembly uses its output. The extractor (Phases 2–4, `evidence/extract.py`) was
built against the draft of this contract. Any change from now on needs agreement from all three members.

This file defines what the Resource Evidence component (Member 1) outputs, and
how that output is projected into the shared diagnosis report
([report-schema.md](report-schema.md), owned by Member 3).

It details **Interface 2** of [interfaces.md](interfaces.md) and does not change
it: the three report fields named there (`shared_resource`,
`polluter_write_location`, `victim_read_location`) are produced exactly as
described under "Projection into Member 3's report" below. This file lives in
`docs/contracts/`, so per CONTRIBUTING.md it needs approval from both other
members.

## Scope (Iteration 1)

- **Static only.** Reads compiled `.class` files via `javap` (JDK 8). Never runs
  tests, never instruments at runtime.
- **Supported resource categories** (names identical to Member 3's
  `shared_resource.kind`):

  | `category` | Write | Read | `resource_id` format |
  | --- | --- | --- | --- |
  | `static-field` | `putstatic` | `getstatic` | `<owner class>#<field>`, e.g. `odfixture.Config#mode` |
  | `system-property` | `System.setProperty`, `System.clearProperty` | `System.getProperty`, `Integer.getInteger`, `Long.getLong`, `Boolean.getBoolean` | `sysprop:<key>`, e.g. `sysprop:odfixture.turbo` |

  `Long.getLong` is added to the brief's list because it reads a system
  property in exactly the same way as `Integer.getInteger`. Remove it if the
  team prefers the brief's exact list.
- A system property is a supported resource **only when its key is a constant
  string** (an `ldc` immediately feeding the call). Anything else is reported
  in `unsupported_observations`, never guessed.
- Class names are Java binary names with dots (`odfixture.Config`,
  nested: `a.B$C`), matching Member 3's `class` fields, not javap's
  slash form.

## Terms

- **Root**: a method that JUnit runs as part of one test: the test method
  itself, or one of its lifecycle methods (`via` values below), including
  lifecycle methods inherited from superclasses in the project's classes.
- **Depth**: the number of methods on the path from the root to the method
  that contains the access instruction. Depth 1 means the instruction is in
  the root itself. Depth 2 means it is in a project method called directly
  from the root. `--depth N` (default **2**, supported 1–5) reports accesses with `depth <= N`.
  *Pair mode deepens (ADR-006):* if a pair has no edge and a walk on either side stopped at the
  depth limit (`DEPTH_LIMIT`), the pair is analysed again one level deeper, up to 5. The
  shallowest depth with an edge wins. `--no-deepen` turns this off. Single-test mode never deepens.
  *Why the default is 2:* fixture F2's victim reads its system property inside `FeatureFlags.isTurboEnabled()`, one call below the test method, so at depth 1 F2 has no edge. Depth 2 also equals the POC's frozen scope ("direct references plus one hop"). The cost is more analysis time and more over-approximation (statically reachable accesses that may never run). The depth sweep still reports depths 1–3. See ADR-002; the range 1–5 and pair-mode deepening are ADR-006.
  *Numbering note:* the August POC numbers depth by **hops**: its `FT_HOPS=N` (and "depth N" in `POC/results/depth_sweep.csv`) is **depth N + 1** here, because `extract_static.py` loops `range(HOPS + 1)`. A POC or vault figure quoted at "depth 2" is depth 3 in this contract.
- **Project classes**: classes found in the input directories
  (`classes` + `test-classes`). Calls into anything else (JDK, JUnit,
  third-party jars) are never followed.

## Output 1 — accesses per test method

For each test method analysed, a list of resource accesses. Each access:

| Field | Type | Meaning |
| --- | --- | --- |
| `category` | `static-field` \| `system-property` | Resource category. |
| `resource_id` | string | As in the table above. |
| `resource` | object | `{kind, class, field}` or `{kind, key}`: exactly Member 3's `shared_resource` shape, so it can be copied into the report unchanged. |
| `access` | `READ` \| `WRITE` | |
| `class` | string | Class containing the access **instruction**. The brief called this `declaring_class`; renamed to match Member 3's `codeLocation.class`. Not the class that declares the field (that is `resource.class`). |
| `method` | string | Method containing the instruction (bare name, as in Member 3's `codeLocation.method`). |
| `descriptor` | string | JVM method descriptor of `method`, e.g. `()Z`. Disambiguates overloads; dropped when projecting into the report. |
| `bytecode_offset` | integer | Offset of the access instruction as printed by `javap -c`. For system properties: the offset of the `invoke…` call, not the `ldc` that loads the key. |
| `via` | enum | Which root the access was reached from: `TEST_METHOD`, `BEFORE`, `AFTER`, `BEFORE_CLASS`, `AFTER_CLASS` (JUnit 4 annotations), `SETUP`, `TEARDOWN` (JUnit 3), `CLINIT` (test class's `<clinit>`). |
| `depth` | integer ≥ 1 | As defined above. Always equals `len(call_path)`. |
| `call_path` | list | Frames from the root to the method containing the access. Each frame is `{class, method, bytecode_offset}`. In every frame except the last, `bytecode_offset` is the call instruction that leads to the next frame. In the last frame it equals the access offset. |

Per test, alongside the accesses:

- `unsupported_observations`: things seen in the bytecode that **may** touch
  shared state but that this component cannot model (kinds below).
- `external_calls_not_followed`: sorted distinct owner classes of calls that
  leave the project (e.g. `org.junit.Assert`). Informational only.

## Output 2 — edges for one polluter–victim pair

Given `--polluter` and `--victim`:

| Field | Type | Meaning |
| --- | --- | --- |
| `polluter`, `victim` | `{class, method}` | Same shape as Member 3's `testIdentifier`. |
| `edges` | list | One entry per resource that the polluter WRITES (any root, including `AFTER`/`TEARDOWN`) and the victim READS (any root). |
| `edges[].resource_id`, `edges[].resource` | | As in Output 1. |
| `edges[].polluter_write_locations` | list of accesses | Every polluter WRITE of that resource (full Output-1 access records). |
| `edges[].victim_read_locations` | list of accesses | Every victim READ of that resource. |
| `no_supported_resource_evidence` | boolean | `true` iff `edges` is empty. It means *no supported static evidence was found*. It does **not** mean the tests are independent. |
| `unsupported_observations` | list | Polluter's and victim's, each tagged with `side: "polluter" \| "victim"`. |
| `limitations` | list of strings | The fixed list below, plus case-specific notes. |
| `depth_requested` | integer | The `--depth` asked for (default 2). Set by `analyse_pair` and the command line. |
| `depth_used` | integer | The depth the edges were found at, after any deepening; equals `depth_requested` when nothing was deepened. Set by `analyse_pair` and the command line. |

**Ordering (deterministic):** edges are sorted by
`(min write depth + min read depth, resource_id)`. Locations within an edge
are sorted by `(depth, via, class, method, bytecode_offset)`.

## `unsupported_observations` kinds

| `kind` | Recorded when |
| --- | --- |
| `SYSPROP_NON_CONSTANT_KEY` | A supported system-property method is called but its key is not a constant string. |
| `SYSPROP_BULK` | `System.setProperties` / `System.getProperties` (the whole `Properties` object is shared; individual keys are not modelled). |
| `REFLECTION` | Calls into `java.lang.reflect.*` (e.g. `Field.set`, `Method.invoke`). The target is not resolved. |
| `INVOKEDYNAMIC` | `invokedynamic` (lambdas, string concat); the body is not followed. |
| `VIRTUAL_DISPATCH` | An `invokevirtual`/`invokeinterface` whose runtime target may be a project subclass/implementation. Only the statically named target is followed, if it exists. |
| `UNRESOLVED_CALL` | A call to a project class whose target method cannot be found in that class or its project superclasses. |
| `DEPTH_LIMIT` | A project call that was not followed because `--depth` was reached. |
| `IMPLICIT_CLINIT` | A static member of a project class with a `<clinit>` is used. The JVM may run that `<clinit>` implicitly (e.g. `odfixture.Config.<clinit>` writes `Config.mode`), and this component does not follow it. |
| `JUNIT_RULE_OR_RUNNER` | The test class uses `@Rule`, `@ClassRule` or a `@RunWith` runner; code they run is not analysed. |

Each observation: `{kind, class, method, bytecode_offset, detail}` (+ `side`
in Output 2).

## Fixed limitations (always emitted)

1. Static analysis only; no runtime evidence (Iteration 2).
2. Calls into JDK classes and third-party jars are not followed.
3. Virtual dispatch to subclasses and reflection are not resolved (see `VIRTUAL_DISPATCH`, `REFLECTION`).
4. Only static fields and constant-key system properties are modelled. Files, environment variables, network, databases, singletons reached through instance fields, etc. are not.
5. Written values are not modelled: a polluter that writes and then restores the original value still produces a WRITE.
6. Execution timing is not modelled (e.g. a victim `<clinit>` read that happens before the polluter runs).
7. Missing evidence is not proof of independence.

## Invocation

**Implemented** (Phases 2–4 and ADR-006, `evidence/extract.py`). Language: Python 3, standard library only.
Bytecode is read by running `javap -c -p` (and `-v` for annotations) from a
JDK 8 or newer found on `PATH`.

```
python3 -m evidence.extract --classes <dir> --test-classes <dir> \
    --polluter <Class#method> --victim <Class#method> [--depth N] [--no-deepen]
python3 -m evidence.extract --classes <dir> --test-classes <dir> \
    --test <Class#method> [--depth N]
```

(On Windows the interpreter is usually `python` or `py -3` instead of `python3`.)

| Flag | Required | Meaning |
| --- | --- | --- |
| `--classes <dir>` | yes | The target project's compiled main classes, e.g. `target/classes`. |
| `--test-classes <dir>` | yes | The target project's compiled test classes, e.g. `target/test-classes`. Together with `--classes`, this defines the *project classes*. |
| `--polluter <Class#method>` | pair mode | The candidate polluter, e.g. `odfixture.FeaturePolluterTest#enableTurbo`. Must be given together with `--victim`. |
| `--victim <Class#method>` | pair mode | The victim test. |
| `--test <Class#method>` | single mode | One test method; produces Output 1 only. Cannot be combined with `--polluter`/`--victim`. |
| `--depth N` | no | Call depth as defined under [Terms](#terms). Default 2; accepted values 1–5. In pair mode this is the starting depth (see deepening under [Terms](#terms)). |
| `--no-deepen` | no | Pair mode: analyse at exactly `--depth`, without deepening. |

Exactly one mode must be given: `--polluter` + `--victim`, or `--test`.

**Output:** one JSON object on **stdout** (UTF-8), shaped like the
[example](#example--fixture-f2-at---depth-2) below. In pair mode it contains
`tests` (Output 1 for both tests) and `pair` (Output 2). In pair mode `analysis.depth` is the
requested depth, and `tests` holds the analyses at `pair.depth_used`. In single mode it
contains `tests` only. Nothing else is printed to stdout, so the caller can
parse it directly. Diagnostics go to stderr.

**The extractor never runs tests and never writes into the class
directories.** It only reads `.class` files.

**Calling it from another component** (agreed with Member 2, 2026-10-09):

- `python3 -m evidence.extract` imports the `evidence` package, so run it with the **repository root**
  as the working directory, or put the root on `PYTHONPATH`. Pass **absolute** class directories.
- Or call it in-process: `from evidence import extract`, then
  `project = extract.Project([classes, test_classes])`,
  `pair = extract.analyse_pair(project, polluter_id, victim_id, depth=2, deepen=True)` (ADR-006:
  analyses both tests and deepens as above), and `extract.report_fields(pair)` for the report.
  The older route, `extract.analyse_test(project, test_id, depth)` for each test then
  `extract.find_edges(polluter_id, polluter_result, victim_id, victim_result)`, still works but
  never deepens and sets no `depth_requested`/`depth_used`. Errors raise `extract.ExtractError`, whose
  `.exit_code` is 1 or 2 as below.
- `javap` comes from a JDK 8+ on `PATH`; the environment variable `FLAKETRACE_JAVAP` can name another one.

## Exit codes and errors

- `0`: analysis completed (including an empty edge list).
- `1`: internal error, e.g. `javap` not found or it failed on a class file. One
  line `error: <reason>` on stderr, and no JSON on stdout.
- `2`: input error: missing/unreadable class directory, test class or method
  not found, unsupported `--depth`, or an invalid flag combination. One line
  `error: <reason>` on stderr, and no JSON on stdout.

## Example — fixture F2 at `--depth 2`

All class names, offsets and call paths below come from real `javap -c -p`
output (JDK 1.8.0_502) of the unmodified `fixtures/od-fixture`, saved at
`evidence/javap-dumps/phase1-f1-f2.txt`. The JSON itself was
**written by hand from that output**, because the extractor does not exist yet.

```json
{
  "contract": "flaketrace.resource-evidence/v0-draft",
  "instrumentation_level": "static-only",
  "analysis": {
    "depth": 2,
    "class_dirs": ["fixtures/od-fixture/target/classes", "fixtures/od-fixture/target/test-classes"],
    "javap_version": "1.8.0_502"
  },
  "tests": {
    "odfixture.FeaturePolluterTest#enableTurbo": {
      "test": { "class": "odfixture.FeaturePolluterTest", "method": "enableTurbo" },
      "accesses": [
        {
          "category": "system-property",
          "resource_id": "sysprop:odfixture.turbo",
          "resource": { "kind": "system-property", "key": "odfixture.turbo" },
          "access": "WRITE",
          "class": "odfixture.FeaturePolluterTest",
          "method": "enableTurbo",
          "descriptor": "()V",
          "bytecode_offset": 4,
          "via": "TEST_METHOD",
          "depth": 1,
          "call_path": [
            { "class": "odfixture.FeaturePolluterTest", "method": "enableTurbo", "bytecode_offset": 4 }
          ]
        }
      ],
      "unsupported_observations": [],
      "external_calls_not_followed": []
    },
    "odfixture.FeatureVictimTest#expectsTurboDisabled": {
      "test": { "class": "odfixture.FeatureVictimTest", "method": "expectsTurboDisabled" },
      "accesses": [
        {
          "category": "system-property",
          "resource_id": "sysprop:odfixture.turbo",
          "resource": { "kind": "system-property", "key": "odfixture.turbo" },
          "access": "READ",
          "class": "odfixture.FeatureFlags",
          "method": "isTurboEnabled",
          "descriptor": "()Z",
          "bytecode_offset": 2,
          "via": "TEST_METHOD",
          "depth": 2,
          "call_path": [
            { "class": "odfixture.FeatureVictimTest", "method": "expectsTurboDisabled", "bytecode_offset": 0 },
            { "class": "odfixture.FeatureFlags", "method": "isTurboEnabled", "bytecode_offset": 2 }
          ]
        }
      ],
      "unsupported_observations": [],
      "external_calls_not_followed": ["org.junit.Assert"]
    }
  },
  "pair": {
    "polluter": { "class": "odfixture.FeaturePolluterTest", "method": "enableTurbo" },
    "victim": { "class": "odfixture.FeatureVictimTest", "method": "expectsTurboDisabled" },
    "edges": [
      {
        "resource_id": "sysprop:odfixture.turbo",
        "resource": { "kind": "system-property", "key": "odfixture.turbo" },
        "polluter_write_locations": ["<the WRITE access above, in full>"],
        "victim_read_locations": ["<the READ access above, in full>"]
      }
    ],
    "no_supported_resource_evidence": false,
    "unsupported_observations": [],
    "limitations": ["<the 7 fixed limitations>"]
  }
}
```

(The `"<…>"` placeholders only shorten this document; real output repeats the
full records.)

At `--depth 1` the same pair has **no edge**. The victim's read sits one call
below the test method. The output is `"edges": []`,
`"no_supported_resource_evidence": true`, and the victim side gets one
observation:
`{"kind": "DEPTH_LIMIT", "side": "victim", "class": "odfixture.FeatureVictimTest", "method": "expectsTurboDisabled", "bytecode_offset": 0, "detail": "odfixture.FeatureFlags#isTurboEnabled()Z not followed"}`.

## Projection into Member 3's report

| Report field | Filled from |
| --- | --- |
| `shared_resource` | `edges[0].resource`, or `null` if no edges |
| `polluter_write_location` | `{class, method, bytecode_offset}` of `edges[0].polluter_write_locations[0]`, or `null` |
| `victim_read_location` | `{class, method, bytecode_offset}` of `edges[0].victim_read_locations[0]`, or `null` |
| `instrumentation_level` | `"static-only"` |
| `limitations` | Member 1 contributes the fixed limitations above + one line per dropped edge/location (see open question 1) + one line when the reported write or read is deeper than the default depth 2 (ADR-006, requested by Member 2) |

Example: F2 at depth 2 projects to `shared_resource = {kind: "system-property", key: "odfixture.turbo"}`,
`polluter_write_location = {class: "odfixture.FeaturePolluterTest", method: "enableTurbo", bytecode_offset: 4}`,
`victim_read_location = {class: "odfixture.FeatureFlags", method: "isTurboEnabled", bytecode_offset: 2}`.

## Open questions (status 2026-10-09)

1. **ANSWERED (Member 2, 2026-10-09): option (a).** The report takes `edges[0]` (shortest combined
   depth, then `resource_id`) and the first write/read location; `limitations` names every
   other edge and how many locations were dropped. Implemented as `extract.report_fields`.
   Original question: **Singular location fields.** The report holds one resource and one location
   per side. Anything beyond `edges[0]` and its first locations is lost
   (e.g. F2 at depth 2 has one edge, but FJ cases may have several). Options:
   (a) accept it and list dropped edges in `limitations`; (b) add an optional
   pointer field, e.g. `resource_evidence_reference` (path to this component's
   JSON), like `execution_record_reference`. Option (b) is a schema change
   (the schema sets `additionalProperties: false`).
2. **ANSWERED (Member 3, 2026-10-10): yes, that is the intended meaning.** `victim_read_location`
   names where the read bytecode instruction actually executes, even inside a helper (F2:
   `odfixture.FeatureFlags#isTurboEnabled@2`), not the call site in the test method. This is
   more useful to a developer fixing the bug — it is literally where the read happens — and
   matches `polluter_write_location`'s own meaning symmetrically. The test method's call site
   is still recoverable from the full `call_path` in Output 2, for anyone who wants it; the
   singular report field just doesn't repeat it. No code or schema change needed — this
   confirms `eval/report.py`'s existing behaviour (it takes `report_fields`'s locations as-is).
   Original question: **`victim_read_location` may name a non-test class** at depth > 1 (F2:
   `odfixture.FeatureFlags#isTurboEnabled@2`). Is that the intended meaning
   ("where exactly the victim reads"), or should it name the call site in the
   test method (the first `call_path` frame)?
3. **Partly answered by Phase 4:** the extractor reports F3 pairwise as `odfixture.Toggles#flagA`
   (A → victim) and `#flagB` (B → victim). Still open for Member 3: the ground-truth format.
   Original question: **F3 ground truth is not machine-comparable.** `ground_truth.json` F3 has
   `"field": "flagA and flagB (both required)"`. This component is pairwise:
   `ToggleAPolluterTest#setFlagA → ToggleVictimTest` should yield an edge on
   `odfixture.Toggles#flagA`, and the B pair one on `#flagB`. Could F3 list
   one `shared_resource` per polluter (e.g. a list), so the comparison can be
   automatic?
4. **ANSWERED (Member 3, 2026-10-10): yes, acceptable.** Resources-only automatic comparison
   plus hand-verified offsets is enough evidence for Iteration 1: `GroundTruthTest` already
   catches a wrong or missing *resource* automatically on every change (156 pairs, exact
   match), which is the failure mode that actually matters (wrong field = wrong diagnosis).
   Exact bytecode offsets were hand-verified for F1 (`javap -c -p`, write 1, read 1,
   `eval/examples/example_f1_verified.json`) and spot-checked for F2
   (`FeatureFlags.isTurboEnabled@2`, confirmed independently by Member 1 against
   `eval/reports/f2.json`). Encoding exact offsets into `ground_truth.json` for every case
   would be brittle (any unrelated line-number shift in the fixture source breaks it) for
   little extra protection beyond what the resource check and spot-checks already give.
   Original question: **Ground truth has no expected locations**, so the automatic Phase 5 check
   can compare resources only. Offsets will be checked by hand against
   `javap`. Is that acceptable?
5. **Illustrative offsets. RESOLVED 2026-10-09.** Member 3 verified the real JDK 8 offsets independently with `javap -c -p` (write 1, read 1) and updated `eval/examples/example_f1_verified.json` (commit `af70048`, PR #7). Earlier examples labelled illustrative are still not authoritative; this component does not produce them yet.
6. **ANSWERED (Member 3, 2026-10-10): out of scope for Iteration 1, same boundary as filesystem
   evidence.** No fixture case exercises the brittle shape (victim fails alone, passes after a
   state-setter), so there is no real case driving a new outcome category, and inventing one
   under schedule pressure risks a category nobody has tested end to end. `eval/outcome.py`'s
   decision table reporting a brittle case as `UNRESOLVED(VICTIM_FAILS_ALONE)` is not wrong for
   Iteration 1 — it correctly reports that the victim fails alone, which is true — it is just
   not the *most informative* category for that specific mechanism. If a real brittle case
   turns up in evaluation (e.g. a fastjson pair), it is reported this way and the limitation is
   named, not worked around. A distinct outcome/reason for brittle cases is a candidate for
   Iteration 2, alongside the resource-family expansion already planned there.
   Original question: **BRITTLE cases (POC FJ-01).** In the POC the "victim" fails alone and passes
   after a *state-setter* (`DateFieldTest8`). The resource edge has the same
   write-then-read shape, but the decision table would yield
   `UNRESOLVED(VICTIM_FAILS_ALONE)`. Does Iteration 1 include brittle cases,
   and if so under which outcome?
