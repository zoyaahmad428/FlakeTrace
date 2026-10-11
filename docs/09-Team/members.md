# Members and ownership

*Ownership follows [[07-Defense/ownership-map]] (the version defended at the proposal). The
post-defence action plan's two-student split is superseded by the three-member split in
[[07-Defense/decisions/three-member-split]].*

> Member 1 (Zoya) and Member 3 (Zarpash) confirmed their rows on 2026-10-09.

| # | Name | Reg. no. | GitHub | Owns | Folder |
| --- | --- | --- | --- | --- | --- |
| 1 | Zoya Ahmad | 23i-0805 | `zoyaahmad428` | Resource evidence and explanation | `evidence/` |
| 2 | Abdul Raffay | 23i-0587 | `abdulraffay-m` | Bounded search and verification · CLI · CI · integration | `runner/`, `.github/` |
| 3 | Zarpash Nasim | 23i-0027 | `ZarpashNasim` | Evaluation infrastructure · fixtures · statistics · gated repair | `eval/`, `fixtures/` |

**Joint:** contracts, architecture, the Mid report, the evidence worksheet, the deck.

## Current work — update this whenever your task changes

| Member | Current task | Branch | State | Blocked by |
| --- | --- | --- | --- | --- |
| 1 | Static-field + system-property extraction for F1/F2 | `m1/adr006-deepen` | W8 complete: Phases 2–6 and ADR-006 (depth 1–5, pair-mode auto-deepening; fastjson FJ-01/FJ-02 at `depth_used` 4/5); report chapters next | M2 and M3 switch their calls to `analyse_pair` |
| 2 | Mid packaging: report ch. 5–6, demo rehearsal, tag `mid-eval-v1` (W11–W13) | `main` | All runner work merged (W6, W7, W9, W10, W14/ADR-008 in PR #49); docs synced | Tag waits for every Mid PR to merge |
| 3 | ADR-008 crash-count follow-ups merged (PR #52); closed remaining Mid-Eval loose ends (ADR-002 tick, C6/C7 depth wording, B11 baseline rerun, stale register rows); report ch. 4 and 7–8 per `08-MidEval/README`'s Form 3 table next | `main` (pending: baseline/wording-fix branch not yet pushed) | Phases 0–5 done; real `VERIFIED`/`UNRESOLVED` reports produced for all 7 fixture cases (F1–F4, N1–N3); random-order baseline now run for real on F1–F4, not just F1 (see `docs/evidence-m3.md`) | Report chapters need a refresh against current state; worksheet and tag (W12) not started |

## Evidence files per member

| Member | Evidence log | GenAI log |
| --- | --- | --- |
| 1 | `docs/evidence-m1.md` *(create on first run)* | `docs/genai-log-m1.md` *(create)* |
| 2 | `docs/evidence-m2.md` | `docs/genai-log-m2.md` |
| 3 | [[evidence-m3]] | [[genai-log-m3]] |

## Integration owner

**Member 2** merges the final Mid Eval PR, creates the `mid-eval-v1` tag, and keeps CI green —
this sits inside the CLI/CI ownership already defended.
