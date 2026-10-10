"""Ordered single-JVM test runner for JUnit 4 (W6).
Design: docs/03-Design/decisions/ADR-003-order-runner-junitcore-harness.md.

Implements the OrderRunner protocol from eval/baseline.py: each run_ordered call starts one
fresh JVM that runs the given tests in exactly the given order (runner/harness/FtHarness.java).
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Sequence

from eval.baseline import FailureSignature, RunOutcome, TestIdentifier

HARNESS_SOURCE = Path(__file__).resolve().parent / "harness" / "FtHarness.java"

# A stack is cut at the first frame from JUnit's runner, reflection or the harness. These
# frames differ between JDK 8 and JDK 21 and say nothing about the failure itself.
_FRAMEWORK_PREFIXES = (
    "org.junit.runner.",
    "org.junit.runners.",
    "org.junit.internal.runners.",
    "sun.reflect.",
    "jdk.internal.reflect.",
    "java.lang.reflect.",
    "FtHarness.",
)

# Same masks as the POC's frozen signature definition (docs/05-Testing/poc/frozen-definitions.md).
_MESSAGE_MASKS = [
    (re.compile(r"0x[0-9a-fA-F]+"), "<HEX>"),
    (re.compile(r"@[0-9a-fA-F]{4,}"), "@<ID>"),
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\S*"), "<TS>"),
    (re.compile(r"/tmp/\S+"), "<TMP>"),
    (re.compile(r"(/[\w.\-]+){2,}"), "<PATH>"),
    (re.compile(r"\d+"), "<N>"),
]

_UNESCAPES = {"t": "\t", "n": "\n", "r": "\r", "\\": "\\"}


class ToolError(RuntimeError):
    """A required tool is missing or the harness cannot be compiled -- not a bug in FlakeTrace."""


def normalise_stack(frames: List[str]) -> str:
    kept = []
    for frame in frames:
        if frame.startswith(_FRAMEWORK_PREFIXES):
            break
        kept.append(frame)
    return "\n".join(kept)


def normalise_message(message: str) -> str:
    lines = message.strip().splitlines()
    first = lines[0].strip() if lines else ""
    for pattern, replacement in _MESSAGE_MASKS:
        first = pattern.sub(replacement, first)
    return first[:200]


def _unescape(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            out.append(_UNESCAPES.get(text[i + 1], text[i + 1]))
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def parse_results(
    text: str, order: Sequence[TestIdentifier], missing_type: str, missing_message: str
) -> Dict[TestIdentifier, RunOutcome]:
    """Turn the harness's result file into one RunOutcome per test in `order`. A test with no
    complete result line (the JVM crashed or timed out first) fails with `missing_type`."""
    results: Dict[TestIdentifier, RunOutcome] = {}
    # Split on "\n" only (the harness escapes it, but not every character splitlines() splits on),
    # and drop the last piece: it is "" after a complete line, or a line cut off mid-write.
    for line in text.split("\n")[:-1]:
        fields = line.split("\t")
        if len(fields) != 6:
            continue
        index, _spec, status, exception_type, message, frames = fields
        test = order[int(index)]
        if status == "PASS":
            results[test] = RunOutcome(passed=True)
        elif status == "SKIP":
            results[test] = RunOutcome(
                passed=False,
                failure_signature=FailureSignature(
                    "flaketrace.NotExecuted", "", "ignored or an assumption failed"
                ),
            )
        else:
            frame_list = _unescape(frames).split("|") if frames else []
            results[test] = RunOutcome(
                passed=False,
                failure_signature=FailureSignature(
                    exception_type, normalise_stack(frame_list), normalise_message(_unescape(message))
                ),
            )
    for test in order:
        if test not in results:
            results[test] = RunOutcome(
                passed=False, failure_signature=FailureSignature(missing_type, "", missing_message)
            )
    return results


def _tool(name: str) -> str:
    # shutil.which finds mvn.cmd / java.exe on Windows; a bare "mvn" in an argument list does not.
    path = shutil.which(name)
    if path is None:
        raise ToolError(f"'{name}' not found on PATH")
    return path


def maven_test_classpath(project_dir) -> List[str]:
    """Compile the project's tests and return its test classpath, using only the jars the
    project itself declares (JUnit included). Writes only to the project's target/."""
    project = Path(project_dir).resolve()
    with tempfile.TemporaryDirectory(prefix="flaketrace-cp-") as tmp:
        cp_file = Path(tmp) / "cp.txt"
        subprocess.run(
            [
                _tool("mvn"), "-B", "-q", "-f", str(project / "pom.xml"),
                "test-compile", "dependency:build-classpath", f"-Dmdep.outputFile={cp_file}",
            ],
            check=True,
        )
        jars = [p for p in cp_file.read_text(encoding="utf-8").strip().split(os.pathsep) if p]
    return [str(project / "target" / "test-classes"), str(project / "target" / "classes")] + jars


