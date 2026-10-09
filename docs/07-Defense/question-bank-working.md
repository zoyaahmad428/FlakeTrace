# Panel Question Bank — Working Copy

*The full 109-question pack lives in the source document. This is the **working** version:
questions triaged by how ready we actually are, with the answer compressed to what you must
say and links to the backing.*

**Answer discipline (applies to every question below):**
> Lead with the direct answer in one sentence. Give the evidence in the second. Give the
> limitation in the third. **Stop.** Panels punish the fourth sentence far more often than
> they punish the missing one.

**Readiness key:** ✅ ready · ⚠️ shaky, rehearse · ❌ open gap, say so honestly

---

## The three questions asked in almost every defence

Time these to under a minute each. They set the tone for everything that follows.

### ✅ The one-minute pitch (Q102)
> Java teams run automated test suites in CI. A test passes alone and fails after other tests
> because an earlier test left shared state behind. Developers can detect the instability but
> not diagnose it — they rerun, reorder and comment tests out by hand, and most often
> quarantine the test, which removes coverage permanently.
>
> Commercial tools detect and quarantine well; research tools separately minimise orders,
> rank relevant tests or explain state differences. None returns a bounded, verified,
> replayable diagnosis with an evidence path and an honest refusal.
>
> FlakeTrace takes a pinned project, a target test and an execution budget, runs controlled
> order experiments, and returns a verified certificate — the interfering test, the shared
> resource, the bytecode locations, a replay command and a reliability interval — or a typed
> unresolved result.

### ✅ Contribution statement (Q29) — verbatim
See [[00-Meta/project-one-pager]]. Memorise it word for word. Never shorten it to "we find
minimal polluter sequences and explain shared state" — that claim is taken three times over.

### ⚠️ The POC result (Q35)
> Negative, at that scope. Zero write-read overlap between candidates and the victim at
> one-hop resource scope, across every reproduced case. The overlap score was empty for every
> candidate, so the ranked strategy produced an ordering byte-identical to one-by-one
> confirmation, and the execution saving was exactly zero against a gate of thirty percent.
> Two of five pre-registered gates were missed outright.

**Do not say** "mixed" or "inconclusive." It was a clean, interpretable negative, and its
interpretability is what makes it useful.

---

## Section 1 — Problem and stakeholders

| Q | Readiness | Note |
| --- | --- | --- |
| Q1 problem in one sentence, no technology | ✅ | [[00-Meta/project-one-pager]] |
| Q2 name your stakeholders | ✅ **now** | Mahad Sheikh (CEO, Inspirovix), eng lead at Trillet AI, full-stack eng at Learnsignal. **Confirm naming consent for SH2/SH3 before the day** |
| Q3 current workflow and cost | ✅ | 15 min minor → full working day major; weekly minor, monthly root-cause. [[00-Meta/stakeholder-evidence]] |
| Q4 why is rerunning not enough | ✅ | Rerunning tells you the outcome changed, not which predecessor, through which state, or whether the sequence is smallest |
| Q5 is the problem big enough | ✅ | Minority by count, disproportionate by investigation time — retry works for timing flakiness, not OD |
| Q6 why self-host rather than buy a dashboard | ✅ | SH3: sending source out is "out of the question". Say "their published documentation does not describe it" — **never** "they cannot" |
| Q7 SDG | ✅ | SDG 9, claimed narrowly. Not claiming social impact |
| Q8 if stakeholders lose interest | ✅ | Evaluation is against public baselines on a public benchmark. SH1 already agreed to review results |
| **— Java gap** | ❌ | **Not in the original pack. They will find it.** [[07-Defense/weak-points]] §1 |

## Section 2 — Stream and scope

| Q | Readiness | Note |
| --- | --- | --- |
| Q9 why Stream B not A | ✅ | Began from a workflow failure, not a paper. RankF is a baseline, not a starting point. Deliverable is an operable product, not a metric |
| Q10 product boundary | ✅ | [[02-Requirements/scope-boundary]] |
| Q11 why exclude DB/network | ✅ | Three families completely > seven badly. Unsupported ≠ silent: opaque events feed abstention + coverage report |
| Q12 JUnit 5 conditional in 2026 | ✅ | Real limitation, stated. JUnit 4 first because Surefire discovery, boundary attribution and the public corpora are all well understood there |

