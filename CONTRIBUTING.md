# Contributing to FlakeTrace

The supervisor evaluates this repository as evidence of industry practice: meaningful
branches, automated tests, reviewed pull requests and visible individual ownership. These
rules make that evidence appear naturally from normal work.

## Branches

| Branch | Use |
| --- | --- |
| `main` | Always passing CI. Protected: no direct pushes, PR + 1 approval + green CI |
| `m1/<topic>`, `m2/<topic>`, `m3/<topic>` | A member's feature work, e.g. `m2/order-runner` |
| `docs/<topic>` | Docs, report and Mid Eval evidence changes |
| `chore/<topic>` | Repo setup, CI, tooling |

One branch per piece of work. Keep branches short-lived (merge within a few days) so the
three areas do not drift apart.

## Commits

**Every commit is made by a member, never by an AI agent.** Agents write code and docs, then
stop and give you the exact commands (see `CLAUDE.md` §3). You read `git diff --staged`,
then run the commit and push yourself.

**Before your first commit on any machine**, make sure your commits are credited to you:

```bash
git config user.name  "Your Name"
git config user.email "the-email-on-your-GitHub-account"
```

If GitHub shows your commits with a grey avatar, that email is not on your account: add it
under GitHub → Settings → Emails.

**When to commit:** after each logical unit of work that is finished and verified — a
function plus its test, a fixed bug, one doc section. Not one giant commit per day, and not
half-finished work.

**Message format:**

```
[M2] runner: run an explicit ordered list of tests in one JVM      ← title, ≤72 chars

Implements OrderRunner.run_ordered from eval/baseline.py: one fresh   ← what and why
JVM per call, tests executed in exactly the given order.

Verified: python3 -m unittest runner.tests.test_order_runner -> OK   ← real command + result
Refs: W6                                                              ← work package / issue

Co-Authored-By: Claude <noreply@anthropic.com>                        ← if AI helped materially
```

- Title prefix: the member who did the work (`[M1]`, `[M2]`, `[M3]`, or `[ALL]` for joint
  work), then the area (`runner`, `evidence`, `eval`, `fixtures`, `ci`, `docs`, `contract`,
  `report`), then an imperative summary.
- Stage files by name; avoid `git add .` so unrelated files never sneak in.
- The commit includes the docs it affects (evidence log, iteration plan, README …).
- Bad: `update`, `wip`, `fixes`. Good: `[M3] eval: reject n=0 in wilson_interval with a clear error`.
- Do not squash away history when merging: use **"Create a merge commit"** or
  **"Rebase and merge"** so each member's individual commits remain visible.

## Pull requests

1. Push your branch and open a PR into `main`. Fill in the template.
2. CI must pass.
3. **Another member reviews and approves.** The reviewer actually runs or reads the change and
   leaves at least one real comment or question. Reviews are graded evidence of team practice.
4. A PR that changes anything in `docs/contracts/` or `eval/schema/` needs approval from
   **both** other members, and the PR description says so.

## Tags and releases

- `mid-eval-v1` — the exact version demonstrated at the FYP-1 Mid Evaluation. Created by the
  integration owner (Member 2) after the final PR is merged, at least 48 hours before the
  meeting. Recorded in the evidence worksheet.
- Later: `final-1`, `mid-2`, `final-2`.

## Evidence every member keeps up to date

| File | What goes in it |
| --- | --- |
| `docs/evidence-m<N>.md` | Requirement → file/function → command → real result → limitation |
| `docs/genai-log-m<N>.md` | Per session: asked, kept, changed, verified, rejected |
| `docs/09-Team/members.md` | Your current task and its state |

## One-time GitHub setup (repository admin)

1. **Settings → Branches → Add branch protection rule** for `main`:
   - Require a pull request before merging, with **1 approval**
   - Require status checks to pass: `python-eval`, `fixture-build`
   - Do not allow bypassing the above settings
2. **Settings → Collaborators:** all three members have **Write** access.
3. **Settings → General → Pull Requests:** allow merge commits and rebase merging.
4. Optional: install the Claude GitHub App on this repository so members' Claude sessions can
   push branches and open PRs.
