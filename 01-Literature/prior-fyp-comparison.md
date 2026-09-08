# Prior FAST FYP comparison

**Scope of check:** departmental FYP repository, **Fall 2019 – Fall 2025, 989 projects.**
**Result:** no near-duplicate found.

---

## Method — say this, because "did you search systematically or just look at titles?" is Q23

> **Systematically.** We swept all ~989 project records across Fall 2019 to Fall 2025 for
> **testing, flakiness, test-order, CI and debugging** terms, then **read the full record for
> every hit** rather than the title. Three entries survived as structurally comparable and are
> in the comparison table; the rest are recorded as screened out **with the reason**.

## The three structurally comparable entries

| Project | What it does | Structural difference — **not cosmetic** |
| --- | --- | --- |
| **F22-032-D-ETesting** | Automated exploratory testing | **It generates tests. We consume an existing suite and diagnose an interaction within it.** |
| **F22-033-D-WebSPLAT** | Reusable functional testing for web software product lines | **It reuses tests across product-line variants. Our unit of analysis is the ordering relation between tests in one suite.** |
| **S25-049-D-TestML** | ML-supported test generation, optimisation and defect prediction | **It is broad and feature-oriented. We are deliberately narrow: one budgeted diagnosis problem, one replayable evidence artefact as output.** |

**If pressed on TestML specifically:**
> The difference is that a broad ML-supported testing platform has **many features and no
> single central trade-off**, whereas our entire project is **one trade-off** — evidence
> quality against execution budget.

The nearest other neighbours are general test-automation and CI-tooling projects — none
addresses order-dependence, budgeted diagnosis or evidence certification.

## What we explicitly do NOT claim (Q22)

> **We do not know that no previous FYP did this internally, and we do not claim it.** A
> title-and-summary repository cannot prove that no internal module overlapped.
>
> What we **can** state is that **the supplied repository summaries do not describe an
> order-dependent polluter and resource certificate** — and that is the exact wording we use.

**If reports or demonstrations for the three closest projects are available to us, we will
inspect them and record the result.** `STATUS: not yet done — offer it, do not claim it.`

---

## Why this matters for the guide's requirements

Prior-FYP comparison is a named approval condition. Having done it **systematically and
recorded the screen-out reasons** converts it from an assertion into evidence — and having a
precise limit on what the check can prove (B10 in [[07-Defense/claims-ledger]]) is what
distinguishes it from an overclaim.
