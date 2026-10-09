# Stakeholder Evidence

*Three practitioner interviews, complete. This closes the gap the Dossier listed as our
weakest area — with one important caveat, recorded in [[07-Defense/weak-points]] §1.*

Questionnaire: 14 questions, 15–20 minutes, process and timing only — no source code,
credentials or customer data requested.

---

## Who we spoke to

| # | Person / role | Organisation | Stack | Scale |
| --- | --- | --- | --- | --- |
| SH1 | Mahad Sheikh, CEO (technical + management) | Inspirovix | Python/pytest, JS-TS/Jest, GitHub Actions, Docker | Few hundred tests; 5–15 min CI runs |
| SH2 | Engineering Lead (3 months as lead, 2 years at company) | Trillet AI — voice-agent SaaS | Node.js/Fastify + React/TS, both Vitest, GitHub Actions, Northflank | Suite being built out, not yet a required gate; 7–10 min full run |
| SH3 | Full-stack engineer (2.5 years) | Learnsignal — accountancy LMS | TypeScript, Next.js, Vitest, Playwright | **~5,500 Vitest tests across ~570 files** + 27 Playwright specs; ~50,000 student profiles in production |

---

## What all three independently confirmed

### 1. Order-dependent failures happen, and isolation is manual

- **SH1:** tests "accidentally share state, modify environment variables, leave database
  records behind, change global configuration, or fail to clean up resources." Their method:
  reproduce, then run the failing test with progressively smaller groups of preceding tests.
  *"Manually narrowing down a large suite can be time-consuming. A tool that automatically
  identifies the test responsible for contaminating another test would therefore be useful."*
- **SH2:** a test mutating shared state left a record behind, breaking a later test.
  Diagnosis was: notice the failure is always the same test in the same position → run in
  isolation (passed) → run after the suspected test (failed). *"It is manual binary search —
  intuition and trial and error. **There is no tooling support for it.**"*
- **SH3:** cross-test pollution in the Playwright suite against a **shared staging database
  with nine fixed test profiles** — residual enrolments and progress records altering
  conditions for later specs. Diagnosis is binary-search isolation across preceding tests.
  Because it is slow, *"our standard mitigation is simply inserting defensive database
  teardown hooks."*

**This is the current-workflow evidence Stream B requires.** Three independent teams,
three stacks, same manual procedure, no tooling.

### 2. Time cost

| | Per incident | Frequency |
| --- | --- | --- |
| SH1 | 30–60 min simple; **several hours** when CI-only and not locally reproducible | ~monthly |
| SH2 | 25–30 min for the described case | Flaky failures **a few times a week**; root cause actually investigated only 1–2× per month |
| SH3 | ~15 min minor | Minor weekly; **2 major incidents this year, each ~a full working day** |

SH2's reason for the gap between "happens weekly" and "investigated monthly" is worth
quoting: the team is *"pulled in a lot of directions… the test pipeline competes with live
priorities rather than being a fixed part of the workflow."* That is the decision cost the
project targets — not just time spent, but investigation deferred.

### 3. Existing tools explain *what* failed, not *why it is intermittent*

**SH1:** GitHub Actions logs, pytest/Jest output, application logs, Docker logs, monitoring.
*"They are much weaker at explaining why a failure is intermittent… they normally do not
automatically tell us that Test A modified some shared state that caused Test B to fail 30
tests later. Finding that relationship usually requires manual investigation."*

Direct support for claim B8 — the residual diagnostic gap is real from the user side, not
only from the product-documentation side.

### 4. Typed abstention is wanted — this is the strongest result in the interviews

Question 13 described the tool including its refusal behaviour, and asked whether "I could
not determine this within your budget" would make it useless.

- **SH1:** *"I would prefer the tool to say 'I could not determine this within your budget'
  rather than provide an uncertain answer. In engineering, a clearly stated unknown is more
  useful than a confident but incorrect diagnosis."* Wanted in the output: suspected
  relationship, reproduction command, executions performed, time consumed, and enough
  evidence for a developer to verify.
- **SH2:** *"A tool that guesses is worse than useless — if it tells me test B is caused by
  test A and it is wrong, I have wasted an hour chasing a phantom. A definitive 'I ran forty
  orderings and could not isolate the cause within your limit' tells me something real."*

