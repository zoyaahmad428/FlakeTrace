# ADR-012 — Execution semantics: class-level lifecycle, and what is and is not reset

**Date:** 2026-11-13 · **Status:** `ACCEPTED` by M1, M2 and M3 on 2026-11-13 (in person; PR #101); section 2 still
needs its spike first ·
**Owner:** M2 · **Verifier:** M1 (compares normal and diagnostic execution) ·
**Closes:** FT006, FT021 · **Work packages:** W22, W27 ·
**Builds on:** [[03-Design/decisions/ADR-003-order-runner-junitcore-harness]],
[[03-Design/decisions/ADR-004-w7-diagnosis-runs]]

## Context

**Lifecycle (FT006).** `FtHarness.runOne` runs every test as its own JUnit request:

```java
core.run(Request.method(cls, spec.substring(hash + 1)));
```

JUnit builds a one-method class runner for each call, so class-level setup and teardown —
`@BeforeClass`, `@AfterClass`, `@ClassRule` — run **once per test method**. Under Maven Surefire
they run **once per class**. A project whose `@BeforeClass` initialises shared state, or whose
`@AfterClass` cleans it, can behave differently under our harness than under its own build. That
can hide a real order dependency or create one that does not exist.

We already met this kind of error once: the POC's 182 false polluters came from a missing
suite-level `@BeforeClass` (claims ledger C10).

**Reset (FT021).** Three statements in our documents are stronger than the code:

| We said | What the code does |
| --- | --- |
| "The code is never modified" | `runner/integrity.py` hashes project files **before and after** a diagnosis. A file changed and restored in between is not seen |
| "Source integrity" | The top-level `target/` and `.git/` are excluded. Files outside the project are not looked at |
| "Each run is clean" | A fresh JVM resets static fields and JVM system properties. It does **not** reset files, environment variables, network or external services |

There is no sandbox. Tests run with the user's permissions and with network access.

## Decision

### 1. State the boundary, in the product and in every document

**Supported execution contract (Iteration 2):**

| | |
| --- | --- |
| Subjects | **Trusted projects only**: code the user would run on their own machine anyway |
| Build | Maven; compiled classes and the test classpath come from the project's own build |
| Tests | JUnit 4, and JUnit 3 `TestCase` through JUnit's own adapter |
| One order | One fresh JVM, tests in exactly the given order |
| Reset between orders | JVM state only: static fields, system properties, loaded classes, threads |
| **Not** reset | Files anywhere, the working directory, environment variables, network and external services, the system clock and timezone |
| Integrity check | "The project's files, outside `target/` and `.git/`, have the same SHA-256 after the diagnosis as before" — and nothing more |

Words we stop using until they are true: *sandboxed, isolated, clean execution, the source is
never modified*. Say instead: *"the project's files were identical before and after"*.

A test that depends on a file left by an earlier **order** is outside the contract. It is one of
the cases the committed filesystem family and the container exist for, in FYP-2.

### 2. Class-grouped execution in the harness — spike first

Run consecutive tests of the same class as **one** JUnit request, so class-level lifecycle runs
once per block, as under Surefire.

```
order:   A#1  A#2  B#1  A#3
blocks: [A#1  A#2] [B#1] [A#3]
```

For each block: one request for the class, filtered to the block's methods and sorted into the
block's order.

| Point | Rule |
| --- | --- |
| Every test is always reported | Results are written as each test finishes, from the listener, not after the block — a crash in the middle still leaves the earlier results |
| `@BeforeClass` itself fails | Every test of the block is reported as failed with that exception |
| A class appears in two blocks (`A` above) | Allowed, and noted in the record. Surefire never produces such an order, and neither do our class-first shuffles; it can only come from a hand-written `--order` |
| Mode switch | `--lifecycle class-grouped` (the new default once validated) or `per-method` (today's behaviour, kept for comparison) |
| Recorded | The mode is written in the record header and in the report |

**Spike before committing to this** (half a day, not merged): confirm on JUnit 4.13.2 and on a
JUnit 3 `TestCase` that a class request can be filtered to chosen methods and sorted into a chosen
order, and that per-test results arrive through the listener. If the JUnit 3 adapter cannot be
ordered, JUnit 3 classes keep `per-method` and the report says so.

### 3. A lifecycle control, compared against normal execution

A small self-test class in Member 2's own test resources (`runner/tests/resources/`, where the
JUnit 3 self-test already lives — **not** Member 3's fixture):

```java
public class LifecycleControlTest {
    static int classSetups = 0;
    @BeforeClass public static void once() { classSetups++; }
    @Test public void first()  { assertEquals(1, classSetups); }
    @Test public void second() { assertEquals(1, classSetups); }
}
```

| Execution | Expected | What it shows |
| --- | --- | --- |
| Maven Surefire, `mvn -Dtest=LifecycleControlTest test` | both pass | Normal behaviour |
| Our harness, `per-method`, order `[first, second]` | `second` **fails** (`classSetups == 2`) | Today's deviation, measured |
| Our harness, `class-grouped`, same order | both pass | The fix matches normal execution |

Member 1 runs all three on her machine and records setup counts and signatures. This is the
"class-lifecycle control against normal execution" FT006 asks for, and a small instance of the
non-perturbation control we already committed to ([[02-Requirements/non-functional]]).

### 4. Diagnose on a disposable copy

`--workspace copy` (proposed default): copy the project to a temporary folder, build and run
everything there, delete it at the end.

| Effect | |
| --- | --- |
| The user's project is never written to | True **by construction**, not by checking afterwards |
| Files a test leaves inside the project | Die with the copy; they cannot affect the user's next build |
| Cost | One copy and one Maven build per diagnosis |
| Limit | Files written **outside** the project (temp directory, home) are still not contained |

The before/after hash is still computed, now on the copy, and still reported.

### 5. A pinned container for reproducibility — not for security

A `Dockerfile` on a pinned Maven + Temurin 8 image with Python, and one documented command that
runs a fixture diagnosis inside it.

What it gives: the same JDK, Maven, locale and timezone on every machine; the image digest in the
record; a first answer to the handbook's "buildable without the original developer present" and
"a first deployment attempted".

What it does **not** give: a security sandbox. Rootless execution, disabled network, dropped
capabilities and resource limits remain the committed FYP-2 safety work
([[02-Requirements/non-functional]]). The report must not suggest otherwise.

### 6. More of the environment in the record

Added to the record header, because real cases depend on them (two fastjson cases flip with the
timezone — POC log): the tool's own git commit and dirty flag, Maven version, JUnit version,
Python version, `user.timezone`, default locale, `file.encoding`, the lifecycle mode, the
workspace mode, the container image digest or `null`, and the full command line.

## Consequences

- Real-project results ([[05-Testing/real-case-protocol]]) are produced **after** section 3's
  control passes, and name the lifecycle mode they ran under.
- Panel action A3 is answered with section 1's exact sentence, and with section 4 once it exists.
- The report's sections on integrity and limitations (6.6.2, 8.10) are corrected to section 1.
- Suite-level context (a project whose Surefire configuration runs suite classes, as jsoniter
  does) is **not** solved by this ADR. It stays a named unsupported case until a subject needs it.

## Order of work

1. Section 1 wording into the documents and the CLI text now (W16).
2. Section 6 header fields (small, unblocks the evidence bundle of ADR-013).
3. The spike of section 2; then the harness change with the control of section 3 (W22).
4. Section 4, then section 5 (W22, W27) — both can be cut if time is short; sections 1–3 cannot.

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☑ | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
| M2 | ☑ | Agreed 2026-11-13 in person with M1 and M3; recorded their agreement in PR #101 |
| M3 | ☑ | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
