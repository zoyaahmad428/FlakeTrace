# Component interfaces — shared contract

*Status: `PROPOSED` 2026-10-09 — becomes `FROZEN` once all three members approve it in the
restructure PR. After that, changing it needs all three approvals (see CONTRIBUTING.md).*

This file says how the three members' code connects. The data shape of the final output is in
[report-schema.md](report-schema.md); this file covers the calls that produce it.

## The end-to-end flow for one diagnosis

```
 target project + victim test
          │
          ▼
 ┌─────────────────────────┐   ordered list of tests     ┌──────────────────────────┐
 │ M2  runner/             │ ──────────────────────────▶ │ one fresh JVM per order  │
 │ OrderRunner             │ ◀────────────────────────── │ JUnit 4 execution        │
 │ polluter search         │   per-test pass/fail +       └──────────────────────────┘
 │ minimiser · verifier    │   failure signature
 └──────────┬──────────────┘
            │ victim, polluters, reduced_sequence, raw run counts,
            │ failure_signature, source_integrity, execution_record_reference
            ▼
 ┌─────────────────────────┐   compiled classes of target   ┌───────────────────────────┐
 │ M1  evidence/           │ ◀───────────────────────────── │ javap bytecode, no source │
 │ resource extractor      │                                 │ changes                   │
 └──────────┬──────────────┘
            │ shared_resource, polluter_write_location, victim_read_location
            ▼
 ┌─────────────────────────┐
 │ M3  eval/               │  wilson_interval() → reproduction, victim_alone
 │ outcome.decide()        │  decide() → outcome, unresolved_reason
 │ schema_validator        │  validate_report() → the final JSON report
 └─────────────────────────┘
```

## Interface 1 — `OrderRunner` (implemented by M2, consumed by M2's search and M3's baseline)

Defined in `eval/baseline.py` (written by M3 before any runner existed — the runner must
satisfy it, not the other way round).

```python
class OrderRunner(Protocol):
    def run_ordered(self, order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]: ...
```

| Rule | Why |
| --- | --- |
| All tests in `order` run **in one JVM, in exactly that order** | Shared static state only survives within one JVM; this is the phenomenon |
| Each call to `run_ordered` uses a **fresh JVM** | Calls must not pollute each other |
| Every test in `order` appears in the result | A missing entry is ambiguous; a crash must be reported as a failure |
| A failed test carries a `FailureSignature` (exception type + normalised stack trace) | `FailureSignature.matches()` ignores the message on purpose |
| The target project's source files are never written to | Source-integrity promise to the panel |

M3's `eval/tests/fake_runner.py` is the reference behaviour for tests. Production code never
imports it.

## Interface 2 — resource evidence (implemented by M1, consumed by M2 and M3)

**Input:** path to the target project's compiled classes (`target/classes`,
`target/test-classes`), the victim and the candidate polluters.

