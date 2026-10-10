# ADR-006 — Resource evidence depth: accept 1–5 and deepen pair mode only when needed

**Date:** 2026-10-10 · **Status:** `ACCEPTED` by M1, M2 and M3 (PRs #28, #29, #33) and
implemented, together with the change to
[docs/contracts/resource-evidence.md](../../contracts/resource-evidence.md), in M1's `m1/adr006-deepen` PR · **Owner:** M1 (evidence) · **Work package:** W8 ·
**Builds on:** [[03-Design/decisions/ADR-002-evidence-extractor-implementation]],
[[03-Design/decisions/ADR-005-w9-diagnose-cli]]

## Context

ADR-002 set the default depth to 2 and the accepted range to 1–3. The fixture alone justified
that. The first real project does not fit it.

All numbers below are from real runs recorded in [[evidence-m1]]. Depths 4 and 5 are
exploration: a scratch script lifted the cap in memory, and the code still accepts 1–3.

**Fixture** (all 156 ordered pairs of the 13 fixture tests): the same 4 ground-truth edges
(F1, F2, F3-A, F3-B) at depths 2, 3, 4 and 5. No false edge appears at any depth.

**fastjson @ `e05e9c5`.** "Real" means the POC ran the candidate before the victim and it
changed the victim's result (`od_relevant` in `POC/results/scan_*.csv`).

| Case | Candidates (real / not) | Depth 1–3 | Depth 4 | Depth 5 |
| --- | --- | --- | --- | --- |
| FJ-01 | 72 (42 / 30) | 0 real, 0 false | 42 real, 1 false | 42 real, 1 false |
| FJ-02 | 722 (24 / 698) | 0 real, 0 false | 1 real, 0 false | 24 real, 0 false |

- The one false edge is `DateTest2#test_date`. It writes `JSON.defaultTimeZone`, but sets it to
  America/Chicago and restores the old value in `tearDown`. This is the contract's documented
  limitation "written values are not modelled".
- Cost of one pair: FJ-01 at depth 4 took 7.5 s, FJ-02 at depth 5 took 26.3 s (fresh `Project`,
  javap 21). At depth 2 the same pairs take about 3–6 s.
- Why so deep: the victims reach the shared field only inside constructors. FJ-01 goes
  `DateTest.test_date → JSON.toJSONStringWithDateFormat → JSON.toJSONString →
  JSONSerializer.<init>`. FJ-02 goes `… → DefaultJSONParser.<init> → DefaultJSONParser.<init> →
  JSONScanner.<init> → JSONLexerBase.<init>`.

So at the agreed depths the tool explains none of the real cases. Raising the fixed depth
explains them, but makes every pair pay the deepest cost and the most over-approximation.

## Decision (proposed)

1. **Accepted depths become 1–5.** The default stays **2**.
2. **Pair mode deepens on its own, one level at a time, only when needed.** It starts at the
   requested depth (default 2). If there is no edge **and** the walk reported `DEPTH_LIMIT` on
   either side, it repeats the pair one level deeper. It stops at the first depth with an edge,
   at 5, or when nothing was cut off.
   - The pair output records `depth_used` and `depth_requested`.
   - Single-test mode (Output 1) does not deepen; `--depth N` there means exactly N.
   - `--no-deepen` keeps the old behaviour for the depth sweep and for tests.
3. **One small change for callers.** `find_edges` receives tests that are already analysed, so it
   cannot deepen by itself.
   - A new helper, `analyse_pair(project, polluter_id, victim_id, depth=DEFAULT_DEPTH)`,
     analyses both tests, deepens as above and returns the same pair object as `find_edges`.
   - Member 2's `runner/cli.py` and Member 3's `eval/report.py` would replace their three
     calls with it. `report_fields` and the report's shape do not change.
   - Until a caller switches, it keeps today's behaviour exactly.

Why the shallowest depth: an edge found at depth 2 is not replaced by more remote ones. The
fixture never goes past 2, and fastjson stops at 4 or 5.

## Proposed contract change (needs M2 and M3)

In [docs/contracts/resource-evidence.md](../../contracts/resource-evidence.md):

- **Terms → Depth:** "supported 1–3" becomes "supported 1–5". Add one sentence on pair-mode
  deepening.
- **Invocation:** `--depth N` accepts 1–5. Add `--no-deepen`.
- **Output 2:** add `depth_requested` (integer) and `depth_used` (integer) to the pair object.
- **New in "Calling it from another component":** `analyse_pair(project, polluter_id, victim_id, depth)`.
- **Unchanged:** default 2, every existing field, the edge ordering, the exit codes,
  `report_fields`.

## Alternatives considered

| Option | Why not |
| --- | --- |
| Keep 1–3 | Honest, but the tool explains neither real case. FJ-01 and FJ-02 stay `NO_SUPPORTED_RESOURCE_EVIDENCE`. |
| Accept 1–5, default 5 | One constant changes and the CLI picks it up. But every pair pays depth-5 cost (26.3 s for FJ-02) and the most over-approximation, even when depth 2 already has the answer. |
| Accept 1–5, default 2, no deepening | Deeper analysis is opt-in, but `py -m runner diagnose` always uses the default, so the end-to-end path still finds nothing on fastjson. |
| Unlimited depth | No measured need beyond 5. Cost and over-approximation grow without bound. |

## Consequences

- A pair with no edge can cost up to four walks (depths 2–5). Measured after implementation
  (real CLI, default settings, javap 21, one run each): FJ-01 7.73 s (`depth_used` 4), FJ-02
  24.99 s (`depth_used` 5), whole command including the deepening.
- `depth_used` makes the over-approximation visible: a reader can see how far the evidence is
  from the test method.
- Claims C6/C7 (FJ-02 "two hops", rank 39 → 1 at "depth 2") use the POC's hop numbering. They
  still need a joint wording check; this ADR does not change them.
- Two real cases from one project are thin evidence for the bound 5. The bound is a choice to
  revisit, not a finding.

## Verification plan (when agreed)

- Existing tests unchanged; `GroundTruthTest` still sees exactly 4 edges, all at `depth_used` 2.
- New tests on the self-test project: an access 3 calls down is found by deepening from 2 with
  `depth_used` 3; `--no-deepen` does not find it; a pair with no cut-off walk does not deepen.
- fastjson FJ-01 and FJ-02 run through the real CLI: an edge with `depth_used` 4 and 5, timing
  recorded in [[evidence-m1]].

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☑ | Chose auto-deepening with range 1–5 on 2026-10-10 |
| M2 | ☑ | Agree 2026-10-10, with two requests: (1) the report has no field for `depth_used`, so `report_fields` should add a `limitations` line when evidence was found above depth 2 (deeper evidence over-approximates more, e.g. `DateTest2`); (2) M2 switches `runner/cli.py` to `analyse_pair` after this lands, confirming F1–F3 stay at `depth_used` 2 |
| M3 | ☑ | Agree 2026-10-10. Shallowest-edge-wins auto-deepening explains both real fastjson cases without moving the default or paying depth-5 cost on F1/F2/F3; will switch `eval/report.py`/`eval/tools/run_w9_integration.py` to `analyse_pair` once it lands |
