"""Tests for evidence/extract.py (Member 1), Phase 2: depth 1 with lifecycle attribution.

Input: Member 1's own test classes in evidence/tests/resources/m1-selftest/ (not a
project fixture). Compile them first, with JDK 8 like the rest of the project:

    mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile

Expected offsets were read by hand from JDK 8 `javap -c -p` output of those classes
(recorded in docs/evidence-m1.md). Run from the repository root:

    python3 -m unittest evidence.tests.test_extract -v
"""
import json
import os
import shutil
import subprocess
import sys
import unittest

from evidence import extract

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.join(HERE, "resources", "m1-selftest", "target")
CLASSES = os.path.join(TARGET, "classes")
TEST_CLASSES = os.path.join(TARGET, "test-classes")
REPO_ROOT = os.path.dirname(os.path.dirname(HERE))


def summary(accesses):
    """(access, resource_id, class, method, offset, via) tuples, easy to compare."""
    return [(a["access"], a["resource_id"], a["class"], a["method"], a["bytecode_offset"], a["via"])
            for a in accesses]


@unittest.skipUnless(os.path.isdir(TEST_CLASSES),
                     "self-test classes not compiled: run mvn -B -q -f "
                     "evidence/tests/resources/m1-selftest/pom.xml test-compile")
@unittest.skipUnless(shutil.which(extract.javap_command()), "javap not found (need a JDK 8+)")
class DepthOneExtractionTest(unittest.TestCase):

    def analyse(self, test_id):
        return extract.analyse_test(extract.Project([CLASSES, TEST_CLASSES]), test_id, depth=1)

    def test_finds_exactly_the_four_known_accesses_with_offsets(self):
        result = self.analyse("m1selftest.M1SelfTest#writesAndReads")
        body = ("m1selftest.M1SelfTest", "writesAndReads")
        self.assertEqual(summary(result["accesses"]), [
            ("WRITE", "m1selftest.SelfTestState#counter", *body, 1, "TEST_METHOD"),
            ("READ", "m1selftest.SelfTestState#counter", *body, 4, "TEST_METHOD"),
            ("WRITE", "sysprop:m1.selftest.key", *body, 12, "TEST_METHOD"),
            ("READ", "sysprop:m1.selftest.key", *body, 18, "TEST_METHOD"),
        ])
        self.assertEqual(result["unsupported_observations"], [])
        for access in result["accesses"]:
            self.assertEqual(access["depth"], 1)
            self.assertEqual(access["call_path"], [{"class": access["class"], "method": access["method"],
                                                    "bytecode_offset": access["bytecode_offset"]}])

    def test_resource_shapes_match_member3_shared_resource(self):
        accesses = self.analyse("m1selftest.M1SelfTest#writesAndReads")["accesses"]
        self.assertEqual(accesses[0]["resource"],
                         {"kind": "static-field", "class": "m1selftest.SelfTestState", "field": "counter"})
        self.assertEqual(accesses[2]["resource"], {"kind": "system-property", "key": "m1.selftest.key"})

    def test_junit4_lifecycle_and_inherited_before_are_attributed(self):
        result = self.analyse("m1selftest.M1LifecycleSelfTest#emptyBody")
        sub, base = "m1selftest.M1LifecycleSelfTest", "m1selftest.M1LifecycleBase"
        self.assertEqual(summary(result["accesses"]), [
            ("WRITE", "sysprop:m1.selftest.clinit", sub, "<clinit>", 4, "CLINIT"),
            ("WRITE", "m1selftest.SelfTestState#counter", sub, "beforeAll", 1, "BEFORE_CLASS"),
            ("WRITE", "m1selftest.SelfTestState#counter", base, "baseBefore", 1, "BEFORE"),
            ("WRITE", "sysprop:m1.selftest.key", sub, "after", 2, "AFTER"),
            ("READ", "m1selftest.SelfTestState#counter", sub, "afterAll", 0, "AFTER_CLASS"),
        ])

    def test_junit3_setup_and_teardown_are_attributed(self):
        result = self.analyse("m1selftest.M1Junit3SelfTest#testNothing")
        cls = "m1selftest.M1Junit3SelfTest"
        self.assertEqual(summary(result["accesses"]), [
            ("WRITE", "m1selftest.SelfTestState#counter", cls, "setUp", 1, "SETUP"),
            ("READ", "sysprop:m1.selftest.flag", cls, "tearDown", 2, "TEARDOWN"),
        ])

    def test_unsupported_cases_are_reported_not_guessed(self):
        result = self.analyse("m1selftest.M1UnsupportedSelfTest#tricky")
        self.assertEqual(result["accesses"], [])      # helper()'s write is one call away
        kinds = [(u["kind"], u["bytecode_offset"]) for u in result["unsupported_observations"]]
        self.assertEqual(kinds, [("SYSPROP_NON_CONSTANT_KEY", 23), ("REFLECTION", 37), ("DEPTH_LIMIT", 40)])


@unittest.skipUnless(os.path.isdir(TEST_CLASSES), "self-test classes not compiled")
class CommandLineTest(unittest.TestCase):

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "evidence.extract", *args],
                              capture_output=True, text=True, cwd=REPO_ROOT)

    def test_prints_contract_json_on_stdout(self):
        if not shutil.which(extract.javap_command()):
            self.skipTest("javap not found")
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1SelfTest#writesAndReads", "--depth", "1")
        self.assertEqual(done.returncode, 0, done.stderr)
        output = json.loads(done.stdout)
        self.assertEqual(output["instrumentation_level"], "static-only")
        self.assertEqual(len(output["tests"]["m1selftest.M1SelfTest#writesAndReads"]["accesses"]), 4)

    def assert_input_error(self, done, text):
        self.assertEqual(done.returncode, 2)
        self.assertEqual(done.stdout, "")
        self.assertIn(text, done.stderr)

    def test_missing_class_directory_is_an_input_error(self):
        done = self.run_cli("--classes", "/no/such/dir", "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1SelfTest#writesAndReads", "--depth", "1")
        self.assert_input_error(done, "class directory not found")

    def test_unknown_test_method_is_an_input_error(self):
        if not shutil.which(extract.javap_command()):
            self.skipTest("javap not found")
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1SelfTest#noSuchMethod", "--depth", "1")
        self.assert_input_error(done, "test method not found")

    def test_unimplemented_depth_is_refused_clearly(self):
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1SelfTest#writesAndReads")
        self.assert_input_error(done, "not implemented yet")


if __name__ == "__main__":
    unittest.main()
