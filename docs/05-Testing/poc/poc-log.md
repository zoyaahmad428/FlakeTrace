# POC — Execution Log

**Executed 25–28 August 2026.** Status: `EXECUTED`. This is the only part of the project
describing work already performed. Decision recorded: **NARROW**.

> **Panel note.** The FAST guide states a POC that disproved its assumption and caused the
> group to revise its approach is usually *more* valuable than one that confirmed it. Lead
> with the negative result on the slide. A panel that discovers it under questioning treats
> it as concealment; a panel told up front treats it as engineering judgement.

---

## 1. The question we set out to answer

> Can a lightweight shared-resource signal — static-field write/read overlap — prioritise the
> true polluter for a victim test, and thereby reduce the number of confirmation executions
> required, on real, buildable Maven projects?

We deliberately did **not** set out to reproduce a flaky test. Reproduction is a known fact
and proves nothing about our contribution. We tested the one assumption that, if false,
invalidates the whole ranking argument.

## 2. Pre-registration

Definitions and decision gates were written and committed to version control **before any
experiment ran**. The commit timestamp is held as evidence. Frozen definitions:
[[05-Testing/poc/frozen-definitions]].

| Measure | Pre-registered gate | Outcome |
| --- | --- | --- |
| Reproduction yield | ≥ 3 of 4 cases reproduce in clean containers | **Partial** — 4 reproduced clears the count, but 4 of 8 is a 50% rate against a gate written as 3 of 4 |
| Ranking quality | True polluter in top 5 or top 20% for ≥ 3 cases | **Failed** — zero overlap, so there was no ranking to evaluate |
| Execution saving | ≥ 30% fewer median confirmations than one-by-one | **Failed — 0%** |
| Replay reliability | ≥ 9 of 10 matching failures per accepted pair | **Passed** — 10/10 on all four, Wilson 95% [0.72, 1.00] |
| Evidence integrity | Every reported overlap names exact field + bytecode locations | **Passed** |

## 3. Case selection

From IDoFT's `pr-data.csv` (8,075 rows) → filtered to OD categories with usable status →
pool of 1,438 rows → screened against tractability rules (no Android, no DB/network test
dependencies, no integration or benchmark modules, no very large builds).

| Project | Pinned SHA | Licence | Cases |
| --- | --- | --- | --- |
| json-iterator/java | `6925cf4c` | MIT | JI-01 – JI-04 |
| alibaba/fastjson | `e05e9c5e` | Apache-2.0 | FJ-01 – FJ-04 |

All eight victims sit in distinct test classes. The four fastjson victims map to four
distinct fixing pull requests; one candidate was swapped out because it shared a root-cause
PR with another.

**Deviation recorded:** fastjson is archived on GitHub. This did not block the work — the
pinned commit fetches normally — and an archived repository cannot move under us, which
*strengthens* reproducibility rather than weakening it.

## 4. Environment

Clean `maven:3.9-eclipse-temurin-8` containers, shared Maven cache volume, image digest
recorded. **JDK 8 was required:** fastjson targets source level 1.5 and jsoniter 1.6, both
rejected by modern JDKs.

Test execution ran with **networking disabled**; dependency fetch was a separate,
network-enabled stage. (This is the two-phase model that also answers Q79.)

## 5. Survey findings that changed the plan

Three properties discovered during setup, none anticipated:

1. **All eight cases are JUnit 3.** Classes extend `TestCase`, methods follow `public void
   test*`, `@Test` annotations essentially absent. Candidate enumeration had to follow the
   naming convention rather than the annotation. *(This is why JUnit 3 support via the
   JUnit38 adapter is validated rather than assumed — see claim E1.)*
2. **Old compiler targets.** Neither project builds on a modern JDK.
3. **Large candidate sets.** After package restriction, one fastjson case still had **730
   candidates**, two others 529 — exceeding jsoniter's entire 384-method module.

## 6. Tooling built

