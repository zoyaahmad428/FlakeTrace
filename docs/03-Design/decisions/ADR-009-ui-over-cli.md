# ADR-009 — The web UI runs the CLI and shows only the report it writes

**Date:** 2026-10-14 · **Status:** `PROPOSED` (M2; for M1 and M3 to review) · **Owner:** M2 ·
**When:** Iteration 2, after the Mid evaluation · **Spec:** [[03-Design/specs/2026-10-14-ui-design]] ·
**Builds on:** [[03-Design/decisions/ADR-005-w9-diagnose-cli]]

## Context

The proposal-stage web UI (`POC/POC/flaketrace-ui`) shows nine screens, but its data comes from the POC:
a recorded run (`src/data/recorded.json`), a simulator that makes up a result when no recorded run
matches (`src/lib/sim.ts`, used in `src/lib/api.ts`), and replay dots drawn from a formula
(`flakyReproduces` in `src/screens/Certificate.tsx`). Its live backend (`flaketrace_backend.py`) runs the
proposal's source-level analysis, not the current pipeline.

The current pipeline has one entry point, `py -m runner diagnose` (ADR-005), which writes a report
validated against `eval/schema/report.schema.json`. We want the UI to show that pipeline's results,
including live runs, without showing anything the tool did not produce.

## Options

| Option | For | Against |
| --- | --- | --- |
| **A. New Python backend that runs the CLI as a subprocess and returns the report file** | The UI shows exactly what the terminal shows; `runner/` internals can change freely; Python + unittest like the rest of the repo | A run takes 20–40 s, so the browser must poll a job instead of waiting on one request |
| B. Extend the POC backend | Already serves the UI | 1,020 lines of the old analysis; `POC/` is read-only legacy |
| C. Call Python from the Vite dev server | No separate process | Works only under `npm run dev`; run handling in JavaScript; hard to test in CI |
| D. Import `runner.diagnose` in the backend | No subprocess | Couples the UI to runner internals and duplicates what `cli.py` already does (input checks, evidence, report assembly) |

## Decision

**Option A.** `ui/server.py` (standard-library `http.server`, `127.0.0.1` only) starts
`py -m runner diagnose` as a subprocess, one job at a time, and reads **only** the `*.report.json` the
CLI writes, after validating it against the schema. Exit codes 1–3 are shown as the CLI's own message.
Parts of the POC UI that FlakeTrace has not built stay visible, greyed and labelled with the plan they
belong to ("NOT BUILT YET — PLANNED FOR X") or "NOT BUILT — NOT IN CURRENT PLAN". The POC's simulated
and recorded data is deleted.

## Constraint that forced it

The UI must never show a result the tool did not produce. Reading the report file the CLI writes, and
nothing else, makes that true by construction. If the CLI ever streams structured progress, this
decision can be revisited for progress display only.

## Consequences

- No contract change: the UI is a reader of `report.schema.json` and a caller of the existing CLI.
- `runner/cli.py` exit codes and the report file name (`<record>.report.json`) become something the UI
  depends on; changing them needs the UI tests updated in the same PR.
- New folder `ui/`, owned by M2; a new `ui` CI job.
