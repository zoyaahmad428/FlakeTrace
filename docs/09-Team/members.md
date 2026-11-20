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
| 2 | W18 outcome tallies in the runner · W19 step 1: `RunTally` and the classifier in `eval/baseline.py`, for M3 (M3 reviews) · W20 deletion runs · W22 lifecycle, reset boundary · W24 budget ledger · W25 policy integration · W23 replay · W31 supervisor meeting and action register · tag and report compile | W21 · W26a · poster claims | `m3/w19-verdict-contract-v2` (PR #106, with M3's permission) | W16, W18, W19 step 1 and W22 jobs 1–4 merged (PRs #102–#104). 2026-11-19: on M3's PR #106 — merged `main`, report shows M1's every edge, deletion answer (ADR-011 §2), web UI on schema v2, Mid-report check reads tag `mid-eval-v1`; CI line for M1's FT005 controls (PR #107). Awaiting M1: W18, W22 control run. Next: W20 deletion runs |
| 3 | W17 lead: agree the verdict contract *(done 2026-11-13)* · W19 decision, schema v2, report, fixture N4 (step 1 written by M2 while M3 has no laptop; M3 reviews it) · W20 acceptance rule · W23 bundle and recount · W26 real case · W27 container · GenAI register (FT015) | W16 consistency · W24 · W28 status against code · worksheet pages | — | W17 done 2026-11-13. W19 step 1 (`RunTally`/`classify`, PR #103) reviewed, matches ADR-010 exactly. **W19 built 2026-11-18**: `eval/outcome.py`/`eval/report.py` rewritten for the 13-row decision table and schema v2 (`candidate_reasons`, `resource_edges`, `assurance`); fixture N4 added (ADR-010 test T5, FT003) and confirmed through the real `diagnose` command; F1–F4/N1–N3 verdicts unchanged (test T6). 119/119 `eval/tests` and 63/63 `runner/tests/test_cli` passing. Two small mechanical fixes made in M2's `runner/cli.py`/`runner/tests/test_cli.py` (field rename + one verdict-change assertion) that would otherwise have broken on schema v2 — Member 3 (not M2) authorized each as a non-design-decision fix to keep CI green; flagged in `docs/evidence-m3.md` for M2's actual review. Awaiting M1's independent reproduction (FT003's acceptance requires it) and M2's `ui/web/` field-name update (ADR-010 Consequences). **W16 verified 2026-11-18**: M2's merged part (`9a05788`) checked against ADR-010 §2/ADR-011 §5 — matches exactly; M3's own `eval/` part found already clean (written fresh in W19), one wording inconsistency fixed against the CLI's exact phrase; M1's part (`m1/w16-evidence-wording`) still on an open branch, re-check once merged. **W26a done 2026-11-19**: fastjson FJ-03 fetched and built for real (real JDK 8, no Docker), premise confirmed 10/10 both ways. Found a real `runner/discovery.py` gap (custom Surefire includes not read, blocks the real CLI on this case) and that random shuffle search can't find this bug on a dense real suite (other tests undo the pollution) — both genuine findings, flagged for M2/the team ([[00-Meta/risk-register]]). Protocol frozen for steps 1-5; steps 6-9 blocked on the discovery.py fix. **A1 fail-safe fix done 2026-11-19**: `deletion_status=None` no longer satisfies S3 in `eval/outcome.py` (reversed my own W19-flagged design choice, on explicit instruction, test-first). **Superseded/reconciled 2026-11-20**: M2 independently built the same fail-safe on `eval/report.py` (PR #106, with M3's permission) via a more complete, ADR-011-vocabulary-correct mechanism (`DELETION_INCOMPLETE`, not a placeholder); merge conflict resolved by keeping M2's `report.py` implementation and my own `outcome.py` guard together (defense in depth) — see `docs/evidence-m3.md`. F1/F2/F4 stay `VERIFIED`, F3 (two required polluters) honestly reports `CANDIDATE [DELETION_EVIDENCE_INCOMPLETE]` instead of `VERIFIED`. `fixtures/od-fixture/ground_truth.json` deliberately left as `VERIFIED` (the W20 target). **Corrected course on the Mid report, 2026-11-20**: M2's other PR #106 commit made the Mid report's generated table a closed record, checked by CI against tag `mid-eval-v1`'s frozen reports, never live data — found by actually reproducing that CI step locally (also caught a real bug it would have hit: `json_to_tex.py`'s `rate()` needs to accept both schema v1 `successes` and v2 `matched`, since the tag is permanently v1; fixed). This meant my own chapter edits (today's F3/N2 "corrections" *and* yesterday's N4-driven order-length/seed edits) were wrong, not just premature — reverted `chapter8_testing.tex`, `chapter4_requirements.tex`, `appendix_test_cases.tex` and `chapter6_module_m3.tex` to byte-identical with the tag. The actual code and every Iteration-2 doc still correctly say F3 is `CANDIDATE` today; only the frozen Mid report must not. Flagged M1's/M2's now-stale "F3 ... VERIFIED" chapter claims and claims-ledger row E14 as no longer an issue for the *frozen* Mid report specifically (they match the tag correctly) — the real remaining flag is just claims-ledger row E14 itself being a live, ongoing claims document, not tied to the tag. Next: W20 (the real multi-test deletion-acceptance rule that would let F3 reach `VERIFIED` for real) once M2's runs land, or help unblock W26a's discovery.py gap |

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
