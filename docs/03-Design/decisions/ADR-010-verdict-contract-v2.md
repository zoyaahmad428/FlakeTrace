# ADR-010 — Verdict contract v2: outcome categories, what `VERIFIED` asserts, a report for every status

**Date:** 2026-11-13 · **Status:** `ACCEPTED` by M1, M2 and M3 on 2026-11-13 (in person;
PR #101), with Q1–Q3 settled below. The supervisor's view on what `VERIFIED` means is still to be
asked ([[10-Final1/supervisor-agenda]] item 2); Q1 and Q3 are reopened if it differs ·
**Owner:** M3 (decision, schema, report) with M2 (runner counts) and M1 (resource wording) ·
**Closes:** FT003, FT010, the wording half of FT005, part of FT017 ·
**Work packages:** W17, W18, W19, W16 ·
**Builds on:** [[03-Design/decisions/ADR-004-w7-diagnosis-runs]],
[[03-Design/decisions/ADR-008-not-reproduced-and-order-search]]

> **This ADR proposes changes to two shared contracts:** [[contracts/report-schema]] (with
> `eval/schema/report.schema.json`) and the `DiagnosisRuns` shape in [[contracts/interfaces]].
> Nothing in those files changes until all three members tick the table at the end.

## Context

The Mid review found three ways a report can say more than the evidence does.

**1. A victim that fails alone with a different exception is treated as passing alone (FT003).**
`runner/verify.py` `repeat()` returns two numbers: runs that failed *with the reference signature*,
and runs that failed *for any reason*. In `runner/diagnose.py` `run_steps()` the alone check keeps
only the first:

```python
alone_successes, alone_any = repeat(runner, [victim], victim, reference, n)
if alone_successes >= 1:
    return DiagnosisRuns(VICTIM_FAILS_ALONE, ...)
...
return DiagnosisRuns(status, ..., n, 0, search_runs, ...)   # alone_n = n, alone_successes = 0
```

`alone_any` is never used again. `eval/outcome.py` then reads `isolation_successes == 0` as "the
victim never failed alone", and its `VERIFIED` rationale says so in words.

Reproduced on `main` `7cf453d`, 2026-11-13: a scripted victim that fails alone 20/20 with
exception B and fails after P 20/20 with exception A gets a schema-valid **`VERIFIED`** naming P
([[evidence-m2]]).

**2. One runner status has no report (FT010).** `eval/report.py` raises `UnhandledStatus` for
`NO_SINGLE_POLLUTER`; the command prints "No report" and exits with code 3. The requirement says
every diagnosis ends in a typed outcome.

**3. The word `VERIFIED` covers two different kinds of evidence (FT005).** Replaying a sequence is
measured by execution. A resource edge is a static intersection of *possible* writes and reads.
The report presents them under one word, and the rationale says "a resource edge supports it".

There is also an old inconsistency (FT017): [[03-Design/certificate-contract]] defines
**Candidate** as "replays, but at least one certification requirement is unmet — most often the
resource path is missing". The code returns `UNRESOLVED(NO_SUPPORTED_RESOURCE_EVIDENCE)` for
exactly that case.

## Decision

### 1. One victim run has exactly one of four outcomes

| Category | Meaning |
| --- | --- |
| `PASS` | The victim passed |
| `MATCH` | A real failure whose signature matches the reference |
| `OTHER` | A real failure with a different signature |
| `INFRA` | A crash, a timeout, or the test was not executed (the runner's synthetic `flaketrace.*` types) |

Every repeated phase returns a **tally** of these four, not two overlapping numbers:

```python
@dataclass(frozen=True)
class RunTally:
    n: int
    passed: int
    matched: int
    other: int
    infra: int          # passed + matched + other + infra == n, checked on construction
```

The classification lives in **one** function, next to `FailureSignature` in `eval/baseline.py`
(the home of the shared types), together with the one definition of the synthetic prefix
`flaketrace.` — today a constant in `runner/search.py` and three string literals in
`runner/order_runner.py`. The recount checker of ADR-013 needs the same rule on Member 3's side, so
it must not live only in the runner. Member 3 owns `eval/baseline.py`. *Agreed 2026-11-13: while
Member 3 has no laptop, Member 2 writes `RunTally` and the classifier there and Member 3 reviews it
when back.*

`DiagnosisRuns` carries `alone: RunTally` and `sequence: RunTally` in place of
`alone_n / alone_successes` and `sequence_n / sequence_successes / sequence_any_failures`.

### 2. What `VERIFIED` asserts — exactly four claims

| Claim | Evidence | Established when |
| --- | --- | --- |
| **S1 reproduces** | `sequence` tally | Wilson 95% lower bound of `matched / n` ≥ 0.70 (unchanged policy D4) |
| **S2 passes alone** | `alone` tally | `passed == n`. Any `matched`, `other` or `infra` run breaks it |
| **S3 every kept test is needed** | Deletion checks, [[03-Design/decisions/ADR-011-deletion-evidence]] | Every kept predecessor is `NEEDED` |
| **R1 a static overlap exists** | Member 1's edges | At least one supported polluter-write / victim-read edge for every polluter (the ADR-007 rule, unchanged) |

`VERIFIED` asserts S1, S2, S3 and R1, **and nothing else**. In particular it does **not** assert
that the named resource is the cause. Every place the word is shown says so:

```
VERIFIED (sequence)   odfixture.ConfigVictimTest#expectsDefaultMode
  resource: static overlap on Config#mode — a possible mechanism, not confirmed as the cause
```

Words that are no longer used for static evidence, in code, UI, report and slides: *cause, caused
by, root cause, mechanism found, explains the failure*. Use: *potential shared resource, static
overlap, possible write/read*.

### 3. The decision table, first match wins

| # | Condition | Outcome |
| --- | --- | --- |
| 1 | Source integrity check failed | `UNRESOLVED(SOURCE_INTEGRITY_FAILED)` |
| 2 | The search was inconclusive: the failure was seen once and could not be obtained again | `UNRESOLVED(INCONSISTENT_OUTCOMES)` ← new, FT010 |
| 3 | The execution budget ran out before a sequence was found | `UNRESOLVED(BUDGET_EXHAUSTED)` ← new, ADR-014 |
| 4 | No real failure anywhere, and at least one infrastructure failure | `UNRESOLVED(INFRASTRUCTURE_FAILURE)` |
| 5 | No real failure anywhere | `UNRESOLVED(NOT_REPRODUCED)` |
| 6 | `alone.matched ≥ 1` | `UNRESOLVED(VICTIM_FAILS_ALONE)` |
| 7 | `alone.other ≥ 1` | `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)` ← new, **FT003** |
| 8 | `alone.infra ≥ 1` (so `alone.passed < n`) | `UNRESOLVED(INFRASTRUCTURE_FAILURE)` |
| 9 | `sequence.matched == 0` and `sequence.other ≥ 1` | `UNRESOLVED(SIGNATURE_MISMATCH)` |
| 10 | `sequence.matched == 0` and `sequence.infra ≥ 1` | `UNRESOLVED(INFRASTRUCTURE_FAILURE)` |
| 11 | `sequence.matched == 0` | `UNRESOLVED(NOT_REPRODUCED)` |
| — | *From here the sequence reproduced at least once and the victim passed alone every time* | |
| 12 | Any of S1, S3, R1 is not established | `CANDIDATE`, with every unmet claim listed in `candidate_reasons` |
| 13 | Otherwise | `VERIFIED` |

`candidate_reasons` values: `BELOW_REPLAY_THRESHOLD` · `DELETION_EVIDENCE_INCOMPLETE` ·
`DELETION_EVIDENCE_INCONCLUSIVE` · `NO_SUPPORTED_RESOURCE_EVIDENCE` · `BUDGET_EXHAUSTED`.

**Row 7 in plain words.** If the victim fails on its own, in any way, we cannot say an earlier
test makes it fail. The report still records what was seen — "after P the failure changes to A in
20 of 20 runs" goes in `limitations` — so the developer loses nothing, but no test is blamed.

**Row 8 is deliberately strict.** One timeout in twenty alone runs withholds `VERIFIED`. The
alternative, re-running infrastructure failures a bounded number of times, is cheap to add later
and is left as an open question below.

### 4. One change of behaviour that needs a decision: no edge → `CANDIDATE`

Today a sequence that replays 20/20, passes alone 20/20, and has **no** static edge is
`UNRESOLVED(NO_SUPPORTED_RESOURCE_EVIDENCE)`. Under row 12 it becomes
`CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`.

| | Option A — `CANDIDATE` (recommended) | Option B — keep `UNRESOLVED` |
| --- | --- | --- |
| Matches the defended certificate contract | Yes, word for word | No |
| Useful to a developer | "We found the order, we cannot explain it" — they can still replay it | Reads the same as "we found nothing" |
| Fits real projects | fastjson needed depth 4–5 for an edge; many real cases will have none | Most real diagnoses would be `UNRESOLVED` |
| Cost | Changes a rule the team agreed on 2026-10-08 | None |

No fixture case's ground truth changes under option A (F1–F4 have edges, N1–N3 stop earlier).

### 5. A report for the inconclusive search (FT010)

The runner status `NO_SINGLE_POLLUTER` is renamed `INCONSISTENT`: it is reached only when the
victim failed in the starting order and then did not fail again — not alone, not after any single
earlier test, not in the full order once more. That is nondeterminism, and the certificate
contract already has a reason for it.

The report is schema-valid, with `polluters: []`, `reduced_sequence` equal to the starting order,
every count that exists, and a `limitations` line with the next step: *"The failure appeared once
in N runs and could not be obtained again; likely not order-dependent. Re-run with a larger `--n`,
or supply the exact failing order with `--order`."* The command exits 0 because a report was
written. Exit code 3 is retired.

### 6. The report shows its evidence levels

New fields (the schema gains `"schema_version": 2`):

```json
"victim_alone": {"n": 20, "passed": 20, "matched": 0, "other": 0, "infra": 0,
                 "confidence": 0.95, "lower": 0.0, "upper": 0.161},
"reproduction": {"n": 20, "passed": 0, "matched": 20, "other": 0, "infra": 0,
                 "confidence": 0.95, "lower": 0.839, "upper": 1.0},
"assurance": {
  "sequence": {"reproduces": "ESTABLISHED", "passes_alone": "ESTABLISHED",
               "deletion": "DELETION_VERIFIED"},
  "resource": {"level": "STATIC_OVERLAP", "mechanism": "NOT_ASSESSED"}
},
"resource_edges": [ ...every edge Member 1 found, each with its depth... ],
"candidate_reasons": []
```

- `successes` is renamed `matched`; `sequence_any_signature_failures` is replaced by the tally.
- `resource.level` is `NONE`, `STATIC_OVERLAP` or, only after
  [[03-Design/decisions/ADR-015-resource-intervention-check]], `MECHANISM_CONFIRMED`.
- `resource_edges` lists **all** edges, so the one shown in `shared_resource` is no longer the
  only one a reader can see. `shared_resource` keeps its meaning: the first edge in Member 1's
  documented order, shown for convenience.

## Tests to write before the fix

Each must **fail on `7cf453d`** and pass after. Keep the failing run's output in the evidence log.

| Test | Scenario | Expected |
| --- | --- | --- |
| T1, scripted | Alone: B 20/20. After P: A 20/20 | `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)`, `alone.other == 20`, no polluter blamed |
| T2, scripted | Alone: pass 17, B 3. After P: A 20/20 | Same reason, `alone.other == 3` |
| T3, scripted | Alone: pass 18, timeout 2. After P: A 20/20 | `UNRESOLVED(INFRASTRUCTURE_FAILURE)` |
| T4, scripted | Fails once in the starting order, never again | A schema-valid `UNRESOLVED(INCONSISTENT_OUTCOMES)` report, exit 0 |
| T5, **Java fixture N4** | A victim that throws `IllegalStateException` alone and `AssertionError` after its polluter | Ground truth `UNRESOLVED(VICTIM_FAILS_ALONE_DIFFERENTLY)` through the real command — the *integrated* regression the supervisor asked for |
| T6, existing | F1–F4, N1–N3 | Unchanged verdicts, new fields present |

T5 needs a new fixture case and a `ground_truth.json` entry, both Member 3's files. The ground
truth is written **before** the first run, as for every fixture case.

## Consequences

- The seven reports in `eval/reports/` are regenerated under schema v2. They are **new runs**; the
  Mid results stay reachable at tag `mid-eval-v1`.
- `eval/outcome.py`'s `DecisionInput` changes shape. Its tests are rewritten against tallies.
- `ui/` reads reports: Member 2 updates the field names and the wording.
- The report chapters that state what `VERIFIED` means (4.5–4.6, 6.6) are corrected in the same
  iteration ([[10-Final1/report-v2-plan]]).
- [[03-Design/certificate-contract]] is updated to this table once the ADR is accepted.

## Order of work — agree the interface before editing in parallel

1. All three agree this ADR and the `RunTally` shape (W17).
2. M2 adds `RunTally` and the classifier to `eval/baseline.py`; M3 reviews when back *(swapped
   2026-11-13 by M3's agreement, because M3 has no laptop; M3 still owns the file)*.
3. M2 switches `repeat()`, `run_steps()` and `DiagnosisRuns` to tallies (W18). M3 switches
   `decide()`, the schema and `assemble_report()` (W19). T1–T4 turn green.
   *Implementation note (W18, M2, 2026-11-14):* the fields are named `alone_tally` and
   `sequence_tally`, because `DiagnosisRuns.sequence` is already the list of tests. While M3 has no
   laptop they are added **beside** the old count fields, which are filled from the tallies, and
   `NO_SINGLE_POLLUTER` stays importable as an alias of `INCONSISTENT`, so M3's `eval/` code and
   tests keep working unchanged. The old fields and the alias are removed when W19 reads the
   tallies. Until then the verdict for T1–T3 is still the Mid's (`decide()` reads the old fields).
4. M3 adds fixture N4; T5 turns green through the real command.
5. M1 reruns T1–T5 on her own machine at the correction commit and records the result (FT003's
   acceptance requires an independent reproduction).

## Open questions

| # | Question | Who decides | Answer (2026-11-13, M1, M2, M3 in person) |
| --- | --- | --- | --- |
| Q1 | Option A or B for a sequence with no edge (section 4) | All three + supervisor | **Option A.** Replays reliably, passes alone, no static edge → `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`. Still to be put to the supervisor (agenda item 2) |
| Q2 | Should an `INFRA` run be retried a bounded number of times before it counts (row 8)? | M2 + M3 | **No retries for now.** A crashed or timed-out run counts as `INFRA` as it is; row 8 stays strict |
| Q3 | Is `VERIFIED (sequence)` the right display, or should the outcome itself be renamed? | Supervisor | **Parked with a default:** keep `VERIFIED`, always displayed with the qualifier (section 2), until the supervisor decides |

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☑ | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
| M2 | ☑ | Agreed 2026-11-13 in person with M1 and M3; recorded their agreement in PR #101 |
| M3 | ☑ | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
