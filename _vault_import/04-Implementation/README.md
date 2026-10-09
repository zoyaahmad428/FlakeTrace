# Implementation

**Dormant until after proposal approval.** Nothing here yet, and correctly so.

When it starts, one note per major component, mapped to the architecture in
[[03-Design/architecture]]:

```
project-adapter.md
sandbox-runner.md
evidence-collector.md
evidence-store-graph.md
diagnosis-planner.md
minimiser-verifier.md
certificate-generator.md
cli-ci-adapter.md
cdr/                    (gated — only if Final-1 exit criteria are met)
```

## What each note must contain

Not "what I built" — the **four-point ownership standard** the panel applies:

1. **What it does and why it is there** — the component's role and the sub-problem it addresses
2. **Why it is built this way** — at least one alternative considered, and why it was rejected
3. **What breaks** — what fails if an input, assumption, dependency, requirement or scale
   changes, and what the system does when it fails
4. **How to modify it** — a specific change and what else must change with it

> A member who cannot do these four things does not own that component, **whatever the
> repository history shows**.

Write these as you build, not before the defence. Reconstructing a design rationale six months
later is how projects fail the ownership section.

## Existing POC tooling (already written, not product code)

| Component | Purpose | Lives |
| --- | --- | --- |
| `FtRunner.java` | Ordered execution, one fresh JVM per order, machine-readable outcome + normalised signature | POC bundle |
| `FtList.java` | Candidate enumeration without initialising classes | POC bundle |
| `extract_static.py` | `javap`-based getstatic/putstatic extraction with bytecode offsets | POC bundle |
| `step_scan.py` | Exhaustive `[candidate, victim]` scan | POC bundle |
| `step_analyze.py`, `step_replay.py` | Offline strategy replay; clean-container replay with Wilson intervals | POC bundle |

These are **experiment tooling, not the product**. Some ideas carry over (single-scan protocol,
`javap` over ASM, non-initialising enumeration); the code does not.
