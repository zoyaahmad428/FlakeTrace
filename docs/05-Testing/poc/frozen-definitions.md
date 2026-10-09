# Frozen Definitions

**Committed to version control before any experiment ran.** The commit timestamp is held as
evidence — this is what makes the pre-registration genuine rather than claimed.

> A panel asking about your POC will ask whether the gates were written before or after the
> results. **Before.** Both commits are held.

---

## Candidate set

All test methods in the victim's Maven module, **excluding the victim**.

For JUnit 3 subjects, a test method is a **public no-arg method named `test*` on a
`junit.framework.TestCase` subclass**.

> **If the module exceeds 300 such methods, restrict to the victim's package and record the cap
> as a declared limitation.**

*(This cap mattered: after package restriction one fastjson case still had **730** candidates,
two others **529** — exceeding jsoniter's entire 384-method module.)*

## Order-dependent (polluter)

A candidate *c* such that `[c, v]` executed in a **single JVM** produces the target failure
signature for victim *v*, while `[v]` alone passes.

## Failure signature

The triple:
1. exception fully-qualified class name
2. normalised first line of the message
3. topmost stack frame **inside the project package**

**Masked:** digits · hex addresses · temporary paths · timestamps.

> **A timeout, compilation error or OOM is NOT the same reproduction as the intended assertion
> failure.**

*This is the Qi et al. defence written into the protocol before the experiment — exit code is
not a signature.*

## Confirmation and cost unit

One **confirmation** = one execution of one candidate order.

Primary cost unit = **test-method invocations**, not Maven launches.

*(A single Maven launch may execute 5 tests or 5,000 — launches are a poor unit. Rahman et al.
count tests run plus separately measured Surefire overhead.)*

## Reproduced case

The victim **passes alone ≥ 10/10** **and** **fails with the matching signature in ≥ 9/10
replays** of the confirmed polluting order.

## Resource identifier

`ownerInternalName.fieldName:descriptor`

- **Static fields only** — `getstatic` / `putstatic`
- Direct references **plus a declared number of hops** into project-owned callees
- Attribution per test method includes: the method, the class's `setUp`, the class's `tearDown`,
  and the class's `<clinit>`

> **Reflection, filesystem, system properties, network and database state are out of scope and
> recorded as unsupported — NEVER as zero-overlap.**

*That last clause matters: recording an unsupported family as zero would manufacture a false
negative and corrupt the ranking metric.*

## Single-scan protocol

The exhaustive scan runs **once per case**. Ground truth, the one-by-one baseline, random
baselines and the ranked strategy are **all computed offline** from that outcome table.

> **No strategy triggers a re-run.**

Cost is *N* executions, not *N* × strategies. This is what made the experiment affordable — and
what makes three of the five outstanding pre-defence items runnable without re-scanning.

---

## Amendment recorded 27 August 2026 — disclose this unprompted

**Added:** execution-context fidelity to the runner definition, requiring invocation of a
project's test-suite `@BeforeClass` where its Surefire configuration runs **suite classes rather
than test classes**.

**Why:** it corrected the harness defect producing false positives — jsoniter's runtime code
generation collided with itself when run without suite context.

**What it changed:** neither the reproduction criterion nor the strategy scoring.

**Effect on results:** moved a count from **182 to 0** — **against our own interest**.

**Both commits are held.**

> **Volunteer this.** An amendment to a pre-registration is exactly the kind of thing a panel
> treats as concealment if discovered and as integrity if disclosed. The direction of the change
> — it removed a favourable-looking result — is the strongest part of the disclosure.

---

## Pre-registered decision gates

| Measure | Gate |
| --- | --- |
| Reproduction yield | ≥ 3 of 4 cases reproduce in clean containers |
| Ranking quality | True polluter in top 5 or top 20% for ≥ 3 reproduced cases |
| Execution saving | ≥ 30% fewer median confirmations than one-by-one, **identical candidate sets** |
| Replay reliability | ≥ 9 of 10 matching failures per accepted pair |
| Evidence integrity | Every reported overlap names the **exact field and bytecode locations** |

## Pre-registered pivot conditions

1. **Fewer than three of four cases reproduce** → the dataset pipeline becomes the first risk;
   reduce case scope before claiming readiness
2. **The depth-2 ablation also produces empty overlap** → the resource-evidence pillar collapses;
   restate the contribution around order evidence and certification alone

**Neither fired.** See [[07-Defense/decisions/poc-scope-narrow]].
