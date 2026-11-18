# Example diagnosis reports

This folder has two kinds of file, clearly distinguished in each file's own
`limitations` array -- check that field before trusting any number here.

**REAL** — `reproduction`/`victim_alone` counts measured by actually running
`fixtures/od-fixture` 20 times each way via plain Maven inside
`maven:3.9-eclipse-temurin-8` on 2026-10-09
(`eval/tools/run_real_reps.sh`), not hand-picked. The raw run backing each
is at `eval/benchmark/logs/<case_id>.json`, and the full numbers are in
`docs/evidence-m3.md`. What's still illustrative even in these files:
`polluter_write_location`/`victim_read_location`'s `bytecode_offset` values
(no real static-evidence extractor exists yet -- Member 1's component) and
`source_integrity` (no real integrity checker exists yet -- Member 2's
component).

**SYNTHETIC** — entirely hand-written, `com.example.*` names, not tied to
any real case in this repo. Needed because od-fixture's F1-F3 cases are
deliberately deterministic (confirmed by the real runs above: always
20/20 or 0/20, never an in-between rate), so some decision-table rows
have no naturally-occurring example in this fixture yet.

Schema v2 (ADR-010, W19, 2026-11-18): every file here was regenerated for
the new shape (`matched`/`other`/`infra` tallies, `candidate_reasons`,
`resource_edges`, `assurance`). The decision table itself changed: see
[[03-Design/decisions/ADR-010-verdict-contract-v2]] for the full table.
`example_no_resource_evidence.json`'s outcome changed from `UNRESOLVED` to
`CANDIDATE` (Q1, option A) — its old 18/20 count is also corrected to 19/20,
since 18/20's Wilson lower bound (0.699) is actually just below the 0.70
threshold, which would have triggered `BELOW_REPLAY_THRESHOLD` too and
muddied what the example is meant to isolate.

| File | Decision table row | Kind |
| --- | --- | --- |
| `example_f1_verified.json` | reproduces strongly, resource edge exists -> VERIFIED | REAL (F1, single polluter) |
| `example_f3_verified.json` | same row, two-polluter edge case | REAL (F3, both polluters required) |
| `example_candidate.json` | reproduces weakly (lower bound < 0.70) -> CANDIDATE [BELOW_REPLAY_THRESHOLD] | SYNTHETIC |
| `example_victim_fails_alone.json` | victim fails alone, matching the reference -> UNRESOLVED(VICTIM_FAILS_ALONE) | REAL (N1, deterministic 20/20) |
| `example_victim_fails_alone_intermittent.json` | same row, intermittent alone-failure | REAL (N2, 12/20 -- genuinely measured, not round) |
| `example_victim_fails_alone_differently.json` | victim fails alone with a DIFFERENT signature -> UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY) | SYNTHETIC — ADR-010's FT003 fix; see the real fixture case N4 for the integrated regression |
| `example_not_reproduced.json` | no reference failure ever established -> UNRESOLVED(NOT_REPRODUCED) | SYNTHETIC |
| `example_signature_mismatch.json` | reference established during search, but the candidate sequence re-verifies with a different signature -> UNRESOLVED(SIGNATURE_MISMATCH) | SYNTHETIC |
| `example_no_resource_evidence.json` | reproduces strongly, no resource edge -> CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE] | SYNTHETIC |
| `example_source_integrity_failed.json` | source-integrity check failed -> UNRESOLVED(SOURCE_INTEGRITY_FAILED) | MIXED -- real F1 stats, hypothetical integrity failure |

`eval/tests/test_examples.py` validates every file here against
`eval/schema/report.schema.json` and cross-checks that running
`eval.outcome.decide()` on the same counts reproduces the same outcome --
for the REAL files, those counts are also cross-checked against the real
log files in `eval/benchmark/logs/`.