## Section 3 — Prior art ⚠️ *the section most likely to fail the proposal*

> **Absolute instruction:** do not defend "we uniquely find a minimal polluter sequence and
> explain shared state." Three research systems already cover parts of that.

| Q | Readiness | Note |
| --- | --- | --- |
| Q13 iFixFlakies already minimises | ✅ | We add four things: active budget allocation, bounded resource provenance, statistical verification, typed abstention. **The measurable claim is a cost claim** |
| Q14 RankF already ranks | ✅ | "It is not interesting on its own — which is exactly why RankF is a mandatory baseline." Our signal differs *in kind*: theirs static suite properties, ours execution-collected resource overlap. **We committed to reporting the answer even if it is no** |
| Q15 Takuan already explains | ✅ | "No, and we do not claim it is." Difference is correlation vs **intervention** |
| Q16 iDFlakies | ✅ | Input source, not competitor |
| Q17 so you combined four systems | ✅ | We compete with all four. The guide does not require invention — system/architecture contribution is valid |
| Q18 what if a paper last month did this | ✅ | Add as baseline, restate the delta, rescope before scope freeze if nothing remains. **Do not get defensive — this tests composure** |
| Q19 what do they do better than you | ✅ | iFixFlakies generates patches; RankF validated at far larger scale; Takuan covers state we call unsupported |
| **Q20 which have you actually run** | ❌ | **None yet.** Say so. Integration FYP-I early; measurement is a Final-1 exit condition. **Do not say "studied" if you mean "read the paper"** |

## Section 4 — Prior FAST projects

| Q | Readiness | Note |
| --- | --- | --- |
| Q21 how is this different | ✅ | F22-032-D-ETesting (generates tests), F22-033-D-WebSPLAT (reuse across variants), S25-049-D-TestML (broad, feature-oriented). We are deliberately narrow: one budgeted diagnosis problem |
| Q22 how do you know no FYP did this internally | ✅ | "We do not, and we do not claim it." A title-and-summary repository cannot prove it |
| Q23 systematic or titles | ✅ | 989 records swept for testing/flakiness/test-order/CI/debugging terms; full record read for every hit |

## Section 5 — CCP

| Q | Readiness | Note |
| --- | --- | --- |
| Q24 state your CCP | ✅ | [[00-Meta/project-one-pager]]. "That is one problem, not several. Every clause competes with every other one" |
| Q25 Seoul Accord characteristics | ✅ | **Seven of nine.** Do not claim diverse stakeholders strongly — most over-claimed characteristic |
| Q26 is complexity just many technologies | ✅ | "Remove every technology choice and the problem remains." No framework decides which test order to run next |
| Q27 concrete number for the trade-off | ✅ | Budget 500 invocations, 2-test order at 2 invocations/replay → verification reserves 40, search gets 460. Raise the reserve → fewer candidates; lower it → interval widens past Verified |
| Q28 is abstention just not solving it | ✅ **strengthened** | Now has *user* evidence: SH2 "a tool that guesses is worse than useless"; SH1 "a clearly stated unknown is more useful" |

## Section 6 — Contribution

| Q | Readiness | Note |
| --- | --- | --- |
| Q29 verbatim | ✅ | Memorise |
| Q30 which contribution type | ✅ | System/architecture primary, method secondary. **Not claiming algorithmic novelty** |
| Q31 the sentence that survives everything failing | ✅ | "An OD failure can be turned into an artefact another engineer can replay on a clean machine and audit, or an honest refusal — and we measured what that costs relative to the current best research tools" |
| Q32 if you do not beat RankF | ✅ | "No, but it changes the claim, and we have pre-registered how." Thresholds frozen before the held-out run |

## Section 7 — The POC ⚠️ *hardest and strongest*

