# Takuan — Levin, Li, Zhang, Shi, Lam (ICSE-NIER 2025)

**Role for us:** `BASELINE` for explanation. **Ref:** [6]

> **The most recent and most directly comparable explanation technique.** It is why we must
> never claim dynamic shared-state explanation as novel.

---

## What it does

Captures **dynamic invariants** (using Daikon [39]) that hold during a passing run and compares
them against those from a failing run — on the basis that invariants holding in a passing
order but not a failing one can indicate the **"clean" value of the shared state**.

Also develops automated approaches that use those invariants to **search for methods that
reset the shared state**.

The authors state that Takuan's ability to analyse **polluted external shared state such as
the file system** lets it handle cases prior work cannot.

## Evaluation scale — note this carefully

**Preliminary, explicitly so.** 13 tests; correct problem invariants produced for **6**.

ICSE-**NIER** is the New Ideas and Emerging Results track, which publishes early-stage work
with smaller evaluations. Worth knowing: this is a NIER-scale result, not a fully validated
one. *(Say this only if the scale is directly relevant — it is not a way to dismiss the work.)*

## The honest consequence for us

> **Dynamic shared-state explanation is not novel and must not be claimed as such.**

## What Takuan does NOT provide — our increment

An **intervention-backed provenance chain**:
- a candidate **writing** a normalised resource
- the target **reading** the same resource
- **controlled order interventions** changing the target's measured failure rate

bound to an **execution budget** and a **replay contract**.

> That combination — **not the use of dynamic state** — is the defensible increment.

## The answer (Q15)

> No, and we do not claim it is. Takuan compares dynamic invariants between passing and
> failing orders and handles external state; its preliminary evaluation covered 13 tests and
> produced correct problem invariants for 6.
>
> Our difference is **the nature of the evidence, not the fact of explaining**. Takuan reports
> an invariant difference — **a correlation** between two executions. We report an
> **intervention-backed path**: a specific write event, a normalised resource identifier, a
> specific read event, plus counterfactual checks in which we delete each retained predecessor
> and insert the suspected polluter to see whether the outcome follows.
>
> **A correlation and an intervention are different evidential objects**, and the certificate
> is designed around the second.

**If pressed on whether intervention is really stronger:**
> Yes, in the specific sense that it rules out coincidental invariant differences caused by an
> unrelated predecessor. It **does not establish causality in general** — which is why
> "definitive causality" is an explicit exclusion.

## What it does better than us (Q19)

**Its invariant-based explanation covers state we classify as unsupported**, because
Daikon-style invariants do not depend on our three resource families.

## Evaluation plan against it

Takuan on an **overlapping explanation subset**, treated as a research comparator rather than
a product. Compare explanation coverage and correctness; **report unsupported-resource cases**.
`STATUS: not yet run — Final-1 exit condition.`
