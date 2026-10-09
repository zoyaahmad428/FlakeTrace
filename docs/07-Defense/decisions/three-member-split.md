# Decision: expand from two members to three, evaluation as the third pillar

**Date:** 4 September 2026 (Revision 2) · **Status:** `PROPOSED — departmental approval pending`
· **Owner:** joint

---

## The decision

The team expands from two to three. The third pillar is **evaluation infrastructure**, not a
third product feature. CDR is a gated extension owned by the same member.

**Approval status:** this is Dossier decision 1, awaiting supervisor and departmental
confirmation. *A scope written for three against a roster of two would be worse than a
narrower scope written for two* — which is why it must resolve before the proposal is
submitted. Tracked in [[07-Defense/weak-points]] §8.

## Why evaluation and not a third feature

**A third member owning a bolted-on feature fails the removal test** — the product still
works without them. Evaluation infrastructure passes it.

The POC produced direct evidence that evaluation was the **binding weakness, not feature
count**:

| Evidence | What it showed |
| --- | --- |
| A single-case ablation was carrying the entire diagnosis | No ablation infrastructure existed to do better |
| 182 identical `LinkageError`s required a human to notice | A signature-clustering check should have tripped automatically |
| A timezone override erased the phenomenon under measurement | No four-way instrumented/uninstrumented control existed |

**Both defects that would have invalidated every result were harness problems, not algorithm
problems.**

## The removal test, applied

> Without Member 3 the project has an algorithm and no trustworthy evidence that it works —
> which, for a Stream B project evaluated against research baselines, is not a partial loss.

Additionally: **a baseline implemented by the person whose method it competes against is not
independent.** Independence of the baseline implementation is itself a design requirement,
and it needs a separate owner.

## Scope discipline — what did NOT grow

The committed core is **unchanged** from the two-member boundary:

- resource families (static fields, system properties, filesystem paths) — unchanged
- build system (Maven/Surefire) — unchanged
- language (Java, JUnit 4 incl. JUnit 3 adapter) — unchanged
- certificate contract — unchanged

> The scope grew by **exactly one pillar**. That was deliberate: the guide's warning is that
> over-scoping is the primary failure mode, and **adding a member is the most common trigger
> for it**.

## Risk this creates

Recorded in the risk register: *three-person overload — integration cost rises faster than
headcount.* Mitigation: interface contracts frozen early; CDR gated; **a third member is not
1.5× delivery**. Trigger for change: FYP-I milestones slip.

## Fallback if approval does not come

CDR drops first. The evaluation pillar redistributes across two members with reduced ablation
scope, and the depth × strategy matrix narrows. The committed core is unaffected either way.

## Panel answer (Q91)

> The team grew to three and the scope grew by exactly one pillar: evaluation infrastructure
> as a first-class component, with CDR as a gated extension owned by the same member. The
> committed core did not expand — the resource families, the build system, the language and
> the certificate contract are unchanged from the two-member boundary.
>
> That was deliberate. The guide's warning is that over-scoping is the primary failure mode,
> and adding a member is the most common trigger for it.