| Component | Purpose |
| --- | --- |
| `FtRunner.java` | Executes an ordered test sequence in a single JVM, one fresh JVM per order, printing machine-readable outcome + normalised failure signature per test. Drives tests through JUnit 4's `Request.method()`, which handles JUnit 3 classes via `JUnit38ClassRunner` |
| `FtList.java` | Candidate enumeration: public no-arg `test*` methods on non-abstract `TestCase` subclasses. **Loads classes without initialising them**, so no subject `<clinit>` fires during enumeration |
| `extract_static.py` | Runs `javap -c -p` over compiled classes, parses every `getstatic`/`putstatic` → `owner.field:descriptor` + bytecode offset. Attribution per test method covers the method, `setUp`, `tearDown`, `<clinit>` and N hops into project-owned callees |
| `step_scan.py` | Exhaustive scan: runs `[candidate, victim]` for every candidate, records victim outcome + signature |
| `step_analyze.py`, `step_replay.py` | Offline strategy replay; clean-container replay verification with Wilson intervals |

**`javap` chosen over ASM deliberately:** no external dependency, and the bytecode offsets it
prints satisfy the evidence-integrity requirement without extra work.

### The single-scan protocol — why the experiment was affordable

The exhaustive scan runs **once per case**. Ground truth, the one-by-one baseline, five
seeded random baselines and our ranked strategy are then all computed **offline** from that
one outcome table. Cost is *N* executions, not *N × strategies*.

This is also what makes the outstanding depth × strategy matrix affordable without
re-scanning — three of the five remaining pre-defence items run offline against data we
already hold.

## 7. What was run

| Stage | Work |
| --- | --- |
| Build gate | Both subjects cloned at pinned SHAs, built green in clean containers; environment recorded |
| Isolation & classification | Each of 8 targets run alone, 10×. Six passed 10/10 (victims); two failed 10/10 (brittle) |
| Extraction | 2,132 fastjson + 58 jsoniter test classes disassembled, plus main classes; read/write sets per test method |
| Scan & baselines | **2,606 orders / 5,212 test-method invocations**; all strategies replayed offline |
| Replay | 10 clean-container replays per accepted pair, with Wilson intervals |
| Decision | Recorded |

## 8. The headline result — negative

At the frozen **one-hop** analysis depth, `|writes(candidate) ∩ reads(victim)|` was
**zero for every candidate in every case**.

Not a weak signal — **no signal**. The ranked strategy was therefore byte-identical to
one-by-one confirmation and saved **0%** against a 30% gate.

**Why the signal was empty:** direct static-field references in a test method body do not
capture state written through helper methods, factory calls, static initialisers or library
entry points — which is where the state actually moves in both subject projects.

## 9. The depth-2 ablation

In case **FJ-02**: the state-setter writes `JSON.defaultTimeZone` at
`DateParserTest.setUp@5`; the target reads it at `TypeUtils.cast@536` — **two hops down the
call chain**. At one-hop depth this write and this read are invisible to each other.

Re-extracting at depth 2 moved FJ-02's true polluter from **rank 39 to rank 1** — a 97.4%
reduction in confirmations for that case.

**The other three reproduced cases did not move at any depth we tested.**

> **Conclusion: depth is necessary but not sufficient. One case improving is a mechanism
> finding, not a method.**

The claim this supports is narrow — that *depth is the variable worth investigating* — not
that depth two works. See [[07-Defense/decisions/depth-configurable]].

## 10. Two harness defects found and corrected

**These are the most important part of the POC and we intend to lead with them.**

### Defect 1 — 182 fabricated polluters

Our first jsoniter scan reported **182 of 210 candidates as polluters**. Every one failed
with an *identical* `LinkageError`.

jsoniter's Surefire configuration does not run test classes directly — it runs **five suite
classes with `reuseForks=false`**, and each suite's `@BeforeClass` selects the runtime
codegen mode. Our runner had no suite context, so jsoniter's runtime code generation
collided with itself.

Fix: a flag that invokes the suite's `@BeforeClass` before each order. The count fell from
**182 to 0**.

