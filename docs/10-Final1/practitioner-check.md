# W32 — Java/Maven practitioner workflow check (FT018)

*v2 · 2026-11-22 · Status: `READY EXCEPT PARTICIPANT` (M1). **No practitioner has been
contacted and no session has been held.** The acceptance task (M3) was supplied on 2026-11-21, and
the case (M2) on 2026-11-21 as a committed F1 bundle (both below). Verifier: M3
([[10-Final1/iteration-2-plan]]).*

## Why this exists

Our three practitioner interviews ([[00-Meta/stakeholder-evidence]]) support the problem shape,
but none of the three uses Java, Maven, JUnit or Surefire ([[07-Defense/weak-points]] §1). The
supervisor's finding **FT018** asks for one Java/Maven practitioner workflow check covering:
1. a realistic input;
2. the expected decision;
3. an acceptable runtime;
4. the evidence needed to act.

**Closes when** ([[10-Final1/feedback-register]]): a dated, consented record linked to an
acceptance task, or a recorded blocker and a substitute agreed with the supervisor.

What one session can and cannot show: it is one person's view (n = 1). It can show whether a
Java practitioner reads our report the way we intend and what they would need to act on it. It
cannot validate the tool, and it must never be quoted as if it did.

## Roles

| Who | Does |
| --- | --- |
| M1 (Zoya) | Finds the participant, runs the session, writes the record |
| M2 (Raffay) | Supplies the case: the input, and the report FlakeTrace produced for it |
| M3 (Zarpash) | Supplies the acceptance task and its pass criteria **before** the session; verifies the record |

## Who qualifies

- Works, or has worked, on a Java project built with Maven and tested with JUnit.
- Not a member of this project and not a FAST student on it.
- Has debugged a test that fails in the suite but passes alone. This is helpful, not required.

## Finding someone — record every attempt

Each attempt goes in the log at the end, with its date and outcome. If nobody can be found, that
log is the blocker evidence FT018 accepts.
1. Ask the supervisor for an introduction (Dossier decision 5; [[07-Defense/weak-points]] §1).
2. Ask SH1, who agreed to review our results ([[00-Meta/stakeholder-evidence]] §9), whether
   they know a Java/Maven engineer.
3. Faculty members or alumni with industry Java experience.

## Consent — read aloud and agreed before anything else

> We are a final-year project team at FAST-NUCES Islamabad (F26-214, FlakeTrace). This is a
> 30-minute conversation about how you handle tests that fail only when other tests run first.
> We will ask about your process and timing, and show you one report from our tool. We will not
> ask for any of your company's code, credentials, customer data or internal documents.
> We will take written notes. We will record audio only if you say yes now. We will record your
> name and role only if you agree; otherwise only your role and stack. Before we quote you, we
> will show you the quote and you may change or withdraw it. You can stop at any time, and you
> can ask us to delete your notes later. The notes go into our project repository, which our
> supervisor and evaluation panel read. Do you agree?

Record **how** consent was given (spoken, written, by message) and its date. No consent means no
session.

## The session (30 minutes)

| # | Part | Time | FT018 item |
| --- | --- | --- | --- |
| 1 | Consent | 2 min | — |
| 2 | Background | 3 min | — |
| 3 | The case, *before* showing our report | 8 min | 1 realistic input, 4 evidence |
| 4 | Our report for the same case | 8 min | 2 expected decision, 4 evidence |
| 5 | The acceptance task (M3) | 5 min | links the record to a task |
| 6 | Runtime and adoption | 4 min | 3 acceptable runtime |

**2. Background**
- What do you build, in which Java and Maven versions, and with which JUnit?
- Roughly how many tests does the suite have, and how long does a full run take?
- How often do you see a test fail in the suite but pass when you run it alone?
- Who investigates such a failure, and when?

**3. The case, before our report.** Show the input M2 supplies: the failing test, the order it
failed in, and its failure message. Do not show the tool's answer yet.
- Is this a realistic input in your world? What is missing?
- What would you do first? What next?
- How long would this take you?
- What would you need to see before you change code or open a ticket?

**4. Our report for the same case.**
- What does this report tell you, in your own words?
- What would you do now? Is that what you would have decided without it?
- What do "VERIFIED (sequence)" and "static overlap: a possible mechanism, not confirmed as the
  cause" mean to you? (This checks our wording; claims ledger G1 and G3.)
- What is missing before you would act on it?
- What would make you distrust it?

**5. The acceptance task.** As written by M3, with the time limit and pass criteria fixed
before the session. Record pass or fail exactly as observed.

**6. Runtime and adoption.**
- How long may a diagnosis like this take before it is not worth it: minutes, an hour,
  overnight?
- Where would you run it: on a laptop, in CI on every build, or on demand?
- What would stop your team from using it?

## The case — supplied by M2, 2026-11-21

**Fixture F1**, as a committed evidence bundle:
`eval/bundles/20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/` (Interface 8, [[evidence-m2]]). It holds `report.json`,
`record.jsonl`, `manifest.json`, `replay.md` and `environment.txt`. M2 made it from a clean
`main` (`tool.dirty: false`), it replays `same`, and it contains no personal paths.

