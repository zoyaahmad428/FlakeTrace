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
| 1 | Static-field + system-property extraction for F1/F2 | `m1/depth-adr` | Phases 2–5 done (fixture matches ground truth; fastjson FJ-01/FJ-02 need depth 4/5); ADR-006 proposed; Phase 6 next | ADR-006 needs M2 and M3 agreement |
| 2 | W9 command `py -m runner diagnose` (ADR-005) | `m2/w9-cli` | Built and run on the fixture (F1/F2 `VERIFIED`, N1 `UNRESOLVED`, F3 exit 3); PR #26 in review, CI green on JDK 8; ADR-005/I4 need M1, M3 agreement; W10 next | — |
| 3 | W9 report assembly done for F1/F2/N1/N2 (real end-to-end, `eval/report.py` wired to M1's real `find_edges`/`report_fields`); report ch. 4 and 7–8 per `08-MidEval/README`'s Form 3 table next | `m3/n2-integration` | Phases 0–5 done; real `VERIFIED`/`UNRESOLVED` reports produced for F1, F2, N1, N2 (see `docs/evidence-m3.md`) | Only F3 remains, needs W10 (M2, multi-polluter search/minimisation — not started) |

## Evidence files per member

| Member | Evidence log | GenAI log |
| --- | --- | --- |
| 1 | `docs/evidence-m1.md` *(create on first run)* | `docs/genai-log-m1.md` *(create)* |
| 2 | `docs/evidence-m2.md` | `docs/genai-log-m2.md` |
| 3 | [[evidence-m3]] | [[genai-log-m3]] |

## Integration owner

**Member 2** merges the final Mid Eval PR, creates the `mid-eval-v1` tag, and keeps CI green —
this sits inside the CLI/CI ownership already defended.
