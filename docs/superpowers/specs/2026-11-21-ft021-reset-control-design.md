# FT021 reset-sensitive control: design

**Date:** 2026-11-21 · **Owner:** M2 · **Verifier:** M3 (FT021: "checks recorded provenance") · **ADR:** ADR-012 §1
(the reset boundary, agreed by all three) · **Finding:** FT021, panel action A3

## Intent

ADR-012 §1 states what one fresh JVM per order resets (static fields, system properties, loaded classes, threads)
and what it does not (files anywhere, the working directory, environment variables, network, clock and timezone).
FT021 asks for a **reset-sensitive control** so that statement is shown by real runs, not only written: "the reset
boundary is written down and matches the code".

## Goals / non-goals / anti-goals

- **Goals:** a control project whose tests leave state in one order and look for it in the next order (a new JVM);
  a real-JVM test whose expectations are **one table** mirroring ADR-012 §1; the measured result in the docs.
- **Non-goals:** detecting leftover state during a diagnosis (needs file-access evidence: the filesystem family,
  FYP-2; recorded as the follow-up); environment variables and the clock (a Java test cannot change them, so the
  table records them as "not reset, not testable from Java").
- **Anti-goals:** a control that passes vacuously (the reader must be shown to catch leftovers); writing into this
  repository during tests; any wording that implies isolation or a sandbox.

## Approaches

| | Approach | Trade-off |
| --- | --- | --- |
| **A (chosen)** | New Maven project `runner/tests/resources/reset-control/` (writer and reader classes), driven by a real-JVM test in `runner/tests/test_order_runner.py` with an expectation table | Separate from the lifecycle control, whose Surefire run in CI must pass; one table to edit when the hardened container (FYP-2) makes files reset |
| B | Add the classes to `lifecycle-control` | Its CI Surefire step would fail by design (in one JVM nothing is reset) |
| C | Put it in the od-fixture | M3's folder, for a runner property |

## Design

- `ResetWriterTest#leaveState`: sets a static field, sets system property `flaketrace.reset.control`, writes
  `flaketrace-reset-control.marker` into `java.io.tmpdir` and into the working directory.
- `ResetReaderTest`: `staticFieldIsDefault`, `systemPropertyIsUnset`, `tempFileIsAbsent`, `workingDirFileIsAbsent`
  — each asserts the state is gone (passes when reset).
- The POM skips Surefire (`skipTests`), with a comment: under plain `mvn test` writer and reader share one JVM, so it
  is meaningful only through FlakeTrace's harness.
- Test `TestResetControl` (real JVM, `OrderRunner` with a **temporary working directory**; markers deleted before
  and after):
  - `EXPECTED = {"static field": "reset", "system property": "reset", "file in the temp folder": "not reset",
    "file in the working directory": "not reset"}`, each row naming its reader method;
  - **across orders:** order 1 `[writer]`, order 2 `[all four readers]` → a reader passes iff its row says "reset";
  - **sanity (no vacuous pass):** one order `[writer, readers]` in one JVM → all four fail, so each reader really
    detects its leftover.
- Docs: `docs/04-Implementation/sandbox-runner.md` reset table with the measured result; `runner/README.md`; FT021 /
  A3 rows in the action register (Partly, M3 to check); evidence and GenAI log; the FYP-2 follow-up (detection) in
  the risk register or roadmap note.

## Left to the builder

Class and method names beyond those above; the exact marker contents.