| Part 3 shows (input only) | Part 4 shows (FlakeTrace's answer) |
| --- | --- |
| Victim `odfixture.ConfigVictimTest#expectsDefaultMode`; it fails in the suite with `java.lang.AssertionError` | `report.json`: `VERIFIED (sequence)`, polluter `odfixture.ConfigPolluterTest#pollute`; the alone tally (20 of 20 alone runs passed) and the sequence tally (20 of 20 failed the same way); the resource as a static overlap, not the cause |

**fastjson FJ-03** is the real-code alternative. In order mode it is `UNRESOLVED
(NOT_REPRODUCED)`, because no full order fails. With pair mode (`--search pairs`, W35, PR #160),
M2 reports a diagnosis from the victim alone: `CANDIDATE`, polluter
`SerializeWriterTest_14#test_writer_1`, found after 368 of 524 pairs. Its report would ask a
harder question (a candidate, a constructed pair, no resource edge), and it is not yet
independently reproduced (M1 is W35's verifier).

**Show only a report produced by a real run.** These are.

## The acceptance task — supplied by M3, 2026-11-21

Written and fixed before any session, against the real F1 case (`eval/bundles/
20261121T093338Z-odfixture.ConfigVictimTest#expectsDefaultMode/`, the clean checkout M2
prepared for this). If M2 supplies FJ-03 instead, use the FJ-03 variant at the end of this
section — the task's shape is the same either way, only Q2's exact wording changes.

**What the participant is asked to do.** Immediately after Part 4's open discussion, with no
further talking, show them the same report once more (on paper or the screen) and ask them to
write short answers to three questions, unaided:

1. *"Which one test would you look at first, based on this report?"*
2. *"Does this report prove that the shared resource access is why the victim test fails?
   Answer yes or no, and point to the exact line or field that supports your answer."*
3. *"Before you would treat this as a confirmed bug in your own code review, what is the one
   thing this report does not give you?"*

**Time limit:** 5 minutes total (the session plan's own Part 5 allocation), no help, no going
back to re-read the Part 4 discussion.

**Pass criteria, fixed now, before the session:**

| Q | Passes if | Fails if |
| --- | --- | --- |
| 1 | Names the test in the report's `polluters[0]` (for F1: `odfixture.ConfigPolluterTest#pollute`, the class name alone also accepted) | Names any other test, or says the report does not say |
| 2 | Answers **No**, and points to the CLI's own line "static overlap: a possible mechanism, not confirmed as the cause" or `assurance.resource.mechanism: "NOT_ASSESSED"` | Answers "Yes", or treats the overlap as confirmed causation in any wording — **this fails the whole task regardless of Q1/Q3**, because it is the one thing FT018 actually tests: whether a real practitioner reads `VERIFIED` as proof of cause |
| 3 | Names something in the spirit of "runtime confirmation that the write actually reached the read in this execution" / "proof the resource access is the mechanism" — any phrasing recognising that only static analysis was shown | Names something the report *does* give (the polluter's name, that it reproduces, that it passes alone) |

**Overall pass/fail:** PASS requires Q2 to pass, plus at least one of Q1/Q3. Record each
answer verbatim and each question's pass/fail in the record template below — not paraphrased,
so the result cannot be fitted after the fact.

**FJ-03 variant**, if M2's case is FJ-03 instead of F1: that real report is
`CANDIDATE [NO_SUPPORTED_RESOURCE_EVIDENCE]` — no resource edge at all (the pollution is a JDK
`ThreadLocal` call that static analysis does not follow, [[04-Implementation/evidence-collector]]).
Rephrase Q2 to *"Does this report name any mechanism for why the victim fails? Answer yes or
no, and point to what supports your answer"* (passes on **No**, citing
`candidate_reasons: ["NO_SUPPORTED_RESOURCE_EVIDENCE"]` or the CLI's own "no resource" line).
Same test, in both variants: whether a result short of outright proof is read as weaker than it
is, not as a confirmed cause.

## Record template — one per session

```
Date, time, mode (online / in person):
Participant (name and role only if agreed; otherwise role and stack):
Consent: how given, date; audio yes/no:
Stack (Java, Maven, JUnit versions; suite size; run time):
Part 3 answers (realistic? first steps? time? evidence needed?):
Part 4 answers (understood as? decision? missing? distrust?):
Wording check (what VERIFIED (sequence) and static overlap meant to them):
Acceptance task: version used, result (pass / fail), time taken, notes:
Runtime and adoption answers:
Quotes shown to the participant and approved (yes / no, date):
What did not work in this session:
Recorded by, date written:
```

## If nobody can be found

By the team's agreed cut-off (plan cut order, item 6), record the attempt log below as the
blocker, and propose a substitute **to the supervisor**. Possible substitutes, for the
supervisor to choose from, not decided by us:
- a Java-experienced faculty member doing the acceptance task alone;
- a written questionnaire answered by a Java/Maven engineer at a distance.

Tell the supervisor before the Final, not at it.

## Attempt log

| Date | Who was asked (role, or "supervisor") | How | Outcome |
| --- | --- | --- | --- |
| *none yet* | | | |
