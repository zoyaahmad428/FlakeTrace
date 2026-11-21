# eval — Member 3 (Evaluation & Repair)

Dependency-free Python unless noted. `pip install -r eval/requirements.txt`
for the schema validator's `jsonschema` dependency.

| Module | Purpose |
| --- | --- |
| `stats.py` | Wilson score confidence intervals; `compare_sequence_to_isolation`. |
| `baseline.py` | `RunTally`, `classify()` — the four-way PASS/MATCH/OTHER/INFRA classification every tally in the report is built from (ADR-010/W18). Also the random-order baseline — **see status below.** |
| `schema/report.schema.json` | The diagnosis report contract, schema v2 (ADR-010/ADR-011, W19) — see `docs/contracts/report-schema.md`. |
| `outcome.py` | `decide()` — the 13-row VERIFIED/CANDIDATE/UNRESOLVED decision table (ADR-010), including the deletion-evidence claim S3 (ADR-011). |
| `report.py` | `assemble_report()` — joins Member 2's raw tallies and Member 1's resource-edge data into one schema-v2-validated report; decides nothing itself, calls `outcome.decide()`. |
| `schema_validator.py` | Validates a report dict/file against the schema. |
| `bundle.py` | `create_bundle()`/`verify_bundle()` — the ADR-013 evidence bundle (W23): a report travels with its record, every path relative or redacted, and `verify_bundle` independently recounts every tally from the record alone and re-decides, never trusting the runner's own numbers. `python -m eval.bundle create\|verify`. |
| `bundles/` | Real, committed bundles (ADR-013 §4) — see `eval/bundles/README.md`. Replaces `eval/reports/*.json`'s absolute-path limitation, one case at a time. |
| `examples/` | Hand-written example reports, one per decision-table row. Not results. |
| `benchmark/manifest.json` | Frozen case list (F1-F3, N1-N2, plus one real POC case with a pinned SHA) — see status below. |
| `benchmark/yield_report.py` | Generates the attempted→built→victim-passes-alone→reproduced→excluded funnel from `benchmark/logs/`, never from hand-typed numbers. |
| `tests/` | Unit tests for everything above. |

## Schema v2 (ADR-010/ADR-011, W19) — what changed from the Mid build

Every run tally (`reproduction`, `victim_alone`) is a `RunTally`: `{n, passed, matched, other,
infra}`. `passed` is a clean pass; the other three come from `baseline.classify()` applied to
each run against the reference failure signature — `matched` (same exception as the
reference), `other` (a real failure, but a *different* exception — this is what tells a
victim that fails alone with a different signature apart from one that genuinely never fails
alone, ADR-010's FT003 fix), `infra` (crashed, timed out, or never executed — a tooling
problem, not evidence either way). The old schema-v1 field `successes` is `matched` now; a
report built for the Mid (tag `mid-eval-v1`) still uses the old name and is read separately
(`mid-eval-report/scripts/json_to_tex.py --reports <dir>` handles both).

`decide()`'s 13-row table checks four claims before `VERIFIED`: S1 (`sequence` reproduces,
Wilson lower bound ≥ 0.70), S2 (`alone` tally fully clean), S3 (deletion evidence — see
below), R1 (a static resource edge exists). Falling short of one or more without failing
outright gives `CANDIDATE`, with `candidate_reasons` naming which (e.g.
`NO_SUPPORTED_RESOURCE_EVIDENCE`, `DELETION_EVIDENCE_INCOMPLETE`,
`BELOW_REPLAY_THRESHOLD`). The report also carries `resource_edges` (every edge Member 1's
extractor found, each with its depth — W21) and an `assurance` block summarising the three
pillars (`sequence.reproduces`/`passes_alone`/`deletion`, `resource.level`/`mechanism`) in one
place for a reader who wants the summary without re-deriving it from the raw fields.

