# Resource evidence — output contract (Member 1)

**Status: DRAFT, not yet confirmed with Member 3.** No extraction code may be
written against this contract until Member 3 has confirmed it. Changes after
confirmation need agreement from Member 1 and Member 3 (Member 2 consumes
nothing from this file in Iteration 1).

This file defines what the Resource Evidence component (Member 1) outputs, and
how that output is projected into the shared diagnosis report
([report-schema.md](report-schema.md), owned by Member 3).

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
  from the root. `--depth N` (default 1, supported 1–3) reports accesses with
  `depth <= N`.
  *Note:* the August POC's `FT_HOPS=1` corresponds to **depth 2** here.
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

## Exit codes and errors

- `0`: analysis completed (including an empty edge list).
- `2`: input error: missing/unreadable class directory, test class or method
  not found, unsupported `--depth`. One line `error: <reason>` on stderr, and
  no JSON on stdout.

## Example — fixture F2 at `--depth 2`

All class names, offsets and call paths below come from real `javap -c -p`
output (JDK 1.8.0_502) of the unmodified `fixtures/od-fixture`, saved at
`resource-evidence/evidence/phase1-javap-f1-f2.txt`. The JSON itself was
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
| `limitations` | Member 1 contributes the fixed limitations above + one line per dropped edge/location (see open question 1) |

Example: F2 at depth 2 projects to `shared_resource = {kind: "system-property", key: "odfixture.turbo"}`,
`polluter_write_location = {class: "odfixture.FeaturePolluterTest", method: "enableTurbo", bytecode_offset: 4}`,
`victim_read_location = {class: "odfixture.FeatureFlags", method: "isTurboEnabled", bytecode_offset: 2}`.

## Open questions for Member 3 (must be answered before Phase 2)

1. **Singular location fields.** The report holds one resource and one location
   per side. Anything beyond `edges[0]` and its first locations is lost
   (e.g. F2 at depth 2 has one edge, but FJ cases may have several). Options:
   (a) accept it and list dropped edges in `limitations`; (b) add an optional
   pointer field, e.g. `resource_evidence_reference` (path to this component's
   JSON), like `execution_record_reference`. Option (b) is a schema change
   (the schema sets `additionalProperties: false`).
2. **`victim_read_location` may name a non-test class** at depth > 1 (F2:
   `odfixture.FeatureFlags#isTurboEnabled@2`). Is that the intended meaning
   ("where exactly the victim reads"), or should it name the call site in the
   test method (the first `call_path` frame)?
3. **F3 ground truth is not machine-comparable.** `ground_truth.json` F3 has
   `"field": "flagA and flagB (both required)"`. This component is pairwise:
   `ToggleAPolluterTest#setFlagA → ToggleVictimTest` should yield an edge on
   `odfixture.Toggles#flagA`, and the B pair one on `#flagB`. Could F3 list
   one `shared_resource` per polluter (e.g. a list), so the comparison can be
   automatic?
4. **Ground truth has no expected locations**, so the automatic Phase 5 check
   can compare resources only. Offsets will be checked by hand against
   `javap`. Is that acceptable?
5. **Illustrative offsets.** `eval/examples/example_f1_verified.json` uses
   write offset 3 / read offset 5 for F1. Real JDK 8 offsets are 1 / 1
   (`putstatic` at 1 in `ConfigPolluterTest.pollute`, `getstatic` at 1 in
   `ConfigVictimTest.expectsDefaultMode`). The examples are labelled
   illustrative, so this is only a note in case realistic values are wanted.
6. **BRITTLE cases (POC FJ-01).** In the POC the "victim" fails alone and passes
   after a *state-setter* (`DateFieldTest8`). The resource edge has the same
   write-then-read shape, but the decision table would yield
   `UNRESOLVED(VICTIM_FAILS_ALONE)`. Does Iteration 1 include brittle cases,
   and if so under which outcome?
