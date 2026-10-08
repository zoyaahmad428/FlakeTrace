# Example diagnosis reports

Everything in this folder is a **hand-written illustrative example**, not a
recorded result from running FlakeTrace against any real project. Counts like
"17/20" are chosen by hand to exercise one row of the decision table in
[eval/outcome.py](../outcome.py) and are internally consistent with
`eval.stats.wilson_interval` (the `lower`/`upper` fields were computed by
calling that function with the chosen `successes`/`n`, not typed from
guesswork) -- but no actual 20-repetition benchmark run produced them.

Two examples (`example_f1_verified.json`, `example_f3_candidate.json`) reuse
class/method names from `fixtures/od-fixture` because that fixture's F1 and
F3 cases are structurally the scenario being illustrated, but the specific
reproduction counts are still illustrative, not measurements from Phase 1's
validation runs (which ran single reps, not 20-rep statistics).

Each file is named after the decision-table row it demonstrates:

| File | Decision table row |
| --- | --- |
| `example_f1_verified.json` | reproduces strongly, resource edge exists -> VERIFIED |
| `example_f3_candidate.json` | reproduces weakly (lower bound < 0.70), resource edge exists -> CANDIDATE |
| `example_victim_fails_alone.json` | victim fails alone -> UNRESOLVED(VICTIM_FAILS_ALONE) |
| `example_not_reproduced.json` | sequence never fails at all -> UNRESOLVED(NOT_REPRODUCED) |
| `example_signature_mismatch.json` | sequence fails, but never with the reference signature -> UNRESOLVED(SIGNATURE_MISMATCH) |
| `example_no_resource_evidence.json` | reproduces strongly, no resource edge -> UNRESOLVED(NO_SUPPORTED_RESOURCE_EVIDENCE) |
| `example_source_integrity_failed.json` | source-integrity check failed -> UNRESOLVED(SOURCE_INTEGRITY_FAILED) |

`eval/tests/test_examples.py` validates every file here against
`eval/schema/report.schema.json` and cross-checks that running
`eval.outcome.decide()` on the same counts reproduces the same outcome.
