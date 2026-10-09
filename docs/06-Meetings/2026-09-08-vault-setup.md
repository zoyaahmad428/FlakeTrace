# Meeting — 2026-09-08 — Vault setup and defence preparation start

**Present:** M1
**Type:** working session

---

## What happened

Set up the Obsidian vault + GitHub repository for shared context, and populated it from the
existing project documents (Dossier, Technical Design, Literature Review, Panel Question Bank,
Stream B Guide Rev 2, Alignment Worksheet, Prerequisite Glossary, three stakeholder
questionnaires, architecture diagram, Gantt chart).

## Findings that changed our understanding

| Finding | Consequence |
| --- | --- |
| **All three stakeholder interviews are complete** — Inspirovix, Trillet AI, Learnsignal | Closes the gap the Dossier listed as our weakest. A2–A8 in the claims ledger move to `SETTLED` |
| **None of the three uses Java, Maven, JUnit or Surefire** | New `OPEN` claim A9. Recorded as [[07-Defense/weak-points]] §1 with the answer drafted. **Closure action: one Java/Maven practitioner before defence** |
| **Two stakeholders independently said a guess is worse than a refusal** | Q28 (abstention) now has *user* evidence, not only architectural justification. Materially strengthens the contribution argument |
| **POC write-up has an internal inconsistency** — 6 victims / 2 brittle at isolation vs 4 reproduced all fastjson, with 2 fastjson targets classified brittle | New `OPEN` claim C13. **Highest-priority documentation fix. Do not put both numbers on the same slide until reconciled** |
| **CDR wording may differ across slide deck / proposal / Rev 2** | New `OPEN` claim E6. Audit required before slides are built |

## Decisions made

| Decision | Rationale | Owner |
| --- | --- | --- |
| Vault structure: 00-Meta … 07-Defense, claims-ledger as the spine | Everything defensible needs a traceable source; the ledger makes that operational rather than aspirational | Joint |
| Every claim carries a `STATUS` — SETTLED / OPEN / ASSUMPTION / POLICY / FROZEN | The question bank is explicit that a named open item is forgiven and a fabricated closure is not | Joint |
| `POLICY` rows (18/20, 0.70 Wilson bound, 25% target, budget split) are defended **as policy**, never as published findings | Blurring the distinction is punished; naming it is respected | M2 |

## Actions

| Action | Owner | Priority |
| --- | --- | --- |
| Reconcile victim/brittle vs reproduction count wording | M3 | **Do first — cheap and dangerous if left** |
| Audit CDR wording across slide deck, proposal doc, Rev 2 | Joint | **Do first** |
| Ask supervisor for a Java/Maven practitioner introduction (Dossier decision 5) | Joint | Highest value |
| Confirm three-member departmental approval (Dossier decision 1) | Joint | Blocking |
| Confirm naming consent with SH2 and SH3 | Joint | Before defence |
| Depth sweep — depths 1/2/3/unbounded × 4 cases, rank **and** overlap-set size | M1 | 1 |
| Per-case cause classification for the three non-moving cases | M1 | 2 |
| Oracle ceiling + alternative rankings, offline | M3 | 3 |
| One out-of-domain subject, hard-capped | M3 | 4 |
| Instrumentation non-perturbation check | M2 | 5 |
| Run rehearsal pass 1 (solo, aloud, no notes) | All | Before pass 2 |

## Open questions carried forward

- Which member fronts each section on the day?
- Do we lead the slide deck with the negative POC result? *(Dossier decision 3 — our intention is
  yes; awaiting supervisor's view)*
- Priority order for remaining time — is single-project evidence more urgent than the depth
  sweep? *(Dossier decision 4)*
