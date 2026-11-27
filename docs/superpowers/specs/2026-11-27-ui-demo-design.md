# The web UI as the Final demo: run options, honest labels, committed evidence

**Status:** approach B and step 6 option A chosen by M2 on 2026-11-27; builder check done (6 questions: 5
settled as M2's calls, marked; 1 answered by M2); design approved by M2 on 2026-11-27. **Owner:** M2 (`ui/`,
ADR-009: the UI is a front end over the CLI, it never simulates). **Work packages:** W33 (demo rehearsed), W31
(panel wording); demo plan v2.

## Intent and why

The Final demo is driven from the web UI (Form 4: demo quality 15, implementation 25, testing 10 marks). Since the
UI was built (Iteration 1), the CLI gained budget (W24), policy and scope (W25), bundles and replay (W23), pair mode
(W35) and schema v3 with `reproduced_by`. The UI still passes only `--n` and `--order`, its "not built" labels say
ranking, runtime evidence and the container are "planned for Iteration 2", and it cannot open a bundle. The panel
must see, in the UI, exactly what the tool ran and what it established — never more.

## What exists today (read, not assumed)

- `ui/server.py`: `Jobs.start(project, victim, n, order)` builds `py -m runner diagnose … --n --records
  --copy-parent [--order]`; one job at a time; `JOB_TIMEOUT_S = 600`; `check_diagnose_request` validates the body;
  `GET /api/reports` lists schema-valid `eval/reports/*.json` via `eval.schema_validator`; `/api/validate`.
- `ui/web/src/screens/Target.tsx`: victim, fixture picker, known order, `n`, a read-only Wilson floor, and
  `<NotBuilt item={UNBUILT.budget} />`. `state.tsx` `Form = {project, victim, n, order}`.
- `ui/web/src/lib/labels.ts` (`UNBUILT`): container, remoteSource, budget, ranking, filesystem, runtime, teardown,
  repair, verify, evosuite. `labels.test.ts` and `nosim.test.ts` guard them.
- `ui/web/src/lib/report.ts`: mirrors the schema ("schema v2" in its comment); `exploration()` describes
  `order_exploration`, which M3 omits in pair mode, so a pair-mode report says nothing about how it reproduced.
- `Source.tsx`: loads a report from `eval/reports/` or a local file.
- Timing measured on FJ-03 (evidence-m2): pair mode 8 min of runs + ~3 min Maven build in the disposable copy.

## Goals

