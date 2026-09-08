# What the POC Changed

*Four design changes follow directly from the result. Being able to point at these is the
strongest use of a negative finding — it converts "our hypothesis failed" into "our
hypothesis failed and here is what we did about it."*

---

## The four changes

| Change | Driven by | Status now |
| --- | --- | --- |
| **Analysis depth becomes a committed, configurable feature** with declared defaults and reported precision cost | The zero-overlap result and the depth-2 ablation | `COMMITTED` — [[07-Defense/decisions/depth-configurable]] |
| **Ablation infrastructure becomes a committed pillar**, not an incidental script | A single-case ablation was carrying the whole diagnosis | `COMMITTED` |
| **Controlled fixture suite becomes committed scope** | Real subjects will not produce multi-predecessor, budget-exhaustion or unsupported-resource cases on demand | `COMMITTED` — [[05-Testing/fixture-suite]] |
| **Team expands to three members**, evaluation infrastructure as the third pillar | The POC exposed evaluation as the binding weakness, not feature count | `PROPOSED` — approval pending, [[07-Defense/decisions/three-member-split]] |

## Two further changes to the claim itself

Beyond design, the POC changed **what we are allowed to say**:

1. **Order-outcome history is now a first-class ranking signal**, not an optional extra. The
   resource abstraction is no longer assumed sufficient on its own.
2. **The fallback branch is now active, not hypothetical.** If resource recall stays weak:
   order-outcome evidence carries the ranking, resource events are used *only* to certify
   explanations, and **the contribution claim changes accordingly** rather than being
   quietly retained.

That second point is the one to give when asked *"what are you least confident about?"* —
naming a real uncertainty **with its pre-registered fallback** is the answer that most
improves a panel's estimate of a team.

## Why this is the right response to a failed POC

The FAST guide's position: a failed assumption is not a failed project. What matters is
whether the revised project remains coherent and defensible.

The mapping to make explicit:

```
zero overlap at depth 1
    └─> mechanism identified (state moves through callees, not test bodies)
            └─> depth becomes a parameter, not a constant
                    └─> depth becomes an axis of the evaluation (RQ1)
                            └─> depth sweep replaces single-case ablation

single-case ablation carrying the diagnosis
    └─> evaluation infrastructure was the binding weakness
            └─> ablation harness becomes committed, not incidental
                    └─> third member owns it as a full pillar (removal test passes)

two harness defects producing clean-looking output
    └─> the harness is itself an object requiring validation
            └─> four-way instrumented/uninstrumented control becomes a
                committed testable requirement
```

## What we deliberately will NOT do with the remaining time

Stating this pre-emptively prevents the panel proposing it as an obvious fix we missed:

- **Add dynamic tracing** — weeks of work; belongs in FYP-I with an overhead budget attached
- **Scale to eight or ten cases** — depth of evidence per case is what matters now, not count
- **Re-run the exhaustive scan** — the single-scan protocol means three of the five
  outstanding items run offline against data we already hold

## Outstanding work before the defence

Five items. Three run **offline against data we already hold** and require no re-scanning.

| # | Work | Gap it closes | Owner |
| --- | --- | --- | --- |
| 1 | **Depth sweep** at depths 1, 2, 3 and unbounded across all four reproduced cases, reporting rank of the true polluter **and overlap-set size** at each depth | Replaces a single-case ablation with a 4×4 matrix. Overlap-set growth is the point: if precision collapses at depth 3 through shared utility code, "there is an optimal depth" becomes a real tuning result | M1 |
| 2 | **Per-case cause classification** for the three non-moving cases: depth-limited, reflection-mediated, wrong resource family, or multi-predecessor | Converts "the signal was empty" into four named reasons. The multi-predecessor case matters most — it would mean our **pairwise design**, not our signal, was the limitation | M1 |
| 3 | **Oracle ceiling and alternative rankings**, computed offline: perfect-knowledge ranking, positional score, class-locality, setup-writer heuristic | The oracle states what the prize is worth. If any cheap ranking beats one-by-one, the finding becomes "cheap ranking is viable, our feature choice was wrong" | M3 |
| 4 | **One out-of-domain subject** — non-JSON, one case, hard-capped effort | All four reproduced cases came from one library. Our setup required ≥2 projects; jsoniter returned zero. **This is currently single-project evidence** | M3 |
| 5 | **Instrumentation non-perturbation check** — same order 10× under our runner and 10× under unmodified Surefire, signatures compared | Answers "how do you know your tool did not create the failure" with **measurement rather than assertion** | M2 |

Plus two documentation items from [[07-Defense/weak-points]] that should be done first
because they are cheap and dangerous if left:

| Work | Owner |
| --- | --- |
| Reconcile victim/brittle classification vs reproduction count in the write-up | M3 |
| Audit CDR wording for consistency across slide deck, proposal doc and Rev 2 | Joint |

## The line to have ready

*If asked "your POC failed, should we not defer this proposal?"*

> The POC tested the assumption whose failure would have been most expensive to discover in
> FYP-II, and it found the failure in one day rather than in six months. It produced a
> specific mechanistic diagnosis, a design change we have committed to, and two harness
> defects that would have corrupted every later measurement.
>
> The condition for deferral in the guide is that feasibility has not been established. We
> reproduced cases in clean containers across the stated go/no-go gate, and we established
> that our harness measures what it claims to measure. What we have **not** established is
> that resource guidance helps at an affordable depth — and that is the question the project
> exists to answer.
