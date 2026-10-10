# Real, pipeline-produced diagnosis reports (W9)

Unlike `eval/examples/` (hand-written illustrative examples, explicitly labelled as not
results), everything in this folder was **genuinely produced by the real pipeline**:
`runner.diagnose.diagnose()` (Member 2, real Maven/JVM runs) +
`evidence.extract.analyse_pair()` / `report_fields()` (Member 1, real `javap` bytecode reads
and the real pair-mode correlation, auto-deepening 1→5 only when needed, ADR-006) +
`eval.report.assemble_report()` (Member 3, Wilson intervals + the decision table) +
`eval.schema_validator.validate_report()` (passed, not just asserted).

Reproduce with: `py eval/tools/run_w9_integration.py` (takes a few minutes; needs Maven + a
JDK on `PATH`, same requirements as `runner/`).

| File | Victim | Real outcome |
| --- | --- | --- |
| `f1.json` | `odfixture.ConfigVictimTest#expectsDefaultMode` | `VERIFIED` (20/20 reproduced, 0/20 alone, real resource edge) |
| `f2.json` | `odfixture.FeatureVictimTest#expectsTurboDisabled` | `VERIFIED` (20/20 reproduced, 0/20 alone, real resource edge via a helper call, `FeatureFlags.isTurboEnabled`) |
| `n1.json` | `odfixture.NegativeAloneFailTest#alwaysFails` | `UNRESOLVED(VICTIM_FAILS_ALONE)` (20/20 alone-failures) |
| `n2.json` | `odfixture.NegativeFlakyTest#sometimesFails` | `UNRESOLVED(VICTIM_FAILS_ALONE)` (intermittent by design — 9/20 alone-successes in the committed run; the exact count varies run to run, as N2's whole point requires) |

Each report's `execution_record_reference` points at a raw per-run JSONL execution record
(`runner.recording.RecordingRunner`) under a local `flaketrace-records/` folder — one real JVM
invocation's full result per line, not summarised. That folder is **not committed**:
`.gitignore` already excludes `flaketrace-records/` (Member 2's convention, since every run
produces new timestamped files). Re-run `run_w9_integration.py` to regenerate it locally.

## Known limitation

`execution_record_reference` is an **absolute, machine-specific path** — the path in the
committed JSON won't resolve on another machine. This comes from
`eval/tools/run_w9_integration.py`'s own `RECORD_DIR` (built from `Path(__file__).resolve()`),
not from `runner.diagnose.diagnose()`: that function uses whatever `record_dir` it is given
as-is for the record path it returns (`runner/diagnose.py:103`); it only calls
`Path(record_dir).resolve()` separately, for the record-vs-project containment safety check
(`runner/diagnose.py:93`), not for the path written into `execution_record`. (An earlier
version of this note wrongly attributed the resolving to `diagnose()` itself — corrected
after Member 2 pointed it out; see `docs/evidence-m3.md`.) Worth raising as a joint question
if a portable reference is wanted later.

## What's NOT here yet

F3 only — it needs multi-polluter search, not implemented by Member 2 yet (`W10`). That is an
open item tracked in `docs/evidence-m3.md`, not invented or worked around.

F2 and N2 **are** here now, both added after being blocked:

- F2 needed `--depth 2` (the contract default, already implemented by Member 1), not a depth
  Member 1 hadn't built. This script was wrongly calling `analyse_test` with `depth=1`, which
  cannot see a resource accessed through a one-level helper call (F2's victim reads the
  property inside `FeatureFlags.isTurboEnabled()`, not in its own test method) — flagged by
  Member 2, fixed together with the correlation-logic duplication above.
- N2 used to report `NOT_REPRODUCED` on some machines (a `DiagnosisRuns.status`
  `eval.report.assemble_report()` deliberately does not handle — see its module docstring),
  because its old flakiness mechanism (`System.nanoTime()`'s lowest bit) could be
  deterministically even on some hardware. After Member 3 fixed that mechanism and Member 2
  confirmed it now reliably reports `VICTIM_FAILS_ALONE` on every platform tested, N2 needed
  no new code here — `assemble_report` already handles that status.

## Depth: `analyse_pair()`, not separate `analyse_test()`+`find_edges()` calls

`eval/tools/run_w9_integration.py` now calls Member 1's `evidence.extract.analyse_pair()`
(ADR-006, PR #34) instead of analysing the polluter and victim separately and combining them
with `find_edges()`. `analyse_pair()` starts at the contract default (depth 2) and deepens one
level at a time, but only when the walk actually hit `DEPTH_LIMIT` and found no edge — it stops
at the shallowest depth that has one. F1 and F2 both still resolve at depth 2 (confirmed: the
regenerated reports are byte-identical to before except for the execution-record timestamp),
so this change costs nothing on the fixture; it is what makes a real project whose evidence
sits deeper (fastjson's two cases, at depth 4 and 5 — `docs/evidence-m1.md`) explainable
without every pair paying that cost. `eval/report.py` itself needed no change: it already took
`report_fields(pair)`'s output as an opaque `resource_fields` argument, independent of how the
caller produced `pair`.
