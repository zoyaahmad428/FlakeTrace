# ui/ — FlakeTrace web UI (Member 2, ADR-009)

Shows what `py -m runner diagnose` produces, on the nine screens of the proposal-stage UI. Every value
comes from a report the CLI wrote; parts FlakeTrace has not built are greyed out and labelled
"NOT BUILT YET — PLANNED FOR …" or "NOT BUILT — NOT IN CURRENT PLAN".

| Part | What |
| --- | --- |
| `server.py` | Backend on 127.0.0.1:8765: runs the CLI as a subprocess (one job at a time, 10-minute limit), lists `eval/reports/`, validates reports against `eval/schema/report.schema.json` |
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
