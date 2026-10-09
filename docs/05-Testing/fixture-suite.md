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
