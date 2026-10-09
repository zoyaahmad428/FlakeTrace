# iDFlakies — Lam, Oei, Shi, Marinov, Xie (ICST 2019)

**Role for us:** `INPUT SOURCE` and order-generation convention — **not a competitor.**
**Ref:** [3]

---

## What it does

Detects flaky tests by **reordering and rerunning** tests, and partially classifies them as
likely OD or NOD by checking various test orders.

A **Maven plugin** for Java projects using JUnit, offering five run configurations: the base
configuration reruns the original order many times; the others reorder using random orderings
or by reversing the original order.

## Dataset

Built a dataset of **422 flaky tests**: **50.5% order-dependent**, 49.5% not.

→ Direct evidence that **order dependence is not a marginal category in practice**. Use this
when asked "is this problem big enough?"

## Two constraints we adopt without modification

These come from this paper and govern how a suite may **legitimately** be shuffled:

1. **Random orderings must not interleave test methods from different test classes** — such an
   ordering **would not be produced by popular frameworks such as JUnit**. Rahman et al.
   explicitly ensure their generated orders are valid in this sense.
2. **Randomise test classes first, then methods within each class** — iDFlakies' study found
   this detects the most flaky tests overall.

> A shuffling strategy ignoring either constraint produces orders that are either **unreachable
> in production** or **less effective**. A panel is entitled to ask which of the two errors a
> candidate tool commits — know that we commit neither.

Also the source of our **20-order** choice for order-history evidence: Rahman et al. chose 20
to match the number suggested by iDFlakies.

## IDoFT — the dataset, and why it is amber

The **Illinois Dataset of Flaky Tests** consolidates the findings of the iDFlakies line of
work. Standard public catalogue of projects, SHAs, modules, test names and categories. [37]

> **It is a source catalogue, not proof that cases build, contain resource-level ground truth,
> or are legally redistributable.**

This is precisely why dataset readiness is marked **amber** and not green. See
[[07-Defense/weak-points]] §7.

Our POC started from IDoFT's `pr-data.csv` — 8,075 rows → 1,438 after filtering to OD
categories with usable status.

## The answer (Q16)

> iDFlakies detects and partially classifies flaky tests through reordered executions. It
> answers *"is this test order-dependent."* **We start after that question is answered** — our
> input is a known order-dependent failure.
>
> So iDFlakies is an **input source and a metadata source** for us, not a competitor, and we
> **do not claim generic order-dependence detection as any part of our contribution.**

## What remains open

Does not locate the OD-relevant test, explain the shared state, or bound its own execution cost.
