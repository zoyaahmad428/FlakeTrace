# Architecture

*Status (2026-11-13): target architecture for the whole project. Iteration 1 implemented part of
it (next paragraph). **Iteration 2's additions are in the section "Iteration 2 — what changes"
below**, proposed in ADR-010 to ADR-015 after the Mid review.*

*Status (2026-10-11): target architecture for the whole project; Iteration 1 implements part of it.
Implemented: sandbox runner (`runner/order_runner.py`, one fresh JVM per order, per-run timeout,
no container yet), test discovery and environment record (`runner/discovery.py`,
`runner/diagnose.py`), outcome normaliser (failure signatures), evidence collector — static only
(`evidence/extract.py`), minimiser/verifier (`runner/search.py`, `runner/minimise.py`, repeated
runs, `eval/stats.py`), certificate as a schema-validated JSON report plus summary
(`eval/report.py`, `eval/outcome.py`), CLI (`runner/cli.py`). Not yet implemented: evidence
store/graph, diagnosis planner (only a candidate `priority` hook, unused by the CLI), budgets
beyond the timeout, dynamic evidence, CI adapter, CDR. Iteration 1 evidence approach: [[03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation]].
How components call each other: [[contracts/interfaces]].*

---

## Iteration 2 — what changes

*`ACCEPTED` 2026-11-13 (ADR-010 to ADR-014; ADR-015 as a spike only). Nothing in this section is
built yet.*

The Mid review found the pipeline sound and three things missing around it: the verdict claimed
more than the counts supported, no report could be audited away from the machine that made it,
and nothing decided what to run next or when to stop. Iteration 2 adds exactly those.

```
                 victim, project, n, BUDGET, POLICY
                              │
        ┌─────────────────────▼──────────────────────┐
        │ PLANNER  (runner/)                  ADR-014 │◄── ranked candidates ── EVIDENCE (evidence/)
        │ chooses the next run · stops at the budget  │                        rank_candidates
        │ never spends the verification reserve       │                        all edges, static overlap
        └───────┬─────────────────────────▲───────────┘
                │ order                   │ outcome + cost
        ┌───────▼─────────────────────────┴───────────┐
        │ BudgetedRunner ► RecordingRunner ► OrderRunner │
        │ ledger           record.jsonl      one JVM,    │
        │ ADR-014          ADR-013           class-grouped lifecycle  ADR-012
        └───────┬──────────────────────────────────────┘
                │ four-way TALLIES: alone · sequence · each deletion     ADR-010, ADR-011
        ┌───────▼──────────────────────────────────────┐
        │ DECISION + REPORT  (eval/)            ADR-010 │
        │ four named claims · typed reason for every end │
        └───────┬──────────────────────────────────────┘
                │ report.json + record.jsonl + manifest
        ┌───────▼──────────────────────────────────────┐
        │ BUNDLE ─► verify-bundle (recount, re-decide)   │  ADR-013
        │        ─► replay on another machine           │
        └────────────────────────────────────────────────┘
```

| New or changed | What it is | Owner | ADR |
| --- | --- | --- | --- |
| **Outcome tally** | Every repeated phase returns pass / matching failure / other failure / infrastructure, not two overlapping counts | M3 type, M2 producer | 010 |
| **Verdict contract v2** | `VERIFIED` asserts four named claims and nothing else; `CANDIDATE` is typed; every way a diagnosis can end has a report | M3 | 010 |
| **Deletion verifier** | Each kept test is removed and the sequence repeated; unneeded tests are dropped | M2 runs, M3 rule | 011 |
| **Class-grouped harness** | Consecutive tests of one class run as one JUnit request, so class-level setup runs once, as under Surefire | M2 | 012 |
| **Execution contract** | A written statement of what is reset between runs and what the integrity check proves | M2 | 012 |
| **Evidence bundle, recount, replay** | A report travels with its record; an independent recount recomputes it; another machine replays it | M3, M2 | 013 |
| **Budget ledger and reserve** | One wrapper every JVM run passes through; verification is paid for before search | M2 | 014 |
| **Planner, version 1** | Candidate order from static evidence; one real decision — analyse deeper or start running | M2 with M1 | 014 |
| **Candidate ranking** | `rank_candidates`: a tuple score, no fitted weights, cached per test | M1 | 014 |
| **Resource intervention** | Restore the named resource between polluter and victim and see whether the failure goes away. Spike only | M1, M2 | 015 |

**What this does to the eight components.** The *diagnosis planner* (5) exists for the first time,
in its simplest form. The *minimiser / verifier* (6) gains deletion evidence. The *certificate
generator* (7) gains the bundle and the replay command it always promised. The *sandbox runner* (2)
gains a budget and a faithful class lifecycle, and still has no container hardening. The *evidence
store / graph* (4) and dynamic collection are unchanged: still FYP-2.

**The interdependence, now in code rather than on a slide:** the planner asks the extractor for
evidence, the cost of that evidence comes out of the same budget as the runs, and the runs it
then chooses decide which further evidence is worth paying for.

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
model-based optional and ablatable) · patch verifier. Patches are suggestions: a developer
reviews and applies them.

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
   location, generates a candidate patch, checks it on a disposable copy with the verification
   contract, and gives the diff to a developer — the analysed project's source is never changed

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
