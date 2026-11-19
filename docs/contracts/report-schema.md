# Diagnosis report schema — shared contract

*Schema v2 (ADR-010/ADR-011, W19, 2026-11-18). The decision table and field shapes below
implement [[03-Design/decisions/ADR-010-verdict-contract-v2]], agreed by all three members
2026-11-13 (PR #101) and built by Member 3 in W19. Schema v1 (what this file described through
the Mid) is frozen at tag `mid-eval-v1`.*

This is a **shared contract**. The schema lives at
[eval/schema/report.schema.json](../../eval/schema/report.schema.json) and the
decision logic that produces `outcome`/`unresolved_reason`/`candidate_reasons`
lives at [eval/outcome.py](../../eval/outcome.py). Changing any field here, or
the decision table, needs agreement from all three members — downstream
consumers (the UI, the benchmark/yield report) depend on this shape staying
stable.

Validate any report against the schema with
[eval/schema_validator.py](../../eval/schema_validator.py)
(`validate_report(dict)` / `validate_report_file(path)`), which uses the
`jsonschema` package so the validator can never drift from the schema
document itself.

## Fields

| Field | Type | Produced by | Meaning |
| --- | --- | --- | --- |
| `schema_version` | `2` (fixed) | Member 3 | Which version of this contract the report was built against. |
| `victim` | `{class, method}` | Member 2 | The test being diagnosed. |
| `polluters` | `{class, method}[]` | Member 3, from Member 2's raw counts | The test(s) identified as responsible. Empty whenever the outcome is `UNRESOLVED` for any reason except `SOURCE_INTEGRITY_FAILED` — a found candidate is not reported as blamed unless the evidence actually supports it (ADR-010 rows 6–11: "no test is blamed"). |
| `original_failing_order` | `{class, method}[]` | Member 2 | The full order in which the failure was first observed (the declared/CI order, or what `--order` gave), before minimisation. |
| `reduced_sequence` | `{class, method}[]` | Member 3, from Member 2's raw counts | The minimised ordered list of tests (polluter(s) + victim) that reproduces the failure — collapsed to just `[victim]` whenever `polluters` is emptied for the "no test is blamed" reason above; the starting order when no polluter was ever found (`INCONSISTENT`/`NOT_REPRODUCED`). |
| `reproduction` | a *runTallyWithInterval*: `{n, passed, matched, other, infra, confidence, lower, upper}` | Member 3, from Member 2's `sequence_tally` (ADR-010 §1) | How `reduced_sequence`'s n repeated runs broke down into the four ADR-010 categories, with `matched`'s Wilson score interval. `matched` replaces v1's `successes`; `other`/`infra` are new. |
| `victim_alone` | same shape as `reproduction` | Member 3, from Member 2's `alone_tally` | Same breakdown for running the victim alone. Any nonzero `matched` or `other` withholds a verdict (ADR-010 rows 6–7); nonzero `infra` does too (row 8). |
| `shared_resource` | `{kind, class, field}` or `{kind, key}` or `null` | Member 1 | The static field or system property both the polluter and the victim touch. `null` if no resource edge was found, or if `polluters` is emptied (see above — the write location would otherwise still name the un-blamed polluter). |
| `polluter_write_location` | `{class, method, bytecode_offset}` or `null` | Member 1 | Where the polluter writes the shared resource. Same nulling rule as `shared_resource`. |
| `victim_read_location` | `{class, method, bytecode_offset}` or `null` | Member 1 | Where the victim reads the shared resource. Same nulling rule. |
| `resource_edges` | array of `{shared_resource, polluter_write_location, victim_read_location}` | Member 1 (via Member 3's assembly) | New in v2: every edge Member 1 found, not just the one shown in `shared_resource`. Iteration 1/2 limitation: today's extractor reports at most one edge per polluter, so this has at most one entry until Member 1's W21 lands all edges. Empty whenever `shared_resource` is `null`. |
| `failure_signature` | `{exception_type, message, stack_trace}` or `null` | Member 2 | The reference failure signature `reproduction`/`victim_alone` are measured against. `null` exactly when no reference failure was ever observed anywhere in the diagnosis (ADR-010 rows 4/5) — this can only happen when `unresolved_reason` is `NOT_REPRODUCED` or `INFRASTRUCTURE_FAILURE`, but not every report with one of those two reasons has a null signature (rows 10/11 reach the same two reasons from a reference established during the search). |
| `order_exploration` | `{order_given, shuffled_orders_tried, orders_exhausted, seed_base, reproducing_seed, infrastructure_failures}`, optional | Member 2 | ADR-008, unchanged by ADR-010. Omitted entirely until the producing fields exist. |
| `assurance` | `{sequence: {reproduces, passes_alone, deletion}, resource: {level, mechanism}}` | Member 3 | New in v2 (ADR-010 §6): the report's own evidence levels. Present only when `outcome` is `CANDIDATE` or `VERIFIED`. `deletion` is one of `DELETION_VERIFIED`/`INCONCLUSIVE`/`INCOMPLETE`/`NOT_APPLICABLE` (ADR-011) or `NOT_YET_CHECKED` — Member 3's own addition, flagged for the team's review, meaning ADR-011's deletion checks (W20) have not landed yet. `resource.mechanism` is always `NOT_ASSESSED` until ADR-015 lands (not built). |
| `instrumentation_level` | `"static-only"` (fixed) | contract constant | Runtime instrumentation is not built. |
| `execution_record_reference` | string | Member 2 | Pointer to Member 2's recorded execution log / run id backing this report. |
| `source_integrity` | `{passed, details}` | Member 2 | Whether the source-integrity check confirmed the instrumented bytecode matches the analyzed source. If `passed` is `false`, the outcome is always `UNRESOLVED(SOURCE_INTEGRITY_FAILED)` — see decision table. |
| `outcome` | `VERIFIED` \| `CANDIDATE` \| `UNRESOLVED` | Member 3, via `eval.outcome.decide()` | The final verdict. |
| `unresolved_reason` | enum or `null` | Member 3 | Required (non-null) when `outcome` is `UNRESOLVED`; must be `null` otherwise. |
| `candidate_reasons` | string[] | Member 3 | New in v2: every certification claim (S1/S3/R1) a `CANDIDATE` outcome did not meet, not just one. Always present; empty unless `outcome` is `CANDIDATE`. |
| `limitations` | string[] | Member 3 | Free-text caveats about this specific diagnosis. |

## Outcome enum

- **`VERIFIED`** — all four claims (S1 reproduces, S2 passes alone, S3 every kept test needed, R1 a static overlap exists) are established. Does **not** assert the resource is the cause.
- **`CANDIDATE`** — reproduces reliably and passes alone, but at least one of S1/S3/R1 is not established — see `candidate_reasons`.
- **`UNRESOLVED`** — no verdict can be made; see `unresolved_reason`.

**Ranking alone must never produce `VERIFIED`** — a resource edge
(`shared_resource` non-null) is always required; without one the outcome is
`CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`, never `VERIFIED`.

## Unresolved-reason enum

| Reason | Meaning |
| --- | --- |
| `SOURCE_INTEGRITY_FAILED` | The source-integrity check failed, so no other evidence can be trusted. Checked first, overrides everything. |
| `INCONSISTENT_OUTCOMES` | New (ADR-010 §5, FT010). The failure was seen once in the starting order and could not be obtained again. |
| `BUDGET_EXHAUSTED` | New (ADR-010/ADR-014). The execution budget ran out before a sequence was found. Not yet emitted — ADR-014/W24 has not landed. |
| `INFRASTRUCTURE_FAILURE` | A crash or timeout, never a real exception. Three distinct rows reach this: no reference anywhere (row 4), the alone check only crashed (row 8), or the candidate sequence only crashed on re-verification (row 10). |
| `NOT_REPRODUCED` | Either no reference failure was ever established (row 5), or one was established during the search but the candidate sequence did not reproduce it on re-verification (row 11 — ADR-011's motivating case: single-trial `ddmin` can shrink to a sequence that does not hold up). |
| `VICTIM_FAILS_ALONE` | The victim reproduced its reference failure signature at least once alone. |
| `VICTIM_FAILS_ALONE_DIFFERENTLY` | New (ADR-010 §3 row 7, FT003 — the Mid's bug). The victim failed alone with a **different** signature. The Mid build counted only matching alone failures, so this read as "never failed alone" and could name a polluter wrongly. |
| `SIGNATURE_MISMATCH` | A reference was established, the victim passes alone, but the candidate sequence's re-verification failed only with a different signature. |

**Retired by ADR-010 (2026-11-13):** `NO_SUPPORTED_RESOURCE_EVIDENCE` and
`BELOW_CONFIDENCE_THRESHOLD` are no longer `UNRESOLVED` reasons — a
reliably-reproducing, passes-alone sequence is `CANDIDATE` now (Q1, option A),
with the same names reused as `candidate_reasons` values instead.

## Candidate-reasons enum

| Reason | Claim unmet |
| --- | --- |
| `BELOW_REPLAY_THRESHOLD` | S1 — Wilson lower bound of `reproduction.matched/n` is below the threshold (0.70). |
| `DELETION_EVIDENCE_INCONCLUSIVE` | S3 — a deletion check (ADR-011) found removing a kept test gave an inconclusive result. |
| `DELETION_EVIDENCE_INCOMPLETE` | S3 — a deletion check did not run (budget, or not yet built). |
| `NO_SUPPORTED_RESOURCE_EVIDENCE` | R1 — no polluter-write/victim-read resource edge was found. |
| `BUDGET_EXHAUSTED` | Reserved; not currently emitted (ADR-011 §3 rolls a mid-run budget exhaustion into `DELETION_EVIDENCE_INCOMPLETE` instead). |

A `CANDIDATE` report can carry several of these at once.

## Decision table

Implemented in [eval/outcome.py](../../eval/outcome.py) (`decide()`), evaluated
top to bottom, first match wins. Full rationale, the four claims S1–S3/R1, and
the "no test is blamed" rule are in
[[03-Design/decisions/ADR-010-verdict-contract-v2]] section 3; this file's
copy is a quick-reference.

1. `source_integrity.passed` is `false` → `UNRESOLVED(SOURCE_INTEGRITY_FAILED)`
2. The search was inconsistent (seen once, not again) → `UNRESOLVED(INCONSISTENT_OUTCOMES)`
3. Execution budget ran out before a sequence was found → `UNRESOLVED(BUDGET_EXHAUSTED)`
4. No reference failure ever established, and an infrastructure failure somewhere → `UNRESOLVED(INFRASTRUCTURE_FAILURE)`
5. No reference failure ever established → `UNRESOLVED(NOT_REPRODUCED)`
6. `victim_alone.matched >= 1` → `UNRESOLVED(VICTIM_FAILS_ALONE)`
7. `victim_alone.other >= 1` → `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)`
8. `victim_alone.infra >= 1` → `UNRESOLVED(INFRASTRUCTURE_FAILURE)`
9. `reproduction.matched == 0` and `reproduction.other >= 1` → `UNRESOLVED(SIGNATURE_MISMATCH)`
10. `reproduction.matched == 0` and `reproduction.infra >= 1` → `UNRESOLVED(INFRASTRUCTURE_FAILURE)`
11. `reproduction.matched == 0` → `UNRESOLVED(NOT_REPRODUCED)`
12. Any of S1 (reproduces ≥ 0.70 Wilson lower bound), S3 (deletion-verified) or R1 (resource edge exists) not established → `CANDIDATE`, with every unmet claim in `candidate_reasons`
13. Otherwise → `VERIFIED`

### Decisions made explicitly with all three members (2026-11-13)

- **Q1 (option A):** a sequence that reproduces reliably and passes alone but has no resource edge is `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`, not `UNRESOLVED`.
- **Q2:** no bounded retries for an `INFRA` run before it counts — a crash or timeout counts as `INFRA` as-is; row 8 stays strict.
- **Q3:** `VERIFIED` keeps its name, always shown with the qualifier "(sequence)" — parked pending the supervisor's view.
- **S3/budget defaulting:** `eval.outcome.decide()`'s `deletion_status`/`budget_exhausted` inputs default to "not yet checked"/`False` until ADR-011 (W20) and ADR-014 (W24) land, so this W19 change does not regress any fixture's `VERIFIED` verdict (test T6). The report says so honestly (`assurance.sequence.deletion = "NOT_YET_CHECKED"`) rather than fabricating a result.

## Examples

Hand-written illustrative examples for every row of the decision table live
under [eval/examples/](../../eval/examples/), labelled as examples, not
results — see that folder's README. They are validated against this schema
and cross-checked against `eval.outcome.decide()` in
[eval/tests/test_examples.py](../../eval/tests/test_examples.py).
