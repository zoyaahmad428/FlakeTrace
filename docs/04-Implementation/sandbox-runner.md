# Order runner — `runner/order_runner.py` + `runner/harness/FtHarness.java` (Member 2)

*Status (2026-10-09): W6 complete — proven on fixture F1 on JDK 21 (local) and JDK 8 (CI);
every test always reported (crash, timeout, skip, bad input). Four-point ownership
note per [[04-Implementation/README]]. Contract: [[contracts/interfaces]] Interface 1. Design:
[[03-Design/decisions/ADR-003-order-runner-junitcore-harness]]. Evidence: [[evidence-m2]].*

## 1. What it does and why it is there

Given a list of JUnit 4 test methods, it runs them **in exactly that order in one fresh JVM**
and returns, for every test, pass or fail plus a normalised failure signature. Shared static
state (the phenomenon FlakeTrace diagnoses) only survives inside one JVM, so everything else —
victim-alone check, polluter search, minimisation, repeated-run verification, and M3's
random-order baseline — is built on this one call.

## 2. Why it is built this way

- **JUnitCore harness, not Maven Surefire.** Surefire orders tests by class and groups methods
  inside their class, so it cannot run `[A#x, B#y, A#z]`; it also costs a Maven start-up per
  call. The harness calls `Request.method` per test, in the order given.
- **Python driver, not all-Java.** The evaluation code (`eval/`) is Python; `run_ordered`
  returns `eval.baseline` types directly with no JSON boundary.
- **The target's own JUnit.** The classpath comes from `mvn dependency:build-classpath`, so no
  dependency is added to the analysed project.
- **Results go to a file, not stdout,** so a test that prints cannot corrupt them.

Rejected: Surefire (cannot honour method order); all-Java runner (second language boundary);
JUnit Platform launcher (needs the Vintage engine, a new dependency).

## 3. What breaks

- **`java`, `javac` or `mvn` missing from PATH** → `RuntimeError("'mvn' not found on PATH")`;
  the real-JVM tests skip (or fail in CI, where `FLAKETRACE_REQUIRE_JVM` is set).
- **Different JDKs print different reflection frames** (`sun.reflect.*` on 8,
  `jdk.internal.reflect.*` on 21). The stack is cut at the first such frame, so assertion
  failures match across JDKs. JDK-internal frames *above* the cut (e.g. `java.lang.Integer.parseInt` when a test passes bad input) keep their line numbers, which differ between JDKs, so such signatures match only within one JDK. Every run of one diagnosis uses the same JDK, so this does not affect a diagnosis; it does mean signatures from different machines are not always comparable. Also, a new JDK with a new internal package would need a new prefix in
  `_FRAMEWORK_PREFIXES`.
- **Working directory:** tests run in `working_dir`; if the caller leaves it `None`, a test that
  opens a relative path (e.g. `new File("pom.xml")`) looks in the caller's directory and fails
  falsely or writes files there.
- **Class-level setup:** each method is its own `Request`, so `@BeforeClass` runs once per
  method. A project whose tests rely on one shared `@BeforeClass` per class could behave
  differently than under Surefire.
- **A JVM that crashes, hangs or skips a test.** The contract says every test must appear in
  the result, so nothing is dropped: tests without a result line fail as `flaketrace.JvmCrash`
  or (after `timeout_s`) `flaketrace.Timeout`; `@Ignore`/`Assume` fail as
  `flaketrace.NotExecuted`, because counting a skip as a pass could make a victim look clean
  when it never ran. A misspelt class or method fails with the JVM's own exception and the
  rest of the order still runs. A duplicate test in one order raises `ValueError` (the result
  is keyed by test and cannot hold two outcomes).

## 4. How to modify it

- **Run consecutive methods of the same class in one `Request`** (to match Surefire's
  `@BeforeClass` behaviour): change `FtHarness.runOne` to take a group of methods and use
  `Request.aClass(cls).filterWith(...)` with an ordering; the result lines must still be one
  per test, so `parse_results` is unchanged.
- **Support a new JDK's reflection package:** add its prefix to `_FRAMEWORK_PREFIXES` and a
  frame list for it to `TestNormalisation` in `runner/tests/test_order_runner.py`.
