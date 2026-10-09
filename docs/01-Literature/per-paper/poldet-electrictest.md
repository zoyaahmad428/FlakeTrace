# PolDet, ElectricTest — shared-state detection and the overhead problem

**Role for us:** evidence for two of our own design positions — overlap is a **prior, not
proof**, and overhead must be **measured, not assumed**. Refs: [9], [10], [34]

---

## PolDet — Gyori, Shi, Hariri, Marinov (ISSTA 2015) [9]

**What it does:** finds tests that modify a location on the **heap shared across tests** or on
the **file system**. Captures heap state before a test's setup and after its teardown and
compares under a common-root isomorphism, **disregarding private fields and local variables
because other tests cannot access them**. Additionally monitors the file system.

**Reports as evidence:** an **access path through the heap** to the polluted value, or the
**name of the modified file**. *(This is the precedent for our certificate's resource path.)*

### The finding that shapes our claim language

**26 projects, 6,105 tests → 324 polluting tests reported → manual inspection judged 194 to be
relevant pollutions** that could easily affect other tests.

> **324 reported / 194 relevant is direct evidence that a shared-state signal is a ranking
> prior and an explanation aid — NOT a proof of causation.**

This is precisely why our certificate says **"evidence-supported interference path"** rather
than **"proven root cause"**, and why *definitive causality* is an explicit exclusion. Our
language is a **response to that measured imprecision**, not defensive hedging.

Also: the committed resource families (static fields, system properties, filesystem paths) are
**precisely the families for which the literature demonstrates tractable, inspectable evidence
extraction**.

---

## ElectricTest — Bell, Kaiser, Melski, Dattatreya (ESEC/FSE 2015) [10]

**What it does:** detects dependencies between test cases by **monitoring test execution**, and
reports **the code with stack trace** that causes a dependency.

### The overhead number that bounds deployability

> **ElectricTest added on average a 20× slowdown when soundly detecting dependencies.**

A reimplementation of PolDet over Java PathFinder reported **1.43× overhead relative to base
JPF** — though base JPF is itself an expensive substrate [34].

### Why this matters more than it looks

**The probe changes the phenomenon.** Because flaky outcomes are sensitive to execution
conditions — Luo et al. found **85% of Async Wait cases manifested by adding a single time
delay** — an instrumentation layer heavy enough to change timing **can create or suppress the
very failure being diagnosed.**

**We have our own instance of this.** The POC's timezone override erased the phenomenon
entirely. That is why the four-way control is **committed rather than aspirational**:

> For every case: passing order and failing order, each **uninstrumented and instrumented**,
> with all four outcomes required to match expectation before any measurement is accepted.

And why the NFR is **median and p95 overhead measured against uninstrumented execution,
reported as a metric rather than asserted.**

---

## Also in this space

**Gambi, Bell, Zeller** — practical test dependency detection (ICST 2018) [38].

---

## The static/dynamic split this evidence justifies (Q56)

| | Strength | Weakness | We use it for |
| --- | --- | --- | --- |
| **Static bytecode analysis** | cheap, no runtime overhead, no perturbation risk | **over-approximates** — reports every reference on every path, including paths not taken | **candidate generation**, where over-approximation is acceptable because the confirmation step filters it |
| **Dynamic collection** | precise about what actually happened | costs overhead, **can perturb** | **evidence in the certificate**, where precision is required because we assert a specific write reached a specific read |

**The static-only and dynamic-only ablations measure whether that split is justified.**
