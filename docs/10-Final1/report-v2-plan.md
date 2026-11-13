# Report v2.0 and worksheet corrections

*v1 · 2026-11-13 · Status: checklist. Writing rules stay in `mid-eval-report/CLAUDE.md`; chapter
ownership there is unchanged.*

The handbook's Table 1a asks for **"FYP Report (version 2.0) (with corrections), adding subsequent
iterations"** at the Final. The Mid report is version 1.0 and stays reachable at tag `mid-eval-v1`.
Version 2.0 is the same document, corrected and extended — not a new one.

---

## 1. The two official comments

| Comment | What we know | Action |
| --- | --- | --- |
| "Restore the missing abstract" | `chapters/04_abstract.tex` holds a 188-word abstract; the submitted PDF lists it on page vii. The supervisor's own audit calls it "about 190 words". So we do not know what is missing | **Ask** ([[10-Final1/supervisor-agenda]] item 7). Meanwhile: check the abstract is on its own page directly after the title page, as the handbook says, and shorten it to 50–125 words |
| "Align the report properly with the template" | Not specified. The supervisor's audit found the chapter content maps to the template, and separated inherited template defects from ours (FT019) | **Ask** which parts. Meanwhile: the items in section 3 |

**Shortening the abstract.** Handbook: "three to five sentences… 50–125 words… purpose, findings
and conclusions, without commenting on or evaluating the work". Joint file, Member 2 assembles,
Member 1 checks every number against a measured result. It must describe the system as it is at
the Final — written **last**.

## 2. Corrections from the Mid review

| Issue | Where | Correction | Owner |
| --- | --- | --- | --- |
| FT013 | Signature page, physical page 10 | Each member signs their own line. Genuine signatures in the compiled PDF | Each; M2 compiles |
| FT003 | 4.5–4.6, 6.6, Table 4.4 | What `VERIFIED` asserts: the four claims of ADR-010. Remove "passes alone" where it was not measured that way; describe the defect found and its fix | M3, M2 |
| FT004 | Table 4.4, 6.6.2 | "Every verified sequence passes 1-minimality" → the deletion-evidence wording of ADR-011 | M3, M2 |
| FT005 | 2.6, 4.x, 6.6.1 | Static evidence is potential overlap. Sequence assurance and resource evidence described separately | M1 |
| FT006, FT021 | 6.6.2, 8.10 | The execution contract and reset boundary of ADR-012, word for word | M2 |
| FT010 | 4.x, 6.x | Every diagnosis now ends in a typed report — once it does | M3 |
| FT012 | Chapter 3, 9.x, the roadmap figure | One schedule. No May–June essential integration | M2 |
| FT017 | 6.9–6.10, Tables 4.2 and 4.5, member table | One authoritative implemented / planned table at the submission commit. The tag sentence corrected. Old statements kept only with their date | Chapter owners; M3 checks |
| FT008 | 7.8, 9.2, conclusion | What was run on a real project, exactly; targets called targets | M3 |
| FT015 | Table 8.3 | GenAI levels consistent with the worksheet and register | M3 |

## 3. What Form 5 scores, and what is new for it

| Form 5 criterion | Max | New content needed in v2.0 | Owner |
| --- | --- | --- | --- |
| Report matches demonstrated system | 5 | Every feature described is in the tag `final1-v1`; planned work is marked planned | M2 |
| Updated requirements and traceability | 15 | **Traceability matrix for every committed requirement: requirement → design → test → status.** Requirements reworded where the Mid found them stronger than the checks | M3 |
| Updated design artefacts with rationale | 20 | Architecture and behaviour diagrams redrawn for Iteration 2: tallies, deletion checks, budget ledger, ranked search, bundle and recount. ADR-010 to ADR-015 summarised as "what changed since the Mid and why" | M2, M1 |
| Implementation details and reproducibility | 20 | Setup and run instructions that another person followed (the peer-reproduction record). The container command. Bundle format | Module owners |
| Testing evidence and early validation | 20 | The regression tests for FT003, FT004, FT010 with their failing-then-passing runs. The controls. The real case, with inputs, expected and actual results, **and what failed** | M3 |
| R&D continuation and FYP-2 evaluation plan | 10 | Baselines, benchmark, metrics and the held-out rule for FYP-2, from [[05-Testing/evaluation-plan]] and [[05-Testing/real-case-protocol]] | M3, M1 |
| Tool / API / GenAI disclosure, risks, limitations | 10 | Form 13 sheet; the reconciled register; the limitations of section 2 | Each; M3 compiles |

**Also from the handbook's Final-1 gate** (its stage table, which it marks as proposed): a draft
test, deployment, rollback and handover plan with defect severity definitions; the timeline
revised against actual progress; every scope change recorded. One short section each is enough.

**Document control.** The handbook asks every document to carry version, date, author and status.
Add a control block to the report's front matter: v1.0 (Mid, 13 October), v2.0 (Final).

## 4. Chapter mapping

The handbook's suggested contents and where ours covers it. Nothing needs renumbering; the
supervisor's audit accepted the mapping.

| Handbook | Ours |
| --- | --- |
| Introduction · Project vision | Chapter 1 |
| Research on existing ideas | Chapter 2 |
| Software requirement specification | Chapter 4, Appendix B |
| Iteration plan | Chapter 3 |
| Iteration 1 | Chapters 5–6 as submitted |
| **Iteration 2** | **New in v2.0:** what was corrected and built since the Mid |
| Implementation details | Chapter 6 module sections |
| User manual | **New in v2.0:** the commands, the bundle, the container — short |
| References, appendices | As now |

## 5. The worksheet

| Issue | Correction | Owner |
| --- | --- | --- |
| FT013 | Supply the **editable** filled worksheet, not only a PDF | M2 |
| FT014 | Nine declarations, the dated confirmation — each member, personally, after the facts are corrected. Twelve group confirmations and three signatures | Each |
| FT015 | Section 10's register and each individual section agree on every GenAI level | M3; each checks own rows |
| FT016 | Page 8: recover the full rationale column; landscape if needed; check **every** exported page | M1; M3 checks |
| FT022 | Section 2: statuses as in [[10-Final1/action-register]], not "Complete" | M2 |
| Audit rows marked Partial | Dated milestones (block 7); owner column on tests (block 20); stale status (block 19) | Owners of those blocks |

**Do not tick a declaration that is not true yet.** An unticked box is a missing confirmation; a
false one is an integrity problem.

## 6. Form 13 — external tool, API and GenAI disclosure sheet

New to us in the 3rd Edition. A student-submitted sheet, updated before every evaluation: *"not a
prompt journal; it is a contribution boundary document."*

| Column | From |
| --- | --- |
| Tool / model | [[08-MidEval/genai-register]] |
| Used in which part | The same |
| Category: Support / Core-assist / Core-replacement | The handbook does not map its L1–L4 levels onto these three. **Our proposed mapping, to confirm with the supervisor:** L1–L2 → Support · L3 → Core-assist · L4 → Core-replacement. We declare no Core-replacement — and each member must be able to show why |
| Student contribution beyond the tool | Per-member logs |
| Validation and risk control | Tests, mutation checks, hand cross-checks, the errors caught |

Signed and dated by all three.

## 7. Before compiling

- [ ] Every number traces to a bundle, a test log or a committed result file
- [ ] No retired phrase remains (ADR-010 §2, ADR-011 §5, ADR-012 §1)
- [ ] Planned and built are never mixed in one sentence
- [ ] The abstract matches the measured claims and the word limit
- [ ] The compiled PDF is read page by page for clipped tables, by someone who did not compile it
- [ ] Signed
