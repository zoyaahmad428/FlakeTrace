# W22 job 3 — class-grouped execution and the lifecycle control: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `--lifecycle class-grouped` runs consecutive same-class tests as one JUnit request (class
lifecycle once per block); a lifecycle control runs under Surefire and both harness modes.

**Architecture:** the harness splits the order into blocks and, for classes on JUnit's default
runner, runs one filtered and sorted request per block, writing each result at `testFinished`. The
result line format is unchanged. Python passes the mode from the CLI through `diagnose` to
`OrderRunner` and records it in the header.

**Tech Stack:** Java 8 source level, JUnit 4.13.2, Python 3 `unittest`, Maven, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-11-14-w22-class-grouped-execution-design.md`

**Branch:** `m2/w22-record-env` (the W22 package branch, after `862bb82`).

## Global Constraints

- Default mode stays `per-method` everywhere (harness, `OrderRunner`, `diagnose`, CLI).
- Mode values exactly `per-method` and `class-grouped`.
- Grouped only when `Request.aClass(cls).getRunner().getClass()` is `org.junit.runners.JUnit4` or
  `org.junit.runners.BlockJUnit4ClassRunner` (verified 2026-11-14: a plain JUnit 4 class gets
  `JUnit4`; JUnit 3 gets `JUnit38ClassRunner`; `@RunWith(Parameterized)` gets `Parameterized`).
- Result line format unchanged: `index\tspec\tstatus\ttype\tmessage\tframes`.
- Harness compiles with `-source 8 -target 8`.
- Member 2 commits; the agent hands over commands.

## Review Focus

1. A class that fails to load inside a `class-grouped` block → every test of the block `FAIL` with
   the load exception, as `per-method` does today. *(Task 1 test.)*
2. The JVM dies mid-block → tests that finished keep their lines; the rest become
   `flaketrace.JvmCrash`. *(Task 1 test.)*
3. The same test requested twice is still refused by `OrderRunner` before the harness. *(existing test.)*
4. A class appearing in two blocks (`A B A`) → both `A` blocks run, each with its own setup, results
   for all three. *(Task 1 test.)*
5. An unknown `--lifecycle` value → `ValueError` from `OrderRunner`, argparse error from the CLI. *(Tasks 1, 2.)*

---

### Task 1: harness `class-grouped` mode, `OrderRunner(lifecycle=)`, the lifecycle control

**Files:**
- Create: `runner/tests/resources/lifecycle-control/pom.xml` (groupId `flaketrace`, artifactId
  `lifecycle-control`, JUnit 4.13.2 test scope, `maven.compiler.source/target` 1.8, UTF-8)
- Create: `runner/tests/resources/lifecycle-control/src/test/java/LifecycleControlTest.java` (ADR-012 §3, exactly)
- Create: `runner/tests/resources/OrderProbeTest.java` (`static StringBuilder log`; `a()` appends
  "a"; `b()` asserts `log.toString()` equals `"a"`; `exits()` calls `System.exit(3)`)
- Create: `runner/tests/resources/BrokenSetupProbeTest.java` (`@BeforeClass` throws
  `IllegalStateException("setup broke")`; tests `a`, `b`)
- Modify: `runner/harness/FtHarness.java`, `runner/order_runner.py`
- Modify: `.github/workflows/ci.yml` (runner job: a step running Surefire on the control project)
- Test: `runner/tests/test_order_runner.py`

**Interfaces:**
- Produces: `OrderRunner(classpath, working_dir=None, timeout_s=120.0, lifecycle="per-method")`;
  attribute `OrderRunner.lifecycle`; `LIFECYCLES = ("per-method", "class-grouped")` in `runner/order_runner.py`.
- Harness CLI: `FtHarness <results> [--lifecycle <mode>]`.

- [ ] **Step 1: Write the failing tests**

New class `TestLifecycleControl` (real JVM, same skip/require guard as `TestOrderRunnerOnF1`;
classpath `maven_test_classpath(CONTROL)` with `CONTROL = resources/lifecycle-control`):
```python
FIRST, SECOND = TestIdentifier("LifecycleControlTest", "first"), TestIdentifier("LifecycleControlTest", "second")
def test_per_method_runs_class_setup_per_test(self):
    r = OrderRunner(self.classpath).run_ordered([FIRST, SECOND])
    self.assertTrue(r[FIRST].passed)
    self.assertEqual(r[SECOND].failure_signature.message, "expected:<<N>> but was:<<N>>")
    self.assertEqual(r[SECOND].failure_signature.exception_type, "java.lang.AssertionError")
def test_class_grouped_runs_class_setup_once(self):
    r = OrderRunner(self.classpath, lifecycle="class-grouped").run_ordered([FIRST, SECOND])
    self.assertTrue(r[FIRST].passed and r[SECOND].passed)
def test_unknown_lifecycle_is_refused(self):
    with self.assertRaises(ValueError):
        OrderRunner(self.classpath, lifecycle="per-class")