class OrderRunner:
    """Satisfies eval.baseline.OrderRunner. One fresh JVM per run_ordered call."""

    def __init__(self, classpath: Sequence[str], working_dir=None, timeout_s: float = 120.0):
        """`working_dir` is where the tests run; pass the target project's directory, as Maven
        would, so tests that use relative paths behave the same. None = the caller's directory."""
        self.classpath = list(classpath)
        self._working_dir = working_dir
        self._timeout_s = timeout_s
        self._java = _tool("java")
        self._harness_dir = tempfile.mkdtemp(prefix="flaketrace-harness-")
        compiled = subprocess.run(
            [_tool("javac"), "-source", "8", "-target", "8", "-Xlint:-options",
             "-d", self._harness_dir, str(HARNESS_SOURCE)],
            env=_env_with_classpath(self.classpath),
            capture_output=True,
            text=True,
        )
        if compiled.returncode != 0:
            raise ToolError(f"could not compile FtHarness:\n{compiled.stderr}")

    def run_ordered(self, order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]:
        order = list(order)
        if len(set(order)) != len(order):
            raise ValueError("order contains the same test more than once")
        if not order:
            return {}
        with tempfile.TemporaryDirectory(prefix="flaketrace-run-") as tmp:
            result_file = Path(tmp) / "results.tsv"
            try:
                finished = subprocess.run(
                    [self._java, "FtHarness", str(result_file)],
                    input="".join(f"{test}\n" for test in order),
                    env=_env_with_classpath([self._harness_dir] + self.classpath),
                    cwd=self._working_dir,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=self._timeout_s,
                )
                missing = (
                    "flaketrace.JvmCrash",
                    f"JVM exited with code {finished.returncode} before this test reported",
                )
            except subprocess.TimeoutExpired:
                missing = ("flaketrace.Timeout", f"JVM exceeded {self._timeout_s}s")
            text = result_file.read_text(encoding="utf-8") if result_file.exists() else ""
        return parse_results(text, order, *missing)

    def list_methods(self, class_names: Sequence[str]) -> List[TestIdentifier]:
        """The test methods of each class, in the order JUnit would run them (FtHarness --list).
        Classes JUnit cannot run (abstract, no @Test methods, fail to load) are left out."""
        with tempfile.TemporaryDirectory(prefix="flaketrace-list-") as tmp:
            result_file = Path(tmp) / "methods.txt"
            subprocess.run(
                [self._java, "FtHarness", "--list", str(result_file)],
                input="".join(f"{name}\n" for name in class_names),
                env=_env_with_classpath([self._harness_dir] + self.classpath),
                cwd=self._working_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self._timeout_s,
                check=True,
            )
            lines = result_file.read_text(encoding="utf-8").split("\n")[:-1]
        return [TestIdentifier(*line.split("#", 1)) for line in lines]


def java_version() -> str:
    """First line of `java -version` (printed on stderr), for the execution record."""
    finished = subprocess.run([_tool("java"), "-version"], capture_output=True, text=True)
    return finished.stderr.strip().splitlines()[0]


def _env_with_classpath(classpath: Sequence[str]) -> Dict[str, str]:
    # CLASSPATH in the environment instead of -cp avoids Windows' ~32k command-line limit.
    return dict(os.environ, CLASSPATH=os.pathsep.join(classpath))
