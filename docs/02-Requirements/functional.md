# Functional Requirements

*Status: `PROPOSED` — to be baselined at Mid-1.* Derived from the committed scope in
[[02-Requirements/scope-boundary]].

---

| ID | Requirement | Acceptance |
| --- | --- | --- |
| **FR-1** | Accept a pinned repository, module, target test and execution budget; validate the project, discover tests, and record the environment (image digest, JDK, Maven, Surefire, JUnit versions, locale, timezone) | A frozen, reproducible case identity is emitted and stored |
| **FR-2** | Execute declared test orders in a sandboxed container, **one fresh JVM per order**, with execution-context fidelity for projects whose Surefire configuration runs suite classes | Outcomes are normalised to a failure signature; budgets and timeouts enforced; cleanup verified |
| **FR-3** | Collect bounded resource events for the three committed families, attributed to test boundaries including `setUp`, `tearDown` and `<clinit>`, at **configurable analysis depth** | Every reported event names the resource identifier and bytecode offset; events outside a test boundary are recorded as such, **never attributed to the next test** |
| **FR-4** | Rank candidates and select the next experiment by **expected information gain per unit estimated cost**, reserving verification budget that the search may not draw down | Two policies implemented: ranked one-by-one (simple) and cost-aware adaptive (student-designed). Both evaluated |
| **FR-5** | Minimise the reproducing order with **1-minimality deletion checks** and counterfactual checks, then verify by repeated clean-container replay with a Wilson interval | Deletion-minimality rate measured; multi-test candidates preserved rather than discarded |
| **FR-6** | Emit **Verified / Candidate / Unresolved** with a machine-readable typed reason, a human-readable report, an exact replay command, and the evidence bundle | Contents per [[03-Design/certificate-contract]]; **no numeric confidence score** |
| **FR-7** | Provide a CLI with CI-compatible exit codes and published artifacts, installable on clean Linux from documentation | [[02-Requirements/non-functional]] NFR-2 |

## Status after the Mid review (2026-11-13)

One status per requirement, read from the code at `main` `7cf453d` and the supervisor's review.
**This table is the single place a requirement's status is stated**; the report's tables are
copied from it (FT017 found FR-1 "Partial" in one table and "Done" in another).

| ID | Status | Built | Not built or found wrong | Closes with |
| --- | --- | --- | --- | --- |
| FR-1 | **Partial** | Project and victim accepted; tests discovered; JDK, OS, project commit recorded | No budget input. No Maven, Surefire, JUnit version, locale, timezone or image digest in the record | W22, W24 |
| FR-2 | **Partial** | Exact order, one fresh JVM per order, signatures, per-run timeout | No container. Class-level lifecycle runs per method (FT006). No budget enforcement. No verified cleanup | W22, W24, W27 |
| FR-3 | **Partial** | Static fields and constant-key system properties, with offsets, lifecycle attribution, depth 1–5 | Filesystem family. Evidence is static only | FYP-2 |
| FR-4 | **Not built** | A `priority` argument nobody passes | Ranking, budget, reserve, both policies (FT007) | W24, W25; adaptive policy FYP-2 |
| FR-5 | **Partial — with a defect** | One-by-one search, `ddmin`, repeated replay with a Wilson interval | Deletions never repeated (FT004). "Passes alone" checked against the reference signature only (FT003). No counterfactual resource check | W18, W19, W20 |
| FR-6 | **Partial** | Three classes, typed reasons, JSON report and summary | One status has no report (FT010). No replay command, no bundle (FT009). Resource evidence worded too strongly (FT005) | W19, W21, W23 |
| FR-7 | **Partial** | One command with exit codes; CI on JDK 8 | Not installable on clean Linux from documentation | W27; install FYP-2 |

**Wording corrected by the review.** Where a requirement's acceptance text is stronger than what
any check can show, the acceptance text is what changes — openly, in the report's requirements
chapter, with the date:

| Requirement text | Becomes |
| --- | --- |
| FR-5 "1-minimality deletion checks" | "…each kept predecessor removed and the sequence repeated `m` times (ADR-011)" |
| FR-6 "a resource-event path" (via the certificate contract) | "…a static write/read overlap, labelled as such; a confirmed mechanism only where an intervention was run" |
| The frozen definition "while `[v]` alone passes" | Unchanged — and now implemented literally: **every** alone run passes (ADR-010) |

## Traceability

| FR | Component | Owner |
| --- | --- | --- |
| FR-1 | Project adapter | M2 |
| FR-2 | Sandbox runner, outcome normaliser | M2 |
| FR-3 | Evidence collector, test–resource graph | M1 |
| FR-4 | Diagnosis planner | M2 |
| FR-5 | Minimiser, verifier | M2 |
| FR-6 | Certificate generator (evidence path: M1) | M2 + M1 |
| FR-7 | CLI / CI adapter | M2 |

Evaluation infrastructure spanning all of these: **M3**.

## Frozen definitions these depend on

Committed to version control **before any experiment ran** — reproduced here because several FRs
are meaningless without them.

**Candidate set.** All test methods in the victim's Maven module, excluding the victim. For
JUnit 3 subjects, a test method is a public no-arg method named `test*` on a
`junit.framework.TestCase` subclass. **If the module exceeds 300 such methods, restrict to the
victim's package and record the cap as a declared limitation.**

**Order-dependent (polluter).** A candidate *c* such that `[c, v]` executed in a single JVM
produces the target failure signature for victim *v*, while `[v]` alone passes.

**Failure signature.** The triple (exception FQCN, normalised first line of message, topmost
stack frame inside the project package). Digits, hex addresses, temporary paths and timestamps
masked. **A timeout, compilation error or OOM is NOT the same reproduction as the intended
assertion failure.**

**Confirmation and cost unit.** One confirmation is one execution of one candidate order. The
primary cost unit is **test-method invocations**, not Maven launches.

**Reproduced case.** The victim passes alone ≥ 10/10 **and** fails with the matching signature in
≥ 9/10 replays of the confirmed polluting order.

**Resource identifier.** `ownerInternalName.fieldName:descriptor`, static fields only
(`getstatic`/`putstatic`), direct references plus a declared number of hops into project-owned
callees. Attribution per test method includes the method, the class's `setUp` and `tearDown`, and
the class's `<clinit>`. Reflection, filesystem, system properties, network and database state are
**out of scope and recorded as unsupported, never as zero-overlap**.

**Single-scan protocol.** The exhaustive scan runs **once per case**. Ground truth, the
one-by-one baseline, random baselines and the ranked strategy are all computed offline from that
outcome table. **No strategy triggers a re-run.**

> **Amendment recorded 27 August 2026:** execution-context fidelity added to the runner
> definition, requiring invocation of a project's test-suite `@BeforeClass` where its Surefire
> configuration runs suite classes rather than test classes. This corrected a defect producing
> false positives. **It changed neither the reproduction criterion nor the strategy scoring.**
> *(Disclose this unprompted — it moved a result from 182 to 0, against our own interest.)*
