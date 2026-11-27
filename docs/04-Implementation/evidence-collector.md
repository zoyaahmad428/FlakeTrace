# Evidence collector — `evidence/extract.py` (Member 1)

*Status (2026-11-20): Iteration 1, Phases 2–6 and ADR-006: depth 1–5, single-test and pair mode, pair-mode auto-deepening; wording qualified for W16 (claims ledger G3); every edge in `resource_edges` (W21); `rank_candidates` with a per-test cache (W25 part 1, ADR-014 §5). The ranking rule is not yet measured on any case. Four-point ownership note per
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
`report_fields` projects the first edge into Member 3's report. An edge is a **static overlap —
a possible mechanism, not confirmed as the cause**: the extractor sees that the code *may* write
and read the same resource, not that it did, with what value, or in what order (ledger G3). This
is the *where to look* part of the certificate: without it FlakeTrace can only say "this order
fails", which iDFlakies already does. `rank_candidates` (W25) uses the same edges *before* the
search, to choose which candidate polluter to try first: most shared resources, then shallowest
edge, then original position. It never removes a candidate.

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

- **Ranking is a sort key, not a weighted score.** A tuple compared left to right (ADR-014 §5)
  has nothing to fit, so it cannot be tuned to the cases it is measured on. With no evidence it
  gives exactly the original order. Whether it beats `original` anywhere else is for the
  measurement (W25, M3) to show, not for this design to claim.
- **One analysis per test, cached.** A pair analysis per candidate would analyse the victim N
  times. `AnalysisCache` keeps each test's Output 1 and reuses `find_edges` on it.

Rejected: ASM/Javassist (dependency, offset workaround); copying the POC code (team docs; ownership);
the POC's class-initialiser and co-touch terms in the first ranking (ADR-014 §5: each only with a
measured comparison).

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
  `JSON.defaultLocale` and names `JSON.defaultTimeZone` in `limitations`. The test's own
  constants point to the time zone, but no run has confirmed which field makes it fail.
- **Virtual dispatch.** Only the statically named target is followed. If a subclass
  overrides it, the code that really runs is not analysed; `VIRTUAL_DISPATCH` says so. An
  interface call with no default method has nothing to scan.
- **Calls into the JDK or third-party jars are never followed** (e.g. a library that sets a
  system property internally is invisible). They are listed in `external_calls_not_followed`.
- **State changed through the object a static field holds is not a write.** On the real case
  FJ-03, the polluter and the victim both only *read* the static `SerializeWriter.bufLocal` (a
  `ThreadLocal`). The pollution is the polluter's `bufLocal.set(buf)`, a call into the JDK that is
  not followed, so there is no WRITE and no edge, even at depth 5 (investigated 2026-11-20,
  [[evidence-m1]]). A READ on both sides of one static field is exactly ADR-014's deferred
  "co-touch" term. It is not in the ranking rule, and per plan rule 4 it can be added only as a new,
  separately committed rule, measured on cases other than FJ-03.
- **Not seen at all:** reflection, invokedynamic bodies, keys built at runtime, `@Rule`/`@RunWith`
  code, implicit `<clinit>` of other classes, and the test class constructor and instance-field
  initialisers. The first five are reported as unsupported observations; the constructor is a
  known gap (see the open points in [[evidence-m1]]).
- **An empty edge list is not proof of independence.** The pair output always says so
  (`no_supported_resource_evidence`, fixed limitation 7). A polluter that restores the value
  it wrote still produces an edge, because values are not modelled.
- **Only one edge is the report's headline.** `shared_resource` and the two locations hold the
  first edge; every edge is listed in `resource_edges` (W21, schema v2), and `limitations` names
  each further one as "not the headline resource; it is listed in resource_edges". Before
  2026-11-20 that line said "not shown in this report", which stopped being true once
  `resource_edges` existed (found by M2 verifying W21).
- **Ranking inherits every blind spot above.** A polluter that writes through reflection, a
  library or an unresolved virtual call has no edge, so it keeps its original position. It is
  never dropped. A restoring polluter still ranks first (FT005 control 1), because values are
  not modelled.
- **Input errors** (missing directory, unknown class/method, bad depth, bad flag combination): exit code 2
  with `error: …` on stderr. javap missing or failing: exit code 1.

## 3a. Is anything injected? Static evidence, and the runtime fallback

*Panel action A2 (proposal defence): "Say whether trace instructions are injected". Written
2026-11-25.*

- **No.** FlakeTrace injects nothing into the code under test: no agent and no source edits. The
  evidence collector reads the **compiled** `.class` files with `javap` (ADR-001). The runner builds
  the project normally with Maven (`test-compile`) and re-runs the project's own tests in chosen
  orders, on a disposable copy by default (ADR-012).
  The report states this as `instrumentation_level: "static-only"`.
- **What the static evidence is.** An edge means: the polluter's code *may* write a resource that
  the victim's code *may* read. It is a **potential overlap: a possible mechanism, not confirmed as
  the cause** (claims ledger G3, FT005). Every report carries the fixed limitations, the first of
  which is "Static analysis only; no runtime evidence". `assurance.resource` is
  `STATIC_OVERLAP` (or `NONE` when no edge was found), with `mechanism: NOT_ASSESSED`; it is
  never `MECHANISM_CONFIRMED`. Section 3 lists what static
  analysis cannot see.
- **The approved runtime fallback, and its status.** ADR-001 names a **runtime Java agent** as
  the **Iteration 2 fallback**, for cases static evidence cannot resolve. It would instrument
  bytecode **in memory**, on a temporary copy, and only for the already-reduced sequence. Its
  skill risk and its risk of perturbing the failure were ADR-001's reasons for not starting with an
  agent, not the reason it is unbuilt now. In Iteration 2 the team instead accepted ADR-015's
  cheaper intervention check as a **spike** only (W34, a stretch goal): put the named resource back
  to its earlier value between polluter and victim, and see whether the failure goes away.
  **Neither is built.** No report today claims more than a static overlap. Whether causal
  certification of the resource remains a promise, and by which milestone, is a question for the
  supervisor ([[10-Final1/supervisor-agenda]], item 2).
- **A real case that needs it.** On fastjson FJ-03 the static evidence finds **no** edge. The
  pollution goes through a static `ThreadLocal` that both tests only read, via a JDK call (section
  3; [[evidence-m1]]). So FlakeTrace says `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`, not
  `VERIFIED`. ADR-015's check cannot help here as designed, because it resets the resource static
  analysis names, and here there is none. Only runtime observation could name the resource.

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
- **Change the ranking rule:** `rank_candidates`'s `order` function and the `score` tuple, with
  tests in `RankCandidatesTest`. Any change after measurement has started must be recorded as a
  new rule, with its own commit before it is run (iteration-2-plan rule 4), and Member 2 must
  review it.
- **Change how calls are followed:** `walk_root` (breadth-first queue, visited set) and
  `follow_call` (resolve the named target, record `VIRTUAL_DISPATCH`/`DEPTH_LIMIT`/
  `UNRESOLVED_CALL`). To follow overrides you would have to load every project class to find
  subclasses: that is a precision/cost decision for an ADR.
