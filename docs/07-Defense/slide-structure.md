# Proposal Defence Slide Structure

*Official 10-slide structure. Slide order should not be changed — the panel expects this
sequence. All required content must be visible on the slide itself, not only in the appendix
or spoken commentary.*

---

## Required slides

| # | Slide | What to show | Our status | Vault source |
| --- | --- | --- | --- | --- |
| 1 | **Title and one-line problem** | Project title, members, supervisor, one-line problem statement | ✅ | [[00-Meta/project-one-pager]] |
| 2 | **Problem and users** | Who has the problem, current workflow, why it matters | ✅ Three named contacts. ⚠ Address the Java gap here, don't wait for it to be found | [[00-Meta/stakeholder-evidence]] |
| 3 | **Existing solutions and prior FYP comparison** | Product/prior-FYP comparison table and the **real gap** | ✅ | [[01-Literature/contemporary-comparison-table]] + [[01-Literature/prior-fyp-comparison]] |
| 4 | **R&D / recent technical work** | Relevant papers/methods/technical sources and **what you learned from them** | ✅ | [[01-Literature/parameter-provenance]] |
| 5 | **Complex computing challenge** | What is technically hard and **why this is not a course project** | ✅ Seven of nine Seoul Accord characteristics | [[00-Meta/project-one-pager]] §CCP |
| 6 | **Proposed solution and contribution** | Architecture idea, main modules, **clear contribution statement** | ✅ | [[03-Design/architecture]], contribution statement in [[00-Meta/project-one-pager]] |
| 7 | **POC-lite / feasibility evidence** | See below — **we exceed the bar, frame it that way** | ✅✅ | [[05-Testing/poc/poc-log]] |
| 8 | **Evaluation plan and risks** | How success will be measured; risks, dependencies, tool/API/GenAI boundary | ✅ | [[05-Testing/evaluation-plan]] + [[00-Meta/risk-register]] |
| 9 | **Work division and iteration plan** | Member-wise responsibilities and milestones | ✅ | [[07-Defense/ownership-map]] + [[00-Meta/roadmap]] |
| 10 | **DEI, Ethics and legal issues** | DEI statement, Ethical and Legal statement | ✅ | [[00-Meta/risk-register]] §Ethics, legal and DEI |

---

## Slide 7 — read this before building it

**The official bar is lower than what our project has.** The requirement is a
*"clickable high-fidelity functional prototype (interface without core functionality behind
the interface), API/data check, baseline run, sample pipeline, or risk experiment shown.
**Full MVP not required.**"*

Our POC is not a clickable mockup or an interface stub — it is an **executed, evidence-backed
experiment**: 8 targets built at pinned SHAs, 4 reproduced in clean containers, 2,606 controlled
orders run, a negative result against pre-registered gates, two harness defects found and
corrected, and a recorded decision.

**Frame the slide as exceeding the requirement, explicitly:**

> "The guide asks for feasibility evidence — a prototype, a baseline run, or a risk experiment.
> We went further: we ran the actual risk experiment end-to-end, with pre-registered success
> gates, on real projects, in clean containers."

**Do not undersell it by treating slide 7 as a checkbox.** This is your strongest slide — see
[[07-Defense/weak-points]] and [[07-Defense/one-minute-answers]] for why leading with the
negative result is the correct move, not a hedge.

**Structure the slide as the story:**
1. The one risky assumption tested — and why that one
2. Pre-registered gates, committed before any experiment ran
3. The result: negative. Zero overlap at depth 1. 0% saving against a 30% gate
4. Why — the mechanism (FJ-02's two-hop path)
5. The two harness defects — 182→0, timezone erasure. **These are the most important part**
6. The decision: NARROW, and the four design changes that followed

Evidence to have on screen, not on the slide itself:
[[05-Testing/poc/poc-log]] §14 checklist.

---

## Slide 9 — work division and iteration plan

Pull directly from [[07-Defense/ownership-map]] (who owns what, individual evidence produced,
the removal test for each member) and [[00-Meta/roadmap]] (phase table with **exit evidence**,
not activities — the panel is trained to prefer "what will exist" over "what we'll be doing").

Include the Gantt chart: `attachments/GanttChart.jpeg`.

**Do not just list tasks per person.** Show the **removal test** reasoning for Member 3 in
particular (Q88 is a near-certain question) — the POC's two invalidating defects were harness
problems, not algorithm problems, which is the strongest available argument that evaluation
infrastructure is a full pillar and not support work.

---

## Slide 10 — DEI, ethics and legal

Pull directly from [[00-Meta/risk-register]] §Ethics, legal and DEI. Three ethics issues named
(executing third-party code, handling potentially sensitive source/output, responsible
claim-making), the legal position (all subjects open source, fetched by script, never
redistributed), and the DEI statement (self-hosted, no GPU/cloud/paid API required, widens who
can diagnose these failures).

Keep this slide **short and factual** — it is a required disclosure, not a place to argue.

---

## Consistency audit before slides are finalised

| Check | Why | Status |
| --- | --- | --- |
| **CDR wording matches** across slide deck, proposal document and Rev 2 | *"A panel that finds two of your own documents contradicting each other will pursue it much harder than one that finds a gap you named yourself"* | ❌ [[07-Defense/weak-points]] §5 |
| **Victim/brittle vs reproduction count** reconciled | Do not put both numbers on the same slide until fixed | ❌ [[07-Defense/weak-points]] §4 |
| Every number on a slide appears in [[05-Testing/poc/raw-numbers]] | If it is not there, do not say it | |
| Every claim on a slide has a ledger row | [[07-Defense/claims-ledger]] | |
| No slide says "minimum", "automatically fixing", "calibrated", or "dataset is ready" | The four phrasing traps | |
| Slide 7 frames the POC as **exceeding** the feasibility-evidence bar, not meeting a checkbox | See above | |

## Open items the panel is entitled to check

Say **open**, say **when it closes**, say **who approves**. Do not manufacture an answer for any
of these:

- [ ] At least two named stakeholder contacts with documented current-workflow baseline and
      measured or estimated time cost — ✅ **three have this**, ⚠ **none in our target ecosystem**
- [ ] Contemporary comparison explicitly including iFixFlakies, RankF and Takuan, **dated** — ✅
- [ ] Three or more clean-container public reproductions with exact commits and saved evidence,
      **demonstrable on the day rather than described** — ✅ four, ⚠ all one project
- [ ] POC decision record with pre-registered rules and honest failure analysis — ✅
- [ ] Frozen committed resource, build-system and language boundaries with optional features
      removed from the promise — ✅
- [ ] Licence status recorded per subject project and per research artifact — ✅
- [ ] Baseline, metric, statistical and acceptance definitions approved **before** the held-out
      evaluation — ✅ frozen
- [ ] Named acceptance participants or a recorded substitute plan — ⚠ **one named (SH1), need a
      substitute plan for the rest**
