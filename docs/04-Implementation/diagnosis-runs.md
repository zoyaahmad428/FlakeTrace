# Diagnosis runs — `runner/diagnose.py` and its modules (Member 2, W7)

*Status (2026-10-09): complete — run on all five fixture cases locally (JDK 21) and in CI
(JDK 8, run `37971869749`). Four-point ownership note per [[04-Implementation/README]]. Design:
[[03-Design/decisions/ADR-004-w7-diagnosis-runs]]. Evidence: [[evidence-m2]].*

## 1. What it does and why it is there

`diagnose(project, victim, n=20)` turns W6's single primitive — run an order in one fresh JVM —
into the raw evidence a diagnosis report needs: the original failing order and its reference
failure signature, how often the victim fails **alone**, which earlier test **pollutes** it, how
often `[polluter, victim]` **reproduces** the failure, whether the project's files outside
`target/` and `.git/` had the **same hashes before and after** (not a sandbox; claims ledger G4), and a **record** of every JVM run. It returns plain counts (`DiagnosisRuns`); the
verdict stays with M3's `decide()`, so the statistics and decision rules live in one place.

| Module | Job |
| --- | --- |
| `integrity.py` | SHA-256 of every project file except `target/`, `.git/`, before and after; on a copy (W22), both the copy and the user's original are checked |
| `recording.py` | `RecordingRunner` writes each run as one JSON line, immediately; the header also names the project's git commit, whether it had uncommitted changes, and the OS (`environment()`, panel action A7), and since W22 what the runs ran under: FlakeTrace's commit, Maven, Python, the test JVM's version, timezone, locale, encoding and JUnit version (`FtHarness --env`), lifecycle and workspace mode, and the command line (ADR-012 §6) |
| `discovery.py` | Surefire-like class list; methods from JUnit (`FtHarness --list`) |
| `search.py` | `reproduce` (reference signature), `find_polluter` (one-by-one) |
| `minimise.py` | `ddmin` — when no single test is enough, shrinks the tests before the victim with single trials, not deletion-verified (W10, ADR-007; FT004) |
| `orders.py` | class-first shuffled orders when the starting order never fails; the first real failure becomes the failing order (ADR-008) |
| `verify.py` | `repeat` ×n → a `RunTally`: passed, matched, other, infra (W18, ADR-010). The old pair of counts hid a victim that failed alone *differently* (FT003) |
| `diagnose.py` | `run_steps` (logic, testable with a fake runner) + `diagnose` (real wiring) |

## 2. Why it is built this way

- **Small modules + a recording wrapper** (ADR-004 option A). Rejected: one big module (hard to
  test and to defend piece by piece); each step writing its own log lines (one forgotten call
  makes the record silently incomplete).
- **One-by-one polluter search**, not bisection: simple, one polluter per run, easy to explain;
  bisection is the W10 minimiser's job. A `priority` list lets W9 try M1's evidence-backed
  candidates first without W7 changing.
- **Discovered order + explicit override**: the demo input is "project + victim"; real projects
  whose CI order differs pass `original_order`.
- **`n = 20`**: 20/20 → Wilson lower bound 0.839 and 19/20 → 0.764, both above the 0.70 bar, so
  one noisy run cannot flip a verdict.
- **`run_steps` takes any runner**, so every early stop is unit-tested with M3's
  `FakeOrderRunner` in milliseconds; only `diagnose` touches Maven and the JVM.

## 3. What breaks

- **More than one polluter needed** (F3) → `ddmin` finds a reduced set (F3: `setFlagA`, `setFlagB`; 10 minimise runs = 1
  re-check of the full order + 9 `ddmin`) → `POLLUTER_FOUND` with several polluters. The full order must
  fail once more before `ddmin`, so a one-off flaky failure ends `INCONSISTENT` (called `NO_SINGLE_POLLUTER` before W18) with nobody blamed. Each `ddmin` check is one run, so a flaky check can keep a bystander, and verify ×n does **not** expose it: the longer sequence still fails (FT004, reproduced 2026-11-13 in [[evidence-m2]]). Repeated deletion checks are ADR-011 (W20).
- **A rarely-failing flaky victim** can pass all `n` alone runs by chance and then fail during
  the search, giving a spurious polluter; the verify counts expose it (few matches of `n`), so
  `decide()` can at most say `CANDIDATE`.
- **The victim never fails for real in the starting order** → up to 31 distinct shuffled orders
  (ADR-008; F4: reproduced by seed 1 after 2 orders). If none fails, the alone check still runs
  (`alone_n = n`): a real alone failure gives `VICTIM_FAILS_ALONE`; nothing at all gives
  `NOT_REPRODUCED` (N3) with every count, and crash-only runs are `infrastructure_failures`.
- **`record_dir` inside the analysed project** → refused with `DiagnoseInputError` (a `ValueError`); a record written
  there would itself make the integrity check fail.
- **Flaky victims**: N2 (fails ~50%, `Random.nextBoolean` since PR #14) ends `VICTIM_FAILS_ALONE`.
  Without the alone check it would be blamed on a spurious polluter (seen in a mutation check,
  [[evidence-m2]] 2026-10-10). Its earlier `System.nanoTime()` parity never failed on Windows.
- **Order mismatch**: Surefire's default `runOrder` is `filesystem`; discovery assumes
  alphabetical. **Multi-module projects**: only the top-level `target/` is excluded from hashing.
- A crash or timeout is never a reference or a match — it only counts as "failed for any reason".

## 4. How to modify it

- **Change the minimiser**: `ddmin` in `minimise.py` takes any runner, so try changes against
  `runner/tests/test_minimise.py` (fake runner) first; `run_steps` calls it only when `find_polluter`
  returns `None` and the prefix is not empty.
- **Change the default `n`**: the `n=20` default of `diagnose`; also update ADR-004 and the
  report (it is open question I3, agreed with M3).
- **Add a step**: set `_label(runner, "<step>")` before its runs so the execution record names
  it, and add its counts as new `DiagnosisRuns` fields with defaults so existing callers keep
  working.
