# Evaluation Plan

*Status: `PROPOSED`.* Testing, evaluation and acceptance are **three different things** (Q74) —
know the distinction cold.

| | Asks | Contains |
| --- | --- | --- |
| **Testing** | Does the implementation meet its requirements? | Unit, integration, system and security tests: timeouts, OOM, cleanup, unsupported resources, malformed builds |
| **Evaluation** | Is the approach better under the stated budgets, and where does it fail? | Baseline comparison, ablations, failure analysis |
| **Acceptance** | Will the people it is for actually use it? | Named developers/QA/CI maintainers performing realistic tasks, with a recorded decision |

---

## Research questions

| RQ | Question | Measured by |
| --- | --- | --- |
| **RQ1** | Does evidence-guided ranking place true OD-relevant tests earlier? | top-k recall, MRR, candidate confirmations, time to first confirmed relevant test |
| **RQ2** | Does adaptive selection produce verified certificates under lower budgets? | success-vs-budget curves, total invocations, wall time, paired effect sizes |
| **RQ3** | Are returned sequences replayable and deletion-minimal? | repeated clean replays, Wilson intervals, per-predecessor deletion checks |
| **RQ4** | Are resource explanations correct and appropriately limited? | audited paths, precision and coverage, intervention consistency, unresolved rate |
| **RQ5** | What engineering overhead and failure modes does the product introduce? | median/p95 overhead, failure taxonomy |
| **RQ6** | Does the certificate improve a realistic diagnosis task for intended users? | acceptance task outcomes |
| RQ7 *(gated)* | Does certificate conditioning improve automated repair over unconditioned prompting? | precision, coverage |
| RQ8 *(gated)* | Does the verification contract prevent unsafe repairs being reported as fixes? | adversarial patch-rejection rate |

## Baselines (Q70) — all of them

- **Random** candidate ordering with **fixed seeds** — *a floor, so a reader can see how much of
  any improvement is attributable to ordering at all. Reported, not defended*
- **Original-order one-by-one (OBO)** confirmation
- **iFixFlakies minimiser** and delta debugging on the overlapping reproducible subset
- **RankFO**, and where feasible **RankFL**, on the same candidate sets
- **Takuan** on an overlapping explanation subset — research comparator, not product
- **Oracle ceiling** — perfect-knowledge ranking, states what the prize is worth

`STATUS: none run yet. Integration FYP-I early; measurement is a Final-1 exit condition.`

## Ablations

resource-only · order-only · static-only · dynamic-only · **no cost term** · **no verification
reserve** · **analysis-depth sweep reporting both rank and overlap-set size**

Two of these test our own `POLICY` decisions directly:
- *no cost term* → does the cost term earn its complexity?
- *no verification reserve* → the budget split has **no canonical citation**; this ablation **is
  the experiment that tests it**

## Metrics

Isolation success at budget · **test-method invocations as primary cost unit** · top-1/top-5
recall and MRR · confirmations before first true polluter · replay reliability with Wilson
intervals · deletion-minimality rate · explanation precision, coverage and unknown rate ·
instrumentation overhead median and p95 · abstention quality by reason.

> **We will not report a numeric confidence score.** Reliability is always expressed as matching
> failures out of N replays plus an interval.

## What result would tell us the project failed (Q76)

1. **A Verified certificate that is wrong** — a returned sequence and resource path an audit
   shows does not hold. **The most serious.**
2. **High false-confidence rate on controls**
3. Below those: if resource evidence adds nothing over order evidence at any affordable depth,
   **and** the adaptive policy does not beat the baselines → the technical contribution reduces
   to **certification and deployment engineering**, which we would **report as such rather than
   dress up**

**Each has a pre-registered branch in the fallback ladder.**

## Dataset discipline

**Split by project, never randomly by test** (Q65) — two tests in a module share the same static
fields, helpers and often the same polluter, so a threshold tuned on one predicts the other for
reasons that have nothing to do with our method.

Development projects → instrumentation and debugging.
Validation projects → freezing thresholds.
**Untouched projects → the final held-out result.**

**Leakage rule** (Q66): *a fix commit or issue description may not be used as an algorithm input
if it is also the oracle used to judge the explanation.* Where our resource-cause oracle comes
from a fix commit, that case is **oracle-only** and the pipeline never sees the commit.

**We also publish exclusions and build failures.** Reporting only the cases that worked would
bias the yield toward easy cases and inflate every metric.

## Frozen manifest contents (Q64)

Per case: project URL and exact commit SHA · module and fully qualified test identifiers ·
JDK/Maven/Surefire/JUnit versions · dependency mirrors or caches required · known passing and
failing orders with victim/brittle/polluter/state-setter/cleaner labels where available · build
status, reproduction count, failure signature, exclusion reason · **project and artifact licence
with whether code can be redistributed or only fetched by script** · container digest, setup
script hash, expected runtime · **the source of the resource-cause oracle** (issue, fix commit,
paper annotation or manual audit).

**Manifest version zero exists now** with our two POC projects. The larger verified subset is
frozen **before Mid-1**.

## Fallback ladder if projects will not build (Q67)

1. Use the **verified RankF subset** and publish the yield
2. If insufficient, **reduce case count and report it** — never substitute synthetic-only
   results silently
3. The controlled fixture suite tests the *implementation* — **and we state plainly it is not a
   substitute for real projects**

## User acceptance tasks (Q75)

1. Run FlakeTrace on a prepared project and identify whether the outcome is Verified, Candidate
   or Unresolved
2. **Replay** the returned order on a clean environment
3. Identify the suspected predecessor, the shared resource, the evidence strength and the
   remaining limitation
4. **Choose the next engineering action and explain why**
5. Compare that task against doing the same work from raw logs and a conventional flaky-test
   history view

**Measured:** task completion · whether the chosen next action was correct · time · errors ·
assistance needed · the recorded acceptance decision.

**Named participant secured:** SH1 (Mahad Sheikh, Inspirovix) agreed to review results and give
practitioner feedback. Substitute plan needed for the remainder.

## Licences (Q68)

Default is **fetch-by-script with a pinned SHA**, which **avoids redistribution entirely**. Our
evidence bundle contains manifests, logs, results and our own code — **not third-party source**.

POC subjects: json-iterator/java **MIT**, alibaba/fastjson **Apache-2.0**. IDoFT is publicly
available research data containing no personal information. Artifact licences recorded
**separately** from subject-project licences.
