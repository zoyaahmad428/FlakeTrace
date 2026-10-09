# AI Usage Log

*Required by current university policy and the School guide. Submitted with the dependency
disclosure sheet and countersigned by the supervisor.*

> **The log is evidence FOR you, not against you.** Panels use it to choose what to ask about,
> **not to deduct marks for using tools**. A group that records honest, specific entries and can
> explain the CCP-relevant ones demonstrates exactly the ownership the guide requires.
>
> **An empty log on a project that plainly used assistance, or a log whose entries cannot be
> defended, is treated as a disclosure failure.**

---

## The standard of understanding that applies

For any part of the system touching the complex computing problem, the responsible member must
be able to:

1. **Explain what it does and why it is there** — walk through the component's role and the
   sub-problem it addresses, **without reading from the code**
2. **Justify why it is built this way** — name at least one alternative considered, and say why
   it was rejected
3. **Predict what breaks** — state what fails if an input, assumption, dependency, requirement
   or scale changes, and what the system does when it fails
4. **Modify it under questioning** — describe or make a specific change and identify what else
   must change with it

> **A member who cannot do these four things does not own that component, whatever the
> repository history shows.** The standard applies uniformly — from scratch, adapted from a
> tutorial, taken from a published implementation, or produced with assistance.

Peripheral code is held to a lower standard: know what it does and why it is there, but you are
not expected to defend every line of routine scaffolding.

---

## Dependency classification

Every external component is one of:

| Class | Meaning | Ours |
| --- | --- | --- |
| **Support** | Scaffolding, tooling, formatting — not part of the contribution | |
| **Core-assist** | Touches the CCP but the design and decisions are ours | |
| **Core-replacement** | Would replace the contribution itself | **Nothing we claim as contribution sits here** |

**Questions to ask about every important dependency:**
- What exactly does it provide, and which part remains our technical responsibility?
- Would the FYP still contain a meaningful computing contribution if it were replaced?
- How will outputs, failures, limitations, cost, security and fallback behaviour be tested?
- Can we explain and modify the surrounding design and integration?
- Have we correctly cited or attributed external code, data, models, prompts, text and
  documentation?

---

## Log

| Date | Member | Tool | Purpose | Artefact affected | Class | Verified by |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |

**Categories to record** (from the guide):
- **Code** — generation, completion, refactoring, debugging assistance
- **Documentation and writing** — which artefacts were drafted with assistance and **verified by
  you for technical accuracy** before submission
- **Anything else** — data cleaning, configuration, translation, diagram drafting, or any use you
  would not want a panel to discover unrecorded

---

## The answer (Q100)

> We use [tools] for [purposes]. Every use is acknowledged in the report as the HEC guidance
> requires. **No component we claim as our contribution is produced by a tool we did not author
> or adapt** — the planner policy, the minimiser, the verifier and the resource abstraction are
> ours.
>
> The guide's classification applies: external components are support, core-assist or
> core-replacement, and **nothing we claim as contribution sits in the core-replacement
> category.**

---

## ⚠ Before the defence

- [ ] Log is **current** — no gaps between the last entry and the defence date
- [ ] Every CCP-relevant entry can be explained against the four-point standard above
- [ ] Dependency disclosure sheet complete
- [ ] Supervisor countersignature obtained
