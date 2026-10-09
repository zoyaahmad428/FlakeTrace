# FlakeTrace POC — decision record v2 (strengthening iteration)

**Date:** 2026-09-04  **Protocol:** `manifest/definitions_v2.md`, frozen 15:48:47
before the held-out results were analysed (commit `f535370`).
v1 (`decision/decision_record.md`) stands unchanged as the pre-registered
outcome of the first iteration.

Supervisor condition: *Revise-then-Proceed becomes Strong Proceed once the
depth sweep, per-case cause classification and out-of-domain case are recorded.*
All three are recorded below, together with the findings they produced —
including one that does not favour the project.

---

## 1. Deliverable A — resource-depth sweep

`results/depth_sweep.csv`. Two scoring definitions across depths 1–4, replayed
offline against the single exhaustive scan. Development set (fastjson).

| depth | W_R median saving | LEX median saving | gate 2 | gate 3 |
|---|---|---|---|---|
| 1 | 0.0% | 82.7% | PASS | PASS |
| **2 (pre-registered)** | 40.0% | **83.8%** | **PASS** | **PASS** |
| 3 | 40.0% | 60.7% | fail | PASS |
| 4 | 40.0% | 60.7% | fail | PASS |

**Finding — depth has an interior optimum.** Deeper is not better: at depths 3–4
FJ-04's first hit degrades from rank 27 to 129, because expansion adds noise
faster than signal. Depth is a tuned parameter that must be declared and swept,
not maximised.

## 2. Deliverable B — per-case cause classification

`results/cause_classification.csv`, at the pre-registered depth 2, over all
8 reproduced cases. Classified from evidence about *confirmed* OD-relevant
candidates, not from narrative.

| Case | Scope | Cause | Evidence |
|---|---|---|---|
| FJ-01 | package | `A_DIRECT_PUTSTATIC` | `JSON.defaultLocale` |
| FJ-02 | package | `A_DIRECT_PUTSTATIC` | `JSON.DEFFAULT_DATE_FORMAT` |
| FJ-03 | package | `B_VIA_STATIC_REF` | `SerializeWriter.bufLocal` (ThreadLocal buffer cache) |
| FJ-04 | package | `B_VIA_STATIC_REF` | `JSON.DEFAULT_GENERATE_FEATURE` |
| OR-01 | full module | **`D_VIA_CLINIT`** | `LogBackendFactory` → `DaoManager.<clinit>` |
| OR-02 | full module | `B_VIA_STATIC_REF` | `Logger.UNKNOWN_ARG` |
| OR-03 | full module | `C_UNSUPPORTED` | no shared static at any swept depth |
| OR-04 | full module | `C_UNSUPPORTED` | no shared static at any swept depth |

**Mechanism D is new and was only visible out of domain.** In ormlite the
polluter writes `LoggerFactory.logBackendFactory`, which **no victim ever
reads** at any depth up to 6. Thirteen classes read it inside their `<clinit>`
to build a static `Logger`; the victims then read *that* logger. Write and read
are on **different fields**, linked through class initialisation. A
write∩read intersection model cannot express this by construction.

**A defect found and repaired during classification.** `javap` declares
constructors by class name but call sites reference `."<init>":` *in quotes*,
which the invoke regex rejected — so constructor bodies and constructor call
edges were both invisible. fastjson's pollution runs through
`new SerializeWriter(...)`. After the fix, `SerializeWriter.<init>` and
`close()` are correctly seen touching `bufLocal`, FJ-03 moved
`C_UNSUPPORTED → B_VIA_STATIC_REF`, and the development-set median saving rose
from 54.8% to 83.8%. The fix is a defect repair, not parameter tuning, but it
post-dates the v2 freeze and is disclosed here.

## 3. Deliverable C — out-of-domain case

**`j256/ormlite-core` @ `632b87c2`**, ISC licence, added for external validity:
a persistence/ORM library rather than a JSON serialiser, and **JUnit 4** rather
than JUnit 3. The enumerator was extended to recognise `@Test` methods; the
existing subjects' candidate sets are unchanged and remain those actually
scanned. Builds green on temurin-8 (1:28). Four victims in four distinct
classes and packages; all four pass alone 10/10 (VICTIM); all four replay
10/10, Wilson [0.72, 1.00].