| Q | Readiness | Note |
| --- | --- | --- |
| Q33 what risky assumption | ✅ | The one that, if false, invalidates the whole ranking argument |
| Q34 setup | ✅ | [[05-Testing/poc/poc-log]] §3–4 |
| Q35 result | ⚠️ | Rehearse. Clean negative, no softening |
| Q36 so your core idea does not work | ✅ | "At one-hop scope — a much more specific statement." Mechanism: state moves through helpers, factories, `<clinit>`, library entry points |
| Q37 one case is anecdote | ✅ | "We do not present it as a result and we would not accept it either." It justifies *one* design decision |
| Q38 what decision | ✅ | NARROW. [[07-Defense/decisions/poc-scope-narrow]] |
| Q39 the two harness defects | ✅ **lead with these** | 182→0; timezone erasure |
| Q40 how do you know there is not a third | ✅ | Four-way instrumented/uninstrumented control, now committed |
| Q41 why 8 cases → fewer | ✅ | Execution capacity, recorded with its reason. "Three cases support a decision about direction and support no claim about magnitude" |
| **Q42 show me the evidence** | ⚠️ | **Checklist in [[05-Testing/poc/poc-log]] §14. Have it on screen, not on a slide** |
| Q43 what would have made you pivot | ✅ | Both conditions pre-registered. "Narrow was correct under our own rules rather than the comfortable one" |

## Section 8 — Technical depth *(every member must be able to answer these regardless of ownership)*

| Q | Readiness | Owner | Note |
| --- | --- | --- | --- |
| Q44 1-minimal vs global minimum | ✅ | all | Removing any single test stops reproduction. Global = exponential. Multi-polluter means a 3-set can be 1-minimal while a different 2-set also reproduces |
| Q45 failure-equivalence rule | ✅ | M2 | Exception type + redacted message + top in-project frames. **Exit code is not a signature** |
| Q46 delta debugging assumes monotonicity | ✅ | M2 | Three safeguards: repeated execution per deletion check; preserve multi-test candidates; wording *and* metric are both 1-minimal |
| Q47 what the interval means | ✅ | all | 95% Wilson on **replay reliability under our harness**. **Not** a probability the diagnosis is correct |
| Q48 why not "calibrated confidence" | ✅ | M2 | Calibration is a specific claim requiring a held-out study. We have not done one |
| Q49 when does it abstain | ✅ | all | Four typed reasons: unsupported resource, budget exhausted, unstable build, inconsistent outcomes |
| Q50 how do you prove instrumentation did not create the failure | ✅ | M1 | Four-way control + median/p95 overhead. **We have direct evidence the risk is real — our own timezone override** |
| Q51 unit of cost | ✅ | M2 | Test-method invocations — hardware-independent, so comparison with iFixFlakies/RankF is not confounded |
| Q52 budget split | ✅ | M2 | Reserve set aside *before* search; planner may not draw it down |
| Q53 how does the planner choose | ✅ | M2 | Expected information gain per unit estimated cost |
| Q54 three families + identity normalisation | ✅ | M1 | Class+field+descriptor through the class loader; property key; canonicalised paths |
| Q55 attribution to a specific test | ✅ | M1 | Test boundaries from the runner. Events outside any boundary recorded as such — **this is exactly the 182-defect class** |
| Q56 static or dynamic | ✅ | M1 | Static for candidate generation (over-approximation filtered by confirmation), dynamic for certificate evidence (precision required) |
| Q57 analysis depth | ✅ | M1 | Depth 1 = test body. Each level ↑ recall, ↑ analysis time and over-approximation. Configurable because the POC showed it is decisive |
| Q58 multiple interacting polluters | ✅ | M2 | Preserve multi-test candidates; report the *sequence*. State the limit: budget may exhaust → unresolved |
| Q59 nondeterministic **and** order-dependent | ✅ | M2 | Detected, not mislabelled. 12/20 replay → interval fails Verified → Candidate or Unresolved |
| Q60 Candidate vs Verified vs Unresolved | ✅ | all | "We found the order but cannot explain it" is genuinely useful and genuinely different from "we found nothing" |
| Q61 certificate contents | ✅ | all | [[03-Design/certificate-contract]] |
| Q62 why classify victim vs brittle | ✅ | all | Different fixes, observable distinction. Conflicting evidence → label mixed, never force |

