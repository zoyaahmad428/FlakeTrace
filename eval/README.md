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

Run everything: `python3 -m unittest discover -s eval/tests -v`

## Random-order baseline status: NOT YET RUN ON REAL TESTS

`baseline.py` defines the `OrderRunner` interface Member 2's real Docker
builder / single-JVM order runner must implement (`run_ordered(order) ->
{test: outcome}`), and `run_random_order_baseline()` is built entirely
against that interface. **No implementation of `OrderRunner` exists in this
repo yet** — Member 2's runner is a separate, not-yet-built component.

Consequently this baseline:

- Has been unit-tested with `eval/tests/fake_runner.py`'s `FakeOrderRunner`
  — a scriptable fake that never launches a JVM or runs real Maven/JUnit.
  That fake lives **only** under `eval/tests/`; `baseline.py` does not
  import it, and no real CLI should ever import it either.
- Has **never been executed against `fixtures/od-fixture` or any other real
  project.** Any number you might expect to see here (e.g. "it took N
  random shuffles to reproduce F1") does not exist yet and must not be
  invented. Once Member 2's order runner is integrated, this baseline can
  be run for real and its results feed into the yield report below.

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
