# ADR-001 — Iteration 1 gathers evidence without instrumentation

**Date:** 2026-10-09 · **Status:** `ACCEPTED` by M1, M2 and M3 (PRs #17, #18, #20) and
implemented in Iteration 1 (W6–W10) ·
**Owner:** M1 (evidence) with M2 (execution)

## Context

The defence panel asked whether trace instructions will be injected, whether code will be
modified, and how detection works without logs. The post-defence plan names a **runtime Java
agent** as the *preferred* design. The team's own contract (`report-schema.md`) fixes
`instrumentation_level = "static-only"` for Iteration 1. These must be reconciled before the
Mid Evaluation, or the design and the code will disagree — which the rubric caps at 50%.

## Decision

Iteration 1 uses **controlled re-execution + static bytecode analysis**, and no
instrumentation:

1. **Re-execution (M2):** run the victim alone, then candidate orders, in a fresh JVM each,
   with exact ordering. This alone finds the polluter and the minimal order — it needs no
   logs and touches no code.
2. **Static evidence (M1):** read `putstatic`/`getstatic` and `System.setProperty`/
   `getProperty` call sites from the compiled `.class` files with `javap`, attributed to test
   methods (including `setUp`, `tearDown`, `<clinit>`), to name the shared resource.
3. **Integrity (M2):** hash the analysed project's source before and after; mismatch →
   `UNRESOLVED(SOURCE_INTEGRITY_FAILED)`.

A runtime Java agent (bytecode instrumentation in memory, on a temporary copy, only for the
already-reduced sequence) is the **Iteration 2 fallback**, used only where static evidence
cannot resolve a case. This is step 5–7 of the post-defence fallback ladder.

## Alternatives considered

| Option | Why not for Iteration 1 |
| --- | --- |
| Runtime Java agent from the start | Highest skill risk (bytecode manipulation, the vault's named skill gap for M1); risk of perturbing the phenomenon (the POC's timezone override erased it once); not needed for static-field / system-property cases |
| Source-level instrumentation (inserting log statements) | Violates the "no source modification" promise; needs a disposable copy and recompilation |
| Relying on application logs | The panel's own objection — many projects have none |

## Consequences

- Answers to panel Q1 (no injection), Q2 (no modification) and the no-logs question are
  **true of the Mid demo** — see [[08-MidEval/panel-action-register]].
- Static analysis may report a resource that the polluter *could* write but did not on this
  run (over-approximation). The outcome logic already requires reproduction statistics **and**
  a resource edge before `VERIFIED`, so a static edge alone cannot overclaim.
- Reflection, dynamically computed property keys and native code are invisible statically →
  `UNRESOLVED(NO_SUPPORTED_RESOURCE_EVIDENCE)`, not a false explanation.

## Research basis (panel action A6, 2026-10-11)

- Static vs runtime evidence: [[01-Literature/per-paper/poldet-electrictest]] — a shared-state
  signal is a prior, not proof (PolDet: 324 reported, 194 relevant [9]); sound runtime
  dependency detection cost about 20× (ElectricTest [10]). Static analysis over-approximates;
  runtime collection is precise but costs overhead and can perturb the failure.
- Our measurement of the over-approximation (ADR-006 data, `docs/evidence-m1.md`): on the two
  real fastjson cases, 1 false edge among the 728 candidates that did not affect the victim
  (a write that is restored in `tearDown`), and every real state-setter found at depth 4–5.
  Two cases from one project — a measurement, not a general result.
- Minimisation: [[01-Literature/minimisation-ddmin-vs-one-by-one]].

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☑ | Agree: Iteration 1 evidence is static-only (javap), no instrumentation; built that way in Phases 2–4 |
| M2 | ☑ | Agreed 2026-10-10: the runner and W9 report rely on static-only evidence |
| M3 | ☑ | Agreed 2026-10-10 |
