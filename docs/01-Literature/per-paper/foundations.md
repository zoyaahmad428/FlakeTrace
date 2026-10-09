# Foundations — flaky tests, cost, and what developers actually find hard

*Grouping the empirical papers that establish the problem exists, costs money, and is not
solved by detection.*

---

## Luo, Hariri, Eloussi, Marinov — "An empirical analysis of flaky tests" (FSE 2014) [1]

**The first systematic empirical characterisation.** 201 commits likely fixing flaky tests
across 51 open-source projects.

- Three largest root-cause categories: **Async Wait, Concurrency, Test Order Dependency**.
  Authors explicitly recommend techniques concentrate on these three.
- **Test Order Dependency: 19 of 201 commits (12%)**
- **47% of the order-dependency cases were caused by dependence on external resources** rather
  than in-memory state alone — and they note this limits techniques comparing only internal
  memory object states
- **96% of flaky tests platform-independent** — they conclude techniques should rank platform
  dependence **lower priority than environment dependence**
- **85% of Async Wait cases manifested by adding a single time delay** — evidence that timing
  perturbation matters

**Why 12% understates it:** order dependency is **deterministic once the order is fixed**,
which makes it the one major category reproducible on demand and therefore tractable for a
diagnostic tool.

**Direct design consequence:** the 47% external-resource finding is why **filesystem paths are
a committed first-class resource family** alongside static fields and system properties.

---

## Memon et al. — "Taming Google-scale continuous testing" (ICSE-SEIP 2017) [19]

The budget-awareness that defines FlakeTrace is **not self-imposed** — it reflects reported
operating conditions.

- Test Automation Platform integrates and tests **>13,000 code projects** on an average day
- **800,000 builds, 150 million test runs**
- **Even with these resources they cannot regression-test each code change individually**
- Flaky tests foreclose the obvious heuristic of rerunning recently failed tests, because such
  a system **would end up mostly re-running flaky tests**

---

## Parry, Kapfhammer, Hilton, McMinn — rerun cost (EMSE 2023) [15]

- Detecting 158 NOD flaky tests in 89,668 test cases by rerunning each up to 2,500 times ≈
  **1.6 single-core years**
- Airflow alone: **1.69 × 10⁶ single-core seconds** for 66 NOD flaky tests ≈ 19.6 hours,
  ~**39 USD** on a 24-core cloud instance

**Alshammari et al.** [14] were **still discovering new NOD flaky tests after 10,000 reruns**
across 24 Java projects.

### The two conclusions that are load-bearing for us

1. Any diagnostic tool consuming an **unbounded** number of test executions is **not
   deployable** in the environment where the problem occurs. **An explicit execution budget is
   a functional requirement, not a convenience.**
2. **Exhaustive detection is not achievable at any realistic budget** — which is why we scope
   to diagnosing an already-known OD failure rather than competing on generic detection.

---

## Eck, Palomba, Castelluccio, Bacchelli — "Understanding flaky tests: the developer's perspective" (ESEC/FSE 2019) [18]

21 professional developers classified 200 flaky tests they had previously fixed; 121
developers surveyed, median 5 years industrial experience.

> **Central finding for us: the challenges developers report concern mostly the REPRODUCTION
> of the flaky behaviour and the IDENTIFICATION OF THE CAUSE — not detection.**

Also: flakiness perceived as significant by the vast majority regardless of team size or
domain; affects resource allocation, scheduling and perceived suite reliability.

**This is the empirical warrant for our product boundary.** The market and the research
literature are both comparatively well served on detection; the reported pain is concentrated
in reproduction and cause identification — exactly what a replayable, evidence-carrying
certificate addresses.

**Corroborated by our own stakeholders** ([[00-Meta/stakeholder-evidence]]): SH1 said existing
tools are *"much weaker at explaining why a failure is intermittent."*

---

## Zhang, Jalali, Wuttke, Muşlu, Lam, Ernst, Notkin — "Empirically revisiting the test independence assumption" (ISSTA 2014) [2]

**The first formal treatment.**

**Definition:** a test is **dependent** when there exists a possibly reordered subsequence of
the original test suite in which the test's result differs from its result in the original
order — using the default execution order as baseline and **the visible test result, not
internal program state**, as the observable.

They show test dependence causes non-trivial consequences including **masking program faults**
and **producing spurious bug reports**.

### The 82% finding — critical for our multi-predecessor position

From 450 manually inspected bug reports they identified **96 distinct dependent tests**, and
found **82% of them can be revealed by no more than two tests**. The remaining fraction cannot.

> A tool whose search is structurally limited to single-predecessor hypotheses will therefore
> be **correct most of the time and silently wrong on a meaningful minority.**

This is the empirical motivation for treating **analysis depth as a configurable parameter
rather than fixing it at one**, and for **retaining multi-test candidates through
minimisation**.

It is also the counterweight to Shi et al. and Rahman et al. treating joint dependence as
"very rare" and excluding it — **rare is not absent, and 18% is the bound.**

---

## Lam, Winter, Astorga, Stodden, Marinov — rerun characteristics (ISSRE 2020) [13]

- After one failure, **87.8% of tests can be found to pass within 5 reruns**, with only minor
  increases at 6 and 7
- They conclude **the commonly used ten-rerun convention attributed to Google is not well
  justified** and recommend ≤5 for post-failure confirmation
- Also show tests previously labelled non-order-dependent **do in fact depend on order** and
  can fail at very different rates under different orders

**This is the source of the honest framing of our 10-replay choice** — see
[[01-Literature/parameter-provenance]]. We do not cite 10 as "the standard"; we cite it as a
screening budget above the ≤5 knee, corroborated by Hashemi et al. showing no gain to 30.
