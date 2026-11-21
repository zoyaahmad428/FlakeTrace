# W23, M2's half — evidence bundle writer and `replay`: design

**Date:** 2026-11-21 · **Owner:** M2 · **Contract:** `docs/contracts/interfaces.md` Interface 8 (agreed by M1, M2,
M3 on 2026-11-21) · **ADR:** ADR-013 §1, §3 · **With:** M3's `eval.bundle verify` (her half), M1's §5 reproduction ·
**Closes (with both halves and M1):** FT009; gives FT020 its handover exercise

## Intent

Today a report cannot be audited: its record is not committed and its path is absolute on one machine. A
bundle makes one diagnosis travel — report, record, environment, the commands to check it — with personal
paths removed, so another person can recount it (`verify`, M3) and re-run its evidence (`replay`, this
design) on their own machine. M1's B2 reproduction, the W32 practitioner case and W26b's "bundles for every
run" all wait on this.

## Goals / non-goals / anti-goals

- **Goals:** `diagnose --bundle <folder>` writes Interface 8's five files with the exact manifest and the
  redaction rule; `replay <bundle> --project <checkout>` follows R1–R6; real F1 and F3 bundles and replays.
- **Non-goals:** `verify` (M3); committing fixture bundles (M3, `eval/bundles/`); the UI reading bundles
  (ADR-013 Consequences: a later option); replaying unresolved reports (R1).
- **Anti-goals:** any home path or user name in a written bundle; replay quietly re-diagnosing (it must
  not search); a "same" verdict reported when the claims differ; a diagnosis without `--bundle` changing.

## Approaches

| | Approach | Trade-off |
| --- | --- | --- |
| **A (chosen)** | A new `runner/bundle.py` (manifest, redaction, writing, reading) and `runner/replay.py` (R1–R6); the CLI calls `write_bundle` after the report and gains a `replay` subcommand. Replay reuses `repeat`, `check_deletions`, `RecordingRunner`, `BudgetedRunner`, `resource_fields` and `assemble_report` | Each piece is used as it is, so replay's tallies are made exactly as a diagnosis makes them |
| B | Replay = `diagnose --order <reduced sequence>` | Simplest, but it would search and minimise again (Interface 8 point 3), and could blame other tests |
| C | The bundle written by `eval/` (M3) | Interface 8 point 1 decided the runner writes; M3 verifies |

## Design

### `runner/bundle.py`

- `write_bundle(folder, report, record_path, project, origin, records, environment_text) -> Path` builds the
  folder name from the record's file name (`<UTC time>-<victim>`, time first, as records are named; without `.jsonl`) *(builder check: Interface 8's "the record's own name")*, redacts, writes
  `report.json` (with `execution_record_reference = "record.jsonl"`), `record.jsonl`, `replay.md`,
  `environment.txt`, then `manifest.json` last with the four checksums. A folder that already exists is an
  error (never overwrite evidence).
- `manifest(header, report, ...)`: every Interface 8 key from the record header (line 1): `tool_commit/dirty`,
  `project_commit/dirty`, `n`, `shuffles`, `seed_base`, `budget`, `policy`, `scope`, `lifecycle`, `workspace`,
  `jvm` (`java.version`, `timezone`, `locale`, `file.encoding`, `junit.version`), `maven_version`,
  `python_version`, `os`, `container_image`, `command`; `run_date` from `started`. `subject.repository`:
  `"fixture"` if the project lies inside this repository, else `git remote get-url origin`, else `null`;
  `module_path` from `git rev-parse --show-toplevel`. Any `user:password@` part of the URL is stripped *(M2's call after the builder check: a token must never reach a committed bundle)*.
- `redact(text, replacements)`: longest first, `\`, `/` and JSON-escaped `\\` forms; the final check refuses
  any remaining home path, or the user name **as a path component** (`\<user>\`, `/<user>/`, `\\<user>\\`)
  (`BundleError`, CLI exit 1). Plain-text matches are not checked or replaced, so a short user name never
  blocks a bundle or rewrites a test name *(M2's call after the builder check)*. Applied to every file's text before it is
  written; the record is rewritten line by line, so its JSON stays valid.
- `reset_assumptions`: ADR-012 §1's sentence as one constant, copied verbatim.
- `environment_text()`: `java -version` and `mvn -v` output (both redacted; `mvn -v` prints Maven's home).
- `read_bundle(folder) -> Bundle(manifest, report, record_header)`: used by replay; checks the checksums
  first (a tampered bundle is not replayed).

### `runner/replay.py`

- `replay(bundle_folder, project, out_folder, timeout_s) -> (ReplayResult, exit_code)`:
  R1 refuse unless `report.outcome in (VERIFIED, CANDIDATE)` and `polluters` non-empty; build the runner on a
  `--workspace copy` of the checkout with the recorded lifecycle (the same `maven_test_classpath` /
  `OrderRunner` path `diagnose` uses), check the victim and polluters exist in discovery (as for `--order`);
  record header gains `"replay_of"`; R2 `repeat(sequence, n)` (`verify`), `repeat([victim], n)` (`alone`),
  `check_deletions(...)` (`deletion`) — in `diagnose`'s order: alone, deletion checks (which may drop a
  test), then the final sequence check on the kept set; **no budget** (the recorded `n` in full; a
  budget-cut original is named in the comparison); the header carries `reference_signature`; a
  `DiagnosisRuns(POLLUTER_FOUND, …, search_runs=0)`; R3
  `resource_fields` + `assemble_report`; write a `kind: "replay"` bundle; R4/R5 `compare(old, new) -> lines,
  same`.
- `compare`: outcome + reasons + polluters (`same` iff all three equal; Interface 8 R5), then informational rows: sequence `matched/n`, alone
  `passed/n`, each deletion check's status, subject commit, tool commit, JDK, OS, Maven, timezone, locale,
  encoding, lifecycle.
- Exit codes: 0 same verdict, 4 verdict differs, 2 input (not a bundle, checksum mismatch, nothing to
  replay, victim/polluter missing), 1 tool failure.

### CLI

- `diagnose --bundle <folder>` (default none); after `report.json` is written, `write_bundle`; the summary
  gains `bundle:     <folder>`.
- `replay <bundle> --project <checkout> [--bundle <folder>] [--records <folder>]`; defaults
  `flaketrace-bundles/` and `flaketrace-records/` in the current folder (git-ignored); never writes into the
  original bundle's folder. Prints the comparison.
- Docs: runner README, `docs/04-Implementation/` notes (bundle + replay), CLAUDE.md §8 and root README command
  lists, W23 plan row, members, evidence, GenAI log.

## Builder check (2026-11-21)

A fresh reviewer read this design as its builder and asked seven questions. Settled by M2 above: the user-name check (path components only), no budget in replay, the default output folders, stripping credentials from the repository URL, the folder name. Agreed by M1 and M3 as Interface 8 clarifications (R2, R5): a replay bundle passes `verify` through `reference_signature` in its header; "same" includes the same polluters.

## Left to the builder

The exact comparison column layout; whether `compare` lives in `replay.py` or `bundle.py`; the wording of
`replay.md` (it must contain the three commands and both commits).
