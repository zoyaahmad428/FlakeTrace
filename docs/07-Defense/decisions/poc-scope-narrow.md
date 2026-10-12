# Decision: NARROW (not Go, not Pivot)

**Date recorded:** 28 August 2026 · **Status:** `EXECUTED` · **Owner:** joint

---

## The decision in one line

> **The resource *scope* is refuted; the approach is not.**

## What prompted it

The POC's central hypothesis returned a clean negative: zero static-field write/read overlap
at one-hop analysis depth, every candidate, every case. **Three of five pre-registered gates
missed outright** (`POC/decision/decision_record.md`, §2): ranking quality and execution
saving (0% against a 30% gate) --- both caused by the depth-1 scope, the mechanism this
document is about --- and reproduction yield (fastjson 4/4, jsoniter 0/4), a **separate**
structural failure explained in the decision record §3(c) (a Surefire suite-context artefact,
unrelated to analysis depth). Corrected 2026-10-12: an earlier revision of this file said
"two of five," omitting the yield gate; the decision record's own pre-registered gate table
has always shown three `BELOW` verdicts.

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

**This NARROW decision (2026-08-28) is a historical record and stands unchanged** --- it is not
retracted or overwritten by later work. The scope changes it committed to (depth as a
configurable parameter, order-outcome history as a ranking signal, the controlled fixture
suite) were acted on, and a later, separate held-out validation
(`POC/decision/decision_record_v3.md`, 2026-09-04, pre-registered protocols `definitions_v2.md`
and `prereg_heldout2.md`) re-ran all five gates under the corrected scope against fresh,
previously-unseen fastjson cases and passed all five. That later result does not change what
happened on 28 August or why NARROW was the correct call under the rules in force that day ---
it is the evidence that NARROW's bet paid off, not a correction to this record.

## The panel answer

*Q38 — "What decision did the POC produce?"*
> Narrow, not Go and not Pivot. Concretely: analysis depth becomes configurable and is
> committed; the resource abstraction is no longer assumed sufficient on its own, so
> order-outcome history is retained as a first-class ranking signal rather than an optional
> extra; and the fallback in the ladder — retain order evidence for ranking and use resource
> events only to certify explanations — is now an active branch rather than a hypothetical one.
