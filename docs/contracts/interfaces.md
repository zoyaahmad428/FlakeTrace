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

## Open integration questions (decide before code is written against them)

| # | Question | Owner to propose | Status |
| --- | --- | --- | --- |
| I1 | Language for the runner: Java harness invoked from Python, or all-Java with a JSON boundary? | M2 | **Answered:** Python runner launching a small Java harness (`FtHarness`, JUnitCore) in one fresh JVM per order — [ADR-003](../03-Design/decisions/ADR-003-order-runner-junitcore-harness.md), agreed by M1, M2, M3 |
| I2 | Does M1's extractor run on the full suite once, or per candidate pair? | M1 | **Answered:** per candidate pair, after the runner has found the polluter(s): `analyse_pair(project, polluter, victim)` once per polluter, starting at depth 2 and deepening only when needed — [ADR-006](../03-Design/decisions/ADR-006-evidence-depth-auto-deepen.md), agreed by M1, M2, M3. Used this way by `runner/cli.py` ([ADR-007](../03-Design/decisions/ADR-007-w10-ddmin-minimisation.md)) and `eval/tools/run_w9_integration.py` |
| I3 | Default `n` for repeated-run verification at Mid (20 suggested by the defence plan) | M2 + M3 | **Answered:** n = 20 (20/20 → Wilson lower bound 0.839, 19/20 → 0.764, both above 0.70) — [ADR-004](../03-Design/decisions/ADR-004-w7-diagnosis-runs.md), agreed by M1, M2, M3 |
| I4 | Where is the single CLI entry point (`flaketrace diagnose …`) and which language? | M2 | **Answered:** Python, `py -m runner diagnose` from the repository root; an installable `flaketrace` command is deferred — [ADR-005](../03-Design/decisions/ADR-005-w9-diagnose-cli.md), agreed by M1, M2, M3 |