**Use this when asked Q28 ("is abstention just a way of not solving the problem?").** The
answer is no longer only architectural — two practitioners independently said a guess is
worse than a refusal, unprompted.

SH2 also asked for something we do not currently commit to: **classification of flakiness
category** (environmental / ordering-dependent / genuinely nondeterministic), because
*"the fix strategy for each is completely different, and right now we waste time
misdiagnosing the category before we even start."* Worth noting as a user-requested feature
we deliberately do not promise — our input is an already-known OD failure.

### 5. Self-hosting is a hard requirement

- **SH3:** sending the repository to an external service is *"out of the question"* — it
  contains database schemas, migration files and integration logic tied to student profiles
  and payment information. Must run on internal GitHub runners or self-hosted.
- **SH1:** local analysis *"strongly preferable"*; proprietary and client code. *"A tool that
  can operate completely within our own infrastructure would therefore be easier to approve."*

This converts self-hosting from a design preference into a **stakeholder requirement**, and
is why the committed product needs no cloud, no GPU and no paid API.

### 6. CI overhead tolerance — our NFR envelope

| | On every PR | Opt-in / nightly |
| --- | --- | --- |
| SH1 | 5–15 min acceptable *if it does not run on every successful build* | Longer tolerable when explicitly requested |
| SH3 | 5 min → "pushback"; **15 min → "completely unacceptable"** | **30 min entirely tolerable** |

**Design consequence:** the tool is invoked *on demand for a known failing test*, not on
every build. Both stakeholders' numbers support that boundary. This is the evidence behind
the overhead NFR in [[02-Requirements/non-functional]].

### 7. Quarantine is real, and is disguised

- **SH1:** very few disabled — *"a skipped test gradually loses its value"* — low single digits.
- **SH3:** officially none bypassed, ~6 conditional skips. **But the entire 8-test
  accessibility suite runs with `continue-on-error`**, so it *"consistently fails during CI
  without obstructing deployment pipelines, rendering it practically disabled in function if
  not in name."*

SH3's answer is the more useful one: quarantine does not always look like quarantine. Use it
if a panel challenges the "quarantine removes coverage permanently" claim.

### 8. The consequence: erosion of trust, and the missed-regression risk

**SH1:** *"Once developers become accustomed to seeing random failures, there is a risk that
they start automatically re-running failed pipelines instead of investigating them."* No
confirmed production incident attributable to a dismissed flaky test — but *"a genuine
regression can look similar to a known intermittent failure."*

Note the honesty: no stakeholder claimed a catastrophic incident. **Do not inflate this.**
The consequence we defend is coverage loss and trust erosion, both directly evidenced.

### 9. Adoption conditions (relevant to acceptance testing)

SH1's stated conditions: low setup/maintenance overhead, runs entirely in own
infrastructure, configurable time/compute budget, clear reproducible results rather than a
"flaky" label, reasonable CI overhead, useful output when diagnosis fails, and a local
reproduction command. **SH1 also agreed to review our results later and give practitioner
feedback** — that is a named acceptance participant, which the guide requires.

---

## Where this evidence does *not* reach — read before citing it

**None of the three uses Java, Maven, JUnit or Surefire.** Their stacks are Python/pytest,
Node/Vitest and TypeScript/Vitest. The polluted state they describe is largely **database
rows on shared staging instances**, which sits in our explicitly excluded list.

The interviews therefore support:
- the **problem shape** (manual isolation, no tooling, real time cost)
- the **design commitments** (budget, typed abstention, self-hosting)
- the **overhead envelope** (on-demand, not every build)

They do **not** support:
- that Java teams specifically face this (that rests on IDoFT, RankF, iFixFlakies corpora)
- that our three JVM resource families are the ones users care about most

Full treatment, including the answer to give the panel:
[[07-Defense/weak-points]] §1. **Closure action: one Java/Maven practitioner on record
before the defence.**

---

## Recording for the defence

> Our recorded stakeholder contacts are Mahad Sheikh (CEO, Inspirovix), an engineering lead
> at Trillet AI, and a full-stack engineer at Learnsignal. Workflow evidence is in the three
> completed questionnaires. Measured time cost ranges from 15 minutes for a minor incident to
> a full working day for a major one, with weekly minor occurrence and monthly root-cause
> investigation.

*Ask each participant to confirm how they wish to be identified before the defence — SH2 and
SH3 are currently recorded by role rather than name.*
