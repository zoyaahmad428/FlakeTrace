"""Original-order discovery (W7, ADR-004): the test methods Maven Surefire would run, classes in
alphabetical order, methods in JUnit's own order. Which classes are tests follows the project's
own Surefire includes and excludes (read from its effective POM), falling back to Surefire's
defaults only when the project sets none -- fastjson's `**/bvt/**/*.java` is the real case that
needed this (W26a, FJ-03)."""

import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from eval.baseline import TestIdentifier


@dataclass(frozen=True)
class SurefireSelection:
    """Surefire's include and exclude patterns, as written in the POM."""

    includes: Tuple[str, ...]
    excludes: Tuple[str, ...]


# Surefire's defaults when a project sets no includes / no excludes.
DEFAULT_SELECTION = SurefireSelection(
    includes=("**/Test*.java", "**/*Test.java", "**/*Tests.java", "**/*TestCase.java"),
    excludes=("**/*$*",),
)

# Settings that choose a different set of tests than includes/excludes; not supported, so a
# project using them is refused rather than diagnosed on a silently different suite.
UNSUPPORTED_SETTINGS = ("test", "includesFile", "excludesFile", "groups", "excludedGroups",
                        "testClassesDirectory", "dependenciesToScan")
# Settings that matter only when set to true (Surefire would run no tests at all).
UNSUPPORTED_IF_TRUE = ("skip", "skipTests")


class DiscoveryConfigError(ValueError):
    """The project's Surefire configuration uses a setting discovery does not support."""


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(element, name: str):
    return next((c for c in element if _local(c.tag) == name), None)


def _patterns(configuration, list_name: str) -> Optional[Tuple[str, ...]]:
    container = _child(configuration, list_name) if configuration is not None else None
    if container is None:
        return None
    patterns = []
    for item in container:
        patterns += [p.strip() for p in (item.text or "").split(",") if p.strip()]
    return tuple(patterns) or None


def _refuse(what: str):
    raise DiscoveryConfigError(
        f"the project's Surefire configuration {what}, which FlakeTrace's test discovery does not "
        "support; it would diagnose a different set of tests than the project's build runs")


def _build_plugin(root, artifact_id: str):
    """The plugin in project/build/plugins -- never pluginManagement, which Maven prints first
    and which does not configure the build by itself (review of A1)."""
    build = _child(root, "build")
    plugins = _child(build, "plugins") if build is not None else None
    for plugin in plugins if plugins is not None else []:
        identifier = _child(plugin, "artifactId")
        if identifier is not None and identifier.text == artifact_id:
            return plugin
    return None


def surefire_selection(effective_pom: str) -> SurefireSelection:
    """The includes/excludes Surefire's `default-test` execution uses: that execution's own
    configuration first, then the plugin-level configuration, then Surefire's defaults."""
    root = ET.fromstring(effective_pom)
    if _local(root.tag) == "projects":
        _refuse("is a multi-module reactor; diagnose one module (run --project on its folder)")
    plugin = _build_plugin(root, "maven-surefire-plugin")
    if plugin is None:
        return DEFAULT_SELECTION
    plugin_config = _child(plugin, "configuration")
    execution_config = None
    executions = _child(plugin, "executions")
    for execution in executions if executions is not None else []:
        identifier = _child(execution, "id")
        goals = _child(execution, "goals")
        runs_tests = goals is not None and any((g.text or "").strip() == "test" for g in goals)
        if identifier is not None and identifier.text == "default-test":
            execution_config = _child(execution, "configuration")
        elif runs_tests:
            _refuse(f"adds a second test execution ({(identifier.text if identifier is not None else '?')})")
    for configuration in (execution_config, plugin_config):
        if configuration is None:
            continue
        for setting in UNSUPPORTED_SETTINGS:
            if _child(configuration, setting) is not None:
                _refuse(f"sets <{setting}>")
        for setting in UNSUPPORTED_IF_TRUE:
            flag = _child(configuration, setting)
            if flag is not None and (flag.text or "").strip().lower() == "true":
                _refuse(f"sets <{setting}>true</{setting}>")

    def first(list_name: str) -> Optional[Tuple[str, ...]]:
        for configuration in (execution_config, plugin_config):
            found = _patterns(configuration, list_name)
            if found is not None:
                return found
        return None

    selection = SurefireSelection(includes=first("includes") or DEFAULT_SELECTION.includes,
                                  excludes=first("excludes") or DEFAULT_SELECTION.excludes)
    for pattern in selection.includes + selection.excludes:
        if "${" in pattern:
            _refuse(f"uses a pattern with an unresolved property ({pattern})")
        if pattern.startswith("%regex["):
            # Surefire's own regex input differs between its versions and from a plain path.
            _refuse(f"uses a %regex pattern ({pattern})")
        if "#" in pattern:
            _refuse(f"uses a method filter ({pattern}); Surefire itself refuses these in includes")
        if pattern.endswith(".*") or pattern.startswith("/"):
            # Surefire 2.x and 3.x match these differently; write e.g. **/FooTest.java instead.
            _refuse(f"uses a pattern Surefire 2.x and 3.x read differently ({pattern}); write it as "
                    "**/Name.java")
    return selection


def project_selection(effective_pom_file) -> SurefireSelection:
    """The selection in the effective POM Maven wrote to `effective_pom_file`."""
    return surefire_selection(Path(effective_pom_file).read_text(encoding="utf-8"))


def _pattern_regex(pattern: str) -> str:
    """Surefire's Ant-style pattern as a regex over a class path without its extension. As in
    Surefire: a dotted class name (no `/`, no extension) is a path, and a pattern that does not
    start with `**/` is matched in any folder."""
    pattern = pattern.replace("\\", "/")
    if "/" not in pattern and not re.search(r"\.(java|class)$", pattern):
        pattern = pattern.replace(".", "/")
    pattern = re.sub(r"\.(java|class)$", "", pattern).lstrip("/")
    if not pattern.startswith("**/"):
        pattern = "**/" + pattern
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            # ** means "any folders" only as a whole path segment; inside a name it is like *.
            whole_segment = (i == 0 or pattern[i - 1] == "/") and i + 2 == len(pattern)
            out.append(".*" if whole_segment else "[^/]*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return "".join(out)


def _matches(pattern: str, class_path: str) -> bool:
    return re.fullmatch(_pattern_regex(pattern), re.sub(r"\.class$", "", class_path)) is not None


def is_selected(class_path: str, selection: SurefireSelection) -> bool:
    """True when the `.class` file at `class_path` (under test-classes) matches an include and no
    exclude."""
    path = class_path.replace("\\", "/")
    return (any(_matches(p, path) for p in selection.includes)
            and not any(_matches(p, path) for p in selection.excludes))


def test_class_names(test_classes_dir, selection: SurefireSelection) -> List[str]:
    root = Path(test_classes_dir)
    names = []
    for folder, _subfolders, files in os.walk(root):
        for name in files:
            if not name.endswith(".class"):
                continue
            relative = (Path(folder) / name).relative_to(root)
            if is_selected(relative.as_posix(), selection):
                names.append(".".join(relative.with_suffix("").parts))
    return sorted(names)


def discover_order(runner, test_classes_dir, selection: SurefireSelection) -> List[TestIdentifier]:
    """`runner` is an order_runner.OrderRunner (it owns the harness that asks JUnit). `selection` is
    required -- the project's own, from project_selection() -- so no caller gets the default test
    names by forgetting it."""
    return runner.list_methods(test_class_names(test_classes_dir, selection))
