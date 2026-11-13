# ADR-011 — Deletion evidence: check every kept test by repeated removal

**Date:** 2026-11-13 · **Status:** `PROPOSED` — needs M1, M2 and M3 ·
**Owner:** M2 (runs and records) with M3 (acceptance rule, storage in the report) ·
**Closes:** FT004 · **Work package:** W20 ·
**Builds on:** [[03-Design/decisions/ADR-007-w10-ddmin-minimisation]],
[[03-Design/decisions/ADR-010-verdict-contract-v2]] (claim S3)

## Context

`runner/minimise.py` `ddmin` asks one question per subset — "does the victim fail with the
reference signature after these tests?" — runs it **once**, and caches the answer. The final
verification repeats the kept sequence `n` times. Nothing ever repeats the sequence with one kept
test removed.

That is sound when outcomes are deterministic. When they are not, one unlucky trial is enough to
keep a test that is not needed, and the report still says `VERIFIED` and "1-minimal".

Reproduced on `main` `7cf453d`, 2026-11-13 ([[evidence-m2]]): P alone is enough to make the victim
fail, but `[P, victim]` passes on the two single trials it is given (one in the one-by-one search,
one in `ddmin`). The result keeps **P and Q**, is `VERIFIED` 20/20 — and `[P, victim]` then fails
20 of 20.

What `ddmin` really guarantees: the result is 1-minimal **for the answers it happened to observe**.
Our report claimed more than that.

## Decision

### 1. After minimisation, run a deletion check for every kept test

For a kept set `R = [p1 … pk]` and each `p` in `R`: run `R without p`, then the victim, `m` times
in fresh JVMs, and tally the victim's outcomes with the four categories of ADR-010.

| Status of `p` | Rule | What it means |
| --- | --- | --- |
| `NEEDED` | `passed == m` | Without `p` the victim passed every time. The failure rate without `p` is below the Wilson upper bound of 0 in `m` — 0.161 at `m = 20` |
| `NOT_NEEDED` | Wilson 95% lower bound of `matched / m` ≥ 0.70 | Without `p` the failure still reproduces reliably. `p` is dropped and the checks start again on the smaller set |
| `INCONCLUSIVE` | anything else | Removing `p` sometimes reproduces the failure, or fails differently, or crashed. The sequence is not stable enough to call minimal |

`m` defaults to `n` (20). The thresholds are the ones the sequence check already uses, so there is
one policy, not two.

### 2. One polluter costs nothing extra

For `R = [p]`, "R without p" is the victim alone — the alone check has already measured it. The
deletion check for a single polluter **is** the alone tally, reused and labelled as such.

### 3. The loop is bounded

Dropping a `NOT_NEEDED` test restarts the checks on a set one smaller, so there are at most `k`
rounds. Each round re-verifies the new, shorter sequence `n` times. Every run goes through the
execution budget ([[03-Design/decisions/ADR-014-budget-ledger-and-ranked-search]]); if the budget
ends first, the remaining checks are recorded as not run.

### 4. What the report says

```json
"deletion_checks": [
  {"removed": {"class": "…ToggleAPolluterTest", "method": "setFlagA"},
   "runs": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0},
   "status": "NEEDED", "source": "deletion-run"},
  {"removed": {"class": "…ToggleBPolluterTest", "method": "setFlagB"},
   "runs": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0},
   "status": "NEEDED", "source": "deletion-run"}
]
```

`assurance.sequence.deletion` (ADR-010):

| Value | When | Effect on the verdict |
| --- | --- | --- |
| `DELETION_VERIFIED` | Every kept test is `NEEDED` | Claim S3 established |
| `INCONCLUSIVE` | At least one is `INCONCLUSIVE` | `CANDIDATE [DELETION_EVIDENCE_INCONCLUSIVE]` |
| `INCOMPLETE` | At least one check was not run, or ran fewer than 10 times | `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]` |
| `NOT_APPLICABLE` | No polluter was found | — |

`source` is `deletion-run` or `alone-check` (section 2).

### 5. The words we use

| Before | After |
| --- | --- |
| "1-minimal" | "deletion-verified: each kept test was removed and the failure did not return in `m` of `m` runs" |
| "every test in the result is needed" | "…is needed, with the failure rate without it below 0.161 at 95% confidence (`m` = 20)" |
| — | When the checks did not run: "reduced by single-trial delta debugging; not deletion-verified" |

Never "minimum". That has not changed (claims ledger D9).

### 6. `ddmin` itself stays as it is

Single-trial `ddmin` is kept: it is cheap, and its two possible mistakes are now both caught
afterwards.

| `ddmin` mistake | Caught by |
| --- | --- |
| Keeps a test that is not needed (a failing subset happened to pass once) | The deletion check finds it `NOT_NEEDED` and drops it |
| Shrinks to a subset that does not reliably fail (a passing subset happened to fail once) | The sequence check: below the threshold gives `CANDIDATE`, zero matches gives `UNRESOLVED` |

An option to repeat each `ddmin` trial is not added now. It multiplies the search cost, and the
checks above already protect the verdict.

## Tests to write before the fix

| Test | Scenario | Expected |
| --- | --- | --- |
| T1, scripted | The FT004 counterexample above | Q is found `NOT_NEEDED` and dropped; final sequence `[P, victim]`; `DELETION_VERIFIED` |
| T2, scripted | Removing Q reproduces 9 of 20 | Q `INCONCLUSIVE`; `CANDIDATE [DELETION_EVIDENCE_INCONCLUSIVE]`; both tests still listed |
| T3, real fixture F3 | Two polluters, both required | Both `NEEDED`, 20/20 passes each; `VERIFIED` |
| T4, real fixture F1 | One polluter | One check, `source: alone-check`, no extra JVM runs |
| T5, scripted | Budget ends after the first deletion check | Second check recorded as not run; `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]` |

T1 must fail on `7cf453d` first.

## Cost

For `k` kept tests, one round costs `k × m` JVM launches and `k × m × k` test-method invocations.
F3 (`k = 2`, `m = 20`): 40 launches, 80 invocations, on top of today's 20-run sequence check.

## Consequences

- `DiagnosisRuns` gains `deletions`; the report gains `deletion_checks`. Both are contract changes
  agreed together with ADR-010.
- The CLI summary line "1-minimal, not necessarily the minimum" changes to the wording in
  section 5.
- Every deletion run is one more line in the execution record, with step `deletion` and the
  removed test, so the recount checker of ADR-013 can recompute each tally.

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☐ | |
| M2 | ☐ | |
| M3 | ☐ | |
