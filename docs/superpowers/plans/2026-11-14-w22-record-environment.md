# W22 job 1 — environment fields in the execution record: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** every execution-record header states the tool commit, Maven, Python, the test JVM's
version/timezone/locale/encoding/JUnit version, the lifecycle and workspace modes, the container
image and the command line.

**Architecture:** the JVM facts come from a new `FtHarness --env` mode run by
`OrderRunner.jvm_environment()`; the rest from Python in `runner/diagnose.py`, reusing the
existing git probe. Nothing is removed from the header.

**Tech Stack:** Python 3 (stdlib `unittest`), Java 8 source level, JUnit 4.13.2 (fixture).

**Spec:** `docs/superpowers/specs/2026-11-14-w22-record-environment-design.md`

**Branch:** `m2/w22-record-env`, stacked on `m2/w18-tallies` (not yet merged).

## Global Constraints

- Header keys added, none removed: `java_version`, `project_commit`, `project_dirty`, `os` stay.
- A failed probe never stops a diagnosis: the affected values are `null`.
- `lifecycle` is `"per-method"`, `workspace` is `"in-place"`, `container_image` is `null` (until jobs 3, 4 and W27).
- The harness compiles with `-source 8 -target 8` (unchanged in `OrderRunner.__init__`).
- Member 2 commits; the agent hands over commands (root `CLAUDE.md` §3).

## Review Focus

1. `mvn -v` prints warnings or ANSI colour codes before the version line → `maven_version` is the
   line starting `Apache Maven`, colour codes removed; `null` if there is none. *(Task 2 test.)*
2. The `--env` JVM hangs or the harness cannot start → `jvm_environment()` returns `{}` within
   `timeout_s`. *(Task 1 test.)*
3. FlakeTrace runs from a folder that is not a git checkout (a zip download) → `tool_commit` and
   `tool_dirty` are `null`. *(Task 2 test.)*
4. A locale with no country (`en`) or a timezone given as an offset (`GMT+05:00`) → recorded as
   the JVM reports it, no parsing. *(Task 1 parser test.)*
5. The header must still be one JSON line → every value is a string, bool, number, list or
   `null`. *(Task 2 fixture test reads it back with `json.loads`.)*

---

### Task 1: `FtHarness --env` and `OrderRunner.jvm_environment()`

**Files:**
- Modify: `runner/harness/FtHarness.java` (new `env(String file)` and its `--env` branch in `main`)
- Modify: `runner/order_runner.py` (new `parse_env`, `OrderRunner.jvm_environment`)
- Test: `runner/tests/test_order_runner.py`

**Interfaces:**
- Produces: `parse_env(text: str) -> Dict[str, str]`;
  `OrderRunner.jvm_environment() -> Dict[str, str]` with keys exactly
  `java.version`, `timezone`, `locale`, `file.encoding`, `junit.version`, or `{}` on any failure.

- [ ] **Step 1: Write the failing tests**

In `TestNormalisation` (no JVM):
```python
def test_env_lines_become_a_dict_without_parsing_the_values(self):
    text = "java.version\t1.8.0_452\ntimezone\tGMT+05:00\nlocale\ten\nfile.encoding\tCp1252\njunit.version\t4.13.2\n"
    self.assertEqual(parse_env(text), {"java.version": "1.8.0_452", "timezone": "GMT+05:00", "locale": "en",
                                       "file.encoding": "Cp1252", "junit.version": "4.13.2"})

def test_env_ignores_a_cut_off_last_line(self):
    self.assertEqual(parse_env("locale\ten_US\njunit.ver"), {"locale": "en_US"})
```
In `TestOrderRunnerOnF1` (real JVM):
```python
def test_env_reports_the_jvm_and_junit(self):
    env = self.runner.jvm_environment()
    self.assertEqual(set(env), {"java.version", "timezone", "locale", "file.encoding", "junit.version"})
    self.assertEqual(env["junit.version"], "4.13.2")

def test_env_timezone_comes_from_the_test_jvm(self):
    with mock.patch.dict(os.environ, {"JAVA_TOOL_OPTIONS": "-Duser.timezone=Pacific/Kiritimati"}):
        self.assertEqual(self.runner.jvm_environment()["timezone"], "Pacific/Kiritimati")

def test_env_failure_gives_an_empty_dict(self):
    broken = OrderRunner(self.runner.classpath, timeout_s=0.001)
    self.assertEqual(broken.jvm_environment(), {})
```

- [ ] **Step 2: Run, expect failure**

Run: `py -3 -m unittest runner.tests.test_order_runner`
Expected: `ImportError: cannot import name 'parse_env'`.

- [ ] **Step 3: Implement**

Java: `--env <file>` writes the five `key<TAB>value` lines (`System.getProperty("java.version")`,
`TimeZone.getDefault().getID()`, `Locale.getDefault().toString()`,
`System.getProperty("file.encoding")`, `junit.runner.Version.id()`), then `System.exit(0)`.
Python: `parse_env` splits on `"\n"`, drops the last piece (same rule as `parse_results`), keeps
lines with exactly one tab. `jvm_environment` runs `[java, "FtHarness", "--env", file]` with the
harness classpath, `cwd=working_dir`, `timeout=timeout_s`, `check=True`; any `OSError`,
`subprocess.SubprocessError` or missing file → `{}`.

