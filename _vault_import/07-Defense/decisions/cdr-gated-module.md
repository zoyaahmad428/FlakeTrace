# Decision: Certificate-Driven Remediation as a gated module

**Date:** 4 September 2026 (Revision 2) · **Status:** `GATED` · **Owner:** Member 3 (secondary)

⚠ **This decision collides with an explicit exclusion in our own earlier guide. Expect the
panel to notice. See [[07-Defense/weak-points]] §5 — the wording must be consistent across the
slide deck, the proposal document and Revision 2 before the defence.**

---

## The apparent contradiction

Our original Stream B evaluation guide **removed automatic repair from committed scope**.
Revision 2 adds a remediation module.

## Why it is not actually a contradiction

**What was excluded:** *automatic source-code repair* — the system deciding on and applying a
fix.

**What CDR does:** consumes a **Verified** certificate and produces a ranked set of
remediation options with the evidence supporting each. **A human evaluates and applies.**
CDR does not modify source.

> **Never say "automatically fixing" — even informally. One such phrase and the panel will
> hold you to the stronger claim for the rest of the session.**

## The five constraints that keep it narrow

1. **Allowlisted patterns only**
2. **Verified certificates only** — never Candidate, never Unresolved
3. **Verified by re-execution** under the same repeated-replay contract as the diagnosis
4. **Ablatable** against a deterministic templated generator that uses no model and no network
5. **Gated** behind the committed core reaching its Final-1 exit criteria

## Why a module and not a feature

Because it depends on the certificate being trustworthy, which is a property the **core must
establish first**. A remediation suggestion built on an unverified diagnosis is *worse than
no suggestion* — it converts a weak inference into an actionable-looking instruction.

Making it a separate, gated module makes that dependency **structural rather than a matter of
discipline**.

It also keeps the removal test clean: **remove CDR and the product still delivers its
contribution.**

## The literature basis for gating it

This is not caution for its own sake — the automated-program-repair literature makes it
mandatory:

- **Qi et al.** analysed reported patches from three generate-and-validate systems and found
  the majority were **not even plausible**, with the overwhelming majority incorrect — often
  equivalent to a single modification deleting functionality. The infrastructure defect: patch
  evaluation checked the **process exit code rather than the output**.
- **Smith et al.** named the general phenomenon **overfitting** — a patch passing available
  tests but not generalising, because test suites are too weak to fully specify correct
  behaviour.
- **FlakyDoctor's** own loop validates every candidate patch by execution and re-prompts on
  failure rather than emitting unvalidated output.

> **Presenting a plausible patch as a correct one is the single most reproducible failure mode
> in this literature.**

This is also the direct source of our rule that failure equivalence is defined over a
**normalised failure signature, never the Maven exit code** — Qi et al. is the precise
historical precedent for that mistake.

## How CDR differs from iFixFlakies patch generation

iFixFlakies searches the suite for **cleaners** — existing tests whose execution restores the
polluted state — and synthesises a patch from them. Its structural limit, stated by its own
successors: cleaners are **not guaranteed to exist**.

CDR starts from the **certificate's resource path**, so its suggestions are indexed on the
specific resource written and read: *reset this static field in teardown, restore this system
property, isolate this filesystem path.*

> The honest comparison: iFixFlakies produces a candidate patch; we produce a targeted,
> evidence-linked recommendation. Where they overlap we report iFixFlakies as the comparator,
> and **if CDR does not add measurable value over it, that is a finding we publish rather than
> a module we defend.**

## If CDR does not ship

An optional extension and **nothing from the committed scope**. The member who owns it is not
left without evidence, because their committed ownership sits in the core — evaluation
infrastructure ([[07-Defense/ownership-map]]).

CDR is **first on the cut list** if we are behind at Final-1.

## Panel answer (Q82)

> The exclusion stands and CDR does not violate it. What we excluded was automatic
> source-code repair — the system deciding on and applying a fix. CDR does not modify source.
> It consumes a Verified certificate and produces a ranked set of remediation options with the
> evidence supporting each, which a human evaluates and applies.
>
> It is also gated: it is not part of the committed core and does not begin until the core
> pipeline reaches its exit criteria at Final-1. If the core is late, CDR does not ship and the
> project is still complete.
