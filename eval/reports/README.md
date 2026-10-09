# Real, pipeline-produced diagnosis reports (W9)

Unlike `eval/examples/` (hand-written illustrative examples, explicitly labelled as not
results), everything in this folder was **genuinely produced by the real pipeline**:
`runner.diagnose.diagnose()` (Member 2, real Maven/JVM runs) +
`evidence.extract.analyse_test()` (Member 1, real `javap` bytecode reads) +
`eval.report.assemble_report()` (Member 3, Wilson intervals + the decision table) +
`eval.schema_validator.validate_report()` (passed, not just asserted).

Reproduce with: `py eval/tools/run_w9_integration.py` (takes a few minutes; needs Maven + a
JDK on `PATH`, same requirements as `runner/`).

| File | Victim | Real outcome |
| --- | --- | --- |
| `f1.json` | `odfixture.ConfigVictimTest#expectsDefaultMode` | `VERIFIED` (20/20 reproduced, 0/20 alone, real resource edge) |
| `n1.json` | `odfixture.NegativeAloneFailTest#alwaysFails` | `UNRESOLVED(VICTIM_FAILS_ALONE)` (20/20 alone-failures) |

Each report's `execution_record_reference` points at a raw per-run JSONL execution record
(`runner.recording.RecordingRunner`) under a local `flaketrace-records/` folder — one real JVM
invocation's full result per line, not summarised. That folder is **not committed**:
`.gitignore` already excludes `flaketrace-records/` (Member 2's convention, since every run
produces new timestamped files). Re-run `run_w9_integration.py` to regenerate it locally.

## Known limitation

`execution_record_reference` is an **absolute, machine-specific path**
(`runner.diagnose.diagnose()` calls `Path(record_dir).resolve()` internally), not a
repo-relative one. The committed JSON reflects exactly what the real run produced, uncleaned
— the path in it won't resolve on another machine. This is Member 2's component's behaviour,
not edited here; worth raising as a joint question if a portable reference is wanted later.

## What's NOT here yet

F2 (needs resource-evidence depth 2, not implemented by Member 1 yet), F3 (needs multi-polluter
search, not implemented by Member 2 yet — `W10`), and N2 (handled by `runner.diagnose` as
`NOT_REPRODUCED` on this run, a `DiagnosisRuns.status` `eval.report.assemble_report()`
deliberately does not handle yet — see its module docstring). None of these are invented or
worked around; they are open items tracked in `docs/evidence-m3.md`.
