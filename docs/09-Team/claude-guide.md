# How to direct your Claude (or any AI agent) on this project

All three of us use AI agents. These steps keep three agents from producing three
inconsistent projects, and keep the GenAI disclosure honest without extra effort.

## Setup, once

1. Clone the repo and open your agent **at the repository root**, so it reads `CLAUDE.md`
   automatically. (In Claude Code, `CLAUDE.md` at the root is loaded on start. In other tools,
   paste its contents or tell the agent to read it first.)
2. Open `docs/` as an Obsidian vault if you want to browse notes with links.

## Starting a session — copy, fill in, paste

```
I am Member <N> (<name>) on FlakeTrace. Read CLAUDE.md, docs/09-Team/members.md and
docs/contracts/interfaces.md first.

Today's task: <one concrete task, e.g. "implement OrderRunner.run_ordered for JUnit 4">
Branch: m<N>/<topic>   (create it from an up-to-date main if it does not exist)
Done means: <observable result, e.g. "F1 victim fails after polluter in one JVM, test added">

Rules: stay inside <my folder>; do not change contracts; do not invent any result;
log what you ran in docs/evidence-m<N>.md and this session in docs/genai-log-m<N>.md.
Ask me before any decision that another member would need to agree with.
```

## During the session

- **Ask it to explain before it writes.** "Propose the design and two alternatives first."
  Choosing between alternatives yourself is the ownership evidence the guide wants.
- **Run everything for real.** If the agent says something passes, make it show the command
  output.
- **Keep sessions to one task.** Small branches review faster and integrate cleanly.
- **Push back and record it.** When the agent is wrong, note it in your GenAI log — this is the
  "rejected or corrected suggestion" the evaluation asks every member to show.

## Ending a session

```
Before we stop: update docs/evidence-m<N>.md and docs/genai-log-m<N>.md for this session
(assistance level L1–L4), commit with the [M<N>] prefix, push the branch, and give me a
short list of what I must understand to explain and modify this code myself without AI.
```

Then actually study that list. Open the PR when the task is done, and ask a teammate to review.

## Things an agent must never do here

- Commit to `main`, force-push, or move a tag
- Edit another member's folder or a contract without the owner's agreement
- Put a number in a doc or report that no command produced
- Add a citation nobody has opened
- Modify the source of a project FlakeTrace is analysing
