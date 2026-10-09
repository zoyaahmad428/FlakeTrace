# Weak Points — the honest list

*The panel will find these. Better that we found them first and have an answer ready.*

Ordered by **how much damage they do if discovered rather than disclosed.**

---

## 1. Our stakeholders do not use Java — CRITICAL

**The gap.** Three practitioner interviews are complete and substantive. None of the three
uses our target ecosystem:

| Stakeholder | Stack | Their OD instance |
| --- | --- | --- |
| Mahad Sheikh, CEO, Inspirovix | Python/pytest, JS/TS/Jest, GitHub Actions | Shared state, env vars, leftover DB records |
| Engineering Lead, Trillet AI | Node.js/Vitest, React/TS/Vitest | Record created without cleanup → conflict for next test |
| Full-stack engineer, Learnsignal | TypeScript, Vitest (~5,500 tests), Playwright | Staging-DB pollution across 9 shared test profiles |

**Not one uses Java, Maven, JUnit or Surefire.** Our committed product is Java/Maven/JUnit-only,
and our three resource families (JVM static fields, Java system properties, filesystem paths)
are JVM concepts. The polluted state our stakeholders actually describe is mostly **database
rows on a shared staging instance** — which is in our *explicitly excluded* list.

**Why the panel will hit this.** Stream B's whole obligation is that real practitioners have
*this* problem. A panel reading the interviews will ask: "these people have a problem you
have scoped yourself out of solving."

**The answer — do not soften it:**

> The interviews validate the *problem shape*, not the *technology scope*, and we separate
> those deliberately. Every one of the three independently described manual binary-search
> isolation with no tooling support, all three said a confident wrong answer is worse than a
> stated unknown, and two said source cannot leave their infrastructure. Those are the three
> design commitments the product is built on — budget, typed abstention, self-hosting — and
> they are ecosystem-independent.
>
> What the interviews do **not** establish is that Java teams specifically have this problem,
> and we do not claim they do on this evidence. That claim rests on the published record:
> IDoFT's OD catalogue, RankF's 155 reproduced OD tests across 24 Java projects, and
> iFixFlakies' Java corpus. Java is where the *reproducible public evidence* is, which is why
> the benchmark and the product are Java.

**Follow-up we should expect:** *"Then why not build it for pytest, where your stakeholders
are?"*

> Because the diagnosis method depends on JVM-level facts — bytecode `getstatic`/`putstatic`,
> class-loader-resolved field identity, single-JVM execution semantics under Surefire — and
> because the only public corpora with labelled OD-relevant ground truth are Java. A pytest
> port is a legitimate future direction (iPFlakies did exactly this for Python) but it is a
> different resource abstraction, not a configuration flag.

**Closure action:** get **one Java/Maven practitioner** on record before the defence. Even a
single 30-minute conversation moves this from OPEN to SETTLED. This is Dossier decision 5 —
ask the supervisor for an introduction. *Priority: highest of anything on this list.*

---

## 2. The POC's central hypothesis failed — and one case is carrying the recovery

**The gap.** Zero overlap at depth 1, 0% saving against a 30% gate. The recovery argument
rests on **FJ-02 moving rank 39 → 1 at depth 2**. The other three reproduced cases did not
move at any depth tested.

**Do not say:** "the results were mixed" or "inconclusive." It was a clean, interpretable
negative, and its interpretability is what makes it useful.

**The answer:**

> One case is not a result and we do not present it as one. We present it as a *diagnosis of
> why the gate was missed* and as justification for exactly one design decision: analysis
> depth becomes a configurable, committed parameter and an axis of the evaluation. Whether
> depth two works is RQ1, measured across the frozen benchmark.

**Closure action:** the depth sweep (depths 1, 2, 3, unbounded × 4 cases, reporting rank
**and** overlap-set size) runs offline against data we already hold. It replaces a
single-case ablation with a 4×4 matrix. *Priority 1 of the five outstanding items.*

---

## 3. Single-project evidence

**The gap.** All four reproduced cases came from **fastjson**. jsoniter returned zero. Our
own setup required cases from at least two projects.

Compounding it: both subjects are **JSON libraries built around global static configuration** —
the most favourable possible substrate for a static-field hypothesis. We failed on the
friendliest possible ground.

**The answer:** state it before being asked. It is currently single-project evidence, we
know it, and the out-of-domain subject (non-JSON, one case, hard-capped effort) is priority
4 of the pre-defence items. If it fails to reproduce, we state the limitation rather than
hide it.

---

## 4. Internal inconsistency in our own POC numbers — FIX BEFORE THE DEFENCE

