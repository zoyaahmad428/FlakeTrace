# Discovery reads the project's own Surefire includes (design)

*2026-11-20 · M2 · Status: proposed, awaiting M2's approval · item A1 · unblocks W26a steps 6–9
(M3, real case FJ-03) · risk-register row "Discovery misses real test classes with custom Surefire
includes".*

## Why

`runner/discovery.py` treats a class as a test only if its name matches Surefire's *default*
includes (`Test*`, `*Test`, `*Tests`, `*TestCase`). fastjson replaces them with
`**/bvt/**/*.java`, so the FJ-03 polluter `SerializeWriterTest_14` is never discovered and
`diagnose --order` refuses the case. The original order must be **the tests the project's own
build runs** — no more, no fewer.

## Goals / non-goals / anti-goals

- **Goal:** discovery uses the project's effective Surefire `includes` and `excludes`; Maven's
  defaults only when the project sets none.
- **Goal:** FJ-03's known polluter and victim are discovered; the fixture's order is unchanged.
- **Non-goal:** `-Dtest=…`, `includesFile`/`excludesFile`, groups/categories, JUnit 5 — reported as
  unsupported if present, not silently ignored.
- **Anti-goal:** a silently different suite (more or fewer tests than Maven would run); any write
  into the analysed project.

## Approaches

| | A. Effective POM from Maven (chosen) | B. Parse `pom.xml` | C. No name filter |
| --- | --- | --- | --- |
| Parent POMs, profiles, properties | correct | silently wrong | — |
| Same suite as the project's build | yes | single-POM only | no (adds excluded tests) |
| Cost | `help:effective-pom` added to the existing Maven call; plugin downloaded once | none | none |

Chosen by Claude on M2's standing delegation: A — the only one that equals "what the project's
build runs" for every project layout.

## Design

- **Read the settings:** `maven_test_classpath()` already runs one `mvn` command; it gains
  `help:effective-pom -Doutput=<tmp>` in the same call, and returns (or the caller reads) the
  effective POM text. Probed 2026-11-20 on the fixture: exit 0, nothing written to the project,
  about 6 s alone after the first download.
- **Extract:** in the effective POM, the `maven-surefire-plugin` configuration of the
  `default-test` execution, falling back to the plugin-level configuration: the lists
  `includes/include` and `excludes/exclude`. If none: Surefire's defaults — includes
  `**/Test*.java`, `**/*Test.java`, `**/*Tests.java`, `**/*TestCase.java`; excludes `**/*$*`.
- **Match** (Surefire's rules): a pattern ending `.java` also matches the `.class` file;
  `**` = any folders, `*` = any characters within a name, `?` = one character; patterns are
  matched against the class file's path under `target/test-classes` with `/` separators;
  a pattern not starting with `**/` applies in any folder; a dotted class name (`pkg.a.Bar`) is a
  path. A class is a test when it matches an include and no exclude. Inner classes (`$`) are
  excluded by the default exclude `**/*$*` until the project sets its own excludes (Surefire's
  rule). *(Corrected after the review, 2026-11-20: `%regex[…]` is refused instead of matched,
  because Surefire's own regex input differs between its versions; only `build/plugins` is read,
  never `pluginManagement`; a reactor POM, a second test execution, `excludedGroups`,
  `testClassesDirectory`, `dependenciesToScan` and `skip`/`skipTests`=true are refused. Then, at
  M2's request, the minors too: `**` inside a name is like `*`; `#` filters, `${…}`, and patterns
  ending `.*` or starting `/` are refused; the selection argument is required.)*
- **Unsupported settings** (`test`, `includesFile`, `excludesFile`, `groups`) present in the
  configuration → `DiagnoseInputError` naming the setting, so a different suite is never used
  silently.
- **Unchanged:** class order (alphabetical, as Surefire's `filesystem` order is not portable),
  method order from JUnit via `FtHarness --list`; the analysed project is never written to.
- **Tests first:** pattern-matcher unit tests (defaults, `**/bvt/**/*.java`, excludes, `%regex`,
  inner classes); a tiny Maven test project under `runner/tests/resources/custom-includes/` whose
  pom sets `<include>**/bvt/**/*.java</include>` and an exclude, with one class that matches only
  the custom include and one that matches only the default — today's code fails it; the fixture's
  discovered order is identical before and after; the real FJ-03 discovery is checked once by hand
  on the fastjson checkout (M3's protocol) and recorded.

## Left to the builder

Helper names; XML namespace handling of the effective POM; where the effective-POM text is passed
(return value vs. a second function).

## Limitations to state

Needs `maven-help-plugin` (downloaded on first use, like every other plugin). Surefire's
`runOrder` other than alphabetical is not reproduced (unchanged from today).
