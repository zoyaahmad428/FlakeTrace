# Ownership Map

*Who owns what, what individual evidence each produces, and — most importantly — what
**everyone** must be able to explain regardless of ownership.*

> **The panel's diagnostic is the removal test:** if a member were removed, would a
> meaningful technical responsibility and its evidence disappear?

> **Deferring to a teammate — "that is X's part" — is the single most damaging answer
> available in a defence.** Answer at the level you can, then offer that the owner can add
> detail.

---

## The shared minimum — every member, unprompted

Rehearse until each of these is a three-sentence answer with no hesitation:

1. **What the certificate contains** and what its three decision classes mean
2. **What 1-minimal means** and why a global minimum is not claimed
3. **What the Wilson interval describes** — and what it does not
4. **The four abstention reasons** — unsupported resource, budget exhausted, unstable build, inconsistent outcomes
5. **The three resource families** and what is excluded
6. **The three closest research systems** and the delta against each
7. **What the POC found** and what it changed

Plus, for this project specifically:
8. **The Java/stakeholder gap** and the answer to it ([[07-Defense/weak-points]] §1)
9. **Why CDR does not violate our own repair exclusion**

---

## Member 1 — Resource evidence and explanation

**Owns:** static bytecode extraction with offsets · configurable analysis depth and
call-graph traversal · attribution including `setUp`/`tearDown`/`<clinit>` · bounded dynamic
collection for system properties and filesystem paths · resource identifier normalisation ·
test–resource graph · evidence labelling · certificate evidence path · resource-coverage
reporting.

**Individual design decisions:** supported resource semantics · identifier normalisation ·
provenance · the static-vs-dynamic trade-off · trace coverage · safe redaction.

**Individual evidence produced:** resource-edge precision and coverage · depth sweep results ·
static-vs-dynamic ablation · instrumentation overhead · unsupported-resource taxonomy ·
explanation audit.

**If removed:** the certificate has no evidence path. FlakeTrace degrades to "this order
reproduces the failure" — which iDFlakies already provides.

**Owns before the defence:** depth sweep (priority 1), per-case cause classification
(priority 2).

**Known skill gap to close early:** bytecode manipulation. Learnable within the timeline but
will silently consume weeks if deferred.

---

## Member 2 — Bounded search and verification

**Owns:** sandbox runner with ordered single-JVM execution · execution-context fidelity ·
budget enforcement and the search/verification split · candidate ranking and adaptive policy ·
deletion-minimisation · counterfactual checks · failure-signature normalisation ·
repeated-run verification · typed abstention · certificate generation · CLI, CI integration,
container security.

**Individual design decisions:** candidate policy · cost model · budget allocation · stopping
rule · 1-minimality · failure equivalence · recovery · the replay contract.

**Individual evidence produced:** success-at-budget curves · invocation and time comparisons
against baselines · replay intervals · minimality checks · abstention quality · security and
recovery tests · clean-machine deployment.

**If removed:** no bounded diagnosis, no reliability guarantee, no deployability.

**Owns before the defence:** instrumentation non-perturbation check (priority 5).

---

## Member 3 — Evaluation infrastructure and verified repair

**Owns (primary):** frozen benchmark manifest with yield and exclusion reporting ·
independent baseline implementations · ablation harness · metrics and statistics layer ·
controlled fixture suite · reproducibility bundle · non-perturbation verification.

**Owns (secondary, gated):** repair verification contract · suppression detector · regression
detection · policy engine.

**Individual design decisions:** manifest inclusion and exclusion rules · split and leakage
policy · baseline fairness conditions · control design · remediation ranking.

**Individual evidence produced:** reproduction yield and exclusions · reproducible experiment
bundle · baseline results the other two members did not produce · depth × strategy matrix ·
paired comparisons with intervals · fixture pass/fail evidence · adversarial patch-rejection
rate · reproducibility bundle.

**If removed:** no independent baselines, no ablation infrastructure, no statistical
discipline, no reproducible bundle — and no way to verify a repair is not a cover-up.

**Owns before the defence:** oracle ceiling + alternative rankings (priority 3) ·
out-of-domain subject (priority 4) · **reconciling the victim/brittle vs reproduction-count
wording** (do this first).

**Known skill gap to close early:** statistical rigour.

### Q88 — "Member three sounds like support work. Convince me."

> The strongest evidence is our POC. Both defects that would have invalidated every result —
> the 182 false polluters from missing suite context, and the timezone override that erased
> the phenomenon — were **harness problems, not algorithm problems**. The measurement
> infrastructure is the component that decides whether any number this project produces means
> anything, and it is where the design decisions about leakage, splits, controls and baseline
> fairness live.
>
> Apply the removal test: without member three the project has an algorithm and no
> trustworthy evidence that it works, which for a Stream B project evaluated against research
> baselines is not a partial loss.

**If still doubted:** do not argue. Point at the specific individual design decisions listed
above — the guide's requirement is *decisions, implementation and validation*, not module
count.

### Why the third pillar is evaluation and not a third feature

A third member owning a bolted-on feature **fails the removal test**, because the product
still works without them. Evaluation infrastructure **passes** it — and the POC produced
direct evidence it is a full role: a single-case ablation was carrying the entire diagnosis,
and 182 identical `LinkageError`s should have tripped a signature-clustering check rather
than requiring a human to notice.

**A baseline implemented by the person whose method it competes against is not independent.**

---

## Joint responsibilities

Architecture and interface contracts · benchmark freeze · threshold freeze · threat model ·
end-to-end integration · user acceptance · gating decisions · report and handover.

**Interface contracts are frozen at the design baseline precisely so the three areas cannot
drift into separate submissions.**

## How the three connect — Q89

> The collector's output is the planner's input. The planner's experiment choices determine
> what the collector sees next. The verifier's acceptance rule determines when the planner may
> stop. The evaluation harness defines the controls that make all three trustworthy. And the
> certificate is the single artefact all three produce jointly.

---

## Skills

**Needed:** JVM-level Java including static initialisation and class loading · bytecode
literacy · Maven and Surefire · JUnit internals · Docker and container security · experimental
design and confidence intervals · Linux and Git discipline · technical writing.

**Not needed:** machine learning · frontend development · GPU or CUDA experience.

---

## Defence-day protocol

- Decide **before** walking in which member answers first for each section
- **Whoever owns a subsystem answers it**, even if another member could answer faster
- If asked something outside your area: answer at the level you can, *then* offer that the
  owner can add detail. Never open with the deferral
- The panel is assessing **three engineers, not one spokesperson**
