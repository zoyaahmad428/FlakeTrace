# Members and ownership

*Ownership follows [[07-Defense/ownership-map]] (the version defended at the proposal). The
post-defence action plan's two-student split is superseded by the three-member split in
[[07-Defense/decisions/three-member-split]].*

> ⚠ **Confirm at the 2026-10-09 meeting:** the member numbers for Zoya and Zarpash are
> inferred from commit history (Zarpash's commits are tagged `[M3]`). Correct this table if
> it is wrong, and fill in the registration numbers.

| # | Name | Reg. no. | GitHub | Owns | Folder |
| --- | --- | --- | --- | --- | --- |
| 1 | Zoya Ahmad *(confirm)* | *fill* | `zoyaahmad428` | Resource evidence and explanation | `evidence/` |
| 2 | Abdul Raffay | 23i-0587 | `abdulraffay-m` | Bounded search and verification · CLI · CI · integration | `runner/`, `.github/` |
| 3 | Zarpash Nasim *(confirm)* | *fill* | *fill* (commits as `ZarpashNasim`) | Evaluation infrastructure · fixtures · statistics · gated repair | `eval/`, `fixtures/` |

**Joint:** contracts, architecture, the Mid report, the evidence worksheet, the deck.

## Current work — update this whenever your task changes

| Member | Current task | Branch | State | Blocked by |
| --- | --- | --- | --- | --- |
| 1 | Static-field + system-property extraction for F1/F2 | `m1/static-extraction` | Not started | — |
| 2 | `OrderRunner` implementation + CI | `m2/order-runner` | CI done in restructure PR; runner not started | — |
| 3 | Mid report chapters 1–5; wire baseline to runner when ready | `m3/…` | Phases 0–5 done (see `docs/evidence-m3.md`) | M2 runner for real numbers |

## Evidence files per member

| Member | Evidence log | GenAI log |
| --- | --- | --- |
| 1 | `docs/evidence-m1.md` *(create on first run)* | `docs/genai-log-m1.md` *(create)* |
| 2 | `docs/evidence-m2.md` | `docs/genai-log-m2.md` |
| 3 | [[evidence-m3]] | [[genai-log-m3]] |

## Integration owner

**Member 2** merges the final Mid Eval PR, creates the `mid-eval-v1` tag, and keeps CI green —
this sits inside the CLI/CI ownership already defended.
