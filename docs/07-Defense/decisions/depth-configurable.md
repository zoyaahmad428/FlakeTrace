# Decision: analysis depth becomes a configurable committed parameter

**Date:** 28 August 2026 · **Status:** `COMMITTED` · **Owner:** Member 1

---

## The decision

Analysis depth — how far the static resource analysis follows method calls from the test body
before stopping — moves from a **fixed constant (1)** to a **configurable, committed feature**
with declared defaults, a reported precision cost, and its own axis in the evaluation.

## What depth means

| Depth | Follows |
| --- | --- |
| 1 | Direct references in the test method body only |
| 2 | One level of callees |
| 3+ | Transitively, through project-owned callees |

Each level **increases recall** and **increases both analysis time and the over-approximation
rate**. That trade-off is the reason it is a parameter rather than a value.

## Why — the evidence

At depth 1, `|writes(candidate) ∩ reads(victim)|` was **zero for every candidate in every
case**. The mechanism: direct static-field references in a test method body do not capture
state written through helper methods, factory calls, static initialisers or library entry
points — which is **where the state actually moves in both subject projects**.

Concrete instance (FJ-02):
```
DateParserTest.setUp@5   ──writes──▶  JSON.defaultTimeZone
                                            │
                                       (2 hops down)
                                            │
TypeUtils.cast@536       ──reads───▶  JSON.defaultTimeZone
```
Re-extracting at depth 2 moved the true polluter from **rank 39 to rank 1** — 97.4% fewer
confirmations for that case.

## The honest limit of that evidence

**The other three reproduced cases did not move at any depth we tested.**

> Depth is **necessary but not sufficient**. One case improving is a mechanism finding, not a
> method.

The claim this supports is narrow — *that depth is the variable worth investigating* — not
that depth two works. Whether it works is **RQ1**, measured across the frozen benchmark with
top-k recall and MRR, with depth appearing in the ablation table alongside resource-only,
order-only, static-only and dynamic-only.

## Why configurable rather than "set it to 2"

Two reasons:

1. **The right value is project-dependent.** A suite whose tests call helpers heavily needs
   more depth than one manipulating state inline.
2. **Fixing it as a constant would be choosing a value we have no evidence for** — which is
   exactly the error that produced the zero-overlap result in the first place.

## The outstanding experiment this decision creates

**Depth sweep**, priority 1 of five pre-defence items. Depths 1, 2, 3 and unbounded across
all four reproduced cases, reporting **rank of the true polluter AND overlap-set size** at
each depth.

**Overlap-set growth is the point:** if precision collapses at depth 3 through shared utility
code, then *"there is an optimal depth"* becomes a real tuning result rather than a
hand-wave. Runs offline against data already held — no re-scanning.

## Panel answer (Q57)

> Depth is how far the static resource analysis follows method calls from the test body
> before stopping. Depth one is direct references in the test method itself; depth two follows
> one level of callees. Each level increases recall and increases both analysis time and the
> over-approximation rate.
>
> It is configurable because the POC showed it is the decisive variable, and because the right
> value is project-dependent. Fixing it as a constant would be choosing a value we have no
> evidence for, so it becomes a parameter with a measured depth-versus-cost curve.