**Deletion evidence (S3, ADR-011 §2, A1 fail-safe fix 2026-11-19/20):** a sequence with exactly
one kept polluter gets S3 for free — the alone run, already clean, already proves "removing
that one polluter makes the victim pass". Two or more kept polluters have no such free check
(W20 will build the real repeated-removal one), so `deletion_status` is `DELETION_INCOMPLETE`
and the outcome is `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]`, never `VERIFIED` — fixture F3
(two required polluters) is the real example: its ground truth stays `VERIFIED` as the W20
target, but the tool honestly reports `CANDIDATE` today. `deletion_status=None`/not-yet-checked
never satisfies S3 either, by construction (`eval/outcome.py`'s own guard) — an unestablished
claim must never count as an established one.

**Execution budget (ADR-014, Interface 6, W24):** `DiagnosisRuns.status` can also be
`BUDGET_EXHAUSTED` -- the search ran out of budget before finding any polluter --
which `assemble_report()` maps to `UNRESOLVED(BUDGET_EXHAUSTED)`. A polluter can also be found
but the budget still run out before verification (deletion checks, the final sequence check)
finished; that reaches `CANDIDATE [BUDGET_EXHAUSTED]` instead, via `DecisionInput.
verification_budget_exhausted` -- never `VERIFIED`, even if S1/S3/R1 would otherwise all hold.
The report gains an optional `budget` field (Member 2's `BudgetAccount`, reshaped with
`candidates` as `{total, tried}`) whenever the diagnosis tracked one; omitted entirely for a
diagnosis built before W24, same as `order_exploration`. Without a budget limit, nothing
changes for F1-F4/N1-N4: same verdicts, `budget.exhausted` reads `false`.

Run everything (install the dependency first, or you'll hit
`ModuleNotFoundError: No module named 'jsonschema'`):

```
pip install -r eval/requirements.txt
python3 -m unittest discover -s eval/tests -v
```

## Random-order baseline status: run for real against the real runner (2026-10-11)

`baseline.py` defines the `OrderRunner` interface; `runner.order_runner.OrderRunner`
(Member 2, real since PR #10) satisfies it. Unit-tested throughout with
`eval/tests/fake_runner.py`'s `FakeOrderRunner` — a scriptable fake that never
launches a JVM, lives **only** under `eval/tests/`, and `baseline.py` does not
import it. Shuffling groups by class first, then methods within a class (never
interleaving two classes — JUnitCore/Surefire run a suite class by class, so a
plain whole-pool shuffle could propose an order nothing can actually execute).

**Real runs, F1-F4, 4 independent trials each** (`eval/tools/run_baseline_real.py`,
native Windows/JDK24, candidate pool = victim + that case's polluter(s) + the
fixture's 4 benign noise tests (`odfixture.MathUtilTest`/`StringUtilTest`,
`max_runs=50`, `base_seed` 0/100/200/300):

| Case | Pool size | Runs to find (seeds 0/100/200/300) |
| --- | --- | --- |
| F1 | 6 (1 polluter) | 1, 1, 3, 2 |
| F2 | 6 (1 polluter) | 1, 1, 3, 2 |
| F3 | 7 (2 polluters, both required) | 1, 2, 3, 1 |
| F4 | 6 (1 polluter, order-needs-reshuffle) | 1, 1, 3, 2 |

Found the bug in every trial on every case. Compare to Member 2's real targeted
search: F1/F2/F4 found their polluter in 1 search run each; F3 needed the
one-by-one search (12 runs) plus `ddmin` minimisation (`docs/evidence-m2.md`).
Both are cheap on this small fixture by design — F4 is the more informative
comparison: FlakeTrace's own *discovered* order can never reproduce F4 at all
(the polluter class sorts alphabetically after the victim's), which is exactly
why ADR-008 added a shuffle-search step; a plain random shuffle finds it
immediately because it doesn't depend on discovery order to begin with. The
real value of this comparison method on a *targeted-search-favours* case will
show on a larger real-world project (the idoft cases in
`benchmark/manifest.json`), where a targeted search should scale far better
than random shuffling.

Note: an earlier entry (2026-10-10, `docs/evidence-m3.md`) described the F1
candidate pool as "7 tests ... 5 noise tests". Recounting against
`fixtures/od-fixture/ground_truth.json`'s `benign_noise_tests` (2 classes, 2
methods each = 4 noise tests) gives 6, not 7 — the earlier prose miscounted;
the actual candidate set (and this run's F1 result, byte-for-byte identical)
did not change. Flagged here rather than silently corrected in the old entry.

Not yet done: N1/N2 (no polluter exists to search for, so the random-order
comparison does not apply) and any idoft case (still metadata-only, not
cloned/built).

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
  **This 12/20 is `benchmark/logs/N2.json`'s own one-time, frozen
  2026-10-09 measurement (`isolation_successes`/`isolation_n`), not the
  live, schema-v2 `eval/reports/n2.json`** — the latter is regenerated by
  `eval/tools/run_w9_integration.py` and, because N2's mechanism is
  `java.util.Random().nextBoolean()`, genuinely gives a different rate
  on every real rerun (observed 9/20 through 12/20 across Iteration 2 —
  see `docs/evidence-m3.md`'s 2026-11-19/20 entries). Do not confuse the
  two files' numbers.
- `POC-DEMO-1` and all 5 `IDOFT-*` cases → still honestly `not_yet_run`;
  nothing has run them.

The random-order **baseline** above is a different measurement (how many
random full-suite shuffles it takes to stumble onto the bug) and remains
not-yet-run — these targeted repeated-sequence numbers don't substitute
for it.
