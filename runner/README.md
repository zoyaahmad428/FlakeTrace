# runner/ — bounded search and verification (Member 2)

**Owner:** Member 2 · **State:** not started (2026-10-09)

Implements the `OrderRunner` interface in [`eval/baseline.py`](../eval/baseline.py) and
everything built on it. Contract: [docs/contracts/interfaces.md](../docs/contracts/interfaces.md).

## Planned components, in build order

| # | Component | Produces (report-schema fields) | Needed for Mid demo |
| --- | --- | --- | --- |
| 1 | Ordered single-JVM runner for JUnit 4 | per-test outcomes, `failure_signature` | Yes |
| 2 | Victim-alone check, repeated `n` times | `victim_alone` raw counts | Yes |
| 3 | Polluter search over preceding tests | `polluters`, `original_failing_order` | Yes |
| 4 | Deletion minimisation (handles F3's two-polluter case) | `reduced_sequence` | Yes (F1/F2); F3 stretch |
| 5 | Repeated-run verification of the reduced sequence | `reproduction` raw counts | Yes |
| 6 | Source-integrity check (hash target source before/after) | `source_integrity` | Yes |
| 7 | Execution record (JDK, order, seed, timestamps) | `execution_record_reference` | Yes |
| 8 | CLI entry point | — | Yes |

Test against `fixtures/od-fixture` (F1, F2, F3, N1, N2) — the expected outcomes are in
`fixtures/od-fixture/ground_truth.json`, written before any run.
