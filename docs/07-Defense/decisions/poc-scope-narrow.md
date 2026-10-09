# Decision: NARROW (not Go, not Pivot)

**Date recorded:** 28 August 2026 · **Status:** `EXECUTED` · **Owner:** joint

---

## The decision in one line

> **The resource *scope* is refuted; the approach is not.**

## What prompted it

The POC's central hypothesis returned a clean negative: zero static-field write/read overlap
at one-hop analysis depth, every candidate, every case. Two of five pre-registered gates
missed outright (ranking quality, execution saving at 0% against a 30% gate).

## The three options and why NARROW was chosen

| Option | Would have meant | Why not chosen |
| --- | --- | --- |
| **GO** | Proceed as designed | Two gates failed. Proceeding unchanged would be ignoring our own pre-registered rules |
| **PIVOT** | Abandon the resource-evidence pillar; restate the contribution around order evidence and certification alone | The pre-registered trigger did not fire — see below |
| **NARROW** ✅ | Keep the approach, refute the scope, make depth a committed parameter | The mechanism was identified precisely and is addressable |

## The pre-registered pivot conditions — neither fired

1. **If fewer than three of four cases had reproduced** in clean containers → the dataset
   pipeline becomes the first risk, reduce case scope before claiming readiness.
   *Four reproduced. Did not fire.*
2. **If the depth-2 ablation had also produced empty overlap** — the resource abstraction
   failing at every affordable depth → the resource-evidence pillar collapses.
   *FJ-02 moved rank 39 → 1. Did not fire.*

> **Narrow was therefore the correct decision under our own rules rather than the comfortable
> one.** That distinction is the whole defence of this decision.

## The evidence that made NARROW rather than PIVOT correct

The failure had an **identified mechanism**, not just an outcome. In FJ-02 the state-setter
writes `JSON.defaultTimeZone` at `DateParserTest.setUp@5`; the target reads it at
`TypeUtils.cast@536` — two hops down the call chain. At one-hop depth the write and the read
are invisible to each other.

The abstraction was **too shallow, not wrong in kind**. That is a fixable scope error, not a
refuted premise.

## What NARROW committed us to

1. **Analysis depth becomes a configurable, committed parameter** with declared defaults and
   reported precision cost — no longer a fixed constant
2. **The resource abstraction is no longer assumed sufficient on its own** — order-outcome
   history is retained as a first-class ranking signal, not an optional extra
3. **The fallback branch is now active, not hypothetical:** if resource recall stays weak,
   order evidence carries the ranking and resource events are used only to certify
   explanations — *and the contribution claim changes accordingly*
4. **Ablation infrastructure becomes a committed pillar**, not an incidental script
5. **Controlled fixture suite becomes committed scope**
6. **Team expands to three**, evaluation infrastructure as the third pillar

## What this decision does NOT license us to claim

- ❌ That depth-2 extraction works generally — **it moved one case**
- ❌ That static-field analysis is useless in general — n=4, and both subjects are JSON
  libraries built around global static configuration, the most favourable possible substrate

## Where the evidence lives

Decision record, pre-registered gates, raw logs and failure analysis: the POC evidence bundle
(cite the path/commit on the day). Summary: [[05-Testing/poc/poc-log]],
[[05-Testing/poc/raw-numbers]].

## The panel answer

*Q38 — "What decision did the POC produce?"*
> Narrow, not Go and not Pivot. Concretely: analysis depth becomes configurable and is
> committed; the resource abstraction is no longer assumed sufficient on its own, so
> order-outcome history is retained as a first-class ranking signal rather than an optional
> extra; and the fallback in the ladder — retain order evidence for ranking and use resource
> events only to certify explanations — is now an active branch rather than a hypothetical one.
