# Architecture

*Status (2026-10-09): `PROPOSED`, partially implemented. Implemented: outcome decision,
statistics, report schema (`eval/`). Not yet implemented: runner, evidence collector,
minimiser, CLI. Iteration 1 evidence approach: [[03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation]].
How components call each other: [[contracts/interfaces]].*

---

## Component map

```
   pinned repo, module, target test, budget
              │
              ▼
     ┌────────────────────┐
     │  PROJECT ADAPTER   │  validate · discover · record environment
     └─────────┬──────────┘
               ▼
     ┌────────────────────────────────────────┐
     │  SANDBOX RUNNER                        │
     │  ordered execution · one JVM per order │
     │  budgets · timeouts · isolation        │
     └────┬──────────────────────────┬────────┘
          ▼                          ▼
 ┌──────────────────┐      ┌─────────────────────┐
 │ EVIDENCE         │      │ OUTCOME NORMALISER  │
 │ COLLECTOR        │      │ failure signatures  │
 │ static + dynamic │      └──────────┬──────────┘
 └────────┬─────────┘                 │
          ▼                           ▼
     ┌────────────────────────────────────────┐
     │  TEST–RESOURCE GRAPH / EVIDENCE STORE  │
     └───────────────────┬────────────────────┘
                         ▼
     ┌────────────────────────────────────────┐
     │  PLANNER → MINIMISER → VERIFIER        │
     └───────────────────┬────────────────────┘
                         ▼
              ┌──────────────────────┐
              │ CERTIFICATE GENERATOR│
              └───┬──────────────┬───┘
                  ▼              ▼
          ┌──────────────┐  ┌──────────────────────┐
          │ CLI / CI     │  │ CDR (GATED)          │
          │ ADAPTER      │  │ context → generate → │
          └──────────────┘  │ patch → verify       │
                            └──────────────────────┘
```

Diagram: `attachments/Block_Diagram_SysArch.png`

## The eight components (Q77 — answer in this order)

| # | Component | Responsibility |
| --- | --- | --- |
| 1 | **Project adapter** | Validates repository/module, discovers tests, records environment metadata |
| 2 | **Sandbox runner** | Executes declared orders, emits normalised outcomes, enforces budgets |
| 3 | **Evidence collector** | Captures supported resource events, attributes them to test boundaries |
| 4 | **Evidence store / graph** | Preserves event provenance, candidate relationships, experiment history |
| 5 | **Diagnosis planner** | Ranks candidates, selects the next experiment |
| 6 | **Minimiser / verifier** | Establishes deletion-minimality and replay intervals |
| 7 | **Certificate generator** | JSON, human-readable report, replay command, abstention reason |
| 8 | **CLI / CI adapter** | Starts a diagnosis, streams progress, publishes artifacts and exit states |

Plus **CDR (gated)**: repair-context builder · patch generator (templated mandatory,
model-based optional and ablatable) · patch verifier.

## The interdependence — always name this

> **The planner's budget decisions change what the collector observes, which changes the graph,
> which changes the planner's next decision.**

That loop is:
- the **Seoul Accord "interdependence"** characteristic, evidenced
- the answer to *"are these not three separate projects?"* (Q89)
- why the certificate is **the single artefact all three members produce jointly**

## The five-stage pipeline

| Stage | Action | Output |
| --- | --- | --- |
| 1. Freeze input | Pin commit, module, target test, environment, budget | Reproducible case identity |
| 2. Capture evidence | Bounded static and dynamic resource events; order-outcome history | Test–resource graph with provenance |
| 3. Select experiments | Rank by information gain per unit cost; **reserve verification budget** | Experiment plan |
| 4. Minimise and verify | Deletion-minimisation with 1-minimality checks; repeated clean replay | Minimal order + reliability interval |
| 5. Issue or abstain | Emit Verified / Candidate / Unresolved with typed reason | **Certificate** |

> **Non-negotiable:** every feature consumes this certificate. **None replaces, reinterprets or
> upgrades it.**

## Data flow

1. Adapter **freezes** the case and records the environment (image digest, JDK, Maven, Surefire, JUnit)
2. Runner executes candidate orders; normaliser converts each result into a **failure signature**
3. Collector attributes resource reads/writes to **test boundaries**; store accumulates the graph
4. Planner ranks candidates and selects the next experiment, **reserving verification budget**
5. Minimiser reduces the failing order; verifier establishes the **replay interval**
6. Generator emits Verified / Candidate / Unresolved
7. **If and only if Verified**, CDR builds a repair context, retrieves code slices by certificate
   location, generates a patch, applies it in an isolated workspace, runs the verification contract

## Ownership by component

| Member | Components |
| --- | --- |
| 1 | Evidence collector · evidence store/graph · certificate evidence path · coverage reporting |
| 2 | Sandbox runner · planner · minimiser · verifier · certificate generator · CLI/CI adapter · container security |
| 3 | Evaluation infrastructure across all of it (benchmark manifest, independent baselines, ablation harness, metrics, fixtures, reproducibility bundle) + gated CDR verification |

## Evaluation infrastructure — committed, and why it is affordable

- Frozen **benchmark manifest** with fetch, build, reproduce and yield reporting
- **Independent baselines**: seeded random, original-order OBO, iFixFlakies, RankFO, oracle ceiling
- **Ablation harness**: depth sweep, resource-family toggles, policy variants — all replayed
  **offline against a single scan outcome table, never by re-execution**
- **Metrics layer**: top-k recall, MRR, success-vs-budget curves, Wilson intervals, paired effect sizes
- **Controlled fixture suite** ([[05-Testing/fixture-suite]])
- **One-command reproducibility bundle**

### The single-scan protocol

> For each case the exhaustive `[candidate, victim]` scan runs **once**. Ground truth, the OBO
> baseline, seeded random baselines and every ranking strategy are then computed **offline** from
> that one outcome table.
>
> **Cost is *N* executions, not *N* × strategies.** This is what makes a full depth × strategy
> matrix affordable — and why three of five outstanding pre-defence items need no re-scanning.