## Section 9 — Dataset

| Q | Readiness | Note |
| --- | --- | --- |
| Q63 is your dataset ready | ✅ | **"No, and we mark it amber deliberately."** Do not say ready because it exists |
| Q64 frozen manifest contents | ✅ | Version zero exists with the two POC projects; larger subset frozen before Mid-1 |
| Q65 how will you split | ✅ | **By project, never randomly by test.** Two tests in a module share fields, helpers and often the polluter |
| Q66 what stops leakage | ✅ | A fix commit may not be an input where it is also the oracle. Exclusions published |
| Q67 what if projects will not build | ✅ | Ladder pre-registered. Fixtures are **not** a substitute for real projects and we say so |
| Q68 licences | ✅ | Fetch-by-script at pinned SHA — avoids redistribution entirely. MIT + Apache-2.0 recorded |

## Section 10 — Evaluation

| Q | Readiness | Note |
| --- | --- | --- |
| Q69 research questions | ✅ | RQ1–RQ6 committed, RQ7–RQ8 gated |
| Q70 all your baselines | ✅ | Random (seeded), OBO, iFixFlakies minimiser, RankFO/RankFL, Takuan on overlapping subset, oracle ceiling |
| Q71 success criteria numbers | ✅ | ≥25% lower median invocations; ≤5pp success-at-budget loss; 18/20 + Wilson ≥0.70. **Overhead has no number, deliberately** |
| Q72 measurable NFR | ✅ | Median/p95 instrumentation overhead + clean-machine deployment |
| Q73 statistics, chosen before or after | ✅ | **Before.** Project-wise paired comparisons, bootstrap intervals, effect size |
| Q74 testing vs evaluation vs acceptance | ✅ | Three different things — know the distinction cold |
| Q75 acceptance tasks | ✅ | Five tasks. SH1 already agreed to review |
| Q76 what result means failure | ✅ | A **wrong Verified certificate** is the most serious. Then high false-confidence on controls |

## Section 11 — Architecture and security

| Q | Readiness | Note |
| --- | --- | --- |
| Q77 walk through the architecture | ✅ | Eight components. **Name the loop** — planner ↔ collector ↔ graph |
| Q78 executing untrusted code safely | ✅ | Rootless, no Docker socket, caps dropped, network off, resource limits, read-only base FS, no secrets, redaction, full audit. **Tested adversarially, not asserted.** No multi-tenancy claim |
| Q79 network off but Maven needs downloads | ✅ | Two phases, separate container invocations, separate policies |
| Q80 what does "deployed" mean | ✅ | Third party, clean Linux, from documentation, same certificate class, replays, removes everything. **Someone outside the team performs it** |
| Q81 CI integration | ✅ | CLI + exit codes + artifacts. **Invoked on demand, not every build** — SH1/SH3 overhead numbers support this |

## Section 12 — CDR ⚠️ *collides with our own exclusion*

| Q | Readiness | Note |
| --- | --- | --- |
| Q82 your scope excludes automatic repair | ⚠️ | What was excluded is *automatic source-code repair*. CDR does not modify source. **Never say "automatically fixing" — one such phrase and they hold you to the stronger claim all session** |
| Q83 why a module not a feature | ✅ | It depends on the certificate being trustworthy. Keeps the removal test clean |
| Q84 vs iFixFlakies patch generation | ✅ | Theirs harvests cleaners; ours is indexed on the certificate's resource path |
| Q85 how do you evaluate suggestions | ✅ | Precision against fix-commit oracle with the leakage rule; coverage; human judgement in acceptance |
| Q86 if CDR does not ship | ✅ | An optional extension and nothing from committed scope |
| **— document consistency** | ❌ | [[07-Defense/weak-points]] §5 — audit before slides |

## Section 13 — Three-member ownership

