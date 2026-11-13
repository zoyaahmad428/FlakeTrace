# 2026-11-13 — after the Mid: feedback received, Iteration 2 planned

**Present:** M2 *(planning session with Claude)*; then M1, M2 and M3 in person for the decisions
below. M1 and M3 had no laptop access, so M2 recorded their agreement; they confirm it by
approving PR #101.
**Type:** planning, then **team decision** (W17).

---

## What arrived

- The FYP Committee's official Mid feedback (two comments) — [[10-Final1/mid-eval-outcome]]
- The supervisor's detailed review: 22 findings, FT001–FT022 — [[10-Final1/feedback-register]]
- The FYP Handbook, 3rd Edition — what the Final requires is in [[10-Final1/README]]

## What was done in this session

| Done | Where |
| --- | --- |
| Read all of the above against `main` `7cf453d` | — |
| Reproduced the two certification defects with a scratch script | [[evidence-m2]] |
| Drafted six design proposals | ADR-010 to ADR-015 |
| Drafted the plan to the Final, the registers, the scope inventory, the real-case protocol | `10-Final1/`, [[05-Testing/real-case-protocol]] |
| Updated the notes that described the pre-Mid state | README, status, roadmap, architecture, certificate contract, requirements, claims ledger, risk register, members |

No code was changed. No contract file was changed.

## Proposals waiting for a decision

| # | Proposal | Needs | Decided 2026-11-13 |
| --- | --- | --- | --- |
| 1 | What `VERIFIED` asserts; four outcome categories; a report for every status — ADR-010 | M1, M2, M3 + supervisor | **Agreed as written** by M1, M2, M3, with Q1–Q3 below. Supervisor still to be asked |
| 2 | Repeated deletion checks — ADR-011 | M1, M2, M3 | **Agreed as written** |
| 3 | Class-grouped execution, the reset boundary, disposable copy, pinned container — ADR-012 | M1, M2, M3 | **Agreed as written** (section 2 after its spike) |
| 4 | Evidence bundle, recount, replay — ADR-013 | M1, M2, M3 | **Agreed as written** |
| 5 | Budget ledger, verification reserve, ranked search — ADR-014 | M1, M2, M3 | **Agreed as written** |
| 6 | Resource intervention spike — ADR-015 | M1, M2, M3 + supervisor | **Agreed as a spike only**; go / no-go written up afterwards. Supervisor still to be asked |
| 7 | FJ-03 as the first real case — [[05-Testing/real-case-protocol]] | M3 confirms | Not decided |
| 8 | Work packages W16–W34, their owners and verifiers — [[10-Final1/iteration-2-plan]] | M1, M2, M3 | **Agreed as written** |
| 9 | Member 3 takes the reproducibility container (W27) | M2, M3 | **Agreed:** M3 owns W27 |
| 10 | The unweighted scope count — [[10-Final1/scope-inventory]] | Supervisor | Not decided (supervisor) |

## Decisions — 2026-11-13, in person (W17)

M1 (Zoya), M2 (Raffay) and M3 (Zarpash) agreed:

1. **ADR-010 to ADR-014 as written.**
2. **ADR-010's open questions:**
   - **Q1 — option A.** A sequence that replays reliably and passes alone but has no static edge is
     `CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]`, not `UNRESOLVED`.
   - **Q2 — no retries for now.** A crashed or timed-out run is not re-run; it counts as `INFRA`.
   - **Q3 — keep `VERIFIED`**, always displayed with its qualifier, until the supervisor decides.
3. **ADR-015 as a spike only**, with a go / no-go decision afterwards.
4. **The work packages, owners and verifiers in [[10-Final1/iteration-2-plan]]**, including
   **M3 owning W27** (the reproducibility container).
5. **W19 step 1 is written by M2.** While M3 has no laptop, M2 writes `RunTally` and the outcome
   classifier in `eval/baseline.py` (M3's file); M3 reviews it when back. M3 agreed to this.

Q1 and Q3 change the meaning of `VERIFIED`, so they also go to the supervisor
([[10-Final1/supervisor-agenda]] item 2). If the supervisor decides differently, ADR-010 is
reopened.

## To settle at the first team meeting

- [ ] Poster and Final dates, from the committee's notice
- [x] ADR-010 and ADR-011: agree, or change and agree (this is W17 and it blocks the rest)
- [x] Owners and verifiers in the plan
- [ ] Who asks the supervisor for a meeting, and when
- [ ] Why nothing was committed between 15 October and 13 November — one honest line for the
      variance table
- [ ] Whether the review the supervisor proposed for 23 October took place

## Read and agreed

| Member | Read | Agree with the plan as a starting point | Date | Comment |
| --- | --- | --- | --- | --- |
| M1 | ☑ | ☑ | 2026-11-13 | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
| M2 | ☑ | ☑ | 2026-11-13 | Wrote the plan; agreed in person with M1 and M3 |
| M3 | ☑ | ☑ | 2026-11-13 | Agreed in person 2026-11-13, recorded by M2; confirmed by approving PR #101 |
