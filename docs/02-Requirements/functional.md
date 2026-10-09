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
