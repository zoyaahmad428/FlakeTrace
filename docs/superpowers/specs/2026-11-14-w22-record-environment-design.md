# W22 job 1 — environment fields in the execution record (design)

*2026-11-14 · M2 · Status: proposed, awaiting M2's approval · ADR-012 §6 · closes part of FT006/FT021,
feeds W23 (ADR-013 manifest `environment`).*

## Why

A real-project result is only replayable if the record says what it ran under. Two fastjson cases
flip with the timezone (POC log), and the bundle of ADR-013 copies its `environment` from this
header. Today the header has the project commit, OS and `java -version` only.

## Goals / non-goals

- **Goal:** every record header states, from a real probe: FlakeTrace's own commit and dirty flag,
  Maven version, Python version, the test JVM's `java.version`, timezone, default locale,
  `file.encoding` and JUnit version, the lifecycle mode, the workspace mode, the container image
  (`null`), and the command line.
- **Non-goal:** changing how tests run (job 3), copying the project (job 4), the container (W27).
- **Anti-goal:** a probe failure that stops a diagnosis. Unknown provenance is recorded as `null`,
  as `environment()` already does for a project outside git.

## Approaches

| | A. Ask the test JVM (chosen) | B. Ask Python |
| --- | --- | --- |
| How | `FtHarness --env <file>`, like `--list` | `time`, `locale` modules |
| Accuracy | What the tests saw | Can differ (`JAVA_TOOL_OPTIONS`, `-Duser.timezone`) |
| Cost | One short JVM launch per diagnosis | none |

Chosen by M2's delegation to Claude ("whatever is best in the long run"): A, because the record must
describe the test JVM, and replay (W23) compares exactly these values.

## Design

- **Harness:** `FtHarness --env <file>` writes `key<TAB>value` lines: `java.version`,
  `timezone` (`TimeZone.getDefault().getID()`), `locale` (`Locale.getDefault().toString()`),
  `file.encoding`, `junit.version` (`junit.runner.Version.id()`). Run with the project's classpath
  and working directory, like a test run.
- **Runner:** `OrderRunner.jvm_environment() -> dict` runs it; any failure gives `{}` and the
  header fields become `null`.
- **Header** (`runner/diagnose.py`), added beside today's keys (none removed — readers of
  `java_version`, `project_commit`, `os` keep working):
  `tool_commit`, `tool_dirty` (git of the FlakeTrace checkout), `maven_version` (first line of
  `mvn -v`), `python_version`, `jvm` (the dict above), `lifecycle: "per-method"`,
  `workspace: "in-place"`, `container_image: null`, `command` (the argument list, as given to the
  CLI; `null` when `diagnose()` is called from Python).
- **Tests first:** a unit test of the `--env` parser; a fake-runner test that the header has every
  key and survives a failing probe; a real-JVM test that `jvm.timezone` equals a `-Duser.timezone`
  value forced through `JAVA_TOOL_OPTIONS` (proves the value comes from the JVM, not Python).

## Left to the builder

Exact helper names; how `mvn -v` is parsed (first line, ANSI codes stripped).
