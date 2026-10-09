# Frozen definitions v2 - FlakeTrace POC
Frozen: 2026-09-04, BEFORE the out-of-domain (ormlite) results were analysed.
Supersedes definitions.md (v1, frozen 2026-08-25). v1 is retained unchanged;
its result stands as the pre-registered outcome of the first POC iteration.

## Status of this document
v1 was frozen before any run and returned a NEGATIVE result at its resource
scope. v2 amends the definitions in response to that finding. Two of the
amendments (A3, A4) were chosen by inspecting the fastjson cases, which are
therefore the DEVELOPMENT set and may not be used as evidence for them.
The ormlite-core cases are the HELD-OUT set: they were selected, built and
scanned before this document was written, and their outcome tables had not
been analysed at the time of freezing.

---

## Amendments over v1

### A1. Execution-context fidelity (applied retroactively in v1, disclosed)
Every order must be executed inside the project's DECLARED Surefire execution
context, including suite classes, fork policy and category filters. A harness
that runs test methods outside that context is invalid, and outcomes it
produces are HARNESS ARTIFACTS, not order dependence.
Evidence: jsoniter's Surefire runs five suite classes with reuseForks=false;
ignoring them fabricated 182 of 210 "polluters" with one identical LinkageError.

### A2. OD direction is classified, never fixed
A target that fails in isolation is BRITTLE (it requires a state-setter), not a
broken environment. Direction is determined empirically from 10 isolation runs:
  10/10 pass -> VICTIM;  10/10 fail with one stable signature -> BRITTLE;
  anything else -> UNSTABLE (excluded).
No environment change may be made that alters isolation behaviour without being
recorded as a deviation with justification.
Evidence: forcing TZ=Asia/Shanghai made a state-setter's write a no-op and
erased the order dependence under measurement.

### A3. Resource scope: declared depth 2  [selected on the development set]
The resource scope is transitive intra-project callee reachability to depth 2,
replacing v1's "direct references plus one hop". Depth is declared and its
extraction cost reported. Depth 1 is retained as a mandatory ablation.
Sweep evidence (results/depth_sweep.csv): depth 1 yields zero discrimination;
depth 2 is the optimum; depths 3 and 4 are WORSE, because deeper expansion adds
noise faster than signal. Depth is therefore a tuned parameter with an interior
optimum, not a "more is better" knob.

### A4. Ranking score: lexicographic  [selected on the development set]
    primary   |writes(c) INTERSECT reads(v)|
    secondary |touches(c) INTERSECT reads(v)|      touches = reads UNION writes
Rationale: a putstatic-only model is structurally blind to pollution that flows
through mutation of state reachable FROM a static reference (e.g. mutating the
object held in a static ThreadLocal). The secondary term recovers those cases
without discarding the stronger write->read evidence, which stays primary.

### A5. Cause classification is mandatory per case
Every reproduced case is classified from evidence about its CONFIRMED
OD-relevant candidates:
  A  DIRECT-PUTSTATIC  a confirmed candidate PUTSTATICs a field the target
                       reads, within the declared depth.
  B  VIA-STATIC-REF    no such putstatic, but a confirmed candidate TOUCHES a
                       static the target reads: pollution flows through a
                       static reference.
  C  UNSUPPORTED       no shared static at any swept depth. Reported as
                       UNSUPPORTED - never as evidence that no cause exists.
A case classified C must not be counted against ranking quality; it is outside
what the resource model can express, and is reported in the coverage account.

### A6. Random is a mandatory baseline
Claims must beat BOTH original-order one-by-one (OBO) and seeded random
ordering. OBO alone is a weak baseline: on alphabetically clustered suites it
can place relevant candidates systematically late, and random beat it on three
of four v1 cases without any guidance at all.

---

## Carried over unchanged from v1
Candidate set and the >300 package restriction; failure-signature equivalence
and its masking rules; confirmation and cost unit (test-method invocations);
the reproduced-case rule (>=10/10 alone, >=9/10 replay of the confirmed order);
resource identifier format (ownerInternalName.fieldName:descriptor, static
fields only, GETSTATIC/PUTSTATIC); the single-scan protocol; and the treatment
of reflection, filesystem, system properties, network and database state as
UNSUPPORTED rather than zero-overlap.

## Pre-registered prediction for the held-out set
If A3 and A4 generalise beyond the development set, then on the ormlite-core
cases the LEX score at depth 2 should place a confirmed OD-relevant candidate
within the top-20% of the candidate set for the majority of reproduced cases,
and should not be worse than OBO. If it is not, A3/A4 are overfitted to
fastjson and must be reported as such.
