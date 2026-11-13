# Controlled Fixture Suite

*Ten small hand-built Maven projects, each isolating **one** condition real subjects will not
produce on demand.* Status: `COMMITTED` — became committed scope as a direct consequence of the
POC.

---

## Why it exists

Real subjects will not produce multi-predecessor, budget-exhaustion or unsupported-resource
cases when you need them. Without fixtures, the abstention contract — **our actual
contribution** — cannot be tested at all.

## The ten fixtures

| Fixture | Condition | Expected output |
| --- | --- | --- |
| **F1** | Single static-field polluter, direct write | Verified, rank 1 |
| **F2** | Polluter **three call-hops** from the write site | Verified **only at sufficient depth** |
| **F3** | **Two predecessors both required** | **Unresolved (multi-predecessor)** — *not* a false Verified |
| **F4** | Pollution via **reflection** | **Unsupported resource**, explicit abstention |
| **F5** | System-property pollution | Verified, correct family |
| **F6** | Filesystem-path pollution | Verified, correct family |
| **F7** | **Nondeterministic victim** | **Candidate**, wide interval |
| **F8** | **Misleading signature** | **Not counted as reproduction** |
| **F9** | Budget exhausted before verification | **Unresolved (budget)**, typed reason |
| **F10** | **Non-OD control** | **No confident certificate** |

> **F3, F4, F8, F9 and F10 test the abstention contract — which is our actual contribution.**

## What was actually built, and what Iteration 2 adds (2026-11-13)

The table above is the **plan from the proposal**. What exists in `fixtures/od-fixture` is seven
cases with different labels, each with ground truth written before its first run:

| Built | Condition | Ground truth |
| --- | --- | --- |
| F1 | Static field, one polluter | `VERIFIED` |
| F2 | System property read one call down | `VERIFIED` |
| F3 | Two polluters both required | `VERIFIED` (found by `ddmin`) |
| F4 | Fails only in a shuffled order | `VERIFIED` |
| N1 | Always fails alone | `UNRESOLVED(VICTIM_FAILS_ALONE)` |
| N2 | Flaky on its own | `UNRESOLVED(VICTIM_FAILS_ALONE)` |
| N3 | Fails only under an external condition | `UNRESOLVED(NOT_REPRODUCED)` |

**Proposed for Iteration 2** — controls the Mid review asked for. Member 3 owns the fixture and
its ground truth; the cases marked M2 or M1 live in that member's own test resources instead.

| New | Condition | Expected | Tests | Home |
| --- | --- | --- | --- | --- |
| **N4** | Victim throws one exception alone and a different one after its polluter | `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)` | FT003, integrated | fixture, M3 |
| **R1** | Polluter writes a static field and **restores** it; the victim reads that field; the real cause is elsewhere | An edge is reported as *static overlap* and never as the cause | FT005 | evidence self-test, M1 |
| **R2** | Polluter writes two resources the victim reads; only one matters | **Both** edges visible in the report | FT005 | evidence self-test, M1 |
| **L1** | `@BeforeClass` counts its own calls; two tests assert it ran once | Passes under Surefire and class-grouped execution; fails under per-method execution | FT006 | runner test resources, M2 |
| **B1** | Any existing case, run with a budget too small to finish | `UNRESOLVED(BUDGET_EXHAUSTED)` | FT007; the proposal's F9 | no new code |

Still planned from the original ten and **not** built: reflection (F4 in the plan), filesystem
(F6), misleading signature (F8). Stochastic deletion and the inconsistent search are tested with
a scripted runner, because a real JVM cannot be made to fail on exactly its third run.

## What each one is really testing

- **F2** validates the depth decision empirically, in a case we constructed and therefore know
  the answer to. *The POC's FJ-02 was two hops; F2 goes to three deliberately.*
- **F3** tests whether our **pairwise design** — not our signal — is the limitation. This is the
  same question as pre-defence item 2 (per-case cause classification of the three non-moving
  cases).
- **F4** confirms reflection produces an **opaque event and abstention**, never a
  silent zero-overlap. *(The frozen definitions say unsupported families are "recorded as
  unsupported, **never as zero-overlap**" — F4 proves the implementation honours that.)*
- **F8** is the **Qi et al. defence**: a failure with a misleading signature must not be counted
  as reproduction. Exit code is not a signature.
- **F10** is where **false-confidence rate** is measured. A confident certificate here is the
  single worst outcome the project can produce.

## Timeline

F1–F5 land in **FYP-I early**; F6–F10 by **FYP-I end**. Owned by **Member 3** as part of
evaluation infrastructure.

## The honest limit — say this before being asked

> The fixture suite exists to test the **implementation**. **It is not a substitute for real
> projects**, and we do not present fixture results as evaluation results.

The guide's fallback ladder puts fixtures explicitly *below* reducing case count and reporting
it — synthetic-only results silently substituted for real ones is the failure mode being
guarded against.
