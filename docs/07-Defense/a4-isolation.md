# A4 — How is the code block isolated?

*Panel action A4 (proposal defence). v1.1 · 2026-11-28 · written by M2; **resource row, FJ-03 line and FYP-2 section
checked and corrected by M1 on 2026-11-28** ([[evidence-m1]]). Status: `DRAFT`, awaiting the supervisor's acceptance
([[10-Final1/action-register]] A4, W40).*

**Short answer.** FlakeTrace isolates the failing **sequence of tests** — the smallest set of earlier tests that,
run before the victim, makes it fail — and checks each one by removing it and re-running. It does **not** isolate the
cause inside the code: the shared resource it names is a **static overlap**, a possible mechanism, never confirmed as
the cause.

## What is isolated, how, and how sure we are

| Level | What | How | How sure | Evidence |
| --- | --- | --- | --- | --- |
| Runs | Each test order | One fresh JVM per order, on a disposable copy of the project (ADR-012) | **JVM state only** is reset between orders: static fields, system properties, loaded classes, threads. Files, the working directory, environment variables, network and the clock are **not** (claims ledger G5) | Reset control (FT021), reproduced by M3; project files hashed before and after (G4) |
| Sequence | The polluters plus the victim | Find a failing order; try each earlier test before the victim; if no single test is enough, shrink with delta debugging (single trials); then **remove each kept test and re-run the rest `m` = 20 times** (ADR-011) | A kept test is `NEEDED` only if the victim passed **all 20** runs without it. The sequence is **1-minimal under that rule, never "the minimum"** (D9); it reproduces `n` = 20 times and the victim alone is tallied separately (FT003) | `deletion_checks` in every `VERIFIED` report (G2); FT004, reproduced by M1 |
| Resource | A static field, or a system property with a constant key, that the polluter's code may **write** and the victim's code may **read** | Static bytecode analysis of the compiled classes (`javap`), following calls to depth 2 by default (up to 5); calls into the JDK and libraries are not followed; nothing injected (A2) | **`STATIC_OVERLAP`, mechanism `NOT_ASSESSED`** when an edge is found (every `VERIFIED` report): the polluter *may* write and the victim *may* read it. **`NONE`** when no edge is found (FJ-03). Values, restores and timing are not modelled; missing evidence is not proof of independence (G3) | Every report's `assurance.resource` and fixed limitations |

## Worked example: fixture F3

Committed bundle `eval/bundles/20261121T184910Z-odfixture.ToggleVictimTest#expectsNotBothFlagsSet/` (`verify` OK):

1. **Failing order:** the victim `ToggleVictimTest#expectsNotBothFlagsSet` fails after **17** earlier tests.
2. **Search:** no single earlier test is enough (16 single-test trials).
3. **Reduction:** delta debugging keeps **two**: `ToggleAPolluterTest#setFlagA` and `ToggleBPolluterTest#setFlagB`.
4. **Deletion checks:** each kept test was removed and the rest re-run **20** times; the victim **passed 20/20** each
   time → both `NEEDED`.
5. **Sequence check:** `[setFlagA, setFlagB, victim]` fails **20/20** (Wilson lower bound 0.839); the victim alone fails
   **0/20** → `VERIFIED (sequence)`.
6. **Resource:** static fields `odfixture.Toggles.flagA` and `flagB`, level `STATIC_OVERLAP`, mechanism `NOT_ASSESSED`.

## What this does not claim

- **Not proof for every subset or every future run.** The claim is bounded by the stated rule: single-trial delta
  debugging, then `m` = 20 repeated removals and `n` = 20 repeats. A test that is needed only sometimes, or a smaller set
  delta debugging never tried, can escape it.
- **Not the cause.** `VERIFIED` is about the sequence; the resource is a possible mechanism (G3).
- **Not a sandbox.** State outside the JVM can leak between orders (G5); the projects are trusted (A3).
- **Not every case.** On fastjson FJ-03 the static analysis finds **no** resource edge: both tests only *read* the static
  `ThreadLocal` `SerializeWriter.bufLocal`, and the change happens inside the JDK call `ThreadLocal.set`, which the
  extractor does not follow. So the best result is `CANDIDATE`, not `VERIFIED`.

## What is FYP-2

Confirming the resource itself is **ADR-015**: put the named resource back to its earlier value between the polluters
and the victim, and see whether the failure goes away. It is accepted as a **spike** (W34, stretch), not built; whether
causal certification remains a promise awaits the supervisor ([[10-Final1/supervisor-agenda]], item 2). Where static analysis
names no resource (FJ-03), only runtime observation could, and that is not built either (A2).

## Where the demo shows it

Demo step 2 ([[10-Final1/demo-plan]]): open the committed F3 bundle in the UI (Source → Committed evidence): the
Diagnosis step shows the 17 → 2 reduction and, in its **Deletion checks** panel, each kept test removed: "Removed
odfixture.ToggleAPolluterTest#setFlagA: the victim passed 20 of 20 runs without it → NEEDED", and the same for
`setFlagB`; the Certificate step shows the 20/20 and 0/20 tallies and the static-overlap wording.
