# W22 job 4 — diagnose on a disposable copy (design)

*2026-11-14 · M2 · Status: proposed, awaiting M2's approval · ADR-012 §4 · FT021, panel action A3 ·
cut #3 in the iteration plan if time is short.*

## Why

The panel asked whether FlakeTrace changes the code it analyses. Today the honest answer is narrow:
the project's files outside `target/` and `.git/` hash the same before and after — but FlakeTrace
itself runs `mvn test-compile` **inside the user's project**, writing `target/`, and a test that
writes files leaves them in the user's folder. With `--workspace copy` the user's folder is never
written to: everything happens in a temporary copy that is deleted afterwards. True by
construction, then also checked.

## Goals / non-goals / anti-goals

- **Goal:** `--workspace copy|in-place` on the CLI; with `copy`, the build, every JVM run and
  Member 1's evidence extraction use a temporary copy; the copy is deleted at the end, also on
  error.
- **Goal:** the report's integrity check says both things: the copy's files before/after (what the
  tests did), and the original project's files before/after (the user's folder untouched).
- **Non-goal:** containing writes **outside** the project (temp folder, home directory) — that is
  the container's job (W27) and FYP-2 sandboxing. Stated as a limitation.
- **Anti-goal:** a copy left behind on disk; provenance lost (the record must still name the
  original project and its git commit).

## Approaches

| | A. The CLI owns the copy (chosen) | B. `diagnose()` copies and deletes | C. `diagnose()` copies, caller deletes |
| --- | --- | --- | --- |
| Evidence extraction after `diagnose()` | works — runs inside the copy before it is deleted | breaks — compiled classes gone | works, but every caller must remember to delete |
| Who cleans up | one `with` block in the CLI | `diagnose()` | each caller (leaks) |

**Default: `copy`** on the CLI (and therefore in the UI, which runs the CLI), as ADR-012 §4
proposes. Unlike the lifecycle mode it changes no execution semantics — the same tests run the same
way, in another folder — so it needs no validation run first; it costs one copy and one full Maven
compile per diagnosis. `diagnose()` called from Python keeps working on whatever folder it is given.
*(Both calls Claude's, on M2's delegation.)*

## Design

- **`runner/workspace.py`** (new, M2): `WORKSPACES = ("copy", "in-place")`;
  `workspace(project: Path, mode: str)` — a context manager yielding the folder to use: the project
  itself for `in-place`; for `copy`, `<tmp>/flaketrace-work-*/<project name>` made by `copytree`,
  leaving out the top-level `target/` and `.git/` (the same rule as the integrity check: build output
  is rebuilt, git metadata is read from the original). The temporary folder is removed in `finally`.
- **`diagnose(..., workspace="in-place", origin=None)`:** `origin` is the user's project when
  `project_dir` is a copy. Then the header's `project` and the git provenance come from `origin`,
  `record_dir` must not be inside `origin` either, and the original is hashed before and after as
  well. `source_integrity` passes only if both comparisons pass; its details name both:
  `"copy: 23 files … identical; original project: 23 files … identical"`. The header's `workspace`
  becomes the real mode.
- **CLI:** `--workspace {copy,in-place}`, default `copy`; `with workspace(project, mode) as work:`
  run `diagnose(work, …, workspace=mode, origin=project)` and `resource_fields(work, runs)` inside it.
- **Tests first:** `workspace()` copies the files, leaves out `target/` and `.git/`, removes the copy
  afterwards and also when the body raises; `in-place` yields the project itself; the CLI's default
  is `copy` and passes `origin`; **real run:** a fresh copy of the fixture without `target/`
  diagnosed through the CLI → `VERIFIED (sequence)`, integrity passed, and the fixture copy *still
  has no `target/`* (the user's folder was never written); `--workspace in-place` still creates it
  (today's behaviour); a test that the original is hashed (a file changed in the original during
  the run fails the check — unit level, with a fake runner).

## For M1 and M3

Nothing changes in `evidence/` or `eval/`. `source_integrity.details` gets longer (both checks);
the schema field is unchanged. M1's extractor is now called on the copy's `target/`.

## Left to the builder

Helper names; whether `in-place` also hashes the original twice (it is the same folder — no).

## Limitations to state

Writes outside the project are not contained (temp, home, network). A build that needs `.git`
(e.g. a git-commit plugin) **or files outside the project folder (a multi-module child's parent
`pom.xml`)** fails in the copy — the error message suggests `--workspace in-place`. One extra full
copy and compile per diagnosis. *(Multi-module limitation and the `--copy-parent` option added after
the review, 2026-11-14.)*
