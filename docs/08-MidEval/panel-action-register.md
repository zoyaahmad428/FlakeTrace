# Panel action register

**Decision:** Approved with Minor Modifications (proposal defence, F26-214).
**Source:** `DefenseResult.txt` (claude.ai project) — comments copied exactly below.
Supporting plan: *FlakeTrace – Post-Proposal-Defence Improvement and Execution Plan*
(`Mid Eval/FlakeTrace-Defense.pdf`).

> Every row stays here until closed — including the ones still open. The rubric caps progress
> marks if an action is missing from this register or has no evidence link.

Status values: `OPEN` · `IN PROGRESS` · `COMPLETE` · `BLOCKED`

## Exact panel comments

> Approved. Do more research to improve your proposed solution and implement the given
> suggestions. … students need to think more carefully about the proposed solution (e.g., in the
> case of a Flake Trace, how will the system detect it if no logs are available?). In the next
> presentation, students need to answer: 1) Will log trace instructions be injected into the
> code? 2) Will the code be modified? 3) How will the code block be isolated? 4) What are
> diverse scenarios where this approach is applicable?

## Register

| ID | Panel comment | Decision and rationale | Owner | Status | Evidence | Next action and date |
| --- | --- | --- | --- | --- | --- | --- |
| A1 | How will the system detect it if **no logs** are available? | **Accepted.** Detection never depends on application logs. It uses test identities, execution order, pass/fail, exceptions and stack traces from controlled re-execution, plus resource reads/writes from compiled bytecode. Logs are optional evidence. | M2 | IN PROGRESS | Design: [[03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation]]. Fixture cases F1–F3 contain no logging at all (`fixtures/od-fixture`). | Demo F1 end-to-end with no logs — by submission |
| A2 | Q1: Will **log/trace instructions be injected** into the code? | **Accepted, answer: no for Iteration 1.** Resource evidence is read from compiled bytecode with `javap`; nothing is injected. Runtime tracing (a Java agent, in memory only, on the already-reduced sequence) is an Iteration 2 option if static evidence proves insufficient. | M1 | COMPLETE | [[03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation]]; `evidence/extract.py` reads `.class` files with `javap` and writes nothing (PRs #9, #15). F1 and F2 reports are `VERIFIED` with a bytecode-level resource edge and `source_integrity.passed: true` (`eval/reports/f1.json`, `f2.json`). | Demo step 3 shows the `javap` evidence live. Runtime agent only if static evidence proves insufficient (Iteration 2, ADR-001) |
| A3 | Q2: Will the **code be modified**? | **Accepted, answer: no.** The analysed project's source is hashed before and after every diagnosis; a mismatch forces `UNRESOLVED(SOURCE_INTEGRITY_FAILED)`. | M2 | IN PROGRESS | Contract field `source_integrity` and decision row in `eval/outcome.py` (implemented, tested). Runner-side hashing not yet built. | Hashing in runner — by submission |
| A4 | Q3: How will the **code block be isolated**? | **Accepted.** Two isolations: (1) *sequence isolation* — victim run alone, polluter search, deletion minimisation to a 1-minimal order, repeated runs with a Wilson interval; (2) *cause localisation* — the shared resource with polluter write and victim read locations at method + bytecode-offset level. Statement-level accuracy is not claimed. | M2 (1), M1 (2) | IN PROGRESS | Schema fields `reduced_sequence`, `polluter_write_location`, `victim_read_location`; statistics in `eval/stats.py` (tested, verified against statsmodels). Part (2) done (M1): `report_fields` gives the shared resource with method + bytecode offset per side, e.g. F2 `FeatureFlags.isTurboEnabled@2` (PRs #15, #34; [[evidence-m1]]) | Runner + extractor — by submission; M1 part done |
| A5 | Q4: What **diverse scenarios** is this applicable to? | **Accepted, scoped honestly.** Iteration 1: static-field and system-property pollution, single and multi-polluter (F3). Iteration 2: filesystem paths. Out of scope, recognised and reported as `UNRESOLVED` rather than forced: concurrency races, external services, time-dependent and always-failing tests. Negative controls N1/N2 test exactly this. | M3 | IN PROGRESS | `fixtures/od-fixture/ground_truth.json` (5 cases, written before any run); scope: [[02-Requirements/scope-boundary]] | Run all 5 cases through the pipeline — by submission |
| A6 | Do more **research to improve the proposed solution** | **Accepted.** Research targets: runtime vs static evidence trade-off (iDFlakies, iFixFlakies, PolDet/ElectricTest already in `01-Literature/`); delta debugging for multi-polluter minimisation. | M1 | OPEN | `01-Literature/` (pre-defence) | Add one note on minimisation (ddmin vs one-by-one) and update ADR-001 references — date: *fill* |
| A7 | Plan §7: record the **controlled execution environment** for every run | **Accepted.** Each run records commit, test order, JDK, OS/container, seed, timestamps. | M2 | OPEN | — | Execution record in runner — by submission |
| A8 | Plan §9: **reproduction confidence** — repeat, compare with victim alone, report uncertainty | **Accepted.** | M3 | COMPLETE (logic) | `eval/stats.py`, `eval/outcome.py`, 55 passing unit tests in CI | Real counts once runner exists |
| A9 | Plan §10: **evidence report** with victim, polluters, reduced sequence, frequency, resource, locations, signature, confidence, limitations | **Accepted.** | M3 (schema), all (fields) | COMPLETE (schema) | `eval/schema/report.schema.json`, [[contracts/report-schema]] | First real report on F1 |
| A10 | Plan §8 lists databases, ports, threads, caches | **Adapted.** Committed Iteration 1 families stay at static fields and system properties (filesystem in Iteration 2). Wider resources would repeat the over-scoping risk the defence warned about; they are reported as unsupported. | All | COMPLETE (decision) | [[07-Defense/decisions/resource-family-boundaries]], ADR-001 | Confirm with supervisor at Mid |

## Summary for the worksheet

| | |
| --- | --- |
| **Actions completed** | A2 (no injection; static evidence on F1/F2), A8, A9 (logic and schema), A10 (scope decision) |
| **Actions still open** | A1, A3–A5 need the runner to show live evidence (A4's M1 part is done); A6, A7 not started |
| **Scope consequence** | Approved scope unchanged; runtime instrumentation explicitly moved to Iteration 2 (ADR-001) |
| **Supervisor-approved exceptions** | None yet — A10 to be confirmed |
