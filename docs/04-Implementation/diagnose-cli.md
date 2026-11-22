# Diagnose command — `runner/cli.py` (Member 2, W9)

*Status (2026-11-20): built; verdict contract v2 (ADR-010, W19). The committed reports in `eval/reports/`
give F1, F2, F3, F4 `VERIFIED (sequence)`, N1 `UNRESOLVED(VICTIM_FAILS_ALONE)`, N4
`UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)`. F3 has two polluters; each is removed in turn, 20 runs each,
and both come back `NEEDED` (W20, ADR-011; `CANDIDATE` before W20). Real N4 and F1 runs under the default `class-grouped`
lifecycle on 2026-11-20: see [[evidence-m2]]. CI on JDK 8: see [[evidence-m2]]. (Until 2026-11-20 this
line still said F3 `VERIFIED`; flagged by M3, PR #115.)
Four-point ownership note per [[04-Implementation/README]]. Design:
[[03-Design/decisions/ADR-005-w9-diagnose-cli]].*

## 1. What it does and why it is there

```
py -m runner diagnose --project fixtures/od-fixture --victim odfixture.ConfigVictimTest#expectsDefaultMode
```

One command from a failing test to a schema-validated report. It joins the three members' parts
in-process and decides nothing itself:

1. checks the options (`--victim` is `Class#method`, `--project` has `pom.xml`);
2. `runner.diagnose.diagnose()` (M2) — every JVM run, recorded;
3. only for `POLLUTER_FOUND`: `evidence.extract` (M1) — `analyse_pair` per polluter (starts at
   depth 2 and deepens on its own when nothing is found, ADR-006), then `report_fields`;
4. `eval.report.assemble_report()` (M3) — `decide()` and schema validation;
5. writes `<record>.report.json` next to the execution record and prints a summary.

| Exit | Meaning |
| --- | --- |
| 0 | report written (any outcome, including `UNRESOLVED`) |
| 2 | input wrong (`--victim` not Java `Class#method`, no `pom.xml`, `--n` < 1, records folder inside the project or a file, victim not a test of the project) |
| 1 | a tool failed (Maven, `java`/`javac`/`mvn` missing, test discovery timed out, the extractor, javap) |
| 3 | diagnosis ran but `eval.report` cannot build a report for its status (since W19 no current status does: `INCONSISTENT` and `NOT_REPRODUCED` both get reports) |

## 2. Why it is built this way

- **A module, not an installed command** (ADR-005): an installable `flaketrace` command needs the
  packages renamed to `flaketrace.*` (all members' imports) and the Java harness shipped as package
  data; deferred to a later iteration. `main(argv) -> int` is ready for that one-line entry point.
- **In-process calls**, not M1's command line: one Python program, no JSON parsing or exit-code
  mapping between processes; the contract lists both as supported.
- **Catches M3's `UnhandledStatus`** instead of listing supported statuses itself, so when M3
  supports `NOT_REPRODUCED` reports the command produces them unchanged.
- **Minimisation in the summary** (W10): when `ddmin` found the polluters, one line says how many
  earlier tests were shrunk to how many polluters in how many runs, and that the set was "reduced
  by single-trial delta debugging; not deletion-verified" (W16, claims ledger G2). The report has no
  field for it.
- **Claim wording** (W16, 2026-11-14): a `VERIFIED` headline reads `VERIFIED (sequence)` (ADR-010
  Q3); a shown resource gets the line "static overlap: a possible mechanism, not confirmed as the
  cause"; the alone count is labelled "alone (same failure)", because it counts only failures that
  match the reference signature (claims ledger G1, FT003). Since 2026-11-20 the line adds
  "other failure: X/N", so a victim that fails alone differently (N4) no longer looks like one
  that passes alone (F1) — found by M1 in the W19 check (PR #114), raised by M3.
- **Several polluters** (W10): evidence per polluter, combined by `combine_fields`: the first
  polluter's edge is shown, the others named in `limitations` as "not the headline resource; it is
  listed in `resource_edges`" (every polluter's edges are there since schema v2; until 2026-11-20 this
  line wrongly said "not shown in this report"), and only if **every** polluter has an
  edge — otherwise no resource is shown (`CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]` since
  ADR-010 Q1). Since W21 (PR #105) `combine_fields` also lists every polluter's edges in
  `resource_edges`, each with its depth, so the report shows all of them.
- **Report next to its record**: each report sits with the raw runs that back it, and the record
  path in it is relative when `--records` is (the default).

## 3. What breaks

- Must run from the repository root, or with it on `PYTHONPATH` (`No module named runner` otherwise).
- On Windows the record path in the report uses `\`; it is relative, but not OS-neutral.
- One victim per run. With several polluters the report shows one resource; the others are only
  named in `limitations` until the schema allows one edge per polluter.
- Unexpected exceptions are deliberately not caught: Python prints the traceback (exit 1).
- Inherits ADR-003/004 limits (JUnit 4, alphabetical discovered order, single polluters).

## 4. How to modify it

- New option: add it in `main()`, pass it through `run_diagnose`, add a fast test in
  `runner/tests/test_cli.py` (`TestInputErrors` style).
- New known error: give it its own exception class (like `DiagnoseInputError`, `ToolError`), catch
  it **only** around the call that raises it, map it to 1 or 2, and add a `TestToolErrors.check(...)`
  test. Never catch a broad `ValueError`/`RuntimeError`: internal bugs would look like user errors.
- Tests: `py -m unittest -v runner.tests.test_cli` — 15 fast tests (no JVM) and 5 real runs on the
  fixture (skipped without JDK/Maven unless `FLAKETRACE_REQUIRE_JVM` is set).

## ADR-008 additions (2026-10-11)

- `--order <file>` (the real failing order), `--shuffles N` (default 31), `--seed S` (default 0),
  `--lifecycle class-grouped|per-method` (default `class-grouped` since M1's control run matched Surefire on 2026-11-20, PR #108; W22, ADR-012),
  `--workspace copy|in-place` (default `copy`: everything runs in a temporary copy that is deleted
  afterwards, inside one `with workspace(...)` block around `diagnose()` and the evidence
  extraction, which needs the copy's compiled classes; W22, ADR-012 §4). A bad
  `--order` file, a duplicate, a missing victim or a test the project does not have → exit 2.
- When the starting order never fails, the diagnosis tries distinct class-first shuffled orders; the
  summary names the reproducing seed (`orders: reproduced in shuffled order (seed 1) after 2 …`).
- `NOT_REPRODUCED` is now a report (exit 0) with `failure_signature: null`, `order_exploration`, and the
  summary lines `orders:` (which order — "given" only with `--order`, else "discovered") and `bound:`
  (Wilson upper bound, "not proof of reliability").

## W24 additions (2026-11-20)

- `--budget-invocations N` and `--budget-seconds S` (ADR-014, Interface 6). A limit below the start minimum (`3n` + the tests up to the victim + 2) exits 2 and names the minimum.
- Every summary has a `budget:` line: invocations spent (of the limit), the reserve, candidates tried, and the phase it stopped in.
- `BUDGET_EXHAUSTED` is a report since M3's W24 half (PR #135): `UNRESOLVED (BUDGET_EXHAUSTED)`, exit 0. Its
  `reproduced:` line says "no sequence verified (the starting order failed k of r run(s) before the budget ran
  out)", so the starting order's runs are not read as a verified reproduction (2026-11-20 follow-up).
- When every kept test is `NEEDED`, the `deletion:` line says "each kept test confirmed needed" (M1's W20
  verification, PR #137).

## W25 additions (2026-11-20)

- `--policy original|ranked|random` and `--scope module|package` (ADR-014, Interface 7). `--scope package` with `--order` exits 2.
- A `search:` line: `original order`, `random order (seed S)`, or `ranked by static evidence at depth 2 (k of N candidates with evidence)`, with the fallback note on its own line. A rank orders the search; it never says what caused the failure (claims ledger G3).

## W23 additions (2026-11-21)

- `--bundle <folder>` writes an evidence bundle (Interface 8) after the report; the summary names it.
- `replay <bundle> --project <checkout> [--bundle] [--records] [--workspace]` re-checks it (R1–R7) and prints the comparison. Exit 0 same verdict, 4 different, 2 input (not a bundle, a changed file, nothing to replay, a test missing from the checkout), 1 tool failed.
- **What breaks:** a bundle refuses to be written if your home folder or user name would remain in it — a path printed somewhere new (e.g. a tool's banner) needs adding to `paths` in `runner/cli.py` (diagnose) and
  `runner/replay.py` (replay). User names shorter than 3 characters are not matched as path parts (they
  would also hit JSON escapes such as `\n`).
- `replay` always runs on a copy (Interface 8 R2), takes `n` and the lifecycle from the checksummed record
  (a manifest that disagrees is refused), and never writes inside the original bundle (R7).

## W35 additions (2026-11-22)

- `--search order|pairs` (ADR-016 revised, Interface 9). `--search pairs` with `--order` exits 2: an order file can
  hold a dataset's polluters, which pair mode must never see.
- Pair mode's summary has a `pairs:` line: "found in a constructed pair after k of N pairs; pair mode does not run
  the project's own orders", or "no pair adopted (k of N pairs tried; m failed once and passed when re-run; c crashed
  or timed out; stopped by the budget)". Without an adopted pair, `reproduced:` says "no sequence verified (no pair
  adopted)", and there are no `orders:`/`bound:` lines (they describe orders pair mode never ran). The `budget:` line
  says "pairs tried".
- Order mode's `NOT_REPRODUCED` summary ends its order lines with `next:`, naming `--search pairs` (and
  `--scope package` when that was the scope) with an upper-bound estimate: (candidates + 2n) JVM launches at this
  run's mean seconds per alone run (a one-test JVM, the closest to a pair), rounded up to whole minutes. After
  `--order` it says "re-run without --order and with --search pairs", with no count (the file's tests are not pair
  mode's candidates).
- `summary()` takes the `DiagnosisRuns` as `diagnosis` (not `runs`: that name is a local inside it).
- In pair mode the budget minimum is the reserve plus one pair and its re-run (`reserve + 4`), so a failing pair can
  always be adopted.

## W23 reproduction gaps (2026-11-22)

M1's independent reproduction (PR #159) needed commands `replay.md` did not give. Fixed in `runner/bundle.py` and
`runner/replay.py`:

- `replay.md` writes `python -m eval.bundle verify "<folder>/<name>"` and `python -m runner replay "<folder>/<name>"
  --project <subject>` with real values: the output folder as given when relative, else `eval/bundles` (an absolute
  one would be a personal path); `--project fixtures/od-fixture` for a fixture, else `"CHECKOUT"` or
  `"CHECKOUT/<module>"` with "CHECKOUT is your clone of <repository> at commit <sha>". Step 1 says to use any
  FlakeTrace commit that has `eval/bundle.py`: the bundle's own commit can be older than the verifier.
- The replay's `OS:` row treats `Windows-10-<build>` and `Windows-11-<build>` as the same (Python 3.11 names Windows 11
  "Windows-10"); a different build or system is still `DIFFERENT`.
- Committed bundles keep their old `replay.md` (their checksums protect them); M3's README covers them.
