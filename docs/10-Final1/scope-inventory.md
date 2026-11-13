# Scope inventory — how much of the committed scope is built

*v1 · 2026-11-13 · Status: `PROPOSED`. **The counting is ours and unweighted. The supervisor has
not agreed the items or their weights** ([[10-Final1/supervisor-agenda]] item 5).*

## Why this file exists

Form 4 gives 25 marks to "implementation progress against approved scope: at least 60% of
committed work meaningfully implemented unless scope formally revised". The supervisor's review
noted that "no approved weighted scope inventory exists" and that a completion percentage would be
misleading without one. This is our draft of that inventory, to be corrected and weighted with the
supervisor.

## How it is counted

- The items are the **committed** lists in [[02-Requirements/scope-boundary]] — diagnosis core,
  evaluation infrastructure, safety. Gated, stretch and supporting items are not counted, so the
  web UI earns nothing here.
- **Done** = 1, **Partial** = ½, **Not built** = 0. Every item weighs the same. That is crude:
  the budget planner is worth more than failure-signature normalisation.
- "At the Mid" is the state of tag `mid-eval-v1`, read from the code and the supervisor's review.
- "At the Final if the plan holds" assumes every work package in
  [[10-Final1/iteration-2-plan]] lands. It is a target, not a result.

## Diagnosis core

| # | Committed item | At the Mid | At the Final if the plan holds | Work |
| --- | --- | --- | --- | --- |
| 1 | Maven module validation and test discovery | Done | Done | — |
| 2 | JUnit 4, and JUnit 3 through the adapter | Done | Done | — |
| 3 | Environment capture, including image digest | Partial — JDK, OS, commit; no Maven/JUnit versions, timezone or digest | Done | W22, W23, W27 |
| 4 | Ordered single-JVM execution, one fresh JVM per order | Done | Done | — |
| 5 | Containerised runner | Not built | Partial — pinned image for reproducibility, no hardening | W27 |
| 6 | Execution-context fidelity (class and suite lifecycle) | Not built — `@BeforeClass` runs per method | Partial — class level; suite level still unsupported | W22 |
| 7 | Budget enforcement with a reserved verification split | Not built | Done | W24 |
| 8 | Static extraction of static-field and system-property access, with offsets | Done | Done | — |
| 9 | Configurable analysis depth, lifecycle attribution | Done | Done | — |
| 10 | Filesystem resource family | Not built | Not built — FYP-2 | — |
| 11 | Runtime (dynamic) resource collection | Not built — moved to a fallback by ADR-001 | Not built — spike only (ADR-015) | W34 |
| 12 | Test–resource graph / evidence store | Not built | Not built — FYP-2 | — |
| 13 | Candidate ranking | Not built — hook unused | Done — static-evidence ranking | W25 |
| 14 | Adaptive cost-aware search policy | Not built | Not built — FYP-2 | — |
| 15 | Deletion minimisation with 1-minimality checks | Partial — single-trial `ddmin`, deletions never repeated | Done | W20 |
| 16 | Counterfactual checks | Not built | Partial — deletion checks; resource intervention is a spike | W20, W34 |
| 17 | Failure-signature normalisation | Done | Done | — |
| 18 | Repeated-run verification with Wilson intervals | Partial — works, but the pass-alone defect (FT003) | Done | W18, W19 |
| 19 | Typed abstention | Partial — one status has no report (FT010); no budget reason | Done | W19, W24 |
| 20 | Certificate generation: JSON, human-readable, replay command, evidence bundle | Partial — JSON and summary only | Done | W23 |
| 21 | CLI with CI exit codes; clean Linux install | Partial — CLI and exit codes; no install | Partial — container run; packaged install is FYP-2 | W27 |

## Evaluation infrastructure

| # | Committed item | At the Mid | At the Final if the plan holds | Work |
| --- | --- | --- | --- | --- |
| 22 | Frozen benchmark manifest with yield and exclusions | Partial — fixture entries real, IDoFT entries metadata only | Partial — one or two real cases built and reported | W26 |
| 23 | Independent baselines: random, one-by-one, iFixFlakies, RankFO, oracle | Partial — random detection on the fixture only | Partial — one-by-one and random at the same endpoint; published tools are FYP-2 | W25, W26 |
| 24 | Ablation harness including the depth sweep | Partial — a depth-cost measurement tool | Partial | — |
| 25 | Metrics and statistics layer | Partial — Wilson intervals; no ranking or cost metrics | Partial — cost-to-verdict and position-of-first-relevant added | W25 |
| 26 | Controlled fixture suite | Done — seven cases | Done — plus the new controls | W19, W21, W22 |
| 27 | One-command reproducibility bundle | Not built | Done | W23 |

## Safety

| # | Committed item | At the Mid | At the Final if the plan holds | Work |
| --- | --- | --- | --- | --- |
| 28 | Rootless container, network off, limits, redaction, full audit | Not built — a per-run timeout and the execution record only | Not built — path redaction in bundles only; stated as "trusted projects only" | W22, W23 |

## The count

| | Done | Partial | Not built | Score of 28 | Share |
| --- | --- | --- | --- | --- | --- |
| **At the Mid** | 7 | 10 | 11 | 12 | **43%** |
| **At the Final if the plan holds** | 15 | 8 | 5 | 19 | **68%** |

## What to say about it

- "By our own unweighted count we were at about 43% of the committed scope at the Mid, and the
  plan for the Final takes us to about two thirds. The weights are not agreed yet."
- Do **not** say "60% complete" as a fact. It is a target that depends on the plan and on weights
  the supervisor has not set.
- Five committed items are not built by the Final: filesystem family, runtime collection, the
  graph, the adaptive policy, security hardening. All five were always scheduled for FYP-2 in
  [[00-Meta/roadmap]]. Say so before being asked. None has been dropped.

## If the supervisor weights it differently

A weighting that values the planner, real-project evaluation and safety more heavily will lower
both numbers. That is a reason to settle the weights **now**, while the plan can still change —
not after the Final.
