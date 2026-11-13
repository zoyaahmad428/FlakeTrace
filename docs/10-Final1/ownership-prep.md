# Ownership preparation — each member, without AI

*v1 · 2026-11-13 · Status: preparation sheet. The questions are the supervisor's own, from the
Mid meeting briefing and the contribution review.*

## Why this matters more than any feature

- The Mid review found substantive work from all three of us and still wrote, for each:
  *"Insufficient evidence for a reliable overall contribution judgment."* What is missing is
  **seeing each of us explain and change our own work**.
- At the Final a **panel** asks. The handbook: *"The panel may ask any member to show any part of
  the codebase."*
- Form 11 turns a weak answer into a personal multiplier on the group mark: 1.00 strong, 0.85
  minor gaps, 0.70 limited explanation, 0.50 cannot explain important claimed work.
- Heavy AI assistance is declared (L3 for the core modules) and is acceptable **only** with
  "strong disclosure and evidence beyond tool use". The evidence is you.

**How to use this file:** answer aloud to a teammate, with the laptop closed. Then do the
practical task with AI switched off. Note in your GenAI log what you could not answer — the
handbook treats that as growth, not as failure.

---

## Member 1 — Zoya Ahmad · resource evidence

| Question | A good answer includes |
| --- | --- |
| Why does F2 need depth two? | The property is read inside `FeatureFlags.isTurboEnabled`, a project helper. Depth one scans only the test and its lifecycle methods; depth two follows the call. Disabling auto-deepening makes the difference visible |
| P writes a field and restores it, or shares an irrelevant field with V. What does your edge prove? | A *possible* write/read overlap. Not the value left behind, not the path actually executed, not the cause. Controlled reruns establish the sequence; only an intervention or a runtime observation could establish the resource |
| Does your evidence currently guide the search? | No. The CLI calls `analyse_pair` only after the polluters are found; `find_polluter`'s `priority` is unused. Ranking is planned (ADR-014) |

**Practical task.** Find F2's write and read bytecode offsets. Then add an extractor test for a
write-then-restore polluter or an irrelevant overlap: predict the output before running it, and
explain why the report's wording has to be qualified.

**Also be ready for:** why `javap` and not a bytecode library · one thing static analysis cannot
see · the one false edge measured on fastjson and why it appears.

## Member 2 — Abdul Raffay · runner, search, integration

| Question | A good answer includes |
| --- | --- |
| Walk through F3. What does `ddmin` guarantee? | Reproduce the full order, check the victim alone, try each predecessor once, re-run the full order, then subsets and complements, then repeat the kept order. The result is 1-minimal **for the single trials it observed**, never the global minimum. One cached trial per subset cannot certify a deletion when outcomes vary |
| The victim alone always throws B; after P it always throws A. What does the Mid build report, and why? | `VERIFIED`. Only alone failures matching A are counted; `run_steps` drops the any-failure count on the search path, so the decision sees zero. The fix keeps all four outcome categories and refuses to call that "passes alone" (ADR-010) |
| What do a fresh JVM and the source hashes establish, and what do they leave open? | JVM static state restarts for every order, and the project's files outside `target/` and `.git/` are byte-identical before and after. Files and external state are not reset; a write-and-restore during the run is not seen; tests run with the user's permissions. `@BeforeClass` runs per method, unlike normal execution |

**Practical task.** Write a failing regression for the different-signature-alone case, and name
the fields and the decision rule that must change.

**Also be ready for:** why one JVM per order · why class-first shuffles · what the exit codes mean
· explain the CI workflow line by line · what a `RunTally` is and why two overlapping counts were
not enough.

## Member 3 — Zarpash Nasim · evaluation, decision, fixtures

| Question | A good answer includes |
| --- | --- |
| Why does 18 of 20 fail the 0.70 policy? What does the interval mean? | Wilson 95% lower bounds: about 0.699 for 18/20, 0.764 for 19/20, 0.839 for 20/20. The bound is about how often the replay fails under fixed conditions — not about whether the diagnosis is right. 0.70 is our policy, not a published number |
| Can `decide()` certify deletion minimality or a causal resource from its inputs? | Not at the Mid: it has no deletion input, and a Boolean "edge exists" is static overlap. A schema-valid report is structurally valid; it cannot supply evidence that was never collected |
| What comparison would establish the claimed 25% cost improvement? | The same pinned cases, the same failure signature, harness and definition of success; every test-method invocation counted, search and verification both; yield and paired uncertainty reported. Random runs until the first failure are a different endpoint. Development and held-out projects kept apart |

**Practical task.** Explain which rule wins when source integrity fails but the replay evidence is
strong. Then add a decision test for a mixed alone outcome, or for the status that has no report,
and update the schema and the report contract to match.

**Also be ready for:** why Wilson and not the normal approximation · how each fixture's ground
truth was fixed before its first run · reconcile the L2 and L3 entries, artefact by artefact.

---

## The handover exercise — FT020

Integration knowledge sits with Member 2. Before the Final:

| Who | Does | Records |
| --- | --- | --- |
| **Member 1** | From the written instructions alone, on her own machine: runs the end-to-end command on a fixture case, verifies and replays its bundle, and points to where the runner hands over to the extractor and the extractor to the report | Result, differences and every unclear step, in [[evidence-m1]] |
| **Member 3** | Explains the runner → report mapping and makes one small change on the report side without Member 2 | The change and its test, in [[evidence-m3]] |
| **Member 2** | Writes the instructions and **reviews** the two attempts — does not do them | The fixes made to the instructions |

If an instruction was unclear, the instruction is wrong. Fix it; do not explain it in person.

## Three questions each — keep them current

The worksheet asked each member for three technical questions they cannot yet answer
confidently. They may be revisited at the Final. Each member re-reads their three, and writes one
line on what they have learned since.
