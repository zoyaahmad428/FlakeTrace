# Commercial comparators — Trunk, Tuist, Develocity

**Role for us:** the **product gap**, stated carefully.

---

## What they do — and do well

**Trunk Flaky Tests · Tuist · Gradle Develocity** detect, track, group, retry, quarantine and
chart flaky tests.

> **That ground is taken and well-funded. Do not compete on dashboards.**

## The gap — and the exact wording to use

> **None of the product documentation we reviewed describes returning a verified, replayable
> order plus a resource-level evidence path for a specific order-dependent failure, at a
> measured confidence.**

⚠ **Phrasing discipline — this matters:**

| ❌ Never say | ✅ Say |
| --- | --- |
| "Commercial products cannot do this" | "Their **published documentation does not describe** it" |
| "They don't have this feature" | "…and we **validated the residual workflow need with users**" |

*Claiming knowledge of a closed-source product's internal capability is an overclaim a panel
can puncture in one question.*

## Stakeholder corroboration

This is not only a documentation argument — our own interviews support the residual need from
the user side ([[00-Meta/stakeholder-evidence]]):

**SH1 (Inspirovix)**, on their existing tooling (GitHub Actions logs, pytest/Jest output,
application logs, Docker logs, monitoring):
> *"They are good at telling us what failed… much weaker at explaining why a failure is
> intermittent. They normally do not automatically tell us that Test A modified some shared
> state that caused Test B to fail 30 tests later. Finding that relationship usually requires
> manual investigation."*

**SH2 (Trillet AI)**, on isolating an order-dependent failure:
> *"It is manual binary search — intuition and trial and error. **There is no tooling support
> for it.**"*

## Why a team would install a self-hosted tool rather than buy a dashboard (Q6)

> Because the two do different things. Detection and quarantine products tell you **which**
> tests are unstable and **how often**. None of the documentation we reviewed describes
> returning a verified, replayable order plus a resource-level evidence path for a specific
> order-dependent failure.
>
> **The self-hosted constraint is a stakeholder requirement, not a preference:** the tool
> executes the project's own test code, so teams that cannot send source or test output to a
> third party need it to run inside their own boundary.

**Hard evidence for that second point:**
- **SH3 (Learnsignal):** sending the repository externally is *"out of the question"* — database
  schemas, migration files, integration logic tied to student profiles and payment information.
  Must run on internal runners or self-hosted.
- **SH1:** local analysis *"strongly preferable"*; proprietary and client code. *"A tool that
  can operate completely within our own infrastructure would therefore be easier to approve."*

## Design consequence

The committed product requires **no cloud subscription, no GPU and no paid API** — which is
also our DEI argument: usable by under-resourced teams and institutions.

Only the **gated** CDR module would draw on the ~$100 API budget, bounded to one plan plus one
retry per verified certificate, with a configuration flag disabling all external calls for
on-premises users.
