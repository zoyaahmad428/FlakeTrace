# ADR-014 — Budget-aware diagnosis: one ledger, a verification reserve, evidence-ranked search

**Date:** 2026-11-13 · **Status:** `PROPOSED` — needs M1, M2 and M3 ·
**Owner:** M2 (ledger, planner, integration) with M1 (candidate ranking) and M3 (measurement) ·
**Closes:** FT007; the official instruction "complete budget-aware planning" ·
**Work packages:** W24, W25 ·
**Builds on:** [[03-Design/decisions/ADR-004-w7-diagnosis-runs]] (the unused `priority` hook),
[[03-Design/decisions/ADR-006-evidence-depth-auto-deepen]],
[[03-Design/decisions/ADR-011-deletion-evidence]]

## Context

The project was approved as **budget-aware** diagnosis: choose which experiment to run next,
within one finite execution budget, using incomplete evidence, and keep enough of the budget to
verify the answer (FR-4, claims ledger D6, D7). The supervisor calls this "the defining complex
computing contribution" and found none of it built:

| Approved | On `main` today |
| --- | --- |
| One budget in test-method invocations and wall-clock time | `--n` and `--shuffles` only. A diagnosis runs until it finishes |
| A verification reserve the search cannot spend | None |
| Evidence guides the search | `runner/cli.py` calls the extractor **after** the polluters are found. `find_polluter(priority=…)` exists and is never given a priority |
| Two policies, compared | One fixed order: the original order, one test at a time |

We are not starting from nothing. The POC measured evidence ranking **offline** on real fastjson
cases (`POC/decision/decision_record_v3.md`, 2026-09-04): on eight pre-registered held-out cases
the ranked order reached the first relevant test with a median 39.3% fewer confirmations than the
original order. That result used the POC's own extractor and scoring (`POC/src/scoring.py`), on
one project. The **product** has never ranked anything.

## Decision

### 1. A ledger that every JVM run goes through

```python
@dataclass
class Budget:
    limit_invocations: Optional[int]     # None = unlimited, still counted
    limit_seconds: Optional[float]
```

| | |
| --- | --- |
| Cost unit | **Test-method invocations** — one `run_ordered(order)` costs `len(order)`. Frozen definition D7. JVM launches, wall-clock seconds and static-analysis seconds are counted beside it |
| Where | A `BudgetedRunner` wraps the runner, exactly as `RecordingRunner` does today. No search code counts by hand |
| Phases | `reproduce` · `shuffle` · `alone` · `search` · `minimise` · `verify` · `deletion` — the labels already written to the record |
| Refusal | A run that would cross the limit is **not started**. The ledger raises `BudgetExhausted(phase)` and `diagnose()` ends with what it has |
| Proof | The ledger's totals are recomputable from the record, so `verify-bundle` (ADR-013) checks them |

### 2. A verification reserve the search cannot touch

Verification is what turns a guess into a certificate, so it is paid for first.

```
reserve      = n            the alone check
             + 2 × n        the sequence check for one polluter: [p, victim], n times
explore      = limit − reserve        reproduce, shuffle, search, minimise may spend only this
```

| Situation | Behaviour |
| --- | --- |
| The limit cannot cover the reserve plus one run of the starting order and one candidate pair | Refused at the start as an input error that states the minimum for this `n` |
| `explore` runs out before a polluter is found | `UNRESOLVED(BUDGET_EXHAUSTED)`, with "tried `k` of `N` candidates" and the next step |
| Minimisation keeps `k > 1` tests, so verification costs more than the reserve | Sequence check first, with as many repetitions as are left; then deletion checks. Whatever could not run gives `CANDIDATE` with `BUDGET_EXHAUSTED` and the matching deletion reason — never a `VERIFIED` on thin evidence |

The reserve is a **policy**, not a published number (claims ledger D6). The experiment that tests
it — the same cases with the reserve switched off — is part of the evaluation plan.

### 3. The report carries its budget account

```json
"budget": {
  "limit_invocations": 600, "limit_seconds": null, "reserve_invocations": 60,
  "spent": {"reproduce": 16, "alone": 20, "search": 24, "minimise": 0,
            "verify": 40, "deletion": 0},
  "launches": 53, "wall_seconds": 71.4, "analysis_seconds": 3.2,
  "policy": "ranked", "exhausted": false,
  "candidates": {"total": 14, "tried": 1}
}
```

(Illustrative numbers.) This is the "budget account" the certificate contract lists and the
report has never had.

### 4. Two search policies in the same pipeline

| Policy | Candidate order | Role |
| --- | --- | --- |
| `original` | The order the tests ran in | The baseline. Today's behaviour |
| `ranked` | Evidence first (section 5), then the rest in original order | The contribution |
| `random` (seeded) | A seeded shuffle | The floor, for the evaluation only |

`--policy original|ranked|random`. Everything after the candidate order — verification, deletion
checks, the report, the ledger — is identical. So two policies run on the same case, with the same
budget and `n`, reach **the same endpoint**, and their total invocations can be compared fairly.
That is the like-for-like comparison FT008 says the random-order detection baseline is not.

### 5. Ranking by static evidence — Member 1's output, Member 2's input

```python
rank_candidates(project, victim, candidates, depth=DEFAULT_DEPTH) -> List[RankedCandidate]
# RankedCandidate: test, score (a tuple), reasons (the edges behind the score)
```

