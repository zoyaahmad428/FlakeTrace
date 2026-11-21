# W23, M2's half — bundle writer and replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `diagnose --bundle` writes Interface 8's five-file bundle with paths redacted, and `replay <bundle> --project <checkout>` re-checks its evidence (R1–R7) and prints a same/DIFFERENT comparison.

**Architecture:** `runner/bundle.py` (redaction, manifest, write, read) has no JVM code and is tested on files alone. `runner/replay.py` has a fake-testable core `replay_steps(runner, …)` (like `run_steps`) and a pure `compare(...)`; `runner/diagnose.py` shares its project setup with replay through one extracted helper. The CLI wires both.

**Tech Stack:** Python 3.11 `unittest`, `hashlib`, `FakeOrderRunner`, the od-fixture (JDK 8+, Maven).

**Spec:** `docs/superpowers/specs/2026-11-21-w23-bundle-and-replay-design.md`; `docs/contracts/interfaces.md` Interface 8 (and 4); ADR-013 §1, §3.

## Global Constraints

- Five files exactly: `manifest.json`, `report.json`, `record.jsonl`, `replay.md`, `environment.txt`; UTF-8, `\n` line endings; `manifest.json` written last.
- Manifest keys exactly as Interface 8 (`bundle_version` 1, `kind`, `tool`, `subject`, `victim`, `command`, `parameters`, `environment`, `reset_assumptions`, `fresh_run`, `run_date`, `replay_of`, `files`); every key present, `null` when unknown.
- Placeholders exactly `<project>`, `<records>`, `<home>`, `<user>`. The user name is replaced and checked **only as a path component**.
- Bundle folder name = the record file's name without `.jsonl` (`<UTC>-<victim>`); an existing folder is an error, never overwritten.
- `execution_record_reference` inside the bundle is `"record.jsonl"`.
- Replay: only `VERIFIED`/`CANDIDATE` with polluters (else exit 2 "nothing to replay: no polluter was blamed"); steps `alone`, `deletion`, `verify` in that order; no budget; header gains `reference_signature`, `replay_of`; same = outcome + reasons + polluters; exit 0 same, 4 different, 2 input, 1 tool.
- Defaults `flaketrace-bundles/` (add to `.gitignore`), `flaketrace-records/`; never write into the original bundle's folder.
- A diagnosis without `--bundle` is unchanged. Agent never commits; test-first; failing output into `docs/evidence-m2.md`.

## Review Focus

1. A Windows path written with `\\` inside JSON (escaped) and with `/` → both redacted → Task 1 `test_redacts_every_form_of_a_path`.
2. A user name that is also a word in a test name (e.g. user `pkg`) → test names untouched → Task 1 `test_user_name_is_only_a_path_component`.
3. A tampered bundle given to replay → refused before any JVM run (exit 2) → Task 1 `test_read_bundle_refuses_a_changed_file`, Task 4 CLI test.
4. `--project` pointing at a checkout where a polluter no longer exists → exit 2 naming the test, before runs → Task 3 `test_missing_polluter_is_refused`.
5. Replaying a replay bundle → allowed (it blames polluters), `replay_of` chains → Task 3 `test_a_replay_bundle_can_be_replayed`.

---

### Task 1: `runner/bundle.py`

**Files:** Create `runner/bundle.py`; Test `runner/tests/test_bundle.py`.

