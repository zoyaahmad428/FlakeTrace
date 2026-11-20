# W32 — Java/Maven practitioner workflow check (FT018)

*v1 · 2026-11-20 · Status: `DRAFT PROTOCOL` by M1. **No practitioner has been contacted and no
session has been held.** The case (M2) and the acceptance task (M3) are still to be supplied;
their places are marked below. Verifier: M3 ([[10-Final1/iteration-2-plan]]).*

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

## The case — to be supplied by M2

*Not yet supplied.* It needs the input (victim, the failing order or its source, the failure
message) and the report FlakeTrace produced for it, from a recorded run. Options:
- fixture **F1**: simple, and runs in seconds;
- **fastjson FJ-03**: real, but its ranked and original runs are not yet done
  ([[05-Testing/real-case-protocol]]).

**Do not show a report that was not produced by a real run.**

## The acceptance task — to be supplied by M3

*Not yet supplied.* It must state:
- what the participant is asked to do with the report, for example to name the polluter, what
  was established, and what was not;
- the time limit;
- the pass criteria;

and must be written down before the session, so the result cannot be fitted afterwards.

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
