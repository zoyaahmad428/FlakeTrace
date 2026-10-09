# FlakeTrace — FYP Vault

Obsidian vault for **FlakeTrace: budget-aware, evidence-certified diagnosis of order-dependent
Java test failures**.
FAST School of Computing · Stream B · Three members · Two semesters.

**Current phase:** FYP-1 Iteration 1 → **Mid Evaluation (12–16 Oct 2026)**. Proposal approved
with minor modifications. This vault now lives in the project repository as `docs/` — open
this folder in Obsidian. Changes go through a branch and PR like code.

---

## Start here

| If you want to… | Open |
| --- | --- |
| **Know what the Mid Evaluation needs** | [[08-MidEval/README]] |
| **See the panel's required changes and their status** | [[08-MidEval/panel-action-register]] |
| **Know how we work together / direct our AI agents** | [[09-Team/working-agreement]] · [[09-Team/claude-guide]] |
| **Know how the components connect** | [[contracts/interfaces]] · [[contracts/report-schema]] |
| Understand the project in 5 minutes | [[00-Meta/project-one-pager]] |
| Read one page before walking into the room | [[07-Defense/one-minute-answers]] |
| Know what we may and may not claim | [[07-Defense/claims-ledger]] |
| Know what will hurt us | [[07-Defense/weak-points]] |
| Prepare for the panel | [[07-Defense/question-bank-working]] |
| Know who answers what | [[07-Defense/ownership-map]] |
| Look up a term | [[00-Meta/glossary]] |
| Build the slides (official 10-slide structure) | [[07-Defense/slide-structure]] |

## Folder map

```
00-Meta/          one-pager · glossary · stream & status · stakeholder evidence
                  risk register · roadmap · AI usage log
01-Literature/    per-paper notes · comparison table · parameter provenance
                  references · commercial tools · prior FYP comparison
02-Requirements/  functional · non-functional · scope boundary
03-Design/        architecture · certificate contract
04-Implementation/ per-component notes (code lives in runner/ evidence/ eval/)
05-Testing/       POC evidence · evaluation plan · fixture suite
06-Meetings/      dated notes; decisions get promoted to 07-Defense/decisions/
07-Defense/       claims ledger · decisions · question bank · weak points
                  ownership map · rehearsal log · slide structure · one-minute answers
08-MidEval/       requirements · panel action register · iteration plan · demo plan
                  GenAI register
09-Team/          members · working agreement · Claude guide
contracts/        interfaces · report schema (shared, change needs all three)
evidence-mN.md    per-member evidence of what was actually run
genai-log-mN.md   per-member GenAI session logs
attachments/      architecture diagram · Gantt chart
```

## The one rule that makes this vault work

> **Nothing goes in a defence answer that is not in the claims ledger with a source.**

If you make a claim in a meeting, in a slide, or to the supervisor, it gets a row in
[[07-Defense/claims-ledger]] with its backing and its status. If it has no backing, its status
is `OPEN` or `ASSUMPTION` — and it is **said that way** to the panel, never asserted.

A supervised panel forgives an open item far more readily than a fabricated closure.

## Status legend

| Tag | Meaning |
| --- | --- |
| `EXECUTED` | We ran it and hold the evidence |
| `COMMITTED` | We undertake to deliver it |
| `GATED` | Delivered only if named preconditions are met |
| `PROPOSED` | Design only, not implemented |
| `POLICY` | Our choice, not a published finding — defend it **as a choice** |
| `FROZEN` | Pre-registered; cannot change without recorded approval |
| `OPEN` | Known gap, no closure yet — say so, do not bluff |
| `ASSUMPTION` | Believed but unevidenced — must be labelled as such aloud |

## What needs doing before the defence

**Cheap and dangerous if left — do these first:**
1. Reconcile the victim/brittle vs reproduction-count wording *(M3)* — [[07-Defense/weak-points]] §4
2. Audit CDR wording across slide deck, proposal doc and Rev 2 *(joint)* — §5

**Highest value, needs the supervisor:**
3. **One Java/Maven practitioner on record** — §1, Dossier decision 5
4. Confirm three-member departmental approval — §8, Dossier decision 1

**The five POC items** *(three run offline against data already held)*:
depth sweep *(M1)* · per-case cause classification *(M1)* · oracle ceiling and alternative
rankings *(M3)* · out-of-domain subject *(M3)* · non-perturbation check *(M2)*.
Detail in [[05-Testing/poc/what-changed]].

**Then:** three rehearsal passes — [[07-Defense/rehearsal-log]].

## Working with this vault

- **Pull before you write, push when you stop.** Don't let the vault sit unpushed overnight.
- **One person per file per session** where possible — that's what avoids merge conflicts.
- Decisions made in a meeting get **promoted** the same day: a ledger row, or a file in
  `07-Defense/decisions/`. A decision that lives only in a meeting note is one you will not be
  able to defend.
