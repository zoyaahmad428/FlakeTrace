# Stream Declaration and Current Status

---

## Stream B — application-derived

**Declared:** Stream B.

| Question | Answer |
| --- | --- |
| Did the idea begin from papers, a published method, benchmark or research limitation? | **No.** Research and datasets inform the solution but did not define the entry point |
| Did it begin from an observed real-world workflow failure? | **Yes.** The developer/QA workflow failure after CI identifies an unstable test but cannot explain the order-dependent interaction |
| Which drove it first? | **The application workflow.** Research methods and datasets were then selected to address it |

**Why the classification is appropriate:** the project begins from an unmet diagnostic need in
software testing and must prove the workflow, constraints, operability and evaluation under
realistic CI conditions.

### The answer when challenged (Q9)

> Because it begins with an application workflow failure, not with a paper we wanted to
> reproduce. Developers have a failing CI task and an inadequate diagnosis workflow; we are
> engineering a deployable product for that workflow and evaluating it against research systems.
>
> **If we had started from the RankF paper and set out to improve its ranking accuracy on its
> own benchmark, that would be Stream A. We use RankF as a baseline, not as our starting point.**

**If pressed that it looks like Stream A because the baselines are research tools:**
> The stream is determined by **where the problem came from and what the deliverable is**. Our
> deliverable is an **installable, operable product with a user-facing certificate** — not a
> reported metric.

---

## Proposal defence outcome — 2026-10

**Decision: Approved with Minor Modifications.** The panel asked how detection works without
logs, whether trace instructions are injected, whether code is modified, how the code block
is isolated, and which scenarios apply. Tracked in [[08-MidEval/panel-action-register]].

---

## Supervisor verdict on record (pre-defence)

> **Revise, then Proceed.** The problem, CCP and per-student ownership are strong. The present
> wording does not yet survive a contemporary comparison because iFixFlakies, RankF and Takuan
> already cover important parts of the claimed gap. The revised formulation restores a
> defensible contribution without inflating scope.
>
> *Revision 2 adds a gated remediation module and a third student; the committed diagnosis scope
> is unchanged and remains the contribution.*

---

## Status at a glance

| Area | Current status | What turns it green |
| --- | --- | --- |
| Stream B problem | 🟡 → 🟢 | Stakeholder workflow **recorded** ✅ — but see the Java-ecosystem gap |
| Central CCP | 🟢 | Stronger as budgeted counterfactual diagnosis |
| Contemporary gap | 🟢 | iFixFlakies, RankF, Takuan are now explicit baselines |
| Dataset readiness | 🟡 | Only after a **frozen, licensed, buildable benchmark manifest** |
| Scope | 🟢 | Bounded resource families and hard exclusions in place |
| POC | 🟡 | Experiment run, result negative at frozen scope. Green once depth sweep, per-case classification and out-of-domain case are recorded |
| Evaluation | 🟢 | Precise cost, minimality, replay and abstention definitions in place |
| Ownership | 🟡 | Green once evaluation infrastructure is confirmed as Member 3's primary ownership **and the group change is approved** |
| Repair module (CDR) | 🟡 | Only as a gated, ablatable, verification-bound module |

> **Updated 2026-10-09:** the table above is the pre-defence status. Current status lives in
> [[08-MidEval/iteration-plan]].

## POC decision

**NARROW**, recorded 28 August 2026. The resource *scope* is refuted; the approach is not.
[[07-Defense/decisions/poc-scope-narrow]]

## Five decisions requested from the supervisor

1. **Group size** — confirm the 2→3 expansion is departmentally approved
2. **The gated repair module** — include as gated, or keep out entirely?
3. **Presentation of the negative POC result** — our intention is to *lead* with it
4. **Priority for remaining time** — our ranking: depth sweep → per-case classification →
   out-of-domain subject. Reorder if single-project evidence is the more urgent gap
5. **Stakeholder access** — *"our weakest remaining area."* A Java/Maven CI maintainer or QA
   engineer for 30 minutes would close the biggest gap faster than anything else available to us

## SDG alignment — claimed narrowly

**SDG 9, Industry, Innovation and Infrastructure**, through software reliability infrastructure.

> Unreliable test suites degrade the quality gate industrial software depends on; evidence-based
> diagnosis restores it. **We are not claiming a social-impact contribution.** The guide warns
> against using an SDG label as artificial complexity, so we treat it as **context, not
> justification**.
