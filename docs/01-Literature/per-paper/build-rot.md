# Benchmark decay — catalogues are not benchmarks

*The threat most often underestimated in project proposals, and the evidence base for our
dataset being marked **amber** rather than green.* Refs: [23], [24], [5]

---

## Tufano et al. — "There and back again: can you compile that snapshot?" (JSEP 2017) [23]

**219,395 snapshots across 100 Apache Java projects using Maven.**

- **Broken snapshots occur in 96% of projects**
- **On average only 38% of a project's change history is currently successfully compilable**
- **Dominant cause: dependency resolution**

## Maes-Bermejo et al. — replication (EMSE 2022) [24]

Replicated in 2020 across **139,389 commits from 79 repositories**, then reproduced on **80
further large Java projects with 300,873 commits**.

- Observed **degradation of compilability over time** due to vanishing dependencies and other
  external artefacts
- Confirmed **missing external artefacts are the most influential cause of build failure**

## The precedent inside our exact research area — Rahman et al. [5]

Starting from a **published dataset of 249 OD tests with labelled OD-relevant tests**, they:
1. re-ran every OD test with its corresponding OD-relevant tests to confirm the labels
2. found some **could not be reproduced under Maven Surefire**
3. **confirmed this with the original authors**
4. **excluded them — retaining 155**

> **A dataset already curated by expert researchers still lost 38% of its cases on independent
> re-execution.**

---

## What follows for us

> **Any claim that a public dataset is "ready" before independent rebuild is unsupported by
> this evidence, and reproduction yield must be published alongside results.**

### The answer (Q63)

> No, and we mark it amber deliberately. IDoFT is a **living catalogue** with project URLs,
> commits, modules, tests and categories — **a source catalogue, not proof that cases build,
> contain resource-level ground truth or are legally redistributable.**
>
> The evidence that reproducibility filtering is the real work is public: **RankF began with
> 249 order-dependent tests and retained 155** after confirming reproducibility across 24
> projects. We treat our own build-and-reproduce yield as **a measured quantity to report, not
> an assumption.**

**Do not say the dataset is ready because it exists.** That is the specific overclaim the
evaluation guide flagged for correction from green to amber.

---

## Our own corroborating evidence

The POC met this threat directly:

| Encounter | Consequence |
| --- | --- |
| Neither subject builds on a modern JDK — fastjson targets source 1.5, jsoniter 1.6 | **JDK 8 required**; frozen container image |
| fastjson is **archived** on GitHub | Recorded as a deviation. *Did not block: the pinned commit fetches normally, and an archived repo cannot move under us — which strengthens reproducibility* |
| **4 of 8 targets reproduced** (50%) | Yield is a **measured quantity**, close to Rahman et al.'s ~62% retention |
| All 8 cases turned out to be **JUnit 3** | Candidate enumeration had to follow naming convention, not annotations |

---

## Mitigations committed

- **Pin exact commit SHAs**, rebuild in clean containers, record image digests
- **Two-phase network model**: allowlisted dependency-fetch stage populating a local cache;
  test execution with networking **disabled** against that cache. *Also improves
  reproducibility — a rerun three months later resolves the same artifacts*
- **Publish yield AND exclusions**, not only successes. *Reporting only the cases that worked
  would bias yield toward easy cases and inflate every metric*
- **Pre-registered fallback ladder** (Q67): first fallback is the verified RankF subset with
  published yield; if insufficient, reduce case count **and report it** rather than
  substituting synthetic-only results silently
- **Controlled fixture suite** as a sanity layer — and **we state plainly it is not a
  substitute for real projects**

## Risk register entry

**Historical build rot** is our **single biggest risk** (Q94) — it gates everything
downstream, because without reproduced cases there is no benchmark, no baseline and no
evaluation.

**Trigger:** fewer than three POC cases *(cleared)*, or an inadequate held-out subset at Mid-1
*(next checkpoint)*.
