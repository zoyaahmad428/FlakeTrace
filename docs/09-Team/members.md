# Members and ownership

*Ownership follows [[07-Defense/ownership-map]] (the version defended at the proposal). The
post-defence action plan's two-student split is superseded by the three-member split in
[[07-Defense/decisions/three-member-split]].*

> ⚠ **Confirm at the 2026-10-09 meeting:** the member number for Zoya is inferred from commit
> history. Correct this table if it is wrong, and fill in her registration number. Member 3
> (Zarpash) confirmed 2026-10-09.

| # | Name | Reg. no. | GitHub | Owns | Folder |
| --- | --- | --- | --- | --- | --- |
| 1 | Zoya Ahmad *(confirm)* | *fill* | `zoyaahmad428` | Resource evidence and explanation | `evidence/` |
| 2 | Abdul Raffay | 23i-0587 | `abdulraffay-m` | Bounded search and verification · CLI · CI · integration | `runner/`, `.github/` |
| 3 | Zarpash Nasim | 23i-0027 | `ZarpashNasim` | Evaluation infrastructure · fixtures · statistics · gated repair | `eval/`, `fixtures/` |

**Joint:** contracts, architecture, the Mid report, the evidence worksheet, the deck.

## Current work — update this whenever your task changes

| Member | Current task | Branch | State | Blocked by |
| --- | --- | --- | --- | --- |
| 1 | Static-field + system-property extraction for F1/F2 | `m1/static-extraction` | Phase 2 done (depth 1, lifecycle attribution); Phase 3 (depth 2) next | Contract PR #8 review (M2, M3) |
| 2 | `OrderRunner` implementation + CI | `m2/order-runner` | W6: harness + F1 proof done; failure paths and CI job next | — |
| 3 | Report ch. 4 (requirements) and ch. 7–8 (testing plan, tool/risk disclosure) per `08-MidEval/README`'s Form 3 table; wire baseline to runner when ready | `m3/…` | Phases 0–5 done; real fixture repetitions + idoft dataset cases added (see `docs/evidence-m3.md`) | M2 runner for real numbers |

## Evidence files per member

| Member | Evidence log | GenAI log |
| --- | --- | --- |
| 1 | `docs/evidence-m1.md` *(create on first run)* | `docs/genai-log-m1.md` *(create)* |
| 2 | `docs/evidence-m2.md` | `docs/genai-log-m2.md` |
| 3 | [[evidence-m3]] | [[genai-log-m3]] |

## Integration owner

**Member 2** merges the final Mid Eval PR, creates the `mid-eval-v1` tag, and keeps CI green —
this sits inside the CLI/CI ownership already defended.
