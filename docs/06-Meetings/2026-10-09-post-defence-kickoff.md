# Meeting — 2026-10-09 — post-defence kickoff for Mid Eval

**Present:** M1 / M2 / M3
**Type:** team sync

---

## Context

Proposal approved with minor modifications. Mid Evaluation between 12 and 16 October; report
and worksheet due 48 h before. Code repo had M3's evaluation work but no runner, evidence
extractor or CI; the vault was a separate repo, last updated before the defence.

## Decisions made

| Decision | Rationale | Owner | Promoted to |
| --- | --- | --- | --- |
| One repository; the vault becomes `docs/` | Supervisor grades one repo's history, CI and evidence; code and docs change together; every agent reads one `CLAUDE.md` | All | [[09-Team/working-agreement]] |
| PR + one teammate approval, CI must pass, no pushes to `main` | Industry practice the GCR asks for; reviews are ownership evidence | All | `CONTRIBUTING.md` |
| Iteration 1 evidence is static-only, no instrumentation *(proposed — confirm)* | Answers panel Q1/Q2 truthfully for the demo; runtime agent is Iteration 2 | M1, M2 | [[03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation]] |
| Three-member ownership from the defence stands | Post-defence plan's two-student split predates the three-member approval | All | [[09-Team/members]] |

## To settle in this meeting

- [ ] Exact Mid Eval date/time → [[08-MidEval/README]] and [[08-MidEval/iteration-plan]]
- [ ] Confirm member numbers, registration numbers, M3's GitHub username → [[09-Team/members]]
- [ ] Agree ADR-001 (tick the table)
- [ ] Report chapter owners → [[08-MidEval/README]]
- [ ] Open integration questions I1–I4 → [[contracts/interfaces]]
- [ ] Who sets branch protection on GitHub (repo admin = Zoya)

## Actions

| Action | Owner | Due |
| --- | --- | --- |
| Review and approve restructure PR | M1, M3 | today |
| Set branch protection on `main`; archive `FlakeTrace-Vault` | Zoya (admin) / M2 | after merge |
| Start `OrderRunner` (W6) | M2 | |
| Start static extraction (W8) | M1 | |
| Start report chapters | M3 | |
