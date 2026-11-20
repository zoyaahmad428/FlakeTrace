# Discovery reads the project's Surefire includes: implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `discover_order` returns exactly the tests the project's own Surefire configuration
selects, so FJ-03 (fastjson, `**/bvt/**/*.java`) can be diagnosed.

**Architecture:** a pure selection layer in `runner/discovery.py` (parse the effective POM's
Surefire includes/excludes, match class paths with Surefire's rules); `maven_test_classpath`
optionally writes the effective POM in its existing Maven call; `diagnose()` wires the two.

**Tech Stack:** Python 3 stdlib (`xml.etree`, `re`), `unittest`, Maven `help:effective-pom`.

**Spec:** `docs/superpowers/specs/2026-11-20-discovery-surefire-includes-design.md`

**Branch:** `m2/a1-discovery-includes` (from `main` `f47b503`).

## Global Constraints

- Defaults when the project sets none: includes `**/Test*.java`, `**/*Test.java`,
  `**/*Tests.java`, `**/*TestCase.java`; excludes `**/*$*`.
- Project-set excludes replace the default excludes (Surefire's rule).
- Unsupported Surefire settings `test`, `includesFile`, `excludesFile`, `groups` → error naming
  the setting; never a silently different suite.
- Class order stays alphabetical by fully qualified name; methods from `FtHarness --list`.
- The analysed project is never written to by discovery (`help:effective-pom` writes to a temp file).
- No change to `eval/`, `evidence/`, contracts or schema.

## Review Focus

1. Surefire configured only at plugin level vs. only in the `default-test` execution vs. both →
   the execution's lists win, plugin-level used otherwise. *(Task 1 test.)*
2. Includes listed as one comma-separated `<include>a,b</include>` value → both patterns apply.
   *(Task 1 test.)*
3. A Windows path (`a\b\C.class`) → matched with `/` separators like any other. *(Task 1 test.)*
4. `help:effective-pom` fails (offline, plugin missing) → the Maven call fails as today, with
   the tool error message naming `mvn` (no silent default suite). *(Task 2: existing tool-error
   path, checked by reading; no new test.)*
5. The effective POM has no `maven-surefire-plugin` entry at all → defaults. *(Task 1 test.)*

---

### Task 1: the selection layer in `runner/discovery.py`

**Files:** Modify `runner/discovery.py`; Test `runner/tests/test_discovery.py`.

**Interfaces — Produces:**
- `SurefireSelection` (frozen dataclass): `includes: Tuple[str, ...]`, `excludes: Tuple[str, ...]`.
- `DEFAULT_SELECTION = SurefireSelection(includes=(…4 defaults…), excludes=("**/*$*",))`.
- `class DiscoveryConfigError(ValueError)`.
- `surefire_selection(effective_pom: str) -> SurefireSelection` (raises `DiscoveryConfigError`).
- `is_selected(class_path: str, selection: SurefireSelection) -> bool` — `class_path` is the
  path of the `.class` file under `test-classes`, any separator.
- `test_class_names(test_classes_dir, selection=DEFAULT_SELECTION) -> List[str]`.
- `discover_order(runner, test_classes_dir, selection=DEFAULT_SELECTION) -> List[TestIdentifier]`.
- `is_surefire_test_class` is removed (only its own test used it); its cases move to
  `is_selected(…, DEFAULT_SELECTION)`.

- [ ] **Step 1: failing tests** in `test_discovery.py` (`TestClassSelection`):
  - defaults: `TestFoo.class`, `a/FooTest.class`, `FooTests.class`, `FooTestCase.class` selected;
    `Foo.class`, `FooTestHelper.class`, `FooTest$Inner.class`, `Testing$1.class` not.
  - `**/bvt/**/*.java`: `com/alibaba/json/bvt/serializer/SerializeWriterTest_14.class` selected;
    `com/alibaba/json/other/FooTest.class` not.
  - excludes: includes `**/bvt/**/*.java`, excludes `**/bvt/**/Skip*.java` → `x/bvt/SkipMe.class`
    not selected; with project excludes set, `x/bvt/Outer$Inner.class` IS selected.
  - `%regex[.*Plain.*]` selects `p/PlainCase.class`.
  - Windows separators: `com\\alibaba\\json\\bvt\\A.class` selected by `**/bvt/**/*.java`.
  - `surefire_selection`: a minimal effective-POM string (with the POM namespace
    `http://maven.apache.org/POM/4.0.0`) — plugin-level `<includes>` only → those; execution
    `default-test` `<includes>` overriding plugin-level → the execution's; one
    `<include>a/**/*.java,b/**/*.java</include>` → two patterns; no surefire plugin → defaults;
    `<test>Foo</test>` in the configuration → `DiscoveryConfigError` mentioning `test`.
  - `test_class_names(root, SurefireSelection(("**/bvt/**/*.java",), ()))` on a temp tree with
    `a/bvt/Plain.class`, `a/OtherTest.class` → `["a.bvt.Plain"]`.
- [ ] **Step 2:** `py -3 -m unittest runner.tests.test_discovery.TestClassSelection` →
  `ImportError: cannot import name 'SurefireSelection'`.
- [ ] **Step 3:** implement. Pattern → regex: normalise `\\` to `/`; strip a trailing `.java` or
  `.class` from pattern and path; `**/` → `(?:.*/)?`, `**` → `.*`, `*` → `[^/]*`, `?` → `[^/]`,
  everything else escaped; full match. `%regex[r]` → `re.fullmatch(r, path_with_.class)`.
- [ ] **Step 4:** same command → OK; then the whole `runner.tests.test_discovery` (fixture class
  included) → OK, so the fixture's order is unchanged under `DEFAULT_SELECTION`.

---

### Task 2: Maven reads the effective POM; `diagnose()` uses the project's selection; docs

**Files:** Modify `runner/order_runner.py` (`maven_test_classpath(project_dir, effective_pom=None)`),
`runner/diagnose.py`; Create `runner/tests/resources/custom-includes/` (`pom.xml` with surefire
`<includes><include>**/bvt/**/*.java</include></includes>` and
`<excludes><exclude>**/bvt/**/Skip*.java</exclude></excludes>`; tests
`src/test/java/pkg/bvt/PlainCase.java` (two `@Test`), `src/test/java/pkg/bvt/SkipMeTest.java`
(one `@Test`), `src/test/java/pkg/OutsideTest.java` (one `@Test`)); Test
`runner/tests/test_discovery.py` (new `TestDiscoveryOnCustomIncludes`, real Maven/JVM);
Docs: `runner/README.md`, `docs/04-Implementation/diagnosis-runs.md`, risk register row (M2's
fix — status line only), `docs/05-Testing/real-case-protocol.md` *not touched* (M3's; the
handover tells M3), `docs/evidence-m2.md`, `docs/genai-log-m2.md`, `docs/08-MidEval/genai-register.md`,
`docs/10-Final1/iteration-2-plan.md` (W26a row note), `docs/09-Team/members.md`,
`docs/10-Final1/handover-m1-m3.md`.

**Interfaces — Consumes:** Task 1's `surefire_selection`, `discover_order(…, selection)`,
`DiscoveryConfigError`.

- [ ] **Step 1: failing tests**
  - `TestDiscoveryOnCustomIncludes.setUpClass`: `maven_test_classpath(CUSTOM, effective_pom=tmp)`,
    `selection = surefire_selection(tmp.read_text())`, `order = discover_order(runner, CUSTOM /
    "target" / "test-classes", selection)`.
  - `test_only_the_projects_includes_are_discovered`: `{t.class_name for t in order} ==
    {"pkg.bvt.PlainCase"}` and two methods.
  - `test_effective_pom_is_written_outside_the_project`: the temp file exists, and no new file
    appears in `CUSTOM` outside `target/` (compare a listing before/after, `target` excluded).
  - `test_diagnose.py`: `diagnose()` turns a `DiscoveryConfigError` into `DiagnoseInputError`
    (patch `runner.diagnose.surefire_selection` to raise; patch the Maven call so nothing runs).
- [ ] **Step 2:** run them → `TypeError: maven_test_classpath() got an unexpected keyword
  argument 'effective_pom'` / `ImportError`.
- [ ] **Step 3:** implement: `maven_test_classpath` appends `help:effective-pom
  -Doutput=<path>` to its one `mvn` call when `effective_pom` is given. `diagnose()` creates the
  temp path, passes it, builds the selection (catching `DiscoveryConfigError` →
  `DiagnoseInputError`), passes it to `discover_order`; the `--order` "not among the project's
  tests" message names the include patterns used.
- [ ] **Step 4:** every `runner/tests/test_*.py`, `eval/tests/test_*.py`, `ui.tests.test_server`
  → OK; real CLI on F1 → `VERIFIED (sequence)` as before.
- [ ] **Step 5:** FJ-03 by hand, if a fastjson checkout at `e05e9c5` can be made in the scratch
  folder: `discover_order` finds `SerializeWriterTest_14#test_writer_1` and
  `MaxBufSizeTest#test_max_buf`; record the count. If not feasible here, record "not yet run" and
  ask M3 to run it as W26a step 6's first check.
- [ ] **Step 6:** docs, fresh whole-branch review, verification, hand over.