1. **Run options** in the Target form, in a collapsed "Advanced" section, with the CLI's names and defaults:
   search `order|pairs`, scope `module|package`, policy `original|ranked|random`, seed (always shown: the CLI's
   `--seed` is both the first shuffle seed and the random-policy seed), shuffles, budget invocations and seconds
   (both optional), "write an evidence bundle". `--lifecycle` and `--workspace` are shown read-only at their
   defaults (`class-grouped`, `copy`), like the Wilson floor today. *(M2's call, builder check 5.)*
2. **Server rules equal the CLI's** (so the UI cannot start what the CLI would refuse): `pairs` + a known order →
   refused; `package` + a known order → refused; budget values > 0; enums checked. The CLI stays the authority: an
   exit 2 from it is still shown as an input error.
3. **How it reproduced**, on the Diagnosis step, from the report alone: `reproduced_by "pair"` → "Found in a
   constructed pair (the polluter run directly before the victim); pair mode does not run the project's own
   orders"; `"order"` → today's `exploration()` text; `null` → "never reproduced". Pair counts from
   `budget.candidates.tried`/`budget.candidates.total` when present. A report with no `reproduced_by` key
   (schema v2, before W35) is an order-mode report: today's `exploration()` text, never "never reproduced"
   (the rule replay uses). When `order_exploration.order_given` is true, say "in the given order (N tests)".
   *(M2's call, builder check 4.)*
4. **Committed evidence**: a list of the bundles in `eval/bundles/` (victim, outcome, how reproduced — pair /
   order / **given order** / never, scope, policy, seed, polluter, invocations spent, run date) beside the existing
   reports; the seven 21-Nov FJ-03 bundles ran with a given two-test order (`order_given: true`, 1 candidate) and
   must read "given order", never as order mode reproducing FJ-03 *(builder check 3–4; checked against the files)*; opening one loads its `report.json` into the same screens, labelled
   "Committed bundle `<name>` — pre-run on <date>, not run now", with its `eval.bundle.verify_bundle` result
   (OK, or the first problem), computed **when the bundle is opened, never cached** (about 3 s per bundle measured;
   68 s for all 24, so not at listing).
5. **Honest labels**: every `UNBUILT` entry true today. Features the UI now runs lose their label (budget). Ranking
   becomes runnable (policy). Runtime evidence: "not built — ADR-001's fallback replaced by ADR-015's spike (W34,
   stretch); awaits the supervisor". Container: "a pinned image of FlakeTrace is built (W27); running the analysed
   project in a hardened container is FYP-2".
   A bundle written by a UI run ("write an evidence bundle") goes into the job's own folder, never into
   `eval/bundles/`; the job result names its path and its verify result. *(M2's call, builder check 1: the UI
   never writes into the repository, and a new run is never shown as committed evidence.)* Replay: "in the command line only" (not in this work).
5a. **Check a bundle folder by path** (M2's decision, demo step 6: option A over a terminal step or a UI
   button that tampers itself): a box on the evidence screen takes a local folder path; the server runs the real
   `verify_bundle` on it, read-only, and shows OK or the first problem. Before the slot, the presenter copies the
   FJ-03 bundle to a scratch folder and changes one number; the committed bundle is never touched. Localhost only,
   like every endpoint.
6. **Job timeout** large enough for what the form can start: configurable, default raised to cover a package-scope
   pair-mode run of FJ-03's size (≥ 20 min), shown on the Target step.
7. **Demo plan v2** (`docs/10-Final1/demo-plan.md`): step 5 becomes FJ-03 in pair mode from the victim alone,
   opened as committed evidence (CANDIDATE, `SerializeWriterTest_14#test_writer_1` after 368 of 524, 798
   invocations), then the 7-run comparison (`ranked = original` because there is no static edge; random seeds 76–436
   to a certified polluter, not always the same one); step 6's `verify` shown in the UI (a changed number is caught by the checksum in `read_bundle`, before the
   recount; the demo wording says so); mocked/pre-run parts named. Step 5's bundle is
   `eval/bundles/20261122T120044Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf/` (pairs, package,
   original: CANDIDATE, 368 of 524, 798 invocations).

## Non-goals

Replay from the UI; uploading or fetching a project (remoteSource); running FJ-03 live in the demo slot; editing
bundles (the UI never changes a bundle; step 6's copy is changed by hand before the slot); any change to `runner/`, `eval/` or `evidence/` (the server only calls `eval.bundle.verify_bundle` and the
CLI).

## Anti-goals (a failure even if it works)

- The UI shows a result the CLI did not produce, or a committed bundle as if it were run now.
- A form option the CLI does not have, or a default that differs from the CLI's.
- A label that overstates what is built.

## Constraints

- ADR-009: the UI only calls the CLI and reads its files; `nosim.test.ts` must keep passing.
- Localhost only, one job at a time (unchanged).
- The demo machine needs JDK 8 for fastjson, but step 5 opens a committed bundle, so the demo does not depend on it.
- Tests: `ui.tests.test_server` (Python) and the web tests (`npm test`), both in CI.

## Approaches

| | Approach | Trade-off | Chosen |
| --- | --- | --- | --- |
| A | Run options only | Fixture steps live; FJ-03 (11 min) cannot be shown in the UI within the slot | No |
| **B** | **A + open committed bundles with their verify result** | Every demo step in the UI; FJ-03 from real committed evidence, labelled pre-run | **Yes (M2)** |
| C | Presets ("Standard", "Pair mode") | Hides parameters; UI no longer mirrors the CLI | No |

## Left to the builder

Component layout and styling within the existing design; endpoint names (e.g. `GET /api/bundles`,
`GET /api/bundles/<name>`); how the timeout is configured (constant plus environment variable, or CLI flag of the
server); the exact wording of labels, within goal 5's facts.
