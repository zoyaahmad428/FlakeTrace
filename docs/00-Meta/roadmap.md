# Roadmap

*Answer Q96 with **exit evidence, not activities**. A panel asking for your timeline is asking
what will exist at each gate, not what you will be doing.*

Gantt: `attachments/GanttChart.jpeg`

---

## Phase table

| Phase            | Content                                                                                                                                           | **Exit evidence**                                                                                                                     |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **Proposal**     | Stakeholder evidence · contemporary comparison · POC with pre-registered rules · dataset and licence inspection · frozen scope                    | POC bundle with NARROW decision, **depth sweep, per-case classification, oracle ceiling, out-of-domain case, non-perturbation check** |
| **FYP-I early**  | Buildable benchmark subset · container runner · exact outcome signatures · random and one-by-one baselines · fixtures F1–F5                       | **Reproduction yield, baseline results, clean-container logs**, requirements and design baseline                                      |
| **FYP-I end**    | Static-field and system-property evidence · graph · configurable depth · initial minimiser · end-to-end provisional certificate · fixtures F6–F10 | **Working prototype from input to certificate with measured baselines**                                                               |
| **FYP-II early** | Filesystem evidence · adaptive policy · verification and abstention · security hardening · certificate renderer · **CDR V1 if gates met**         | **Policy ablations, depth matrix, overhead measurement, threat-model tests, clean install**                                           |
| **FYP-II final** | Held-out evaluation · failure analysis · CI packaging · user acceptance · deployment · **CDR V2/V3 if V1 gates met**                              | **Frozen results, acceptance decision, deployed release, reproducibility bundle**                                                     |

## Iteration mapping (from the Gantt)

| Iteration | Months | Milestone |
| --- | --- | --- |
| 1 | Aug – Oct | Architecture & interface contracts · benchmark/threshold/threat-model **freeze** · static extraction · sandbox runner · benchmark manifest and independent baselines |
| 2 | Nov – Jan | Resource normalisation & graph · dynamic collection · search/ranking/adaptive policy · ablation harness · deletion minimisation |
| 3 | Feb – Apr | Failure signatures & repeated-run verification · controlled fixtures & reproducibility bundle · certificate evidence path · repair verification (gated) · CLI/CI & container security · non-perturbation verification |
| 4 | May – Jun | End-to-end integration & user acceptance · final testing, deployment, report & handover |

**Local schedule note:** by the **mid-April job fair**, the practical system should already be
stable enough for professional repeated demonstration. **Essential development should not be
left to the post-job-fair period.**

## Critical path (Q97)

> **Reproduced cases in clean containers.**

Everything downstream — baselines, ranking evaluation, minimisation checks, replay intervals,
acceptance tasks — **consumes them**. That is why the go/no-go data gate sits **before defence**
rather than at Mid-1, and why we ran the reproduction work first in the POC rather than building
the planner first.

## Why this is a full year for three people (Q104)

> Because **three of the four hardest parts cannot be started until the previous one works.**
>
> Reproducing real cases in clean containers is a semester-scale problem on its own — RankF
> discarded nearly 40% of its starting set. Instrumentation that does not perturb the phenomenon
> required us to find and fix two harness defects in a single POC day. The planner cannot be
> evaluated until the baselines are measured, and the baselines cannot be measured until the
> cases reproduce.

**The volume of code is not the argument and we would not make it** — the guide is explicit that
scale of implementation no longer establishes capstone difficulty.

## After proposal approval

**Scope is baselined.** Changes to scope, architecture, security, data handling, evaluation
criteria or ownership should be **recorded and approved rather than made silently**.

| Gate | What must be true |
| --- | --- |
| **Mid-1** | Requirements and design baselines · data/access/licences/ethics secured · real-user workflow validation · **riskiest subsystem prototyped** |
| **Final-1** | Working primary scenario **end-to-end** · integration proven · **baseline measured** · first deployment attempted |
| **Mid-2** | Committed scope integrated · system and non-functional testing complete · evaluation underway · failure/edge cases exercised · release/deployment rehearsed |
| **Job fair (mid-April)** | Stable enough for **professional repeated demonstration** |

## First thing after approval (Q108)

> **Expand the reproduction set.** Every downstream measurement depends on it, and our current
> cases support a direction and no magnitude.
>
> In parallel, **land the four-way instrumented and uninstrumented control as a harness
> requirement**, so that no case enters the manifest without it.
