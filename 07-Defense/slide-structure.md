# Proposal Defence Slide Structure

*The presentation should be concise and **present evidence before the panel begins
questioning**. Slide order may be adjusted, but all of this information must be visible.*

---

## Required slides

| # | Slide | Required content | Our status |
| --- | --- | --- | --- |
| 1 | **Title and one-line problem** | Project title, members, supervisor, **declared stream**, one-sentence problem statement | ✅ [[00-Meta/project-one-pager]] |
| 2 | **Stakeholders and current workflow** | Who faces the problem, how it is currently handled, why the failure matters, **the one relevant SDG** | ✅ Three named contacts. ⚠ Address the Java gap here rather than waiting |
| 3 | **Existing solutions and prior FYPs** | Structural comparison and **evidence-based gap** | ✅ [[01-Literature/contemporary-comparison-table]] + [[01-Literature/prior-fyp-comparison]] |
| 4 | **Research and technical basis** | Relevant current work, alternatives studied, **decisions influenced** | ✅ [[01-Literature/parameter-provenance]] is exactly this |
| 5 | **CCP justification** | Applicable Seoul Accord characteristics, central trade-offs, uncertainty, **why routine development is insufficient** | ✅ Seven of nine |
| 6 | **Proposed contribution and solution** | Contribution statement, high-level architecture, major components, boundaries, **intended deployment target** | ✅ [[03-Design/architecture]] |
| 7 | **POC / technical spike (mandatory)** | The risk tested, **evidence obtained — shown, not described** — what was learned or disproved, the resulting decision | ⚠ Evidence checklist ready; **reconcile the victim/brittle wording first** |
| 8 | **Evaluation plan** | Baseline, data or scenarios, metrics, success criteria, **at least one measurable NFR**, and the failure cases that matter most | ✅ [[05-Testing/evaluation-plan]] |

> **A proposal that cannot demonstrate feasibility evidence should not normally be approved.**
> Slide 7 is not optional and *"POC completed"* on a slide is not a POC.

---

## The single most important presentation decision

**Lead with the negative POC result. Do not bury it.**

The FAST guide states a POC that disproved its assumption and caused the group to revise its
approach is usually **more valuable** than one that confirmed it.

- A panel that **discovers it under questioning** treats it as **concealment**
- A panel that is **told up front** treats it as **engineering judgement**

*(This is Dossier decision 3 — our intention is to lead with it, awaiting the supervisor's view.)*

## Slide 7 — how to build it

Structure the POC slide as the story, not the outcome:

1. **The one risky assumption we tested** — and why that one
2. **Pre-registered gates** — written and committed before any experiment ran
3. **The result: negative.** Zero overlap at depth 1. 0% saving against a 30% gate
4. **Why** — the mechanism: state moves through callees, not test bodies. FJ-02's two-hop path
5. **The two harness defects** — 182→0, and the timezone erasure. *These are the most important
   part*
6. **The decision: NARROW**, and the four design changes that followed

**Not on the slide, but on screen and ready:** the evidence checklist in
[[05-Testing/poc/poc-log]] §14.

## Consistency audit before slides are finalised

| Check | Why | Status |
| --- | --- | --- |
| **CDR wording matches** across slide deck, proposal document and Rev 2 | *"A panel that finds two of your own documents contradicting each other will pursue it much harder than one that finds a gap you named yourself"* | ❌ [[07-Defense/weak-points]] §5 |
| **Victim/brittle vs reproduction count** reconciled | Do not put both numbers on the same slide until fixed | ❌ [[07-Defense/weak-points]] §4 |
| Every number on a slide appears in [[05-Testing/poc/raw-numbers]] | If it is not there, do not say it | |
| Every claim on a slide has a ledger row | [[07-Defense/claims-ledger]] | |
| No slide says "minimum", "automatically fixing", "calibrated", or "dataset is ready" | The four phrasing traps | |

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
