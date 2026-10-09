# Evidence collector — `evidence/extract.py` (Member 1)

*Status (2026-10-09): Phase 2 of Iteration 1, depth 1 only. Four-point ownership note per
[[04-Implementation/README]]. Contract: [[contracts/resource-evidence]]. Decisions:
[[03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation]],
[[03-Design/decisions/ADR-002-evidence-extractor-implementation]].*

## 1. What it does and why it is there

Given a compiled project and one test method (`Class#method`), it reports every **static-field**
read/write (`getstatic`/`putstatic`) and every **system-property** read/write with a constant key
(`System.setProperty/clearProperty/getProperty`, `Integer.getInteger`, `Long.getLong`,
`Boolean.getBoolean`). It covers the test method **and the lifecycle code that runs with it**:
JUnit 4 `@Before/@After/@BeforeClass/@AfterClass`, JUnit 3 `setUp/tearDown`, the `<clinit>`
of the test class, and lifecycle methods inherited from project superclasses. Each access
records the class, method and bytecode offset, and which lifecycle method it came from (`via`).
This is the *where exactly* part of the certificate: without it FlakeTrace can only say "this
order fails", which iDFlakies already does.

## 2. Why it is built this way

- **javap text, not a bytecode library.** `javap -c` prints each instruction's offset, and the
  offset is the evidence. ASM does not expose offsets without a workaround and adds a dependency
  (ADR-002).
- **Written fresh, not copied from the POC.** The POC script was the reference idea only.
- **Annotations are resolved through the constant pool.** JDK 8 `javap -v` prints
  `0: #19()` instead of the annotation name. The same lookup works on newer JDKs.
- **A system-property key is trusted only when it is provably constant.** All call arguments must
  be pushed by one simple instruction each, and the first must be a string constant. Anything
  else is reported as `SYSPROP_NON_CONSTANT_KEY` rather than guessed.

Rejected: ASM/Javassist (dependency, offset workaround); copying the POC code (team docs; ownership).

## 3. What breaks

- **javap output format.** A JDK whose `javap -v` layout differs would break parsing. Mitigation:
  the tests run on real JDK 8 and JDK 21 output and fail loudly (a padding bug in the
  constant-pool regex was caught this way on 2026-10-09).
- **Depth 1 misses accesses one call away.** Fixture F2's victim reads its property inside
  `FeatureFlags.isTurboEnabled()`, so at depth 1 it shows only `DEPTH_LIMIT`. Phase 3 adds depth.
- **Not seen at all:** reflection, invokedynamic bodies, keys built at runtime, `@Rule`/`@RunWith`
  code, implicit `<clinit>` of other classes, and the test class constructor and instance-field
  initialisers. The first five are reported as unsupported observations; the constructor is a
  known gap (see the open points in [[evidence-m1]]).
- **Input errors** (missing directory, unknown class/method, unimplemented depth): exit code 2
  with `error: …` on stderr. javap missing or failing: exit code 1.

## 4. How to modify it

- **Add a supported system-property method** (e.g. a new `Properties` accessor): add one entry
  to `SYSPROP_CALLS` and one test in `evidence/tests/test_extract.py`.
- **Add a lifecycle kind** (e.g. JUnit 5 `@BeforeEach`): add it to `LIFECYCLE_ANNOTATIONS` and
  `VIA_ORDER`. Because `via` is part of the output, update the contract table too, which needs
  all three members.
- **Follow calls (Phase 3):** extend `scan_call`, which today records `DEPTH_LIMIT` for project
  calls, to recurse with a visited set and a growing `call_path`. Then add 2 and 3 to
  `IMPLEMENTED_DEPTHS`.
