# One-Minute Answers

*The compressed set. Everything here should be sayable from memory, in under a minute, by any
of the three members.*

Print this. Carry it. It is the last thing you read before walking in.

---

## The problem (Q1)

> When a Java test passes in isolation but fails after other tests have run, developers can
> usually detect that the instability exists but still have no bounded, reproducible,
> evidence-producing way to identify which earlier test interaction caused it and decide what to
> inspect next.

## The pitch (Q102)

> Java teams run automated test suites in CI. A test passes alone and fails after other tests
> because an earlier test left shared state behind. Developers can detect the instability but not
> diagnose it — they rerun, reorder and comment tests out by hand, and most often quarantine the
> test, which removes coverage permanently.
>
> Commercial tools detect and quarantine well; research tools separately minimise orders, rank
> relevant tests or explain state differences. None returns a bounded, verified, replayable
> diagnosis with an evidence path and an honest refusal.
>
> FlakeTrace takes a pinned project, a target test and an execution budget, runs controlled order
> experiments, and returns a verified certificate — the interfering test, the shared resource,
> the bytecode locations, a replay command and a reliability interval — or a typed unresolved
> result.

## The contribution (Q29) — verbatim

> Existing products mainly detect, track or quarantine flaky tests, while research tools
> separately detect and classify order dependence, minimise relevant test orders, rank
> order-dependent relevant tests or compare dynamic invariants. FlakeTrace contributes a
> self-hosted, budget-aware active-diagnosis pipeline that combines bounded resource-event
> evidence with controlled interventions and returns a statistically verified replay certificate
> or an explicit abstention, evaluated against current research baselines on a frozen,
> project-separated Java benchmark.

## The CCP (Q24)

> Given a known order-dependent Java test failure, produce evidence that is reproducible on
> another machine, minimal under a declared rule, causally supported by an observed
> shared-resource interaction, and statistically characterised — while the search is bounded by a
> fixed execution budget, the instrumentation must not itself change the behaviour under study,
> and the system must refuse to answer rather than answer wrongly when the evidence does not
> support a conclusion.
>
> **That is one problem, not several. Every clause competes with every other one.**

## The POC result (Q35)

> Negative, at that scope. Across the reproduced cases there was zero write-read overlap between
> candidate tests and the victim at one-hop resource scope. Because the overlap score was empty
> for every candidate, the ranked strategy produced an ordering byte-identical to original-order
> one-by-one, and the execution saving was exactly zero percent against a gate of thirty percent.
> Two of five pre-registered gates were missed outright.

## The sentence that survives everything failing (Q31)

> That an order-dependent failure can be turned into an artefact another engineer can replay on a
> clean machine and audit, or an honest refusal — and that we measured what that costs relative
> to the current best research tools.

## Least confident about (Q107)

> Whether resource evidence earns its complexity at a depth we can afford to instrument. Depth
> increases recall and increases both analysis cost and over-approximation, and we have one case
> suggesting depth two matters and no evidence about where the curve turns.
>
> The reason it is survivable is that the fallback is pre-registered: if resource recall stays
> weak, order-outcome evidence carries the ranking and resource events are used only to certify
> explanations — and the contribution claim changes accordingly rather than being quietly
> retained.

## If the POC failed, should we defer? (Q106)

> The POC tested the assumption whose failure would have been most expensive to discover in
> FYP-II, and it found the failure in one day rather than in six months. It produced a specific
> mechanistic diagnosis, a design change we have committed to, and two harness defects that would
> have corrupted every later measurement.
>
> The condition for deferral is that feasibility has not been established. We reproduced cases in
> clean containers across the stated go/no-go gate, and we established that our harness measures
> what it claims to measure. What we have not established is that resource guidance helps at an
> affordable depth — and that is the question the project exists to answer.

## Will you beat RankF? One word. (Q105)

> I would rather not give a one-word answer, because the honest answer has a condition attached.
> On ranking accuracy alone, we may not — RankF is validated at a far larger scale than we will
> reach. Our claim is about cost to a verified, replayable result under a budget, which RankF
> does not produce, and about whether resource evidence adds anything on top of RankF's signals,
> which is an open question we have committed to answering either way.

## The Java stakeholder gap — volunteer this

> The interviews validate the problem shape, not the technology scope, and we separate those
> deliberately. All three independently described manual binary-search isolation with no tooling
> support; two said a confident wrong answer is worse than a stated unknown; two said source
> cannot leave their infrastructure. Those are the three design commitments the product is built
> on, and they are ecosystem-independent.
>
> What the interviews do not establish is that Java teams specifically have this problem, and we
> do not claim they do on this evidence. That rests on the published record — IDoFT's catalogue,
> RankF's 155 reproduced OD tests across 24 Java projects, iFixFlakies' corpus. Java is where the
> reproducible public evidence is, which is why the benchmark and the product are Java.

---

## Four phrases that cost you the room

| ❌ Never | ✅ Instead |
| --- | --- |
| "minimum" | **"1-minimal"** / "deletion-minimal" |
| "automatically fixing" (CDR) | **"ranked remediation options a human applies"** |
| "commercial products can't do this" | **"their published documentation does not describe it"** |
| "the dataset is ready" | **"amber, deliberately — a catalogue is not a benchmark"** |

Plus: never say **"calibrated"**, never present the Wilson interval as the probability the
diagnosis is correct, never say **"mixed"** or **"inconclusive"** about the POC, and never say
you have **"studied"** a baseline when you mean you read the paper.

## The answer discipline

> **Answer. Evidence. Limitation. Stop.**
>
> Panels punish the fourth sentence far more often than they punish the missing one.

## And the one that ends careers

> **"That's X's part."**
>
> Answer at the level you can, *then* offer that the owner can add detail.
