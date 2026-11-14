# W22 job 3 — class-grouped execution and the lifecycle control (design)

*2026-11-14 · M2 · Status: proposed, awaiting M2's approval · ADR-012 §2–§3 · FT006 ·
builds on the spike result in ADR-012 §2.*

## Why

Under Maven Surefire, `@BeforeClass`/`@AfterClass` run once per class. FlakeTrace's harness runs
every test as its own JUnit request, so they run once per **test**. A project whose class setup
initialises shared state can then behave differently under FlakeTrace than in its own build —
hiding a real order dependency or inventing one. The spike measured it: the control class fails
under today's harness (`expected:<1> but was:<2>`).

## Goals / non-goals / anti-goals

- **Goal:** `--lifecycle class-grouped` runs each run of consecutive same-class tests as **one**
  JUnit request, filtered to those methods and in the requested order, so class-level lifecycle runs
  once per block, as under Surefire.
- **Goal:** a lifecycle control that M1 (and CI) can run three ways — Surefire, harness
  `per-method`, harness `class-grouped` — with the results in a table (ADR-012 §3).
- **Non-goal:** changing the default now. `per-method` stays default until M1 has recorded the
  control table on her machine; then a one-line follow-up flips it (ADR-012 §2: "the new default
  once validated").
- **Non-goal:** suite-level context, `@ClassRule` behaviour beyond what JUnit does by itself,
  disposable copy (job 4).
- **Anti-goal:** a test reported as crashed (`INFRA`) when it really failed, or a test silently run
  in a different order than requested.

## Approaches (default mode — decided)

| | A. `per-method` default until M1's control run (chosen) | B. `class-grouped` default now |
| --- | --- | --- |
| Comparison with the Mid baseline | unchanged | every later result on new semantics |
| Validation | M1's independent Surefire comparison, as the ADR says | our own CI only |
| Cost | one-line follow-up to flip | none |

Chosen by Claude on M2's delegation ("whatever you think is right"): A — it follows the ADR's own
rule and keeps the verifier's run meaningful.

## Design

**Which classes are grouped.** Only classes JUnit runs with its default JUnit 4 runner
(`BlockJUnit4ClassRunner` or its subclass `JUnit4`). JUnit 3 `TestCase` (sorting is silently
ignored — spike), `@RunWith` runners (e.g. `Parameterized`) and `suite()` classes stay one test per
request in either mode. *(Claude's call: the spike proved sorting only for the default runner.)*

**Harness** (`FtHarness <results> [--lifecycle per-method|class-grouped]`, default `per-method`):
read the whole order from stdin; split it into blocks of consecutive same-class tests; per block,
if grouping applies, one `Request.aClass(cls).filterWith(block methods).sortWith(block order)`,
else `runOne` per test as today. The result line format is **unchanged** (index, spec, status,
type, message, frames), so `parse_results` and everything downstream is untouched.

| Case | Result line |
| --- | --- |
| Test finishes | written at `testFinished`, so a crash mid-block keeps earlier results |
| `@BeforeClass` throws (class-level failure before any test) | every test of the block: `FAIL` with that exception — a real failure, not a crash |
| A test JUnit never ran (unknown method) | `FAIL` with the same "No tests found matching" exception today's mode gives |
| `@AfterClass` throws (class-level failure after the tests) | tests keep their own results, as Surefire does; noted in limitations |
| Class appears in two blocks (`A B A`) | two requests, `@BeforeClass` twice — allowed; only a hand-written `--order` makes this |

**Python:** `OrderRunner(..., lifecycle="per-method")` (rejects other values) passes the flag;
`diagnose(..., lifecycle=)`; CLI `--lifecycle {per-method,class-grouped}`; the record header's
`lifecycle` becomes the real mode (job 1 wrote a constant).

**Lifecycle control** — a tiny Maven project, `runner/tests/resources/lifecycle-control/`
(`pom.xml` with JUnit 4.13.2, `src/test/java/LifecycleControlTest.java` exactly as ADR-012 §3).
Being a Maven project is what lets Surefire run it. Expected:

| Execution | Command | Expected |
| --- | --- | --- |
| Surefire | `mvn -B -q -f runner/tests/resources/lifecycle-control/pom.xml test` | both pass |
| Harness `per-method`, `[first, second]` | in `runner/tests/test_order_runner.py` | `second` fails: `expected:<1> but was:<2>` |
| Harness `class-grouped`, same order | same | both pass |

CI (`.github/workflows/ci.yml`, M2's) runs the Surefire line and the runner tests on JDK 8.

**Tests first** (`runner/tests/test_order_runner.py`, real JVM): the three control rows; order
honoured inside a block (`[b, a]` makes `b` see that `a` has not run); `@BeforeClass` failure →
both tests `FAIL` with `IllegalStateException`, not `flaketrace.JvmCrash`; unknown method → real
`FAIL`; JUnit 3 class under `class-grouped` keeps the requested order; `OrderRunner` rejects an
unknown mode; CLI flag reaches `diagnose`; header `lifecycle` equals the mode used; F1 under
`class-grouped` still `POLLUTER_FOUND` with its polluter.

## For M1 and M3 (written into `docs/10-Final1/handover-m1-m3.md`)

**M1 — the control run (W22 verification), on your own machine:** the three commands of the
table above, plus `--lifecycle class-grouped` on fixture F1; record setup counts, pass/fail and any
signature in `docs/evidence-m1.md`, with your JDK and anything unclear. When it matches, M2 flips
the default.

## Left to the builder

Helper names; how the harness tells the default runner apart (runner class check); the exact
"no tests found" exception text (copied from what today's mode produces).

## Limitations to state

`@AfterClass` failures are not attributed to any test in `class-grouped` (Surefire behaves the same
way); JUnit 3, custom runners and `suite()` classes keep `per-method` lifecycle; not run on JDK 8
locally (CI is JDK 8).
