# Certification, interval estimation and abstention

*The intellectual basis for FlakeTrace's central output is not drawn from the testing
literature but from algorithmics and statistics. This is the section that explains why the
output is called a **certificate**.*

---

## McConnell, Mehlhorn, Näher, Schweitzer — "Certifying algorithms" (Computer Science Review, 2011) [20]

**Definition:** a **certifying algorithm** produces, with each output, a **certificate or
witness** — an easy-to-verify proof that the particular output has not been compromised by a
bug.

The model: user supplies input *x*, receives output *y* **and certificate *w***, and checks —
manually or by program — that *w* proves *y* is a correct output for *x*. **In this way the
user can be sure of the output's correctness without having to trust the algorithm.**

The authors advance the thesis that certifying algorithms are **superior** to non-certifying
ones, and that **for complex algorithmic tasks only certifying algorithms are satisfactory**.

> **The model presumes a checker that can also REJECT.** This is the principled basis for
> typed abstention.

### The mapping onto FlakeTrace — exact, and the reason we say "certificate"

| Certifying-algorithm model | FlakeTrace |
| --- | --- |
| Input *x* | pinned commit, module, target test, budget |
| Output *y* | classification and replay order |
| **Witness *w*** | the evidence bundle: deletion-minimality checks, counterfactual outcomes for each retained predecessor, resource-event path, repeated-replay record |
| **Checker** | **a third party re-running the emitted replay command on a clean machine** |

> A diagnosis a developer cannot independently re-verify is, in this framing, **exactly the
> non-certifying output the model argues against.**

This is also why the **environment must be recorded in the certificate** — a certificate that
does not record the environment in which the evidence was obtained **cannot be checked by a
third party**.

---

## Brown, Cai, DasGupta — "Interval estimation for a binomial proportion" (Statistical Science, 2001) [22]
## Wilson — the score interval (JASA, 1927) [21]

**The problem:** a returned order may reproduce the target failure only probabilistically, so
a bare success count is not an adequate reliability statement.

**Their finding:** the **chaotic coverage properties of the standard Wald interval are far more
persistent than is appreciated**, and common textbook prescriptions about its safety are
**misleading and cannot be trusted**.

**Their recommendation:** on coverage and expected length — **Wilson** or equal-tailed
**Jeffreys** for small *n*; Agresti–Coull for larger *n*.

### Why this governs our case

> Verification budgets in this setting are **small by construction** — tens of replays, not
> thousands. The small-*n* case therefore governs, and Wilson is the recommended estimator for
> exactly that regime.

**The 20/20 problem, stated concretely:** at 20 out of 20 the normal approximation degenerates
to a point, **which would be a false statement.**

### What the interval means — and what it does NOT (Q47)

> It is a 95% Wilson score interval on **the probability that the returned order reproduces the
> matching failure signature in a clean container.** For a Verified certificate we require at
> least 18 matching failures in 20 independent clean replays and a Wilson lower bound of at
> least 0.70.
>
> **The interval describes replay reliability under our harness. It is NOT a probability that
> the diagnosis is correct, and we do not present it as one.**

### Why not "calibrated confidence" (Q48)

> Because **calibration is a specific claim**: that a stated confidence of 0.8 corresponds to
> being right 80% of the time, demonstrated on held-out data. We have not done a calibration
> study and are not planning one in committed scope, so we say **repeated replay rate with an
> interval**. The word *calibrated* is reserved for a held-out calibration evaluation.

⚠ **Thresholds are POLICY, estimator is literature.** The 18/20 and 0.70 constants are our
acceptance policy, frozen after the POC and validation baselines but **before the held-out
run**. Adjusting them after seeing results would invalidate the evaluation.

---

## Abstention — the synthesis

**No cited OD-diagnosis system defines a typed abstention.** iFixFlakies raises an exception
when a test is incorrectly classified as order-dependent [4] — a **failure signal rather than a
graded outcome**.

The principle comes from two directions:

1. **Certifying-algorithm model** [20] — a checker must be able to reject; an algorithm that
   cannot produce a valid witness has not produced a trustworthy answer
2. **Rerun literature** [14] — **absence of an observed failure at a given budget is not
   evidence of absence**

FlakeTrace's **Verified / Candidate / Unresolved**, each with a machine-readable reason, is the
operationalisation of that principle.

> **Its correctness is measurable:** no false confident diagnosis may be issued on non-OD
> controls.

**And now it has user evidence too** — SH1 and SH2 both independently said a confident wrong
answer is worse than a stated unknown ([[00-Meta/stakeholder-evidence]] §4).

---

## Budget-aware search — where the reserve idea comes from

The requirement for an explicit budget derives from the cost literature [19], [15].

The **cost unit** derives from measurement practice in the closest prior work: Rahman et al.
account for Surefire invocation overhead separately — running an entire module's suite,
subtracting total Surefire-reported test time, repeating **30 times** for an average. That is,
**the literature treats per-invocation harness overhead as a first-class, separately measured
cost term** rather than folding it into test runtime.

→ We count **total test-method invocations** as primary algorithmic cost (a single Maven launch
may execute very different numbers of tests) and report wall-clock, launches and CPU-seconds as
operational costs.

### The verification reserve — honestly labelled as derived

> Reserving part of the budget for verification rather than spending all of it on search **has
> no single canonical citation.** It follows from combining the certifying-algorithm
> requirement that a witness accompany the output [20] with the finite-budget reality [19].
>
> It is stated as a **design position derived from two sources, not an established practice** —
> and **the ablation that removes the verification reserve is the experiment that tests it.**

Say it that way if asked. Claiming a citation that does not support the number is the specific
failure this vault exists to prevent.
