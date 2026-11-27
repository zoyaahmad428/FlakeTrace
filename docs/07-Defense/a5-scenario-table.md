# A5 — Show diverse applicable scenarios

*Panel action A5 (proposal defence); W40 (supervisor review, 23 Nov). v1 · 2026-11-27 · written by M3.
Status: `DRAFT`, then the supervisor's acceptance ([[10-Final1/action-register]] A5, W40). Existing evidence
only -- every row below is from a real run already recorded; nothing here was run new for this table.*

**Short answer.** FlakeTrace has been exercised on nine fixture scenarios covering four scenario kinds
(single-polluter, multi-polluter, reorder-dependent, and three kinds of negative control), two resource
kinds (static field, system property), two FT005 controls that test the resource check's own honesty, and
one real project (fastjson FJ-03) through both search modes. One real case; whether that is enough for
FYP-1, and the bounded resource-kind question (A10), are for the supervisor to decide -- not claimed here.

## The scenario table

| Scenario kind | Case | Resource kind | Verdict | Bundle |
| --- | --- | --- | --- | --- |
| Single polluter, one resource | F1 | static field | `VERIFIED` | `eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/` |
| Single polluter, one resource | F2 | system property | `VERIFIED` | `eval/bundles/20261121T184816Z-odfixture.FeatureVictimTest#expectsTurboDisabled/` |
| Multi-polluter (both required) | F3 | static field | `VERIFIED` | `eval/bundles/20261121T184910Z-odfixture.ToggleVictimTest#expectsNotBothFlagsSet/` |
| Reorder-dependent (shuffle needed) | F4 | static field | `VERIFIED` | `eval/bundles/20261121T185039Z-odfixture.AlwaysEarlyVictimTest#expectsLateFlagUnset/` |
| Negative control: fails alone | N1 | — | `UNRESOLVED (VICTIM_FAILS_ALONE)` | `eval/bundles/20261121T185141Z-odfixture.NegativeAloneFailTest#alwaysFails/` |
| Negative control: non-order-dependent flake | N2 | — | `UNRESOLVED (VICTIM_FAILS_ALONE)` | `eval/bundles/20261121T185218Z-odfixture.NegativeFlakyTest#sometimesFails/` |
| Negative control: external-environment dependency | N3 | — | `UNRESOLVED (NOT_REPRODUCED)` | `eval/bundles/20261121T185248Z-odfixture.EnvDependentNegativeTest#onlyFailsUnderCI/` |
| Regression: victim fails alone, differently | N4 | — | `UNRESOLVED (VICTIM_FAILS_ALONE_DIFFERENTLY)` | `eval/bundles/20261121T185339Z-odfixture.DualFailureVictimTest#expectsStateTwo/` |
| FT005 control 1: write-then-restore | `controls.RestoringVictimTest#check` | static field (`State.restored`) | `VERIFIED (sequence)` | *not bundled* -- run with `--records`, not `--bundle` ([[evidence-m2]], 2026-11-20) |
| FT005 control 2: unrelated overlap | `controls.TwoFieldVictimTest#check` | static field (`State.a`, with `b` disclosed as an extra edge) | `VERIFIED (sequence)` | *not bundled* -- run with `--records`, not `--bundle` ([[evidence-m2]], 2026-11-20) |
| Real project, order mode | FJ-03 `MaxBufSizeTest#test_max_buf`, package scope | *(no static evidence found)* | `UNRESOLVED (NOT_REPRODUCED)`, 12,817 invocations | `eval/bundles/20261124T151413Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf/` |
| Real project, pair mode | FJ-03 `MaxBufSizeTest#test_max_buf`, package scope | *(no static evidence found)* | `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`, 798 invocations | `eval/bundles/20261122T120044Z-com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf/` |

**Scenario kind** is each fixture case's own `category` field in `fixtures/od-fixture/ground_truth.json`
(written before any run, per that file's own `authored_before_any_run` note), collapsed to plain English here.
**Resource kind** is `report.json`'s own `shared_resource.kind`; the four negative controls have no resource
at all because no polluter is ever blamed for them (ADR-010's "no test is blamed" rule) -- shown as `—`, not
omitted, so the table does not look incomplete where it is actually by design.

**Not bundled, not an oversight:** the two FT005 controls were run to answer a specific question (does the
resource check avoid a causal label, and does it disclose every edge it finds) before Interface 8 (bundles)
existed as a concept, and have not been re-run with `--bundle` since -- their real result is recorded in
`docs/evidence-m2.md`'s 2026-11-20 entry, reproduced the same day, but there is no portable bundle folder to
link. Said so plainly rather than inventing a bundle path or silently dropping the row.

**Two resource kinds, not more:** every `VERIFIED` row above is a static field or a system property --
`evidence/extract.py`'s own scope (ADR-006/ADR-010 §6). Filesystem, environment variables and the clock are
read/written by nothing in this fixture set and are explicitly FYP-2 (A10, [[07-Defense/decisions/resource-family-boundaries]]).

## What this table does and does not claim

- It does **not** claim one real case is enough to generalise from -- A10 and the "one case for FYP-1"
  question are the supervisor's to decide, named as open in A5's own action-register row.
- It does **not** claim the two FJ-03 rows differ in result because pair mode is "better" -- order mode's
  `NOT_REPRODUCED` and pair mode's `CANDIDATE` answer different questions (whether *any order* FlakeTrace
  can discover or shuffle reproduces the failure, vs. whether a *constructed pair* does); see ADR-016 and
  [[05-Testing/real-case-protocol]] for why pair mode exists at all.
- Every verdict above is quoted exactly as the real report says it, including the full `CANDIDATE` reason and
  the `UNRESOLVED` reason -- never shortened to just "passed"/"failed".

## Verified

Every row is `existing evidence only`, per the task: no command was run new for this table. Cross-checked
each bundle path still resolves and each real `report.json`'s own `outcome`/`unresolved_reason`/
`shared_resource` against the table before writing it, rather than copying the numbers from an earlier,
possibly-renamed reference (the W36 matrix follow-up on 2026-11-27 found exactly this kind of drift once
already, in `eval/bundles/README.md`).
