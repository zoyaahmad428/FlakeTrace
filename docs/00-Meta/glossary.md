# Glossary

*Every technical term a panel might ask you to define, in plain English. Grouped by theme,
because these are far easier to remember in clusters.*

---

## The project in plain words — read this first

A software team writes automated tests. Normally they run all together, one after another,
every time someone changes the code.

Sometimes a test fails **not because the code is broken, but because of a test that ran
earlier**. The earlier test left something in a messy state — a shared variable, a file, a
setting — and the later test trips over it. Run the later test alone and it passes. Run it
after the messy one and it fails. This is an **order-dependent failure**, and it is a nightmare
to debug, because the suspect is not the failing test; it is one of possibly hundreds that ran
before it.

FlakeTrace takes over that hunt. You give it a project, one failing test, and a spending limit.
It runs carefully chosen experiments, watches which tests touch which shared things, and
narrows the suspects. At the end it either hands you a **certificate** — "run these three tests
in this order and the failure appears 19 times out of 20; here is the exact shared variable,
written here and read there" — or it honestly says **"I could not establish this within the
budget"** instead of guessing.

### The six ideas that unlock 80% of everything else

1. **Shared state** — data outliving a single test, letting one test affect another
2. **Victim and polluter** — the test that fails, and the earlier test that caused it
3. **Budget** — the tool cannot run forever, so *choosing which experiment to run next* is the hard research problem
4. **Minimal order** — the shortest sequence still reproducing the failure
5. **Verification and abstention** — proving the answer by repeating it, and saying "unresolved" rather than inventing one
6. **Baseline** — an existing method you must beat, or at least match, to claim your method is worth anything

---

## 1. The flaky-test problem

**Test (unit test)** — a small program that runs a piece of your code and checks the result.

**Assertion** — the line stating the expectation. If false, the test fails.

**Test suite** — the full collection of tests, usually run together.

**Test isolation** — the principle that a test should give the same result alone or alongside a
thousand others. Order-dependent failures **violate** this principle.

**Flaky test** — sometimes passes, sometimes fails, on exactly the same code. An unreliable
alarm: developers stop trusting the whole suite.

**Order-dependent (OD) test** — a flaky test whose result depends **purely on which tests ran
before it**. The code has not changed; only the order has.

**Victim** — passes alone, fails when a particular earlier test runs first. The innocent party.

**Polluter** — the earlier test leaving shared state in a bad condition. The culprit you hunt.

**Brittle test** — mirror image of a victim: **fails alone**, passes only when another test runs
first and sets things up. Silently depends on someone else's leftovers.

**State-setter** — the earlier test a brittle test secretly relies on.

**Cleaner** — a test that, inserted between polluter and victim, tidies the state back up.
Finding cleaners is how iFixFlakies builds fixes.

**OD-relevant test** — collective term (Rahman et al.) for polluters, state-setters and cleaners.

**Shared state** — any data surviving after a test finishes: a static variable, a file, a system
setting, a database row, a cache entry.

**Reproduction** — making the failure happen again on purpose. Cannot study or prove a fix
without it.

**Failure signature** — a fingerprint of a specific failure: exception type, failing assertion,
stable part of the stack trace. Needed so *"the test failed"* is not confused with *"the test
failed for the right reason."* **A crash from running out of memory is not the same failure as
the assertion you were trying to reproduce.**

**Retry / rerun** — the industry band-aid. Hides the problem rather than diagnosing it.

**Quarantine** — removing a known-flaky test from the pipeline. Also a band-aid, and a risk:
a quarantined test can hide a real bug. *(SH3 showed it does not always look like quarantine —
`continue-on-error` achieves the same thing.)*

**Nondeterminism** — behaviour varying between runs of the same input. Why a single run proves
nothing.

## 2. Java, build tools, CI

**JVM** — the program that runs compiled Java. **All tests in one Maven run typically share a
single JVM** — which is exactly why one test can pollute memory another reads.

**Static field** — a variable belonging to a class rather than an object, so there is **one copy
for the whole program**. It survives between tests: the single most common cause of OD failures.