*Without catching this, the POC would have reported four fabricated reproductions.*

### Defect 2 — a "fix" that erased the phenomenon

Two fastjson targets failed when run alone under the container's UTC timezone. We "fixed"
this by setting `TZ=Asia/Shanghai`, and they passed.

**This was wrong.** Those targets fail alone *because that is what they are* — they are
brittle tests needing `JSON.defaultTimeZone` set by a predecessor, and
`DateFieldTest8.setUp` writes it globally and never restores it. Forcing the timezone through
the environment made the state-setter's write a **no-op** and deleted the exact effect under
measurement.

We removed the override and classified direction empirically instead.

### What the two defects prove

That **the measurement harness is itself an object requiring validation**. Both defects
produced clean-looking output. Neither would have been caught by checking that the code ran
without error.

That is exactly why the negative result is trustworthy — we found the ways the harness could
lie *before* we accepted its answer.

**Both are also the strongest available evidence for Member 3's role** (see
[[07-Defense/ownership-map]]): these were harness problems, not algorithm problems.

## 11. The control that now exists

*Answering "how do you know there is not a third defect?"* — we do not know it and would not
claim it. What we can state is the control now committed:

> For every case, execute the passing order and the failing order **uninstrumented and
> instrumented**, and require all four outcomes to match the expected signature before any
> measurement is accepted.

The timezone defect would have been caught by that control on the first run. It is now part
of the committed harness and is a **testable requirement, not a practice**.

## 12. Decision recorded

**NARROW.** The resource *scope* is refuted; the approach is not.
Full record: [[07-Defense/decisions/poc-scope-narrow]].

### What would have made us PIVOT instead

Both conditions pre-registered:
1. If **fewer than three of four cases had reproduced**, the dataset pipeline would have
   become the first risk and we would have reduced case scope before claiming readiness.
2. If the **depth-2 ablation had also produced empty overlap** — i.e. the resource
   abstraction failing at every affordable depth — the resource-evidence pillar would have
   collapsed and the contribution restated around order evidence and certification alone.

Neither triggered, so **Narrow was the correct decision under our own rules rather than the
comfortable one.**

## 13. Claim boundaries — memorise this section

**Supported by the evidence:**
- 8 targets built at pinned SHAs
- 4 reproduced with verified replay statistics
- the one-hop static-field signal was uninformative *on these subjects*
- depth is necessary but not sufficient
- two harness-validity failure modes identified and corrected

**NOT supported:**
- that static-field analysis is useless *in general* — n = 4, and both subjects are JSON
  libraries built around global static configuration, **the most favourable possible
  substrate for this hypothesis**
- that depth-2 extraction works *generally* — it moved one case

**Deviation to disclose unprompted:** the frozen definitions were **amended after freezing**,
on 27 August, to add execution-context fidelity. The amendment corrected the harness defect
producing false positives. It changed neither the reproduction criterion nor the strategy
scoring, and it moved a result from 182 to 0 — **against our own interest**. Both commits are
held.

**⚠ Items to verify before quoting any POC figure externally:** the isolation classification
(six victims, two brittle) and the reproduction count (four, all fastjson) need reconciling
in the write-up, since two fastjson targets were classified brittle during isolation. The
underlying data exists; the summary wording needs to be made precise.
See [[07-Defense/weak-points]] §4. **Owner: M3. Do this first.**

## 14. Evidence to have on screen — not on a slide

When a panel says *"show me the evidence, not the description of it"*:

- [ ] Manifest with both SHAs
- [ ] Container digest
- [ ] Build logs
- [ ] Per-run outcome CSV
- [ ] Extracted static-field sets showing the empty overlap
- [ ] Ranked ordering next to the OBO ordering, demonstrating they are identical
- [ ] Depth-2 ablation output for FJ-02 showing rank 39 and rank 1
- [ ] The 182-false-polluter log
- [ ] The timezone finding
- [ ] **The one-page decision record on top**

*If asked for one artefact that is not ready, say so immediately and offer the closest thing
you do have.*
