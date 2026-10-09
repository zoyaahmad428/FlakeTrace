# Working agreement

*Agreed by: M1 ☐ · M2 ☐ · M3 ☐ — tick when you have read it. Changes go through a PR.*

## 1. One repository, one source of truth

- Everything lives in this repo: code, contracts, design notes, evidence, report sources.
- `docs/` is the Obsidian vault. Open the `docs/` folder in Obsidian; edit notes there; commit
  through a branch like any other change.
- The old `FlakeTrace-Vault` repo is **archived** (read-only) once this restructure merges.
- The claude.ai project "FlakeTrace – FYP" holds the university's documents (handbook,
  rubrics, templates). It is reference material; if it conflicts with this repo, the repo wins
  for our own decisions, the university documents win for requirements.

## 2. Stay in your lane, meet at the contracts

- Each member owns folders (see [[09-Team/members]]). Others may read, run and review them,
  but changes go through the owner.
- The three areas connect only through [[contracts/interfaces]] and [[contracts/report-schema]].
  Contracts change only with all three approvals.
- If you need something from another member's area, open a GitHub issue assigned to them
  instead of editing their code.

## 3. Git and review

- Branch → PR → CI green → one teammate approves → merge. Details in `CONTRIBUTING.md`.
- **Review within 24 hours** of being asked during the Mid Eval week. A review must contain a
  real comment or question — reviews are graded evidence.
- Pull `main` before starting work each day, and rebase your branch if `main` moved.

## 4. Honesty rules

- No invented numbers, ever. "Not yet run" is a valid, respectable status.
- Mocked, hardcoded or fake parts are labelled in code and in the demo plan.
- Every claim that will be said to the supervisor goes in [[07-Defense/claims-ledger]] with its
  backing.

## 5. Each member owns their own understanding

The evaluation questions each member alone and may ask for a small code change **without AI**.
Therefore:

- You must be able to explain every file in your folder without reading it, name one
  alternative you rejected, one failure case, and how you would modify it.
- After an AI session, spend time reading what was produced until you could rewrite it.
- Record what the AI got wrong — the guide asks for at least one rejected or corrected
  suggestion per member.

## 6. Communication

- Decisions made in chat or in person are written into a meeting note in `06-Meetings/` the
  same day, and promoted to a decision file if they would survive a "why?".
- Blockers are posted immediately, with who is blocked and since when.
- Daily during the Mid Eval week: a two-line update in the team chat — done / next / blocked.
