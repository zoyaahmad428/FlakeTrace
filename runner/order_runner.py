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
    """Turn the harness's result file into one RunOutcome per test in `order`."""
    results: Dict[TestIdentifier, RunOutcome] = {}
    for line in text.splitlines():
        index, _spec, status, exception_type, message, frames = line.split("\t")
        test = order[int(index)]
        if status == "PASS":
            results[test] = RunOutcome(passed=True)
        else:
            frame_list = _unescape(frames).split("|") if frames else []
            results[test] = RunOutcome(
                passed=False,
                failure_signature=FailureSignature(
                    exception_type, normalise_stack(frame_list), normalise_message(_unescape(message))
                ),
            )
    return results


def _tool(name: str) -> str:
    # shutil.which finds mvn.cmd / java.exe on Windows; a bare "mvn" in an argument list does not.
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"'{name}' not found on PATH")
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

    def __init__(self, classpath: Sequence[str], timeout_s: float = 120.0):
        self.classpath = list(classpath)
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
            raise RuntimeError(f"could not compile FtHarness:\n{compiled.stderr}")

    def run_ordered(self, order: List[TestIdentifier]) -> Dict[TestIdentifier, RunOutcome]:
        order = list(order)
        with tempfile.TemporaryDirectory(prefix="flaketrace-run-") as tmp:
            result_file = Path(tmp) / "results.tsv"
            subprocess.run(
                [self._java, "FtHarness", str(result_file)],
                input="".join(f"{test}\n" for test in order),
                env=_env_with_classpath([self._harness_dir] + self.classpath),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self._timeout_s,
            )
            text = result_file.read_text(encoding="utf-8")
        return parse_results(text, order, "flaketrace.JvmCrash", "")


def _env_with_classpath(classpath: Sequence[str]) -> Dict[str, str]:
    # CLASSPATH in the environment instead of -cp avoids Windows' ~32k command-line limit.
    return dict(os.environ, CLASSPATH=os.pathsep.join(classpath))
