# W23 Replay Gaps Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** a bundle's `replay.md` runs as written; the OS row does not report a false difference.

**Architecture:** `_replay_md(header, folder_name, out_folder, repository, module_path)` in `runner/bundle.py`;
`_same_os(old, new)` used by `compare` in `runner/replay.py`.

**Tech Stack:** Python 3.11 `unittest`. **Spec:** `docs/superpowers/specs/2026-11-22-w23-replay-gaps-design.md`.

## Global Constraints

- No `<` or `>` inside a command line of `replay.md`; paths quoted.
- Committed bundles are not rewritten.

## Review Focus

1. An absolute output folder must not put a personal path in `replay.md` (redaction refuses it). (Task 1)
2. A subject with no module path (`module_path` None) → `"CHECKOUT"`. (Task 1)
3. A replay bundle's own `replay.md` (written by `replay`) gets the same commands. (Task 1, real run)

### Task 1: `replay.md` commands (gaps 1, 2, 6)

- [ ] Tests in `TestBundle`: real path and `--project fixtures/od-fixture`, no `<`/`>` in the two commands, step 1
  wording; a relative output folder used as given; an outside subject → `"CHECKOUT"` / `"CHECKOUT/core"` and the
  clone line. Run → fail. Implement. Run `runner.tests.test_bundle` → OK.

### Task 2: OS row (gap 5)

- [ ] `TestOsRow`: Windows 10/11 same build → `same`; other build or system → `DIFFERENT`. Run → fail. Implement.

### Task 3: real check, docs, hand-over

- [ ] Real F1 bundle; run its `replay.md` commands verbatim from the repo root.
- [ ] Docs: `runner/README.md` bundle row, `docs/04-Implementation/diagnose-cli.md`, evidence, GenAI log, register,
  plan W23 row, action register FT009 note.