**Output:** for each polluter→victim pair, zero or more edges in the report-schema shapes
(illustrative values, copied from M3's hand-written `eval/examples/example_f1_verified.json`):

```json
{
  "shared_resource": {"kind": "static-field", "class": "odfixture.Config", "field": "mode"},
  "polluter_write_location": {"class": "odfixture.ConfigPolluterTest", "method": "pollute", "bytecode_offset": 3},
  "victim_read_location":   {"class": "odfixture.ConfigVictimTest", "method": "expectsDefaultMode", "bytecode_offset": 5}
}
```

Iteration 1 supports `static-field` and `system-property` kinds only. No edge found means
`null` in all three fields, which `decide()` turns into `UNRESOLVED(NO_SUPPORTED_RESOURCE_EVIDENCE)` —
it must never be reported as "no dependency exists".

**Implemented (M1, Phases 2–4):** Python 3 (standard library only), invoked as `python3 -m evidence.extract --classes <dir> --test-classes <dir> --polluter Class#method --victim Class#method [--depth N]`; JSON on stdout, exit codes 0/1/2 — full definition in [resource-evidence.md § Invocation](resource-evidence.md#invocation).

## Interface 3 — report assembly (M3)

M2 passes `DiagnosisRuns` with ADR-010 tallies, `sequence_tally` and `alone_tally`
(`RunTally(n, passed, matched, other, infra)`); the five raw count fields that duplicated them were
removed in A4, 2026-11-20 (agreed by M3; M1's approval in the PR). M3's `eval.stats.wilson_interval` and `eval.outcome.decide` produce the
statistical fields and the verdict; `eval.schema_validator.validate_report` must accept the
assembled report before it is shown or saved.

## Interface 4 — deletion checks (W20, ADR-011; M2 produces, M3 consumes)

*Agreed by M1, M2 and M3 on 2026-11-20 (messages, recorded by M2; confirmed by approving the PR
that adds this section). Built against [ADR-011](../03-Design/decisions/ADR-011-deletion-evidence.md),
accepted 2026-11-13. Not built yet.*

**What the runner (M2) produces.** One new field on `DiagnosisRuns`:

```python
deletion_checks: List[DeletionCheck]       # empty when no polluter was found

DeletionCheck(
    removed: TestIdentifier,   # the kept test left out of this run
    runs: Optional[RunTally],  # the victim's m outcomes without it; None when status is NOT_RUN
    status: str,               # NEEDED | NOT_NEEDED | INCONCLUSIVE | NOT_RUN
    source: str,               # "deletion-run" | "alone-check"
    round: int,                # 1, 2, ... ; +1 each time a NOT_NEEDED test is dropped and checks restart
)
```

- **The runner labels each check**, because a `NOT_NEEDED` test is dropped and the checks restart on
  the smaller set (ADR-011 §3). Rules (ADR-011 §1), using M3's code so there is one policy:
  `NEEDED` if `runs.passed == m`; `NOT_NEEDED` if the Wilson lower bound
  (`eval.stats.wilson_interval`) of `runs.matched / m` ≥ `eval.outcome.DEFAULT_LOWER_BOUND_THRESHOLD`
  (0.70); otherwise `INCONCLUSIVE`. `m` defaults to `n` (20).
- **`NOT_RUN`** (new; ADR-011 §3 says "recorded as not run" but names no value): the budget ended
  before this check; `runs` is `None`. Until the budget ledger (W24) lands nothing ends a check
  early, so it appears only in scripted tests.
- **One polluter:** one check, `source: "alone-check"`, `runs` = the alone tally, no extra JVM runs
  (ADR-011 §2).
- `polluters` and `sequence` hold the **final** set only; checks from earlier rounds stay in the list,
  so a dropped test is still visible.

**What the report assembly (M3) does with them.** `eval/report.py` replaces its interim S3 block
(2026-11-19) and sets `assurance.sequence.deletion` from the checks with the highest `round`:

| Checks in the last round | `deletion` | Verdict effect |
| --- | --- | --- |
| all `NEEDED` | `DELETION_VERIFIED` | claim S3 established |
| otherwise, any `INCONCLUSIVE` | `INCONCLUSIVE` | `CANDIDATE [DELETION_EVIDENCE_INCONCLUSIVE]` |
| otherwise, any `NOT_RUN`, or any `runs.n < 10` | `INCOMPLETE` | `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]` |
| no polluter found | `NOT_APPLICABLE` | — |
| polluters but no checks (fail-safe) | `INCOMPLETE` | never `VERIFIED` |

`INCONCLUSIVE` ranks above `INCOMPLETE`: evidence against the result outweighs missing evidence.
M3 does not re-label checks. The report carries every check in a new `deletion_checks` field, shaped
as in ADR-011 §4 plus `round`, with `status: "NOT_RUN"` and `runs: null` allowed — a schema bump M3
proposes in [report-schema.md](report-schema.md). Wording: ADR-011 §5 (never "1-minimal" without
deletion evidence, never "minimum").

**Who does what, in order.**

1. M2: scripted tests T1, T2, T5 (fake runner; T1 fails on `7cf453d` first), T4 on F1, then the runner code.
2. M3, in parallel: the schema field and the aggregation above, tested with a `FakeDeletionCheck`
   under `eval/tests/` that has exactly these fields — coded against this section, not M2's internals.
3. Together, once both are merged: T3, the real F3 run (`odfixture.ToggleVictimTest#expectsNotBothFlagsSet`,
   polluters `setFlagA`, `setFlagB`). Expected: both `NEEDED`, 20/20 passes each, `VERIFIED`.
4. M1: reproduces T3 independently on their machine and records it in `docs/evidence-m1.md`.

## Interface 5 — candidate ranking (W25, ADR-014 §5; M1 produces, M2 consumes, M3 measures)

*Proposed by M1 on 2026-11-20 at M2's request. Agreed when M2 and M3 approve the PR that adds this
section. Built: `evidence/extract.py` (PR #112, merged 2026-11-20). M2 reviewed the ranking rule on
2026-11-20, before any measurement (iteration-2-plan rule 4). This section describes the merged
code; it does not change it.*

**What the evidence collector (M1) provides.**

```python
rank_candidates(project, victim, candidates, depth=DEFAULT_DEPTH, cache=None) -> List[RankedCandidate]

RankedCandidate(
    test: str,          # "Class#method", one per input candidate
    score: tuple,       # (resources shared, shallowest edge depth or None, original position)
    reasons: list,      # the edges behind the score, in the report's resource_edges shape
    note: Optional[str] # None, or why this candidate could not be analysed
)

AnalysisCache()        # .analysed (count of analyse_test calls), .seconds (their total time)
AnalysisCache.get(project, test, depth)   # that test's Output 1 (analyse_test's result), analysed on first use
```

- **Inputs:** `project` is an `evidence.extract.Project` over the compiled classes. `victim` and
  each candidate are `"Class#method"` strings; the caller converts from `TestIdentifier`.
  `depth` is the analysis depth passed to `analyse_test` (default 2).
- **The rule, fixed, with no weights.** Sort by: (1) more resources the candidate WRITES and the
  victim READS first; (2) then the shallower edge, where an edge's depth is the deeper of its two
  sides, as in `resource_edges`; (3) then the original position. A candidate with no edge has
  `score = (0, None, position)`. With no evidence anywhere, the output is the input order.
- **Never drops.** The output has exactly one entry per input candidate, the same set in a new
  order. A candidate that cannot be analysed (for example, class not found) is kept with
  `reasons = []`, its `note` set, and a no-evidence score.
- **An unanalysable victim raises `ExtractError`.** Nothing can be ranked against it. Under
  `--policy ranked` the runner (M2, when built) catches it, keeps the original order (the same
  result as "no evidence"), and records a limitation.
- **`get`.** Returns the cached Output 1 of `analyse_test` for `(test, depth)`, the shape in
  [resource-evidence.md](resource-evidence.md), analysing it on first use. For a test that could not
  be analysed it raises the stored `ExtractError` again, without retrying. The planner reads its
  `unsupported_observations` (kind `DEPTH_LIMIT`) to decide whether to deepen (Interface 7, P4).
  *Added 2026-11-20 by M1, after reviewing M2's `EvidenceRanker`: `get` was already public and used;
  this line only names it.*
- **Cache and cost.** Each test is analysed once per depth, so ranking N candidates costs N + 1
  analyses. A cache passed in is reused across calls. The budget ledger (M2) reads `analysed` and
  `seconds` for `analysis_seconds` (ADR-014 §3). The planner's deeper analyses go through the same
  cache, so they are counted too.
- **No deepening here.** `rank_candidates` analyses at exactly `depth`. Whether to deepen is the
  planner's decision, charged to the ledger (ADR-014 §6, M2).
- **Wording.** `reasons` are static overlaps, possible mechanisms and not confirmed causes (claims
  ledger G3). A higher rank orders the search; it never says what caused a failure.

**Who does what.**

1. M1: the function, the cache and their tests (done, PR #112). Any change to the rule after
   measurement starts is a new rule with its own commit, reviewed by M2 before it is run.
2. M2: `--policy original|ranked|random`. `ranked` calls `rank_candidates` once on the candidate
   list, reorders the search, catches `ExtractError` as above, and passes the cache to the ledger.
3. M3: measures `ranked` against `original` at the same endpoint: offline on the POC's stored scan
   tables (ADR-014 evidence item 5), then live (item 4).

## Interface 6 — budget ledger (W24, ADR-014 §1–§3; M2 produces, M3 consumes)

*Proposed by M2 on 2026-11-20. Agreed by M1, M2 and M3 on 2026-11-20 (team WhatsApp group,
recorded by M2; confirmed by approving the PR that adds this section). Built against [ADR-014](../03-Design/decisions/ADR-014-budget-ledger-and-ranked-search.md),
accepted 2026-11-13. Not built yet. `--policy` and ranking are W25 (Interface 5), not this section.*

**Input.** `diagnose()` and `run_steps()` gain `budget: Optional[Budget] = None`; the CLI gains
`--budget-invocations N` and `--budget-seconds S`.

```python
Budget(
    limit_invocations: Optional[int],   # None = unlimited, still counted
    limit_seconds: Optional[float],     # None = unlimited, still timed
)
```

**Cost.** One `run_ordered(order)` costs `len(order)` test-method invocations (frozen definition D7).
Every JVM run goes through one wrapper, so no search code counts by hand. The seven phases are the
record's step labels: `reproduce`, `shuffle`, `alone`, `search`, `minimise`, `deletion`, `verify`.

**The rules the runner (M2) follows.**

| # | Rule |
| --- | --- |
| B1 | `reserve = 3 × n`: `n` for the alone check plus `2 × n` for one polluter's sequence check `[p, victim]` |
| B2 | **Start check.** With an invocation limit, the limit must be at least `reserve + len(start) + 2`, where `start` is the starting order up to the victim (one run of it, plus one candidate pair). Otherwise `DiagnoseInputError` naming that minimum for this `n`; nothing runs |
| B3 | **Exploration** (`reproduce`, `shuffle`, `search`, `minimise`) may spend only `limit − reserve`. A run that would cross that line is **not started** |
| B4 | **Verification** (`alone`, `deletion`, `verify`) may spend up to the full limit. The alone check always runs in full: B2 and B3 guarantee its `n` invocations |
| B5 | **Before the deletion checks**, the runner holds back `n × (k + 1)` invocations for the final sequence check of the `k` kept tests. A deletion check (all `m` runs) starts only if it fits in what is left above that hold-back; otherwise it, and every later check, is `NOT_RUN` with `runs = None`. No check is ever cut part-way |
| B6 | **The final sequence check** runs `min(n, remaining // len(sequence))` times. Fewer than `n` is possible only when B5's hold-back could not be paid in full; `sequence_tally.n` then shows the real count. If not even one run fits (only when `k + 1 > 2 × n`), the status is `BUDGET_EXHAUSTED`, as for a cut in `minimise` |
| B7 | **Seconds.** A run is not started once `limit_seconds` has passed — **for exploration only**. A JVM run's length is unknown until it ends, so verification is bounded by invocations, and the reserve stays whole. `wall_seconds` can therefore exceed `limit_seconds`; the report shows both |
| B8 | A refused run writes one record line `{"type": "budget-stop", "phase", "would_cost", "spent"}` and no `run` line. So `spent` per phase equals the sum of `len(order)` over that phase's `run` lines, and `launches` equals the number of `run` lines (ADR-014 §1, "Proof"; checked by W23) |

**New status `BUDGET_EXHAUSTED`.** It is set when exploration stopped (B3 or B7) before a polluter set
was found: during `reproduce` or `shuffle` with no failing order yet, during `search`, or during
`minimise` (ddmin's partial set is not reported as a result). The alone check still runs first
(B4), and if the victim fails alone the status is `VICTIM_FAILS_ALONE` instead, because that result is
complete. For `BUDGET_EXHAUSTED`: `polluters = []`, `sequence` = the starting (or reproducing) order,
`sequence_tally` = what the `reproduce` runs saw, as for `NOT_REPRODUCED`, `deletion_checks = []`.

**New field on `DiagnosisRuns`.**

```python
budget: BudgetAccount

BudgetAccount(
    limit_invocations: Optional[int],
    limit_seconds: Optional[float],
    reserve_invocations: int,        # 3 × n, reported even when there is no limit
    spent: Dict[str, int],           # all seven phases, 0 when unused
    launches: int,                   # JVM runs started
    wall_seconds: float,             # from the first run to the last
    analysis_seconds: Optional[float],  # None in W24; W25 adds ranking time (Interface 5 cache)
    policy: str,                     # "original" in W24; W25 adds "ranked", "random"
    exhausted: bool,                 # True when any run was refused (B3, B5, B6 or B7)
    exhausted_phase: Optional[str],  # the phase of the first refused run
    candidates_total: int,           # tests before the victim in the order searched
    candidates_tried: int,           # [candidate, victim] pairs actually run in `search`
)
```

**What the report assembly (M3) does with it.**

- **`UNRESOLVED(BUDGET_EXHAUSTED)`:** status `BUDGET_EXHAUSTED` → `decide(budget_exhausted=True)`
  (ADR-010 row 3, unchanged). The rationale names `candidates_tried` of `candidates_total` and the
  phase, and suggests a larger `--budget-invocations`.
- **`CANDIDATE [BUDGET_EXHAUSTED]`:** status `POLLUTER_FOUND` with `exhausted = True` adds
  `BUDGET_EXHAUSTED` to `candidate_reasons`, next to the deletion reason Interface 4 already gives
  for `NOT_RUN`. So a verdict that verification could not finish is **never `VERIFIED`** (ADR-014 §2).
  This starts emitting the candidate reason that `report-schema.md` lists as "reserved".
- **The report gains `budget`**, the account above in ADR-014 §3's shape, with `candidates` as
  `{"total", "tried"}` and `exhausted_phase` added. This is a schema bump that M3 proposes in
  [report-schema.md](report-schema.md).
- Without a limit nothing changes for F1–F4 and N1–N4: same verdicts, with `budget.exhausted = false`.

**Points ADR-014 leaves open, decided here** (part of what this section's approval agrees to):

1. **"Sequence check first" is a priority, not an order in time.** Interface 4 runs the deletion checks
   before the final sequence check, because a dropped test changes the sequence. B5's hold-back keeps
   the sequence check paid first, while it still runs last.
2. **A seconds limit stops exploration only** (B7): it cannot be checked before a run starts.
3. **A cut in `minimise` is `BUDGET_EXHAUSTED`.** ddmin's partial set has had no repeated runs.
4. **`VICTIM_FAILS_ALONE` outranks `BUDGET_EXHAUSTED` in the runner.** The alone check is always
   complete, so its answer stands. ADR-010's row order in `decide()` is unchanged.
5. **No check is cut part-way** (B5), so `runs.n < 10` never comes from the budget; it comes only
   from a small `-n`.
6. **`INCONSISTENT` stays `INCONSISTENT` under a limit** (added 2026-11-20, after W24's review; agreed
   with Interface 7). Exploration finished, so it is not `BUDGET_EXHAUSTED`. The full order can cost more
   than the reserve pays for; if not one run of it fits, `sequence_tally` is the one full-order re-check
   already run in `minimise` (it passed), because `eval.outcome` refuses `sequence.n == 0`.

**Who does what, in order.**

1. M2: ADR-014's scripted tests first (fake runner): a limit just above the reserve stops the search
   and the alone check ran `n` times; a limit below B2's minimum is refused with that minimum; the
   recount (B8). Then B5/B6 with two kept tests, and a seconds limit. Then the runner, the record line
   and the CLI flags.
2. M3, in parallel: the schema field, the two report rules above, and the rationale, tested with a
   `FakeBudgetAccount` under `eval/tests/` that has exactly these fields.
3. Together, once both are merged: ADR-014 evidence items 1–3 on the fixture. A real F2 run with a
   limit just above B2's minimum, and one with no limit. Results recorded as run, not predicted.
4. M1: reproduces item 2 (a budget too small to finish gives `UNRESOLVED(BUDGET_EXHAUSTED)` with an
   account) on their own machine.

## Interface 7 — search policy (W25, ADR-014 §4–§6; M2 produces, M3 consumes and measures)

*Proposed by M2 on 2026-11-20. Agreed by M1, M2 and M3 on 2026-11-20 (team WhatsApp group,
recorded by M2; confirmed by approving the PR that adds this section), together with Interface 6
point 6. Built against [ADR-014](../03-Design/decisions/ADR-014-budget-ledger-and-ranked-search.md)
and Interface 5 (M1's `rank_candidates`, merged). Runner half built 2026-11-20 (M2, W25); report half: M3.*

**Input.** `diagnose()` and the CLI gain:

| Option | Values | Default | Meaning |
| --- | --- | --- | --- |
| `--policy` | `original`, `ranked`, `random` | `original` | the order the single-polluter search tries candidates in (ADR-014 §4) |
| `--scope` | `module`, `package` | `module` | `module`: every discovered test (today). `package`: only tests whose class is in the victim's own package (not sub-packages) — the real-case protocol's frozen scope rule. Refused with `--order`, which already fixes the tests |

`random` shuffles the candidates with `random.Random(seed)`, where `seed` is `--seed` (the same value
the shuffled-order search starts from). Five fixed seeds give the protocol's step 8.

**The rules the runner (M2) follows.**

| # | Rule |
| --- | --- |
| P1 | **One candidate order per diagnosis**, chosen after the alone check and before `search`: the tests before the victim in the order searched (the starting order, or the shuffled order that reproduced). Everything else — the budget, `minimise`, deletion checks, the sequence check — is identical for all three policies (ADR-014 §4: the same endpoint) |
| P2 | `original` keeps that order. `random` is a seeded shuffle of it. `ranked` is `rank_candidates(project, victim, candidates, depth, cache)` (Interface 5) — the same set in a new order, never fewer |
| P3 | **Fallback.** If `rank_candidates` raises `ExtractError` (the victim cannot be analysed), the order is `original` and `note` says why. The policy stays `ranked` in the record and the report, so the comparison counts the case honestly |
| P4 | **Deepening (ADR-014 §6), `ranked` only.** Start at depth 2. Rank again one level deeper only while **all** hold: no candidate has an edge at this depth; the victim's or a candidate's analysis at this depth has a `DEPTH_LIMIT` observation (Interface 2, `resource-evidence.md`); depth < 5; and, when there is a seconds limit, the analysis time so far is below `deepen_share × limit_seconds`, with `deepen_share = 0.20`. Without a seconds limit it may go to depth 5. An `ExtractError` at a deeper depth keeps the last ranking that worked |
| P5 | **Cost.** Ranking runs no JVM, so it costs no invocations. Its time is `AnalysisCache.seconds`, reported as `analysis_seconds`, and it is part of `wall_seconds`. A seconds limit therefore stops exploration sooner after a long analysis (B7) |
| P6 | **Record line.** One `{"type": "ranking", "policy", "scope", "seed", "depths", "order", "scores", "note"}` line before the first `search` run (`order` as `Class#method`, `scores` as Interface 5's tuples; `[]` unless `ranked`). M3's measurement reads where the relevant tests sat from it |

**New field on `DiagnosisRuns`**, and two `BudgetAccount` fields now filled (Interface 6):

```python
search: SearchPolicy

SearchPolicy(
    policy: str,                       # "original" | "ranked" | "random"
    scope: str,                        # "module" | "package"
    seed: Optional[int],               # random only
    depths: List[int],                 # depths ranked at, in order, e.g. [2, 3]; [] unless ranked
    deepen_share: float,               # 0.20 (ADR-014 §6: a policy value, recorded)
    candidates_with_evidence: Optional[int],  # candidates with an edge at the last depth; None unless ranked
    note: Optional[str],               # why ranking fell back, else None
)
# BudgetAccount.policy = SearchPolicy.policy; BudgetAccount.analysis_seconds = cache seconds (None unless ranked)
```

**What the report assembly (M3) does with it.**

- The report gains `search_policy` with the fields above (a schema bump M3 proposes in
  [report-schema.md](report-schema.md)). A `note` is also added to `limitations`.
- The verdict never depends on the policy: the same evidence gives the same `decide()` input.
- Wording (claims ledger G3): a higher rank orders the search; it never says what caused a failure.
  `reasons` stay out of the report; they are in the record line.

**Points ADR-014 leaves open, decided here** (part of what this section's approval agrees to):

1. **Ranking happens once**, on the order searched. ddmin and the deletion checks do not re-rank:
   they do not use a candidate order.
2. **Deepening is for `ranked` only and only when no candidate has any edge.** One edge at depth 2
   is enough to order the search; going deeper would only re-sort ties.
3. **The 20% share applies only with a seconds limit.** With an invocation limit only, analysis is
   free in invocations, so the limit is the depth (5).
4. **`random` reuses `--seed`.** One seed makes the whole diagnosis repeatable.
5. **The scope fallback is a re-run, not automatic.** "The whole module if the package yields
   nothing" means: if `--scope package` gives no polluter, the user runs again with `--scope module`.
   An automatic second search would spend the budget twice and blur the same-budget comparison.

**Who does what, in order.**

1. M2: ADR-014's scripted tests first (fake runner, fake ranker): the polluter is candidate 9 of 10 and
   the only one with an edge → `original` tries 9 pairs, `ranked` 1, the same verdict, totals 16
   invocations apart; no candidate has an edge → `ranked` keeps the original order; the fallback; the
   deepening stops (edge found, no `DEPTH_LIMIT`, depth 5, the 20% share); `random` is repeatable; the
   scope filter. Then the runner, the record line and the CLI flags. Then real F1–F4 with
   `--policy ranked`: the same verdicts as `original` (ADR-014's test).
2. M3, in parallel: the `search_policy` schema field and the limitation, tested with a
   `FakeSearchPolicy` with exactly these fields; then the offline comparison (ADR-014 evidence
   item 5) and, once this lands, the live one (item 4).
3. M1: reviews that P2 and P4 use `rank_candidates` and the `DEPTH_LIMIT` kind as Interface 2 and 5
   define them.

## Open integration questions (decide before code is written against them)

| # | Question | Owner to propose | Status |
| --- | --- | --- | --- |
| I1 | Language for the runner: Java harness invoked from Python, or all-Java with a JSON boundary? | M2 | **Answered:** Python runner launching a small Java harness (`FtHarness`, JUnitCore) in one fresh JVM per order — [ADR-003](../03-Design/decisions/ADR-003-order-runner-junitcore-harness.md), agreed by M1, M2, M3 |
| I2 | Does M1's extractor run on the full suite once, or per candidate pair? | M1 | **Answered:** per candidate pair, after the runner has found the polluter(s): `analyse_pair(project, polluter, victim)` once per polluter, starting at depth 2 and deepening only when needed — [ADR-006](../03-Design/decisions/ADR-006-evidence-depth-auto-deepen.md), agreed by M1, M2, M3. Used this way by `runner/cli.py` ([ADR-007](../03-Design/decisions/ADR-007-w10-ddmin-minimisation.md)) and `eval/tools/run_w9_integration.py` |
| I3 | Default `n` for repeated-run verification at Mid (20 suggested by the defence plan) | M2 + M3 | **Answered:** n = 20 (20/20 → Wilson lower bound 0.839, 19/20 → 0.764, both above 0.70) — [ADR-004](../03-Design/decisions/ADR-004-w7-diagnosis-runs.md), agreed by M1, M2, M3 |
| I4 | Where is the single CLI entry point (`flaketrace diagnose …`) and which language? | M2 | **Answered:** Python, `py -m runner diagnose` from the repository root; an installable `flaketrace` command is deferred — [ADR-005](../03-Design/decisions/ADR-005-w9-diagnose-cli.md), agreed by M1, M2, M3 |
