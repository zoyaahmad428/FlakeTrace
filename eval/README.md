# eval — Member 3 (Evaluation & Repair)

Dependency-free Python unless noted. `pip install -r eval/requirements.txt`
for the schema validator's `jsonschema` dependency.

| Module | Purpose |
| --- | --- |
| `stats.py` | Wilson score confidence intervals; `compare_sequence_to_isolation`. |
| `schema/report.schema.json` | The diagnosis report contract (see `docs/contracts/report-schema.md`). |
| `outcome.py` | `decide()` — the VERIFIED/CANDIDATE/UNRESOLVED decision table. |
| `schema_validator.py` | Validates a report dict/file against the schema. |
| `baseline.py` | Random-order baseline — **see status below.** |
| `examples/` | Hand-written example reports, one per decision-table row. Not results. |
| `benchmark/manifest.json` | Frozen case list (F1-F3, N1-N2, plus one real POC case with a pinned SHA) — see status below. |
| `benchmark/yield_report.py` | Generates the attempted→built→victim-passes-alone→reproduced→excluded funnel from `benchmark/logs/`, never from hand-typed numbers. |
| `tests/` | Unit tests for everything above. |

Run everything (install the dependency first, or you'll hit
`ModuleNotFoundError: No module named 'jsonschema'`):

```
pip install -r eval/requirements.txt
python3 -m unittest discover -s eval/tests -v
```

## Random-order baseline status: run for real against the real runner (2026-10-10)

`baseline.py` defines the `OrderRunner` interface; `runner.order_runner.OrderRunner`
(Member 2, real since PR #10) satisfies it. Unit-tested throughout with
`eval/tests/fake_runner.py`'s `FakeOrderRunner` — a scriptable fake that never
launches a JVM, lives **only** under `eval/tests/`, and `baseline.py` does not
import it.

**Real run, F1, 4 independent trials** (`runner.order_runner.OrderRunner`, native
Windows/JDK24, candidate pool of 7 tests — the victim, its polluter, and 5 noise
tests, `max_runs=50`): found the bug in **1, 1, 3, and 2** random shuffles
respectively (average 1.75 — close to the ~2 expected for a pool this size, where
each shuffle has roughly even odds of placing the polluter before the victim).
Compare to Member 2's real targeted one-by-one search on the same case: 1 search
run (`docs/evidence-m2.md`). Both are cheap on this small fixture by design; the
real value of this comparison method will show once run against a larger
real-world project (the idoft cases in `benchmark/manifest.json`), where a
targeted search should scale far better than random shuffling.

Not yet done: F2/F3/N1/N2 with the real runner, and any idoft case (still
metadata-only, not cloned/built).

## Benchmark yield report status: 5 of 11 cases actually run

`benchmark/manifest.json` lists 11 frozen cases: F1-F3/N1-N2 from
`fixtures/od-fixture`, one recorded POC case (`POC-DEMO-1`, pinned SHA,
can't be attempted — see its `notes`), and 5 real cases pulled from the
published [idoft dataset](https://github.com/TestingResearchIllinois/idoft)
(`IDOFT-*`, metadata only — real pinned SHAs, not cloned/built/run yet).
`benchmark/yield_report.py` reads `benchmark/logs/<case_id>.json` for each
case and computes the funnel from there — it has **no code path that
invents a count**.

As of 2026-10-09, `benchmark/logs/` has 5 real log files — **F1, F2, F3,
N1, N2 were actually run**, 20 times each way, via plain Maven inside
`maven:3.9-eclipse-temurin-8` (`eval/tools/run_real_reps.sh`; full numbers
in `docs/evidence-m3.md`). This is a manual run driven by Member 3 using
plain Maven, not Member 2's automated pipeline (which still doesn't
exist) — the log files say so (`recorded_by`). Running
`python3 eval/benchmark/yield_report.py` today correctly shows:

- F1, F2, F3 → `built: true`, `reproduced: true` (real, deterministic 20/20).
- N1, N2 → `built: true`, `excluded_reason: "VICTIM_FAILS_ALONE"` (N1
  deterministic 20/20 alone-failures; N2 intermittent — a real, newly
  measured 12/20, not the rough 4/6 sample used informally in Phase 1).
- `POC-DEMO-1` and all 5 `IDOFT-*` cases → still honestly `not_yet_run`;
  nothing has run them.

The random-order **baseline** above is a different measurement (how many
random full-suite shuffles it takes to stumble onto the bug) and remains
not-yet-run — these targeted repeated-sequence numbers don't substitute
for it.
