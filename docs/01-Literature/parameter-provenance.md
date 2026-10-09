# Parameter Provenance

*Every experimental constant in FlakeTrace's protocol, and the published basis for its value.*

> This table exists because **a review that supports the high-level narrative while leaving
> the protocol constants unjustified is not defensible.** Where the literature constrains a
> range rather than fixing a value, the row says so. Where a constant is our policy rather than
> a published finding, it is marked `POLICY` — and must be defended **as a policy**.

---

## Literature-derived parameters

| Parameter | Value | Published basis | Ref |
| --- | --- | --- | --- |
| Classify target as victim or brittle by running it alone | Isolation run | Shi et al. define a victim by `run([v]) = PASS` and a brittle as failing alone; Rahman et al. restate that type is determined by running the OD test by itself | [4], [5] |
| Repeat the isolation run rather than trusting one outcome | Repeated | iFixFlakies' Minimizer explicitly loops a RERUN parameter over isolation and raises an exception if the outcome is inconsistent with an OD classification | [4] |
| **Number of isolation replays** | **10** | **Constrained, not fixed.** Lam et al.: after one failure, 87.8% of tests pass within 5 reruns, minor gains at 6–7; they conclude the ten-rerun convention attributed to Google is **not well justified** and recommend ≤5 for post-failure confirmation. Gruber et al.: 10 reruns surface ~54% of OD and 33% of NOD. Hashemi et al. chose 10 reorderings × 10 reruns and saw **the same results at 20 and 30**. Ten is adopted as a screening budget above the ≤5 knee, corroborated by independent replication showing no gain to 30 — **not claimed to be exhaustive** | [13], [12], [36] |
| Shuffled-suite execution to expose order sensitivity | Randomised orders | Zhang et al. define dependence over reordered subsequences; iDFlakies detects OD by reordering and rerunning | [2], [3] |
| Shuffled orders for baseline / ranking comparison | 10 | Rahman et al. randomly generate 10 failing or passing orders per victim/brittle for the OBO baseline and report the average; RankFL uses the same 10 | [5] |
| Shuffled orders for order-history evidence | 20 | Rahman et al. chose 20 to match iDFlakies' suggestion; RankFO20 performed at least as well as a 95%-confidence-derived variant averaging 24.6 / 22.7 orders | [5], [3] |
| **Shuffles must not interleave methods across test classes** | Enforced | iDFlakies' random orderings deliberately do not interleave methods from different classes, because such an ordering **would not be produced by frameworks such as JUnit**; Rahman et al. verify order validity | [3], [5] |
| **Shuffle classes first, then methods within each class** | Enforced | iDFlakies found this detects the most flaky tests overall | [3] |
| Different rerun budgets for OD vs NOD evidence | OD-specific | Gruber et al.: 95% confidence a test is not order-dependently flaky needs ~31 random-order executions, vs ~170 same-order runs for the NOD case | [12] |
| No claim of exhaustive detection at any budget | Stated limitation | Alshammari et al. still detected new NOD flaky tests **after 10,000 reruns** across 24 Java projects; Parry et al. estimate **1.6 single-core years** to detect 158 NOD tests at 2,500 reruns | [14], [15] |
| POC-stage replay gate | ≥ 9 of 10 matching failures | Smaller screening analogue of the same binomial reasoning; consistent with the 10-replay screening budget | [22], [13] |
| **Minimality claim: 1-minimal, never "minimum"** | Deletion-minimal | Delta debugging returns a 1-minimal result; iFixFlakies' Minimizer applies it to the prefix. Wei et al. note it **does not necessarily find all polluters** in a prefix. Global minimum requires exponential exploration | [11], [4], [28] |
| Retain multi-predecessor candidates | Depth configurable | Shi et al. and Rahman et al. treat joint dependence as very rare and exclude it; **Zhang et al. found 82% of dependent tests revealed by ≤2 tests — bounding how rare, and leaving a non-empty remainder** | [4], [5], [2] |
| **Primary cost unit: total test-method invocations** | Invocations | A single Maven launch may execute very different numbers of tests, so launches are a poor unit. Rahman et al. count tests run and add separately measured Surefire overhead per group | [5] |
| Harness overhead measured, not assumed | Averaged over 30 runs | Rahman et al. obtain Surefire invocation overhead by subtracting Surefire-reported test times from total suite time, repeated 30× | [5] |
| **Failure equivalence by normalised signature, NEVER process exit code** | Signature matching | Qi et al. traced invalid repair results to infrastructure checking the **exit code rather than the output** — a weak proxy that admitted a patch reducing the program to an immediate exit | [26] |
| Committed resource families | static fields, system properties, filesystem paths | Zhang et al. identify static fields and filesystem among root causes; PolDet monitors shared heap locations and the filesystem, reporting an access path or filename; Rahman et al. enumerate static variables and filesystem among global state | [2], [9], [5] |
| Databases, network, threads, timing treated as opaque | Excluded from full diagnosis | Takuan is presented as extending the field precisely by handling external state such as the filesystem that prior work could not; broader external state remains open with preliminary results only | [6] |
| **Shared-state overlap is a prior and an explanation aid, NOT proof of causation** | "Evidence-supported interference path" | PolDet reported **324 polluting tests of which manual inspection judged 194 relevant** — a material false-positive rate for a state-difference signal alone | [9] |
| Instrumentation overhead measured, median and p95 | Measured | ElectricTest added **~20× slowdown** when soundly detecting dependencies; PolDet over JPF showed 1.43× relative to base JPF. Overhead here is large enough to change deployability | [10], [34] |
| Uninstrumented control runs required | Required | Follows from the same overhead evidence; a probe heavy enough to slow execution by an order of magnitude can perturb timing-sensitive outcomes. **We have our own instance — the timezone override** | [10] |
| Freeze environment: image digest, JDK, Maven, Surefire, JUnit, locale, timezone | Recorded in certificate | Gao et al. study what must be controlled to make tests repeatable; Luo et al. found 96% of flaky tests platform-independent but flagged **environment dependence as the higher priority** | [25], [1] |
| **Pin exact commit SHA and rebuild in a clean container** | Required | Tufano et al.: broken snapshots in **96%** of 100 Apache Maven projects; on average only **38%** of change history currently compilable, mainly dependency resolution. A replication observed continued degradation | [23], [24] |
| Publish reproduction yield and exclusions, not only successes | Required | Rahman et al. began from **249** OD tests and retained **155** reproducible after re-running each with its OD-relevant tests, excluding the rest | [5] |
| **Split by project, not randomly by test** | Project-level split | RankFL is trained per module such that evaluating one project uses training tuples from all others, simulating a developer applying a model trained elsewhere | [5] |
| Ranking metrics | Rank-1 count, rank of first relevant test, time to rank + confirm | Precisely the metrics Rahman et al. define and report — **makes our results directly comparable to the strongest published baseline** | [5] |
| Learning-to-rank metric alongside practical ones | MAP or MRR | Rahman et al. report MAP of 0.007 (RankFL) and 0.251 (RankFO) on polluters vs 0.000 for OBO | [5] |
| Any remediation gated behind a Verified certificate and execution-validated | Gated | Qi et al. and Smith et al. establish plausible patches are frequently incorrect; FlakyDoctor's own loop validates every candidate by execution and re-prompts | [26], [27], [8] |
| Remediation presented as non-authoritative suggestion | Required | Overfitting literature shows test-suite passage is not a correctness oracle; the certifying-algorithm model requires **the user, not the tool**, performs the final check | [27], [20] |
| Typed abstention with machine-readable reason | Verified / Candidate / Unresolved | The certifying model presumes a checker that can **reject**; the rerun literature establishes absence of observed failure at a budget is not evidence of absence | [20], [14] |
| **Wilson interval, not Wald** | Wilson 95% | Brown, Cai & DasGupta showed the Wald interval's coverage properties are **"chaotic"** and far more persistently so than appreciated, and that textbook prescriptions about its safety **cannot be trusted**. They recommend Wilson or equal-tailed Jeffreys for small n. Verification budgets here are small **by construction** — tens of replays — so the small-n case governs | [21], [22] |

