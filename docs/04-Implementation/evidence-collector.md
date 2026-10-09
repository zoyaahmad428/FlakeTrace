# Evidence collector — `evidence/extract.py` (Member 1)

*Status (2026-10-09): Phase 3 of Iteration 1: depth 1–3, single-test mode. Four-point ownership note per
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
- **Accesses deeper than `--depth`** are not reported; a `DEPTH_LIMIT` observation marks where
  the walk stopped. Depth 2 is the default because F2's read is one call below the test.
- **Virtual dispatch.** Only the statically named target is followed. If a subclass
  overrides it, the code that really runs is not analysed; `VIRTUAL_DISPATCH` says so. An
  interface call with no default method has nothing to scan.
- **Calls into the JDK or third-party jars are never followed** (e.g. a library that sets a
  system property internally is invisible). They are listed in `external_calls_not_followed`.
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
- **Allow depth 4:** add 4 to `IMPLEMENTED_DEPTHS`. Update the contract's Terms (1–3) with
  all three members, and re-run `evidence.tools.measure_depth` to report its cost.
- **Change how calls are followed:** `walk_root` (breadth-first queue, visited set) and
  `follow_call` (resolve the named target, record `VIRTUAL_DISPATCH`/`DEPTH_LIMIT`/
  `UNRESOLVED_CALL`). To follow overrides you would have to load every project class to find
  subclasses: that is a precision/cost decision for an ADR.
