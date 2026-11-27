# Supervisor review of 23 November 2026, and what we do about it

*v1 · 2026-11-27 · written by M2 with Claude ([[genai-log-m2]]) · Status: `PROPOSED` — for M1 and M3
to read before starting work. The supervisor's plan is itself **Proposed**: no meeting has been
held, and no deadline in it is an agreed commitment.*

**Source:** the supervisor's **Proposed Student Action Plan** `R20261123` v1 (project folder
`SupervisorReveiw_2026-11-23/`), the part of his review package meant for students. It reviewed
`main` at `e0db2bb` against `0d66ff3`, the last `main` of 16 November. This note uses that plan
only; the rest of the package is marked as the supervisor's private material and is not quoted
here.

---

## What the plan says

- FlakeTrace now has full phase tallies, repeated deletion checks, budgeted search, replay and real
  fastjson pair-mode comparisons. **The next work is to make the evidence consistently verifiable
  and the presentation accurate.**
- The FT003/FT004/FT010 corrections are to be kept visible as regressions, and the claim described
  as bounded to the stated run rule — not proof for every subset or future stochastic outcome.
- **Tentative FYP-1 Final: 4 December 2026** (not yet announced). Rehearse a **15-minute** group
  presentation with balanced participation.
- The 43% / conditional 68% scope figures are **our** unweighted inventory, not an approved result.
  The 60% gate needs his scope and weights decision first.
- Everything in the plan is **Proposed** until a meeting records decisions.

## His five priorities, and where we stand on 27 November

| # | His priority (his proposed date) | State on `main` `4f1ad39`, 27 Nov | Our work package |
| --- | --- | --- | --- |
| P1 | **FT009: keep recorded evidence verifiable.** At `e0db2bb`, 16 of 24 committed bundles failed the current checker, because `reproduced_by` became required while `schema_version` stayed 2 (24–25 Nov) | **Mostly fixed after his review:** schema v3 with a frozen `report.v2.schema.json` (PR #170); CI checks every committed bundle (PR #172, `eval.tests.test_committed_bundles`); tamper and checksum tests exist. Re-run on 27 Nov: `test_committed_bundles` OK. **Missing:** the version matrix he asked for | **W36** |
| P1b | Keep FT003/004/010 regressions visible; describe the claim as bounded to the stated run rule | Regressions are in CI. Wording to check in report v2 and the deck | W38 |
| P2 | **FT008/FT017: reconcile real-case counts and wording** (25 Nov) | **Not done.** The seven FJ-03 comparison runs adopt **four** distinct polluters, but the protocol and M3's evidence say five; the protocol says "certified polluter" though every endpoint is `CANDIDATE`. The claims ledger is corrected in this change; the protocol and M3's log are M3's to correct | **W37** |
| P3 | **FT011/FT017/FT022: one build, current artefacts** — regenerate architecture and decision figures, fix stale status text, report, poster and deck matched to one named build (27 Nov) | **Not started.** `architecture.md` corrected in this change; no report v2, poster or deck yet | **W38** |
| P4 | **FT018/FT020: practitioner session or documented blocker; handover walkthrough; FT013–FT015 disclosure delivery** (30 Nov) | W32 protocol, case and task ready; **no participant contacted**. FT015's corrected worksheet made but **not delivered** | W32, W29a |
| P5 | **Freeze and rehearse** — named build, matching artefacts, 15-minute rehearsal with balanced participation, labelled backup recording (2 Dec) | PR #177 (web UI for the demo) open, not rehearsed | **W33** |

He also asked, explicitly, that we **not** add broad new algorithms or a compulsory second real
project to this near-term plan.

## Things we discussed that the review does not list

- **Budget on the real case (W39).** All seven FJ-03 comparison runs used an *unconstrained*
  budget. The iteration objective says "under a stated budget". One evening of budgeted pair-mode
  runs closes it (M-2, FT007).
- **Panel actions A4, A5, A6 (W40).** Each needs a short written answer we can show and defend,
  built from evidence that already exists. See [[10-Final1/action-register]] for the completion
  test of each.
- **A10** needs only the supervisor's decision ([[10-Final1/supervisor-agenda]] v3).

## Who does what next

| Member | In order |
| --- | --- |
| **M2** | Ask for the meeting with agenda v3 · merge PR #177 after M1's and M3's review · set up the report v2 skeleton and regenerate the current figures (W38) · W39 budgeted FJ-03 runs · A4 one-pager with M1 (W40) · the W36 replay column · W33 freeze, tag `final1-v1`, rehearsal |
| **M1** | W32 practitioner contact today · W37 interpretation check · W36 solo repeat · W30 poster, W29b table · A6 note · own report chapters |
| **M3** | W37 count and wording fix · W36 matrix · A5 scenario table · deliver the corrected worksheet (FT015) · A6 note · own report chapters · repeat one W39 run |

Details for M1 and M3: [[10-Final1/handover-m1-m3]].

## Decisions only he can record

Carried into [[10-Final1/supervisor-agenda]] v3: committed scope and weights for the 60% gate;
A10; the bounded assurance claim and execution contract; the FT018 substitute if no practitioner
is found; the abstract and template interpretation; confirmed final dates.

## Related

[[10-Final1/iteration-2-plan]] (W36–W40) · [[10-Final1/action-register]] ·
[[10-Final1/feedback-register]] · [[10-Final1/handover-m1-m3]]