### 3.1 The frozen package restriction produced false negatives

| Scope | OR-01 | OR-02 | OR-03 | OR-04 |
|---|---|---|---|---|
| victim's package (frozen rule) | 0 | 0 | 0 | 0 |
| full module (1,219 candidates) | 1 | 1 | 1 | 1 |

All four are reproducible; the frozen >300-package restriction hid every one.
This is a direct refutation of that rule as a candidate-set policy, and it
means the v1 yield figure understates reproducibility.

### 3.2 The pre-registered prediction was NOT confirmed

v2 predicted the LEX rule at depth 2 would place a confirmed OD-relevant
candidate in the top-20% for the majority of held-out cases.

| Case | Candidates | OBO | LEX | Saving | Top-20%? |
|---|---|---|---|---|---|
| OR-01 | 1,219 | 769 | 788 | −2.5% | no |
| OR-02 | 1,219 | 769 | 70 | +90.9% | **yes** |
| OR-03 | 1,219 | 769 | 769 | 0.0% | no |
| OR-04 | 1,219 | 768 | 768 | 0.0% | no |

**Median saving 0.0%; top-20% in 1 of 4. Prediction NOT confirmed.**

Two qualifications, neither of which rescues the result. All four victims share
**one** polluter (`LoggerFactoryTest#testSetLogFactory`), so this is one
independent polluter observed four times, not four independent trials. And
three of the four are `C_UNSUPPORTED` or `D_VIA_CLINIT` — mechanisms the scored
model cannot represent, so the rule was never able to rank them.

The honest conclusion: **the depth-2 LEX rule is calibrated to fastjson and
does not transfer out of domain as written.** It is a development-set result,
not a validated one.

## 4. Gate status

| # | Gate | Threshold | Observed | Verdict |
|---|---|---|---|---|
| 1 | Yield | ≥3 of 4 | 12 built, **8 reproduced** (fastjson 4/4, ormlite 4/4, jsoniter 0/4) | **BELOW** on aggregate (67%); 2 of 3 projects at 100% |
| 2 | Ranking | top-5 or top-20% in ≥3 | dev set PASS; **held-out 1 of 4** | **BELOW** out of domain |
| 3 | Saving | ≥30% median | dev set 83.8%; **held-out 0.0%** | **BELOW** out of domain |
| 4 | Replay | ≥9/10 each | **8/8 at 10/10**, all CI [0.72, 1.00] | **MEETS** |
| 5 | Evidence integrity | field + bytecode location | non-vacuous; four mechanism classes with named fields | **MEETS** |

## 5. Decision

The three strengthening deliverables are recorded, so the supervisor's stated
condition is met. What they establish is narrower than hoped and is stated as
such:

- The diagnosis pipeline is sound and reproducible across **three** projects,
  two build systems' worth of test conventions (JUnit 3 and 4), and two
  domains — 8 of 8 reproduced cases replay 10/10.
- The resource signal works **where the mechanism is representable** (A and B:
  4 of 4 fastjson cases, up to 83.8% median saving) and provably cannot work
  where it is not (C and D).
- Cause classification is now the load-bearing contribution: it says *in
  advance* whether the resource signal is applicable to a case, which is
  exactly the abstention discipline the product contract requires.

**Recommended framing: Strong Proceed on the pipeline and the cause taxonomy;
Revise-then-Proceed on the ranking claim**, which needs a mechanism-aware score
(covering D) and validation on a held-out set that contains more than one
independent polluter.

## 6. Scope changes carried forward (beyond v2's A1–A6)

- **A7 — retire the >300 package restriction.** It produced false negatives on
  4 of 4 ormlite cases. Replace with a declared module-wide candidate set and
  report cost, or restrict by evidence rather than by package.
- **A8 — add mechanism D to the resource model**: link a write to a read on a
  *different* field when a class initialiser transports the value. Detection is
  already demonstrated computationally in §2.
- **A9 — held-out sets must contain multiple independent polluters.** Four
  victims sharing one polluter is one trial, not four.
- **A10 — report cause class before ranking quality.** A case classified C or D
  must not be scored against a model that cannot express it; it belongs in the
  coverage account.
