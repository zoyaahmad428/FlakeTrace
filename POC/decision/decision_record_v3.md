# FlakeTrace POC — decision record v3 (final gate outcome)

**Date:** 2026-09-04
**Protocols:** `manifest/definitions.md` (v1) → `definitions_v2.md` (v2,
commit `f535370`) → `prereg_heldout2.md` (held-out 2, commit `9157b24`).
Each was committed *before* the data it governs was analysed. v1 and v2 stand
unchanged, including their negative results.

---

## 1. Final gate outcome — all five pass

| # | Gate | Threshold | Observed | Verdict |
|---|---|---|---|---|
| 1 | Build / reproduction yield | ≥75% | **18 of 23 reproduce (78.3%)** across 3 projects | **PASS** |
| 2 | True OD-relevant ranking | top-5 / top-20% in a majority | **8 of 8 held-out cases in top-20%** | **PASS** |
| 3 | Execution saving vs OBO | ≥30% median | **39.3% median on held-out** | **PASS** |
| 4 | Replay reliability | ≥9/10 per accepted pair | **18/18 at 10/10**, Wilson [0.72, 1.00] | **PASS** |
| 5 | Evidence integrity | field + bytecode location | non-vacuous; four mechanism classes with named fields and offsets | **PASS** |

Gates 2 and 3 are measured on the **pre-registered held-out set**, not on the
data the rule was built from. That distinction is the whole result.

## 2. What changed since v2, and why each change was legitimate

**Escalating candidate scope (A7).** v1's ">300 methods ⇒ restrict to the
victim's package" rule was refuted: it hid every polluter in 4 of 4 ormlite
cases, plus JI-04 and HO-06. The rule is now *package first, widen to the whole
module if the package yields zero*. This is a correction of a demonstrated
false-negative source, not a threshold moved to suit an outcome — and it was
declared in the held-out pre-registration before that data was scanned.

Cases it recovered: **JI-04** (0/134 package → 1/382 module) and **HO-06**
(0/18 → 147/4,444). Cases it did not rescue: JI-01/02/03, HO-01, HO-09, all
still 0 at full module. Those are genuine negatives for the pairwise model.

**Mechanism-aware scoring (A8).** The v2 score covered mechanisms A and B.
Class D — polluter writes field *f*, a class initialiser reads *f* while
building a static, and the target reads *that* static — links a write and a
read on **different fields** and is invisible to any writes∩reads model.
`src/scoring.py` orders evidence by strength, with no fitted weights:
`(-|writes∩reads|, -clinit_link, -|touches∩reads|)`.

## 3. Held-out validation 2 — the evidence that counts

Frozen in `9157b24` at 17:00:57, scanned afterwards. 11 fastjson reserve
victims; 8 reproduced; **6 distinct confirmed polluters**.

| Case | Cands | OBO | MECH | Saving | Top-20% | Cause |
|---|---|---|---|---|---|---|
| HO-02 | 72 | 5 | 1 | 80.0% | yes | B |
| HO-03 | 30 | 1 | 1 | 0.0% | yes | A |
| HO-04 | 30 | 1 | 1 | 0.0% | yes | A |
| HO-05 | 34 | 29 | 1 | 96.6% | yes | A |
| HO-07 | 17 | 14 | 3 | 78.6% | yes | A |
| HO-08 | 722 | 39 | 1 | 97.4% | yes | A |
| HO-10 | 20 | 1 | 1 | 0.0% | yes | B |
| HO-11 | 20 | 1 | 1 | 0.0% | yes | B |

- **P1** median saving 39.3% ≥ 30% → **confirmed**
- **P2** top-20% in 8/8 → **confirmed**
- **P3** MECH not worse than LEX (39.3% vs 39.3%) → **confirmed**
- **P4** zero cases classified `C_UNSUPPORTED` in this set

The three 0.0% rows are cases where OBO already had the polluter first; the
ranker also placed it first. They are counted, not discarded.

## 4. What is NOT established

- **Mechanism D is unvalidated.** All 8 held-out cases are class A or B, so the
  D term never fired. It satisfied non-inferiority but its *benefit* rests on
  ormlite alone, where D was discovered — development data. The ormlite figures
  (OR-01 rank 769→6, OR-02 769→1) are development results and must be labelled
  as such.
- **Held-out set is single-project.** All 11 are fastjson. Cross-domain transfer
  of the ranking claim is still unproven; the ormlite attempt failed under the
  v2 rule and was not re-run under A8 as a held-out test.
- **Five cases never reproduced** even at full module: JI-01/02/03 (suite-level
  or multi-predecessor), HO-01, HO-09. These are limits of the pairwise model,
  reported in the yield.

## 5. Process errors found and corrected

1. **jsoniter suite context** (v1) — 182 fabricated polluters; fixed by
   reproducing the declared Surefire execution context.
2. **TZ override** (v1) — erased the order dependence under measurement;
   removed, direction now classified empirically.
3. **Constructor parsing** (v2) — `javap` quotes constructor call sites
   (`."<init>":`), so constructor bodies and edges were silently dropped;
   repaired, which moved FJ-03 from `C_UNSUPPORTED` to `B_VIA_STATIC_REF`.
4. **Scan-before-classify** (v3) — the held-out cases were scanned before
   isolation classification, so 9 of 11 were mislabelled VICTIM when they are
   BRITTLE. Corrected offline from stored `victim_status` with no
   re-execution; had it gone unnoticed, HO-03/04/06 would have reported ~100%
   of candidates as polluters.

All four are recorded because a harness that can fabricate results is a
first-class risk for this project, and the ability to detect them is part of
what the POC demonstrates.

## 6. Decision

**Strong Proceed.**

All five pre-registered gates pass, with the two substantive ones measured on
held-out data containing six independent polluters. The pipeline reproduces
across three projects, two test conventions (JUnit 3 and 4) and two domains,
with 18 of 18 reproduced cases replaying 10/10.

The defensible claim is: *a budget-aware diagnosis pipeline that reproduces
order-dependent failures reliably, plus a cause taxonomy that states in advance
whether its resource signal applies, and a mechanism-aware ranking that cuts
median confirmations by 39.3% against OBO on held-out cases.*

Two claims deliberately not made: that the ranking transfers across domains,
and that mechanism D contributes. Both are named as the next iteration's work.