The score is a tuple compared left to right. **No fitted weights** — the POC's rule, carried over:

| Position | Evidence | Strength |
| --- | --- | --- |
| 1 | The candidate **writes** a resource the victim **reads** (count of such resources) | Strongest: the product's existing edge |
| 2 | The shallowest depth at which that edge was found (shallower first) | Tie-break |
| 3 | Original position | Final tie-break, so `ranked` equals `original` when there is no evidence |

Two further terms exist in the POC and are **not** in this first version: a class-initialiser link
(write → `<clinit>` → read) and co-touching the same static. Member 1 decides whether either is
cheap enough to add; each is switched on only together with a measured comparison.

Rules that keep it honest:

- The ranking rule is fixed **before** it is run on any case with known ground truth (Member 1's
  condition on ADR-004).
- Each test is analysed once and cached; ranking `N` candidates costs `N + 1` analyses, not `N`
  pair analyses.
- Analysis time is reported as `analysis_seconds` and counts against a wall-clock limit.
- A candidate with no edge is **not** ruled out. Ranking changes the order, never the candidate
  set. "Missing evidence is not proof of independence" stays true.

### 6. The planner's one real decision in this version: deepen or run

Evidence is not free either. When no candidate has an edge at the default depth and the analysis
was cut off by the depth limit, there are two ways forward:

| Option | Costs | Gains |
| --- | --- | --- |
| Analyse deeper (ADR-006) | Analysis seconds — measured on fastjson at 143 s to 181 s for 722 candidates across depths 1 to 5 | Possibly an edge, and so a ranked order |
| Start running pairs in the original order | Two invocations per candidate | A definite answer for that candidate |

Rule for this version: deepen one level at a time while analysis time stays under a fixed share
of the wall-clock limit (20% proposed; unlimited when no time limit is set, up to the maximum
depth). The share is a policy value and is recorded in the report.

This is the loop [[03-Design/architecture]] has always named — *the planner's budget decisions
change what the collector observes, which changes the planner's next decision* — in its smallest
working form.

### 7. What is deliberately left for FYP-2

The **adaptive, cost-aware policy** (FR-4's second policy): keep a belief for every candidate,
and choose each next experiment — one pair, or a group of candidates in one JVM — by expected
information gain per invocation. Group tests cost more invocations and can clear many candidates
at once; pair tests are cheap and clear one. Order evidence comes free from the shuffled orders
already run: a test that preceded the victim in a *passing* order is a weaker suspect.

It needs measured baselines first, so it is scheduled after the Final. Its two ablations — no cost
term, no verification reserve — are already in [[05-Testing/evaluation-plan]].

## What must be demonstrated by the Final

The supervisor's wording: *"count total execution cost, stop at the shared limit, retain
verification resources and compare with an unranked search at the same endpoint."*

| # | Evidence | Owner |
| --- | --- | --- |
| 1 | A diagnosis with a limit stops at it: a test where the next run would cross the limit and is not started | M2 |
| 2 | A budget too small to finish gives `UNRESOLVED(BUDGET_EXHAUSTED)`, a report and a budget account | M2, M3 |
| 3 | The reserve holds: with the search exhausted, the alone and sequence checks still ran in full | M2 |
| 4 | `ranked` against `original` on the fixture and on the real case, same budget, total invocations to the same verdict | M3 |
| 5 | The same comparison **offline** on the POC's stored scan tables, using the product's `rank_candidates` — no JVM runs | M3 with M1 |

Item 5 is cheap and decisive. `POC/results/scan_FJ-03.csv` holds the real outcome of all 524
candidate pairs for one fastjson victim: 6 are relevant and the first sits at position **368** in
the original order. Wherever the product's ranking puts the first of those six is a real result,
good or bad.

**A poor result is reported as it is.** The fallback ladder already says what happens then: order
evidence carries the ranking and the contribution claim changes accordingly
([[00-Meta/risk-register]]).

## Tests to write first

| Test | Expected |
| --- | --- |
| Scripted: 10 candidates, limit just above the reserve | Search stops after the affordable pairs; `BUDGET_EXHAUSTED`; the alone check ran `n` times |
| Scripted: limit below the minimum | Input error naming the minimum |
| Scripted: polluter is candidate 9 of 10 and the only one with an edge | `original` tries 9 pairs, `ranked` tries 1; same verdict; ledger totals differ by 16 invocations |
| Scripted: no candidate has an edge | `ranked` and `original` produce the identical order |
| Real F1–F4 with `--policy ranked` | Same verdicts as today |
| Recount | Ledger totals equal the totals recomputed from the record |

## Consequences

- `diagnose()` gains `budget` and `policy`; `DiagnosisRuns` gains the ledger snapshot; the report
  gains `budget`. Contract changes, agreed with ADR-010.
- `evidence/` gains `rank_candidates` and a per-test cache (Member 1).
- The CLI gains `--budget-invocations`, `--budget-seconds`, `--policy`.
- The candidate set for a large module needs the frozen scope rule (victim's package first, the
  whole module if the package yields nothing) as an option. Without it a fastjson diagnosis
  would search thousands of tests ([[05-Testing/real-case-protocol]]).

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☐ | |
| M2 | ☐ | |
| M3 | ☐ | |
