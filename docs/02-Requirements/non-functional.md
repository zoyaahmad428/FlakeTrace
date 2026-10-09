# Non-Functional Requirements

*The guide requires at least one **measurable** NFR — measured against a stated target, with a
defined measurement procedure, and a consequence for breach. We have two.*

---

## NFR-1 — Instrumentation overhead

**Measure:** median and p95 runtime overhead **relative to uninstrumented execution**.

**Why it qualifies:**
- ✅ measured against a stated target rather than asserted
- ✅ defined measurement procedure
- ✅ **has a consequence** — exceeding it triggers the fallback to a lighter collection mode

**Threshold:** ⚠ **no number yet, deliberately.**

> We are not inventing a final overhead figure before we measure it.

**The envelope we do have:**

| Source | Bound |
| --- | --- |
| SH1 (Inspirovix) | 5–15 min additional acceptable on PR CI **if it does not run on every successful build** |
| SH3 (Learnsignal) | 5 min → "pushback"; **15 min → "completely unacceptable"** on every PR. **30 min entirely tolerable** opt-in or as a scheduled nightly workflow |
| ElectricTest [10] | ~**20× slowdown** for sound dependency detection — the ceiling of what this class of technique can cost |
| PolDet over JPF [34] | 1.43× relative to base JPF |

**Design consequence, directly from the stakeholder numbers:** the tool is **invoked on demand
for a known failing test, not run on every build**. Both stakeholders' figures support that
boundary — and it is the answer to Q81 on CI integration.

## NFR-2 — Clean-machine deployment

> A **third party** installs the product on **clean Linux from documented instructions**, runs
> **one frozen benchmark case**, obtains the **same certificate class**, **replays** the returned
> order, and **removes all created containers and workspaces**.

**Someone outside the team performs it.** A demo on a laptop does not count.

This is a **testable acceptance condition, not a claim**, and it is a **Final-2 exit
requirement**.

---

## The non-perturbation control — NFR-adjacent, and committed

> For every case: execute the **passing order and the failing order**, each **uninstrumented and
> instrumented** — **all four outcomes must match the expected signature** before any measurement
> is accepted.

**Committed as a testable requirement, not a practice.** Our own timezone defect would have
been caught by it on the first run.

Priority 5 of the pre-defence items: same order 10× under our runner and 10× under unmodified
Surefire, signatures compared. *Answers "how do you know your tool did not create the failure"
with measurement rather than assertion.*

---

## Security requirements for executing untrusted tests

| Requirement | Detail |
| --- | --- |
| Container | **Rootless**; no Docker socket mounted; Linux capabilities dropped; no privileged mode |
| Network | **Disabled by default**; allowlisted dependency-fetch stage **separated** from test execution |
| Limits | CPU, memory, PID, file-size and wall-time; process-group termination; **verified cleanup** |
| Filesystem | Read-only base; isolated writable workspace; **no host home-directory mount** |
| Secrets | **No CI secrets, SSH agents or cloud credentials** in the execution environment |
| Data | Path and log **redaction**; configurable retention; source and artifacts remain self-hosted |
| Audit | Every command, image digest, input commit and environment variable |
| **CDR additions** | Only certificate-directed code slices may leave the machine, **after redaction**; a configuration flag **disables all external calls** for on-premises users; prompts and responses logged in full |

**Tested adversarially rather than asserted.** A security-test escape or repeated cleanup
failure is a **trigger in the risk register**.

⚠ **We do not claim safe multi-tenant execution.** If clean sandboxing cannot be defended at
evaluation, the fallback limits the product to **explicitly trusted local projects**, and we
state that boundary rather than hiding it.

### The two-phase network model (Q79)

> A **dependency-fetch phase** runs with an allowlist to a configured repository mirror and
> populates a local cache. The **test-execution phase** runs with networking **disabled** against
> that cache. They are **separate container invocations with separate policies**, so test code
> never has network access even though the build did.

**Also improves reproducibility:** a cached, digest-recorded dependency set means a rerun three
months later resolves the same artifacts.

---

## Success criteria (Q71) — with their status honestly marked

| Criterion | Value | Status |
| --- | --- | --- |
| Median test-method invocations vs iFixFlakies / unguided minimisation, at same isolation-success level | **≥ 25% lower** on the overlapping solvable subset | ⚠ **PROJECT-SET** |
| Success-at-budget vs strongest feasible comparator | **≤ 5 percentage points lower**, reported with **paired confidence intervals** rather than averages | ⚠ **PROJECT-SET** |
| Verified certificate | ≥ 18 matching failures in 20 clean replays, Wilson 95% lower bound ≥ 0.70 | ⚠ **PROJECT POLICY**, estimator is literature-mandated |
| Deletion checks | Every Verified sequence passes | — |
| Explanation | Every Verified explanation includes a test→resource→test path in a supported family | — |
| Controls | **No false confident diagnosis on non-OD controls** | — |
| Instrumentation overhead | Below a POC-informed, stakeholder-accepted threshold | ⚠ **NO NUMBER YET, deliberately** |

## Statistical discipline — chosen before results (Q73)

- **Project-wise paired comparisons** — cases within a project are not independent
- **Bootstrap confidence intervals** and a reported **effect size**
- If a significance test is used, it is **chosen before the results**, and we report **practical
  effect rather than p-values alone**
- **Excluded and timed-out cases remain in the yield and failure analysis** — they do not
  disappear from the denominator
