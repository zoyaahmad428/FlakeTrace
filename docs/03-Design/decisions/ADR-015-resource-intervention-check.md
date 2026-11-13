# ADR-015 — Resource intervention check: testing whether the named resource is the cause

**Date:** 2026-11-13 · **Status:** `ACCEPTED as a spike` by M1, M2 and M3 on 2026-11-13 (in person; PR #101): the
spike only, with a go / no-go written up afterwards. Not scheduled before the FYP-1 Final
unless W16–W26 are on track. Needs the supervisor's decision on whether causal certification stays
a promise ([[10-Final1/supervisor-agenda]] item 2) ·
**Owner:** M1 (which resource, what the result means) with M2 (harness step) ·
**Addresses:** the stronger half of FT005 · **Work package:** W34 (stretch) ·
**Builds on:** [[03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation]],
[[03-Design/decisions/ADR-010-verdict-contract-v2]]

## Context

After ADR-010 the report is honest about the resource: *static overlap, a possible mechanism, not
confirmed as the cause*. That is the truthful floor. It is also less than the project set out to
give. The certificate contract lists **counterfactual checks**, and our stated difference from
prior work includes **intervention** (claims ledger B5).

The supervisor left the door open in FT005: *"If causal certification remains an approved promise,
agree a targeted intervention or runtime observation that can establish it."*

ADR-001's fallback for stronger evidence was a Java agent that instruments bytecode. That is the
highest-risk item on our list. There is a cheaper experiment that answers the causal question
directly.

## The idea

We already know the sequence, and static analysis names a candidate resource `r`. Run the sequence
once more with **one change**: between the last polluter and the victim, put `r` back to the value
it had before the polluters ran.

```
normal:        P  ─────────────►  V        V fails
intervention:  P  ──► restore r ──►  V        does V pass?
```

| Result over `k` runs | Meaning | `assurance.resource` |
| --- | --- | --- |
| V passes every time with the restore, and fails without it | Restoring `r` alone removes the failure | `MECHANISM_CONFIRMED` for `r` |
| V still fails every time | `r` is not the cause, or not the only one | `STATIC_OVERLAP`, mechanism `NOT_CONFIRMED` |
| Mixed | — | `INCONCLUSIVE` |

The restore is done by the **harness**, in memory, in the same JVM, between two tests:

| Family | Snapshot before the polluters | Restore before the victim |
| --- | --- | --- |
| System property | `System.getProperty(key)` | `setProperty` or `clearProperty` |
| Static field | `Field.get(null)` by reflection | `Field.set(null, saved)` |

Nothing is injected into the project's classes and no file is changed. The answers to the panel's
first two questions stay "no".

This is what makes the two controls of FT005 decisive rather than descriptive:

| Control | Static analysis says | The intervention says |
| --- | --- | --- |
| Polluter writes `r` and restores it; the real cause is elsewhere | edge on `r` | restoring `r` changes nothing → not confirmed |
| Polluter writes two resources, only one matters | two edges, first by name shown | only the right one, when restored, makes V pass |

## Why it needs a spike before anyone commits to it

| Risk | Why it matters |
| --- | --- |
| **Reading a static field loads its class.** Taking the snapshot runs that class's static initialiser earlier than the tests would have | The check could change the behaviour it measures. Both harness defects found in the POC were the tool changing what it measured (claims ledger C10) |
| The saved value is a **reference**. If the polluter changed the object in place instead of assigning a new one, restoring the reference undoes nothing | The result would read "not confirmed" for a true cause |
| `final` static fields | Cannot be set by plain reflection on every JDK |
| Several polluters and several resources | Restore one resource at a time, or all — and the number of runs grows |
| JUnit 3 and class-grouped blocks (ADR-012) | The restore step must sit between two blocks |

## The spike — two days at most, not merged

1. A harness option that takes one resource identifier and performs snapshot and restore.
2. Run it on fixture F1 (static field, assigned), F2 (system property) and the two FT005 controls.
3. Record for each: does the unmodified sequence still behave identically with the snapshot taken
   but **no** restore? That is the perturbation control — if this differs, stop.
4. Write up what worked, what did not, and the cost in runs.

**Go** if the perturbation control is clean on all four and the controls separate as the table
above predicts. **No-go** otherwise: ADR-010's wording stays the final position on resource
evidence for FYP-1, and runtime observation is reconsidered for FYP-2.

Either result is a finding worth reporting.

## What is not decided here

Schema fields for the intervention result, its place in the budget (it is a verification cost and
would come out of the reserve), and whether `VERIFIED` should ever require it. All three wait for
the spike.

## Agreement

| Member | Agree to the spike? | Comment |
| --- | --- | --- |
| M1 | ☑ | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
| M2 | ☑ | Agreed 2026-11-13 in person with M1 and M3; recorded their agreement in PR #101 |
| M3 | ☑ | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
