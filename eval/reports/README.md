# Real, pipeline-produced diagnosis reports (W9)

Unlike `eval/examples/` (hand-written illustrative examples, explicitly labelled as not
results), everything in this folder was **genuinely produced by the real pipeline**:
`runner.diagnose.diagnose()` (Member 2, real Maven/JVM runs) +
`evidence.extract.analyse_test()` / `find_edges()` / `report_fields()` (Member 1, real `javap`
bytecode reads and the real pair-mode correlation) +
`eval.report.assemble_report()` (Member 3, Wilson intervals + the decision table) +
`eval.schema_validator.validate_report()` (passed, not just asserted).

Reproduce with: `py eval/tools/run_w9_integration.py` (takes a few minutes; needs Maven + a
JDK on `PATH`, same requirements as `runner/`).

| File | Victim | Real outcome |
| --- | --- | --- |
| `f1.json` | `odfixture.ConfigVictimTest#expectsDefaultMode` | `VERIFIED` (20/20 reproduced, 0/20 alone, real resource edge) |
| `f2.json` | `odfixture.FeatureVictimTest#expectsTurboDisabled` | `VERIFIED` (20/20 reproduced, 0/20 alone, real resource edge via a helper call, `FeatureFlags.isTurboEnabled`) |
| `n1.json` | `odfixture.NegativeAloneFailTest#alwaysFails` | `UNRESOLVED(VICTIM_FAILS_ALONE)` (20/20 alone-failures) |

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

F3 (needs multi-polluter search, not implemented by Member 2 yet — `W10`), and N2 (handled by
`runner.diagnose` as `NOT_REPRODUCED` on this run, a `DiagnosisRuns.status`
`eval.report.assemble_report()` deliberately does not handle yet — see its module docstring).
Neither is invented or worked around; both are open items tracked in `docs/evidence-m3.md`.

F2 **is** here now: it needed `--depth 2` (the contract default, already implemented by
Member 1), not a depth Member 1 hadn't built. This script was wrongly calling `analyse_test`
with `depth=1`, which cannot see a resource accessed through a one-level helper call (F2's
victim reads the property inside `FeatureFlags.isTurboEnabled()`, not in its own test method)
— also flagged by Member 2, fixed together with the correlation-logic duplication above.