```
In `TestOrderRunnerOnProbes` (compile the two new probe files too; add a `grouped` runner
`OrderRunner(cls.classpath, lifecycle="class-grouped")`):
- `test_grouped_block_runs_in_the_requested_order`: `[OrderProbeTest#b, OrderProbeTest#a]` → `b`
  fails (`ComparisonFailure` or `AssertionError`), `a` passes; `[a, b]` → both pass.
- `test_grouped_setup_failure_fails_every_test_of_the_block`: both `BrokenSetupProbeTest` tests →
  `exception_type == "java.lang.IllegalStateException"`.
- `test_grouped_unknown_method_is_a_real_failure`: `[OrderProbeTest#nope, OrderProbeTest#a]` →
  `nope` type `java.lang.Exception`, `a` passes.
- `test_grouped_junit3_keeps_the_requested_order`: `[JUNIT3_VICTIM, JUNIT3_POLLUTER]` gives the
  same outcomes as the `per-method` runner on the same order.
- `test_grouped_class_in_two_blocks_runs_both`: `[OrderProbeTest#a, <ProbeTest test that passes>, OrderProbeTest#b]`
  → three results; `b` passes (static log survives in the JVM).
- `test_grouped_class_that_cannot_load_fails_every_test`: two specs of `NoSuchClass` → both
  `java.lang.ClassNotFoundException`.
- `test_grouped_crash_mid_block_keeps_finished_results`: `[OrderProbeTest#a, OrderProbeTest#exits,
  OrderProbeTest#b]` (`exits()` calls `System.exit(3)`) → `a` passes; `exits` and `b` are
  `flaketrace.JvmCrash`.

- [ ] **Step 2: Run, expect failure** — `py -3 -m unittest runner.tests.test_order_runner`;
  expected `TypeError: ... unexpected keyword argument 'lifecycle'` and the control's grouped test
  failing.

- [ ] **Step 3: Implement**
  - Harness: parse `--lifecycle` after `args[0]`; read all stdin lines; split into blocks of
    consecutive equal class names; `per-method` or non-default runner → existing `runOne` per test;
    otherwise one request with `filterWith` (method names of the block) and `sortWith` (index in
    block), a `RunListener` that collects failure/skip per method and **writes the line at
    `testFinished`**; a class-level failure (description without method name) before any test →
    after the run, every block test without a line gets `FAIL` with it; any remaining test without
    a line gets `format("FAIL", new Exception("No tests found matching Method <m>(<class>) from org.junit.internal.requests.ClassRequest@..."))`
    — copy the exact message shape today's `Request.method` failure has (run it once and read it).
  - Python: validate `lifecycle in LIFECYCLES` in `__init__`; pass `["--lifecycle", mode]` after
    the results path in `run_ordered` only (not `--list`/`--env`).
  - CI: in the `runner` job, a step `Lifecycle control under Surefire (ADR-012 §3)`:
    `mvn -B -q -f runner/tests/resources/lifecycle-control/pom.xml test`.

- [ ] **Step 4: Run, expect pass** — `py -3 -m unittest runner.tests.test_order_runner` OK;
  `mvn -B -q -f runner/tests/resources/lifecycle-control/pom.xml test` exits 0.

- [ ] **Step 5: Hand over the commit.**

---

### Task 2: `--lifecycle` through `diagnose` and the CLI, the header, docs and M1's instructions

**Files:**
- Modify: `runner/diagnose.py` (`diagnose(..., lifecycle="per-method")` → `OrderRunner(..., lifecycle=)`; header `"lifecycle": lifecycle`)
- Modify: `runner/cli.py` (`--lifecycle`, `choices=LIFECYCLES`, default `per-method`, passed to `diagnose`)
- Test: `runner/tests/test_cli.py`, `runner/tests/test_diagnose.py`
- Docs: `runner/README.md`, `docs/04-Implementation/sandbox-runner.md` (harness modes),
  `docs/04-Implementation/diagnose-cli.md` (flag), ADR-012 (status of §2/§3: built, default not
  flipped), `docs/evidence-m2.md`, `docs/genai-log-m2.md`, `docs/08-MidEval/genai-register.md`,
  `docs/10-Final1/iteration-2-plan.md`, `docs/09-Team/members.md`,
  `docs/10-Final1/handover-m1-m3.md` (M1's control-run steps, exactly as in the spec), root
  `README.md` + `CLAUDE.md` §8 only if a new command is needed for running tests (the Surefire
  control command).

**Interfaces:**
- Consumes: `OrderRunner(..., lifecycle=)`, `LIFECYCLES` (Task 1).

- [ ] **Step 1: Write the failing tests**
  - `test_cli.py`: `--lifecycle class-grouped` reaches the mocked `diagnose` as
    `kwargs["lifecycle"] == "class-grouped"`; no flag → `"per-method"`; `--lifecycle per-class` →
    exit 2 (argparse).
  - `test_diagnose.py` `TestDiagnoseOnFixture`: `diagnose(FIXTURE, F1 victim, n=3,
    lifecycle="class-grouped")` → `POLLUTER_FOUND`, F1's polluter, header `lifecycle ==
    "class-grouped"`; the job-1 header test keeps `"per-method"` by default.

- [ ] **Step 2: Run, expect failure** (`KeyError: 'lifecycle'` / unexpected keyword).

- [ ] **Step 3: Implement** as in Files.

- [ ] **Step 4: Run the whole suites** — every `runner/tests/test_*.py`, every
  `eval/tests/test_*.py`, `ui.tests.test_server`; the real CLI on F1 with `--lifecycle class-grouped`.

- [ ] **Step 5: Docs, final review (fresh reviewer), verification, hand over the commit.**