**Java system property** — a global key-value setting inside the JVM. Another easily polluted
shared state.

**Filesystem path** — a file or directory on disk. An undeleted temp file changes later
behaviour.

**Reflection** — looking up classes and fields **by name at runtime**. Makes static analysis
unreliable, because an access can exist that never appears literally in the code text.
*(Explicitly unsupported for us.)*

**Bytecode** — the compiled instruction format the JVM executes. Often easier and more reliable
to analyse than source.

**GETSTATIC / PUTSTATIC** — the two bytecode instructions that **read** and **write** a static
field. Scanning for them is a cheap way to build "which test touches which shared variable" —
**this is exactly what our POC did**.

**JUnit 4 / JUnit 5** — two generations of the framework. They discover and run tests
differently, so supporting both is real engineering work, not a checkbox.

**JUnit 3** — older still; classes extend `TestCase`, methods are `public void test*`. **All
eight POC cases turned out to be JUnit 3.** Handled via JUnit 4's `JUnit38ClassRunner`.

**Maven** — the standard Java build tool.

**Maven module** — one buildable sub-project inside a larger repository.

**Surefire** — the Maven plugin that actually executes unit tests. **To control test order, you
control Surefire.**

**Maven launch** — one invocation of the `mvn` command. One launch may run 5 tests or 5,000 —
**which is why the honest unit of cost is test-method invocations, not launches**.

**Build rot** — the slow decay making an old project stop building: dead links, removed library
versions, incompatible JDKs. **Our single biggest risk.**

**Commit SHA / pinning** — recording the exact hash so everyone builds identically the same
code, forever.

**Exit code** — the number a program returns on finish; 0 means success. **Never a valid failure
signature** — see Qi et al.

**Self-hosted** — runs on the team's own machines rather than as a cloud service. **A
stakeholder requirement for us**, not a design preference.

## 3. Program analysis and instrumentation

**Static analysis** — working out what a program *might* do by reading code/bytecode **without
running it**. Fast, cheap, **over-approximates**, blind to reflection.

**Dynamic analysis** — watching the program **while it runs**. Precise about the observed run,
but slower and **can perturb**.

**Instrumentation** — inserting observation code so the program reports what it is doing. Like
attaching sensors to an engine.

**Resource event** — one recorded observation: *at this moment, this test read/wrote this shared
thing.*

**Resource family** — a category of shared state we commit to understanding: **static fields,
system properties, filesystem paths**. Everything else declared out of scope.

**Opaque / unsupported event** — an observation the tool notices but cannot interpret.
**Recording these honestly is what lets the tool say "there is something here I cannot
explain" instead of guessing.**

**Test-boundary attribution** — assigning each event to the test that caused it. Harder than it
sounds: setup, teardown and background threads blur boundaries. *(Our 182-false-polluter defect
was exactly this class of bug.)*

**Normalised resource identifier** — a canonical name, so two spellings of the same path, or the
same field reached via different class loaders, are recognised as **one** resource.

**Provenance** — the record of where evidence came from: which run, which instrumentation
version, which code location. **What makes the certificate auditable rather than taken on
faith.**

**Test–resource graph** — a map linking tests to the shared things they read and write, with
direction. The data structure ranking runs on.

**Instrumentation overhead** — how much slower the run becomes with sensors attached. **If too
high, no team runs it in CI — so it must be measured, not assumed.**

**Observer effect** — the risk that measuring changes the behaviour. **We have a direct
instance: our timezone override erased the failure entirely.**

**Analysis depth / one-hop** — how far the analysis follows method calls from the test body.
Depth 1 = the test body only. **The decisive variable in our POC.**

## 4. Search, minimisation, cost

**Candidate** — a test currently under suspicion of being the polluter.

**OBO (one-by-one)** — the simple baseline: try each earlier test in order, one at a time.
Reliable, dumb, often expensive.

**Delta debugging** — shrinking a failing input by repeatedly removing parts and re-testing.
Similar in spirit to binary search.

