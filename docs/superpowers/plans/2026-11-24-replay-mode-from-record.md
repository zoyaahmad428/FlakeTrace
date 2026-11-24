# Replay Mode From Record Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** replay derives `reproduced_by` from the record header and refuses a report that disagrees.

**Architecture:** in `replay()` (`runner/replay.py`): `search_mode` from `original.header` (as now);
`reproduced_by = "pair" if search_mode == "pairs" else "order"`; if `report.get("reproduced_by")` is set and differs,
return exit 2 before any run. **Spec:** `docs/superpowers/specs/2026-11-24-replay-mode-from-record-design.md`.

## Global Constraints

- The refusal happens before Maven or any JVM run, next to the R2 `n`/`lifecycle` check.

## Review Focus

1. A report with `reproduced_by: null` but polluters cannot occur (schema); treated as missing. (Task 1)

### Task 1

- [ ] Tests in `TestReplay`: an in-between pair bundle (header `"pairs"`, no report field) → `"pair"`, the
  constructed-pair line; a report saying `"order"` with header `"pairs"` → exit 2, no new bundle, message names
  both; existing pair and pre-W35 tests unchanged. Run → the first two fail. Implement. Run `runner.tests.test_replay`
  and `eval/tests` → OK.
- [ ] Docs: runner README replay row, implementation note, evidence, GenAI log, register.
