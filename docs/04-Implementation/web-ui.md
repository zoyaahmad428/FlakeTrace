# Web UI — `ui/` (Member 2, ADR-009)

*Status (2026-11-27): built; the Final demo is driven from it (demo plan v2). Design:
`docs/superpowers/specs/2026-11-27-ui-demo-design.md`; the first version: `docs/03-Design/specs/2026-10-14-ui-design.md`.*

## 1. What it does and why it is there

A front end over the command line, for the panel and for a developer who does not want a terminal. `ui/server.py`
(127.0.0.1:8765) runs `py -m runner diagnose` as a subprocess, one job at a time, and returns only the report file the
CLI wrote, validated against the schema the report's own `schema_version` names. The React app (`ui/web/`) shows it on
nine screens. It can also open the committed bundles in `eval/bundles/` (verified when opened) and check any bundle
folder by path. Nothing is simulated: every value comes from a file the CLI or `eval.bundle` produced
(`ui/web/src/lib/nosim.test.ts`).

## 2. Why it is built this way

- **The CLI is the authority.** Each run option (`search`, `scope`, `policy`, `seed`, `shuffles`, both budgets,
  `bundle`) maps to the CLI flag of the same meaning; an absent field adds no flag, so the CLI's default applies; the
  server refuses, in the CLI's words and order, what the CLI refuses. The CLI's exit 2 is still shown as an input error.
- **Never write into the repository.** A UI run's bundle goes into the job's own temporary folder; the result names it
  and its verify result.
- **One rule for "how it reproduced"** (`report.ts` `reproducedKind`): `pair`, `order`, `given order`, `never`. A
  report without `reproduced_by` (schema v2) is order mode, as replay reads it.
- **Committed evidence is labelled "pre-run, not run now"**, and verified when opened, never from a cache.

## 3. What breaks

- A run longer than the job limit (30 min by default, `FLAKETRACE_UI_JOB_TIMEOUT_S`) is stopped with its JVMs. A
  package-scope FJ-03 pair run takes about 11 min, so the demo opens its committed bundle instead.
- A committed bundle the server cannot read is listed as its own "unreadable" row, with the reason.
- The UI cannot replay a bundle, fetch a project from a URL, or run lifecycle `per-method` / workspace `in-place`
  (shown read-only at the CLI's defaults).
- `check-bundle` reads any local folder: acceptable only because the server listens on localhost and refuses foreign
  hosts and non-JSON posts.

## 4. How to modify it

- **A new CLI option:** add it to `OPTIONS` in `ui/server.py` (field → flag, check), to `DiagnoseRequest` (`api.ts`), to
  `Form`/`toRequest` (`lib/request.ts`) and to the Advanced section (`screens/Target.tsx`). Tests:
  `ui/tests/test_server.py` `TestRunOptions`, `ui/web/src/lib/request.test.ts`.
- **A new committed-evidence column:** `lib/bundles.ts` `bundleRow` and its test, then `screens/Source.tsx`.
- **The Diagnosis step's panels:** `lib/report.ts` `toView` (`reproduced`, `deletions`) and `report.test.ts`, which runs on real committed bundles.
- **A label for something not built:** `lib/labels.ts` and `labels.test.ts`; keep each label true today.
- Tests: `py -3 -m unittest ui.tests.test_server`; in `ui/web`: `npx vitest run`, `npx tsc --noEmit`, `npx vite build`.