**ddmin** — the specific published delta-debugging minimisation algorithm.

**Deletion-minimal (1-minimal)** — a sequence where removing **any single element** stops the
failure reproducing. **A modest and honest claim** — not the globally shortest.

**Monotonicity** — the assumption delta debugging's efficiency relies on. **Violated here** —
which is why we run repeated execution per deletion check and preserve multi-test candidates.

**Counterfactual check** — removing each retained predecessor, and inserting the suspected
polluter, to see whether the outcome follows. **The "intervention" in intervention-backed
evidence.**

## 5. Statistics and evaluation

**Baseline** — prior work you must **actually run and compare against**, not merely cite.
*Converting a threatening competitor into your baseline is the standard defensive move.*

**Ablation** — removing one component to measure what it contributed.

**Control** — a case where you know what the answer should be, used to check the harness.

**Held-out set** — data untouched until the final evaluation.

**Leakage** — the answer reaching the input. *E.g. using a fix commit as an algorithm input
when it is also the oracle.*

**Wilson interval** — the recommended confidence interval for a proportion at **small n**.
Describes **replay reliability under our harness** — *not* the probability the diagnosis is
correct.

**Calibration** — the specific claim that a stated confidence of 0.8 means being right 80% of
the time, **demonstrated on held-out data**. We do not claim it.

**Pre-registration** — writing down your success thresholds **before** looking at results.

**Oracle** — the ground truth you judge against.

## 6. FYP and academic vocabulary

**Stream B** — the FAST category for a project starting from a **real observed workflow
problem**, not from reproducing a paper. Brings an obligation: **show evidence real
practitioners have this problem**.

**CCP (Complex Computing Problem)** — the accreditation concept requiring genuine engineering
difficulty. **A long feature list is not a CCP; one genuinely hard question is.**

**Contribution statement** — one precise sentence stating what your project adds, phrased so a
reviewer can check it against existing work.

**Defensible delta** — the specific, provable difference from the closest existing work. **Ours
is not "we find minimal orders" (done) but "budget-aware, intervention-backed certification
with honest abstention."**

**Prior art** — everything already published or shipped close to your idea. **Must be found
before you claim a gap, not after.**

**Stakeholder evidence** — named interviews or observations with current workflow and time cost
recorded. **Stream B projects are commonly failed for asserting a problem without this.**

**Removal test** — if a member were removed, would a meaningful technical responsibility and its
evidence disappear?

**Deployable** — defined strictly: a third party installs on a clean Linux machine from your
written instructions, runs a benchmark case, gets the same result class, replays it, and cleanly
removes everything. **A demo on your laptop does not count.**

**Threat model** — an explicit statement of who might attack, what they could try, and what you
are and are not defending against. **Claiming security without one is not credible.**

**Research artifact** — the code and data a paper releases. Whether it is actually obtainable
and runnable is **a real risk, not a formality**.

**IDoFT** — the Illinois Dataset of Flaky Tests. **A catalogue of pointers, not a guaranteed
benchmark** — this is why dataset readiness is amber.

**FSE / ICSE / ICSE-NIER** — top-tier software engineering venues. **NIER** = New Ideas and
Emerging Results, publishing early work with smaller evaluations — relevant because Takuan's
13-case evaluation is NIER-scale.

---

## If you only have a week

1. **Run a real Maven project's tests locally and make one test fail by reordering.** Nothing
   here is intuitive until you have watched a suite run and changed its order yourself.
2. **Write two toy tests sharing a static field**, so one breaks the other. Swap the order and
   watch the failure vanish. *This makes victim/polluter/shared state permanent knowledge
   rather than vocabulary.*
3. **Learn confidence intervals for proportions**, then specifically Wilson. **Compute one by
   hand for 18/20.** This is the most commonly probed weak point.
4. **Learn baselines, ablations, controls, held-out sets and leakage.**
5. **Skim the RankF paper** for problem, method, dataset and metrics only. You must be able to
   describe your nearest competitor accurately in one minute.
