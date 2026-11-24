# Verify Committed Bundles Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** a test that fails whenever a committed bundle stops passing `eval.bundle verify`.
**Spec:** `docs/superpowers/specs/2026-11-24-verify-committed-bundles-design.md`.

## Global Constraints

- New file only in `eval/tests/` (M3 agreed); M3's existing tests untouched.

## Review Focus

1. The check must not be vacuous: the #164 incident re-enacted must name exactly the pre-W35 bundles. (Task 1)

### Task 1

- [ ] `eval/tests/test_committed_bundles.py`: every committed bundle verifies; the #164 re-enactment (v2 schema
  made to require `reproduced_by`) names exactly the bundles without the field. Run → OK; full `eval/tests` → OK.
- [ ] Docs: CLAUDE.md §8 eval command, evidence-m2, GenAI log and register.
