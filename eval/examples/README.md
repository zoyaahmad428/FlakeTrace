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
(CANDIDATE, NOT_REPRODUCED, SIGNATURE_MISMATCH, NO_SUPPORTED_RESOURCE_EVIDENCE)
have no naturally-occurring example in this fixture yet.

| File | Decision table row | Kind |
| --- | --- | --- |
| `example_f1_verified.json` | reproduces strongly, resource edge exists -> VERIFIED | REAL (F1, single polluter) |
| `example_f3_verified.json` | same row, two-polluter edge case | REAL (F3, both polluters required) |
| `example_candidate.json` | reproduces weakly (lower bound < 0.70), resource edge exists -> CANDIDATE | SYNTHETIC |
| `example_victim_fails_alone.json` | victim fails alone -> UNRESOLVED(VICTIM_FAILS_ALONE) | REAL (N1, deterministic 20/20) |
| `example_victim_fails_alone_intermittent.json` | same row, intermittent alone-failure | REAL (N2, 12/20 -- genuinely measured, not round) |
| `example_not_reproduced.json` | sequence never fails at all -> UNRESOLVED(NOT_REPRODUCED) | SYNTHETIC |
| `example_signature_mismatch.json` | sequence fails, but never with the reference signature -> UNRESOLVED(SIGNATURE_MISMATCH) | SYNTHETIC |
| `example_no_resource_evidence.json` | reproduces strongly, no resource edge -> UNRESOLVED(NO_SUPPORTED_RESOURCE_EVIDENCE) | SYNTHETIC |
| `example_source_integrity_failed.json` | source-integrity check failed -> UNRESOLVED(SOURCE_INTEGRITY_FAILED) | MIXED -- real F1 stats, hypothetical integrity failure |

`eval/tests/test_examples.py` validates every file here against
`eval/schema/report.schema.json` and cross-checks that running
`eval.outcome.decide()` on the same counts reproduces the same outcome --
for the REAL files, those counts are also cross-checked against the real
log files in `eval/benchmark/logs/`.
