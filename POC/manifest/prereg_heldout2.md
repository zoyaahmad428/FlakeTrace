# Pre-registration — held-out validation 2

Written and committed BEFORE the held-out cases were scanned. Nothing in this
document may be revised after the outcome tables exist; a superseding
pre-registration must be a new file.

## Why a second held-out set is needed

Held-out validation 1 (ormlite-core, `results/heldout_validation.csv`) rejected
the v2 depth-2 LEX rule: median saving 0.0%, top-20% in 1 of 4.

Diagnosing that rejection produced mechanism **D** (write -> class initialiser
-> read on a *different* field) and the A8 mechanism-aware score in
`src/scoring.py`. Because D was discovered by inspecting ormlite, **ormlite is
now development data** and cannot evidence the A8 score. Its post-hoc numbers
(OR-01 rank 769 -> 6, OR-02 769 -> 1) are reported as development results only.

## The rule under test (frozen)

`src/scoring.py`, mode `MECH`, at resource depth 2. Score is a tuple ordered by
strength of evidence, with no fitted weights:

    s1  |writes(c) INTERSECT reads(v)|         mechanism A
    s3  1 if a clinit-transported link exists  mechanism D
    s2  |touches(c) INTERSECT reads(v)|        mechanism B

ordered `(-s1, -s3, -s2)`, ties broken by declared order.

## Held-out set (frozen)

The 11 unused fastjson victims at commit `e05e9c5e` listed in
`manifest/pool_two.csv` and not already in `manifest/cases.csv`. Candidate sets
use the escalating-scope rule: the victim's package first, widened to the whole
module only if the package yields zero OD-relevant candidates.

These cases have not been scanned. Their polluters are unknown at the time of
writing.

## Predictions

1. **Primary.** Across the reproduced held-out cases, the `MECH` score achieves
   a median saving of at least 30% against the OBO baseline.
2. **Secondary.** `MECH` places a confirmed OD-relevant candidate in the top-20%
   of the candidate set for a majority of reproduced held-out cases.
3. **Non-inferiority.** `MECH` is not worse than `LEX` on median saving. If it
   is, the D term is noise rather than signal.
4. **Coverage.** Cases classified `C_UNSUPPORTED` are excluded from 1-3 and
   reported separately, since no score over shared statics can rank them. The
   count of such cases is itself a reported result.

## What refutes the rule

Any of: median saving below 30%; top-20% in a minority of cases; or `MECH`
scoring worse than `LEX`. A refutation is reported as such and the ranking
claim stays at Revise-then-Proceed.

## Independence caveat recorded in advance

Six of the eleven victims were fixed by fastjson PR 2148 and may therefore
share a polluter. The number of DISTINCT confirmed polluters will be reported
alongside the case count, and the effective sample size is the number of
distinct polluters, not the number of victims.
