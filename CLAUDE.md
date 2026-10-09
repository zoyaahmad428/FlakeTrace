# CLAUDE.md — rules for every AI agent working in this repo

You are helping one member of a three-person Final Year Project team (FAST-NUCES Islamabad,
project **F26-214 FlakeTrace**). The supervisor grades this repository directly: its commit
history, branches, CI, tests, design documents and **each member's individual ownership**.
Everything below exists to keep that evidence honest and the three members' work integrated.

## 1. Know who you are working for

Ask the member which member they are (1, 2 or 3) at the start of the session if they have not
said. Ownership is in [docs/09-Team/members.md](docs/09-Team/members.md).

| Member | Owns | Folders |
| --- | --- | --- |
| 1 | Resource evidence: static bytecode extraction, shared-resource edges, evidence path | `evidence/` |
| 2 | Bounded search & verification: order runner, polluter search, minimisation, failure signatures, repeated-run verification, certificate generation, CLI, CI | `runner/`, `.github/` |
| 3 | Evaluation: fixtures, benchmark manifest, baselines, statistics, outcome decision | `eval/`, `fixtures/` |
| Joint | Contracts, architecture, report, Mid Eval evidence | `docs/` |

**Do not edit another member's folder** without the member explicitly saying the owner agreed.
If a change in someone else's area is needed, write it up as a GitHub issue or a note for them
instead.

## 2. Contracts are the integration boundary

The three folders meet only through the contracts in [docs/contracts/](docs/contracts/):

- [report-schema.md](docs/contracts/report-schema.md) — the diagnosis report every component
  feeds; schema at `eval/schema/report.schema.json`
- [interfaces.md](docs/contracts/interfaces.md) — who calls whom, with what data

**Never change a contract on your own.** A contract change needs agreement from all three
members, recorded in the PR description. Code against the contract, not against another
member's internals.

## 3. Git workflow (enforced by branch protection)

- Never commit to `main`. Work on a branch named `m<N>/<short-topic>` (e.g. `m2/order-runner`),
  `docs/<topic>` or `chore/<topic>`.
- Open a PR into `main`; CI must pass and **one other member** must approve.
- Before the evaluation, the demonstrated version is tagged `mid-eval-v1`. Do not move tags.
- Full rules: [CONTRIBUTING.md](CONTRIBUTING.md).

### HARD RULE — the member commits, never the agent

**You must not run `git commit`, `git push`, `git merge`, `git rebase`, `git tag`,
`git reset`, `git stash` or `git checkout`/`git switch` that discards changes.** You may only
read: `git status`, `git diff`, `git log`, `git show`, `git branch`. You may create the
working branch only if the member asks you to.

Why: the evaluation checks that each member understands and owns their history. A commit the
member ran, after reading the diff, is evidence of that. A commit an agent made is not.

### When to stop and hand over a commit

Stop and hand over as soon as **one logical unit** of work is finished and verified — for
example a function plus its test, a fixed bug, one doc section, a contract proposal. Do not
let a session pile up unrelated changes, and do not hand over half-finished work as a commit.
A long task is several commits, each handed over in turn.

### What you give the member at each hand-over

1. **Docs updated first** — see §5. The commit includes its docs.
2. **What changed**, in two or three plain sentences, and the `git status --short` output.
3. **How it was verified**: the exact command and its real result (or "not run").
4. **The exact commands**, ready to paste, staging files by name (never `git add -A` or
   `git add .`):

```bash
git config user.email            # must print the member's GitHub email — stop if not
git add runner/order_runner.py runner/tests/test_order_runner.py docs/evidence-m2.md
git commit -m "[M2] runner: run an explicit ordered list of tests in one JVM" \
  -m "Implements OrderRunner.run_ordered from eval/baseline.py: one fresh JVM per call,
tests executed in exactly the given order, failure signature per failed test.

Verified: python3 -m unittest runner.tests.test_order_runner -> 6 tests OK.
F1 victim fails after its polluter in one JVM; passes alone.
Refs: W6 (docs/08-MidEval/iteration-plan.md)" \
  -m "Co-Authored-By: Claude <noreply@anthropic.com>"
git push -u origin m2/order-runner
```

**Message format:**
- **Title:** `[M<N>] <area>: <what changed>` — imperative ("add", "fix", not "added"),
  at most 72 characters, specific. Areas: `runner`, `evidence`, `eval`, `fixtures`, `ci`,
  `docs`, `contract`, `report`.
- **Body:** *what* and *why* (not a file list); `Verified:` with the real command and result;
  `Refs:` the work package (W1–W13), issue or PR.
- **Trailer:** `Co-Authored-By:` for the assisting AI whenever it materially contributed.
- Bad: `update`, `fixes`, `wip`, `changes to runner`. Good: `[M2] runner: report a crash as
  a failure instead of dropping the test`.

