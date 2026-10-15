# Members and ownership

*Ownership follows [[07-Defense/ownership-map]] (the version defended at the proposal). The
post-defence action plan's two-student split is superseded by the three-member split in
[[07-Defense/decisions/three-member-split]].*

> Member 1 (Zoya) and Member 3 (Zarpash) confirmed their rows on 2026-10-09.

| # | Name | Reg. no. | GitHub | Owns | Folder |
| --- | --- | --- | --- | --- | --- |
| 1 | Zoya Ahmad | 23i-0805 | `zoyaahmad428` | Resource evidence and explanation | `evidence/` |
| 2 | Abdul Raffay | 23i-0587 | `abdulraffay-m` | Bounded search and verification · CLI · CI · integration · web UI over the CLI (from Iteration 2, ADR-009) | `runner/`, `.github/`, `ui/` |
| 3 | Zarpash Nasim | 23i-0027 | `ZarpashNasim` | Evaluation infrastructure · fixtures · statistics · gated repair | `eval/`, `fixtures/` |

**Joint:** contracts, architecture, the Mid report, the evidence worksheet, the deck.

## Current work — update this whenever your task changes

| Member | Current task | Branch | State | Blocked by |
| --- | --- | --- | --- | --- |
| 1 | Mid report: chapters 1–2 and 5, own chapter 6 section, worksheet individual section; GenAI disclosures | `main` (all code merged, last PR #51) | Code complete: W8 and ADR-006 (depth 1–5, auto-deepening), used by M2's CLI and M3's integration through `analyse_pair`; ADR-001/002 accepted, I2 answered, panel action A6 complete; report drafts are files, not yet in the template | — |
| 2 | Iteration 2 web UI over the CLI ([[03-Design/specs/2026-10-14-ui-design]], W15) | `m2/ui` | Report submitted; `mid-eval-v1` tagged on `86d8355` (13 Oct); UI built (backend, nine screens, live runs), tests pass; PR not yet opened | ADR-009 review by M1 and M3 |
| 3 | ADR-008 crash-count follow-ups merged (PR #52); closed remaining Mid-Eval loose ends, merged (PR #54: ADR-002 tick, C6/C7 depth wording, B11 baseline rerun, stale register rows); `eval/reports/` now has all 7 real reports (F1–F4, N1–N3, merged, PR #57); report ch. 4 and 7–8 per `08-MidEval/README`'s Form 3 table next | `main` | Phases 0–5 done; real `VERIFIED`/`UNRESOLVED` reports produced and committed for all 7 fixture cases; random-order baseline run for real on F1–F4, not just F1 (see `docs/evidence-m3.md`) | Report chapters need a refresh against current state; worksheet and tag (W12) not started |

## Evidence files per member

| Member | Evidence log | GenAI log |
| --- | --- | --- |
| 1 | `docs/evidence-m1.md` | `docs/genai-log-m1.md` |
| 2 | `docs/evidence-m2.md` | `docs/genai-log-m2.md` |
| 3 | [[evidence-m3]] | [[genai-log-m3]] |

## Integration owner

**Member 2** merges the final Mid Eval PR, creates the `mid-eval-v1` tag, and keeps CI green —
this sits inside the CLI/CI ownership already defended.