| Q | Readiness | Note |
| --- | --- | --- |
| Q87 who owns what | ✅ | [[07-Defense/ownership-map]] |
| Q88 member three sounds like support work | ✅ **strong** | The POC's two invalidating defects were *harness* problems. Removal test: without M3, an algorithm and no trustworthy evidence it works |
| Q89 are these three separate projects | ✅ | They connect through the loop and shared interfaces; the certificate is the artefact all three produce jointly |
| **Q90 explain a subsystem you do not own** | ⚠️ | **Rehearse this hardest.** Minimum list in [[07-Defense/ownership-map]]. Deferring is the single most damaging answer available |
| Q91 how did the team grow | ✅ | Scope grew by exactly one pillar; committed core unchanged |

## Section 14 — Scope, risk, plan

| Q | Readiness | Note |
| --- | --- | --- |
| Q92 committed scope in one list | ✅ | [[02-Requirements/scope-boundary]] |
| Q93 what is optional and what gates it | ✅ | Each gated on the committed core reaching Final-1 exit criteria |
| Q94 biggest risk | ✅ | **Historical build rot** — gates everything downstream |
| Q95 second | ✅ | **Invisible resources** — "our POC is direct evidence this risk is live rather than theoretical" |
| Q96 timeline with exit evidence, not activities | ✅ | [[00-Meta/roadmap]] |
| Q97 critical path | ✅ | Reproduced cases in clean containers |
| Q98 if behind at Final-1 | ✅ | Cut order: CDR → filesystem evidence → adaptive policy. Core end-to-end path is last. **Recorded scope change, never silent removal** |

## Section 15 — Ethics and practice

| Q | Readiness | Note |
| --- | --- | --- |
| Q99 ethical issues | ✅ | Three, none large, all real: executing third-party code; source/output may contain proprietary data; **responsible claim-making** |
| **Q100 AI tool usage** | ⚠️ | **Log must be current on the day.** [[00-Meta/ai-usage-log]]. The log is evidence *for* you, not against |
| Q101 classify external dependencies | ✅ | Support / core-assist / core-replacement. Nothing we claim as contribution is core-replacement |

## Section 16 — Traps

| Q | Readiness | Note |
| --- | --- | --- |
| Q102 one minute: everything | ⚠️ | Time it |
| Q103 is this a research paper with a CLI on top | ✅ | Deliverable is installable and operable with a testable deployment definition |
| Q104 why a full year for three people | ✅ | **Three of the four hardest parts cannot start until the previous works.** Do not argue from code volume |
| Q105 one-word answer: will you beat RankF | ✅ | **Decline the format, answer the substance.** "On ranking accuracy alone, we may not." Our claim is about cost to a verified replayable result under budget |
| Q106 your POC failed, should we defer | ✅ | [[05-Testing/poc/what-changed]] |
| Q107 least confident about | ✅ | Whether resource evidence earns its complexity at an affordable depth — **with the pre-registered fallback** |
| Q108 first thing tomorrow | ✅ | Expand the reproduction set + land the four-way control as a harness requirement |
| Q109 what have you not thought about | ✅ | Target-as-polluter-for-a-later-test; evidence-bundle retention defaults. **Do not perform humility** |

---

## Rehearsal plan — run this three times, differently each time

**Pass 1 — alone, aloud, no notes.** Anything you cannot say in three sentences you do not
yet understand well enough.

**Pass 2 — in the team**, one member playing panel, asking **out of order**, including
questions belonging to another member's area. *The deferral reflex is trained out only by
being caught doing it.*

**Pass 3 — with the supervisor**, on the fifteen questions from **sections 3, 7 and 13
only** — prior art, POC and ownership are where proposals are actually rejected.

**Time three answers to the second:** the one-minute pitch, the contribution statement, and
the POC result.

**Decide before you walk in** which member answers first for each section, and agree that
whoever owns a subsystem answers it *even if another member could answer faster*. The panel
is assessing three engineers, not one spokesperson.

Log each pass in [[07-Defense/rehearsal-log]].
