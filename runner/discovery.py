"""Original-order discovery (W7, ADR-004): the test methods Maven Surefire would run, classes in
alphabetical order, methods in JUnit's own order."""

import os
from pathlib import Path
from typing import List

from eval.baseline import TestIdentifier


def is_surefire_test_class(simple_name: str) -> bool:
    """Surefire's default includes: Test*, *Test, *Tests, *TestCase. Inner classes ($) excluded."""
    if "$" in simple_name:
        return False
    return simple_name.startswith("Test") or simple_name.endswith(("Test", "Tests", "TestCase"))


def test_class_names(test_classes_dir) -> List[str]:
    root = Path(test_classes_dir)
    names = []
    for folder, _subfolders, files in os.walk(root):
        for name in files:
            if name.endswith(".class") and is_surefire_test_class(name[: -len(".class")]):
                relative = (Path(folder) / name).relative_to(root).with_suffix("")
                names.append(".".join(relative.parts))
    return sorted(names)


def discover_order(runner, test_classes_dir) -> List[TestIdentifier]:
    """`runner` is an order_runner.OrderRunner (it owns the harness that asks JUnit)."""
    return runner.list_methods(test_class_names(test_classes_dir))
