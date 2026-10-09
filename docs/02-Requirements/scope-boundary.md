# Scope Boundary

*The committed / gated / excluded lists. Consistency across this file, the slide deck and the
proposal document is an approval condition — see [[07-Defense/weak-points]] §5.*

---

## Product boundary in one exchange (Q10)

**In:** a pinned Git commit · a Maven module · a target test · an optional known passing or
failing order · a fixed budget in wall-clock time and test-method invocations.

**Out:** a deletion-minimal replay order · a resource-event path · a repeated-run interval · a
replay command · provenance · stated limitations — **or an explicit unresolved certificate**.

**Committed environment:** Linux container · Maven Surefire · JUnit 4 (including JUnit 3
`TestCase` classes via the JUnit38 adapter).

**Committed resource families:** JVM static fields · Java system properties · filesystem paths.

**Everything else** — databases, networks, caches, services, threads, timing — is recorded as
**opaque or unsupported evidence, not diagnosed**.

---

## COMMITTED — diagnosis core

Maven module validation and test discovery · JUnit 4 support including JUnit 3 `TestCase` via
JUnit38 adapter · environment capture including container image digest · containerised runner
with ordered single-JVM execution, **one fresh JVM per order** · **execution-context fidelity**
for projects whose Surefire config runs suite classes · budget enforcement with a **reserved
verification split** · bounded resource collection for the three families · static bytecode
extraction of `getstatic`/`putstatic` with offsets · **configurable analysis depth** ·
attribution including `setUp`/`tearDown`/`<clinit>` · test–resource graph · candidate ranking ·
adaptive cost-aware search policy · deletion-minimisation with 1-minimality checks ·
counterfactual checks · failure-signature normalisation · repeated-run verification with Wilson
intervals · typed abstention · certificate generation · CLI with CI exit codes · clean Linux
install.

## COMMITTED — evaluation infrastructure

Frozen benchmark manifest with yield and exclusion reporting · independent baselines (seeded
random, one-by-one, iFixFlakies, RankFO, oracle ceiling) · **ablation harness including the
depth sweep** · metrics and statistics layer · controlled fixture suite · one-command
reproducibility bundle.

## COMMITTED — safety

Rootless containers · network disabled during test execution · capabilities dropped ·
CPU/memory/PID/time limits · redaction of paths, usernames and credentials before logging or
export · full audit of commands, image digests and input commits.

## SUPPORTING

Certificate explanation chain with evidence labels · failure-signature explorer · local
read-only evidence graph view · HTML report · resource-coverage reporting · caching · case
status tracking · plain-language explanation mode · policy engine · audit export.

## GATED — Certificate-Driven Remediation

Enabled **only** after ranking quality and explanation correctness meet acceptance thresholds
on held-out projects, and after the committed core reaches its **Final-1 exit criteria**.

Certificate-to-repair-context transformation · certificate-directed code retrieval · repair
playbook library · deterministic recommendation layer · **templated patch generator (mandatory,
no model, no network)** · optional certificate-conditioned LLM generator, **ablatable against
the templated one** · structured repair plan with abstention · unified diff with human approval
· five-condition verification contract · suppression detector · regression detection · repair
statuses.

See [[07-Defense/decisions/cdr-gated-module]].

## GATED — other optional tier

JUnit 5 adapter · Gradle support · GitHub Checks presentation · issue-tracker export · history
dashboard · database and network resource adapters.

**Each is gated on the committed core reaching Final-1 exit criteria** — a working end-to-end
path from project input to certificate, with the baseline measured.

## STRETCH

Regression-test generation from a verified repair · EvoSuite coverage of the polluted class,
one demonstration case.

## EXPLICITLY EXCLUDED — removed from the promise entirely

- Generic flaky-test **detection** as the contribution
- Multiple languages · Python support · multiple build systems
- **Claims of definitive causality**
- Unconstrained automatic repair
- Hosted analytics dashboard
- Team case inbox and collaboration features
- IDE plugins
- Natural-language query
- Cross-project correlation
- Broad database or network tracing
- **Safe multi-tenant execution** (explicitly not claimed)

---

## Why JUnit 5 is conditional, in 2026 (Q12)

> It is a real limitation and we state it. JUnit 4 is guaranteed first because Surefire
> discovery, test-boundary attribution and the public benchmark cases are all well understood
> there — **the reproducible OD corpora are predominantly JUnit 4 Maven projects.** JUnit 5
> becomes committed only after we verify that discovery and instrumentation attribute events to
> the correct test boundaries under the Jupiter engine.
>
> Committing to it now would be the kind of promise the guide asks us to remove from committed
> scope.

*Reinforced by the POC: all eight cases turned out to be **JUnit 3**, which is why the JUnit38
adapter path is validated rather than assumed.*

## If we are behind at Final-1 (Q98) — the cut order

1. **CDR** — first out
2. **Filesystem resource evidence** — reduced to an adapter or opaque event
3. **Adaptive policy** — reduced; ranked one-by-one ships as default, adaptive policy reported
   as an evaluated prototype

**The committed core end-to-end path is the last thing cut, because it is the project.**

> Any of those is a **recorded scope change requiring supervisor approval before it is acted
> on**. The guide treats deferral as acceptable when justified and recorded, and **silent
> removal as not**.
