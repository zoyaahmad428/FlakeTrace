# Evidence collector — `evidence/extract.py` (Member 1)

*Status (2026-10-10): Iteration 1, Phases 2–6 and ADR-006: depth 1–5, single-test and pair mode, pair-mode auto-deepening. Four-point ownership note per
[[04-Implementation/README]]. Contract: [[contracts/resource-evidence]]. Decisions:
[[03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation]],
[[03-Design/decisions/ADR-002-evidence-extractor-implementation]],
[[03-Design/decisions/ADR-006-evidence-depth-auto-deepen]].*

## 1. What it does and why it is there

Given a compiled project and one test method (`Class#method`), it reports every **static-field**
read/write (`getstatic`/`putstatic`) and every **system-property** read/write with a constant key
(`System.setProperty/clearProperty/getProperty`, `Integer.getInteger`, `Long.getLong`,
`Boolean.getBoolean`). It covers the test method **and the lifecycle code that runs with it**:
JUnit 4 `@Before/@After/@BeforeClass/@AfterClass`, JUnit 3 `setUp/tearDown`, the `<clinit>`
of the test class, and lifecycle methods inherited from project superclasses. Each access
records the class, method and bytecode offset, and which lifecycle method it came from (`via`).
Given a polluter and a victim, `find_edges` keeps every resource the polluter WRITES
(any root, including `@After`/`tearDown`) that the victim READS, with both sides' locations.
`analyse_pair` does this for a pair and, when there is no edge and a walk was cut off at the
depth limit, repeats it one level deeper (up to 5); the shallowest depth with an edge wins.
`report_fields` projects the first edge into Member 3's report. This is the *where exactly* part of the certificate: without it FlakeTrace can only say "this
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
  Pair mode deepens past the default only when nothing was found and a walk was cut off; real
  fastjson needed depth 4 (FJ-01) and 5 (FJ-02). Deeper evidence over-approximates more, so the
  report says so in `limitations` whenever its write or read is deeper than 2.
- **Two shared resources at the same depth.** The report shows one, picked by the contract's
  order (combined depth, then `resource_id`), not by which one caused the failure. FJ-01 reports
  `JSON.defaultLocale` and names `JSON.defaultTimeZone` (the real cause) in `limitations`.
- **Virtual dispatch.** Only the statically named target is followed. If a subclass
  overrides it, the code that really runs is not analysed; `VIRTUAL_DISPATCH` says so. An
  interface call with no default method has nothing to scan.
- **Calls into the JDK or third-party jars are never followed** (e.g. a library that sets a
  system property internally is invisible). They are listed in `external_calls_not_followed`.
- **Not seen at all:** reflection, invokedynamic bodies, keys built at runtime, `@Rule`/`@RunWith`
  code, implicit `<clinit>` of other classes, and the test class constructor and instance-field
  initialisers. The first five are reported as unsupported observations; the constructor is a
  known gap (see the open points in [[evidence-m1]]).
- **An empty edge list is not proof of independence.** The pair output always says so
  (`no_supported_resource_evidence`, fixed limitation 7). A polluter that restores the value
  it wrote still produces an edge, because values are not modelled.
- **Only one edge fits Member 3's report.** `report_fields` names the rest in `limitations`
  (contract open question 1).
- **Input errors** (missing directory, unknown class/method, bad depth, bad flag combination): exit code 2
  with `error: …` on stderr. javap missing or failing: exit code 1.

## 4. How to modify it

- **Add a supported system-property method** (e.g. a new `Properties` accessor): add one entry
  to `SYSPROP_CALLS` and one test in `evidence/tests/test_extract.py`.
- **Add a lifecycle kind** (e.g. JUnit 5 `@BeforeEach`): add it to `LIFECYCLE_ANNOTATIONS` and
  `VIA_ORDER`. Because `via` is part of the output, update the contract table too, which needs
  all three members.
- **Change the depth range:** change `MAX_DEPTH` (accepted values follow). Update the
  contract's Terms (1–5) with all three members, and re-run `evidence.tools.measure_depth`.
- **Change when pair mode deepens:** the loop in `_analyse_pair` (stop condition: an edge, no
  `DEPTH_LIMIT`, `deepen=False`, or `MAX_DEPTH`).
- **Change how calls are followed:** `walk_root` (breadth-first queue, visited set) and
  `follow_call` (resolve the named target, record `VIRTUAL_DISPATCH`/`DEPTH_LIMIT`/
  `UNRESOLVED_CALL`). To follow overrides you would have to load every project class to find
  subclasses: that is a precision/cost decision for an ADR.
