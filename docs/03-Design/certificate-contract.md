# The Certificate — contract and contents

*The product output. Every member must be able to list its contents and explain its three
decision classes.*

---

## Why it is called a certificate

From the **certifying-algorithm** model (McConnell et al.): a certifying algorithm produces,
with each output, a **witness** — an easy-to-verify proof that the output has not been
compromised by a bug. The user checks the witness and can be sure of correctness **without
having to trust the algorithm**.

| Model | FlakeTrace |
| --- | --- |
| Input *x* | pinned commit, module, target test, budget |
| Output *y* | classification and replay order |
| Witness *w* | the evidence bundle |
| **Checker** | **a third party re-running the replay command on a clean machine** |

> A diagnosis a developer cannot independently re-verify is exactly the **non-certifying output
> the model argues against.**

## The three decision classes (Q60)

| Class | Meaning |
| --- | --- |
| **Verified** | Sequence passed deletion checks, met the replay threshold, **and** carries a resource path in a supported family |
| **Candidate** | Reproducing sequence that replays, but **at least one certification requirement is unmet** — most often the resource path is missing or points at an unsupported family |
| **Unresolved** | No sequence meets the acceptance rule, **with a typed reason** |

> **Why three rather than two:** *"we found the order but cannot explain it"* is genuinely
> useful to a developer and genuinely different from *"we found nothing."*

## The four abstention reasons (Q49)

| Reason | What it tells the developer |
| --- | --- |
| **Unsupported resource** | The evidence points at a family outside static fields, system properties and filesystem paths — *"the state is in a database we do not instrument"* → look there yourself |
| **Budget exhausted** | Search ended before a sequence met the acceptance rule → give it more budget |
| **Unstable build** | The project did not produce consistent outcomes on control runs → **no measurement is trustworthy** |
| **Inconsistent outcomes** | The same order produced conflicting results beyond the verification threshold → likely nondeterministic, not order-dependent |

> **Each reason maps to a different next action — that is the point.** An untyped "unknown"
> tells them nothing.

**Abstention quality is measured**, with two components: certificates correctly withheld on
non-OD controls, and false confident certificates issued.

## Certificate contents (Q61 — be able to list this)

**Case identity** — repository, commit, module, Java/Maven/JUnit versions, target test, failure
signature

**Classification** — victim, brittle, mixed or unsupported

**Replay order** — explicitly labelled **deletion-minimal (1-minimal)**, never "minimum"

**Counterfactual checks** — outcome with each retained predecessor removed, and where applicable
with the suspected polluter inserted

**Resource evidence** — candidate write → normalised resource identifier → victim read, with
**source lines and bytecode offsets on both sides**, plus provenance and coverage limits

**Reliability** — verification runs, failures, empirical rate, **Wilson 95% interval**, stopping
reason, clean-container replay result

**Budget account** — Maven launches, total test-method invocations, wall time, instrumentation
overhead

**Decision** — Verified / Candidate / Unresolved, with human-readable rationale and
machine-readable JSON

**Action artefact** — the **exact replay command** and the evidence bundle

**Stated limitations** and unsupported resource families

## Acceptance thresholds

| Requirement | Value | Basis |
| --- | --- | --- |
| Matching failures | **≥ 18 of 20** clean replays | ⚠ **PROJECT POLICY**, frozen after POC/validation, before held-out run |
| Wilson 95% lower bound | **≥ 0.70** | ⚠ **PROJECT POLICY** — the *estimator* is literature-mandated, the *threshold* is ours |
| Deletion checks | Every Verified sequence passes | — |
| Explanation | Every Verified explanation includes a test→resource→test path in a supported family | — |
| Controls | **No false confident diagnosis on non-OD controls** | — |

## What the interval does NOT mean

> The Wilson interval describes **replay reliability under our harness**. It is **not** a
> probability that the diagnosis is correct, and we do not present it as one.

**We will not report a numeric confidence score.** Reliability is always expressed as *matching
failures out of N replays plus an interval*. The word **"calibrated"** is reserved for a
held-out calibration evaluation we are not doing.

## Victim vs brittle classification (Q62)

| | Fails because | Reproduces when |
| --- | --- | --- |
| **Victim** | a predecessor **pollutes** shared state | a candidate is **inserted before** it |
| **Brittle** | a predecessor it **depends on is absent** | a candidate is **removed from before** it |

The two require **different fixes** and the distinction is **observable**.

> When the observed evidence conflicts, we label **mixed or uncertain** rather than forcing a
> category. **Forcing a label is exactly the false-confidence failure the abstention contract
> exists to prevent.**

## The consequence that justifies all of this

> A false confident certificate **sends a developer to modify the wrong test** — with an
> official-looking artefact justifying it. That is **worse than no answer**.

Two of our three stakeholders said this unprompted. See [[00-Meta/stakeholder-evidence]] §4.
