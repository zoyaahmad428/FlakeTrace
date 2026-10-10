# ADR-005 — W9: one command from a failing test to a validated report

**Date:** 2026-10-10 · **Status:** `PROPOSED` — chosen by M2; it proposes the answer to open
question I4 in [[contracts/interfaces]], which needs M1's and M3's agreement · **Owner:** M2 ·
**Work package:** W9 · **Builds on:** [[03-Design/decisions/ADR-004-w7-diagnosis-runs]],
[[03-Design/decisions/ADR-002-evidence-extractor-implementation]]

## Context

All three parts of the pipeline now exist as Python functions, each run for real on the fixture:

| Part | Owner | Function |
| --- | --- | --- |
| Diagnosis runs (reproduce, alone ×n, polluter search, repeat ×n, integrity, record) | M2 | `runner.diagnose.diagnose()` → `DiagnosisRuns` |
| Resource evidence for a polluter→victim pair | M1 | `evidence.extract.analyse_test`, `find_edges`, `report_fields` |
| Outcome decision and schema-validated report | M3 | `eval.report.assemble_report()` |

Only M3's one-off script `eval/tools/run_w9_integration.py` joins them, with each victim hard-coded.
W9 asks for an end-to-end command, F1 → validated JSON report, and open question I4 asks where
the single CLI entry point lives and in which language.

The command's main user is a developer (and, at the Mid evaluation, the live demo) diagnosing
**one failing test** at a time. Batch evaluation runs stay M3's (they can call the same pieces).

## Decision

**A Python module in `runner/`, launched as `py -m runner diagnose …` from the repository root.**

```
py -m runner diagnose --project <maven-project> --victim <Class#method> [--n 20] [--records flaketrace-records]
```

| Option | Required | Default | Notes |
| --- | --- | --- | --- |
| `--project` | yes | — | Maven project to diagnose; must contain `pom.xml` |
| `--victim` | yes | — | `Class#method`, the same format as M1's extractor |
| `--n` | no | `20` | repeat count (I3) |
| `--records` | no | `flaketrace-records` | folder for the execution record and the report; git-ignored; `diagnose()` refuses a folder inside the project |

No `--depth` (the contract fixes 2) and no `--timeout` (120 s per JVM run); either is added when a
real project needs it.

### Files

| File | Job |
| --- | --- |
| `runner/cli.py` | `main(argv=None) -> int` — parse options, run the flow below, return the exit code |
| `runner/__main__.py` | calls `main()` so `py -m runner` works |

No code in `evidence/` or `eval/` changes; the CLI calls only their public functions.

### Flow

1. Parse options; `--victim` must be Java names `Class#method` (letters, digits, `_`, `$`, `.` in the
   class; no spaces), because it also becomes part of the record's file name; `--project` must
   contain `pom.xml`.
2. `runs = diagnose(project, victim, n, record_dir=records)`.
3. Only if `runs.status == POLLUTER_FOUND`: `Project([target/classes, target/test-classes])`
   (compiled by step 2), `analyse_test` for the polluter and the victim at
   `evidence.extract.DEFAULT_DEPTH` (2), `find_edges`, `report_fields` → `fields`. For any other
   status no polluter is blamed, so there is nothing to look up (`fields = None`).
4. `report = assemble_report(runs, fields)` — M3's `decide()` and schema validation.
   If it raises `UnhandledStatus` (today: `NO_SINGLE_POLLUTER`, `NOT_REPRODUCED`), print why and
   the execution record's path, write **no** report, exit 3. The CLI does not keep its own list
   of supported statuses: when M3 supports more, the CLI produces those reports unchanged.
5. Write the report as `<execution record path minus .jsonl>.report.json`, next to its record,
   and print a short summary: outcome (and reason), victim, polluter, resource with write/read
   offsets, reproduction `s/n` with its lower bound, alone `s/n`, report and record paths.

The report's `execution_record_reference` is the record path as `diagnose()` returns it, which is
relative when `--records` is relative (the default) — portable across machines.

### Exit codes and errors

Codes 0/1/2 follow M1's extractor; 3 is new.