5. Then tell the member to **read `git diff --staged` before running `git commit`.** If they
   do not understand a change, explain it before they commit.

## 4. Honesty rules — these protect marks

1. **Never invent results.** No number, pass count, timing or "it works" claim goes into code
   comments, docs, the report or a PR unless a command was actually run and its output is
   recorded. If something was not run, write "not yet run".
2. **Never fake a component.** Fakes and stubs live only under a `tests/` folder and are
   named `Fake…`. Production code must never import them.
3. **Mark mocked or hardcoded parts** explicitly in the code and in
   [docs/08-MidEval/demo-plan.md](docs/08-MidEval/demo-plan.md).
4. **Do not modify the code under analysis.** FlakeTrace must leave the analysed project's
   source unchanged — this is a promise made to the defence panel.
5. **Citations:** do not add a reference to the report or docs unless a member has opened
   the original source.

## 5. Keep the docs current — every hand-over

Before each commit hand-over, update every doc the work affects. Docs are part of the change,
not a later chore. Check this list each time:

| If the work… | Update |
| --- | --- |
| Ran anything (tests, a build, the tool on a fixture) | `docs/evidence-m<N>.md` — requirement, command, real result, limitation |
| Was materially AI-assisted | `docs/genai-log-m<N>.md` and a row in `docs/08-MidEval/genai-register.md` |
| Changed a component's behaviour, inputs or outputs | That folder's `README.md`, and its four-point note in `docs/04-Implementation/` |
| Progressed or finished a work package | Its row in `docs/08-MidEval/iteration-plan.md`, and your row in `docs/09-Team/members.md` |
| Changed what the live demo can show | `docs/08-MidEval/demo-plan.md` (including what is mocked) |
| Closed or advanced a panel action | Its status and evidence link in `docs/08-MidEval/panel-action-register.md` |
| Needed a design decision | A new file in `docs/03-Design/decisions/` (ADR) — proposed, for the team to agree |
| Created a claim someone will say to the supervisor | A row in `docs/07-Defense/claims-ledger.md` with its backing |
| Needs a contract change | **Do not edit the contract.** Write the proposal in the PR description or an issue |
| Changed how to install, run or test | Root `README.md` and §8 below |

Rules for docs: they live in `docs/` (the Obsidian vault) and use `[[wiki-links]]` between
vault notes; never write a result that was not produced by a real run; keep a doc's `Status`
line true. Plain `.md`/`.txt` files outside `docs/` (folder READMEs, evidence dumps) follow the
same honesty rules.

## 6. Record your own assistance (required by the GenAI policy)

After each working session that materially changed code, tests, diagrams or report text:

1. Append an entry to the member's GenAI log: `docs/genai-log-m<N>.md` — what was asked, what
   was kept, what the member changed, how it was verified, what was rejected or wrong.
2. Append evidence of anything executed to `docs/evidence-m<N>.md` — requirement, file/function,
   exact command, real result, limitation discovered.
3. Classify the assistance level L1–L4 (definitions in
   [docs/08-MidEval/genai-register.md](docs/08-MidEval/genai-register.md)).

`docs/evidence-m3.md` and `docs/genai-log-m3.md` are the model to follow.

End each session by telling the member, in plain words, what they now need to understand to
defend this work themselves. The supervisor will ask each member to explain and modify their
own code **without AI** during the evaluation.

## 7. Where things live

```
CLAUDE.md, CONTRIBUTING.md, README.md   rules and entry points
.github/                                CI workflow, PR template, CODEOWNERS (Member 2)
runner/                                 Member 2 — order runner, search, minimiser, verifier
evidence/                               Member 1 — static extraction, resource edges
eval/  fixtures/                        Member 3 — evaluation, fixtures, statistics
POC/                                    proposal-defence proof of concept (legacy, read-only)
docs/                                   Obsidian vault — open this folder in Obsidian
  contracts/                            integration contracts (joint)
  08-MidEval/                           what the Mid Evaluation requires and our evidence
  09-Team/                              working agreement, members, Claude guide
```

## 8. Commands

```bash
pip install -r eval/requirements.txt
python3 -m unittest eval.tests.test_stats eval.tests.test_outcome eval.tests.test_schema_validator \
    eval.tests.test_examples eval.tests.test_baseline eval.tests.test_yield_report
mvn -B -f fixtures/od-fixture/pom.xml test-compile      # needs JDK 8+ and Maven
python3 -m unittest -v runner.tests.test_order_runner   # needs JDK 8+ and Maven on PATH
mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile
python3 -m unittest -v evidence.tests.test_extract       # needs the two compiles above and javap
```

CI runs exactly what is in `.github/workflows/ci.yml`. If you add tests, add them there.
