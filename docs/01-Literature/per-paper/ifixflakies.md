# iFixFlakies — Shi, Lam, Oei, Xie, Marinov (ESEC/FSE 2019)

**Role for us:** `BASELINE` — the minimisation baseline. Also the source of our core vocabulary.
**Ref:** [4]

---

## What it does

A framework for **automatically fixing** order-dependent flaky tests.

- **Minimizer** — applies delta debugging to the tests preceding the OD test in a failing (or
  passing) order, to find **polluters** for a victim and **state-setters** for a brittle
- **Cleaner discovery** — finds tests that, run between polluter and victim, reset the shared
  state. Falls back to OBO where delta debugging is inapplicable
- **Patcher** — minimises statements within an identified helper, again via delta debugging,
  yielding the minimal statement set to add to the OD test

**Core insight:** helpers — cleaners for victims, state-setters for brittles — *already
contain* the logic to set or reset the shared state, so a patch can be synthesised from them.

## What it gave the field (and therefore is NOT ours)

**The vocabulary.** Victim, brittle, polluter, state-setter, cleaner — fixed by this paper.
Rahman et al. collectively term polluters, state-setters and cleaners the **OD-relevant tests**.

**The classification protocol.** Type is determined by running the OD test by itself: passing
alone → victim; failing alone → brittle. *This is the direct basis for our isolation stage.*

**Repeated isolation.** The Minimizer explicitly loops a RERUN parameter over isolation and
raises an exception if the outcome is inconsistent with an OD classification — the basis for
our "repeat, don't trust a single outcome" rule.

## Distribution finding we rely on

Of 110 OD tests: **100 victims, 10 brittles**. Rahman et al.'s later reproduced set of 155 is
**135 victims / 20 brittles**.

→ Our emphasis on the victim/polluter case is **proportionate to the observed population**,
not an arbitrary simplification. The brittle/state-setter case is retained because it is 13%
of the most recent reproduced population.

## Published limitations — the space we can occupy

| Limitation | Source | What it lets us claim |
| --- | --- | --- |
| Produces **1-minimal**, not globally minimal, orders | delta debugging's property [11] | We report 1-minimal and **never say "minimum" unqualified** |
| **Does not necessarily find all polluters** in a prefix | Wei et al. [28] | Deletion checks on every returned order, not trust in the minimiser |
| **Cleaners are not guaranteed to exist** — relies on developers having already written the cleaning logic | stated by ODRepair's authors [7] | Repair via cleaner-harvesting has a structural ceiling |
| Cleaner discovery is **conditional** — needs a passing order where the polluter runs before the victim, else falls back to OBO over the whole passing order | Rahman et al. [5] | Cost is not uniformly lower than OBO |
| **No budget model** | — | Budget as a first-class input is open |
| **No statistical replay statement** | — | Verification with an interval is open |
| **No resource-level explanation** | — | Provenance path is open |
| **No abstention** | — | Typed refusal is open |

## Cost data (from Rahman et al.'s measurement)

- Delta debugging: **166.5 s average / 34.2 s median** to first polluter
- But **251.7 s average for cleaners**
- In their motivating example: delta debugging **419.0 s** vs OBO **60.9 s**

> **Delta debugging is not uniformly cheaper than OBO** — a nuance our evaluation must
> preserve rather than flatten.

## What we add on top — the four things (Q13)

1. **Active budget allocation** — next experiment chosen by expected information gain per
   estimated cost, not a fixed schedule
2. **Bounded resource provenance** — output names the write, the resource identifier, the read
3. **Statistical verification** — repeated clean-container replay with an interval
4. **Typed abstention** — inconclusive returns a reason, not a guess

> **The measurable claim is a cost claim:** at the same isolation-success level, fewer
> test-method invocations to a verified result.

## Evaluation plan against it

Run the **iFixFlakies minimiser** on the overlapping reproducible subset. Compare success
rate, test invocations, wall time. `STATUS: not yet run — Final-1 exit condition.`
