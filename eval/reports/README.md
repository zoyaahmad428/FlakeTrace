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
| `f3.json` | `odfixture.ToggleVictimTest#expectsNotBothFlagsSet` | `VERIFIED` (20/20 reproduced, 0/20 alone; two polluters, both required — `ddmin` minimisation, ADR-007; `flagA` shown, `flagB` named in `limitations`) |
| `f4.json` | `odfixture.AlwaysEarlyVictimTest#expectsLateFlagUnset` | `VERIFIED` (20/20 reproduced, 0/20 alone; the discovered order never reproduces this on its own — found only through a shuffled order, seed 1, ADR-008) |
| `n1.json` | `odfixture.NegativeAloneFailTest#alwaysFails` | `UNRESOLVED(VICTIM_FAILS_ALONE)` (20/20 alone-failures) |
| `n2.json` | `odfixture.NegativeFlakyTest#sometimesFails` | `UNRESOLVED(VICTIM_FAILS_ALONE)` (intermittent by design — 9/20 alone-successes in the committed run; the exact count varies run to run, as N2's whole point requires) |
| `n3.json` | `odfixture.EnvDependentNegativeTest#onlyFailsUnderCI` | `UNRESOLVED(NOT_REPRODUCED)` (0/20 in the discovered order, 0/20 across 31 shuffled orders, 0/20 alone — the externally-caused failure this models genuinely never reproduces under FlakeTrace's control, ADR-008) |

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

Nothing from the OD fixture — all 7 cases (F1-F4, N1-N3) now have a real report. Only the
`idoft` benchmark cases (`eval/benchmark/manifest.json`) remain unrun; they are still
metadata-only (not cloned/built), tracked separately, not in this folder.

F2, F3, F4, N2 and N3 were each added here after being blocked on a real dependency landing:

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
- F3 needed multi-polluter search (W10, `ddmin`, ADR-007, Member 2's PR #35/#38/#40) before a
  single-polluter search could ever find both required polluters together. This script now
  gets its resource fields from `runner.cli.resource_fields()` (not a hand-rolled
  `analyse_pair`/`report_fields` call per polluter) so F3's two-polluter combination (ADR-007's
  `combine_fields`) is exactly what the real `py -m runner diagnose` CLI does, not a
  reimplementation of it.
- F4 and N3 needed ADR-008's order-search step (Member 2's PR #49: `--order`/shuffled orders,
  the alone check always run) before `diagnose()` could either find F4's bug (the discovered
  order alone never reproduces it — only a shuffle does, seed 1) or build a real
  `NOT_REPRODUCED` report for N3 (this module's own `assemble_report` guard against `alone_n
  == 0`, landed the same day, PR #52).

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
