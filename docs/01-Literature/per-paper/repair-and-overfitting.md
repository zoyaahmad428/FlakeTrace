# Repair literature and why CDR must be gated

*The automated-program-repair literature supplies the strongest available argument for gating
any remediation behind verification. This is the evidence base for
[[07-Defense/decisions/cdr-gated-module]].*

---

## The repair systems

| System | What it does | Our position |
| --- | --- | --- |
| **iFixFlakies** [4] | Synthesises patches from existing helpers (cleaners for victims, state-setters for brittles) | **Repair baseline.** Structural limit stated by its own successors: **cleaners are not guaranteed to exist** — it relies on developers having already written the cleaning logic |
| **ODRepair** — Li, Zhu, Wang, Shi (ICSE 2022) [7] | Addresses exactly that limit by **generating** the required cleaning code rather than harvesting it | **Repair baseline** where runnable |
| **FlakyDoctor** — Chen, Jabbarvand (ISSTA 2024) [8] | Neuro-symbolic: LLM generality + program analysis. **873 confirmed flaky tests (332 OD, 541 ID) from 243 real projects. 57% success on OD, 59% on ID.** Beat ODRepair by 12%, iFixFlakies by 17% on OD | **Repair baseline.** Establishes **LLM repair is not itself novel** |
| **iPFlakies** [35] | Ports detect-and-fix to Python | Precedent for cross-ecosystem porting being a *separate* abstraction |
| **FlakeSync** [41] | Targets async, not order-dependent, flakiness | Out of scope |

### Two FlakyDoctor findings that matter architecturally

1. **The non-LLM components contribute 12–31% of overall performance** — which the authors
   state as evidence that **LLMs alone are not good enough to repair flaky tests in real-world
   projects.** *(Directly supports our templated-generator-mandatory, LLM-optional-and-ablatable
   design.)*
2. **Its loop is:** generate → compile-check → **validate by execution** → re-prompt with the
   unresolved issue, terminating after a fixed number of iterations. *(Precedent for our
   verification contract.)*

---

## Plausible is not correct — the core argument

### Qi, Long, Achour, Rinard (ISSTA 2015) [26]

Analysed the reported patches of three generate-and-validate repair systems. Found that
**because of errors in the patch evaluation infrastructure, the majority of reported patches
were not even plausible** — they did not produce correct outputs for the inputs in the
validation suite — and that **the overwhelming majority were not correct**, being equivalent to
a single modification that **deletes functionality**.

> **The specific infrastructure defect they identify: patch evaluation checked the PROCESS EXIT
> CODE rather than the OUTPUT.**

### Smith, Barr, Le Goues, Brun (ESEC/FSE 2015) [27]

Named the general phenomenon **overfitting**: a patch that passes the available tests but does
not generalise, arising because **test suites are too weak to fully specify correct behaviour.**

---

## The two direct consequences for FlakeTrace

### 1. Failure equivalence must never be defined over the exit code

> Failure equivalence must be defined over a **normalised failure signature** — exception type,
> failing assertion after redaction, and the stable portion of the stack trace within the
> project's own packages — and **never over the Maven process exit code.**
>
> **The Qi et al. finding is the precise historical precedent for that mistake.**

**A timeout, a compilation error and a container OOM must NOT be counted as reproductions of an
assertion failure.** A test failing for an unrelated reason also exits non-zero, and counting
that as reproduction would **inflate every success metric we report.**

*(This is also written into our frozen POC definitions.)*

### 2. Any CDR capability must be strictly downstream of a Verified certificate

- **strictly downstream** of a Verified certificate
- **validated by execution** under the same repeated-replay contract used for the diagnosis
- **presented as a non-authoritative suggestion**, not an accepted fix

> **Presenting a plausible patch as a correct one is the single most reproducible failure mode
> in this literature.**

The certifying-algorithm model reinforces it: **the user, not the tool, performs the final
check.**

---

## How CDR differs from iFixFlakies patch generation (Q84)

> iFixFlakies searches the suite for **cleaners** — existing tests whose execution restores the
> polluted state — and synthesises a patch from them. CDR starts from **the certificate's
> resource path**, so its suggestions are indexed on the specific resource written and read:
> reset this static field in teardown, restore this system property, isolate this filesystem
> path.
>
> The honest comparison is that iFixFlakies produces a **candidate patch** and we produce a
> **targeted, evidence-linked recommendation**. Where they overlap we report iFixFlakies as the
> comparator, and **if CDR does not add measurable value over it, that is a finding we publish
> rather than a module we defend.**