| Code | Meaning | Raised by |
| --- | --- | --- |
| 0 | report written — **any** outcome, including `UNRESOLVED` | — |
| 2 | input is wrong | option checks in step 1; a `DiagnoseInputError` from `diagnose()` (`n < 1`, records folder inside the project or a file, victim not among the project's tests, checked before any record is written) |
| 1 | the tool could not do its job | Maven failing (`CalledProcessError`), test discovery hanging past the timeout (`TimeoutExpired`), a missing `java`/`javac`/`mvn` or harness compile failure (`ToolError` from `runner.order_runner`), any `ExtractError` (the runner already ran these tests, so the extractor failing on them is a tool problem, whatever its own code), a report failing schema validation |
| 3 | diagnosis ran, no report can be built yet | `UnhandledStatus` |

Known errors print one line, `error: <what and what to do>`, on stderr, with no traceback. The
exceptions above are caught only around the call that raises them. `DiagnoseInputError` (a
`ValueError`) and `ToolError` (a `RuntimeError`) are dedicated classes, so an internal `ValueError`
or `RuntimeError` (e.g. `run_ordered`'s duplicate-test check) is not mistaken for a user error
(final-review finding, 2026-10-10). A report failing schema validation exits 1 with a traceback:
that is a bug in the pipeline, not a known error. **Unexpected exceptions are not
caught**: Python prints the traceback and exits 1, so an unforeseen bug stays visible.

A source change detected by the integrity check is a finding, not an error: the report says
`UNRESOLVED(SOURCE_INTEGRITY_FAILED)` and the exit code is 0.

## Alternatives considered

| Alternative | Why not now |
| --- | --- |
| Installed `flaketrace` command (`pyproject.toml`, `pip install -e .`) | Wanted, deferred to a later iteration (M2, 2026-10-10). Doing it properly needs (a) the packages renamed from the generic top-level `runner`/`eval`/`evidence` to `flaketrace.*`, touching all three members' imports, and (b) `runner/harness/FtHarness.java` shipped as package data. How the tool is delivered also depends on the committed Linux container (claim E1). `main(argv) -> int` is shaped so the later entry point is one line: `flaketrace = "runner.cli:main"`. |
| Running M1's extractor as a subprocess (`python -m evidence.extract --polluter … --victim …`) | Adds a process boundary, JSON parsing and exit-code mapping inside one Python program. The contract lists in-process calls with `ExtractError` as equally supported. |
| Writing the raw counts to a file when no report can be built | A second output format nobody agreed on. The execution record already holds every run. |

## Consequences and limitations

- **Must be run from the repository root** (or with it on `PYTHONPATH`), like M1's extractor;
  removed by the later installable command.
- One victim per run; one polluter's resource evidence (the one `diagnose()` found).
- F3 (`NO_SINGLE_POLLUTER`) and `NOT_REPRODUCED` give exit 3 and no report until W10 and the
  agreed schema change (nullable `failure_signature`, a reason for no single polluter).
- The `runner` CI job must install `eval/requirements.txt`: the CLI imports `eval.report`, which
  needs `jsonschema`.
- Inherits ADR-003/004's limits (JUnit 4, `@BeforeClass` per method, discovered order is
  alphabetical, single polluters only).

## Verification plan

1. `runner/tests/test_cli.py`, without a JVM:
   - exit 2 before Maven runs: `--victim` without `#`, `--n 0`, a project without `pom.xml`;
   - with `runner.cli.diagnose` replaced by `unittest.mock.patch` (test code only) returning a
     hand-built `DiagnosisRuns`: `VICTIM_FAILS_ALONE` → exit 0, report written,
     `UNRESOLVED(VICTIM_FAILS_ALONE)`, extractor not called; `NO_SINGLE_POLLUTER` → exit 3,
     no report file, message names the record.
2. Real runs on `fixtures/od-fixture` (skip without JDK/Maven; fail under `FLAKETRACE_REQUIRE_JVM`):

| Case | How | Expected |
| --- | --- | --- |
| F1 | `py -m runner diagnose …` as a separate process, n = 20 | exit 0, `VERIFIED`, resource `odfixture.Config#mode`, report next to the record, relative record path that exists |
| F2 | in-process, n = 20 | exit 0, `VERIFIED`, depth-2 edge `odfixture.turbo` read in `FeatureFlags.isTurboEnabled` |
| F3 | in-process, n = 3 | exit 3, no report |
| N1 | in-process, n = 5 | exit 0, `UNRESOLVED(VICTIM_FAILS_ALONE)` |

   n = 20 for `VERIFIED` because 5/5 has a Wilson lower bound of about 0.57, below 0.70.
3. Each new test is seen failing before the code exists; a mutation (skipping step 3) must make
   the F2 test fail.
4. CI: the `runner` job runs `runner/tests/test_cli.py` after installing `eval/requirements.txt`.

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☐ | in-process calls to `analyse_test`/`find_edges`/`report_fields` at depth 2 |
| M2 | ☑ | Chose approach 1, exit-3 handling and the deferred `flaketrace` install on 2026-10-10 |
| M3 | ☐ | catching `UnhandledStatus`; `assemble_report(runs, fields)` as the only report builder |
