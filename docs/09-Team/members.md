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

*Iteration 2 (2026-11-13). **Agreed** by M1, M2 and M3 in person on 2026-11-13
([[06-Meetings/2026-11-13-post-mid-planning]]); M2 recorded it, M1 and M3 confirm by approving
PR #101.*

| Member | Owns in Iteration 2 | Verifies for others | Branch | State |
| --- | --- | --- | --- | --- |
| 1 | W21 static-overlap wording, all edges, two controls · W25 candidate ranking · W30 poster · W32 Java practitioner check · worksheet table (FT016) | W18, W19, W20 · the lifecycle control (W22) · **the bundle reproduction on her own machine (W23)** · W27 | `m1/w16-evidence-wording` | W16 (`evidence/` wording) built 2026-11-18, awaiting M3 · W21 part 1 (`resource_edges`) built 2026-11-18 |
| 2 | W18 outcome tallies in the runner · W19 step 1: `RunTally` and the classifier in `eval/baseline.py`, for M3 (M3 reviews) · W20 deletion runs · W22 lifecycle, reset boundary · W24 budget ledger · W25 policy integration · W23 replay · W31 supervisor meeting and action register · tag and report compile | W21 · W26a · poster claims | `m2/w22-record-env` | W17 done 2026-11-13. W16 and W19 step 1 merged (PR #103), awaiting M3. W18 built 2026-11-14, awaiting M1. W22 jobs 1–4 (record environment, spike, class-grouped execution, disposable copy) built on `m2/w22-record-env`, awaiting M1's control run. Next: the next unblocked package |
| 3 | W17 lead: agree the verdict contract *(done 2026-11-13)* · W19 decision, schema v2, report, fixture N4 (step 1 written by M2 while M3 has no laptop; M3 reviews it) · W20 acceptance rule · W23 bundle and recount · W26 real case · W27 container · GenAI register (FT015) | W16 consistency · W24 · W28 status against code · worksheet pages | — | W17 done 2026-11-13. W19 step 1 (`RunTally`/`classify`, PR #103) reviewed, matches ADR-010 exactly. **W19 built 2026-11-18**: `eval/outcome.py`/`eval/report.py` rewritten for the 13-row decision table and schema v2 (`candidate_reasons`, `resource_edges`, `assurance`); fixture N4 added (ADR-010 test T5, FT003) and confirmed through the real `diagnose` command; F1–F4/N1–N3 verdicts unchanged (test T6). 119/119 `eval/tests` and 63/63 `runner/tests/test_cli` passing. Two small mechanical fixes made in M2's `runner/cli.py`/`runner/tests/test_cli.py` (field rename + one verdict-change assertion) that would otherwise have broken on schema v2 — Member 3 (not M2) authorized each as a non-design-decision fix to keep CI green; flagged in `docs/evidence-m3.md` for M2's actual review. Awaiting M1's independent reproduction (FT003's acceptance requires it) and M2's `ui/web/` field-name update (ADR-010 Consequences). **W16 verified 2026-11-18**: M2's merged part (`9a05788`) checked against ADR-010 §2/ADR-011 §5 — matches exactly; M3's own `eval/` part found already clean (written fresh in W19), one wording inconsistency fixed against the CLI's exact phrase; M1's part (`m1/w16-evidence-wording`) still on an open branch, re-check once merged. Next: W20 (acceptance rule, deletion checks) once M2's runs land |

**Backups (supervisor's proposal, FT020):** Member 1 backs up reproduction and integration;
Member 3 backs up the report and schema side. A verifier reproduces — they do not do the owner's
work.

**At the Mid (closed):** all code for Iteration 1 merged; tag `mid-eval-v1` on `86d8355`; the web
UI over the CLI merged afterwards (PR #99, 15 October). Detail in the git history and in each
member's evidence log.

## Evidence files per member

| Member | Evidence log | GenAI log |
| --- | --- | --- |
| 1 | `docs/evidence-m1.md` | `docs/genai-log-m1.md` |
| 2 | `docs/evidence-m2.md` | `docs/genai-log-m2.md` |
| 3 | [[evidence-m3]] | [[genai-log-m3]] |

## Integration owner

**Member 2** keeps CI green and creates the evaluation tags: `mid-eval-v1` (done, never moved)
and `final1-v1` for the FYP-1 Final. This sits inside the CLI/CI ownership already defended.