- [ ] **Step 4: Run, expect pass**

Run: `py -3 -m unittest runner.tests.test_order_runner` → OK.

- [ ] **Step 5: Hand over the commit** (Member 2 runs it).

---

### Task 2: the header fields, the CLI's command line, and the docs

**Files:**
- Modify: `runner/diagnose.py` (`git_state`, `tool_environment`, `maven_version`, `diagnose(..., command=None)`, header)
- Modify: `runner/cli.py` (`main` passes `command`)
- Test: `runner/tests/test_diagnose.py`, `runner/tests/test_cli.py`
- Docs: `runner/README.md`, `docs/04-Implementation/diagnosis-runs.md`, `docs/evidence-m2.md`,
  `docs/genai-log-m2.md`, `docs/08-MidEval/genai-register.md`, `docs/10-Final1/iteration-2-plan.md`,
  `docs/09-Team/members.md`, `docs/10-Final1/handover-m1-m3.md`

**Interfaces:**
- Consumes: `OrderRunner.jvm_environment()` (Task 1).
- Produces: `git_state(path) -> Tuple[Optional[str], Optional[bool]]` (used by `environment()` and
  `tool_environment()`); `maven_version(text: str) -> Optional[str]`;
  `tool_environment() -> dict` with `tool_commit`, `tool_dirty`, `maven_version`, `python_version`;
  `diagnose(..., command: Optional[List[str]] = None)`.
  Header keys added: `tool_commit`, `tool_dirty`, `maven_version`, `python_version`, `jvm`,
  `lifecycle`, `workspace`, `container_image`, `command`.

- [ ] **Step 1: Write the failing tests**

`TestEnvironment`:
```python
def test_maven_version_is_the_apache_maven_line_without_colour(self):
    text = "WARNING: something\n\x1b[1mApache Maven 3.9.9 (8e8579a9)\x1b[m\nMaven home: x\n"
    self.assertEqual(maven_version(text), "Apache Maven 3.9.9 (8e8579a9)")
    self.assertIsNone(maven_version("no version here\n"))

def test_tool_outside_git_records_unknown_commit(self):
    with mock.patch("runner.diagnose.shutil.which", return_value=None):
        env = tool_environment()
    self.assertEqual((env["tool_commit"], env["tool_dirty"], env["maven_version"]), (None, None, None))
    self.assertEqual(env["python_version"], platform.python_version())
```
`TestDiagnoseOnFixture`:
```python
def test_record_header_states_the_environment(self):
    victim = TestIdentifier.from_dict(self.truth["F1"]["victim"])
    runs = diagnose(FIXTURE, victim, n=1, record_dir=self.records, command=["diagnose", "--n", "1"])
    header = json.loads(Path(runs.execution_record).read_text(encoding="utf-8").splitlines()[0])
    self.assertEqual(header["jvm"]["junit.version"], "4.13.2")
    self.assertTrue(header["maven_version"].startswith("Apache Maven"))
    self.assertEqual((header["lifecycle"], header["workspace"], header["container_image"]),
                     ("per-method", "in-place", None))
    self.assertEqual(header["command"], ["diagnose", "--n", "1"])
    self.assertIn("tool_commit", header)
    self.assertIn("java_version", header)  # old keys kept
```
`test_cli.py`, next to `test_options_reach_diagnose`: the mocked `diagnose` receives
`command == ["diagnose", "--project", <path>, "--victim", <victim>]` (the argv given to `main`).

- [ ] **Step 2: Run, expect failure**

Run: `py -3 -m unittest runner.tests.test_diagnose.TestEnvironment runner.tests.test_cli`
Expected: `ImportError: cannot import name 'maven_version'` / missing `command` kwarg.

- [ ] **Step 3: Implement**

Move the git calls of `environment()` into `git_state(path)`; `environment()` keeps its output.
`tool_environment()` uses `git_state(Path(__file__).resolve().parents[1])`, runs `mvn -v` (any
failure → `None`) through `maven_version`, and `platform.python_version()`. `diagnose()` adds the
header keys; `jvm` is `runner.jvm_environment()` or `None` when it is `{}`. `cli.main` passes
`command=list(argv if argv is not None else sys.argv[1:])` through `run_diagnose`.

- [ ] **Step 4: Run, expect pass, then the whole suite**

Run every `runner/tests/test_*.py`, every `eval/tests/test_*.py`, `ui.tests.test_server` → OK.
Run the real command on F1 and print the header line.

- [ ] **Step 5: Docs** (the CLAUDE.md §5 list above), then review (superpowers:requesting-code-review)
and verification (superpowers:verification-before-completion).

- [ ] **Step 6: Hand over the commit** (Member 2 runs it).
