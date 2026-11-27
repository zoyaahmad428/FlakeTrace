# ui/ — FlakeTrace web UI (Member 2, ADR-009)

Shows what `py -m runner diagnose` produces, on the nine screens of the proposal-stage UI. Every value
comes from a report the CLI wrote; parts FlakeTrace has not built are greyed out and labelled
"NOT BUILT YET — PLANNED FOR …" or "NOT BUILT — NOT IN CURRENT PLAN", and parts built only in the command line
(replay, the W27 container) "IN THE COMMAND LINE ONLY …". The Diagnosis step shows each deletion check (ADR-011). The Target step's Advanced options run the CLI's search,
scope, policy, budget and bundle options; the Source step opens committed bundles from `eval/bundles/` (verified when
opened) and checks any bundle folder.

| Part | What |
| --- | --- |
| `server.py` | Backend on 127.0.0.1:8765: runs the CLI as a subprocess (one job at a time; 30-minute limit, `FLAKETRACE_UI_JOB_TIMEOUT_S` overrides it), lists `eval/reports/`, validates reports against the schema their own `schema_version` names. `POST /api/diagnose` takes `project`, `victim`, `n`, `order` and the run options `search`, `scope`, `policy`, `seed`, `shuffles`, `budget_invocations`, `budget_seconds`, `bundle`, mapped one to one to the CLI's flags (an absent field adds no flag: the CLI's default); it refuses what the CLI refuses (pairs or package scope with an order). A requested bundle is written into the job's own folder, never into the repository, and the job result names it. `GET /api/bundles` lists every committed bundle in `eval/bundles/` (parameters, mode, report); `GET /api/bundles/<name>` opens one by its exact folder name and runs `eval.bundle.verify_bundle` on it then, never cached; `POST /api/check-bundle {path}` runs the same verify, read-only, on any folder (demo step 6: a hand-changed copy) |
| `web/` | React + Vite app on http://127.0.0.1:5174; `/api` is forwarded to the backend |
| `tests/` | Backend tests (`FakeCli` stands in for the CLI; one real F1 run) |

## Run (Windows)

Needs Python 3.11+ with `pip install -r eval/requirements.txt`, Node.js 20+, and for live runs a JDK 8+
(`java`, `javac`, `javap`) and Maven on `PATH`.

    ui\start.cmd

Then open http://127.0.0.1:5174. A live diagnosis of a fixture case has taken about one minute on the
development laptop. Without the JDK or Maven, live runs are disabled and saved reports can still be opened.

## Test

    py -m unittest -v ui.tests.test_server
    cd ui\web && npm ci && npm test && npm run typecheck && npm run build

Design: `docs/03-Design/specs/2026-10-14-ui-design.md`; plan: `docs/03-Design/plans/2026-10-14-ui-plan.md`.
