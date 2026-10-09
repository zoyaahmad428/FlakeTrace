# Contemporary Comparison

*What each nearest system demonstrably already does — so that no part of it is inadvertently
claimed — and what remains open.*

> **The non-negotiable instruction:** do not defend *"we uniquely find a minimal polluter
> sequence and explain shared state."* iFixFlakies already minimises relevant test orders;
> RankF already ranks OD-relevant tests; Takuan already explains passing/failing state
> differences. Defend the **complete evidence-certified, budget-constrained product** and
> prove its incremental value.

---

## Research systems

| System | What it already does (published) | What remains open | Our position |
| --- | --- | --- | --- |
| **iDFlakies** [3] | Detects flaky tests by reordering and rerunning; partially classifies OD vs NOD; dataset of 422 flaky tests, **50.5% OD**; establishes valid-order constraints and the class-then-method randomisation strategy | Does not locate the OD-relevant test, explain the shared state, or bound its own execution cost | **Input source and order-generation convention — not a competitor.** We do not claim generic OD detection as any part of our contribution |
| **iFixFlakies** [4] | Delta-debugging Minimizer finds polluters and state-setters; discovers cleaners; Patcher synthesises minimal patches from helpers | No budget model; no statistical replay statement; no resource-level explanation; cleaners **not guaranteed to exist**; minimiser is 1-minimal only and not guaranteed to find all polluters | **Baseline.** Run its minimiser on the overlapping reproducible subset; compare success, test invocations, wall time |
| **RankF** (RankFL / RankFO) [5] | Ranks candidates by likelihood of being OD-relevant; **155 OD tests, 34 modules, 24 projects**; medians **9.4–14.1 s** to first OD-relevant test vs **34.2–118.5 s** for baselines; RankFO ranking cost <100 ms | Excludes joint multi-test dependence; RankFO **requires prior test-order data**; Rank-1 stability needs **86–206 orders** vs the 20 used; **the authors themselves name dynamic execution traces as the unexploited information source** | **Baseline, and our strongest one.** Our signal differs *in kind*: theirs is static suite properties, ours is execution-collected resource overlap. The two are combinable |
| **Takuan** [6] | Compares Daikon dynamic invariants between passing and failing orders; handles **external state such as the file system** that prior work could not; derives reset-method searches | **Preliminary evaluation only** (13 tests, correct problem invariants for 6); produces an explanation, not a budgeted verified replayable artefact; no abstention model; no cost accounting | **Baseline for explanation.** Difference is correlation vs **intervention** |
| **PolDet** [9] / **ElectricTest** [10] | Detect state pollution and inter-test dependencies from heap and filesystem observation; provide access paths and stack traces as evidence | PolDet's **324 reported / 194 relevant** split shows state difference alone is not causal proof; ElectricTest's **~20× overhead** bounds CI deployability | Evidence for two of our own design positions: overlap is a **prior, not proof**; overhead must be **measured, not assumed** |
| **ODRepair** [7] / **FlakyDoctor** [8] | Generate cleaning code where no cleaner exists; neuro-symbolic LLM repair, **57% on 332 OD tests**, exceeding ODRepair by 12% and iFixFlakies by 17% | Repair, not diagnosis — both operate **downstream of a known OD-relevant test**. Overfitting literature requires suggestions be execution-validated and non-authoritative | **Repair baselines.** FlakyDoctor establishes that LLM repair is **not itself novel** |

## Commercial products

**Trunk Flaky Tests · Tuist · Gradle Develocity** — all detect, track, group, retry and
quarantine flaky tests competently. That ground is taken and well-funded; **do not compete on
dashboards.**

> **None of their published documentation describes returning a verified, replayable order
> plus a resource-level evidence path for a specific order-dependent failure, at a measured
> confidence.**

⚠ **Phrasing discipline:** claim only that *their published documentation does not describe
it*, and that you validated the residual workflow need with users. **Never** claim commercial
products *cannot* do this.

Stakeholder corroboration (SH1): existing tooling is *"much weaker at explaining why a failure
is intermittent… they normally do not automatically tell us that Test A modified some shared
state that caused Test B to fail 30 tests later."*

---

## What the state of the art leaves open

Synthesising the above:

- ✅ Minimisation of a reproducing order — **solved** [4], [11]
- ✅ Ranking of OD-relevant tests — **solved** for the single-test case, both learned and history-based [5]
- ✅ Shared-state explanation — **demonstrated at preliminary scale** [6], [9]

**What no cited system provides is a single artefact that:**

1. allocates a **declared execution budget** between search and verification
2. carries **statistically qualified replay evidence** rather than a bare answer
3. links candidate, resource and target through **interventions whose outcomes are recorded**
4. **abstains with a typed reason** when the budget cannot support the declared verification contract

## Our defensible increment — the sentence that must survive every row above

> The design and evaluation of a **cost-aware evidence-certification workflow** that combines
> established components — ranked candidate search, delta-debugging minimisation, bounded
> resource-event evidence and repeated-replay interval estimation — under an explicit
> execution budget, a declared failure-equivalence rule, an intervention-backed provenance
> chain, a typed abstention, and a replay contract a third party can independently check on a
> clean machine.
>
> **Novelty is claimed for the composition, the budget allocation policy, the certification
> contract and the empirical evaluation of these against current baselines — not for any
> constituent technique.**

## The honest statement of overlap — say this first, do not wait

> Every one of the six research tools above overlaps with part of our claim. We do not dispute
> this. Our position is that each becomes a **baseline in our evaluation**, and that the
> combination of budget-awareness, typed abstention and intervention-backed certification is
> not offered by any of them.

## Never claim as ours

The following are **not project inventions** and must never be defended as such:

- the victim / brittle / polluter / state-setter / cleaner **vocabulary** [4]
- **delta-debugging minimisation** and its 1-minimality property [11], [4]
- **ranking** of OD-relevant tests [5]
- **dynamic shared-state explanation** [6], [9]
- **cleaner-based or generated repair** of OD tests [4], [7], [8]

## If the panel produces a paper published last month that does exactly this

> Then we would treat it the way we treated RankF and Takuan when we found them: add it as a
> baseline, restate what remains of our delta, and if nothing measurable remains, **rescope
> before the scope freeze rather than after**. That is written into our risk register as the
> nearest-work-overlap risk with rescoping as the trigger.
>
> We would also ask to see it, because our comparison was frozen on [date] and we would rather
> learn it now than at Final-2.

**Do not get defensive. A panel asking this is testing composure and honesty, not knowledge.**
