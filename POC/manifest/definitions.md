# Frozen definitions - FlakeTrace POC
Frozen: 2026-08-25, before any experimental run. Solo execution.

## Candidate set
All test methods in the victim's Maven module. JUnit 3 subjects: a test method
is a public no-arg method named test* in a junit.framework.TestCase subclass.
If the module exceeds 300 such methods, restrict to the victim's package and
record the cap as a declared POC limitation.

## OD-relevant test (polluter)
A candidate c such that [c, v] executed in a single JVM produces the target
failure signature for victim v, while [v] alone passes.

## Failure signature
(exception FQCN, normalised first line of message, topmost stack frame inside
the project package). Digits, hex addresses, paths and timestamps masked.
A timeout, compilation error or OOM is NOT the same reproduction as the
intended assertion failure.

## Confirmation and cost unit
One confirmation = one execution of one candidate order.
Primary cost unit = test-method invocations, not Maven launches.

## Reproduced case
Victim passes alone >=10/10 AND fails with the matching signature in >=9/10
replays of the confirmed polluting order.

## Resource identifier (POC scope)
ownerInternalName.fieldName:descriptor, static fields only (GETSTATIC /
PUTSTATIC), direct references plus one hop into project-owned callees.
Attribution per test method includes the method itself, the class's setUp()
and tearDown(), and the class's <clinit>. Reflection, filesystem, system
properties, network and database state are OUT OF SCOPE and recorded as
UNSUPPORTED, never as zero-overlap.

## Single-scan protocol
The exhaustive [c, v] scan is run ONCE per case. Ground truth, the OBO
baseline, the random baselines (5 seeds) and the resource-ranked strategy are
all computed offline from that one outcome table. No strategy triggers a re-run.