**The gap.** Isolation classified **6 victims / 2 brittle**. Reproduction reports **4 cases,
all fastjson**. But two fastjson targets were classified *brittle* during isolation. These
two statements have not been reconciled in the write-up.

**This is the single most dangerous item on the list**, because it is the kind of thing a
panel finds by reading two of our own slides. The underlying data exists; only the summary
wording is imprecise.

**Closure action:** reconcile the wording against the evidence bundle **before quoting any
POC figure externally**. Assign to M3. Until it is fixed, do not put both numbers on the
same slide.

---

## 5. Our own documents may contradict each other on repair

**The gap.** The original evaluation guide **excluded automatic repair from scope**.
Revision 2 added the CDR module. If the slide deck, the proposal document and Rev 2 word
this differently, the panel will pursue the inconsistency far harder than they would pursue
a gap we named ourselves.

**The defence (and it is a good one):** what was excluded is *automatic source-code repair* —
the system deciding on and applying a fix. CDR does not modify source. It consumes a
**Verified** certificate and produces ranked remediation options with supporting evidence,
which a human evaluates and applies. It is gated behind the core reaching Final-1 exit
criteria.

**Never say "automatically fixing"** — even informally. One such phrase and the panel holds
you to the stronger claim for the rest of the session.

**Closure action:** audit all three documents for consistent wording. Joint. Before slides
are built.

---

## 6. We have not run the baseline tools

**The gap.** iFixFlakies, RankFO, Takuan are named as baselines. We have not yet run any of
them. Q20 in the question bank asks exactly this.

**Do not say** you have "studied" a tool if you mean you read the paper. Panels ask what
version you built and what broke.

**The answer:** state honestly what was run during the POC (our own harness, not the
baselines), that baseline integration is scheduled for FYP-I early, and that baseline
measurement is an explicit **Final-1 exit condition** — not an aspiration.

---

## 7. Dataset is amber and we say so deliberately

**The gap.** IDoFT is a living *catalogue* — project URLs, commits, modules, tests,
categories. It is not proof that cases build, contain resource-level ground truth, or are
legally redistributable.

**Do not say** the dataset is ready because it exists. That is the specific overclaim the
evaluation guide flagged for correction from green to amber.

**The answer:** reproducibility filtering *is* the work, and the evidence is public — RankF
began with 249 OD tests and retained 155 after confirming reproducibility. Tufano et al.
found only 38% of Maven project history compilable. Our own build-and-reproduce yield is a
**measured quantity we will publish**, including exclusions, not an assumption.

---

## 8. Three-member approval not confirmed

**The gap.** Team expanded 2 → 3 with evaluation infrastructure as the third pillar.
Departmental approval is pending (Dossier decision 1).

**Why it matters:** a scope written for three against a roster of two is worse than a
narrower scope written for two.

**The answer:** the scope grew by exactly one pillar — the committed core (resource
families, build system, language, certificate contract) is unchanged from the two-member
boundary. If approval does not come, CDR drops first and the evaluation pillar redistributes.

---

## 9. Instrumentation overhead has no number

**The gap.** Our headline measurable NFR is median/p95 instrumentation overhead — with no
threshold value yet.

**This is deliberate and defensible:** "We are not inventing a final overhead figure before
we measure it." We have stakeholder-derived bounds (5–15 min PR-acceptable per SH1; 30 min
tolerable opt-in/nightly per SH3) and literature-derived context (ElectricTest ~20×,
PolDet-on-JPF 1.43×).

Say it as a deliberate omission with a measurement procedure attached, not as an oversight.

---

## 10. Things we genuinely have not thought about

*Q109 asks this. Do not perform humility — name something real and small.*

- How the certificate handles a case where **the target test is itself the polluter for a
  later test** — our current input model does not represent it.
- **Retention policy defaults** for evidence bundles containing redacted source paths.

Both are recorded as open items rather than resolved.

---

## Quick reference: what closes before the defence

| # | Item | Owner | Effort |
| --- | --- | --- | --- |
| 4 | Reconcile victim/brittle vs reproduction wording | M3 | Hours — do this first |
| 5 | Audit CDR wording across 3 documents | Joint | Hours |
| 2 | Depth sweep, 4×4 matrix, offline | M1 | Days, no re-scanning |
| — | Per-case cause classification for 3 non-moving cases | M1 | Days, offline |
| — | Oracle ceiling + alternative rankings, offline | M3 | Days, offline |
| 3 | One out-of-domain subject | M3 | Days, hard-capped |
| — | Non-perturbation check (10× instrumented vs unmodified Surefire) | M2 | Days |
| 1 | **One Java/Maven practitioner interview** | Joint | Ask supervisor now |
| 8 | Three-member departmental approval | Joint | Ask supervisor now |
