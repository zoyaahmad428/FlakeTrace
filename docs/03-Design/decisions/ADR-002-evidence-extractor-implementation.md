# ADR-002 — Resource evidence extractor: fresh Python/javap implementation, default depth 2

**Date:** 2026-10-09 · **Status:** `PROPOSED`, needs agreement from M1, M2 and M3 ·
**Owner:** M1 (evidence)

## Context

[[03-Design/decisions/ADR-001-iteration1-evidence-without-instrumentation]] fixes
*what* Iteration 1 evidence is: static `getstatic`/`putstatic` and
`System.setProperty`/`getProperty` call sites read from compiled classes with `javap`.
Two choices are left open:

1. **How to build the extractor.** The August POC has a working javap extractor
   (`POC/src/extract_static.py`). [[04-Implementation/README]] and `evidence/README.md`
   say its *idea* carries over but its *code* does not. It also lacks what Iteration 1
   needs: JUnit 4 annotations, inherited lifecycle methods, system properties, call
   paths, and unsupported-case reporting.
2. **The default analysis depth.** [[07-Defense/decisions/depth-configurable]] makes
   depth a configurable parameter but does not fix a default. Fixture F2's victim
   reads its property inside `FeatureFlags.isTurboEnabled()`, one call below the
   test method (`evidence/javap-dumps/phase1-f1-f2.txt`).

## Decision

1. **Write `evidence/extract.py` fresh** in Python 3 (standard library only). It runs
   `javap -c -p` (and `-v` for annotations) from a JDK 8+ and parses the text. The POC's
   regexes are a reference only; no POC code is copied. Invocation and output:
   [docs/contracts/resource-evidence.md](../../contracts/resource-evidence.md).
2. **Default `--depth 2`**, accepted values 1–3.

## Alternatives considered

| Option | Why not |
| --- | --- |
| (a2) Copy the POC's `parse_dump` and regexes with attribution | Contradicts the team docs ("code does not carry over"), and Member 1 must be able to explain every line without AI. |
| (b) Java tool using ASM | ASM's visitor API does not expose instruction offsets without a workaround, and offsets are the core evidence. It also adds a Maven module and a dependency. Javassist or BCEL give offsets, but they are also new dependencies. |
| Default depth 1 | F2 has no edge, so the Mid demo would need `--depth 2` typed out. |
| Default depth 3 | More time and more over-approximation, with no evidence yet that it is needed on the fixture. |

## Consequences

- F2 resolves at the default depth. The depth sweep still reports 1, 2 and 3.
- Depth 2 equals the POC's frozen scope ("direct references plus one hop"). **Numbering
  differs:** the POC counts hops, so POC "depth N" (`FT_HOPS=N`) is depth N + 1 in our
  contract. Any POC or vault figure quoted at "depth 2" (e.g. FJ-02's rank 39 → 1 in
  [[07-Defense/decisions/depth-configurable]] and the claims ledger, C6/C7) is depth 3
  in our numbering. These docs need a wording check before the Mid report quotes them.
- Over-approximation grows with depth. The outcome logic already requires reproduction
  statistics **and** an edge before `VERIFIED` (ADR-001), so a static edge alone cannot
  overclaim.
- Parsing javap text is the main fragility. It will be guarded by tests on real JDK 8
  javap output.

## Agreement

| Member | Agree? | Comment |
| --- | --- | --- |
| M1 | ☐ | |
| M2 | ☐ | |
| M3 | ☐ | |