**Interfaces — Produces:**
- `BundleError(Exception)`; `RESET_ASSUMPTIONS: str` (ADR-012 §1's "Each run is clean" sentence, verbatim from the ADR file).
- `redact(text, paths: Dict[str, str], home: str, user: str) -> str` — `paths` maps absolute path → placeholder (`<project>`, `<records>`); each in raw, `/`, and JSON-escaped (`\\`) forms, longest first; then `home` → `<home>`; then the user name only between path separators.
- `assert_clean(text, home, user)` raises `BundleError` if `home` (any form) or `<sep>user<sep>` remains.
- `clean_url(url) -> Optional[str]` removes `user[:password]@`.
- `manifest(header: dict, report: dict, *, kind, repository, module_path, replay_of, files) -> dict`.
- `write_bundle(out_folder, report, record_path, *, paths, home=str(Path.home()), user=getpass.getuser(), environment_text="", repository=None, module_path=None, kind="diagnosis", replay_of=None) -> Path`.
- `read_bundle(folder) -> Bundle` (`Bundle = namedtuple(manifest, report, header)`) — checks all four checksums first, `BundleError` on any mismatch or missing file.

- [ ] **Step 1: failing tests** (a tmp record with a header containing `"project": "C:\\Users\\alice\\work\\proj"`, a `"command"` list with that path, run lines; a minimal report dict):
  - `test_writes_exactly_five_files_with_lf_and_relative_record`: names; `report.json["execution_record_reference"] == "record.jsonl"`; no `\r\n` in any file.
  - `test_manifest_has_every_contract_key`: the 13 keys; `parameters`, `environment` subkeys as Interface 8; `files` = SHA-256 of the four files' bytes.
  - `test_redacts_every_form_of_a_path`: raw, `/`, and JSON-escaped project path → `<project>`; records path → `<records>`; home → `<home>`.
  - `test_user_name_is_only_a_path_component`: user `pkg`, test name `pkg.VictimTest#v` unchanged; `C:\\Users\\pkg\\x` → `<home>`-or-`<user>` form, never raw.
  - `test_a_remaining_home_path_is_refused`: `assert_clean` raises; `write_bundle` writes no folder.
  - `test_existing_folder_is_not_overwritten`: second write → `BundleError`.
  - `test_clean_url_strips_credentials`: `https://u:t@github.com/a/b.git` → `https://github.com/a/b.git`; `None` → `None`.
  - `test_read_bundle_refuses_a_changed_file`: flip one byte of `record.jsonl` → `BundleError` naming `record.jsonl`.
  - `test_reset_assumptions_is_the_adr_sentence`: the constant occurs verbatim in `docs/03-Design/decisions/ADR-012-*.md`.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_bundle` → `No module named 'runner.bundle'`.
- [ ] **Step 3:** implement. **Step 4:** same → OK.

### Task 2: `diagnose --bundle`

**Files:** Modify `runner/cli.py`, `.gitignore`; Test `runner/tests/test_cli.py`.

**Interfaces:** `--bundle <folder>` (default `None`) on `diagnose`; after the report is written, `write_bundle(...)` with `paths = {project: "<project>", origin (copy mode): "<project>", records folder: "<records>"}`, `environment_text` from `java -version` + `mvn -v` (stderr/stdout captured, `None`-safe), repository from `clean_url(git remote get-url origin)` or `"fixture"` when the project is inside this repository, `module_path` relative to `git rev-parse --show-toplevel`. Summary gains `  bundle:     <path>`. `BundleError` → exit 1 with its message.

- [ ] **Step 1: failing tests:** `test_bundle_flag_writes_a_bundle` (mock `diagnose`, a real tmp record → exit 0, folder exists, `bundle:` line); `TestCliOnFixture.test_f1_bundle_is_portable` (real F1 with `--bundle <tmp>`: five files; `subject.repository == "fixture"`, `module_path == "fixtures/od-fixture"`; neither `str(Path.home())` nor `getpass.getuser()` as a path component in any file; `read_bundle` succeeds).
- [ ] **Step 2:** run → fail. **Step 3:** implement (+ `.gitignore` line `flaketrace-bundles/`). **Step 4:** `py -3 -m unittest runner.tests.test_cli` → OK.

### Task 3: `runner/replay.py` and shared setup

**Files:** Create `runner/replay.py`; Modify `runner/diagnose.py` (extract `prepare_runner(project, timeout_s, lifecycle) -> Tuple[OrderRunner, List[TestIdentifier], Selection]` and `record_header(runner, victim, n, project, source, started, **fields) -> dict` from `diagnose()`, behaviour unchanged — the replay record gets the same header keys, plus `reference_signature` (the report's dict) and `replay_of`); Test `runner/tests/test_replay.py`.

**Interfaces — Produces:**
- `replay_steps(runner, polluters, victim, reference: FailureSignature, n, original_order) -> DiagnosisRuns` — through `BudgetedRunner(runner, Budget(), n, victim)`: `_label alone` → `repeat([victim], n)`; `_label deletion` → `check_deletions(...)`; `_label verify` → `repeat(kept + [victim], n)`; status `POLLUTER_FOUND`, `search_runs 0`, `order_given True`, `budget` = account.
- `report_reference(report) -> FailureSignature` from `report["failure_signature"]`.
- `replayable(report) -> Optional[str]` — `None` if OK, else the refusal text.
- `compare(old_report, new_report, old_manifest, new_manifest) -> Tuple[List[str], bool]`.
- `replay(bundle_folder, project, out_folder, records, timeout_s, workspace_mode, command) -> Tuple[int, List[str], Optional[Path]]` (exit code, comparison lines, new bundle).

- [ ] **Step 1: failing tests** (fake runner; victim fails iff P precedes it):
  - `test_replay_steps_run_alone_deletion_verify_in_order`: one polluter → calls `[V]×n` then `[P,V]×n`, no deletion runs (alone-check), `sequence_tally == RunTally(n,0,n,0,0)`.
  - `test_replay_may_drop_a_polluter`: report blames `[P, Q]`, only P needed → final `polluters == [P]`.
  - `test_only_blamed_reports_are_replayable`: `UNRESOLVED` → `"nothing to replay: no polluter was blamed"`; `VERIFIED` with polluters → `None`.
  - `test_compare_same_and_different`: identical → `same True`, first line `verdict:  VERIFIED -> VERIFIED  same`; different polluters → `False`; `CANDIDATE` reasons differ → `False`; 20/20 vs 19/20 with same verdict → `True`; JDK differs → line ends `DIFFERENT` but `same` stays `True`.
  - `test_missing_polluter_is_refused` and `test_a_replay_bundle_can_be_replayed`: on `replay()` with `prepare_runner` mocked to return a fake runner and a discovered list.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_replay` → `No module named 'runner.replay'`.
- [ ] **Step 3:** implement. **Step 4:** `py -3 -m unittest runner.tests.test_replay runner.tests.test_diagnose` → OK.

### Task 4: `replay` CLI, real runs, docs

**Files:** Modify `runner/cli.py`; Test `runner/tests/test_cli.py`; docs.

**Interfaces:** subcommand `replay <bundle> --project <dir> [--bundle flaketrace-bundles] [--records flaketrace-records] [--workspace copy|in-place]`; prints the comparison lines, then `  bundle:     <new bundle>`; exit codes as Global Constraints.

- [ ] **Step 1: failing tests:** `test_replay_refuses_a_tampered_bundle` (exit 2, no `diagnose`/runner call); `test_replay_nothing_to_replay_exits_2`; `TestCliOnFixture.test_f1_bundle_replays_the_same` (real: `diagnose --bundle`, then `replay <it> --project fixtures/od-fixture` → exit 0, first line ends `same`, new bundle `kind == "replay"`, `replay_of` == original `files["report.json"]`).
- [ ] **Step 2:** run → fail. **Step 3:** implement. **Step 4:** `py -3 -m unittest runner.tests.test_cli runner.tests.test_replay runner.tests.test_bundle` → OK; then the whole runner suite, eval, `ui.tests.test_server`.
- [ ] **Step 5: real runs:** F1 and F3: `diagnose --bundle`, `replay` → record the comparison output; grep each bundle for the home path and user name (none).
- [ ] **Step 6: docs:** runner README (bundle + replay rows, options), `docs/04-Implementation/` notes, root README and CLAUDE.md §8 command lists (`--bundle`, `replay`), W23 plan row, members, evidence, GenAI log, register row. Hand over the commit, PR text and messages.
