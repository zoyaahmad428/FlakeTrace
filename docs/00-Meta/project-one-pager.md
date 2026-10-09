# FlakeTrace — Project One-Pager

*If you read one file in this vault before the defence, read this one. Everything here you
must be able to say aloud without notes.*

---

## The problem in one sentence (technology-free)

> When a Java test passes in isolation but fails after other tests have run, developers can
> usually detect that the instability exists but still have no bounded, reproducible,
> evidence-producing way to identify which earlier test interaction caused it and decide
> what to inspect next.

Three things follow from that sentence, and they define the whole project:

- **The input is a known failure, not an unknown one.** We do not do detection.
- **The output is evidence, not a fix.** Repair is gated and optional.
- **The process is bounded.** An unbounded search is what developers already do by hand.

## What the thing actually does

You give it: a pinned Maven repo + commit, a module, a target test, and an **execution
budget**. It runs controlled test-order experiments and returns one of:

| Outcome | Meaning |
| --- | --- |
| **Verified** | Sequence passed deletion checks, met the replay threshold, and carries a resource path in a supported family |
| **Candidate** | Reproducing sequence that replays, but a certification requirement is unmet — usually the resource path is missing or unsupported. *"We can tell you what to run but not why it fails."* |
| **Unresolved** | No sequence meets the acceptance rule, with a **typed reason** |

The four abstention reasons: **unsupported resource**, **budget exhausted**, **unstable
build**, **inconsistent outcomes**. Each maps to a different next action for the developer —
that is the point of typing them.

## Vocabulary (fixed by Shi et al., not ours)

- **Victim** — passes alone, fails after a predecessor
- **Polluter** — the predecessor that broke it
- **Brittle** — fails alone, needs a predecessor to set state up
- **State-setter** — the predecessor a brittle test depends on
- **Cleaner** — a test that, run between polluter and victim, resets the state

Distribution matters for scope: Shi et al. found 100 victims vs 10 brittles out of 110 OD
tests; Rahman et al.'s 155-case set is 135 victims / 20 brittles. Emphasising victims is
proportionate to the observed population, not an arbitrary simplification.

## The complex computing problem (CCP)

> Allocating a finite execution budget across competing diagnostic actions under
> uncertainty, and knowing when the evidence does not justify a claim.

Stated fully: produce evidence that is reproducible on another machine, minimal under a
declared rule, causally supported by an observed shared-resource interaction, and
statistically characterised — while the search is bounded by a fixed budget, the
instrumentation must not change the behaviour under study, and the system must refuse to
answer rather than answer wrongly.

**That is one problem, not several. Every clause competes with every other one.**

We claim **seven of nine** Seoul Accord characteristics. We do **not** strongly claim
"diverse stakeholders" — our three user groups have overlapping rather than conflicting
success criteria, and that is the most commonly over-claimed characteristic.

## Contribution statement (verbatim — memorise this)

> Existing products mainly detect, track or quarantine flaky tests, while research tools
> separately detect and classify order dependence, minimise relevant test orders, rank
> order-dependent relevant tests or compare dynamic invariants. FlakeTrace contributes a
> self-hosted, budget-aware active-diagnosis pipeline that combines bounded resource-event
> evidence with controlled interventions and returns a statistically verified replay
> certificate or an explicit abstention, evaluated against current research baselines on a
> frozen, project-separated Java benchmark.

Three properties we defend — **not** "we fix flaky tests":

1. **Budget as a first-class input** — spends a declared number of invocations and stops
2. **Typed abstention** — insufficient evidence produces a named reason, not a guess
3. **Intervention-backed evidence** — supported by counterfactual execution, not only static inference

**Contribution type:** primarily *system and architecture*, secondarily *method*. We are
**not** claiming algorithmic novelty and the guide does not require it.

## The POC — lead with this, do not bury it

Executed 25–28 August 2026. **The headline result was negative.**

| What | Number |
| --- | --- |
| Targets built across 2 real projects | 8 |
| Reproduced in clean containers | 4, at 10/10 replay |
| Controlled orders run | 2,606 (5,212 test-method invocations) |
| Static-field write/read overlap at depth 1 | **Zero for every candidate in every case** |
| Execution saving vs one-by-one | **0%** against a 30% gate |
| Depth-2 ablation on FJ-02 | True polluter moved **rank 39 → rank 1** |

Decision recorded: **NARROW** — the resource *scope* is refuted, the approach is not.

Two harness defects found and corrected (both would have fabricated results):
1. **182 false polluters** — runner lacked jsoniter's JUnit suite context; count fell to 0
2. **Timezone override erased the phenomenon** — `TZ=Asia/Shanghai` made the state-setter's write a no-op

See [[05-Testing/poc/poc-log]] for the full account, [[05-Testing/poc/what-changed]] for
consequences, [[07-Defense/decisions/poc-scope-narrow]] for the decision record.

## Prior art — six systems overlap with us, and we say so first

| System | What it already does | Our position |
| --- | --- | --- |
| iDFlakies | Detects/classifies OD via reordering | Input source, not competitor |
| **iFixFlakies** | Delta-debugging minimiser, cleaners, patches | **Baseline** |
| **RankF** | Ranks OD-relevant tests, 155 cases / 24 projects | **Baseline** |
| **Takuan** | Explains via dynamic invariants | **Baseline** for explanation |
| ODRepair | Generates cleaners via test generation | Repair baseline |
| FlakyDoctor | LLM repair, 57% on 332 OD tests | Repair baseline |

**Never defend:** "we uniquely find a minimal polluter sequence and explain shared state."
All three of those are taken. Defend the complete evidence-certified, budget-constrained
product. See [[01-Literature/contemporary-comparison-table]].

## Architecture — eight components

`Project adapter → Sandbox runner → Evidence collector + Outcome normaliser →
Test–resource graph → Planner → Minimiser → Verifier → Certificate generator → CLI/CI`
(plus gated CDR)

**The interdependence to name:** the planner's budget decisions change what the collector
observes, which changes the graph, which changes the planner's next decision. That loop is
why this is one project and not three.

## Ownership

| Member | Owns | If removed |
| --- | --- | --- |
| 1 | Resource evidence: static/dynamic collection, attribution, graph, certificate evidence path | Certificate has no evidence path — degrades to "this order reproduces", which iDFlakies already gives |
| 2 | Bounded search & verification: runner, budget, planner, minimiser, verifier, CLI/CI | No bounded diagnosis, no reliability guarantee, no deployability |
| 3 | Evaluation infrastructure: manifest, independent baselines, ablation harness, metrics, fixtures, reproducibility bundle (+ gated CDR verification) | Algorithm with no trustworthy evidence it works |

**Every member must be able to explain subsystems they do not own.** Deferring — *"that's
X's part"* — is the single most damaging answer available in a defence.
See [[07-Defense/ownership-map]].

## Status right now

- **Stakeholder evidence:** 3 interviews complete — but see the Java gap in [[07-Defense/weak-points]]
- **POC:** executed, NARROW recorded, 5 outstanding items before defence
- **Dataset:** amber, deliberately. IDoFT is a catalogue, not a benchmark
- **Team:** expanded 2 → 3; departmental approval pending
- **Implementation:** not started, and correctly so
