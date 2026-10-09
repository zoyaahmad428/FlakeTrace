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
| 1 | Static-field + system-property extraction for F1/F2 | `m1/resource-edges` | Phases 2–4 done (lifecycle attribution, depth 1–3, polluter→victim edges); Phase 5 (validation) next | — |
| 2 | W7 diagnosis runs (victim-alone, polluter search, repeats, integrity, record) | `m2/w7-diagnosis-runs` | W7 complete (PR #11 in review; CI green on JDK 8); W9 (report assembly) next | — |
| 3 | W9 report assembly done for F1/N1 (real end-to-end); report ch. 4 and 7–8 per `08-MidEval/README`'s Form 3 table next | `m3/w9-report-assembly` | Phases 0–5 done; `eval/report.py` wired to the real `runner.diagnose()` + `evidence.extract()`, real `VERIFIED`/`UNRESOLVED` reports produced for F1/N1 (see `docs/evidence-m3.md`) | F2/F3 need W8's polluter→victim edges (Phase 4, M1 — depth is done) and W10 (M2) |

## Evidence files per member

| Member | Evidence log | GenAI log |
| --- | --- | --- |
| 1 | `docs/evidence-m1.md` *(create on first run)* | `docs/genai-log-m1.md` *(create)* |
| 2 | `docs/evidence-m2.md` | `docs/genai-log-m2.md` |
| 3 | [[evidence-m3]] | [[genai-log-m3]] |

## Integration owner

**Member 2** merges the final Mid Eval PR, creates the `mid-eval-v1` tag, and keeps CI green —
this sits inside the CLI/CI ownership already defended.
