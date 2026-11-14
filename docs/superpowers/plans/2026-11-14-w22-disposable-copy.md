# W22 job 4 — diagnose on a disposable copy: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `--workspace copy` (CLI default) builds and runs everything in a temporary copy of the
project, deletes it afterwards, and reports integrity for both the copy and the original.

**Architecture:** a `workspace()` context manager in a new `runner/workspace.py`; the CLI wraps
`diagnose()` and the evidence extraction in it; `diagnose()` gains `workspace=` and `origin=` so
the record keeps the original project's provenance and the original is hashed too.

**Tech Stack:** Python 3 stdlib (`shutil`, `tempfile`, `contextlib`), `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-14-w22-disposable-copy-design.md`

**Branch:** `m2/w22-record-env` (W22 package branch, after `3b94dda`).

## Global Constraints

- Modes exactly `copy` and `in-place`; CLI default `copy`; `diagnose()` default `in-place`.
- Copy leaves out only the **top-level** `target/` and `.git/` (same rule as `runner/integrity.py`).
- The temporary folder is removed in `finally`, including when the body raises.
- Header `project` and `project_commit`/`project_dirty` name the original project, never the copy.
- No change to `eval/`, `evidence/`, the schema or the contracts.

## Review Focus

1. The diagnosis raises (e.g. Maven fails) inside the copy → the copy is still deleted; the error
   message names the user's project path, not the temp path. *(Task 1 and Task 2 tests.)*
2. `--records` inside the original project while working on a copy → still refused (exit 2).
   *(Task 2 test.)*
3. The original project changes during the run (another process edits a file) → integrity fails
   and names the file under "original project". *(Task 2 unit test.)*
4. A project folder whose name has spaces or non-ASCII characters → the copy works (the repo path
   itself has spaces). *(Task 1 test uses a folder name with a space.)*
5. `--workspace in-place` behaves exactly as before (writes `target/`, one integrity part).
   *(Task 2 real test.)*

---

### Task 1: `runner/workspace.py`

**Files:** Create `runner/workspace.py`; Test `runner/tests/test_workspace.py` (new; CI picks up
every `runner/tests/test_*.py` automatically).

**Interfaces:** Produces `WORKSPACES = ("copy", "in-place")` and
`workspace(project: Path, mode: str) -> ContextManager[Path]` (raises `ValueError` for an unknown mode).

- [ ] **Step 1: failing tests** — on a temp project folder named `"my project"` holding `pom.xml`,
  `src/A.java`, `target/x.class`, `.git/HEAD`, `sub/target/keep.txt`:
  - `copy` yields a different folder, named `my project`, with `pom.xml`, `src/A.java`,
    `sub/target/keep.txt`, and without `target/` or `.git/`;
  - after the `with` block the yielded folder and its temporary parent no longer exist;
  - when the body raises `RuntimeError`, the copy is deleted and the error propagates;
  - `in-place` yields the project path itself and deletes nothing;
  - `workspace(p, "elsewhere")` raises `ValueError`.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_workspace` → `ModuleNotFoundError`.
- [ ] **Step 3:** implement with `tempfile.mkdtemp(prefix="flaketrace-work-")`, `shutil.copytree`
  with an `ignore` callable that drops `target` and `.git` only when the folder is the project root,
  `shutil.rmtree(tmp, ignore_errors=True)` in `finally`.
- [ ] **Step 4:** the same command → OK.

---

### Task 2: `diagnose(workspace=, origin=)`, the CLI flag, docs

**Files:** Modify `runner/diagnose.py`, `runner/cli.py`; Test `runner/tests/test_diagnose.py`,
`runner/tests/test_cli.py`; Docs `runner/README.md`, `docs/04-Implementation/diagnosis-runs.md`,
`docs/04-Implementation/diagnose-cli.md`, ADR-012 (§4 built), `docs/07-Defense/claims-ledger.md`
(G4 wording now has a stronger true statement under `copy`), `docs/10-Final1/demo-plan.md` (the
demo's integrity line), `docs/evidence-m2.md`, `docs/genai-log-m2.md`,
`docs/08-MidEval/genai-register.md`, `docs/10-Final1/iteration-2-plan.md`,
`docs/09-Team/members.md`, `docs/10-Final1/handover-m1-m3.md`.

**Interfaces:** Consumes `WORKSPACES`, `workspace()`. Produces
`diagnose(..., workspace: str = "in-place", origin: Optional[Path] = None)` and
`integrity_of(copy: SourceIntegrity, original: Optional[SourceIntegrity]) -> SourceIntegrity`
in `runner/integrity.py` (passed = both passed; details `"copy: <d1>; original project: <d2>"`,
or the single result unchanged when `original` is `None`).

- [ ] **Step 1: failing tests**
  - `test_integrity.py`: `integrity_of` combines two passing results into one passing result
    whose details start `"copy: "` and contain `"; original project: "`; one failing part makes the
    whole fail and its file name appears in the details; `original=None` returns the copy result.
  - `test_cli.py` (diagnose mocked): with no flag, `diagnose` receives `workspace="copy"`,
    `origin=<given project>`, and a first argument that is **not** the given project; the folder it
    received no longer exists after `run_cli` returns; `--workspace in-place` passes the project
    itself and `origin=None`; `--workspace elsewhere` → `SystemExit` code 2; `--records` inside the
    project with the default workspace → exit 2; a `ToolError` raised by `diagnose` inside the copy
    → exit 1, the message names the given project path, and the copy is gone.
  - `test_diagnose.py` `TestDiagnoseOnFixture` (real JVM): copy `fixtures/od-fixture` without
    `target/` to a temp folder `T`; `main(["diagnose", "--project", T, "--victim", <F1>, "--n", "3",
    "--records", <tmp>])` → 0; `T/target` does **not** exist afterwards; the report's
    `source_integrity` passed with details containing `"original project:"`; the header has
    `workspace == "copy"` and `project == str(T.resolve())`. Same with `--workspace in-place` →
    `T/target` exists, header `workspace == "in-place"`.
  - `test_diagnose.py` (fake runner path is not used by `diagnose`; so unit-test the original check
    through `integrity_of` above — Review Focus 3).
- [ ] **Step 2:** run them → `ImportError` / `KeyError: 'workspace'` / `TypeError`.
- [ ] **Step 3: implement**
  - `diagnose`: `origin = Path(origin).resolve() if origin else None`; record-dir check against
    `project` and `origin`; `before_original = snapshot(origin)` at the start when `origin`; header
    `project`/`environment()` from `origin or project`; header `"workspace": workspace`; at the end
    `source_integrity=integrity_of(compare(before, snapshot(project)), compare(before_original,
    snapshot(origin)) if origin else None)`.
  - CLI: `--workspace` (`choices=WORKSPACES`, default `copy`); `run_diagnose(..., workspace=)`;
    the whole try-block from `diagnose(...)` through `resource_fields(...)` runs inside
    `with workspace(project, mode) as work:`; error messages keep naming `project`.
- [ ] **Step 4:** every runner, eval and UI suite; the real CLI on F1 in both modes.
- [ ] **Step 5:** docs, fresh whole-change review, verification, hand over.