---

## `POLICY` — parameters the literature does NOT settle

**Three constants are project policy, not published findings. Present them as such under
questioning.** Blurring this distinction is punished; naming it is respected.

### 1. The 18-of-20 acceptance count and the 0.70 Wilson lower bound

- The **estimator** is literature-mandated (Brown, Cai & DasGupta) ✅
- The **thresholds** are an acceptance policy chosen by the project ⚠️
- **Frozen after the POC and validation baselines, before the held-out evaluation**

> *If asked why 0.70 and 18 of 20:* they are the defensible starting proposal in our evaluation
> contract, frozen before the held-out run. **Adjusting them after seeing results would
> invalidate the evaluation**, which the guide treats as a change requiring recorded approval.

### 2. The 25% cost-reduction and 5-percentage-point success-loss targets

- The **baselines** (OBO, delta debugging, RankFO) and their published cost figures are
  literature-derived ✅
- The **targets** are project-set success criteria ⚠️

### 3. The split of budget between search and verification

- **Derived**, not cited — combines the certifying-algorithm requirement that a witness
  accompany the output with the finite-CI-budget evidence
- **No cited paper specifies a ratio** — which is exactly why the **no-verification-reserve
  ablation is a required experiment**

### 4. Median instrumentation overhead threshold

**No number yet, deliberately.** "We are not inventing a final overhead figure before we
measure it." Stakeholder-derived envelope: 5–15 min PR-acceptable (SH1); 30 min tolerable
opt-in or nightly (SH3).

---

## What is NOT ours — never defend these as inventions

- the victim / brittle / polluter / state-setter / cleaner vocabulary [4]
- delta-debugging minimisation and its 1-minimality property [11], [4]
- ranking of OD-relevant tests [5]
- dynamic shared-state explanation [6], [9]
- cleaner-based or generated repair of OD tests [4], [7], [8]

---

*Reference numbers match [[01-Literature/references]].*
