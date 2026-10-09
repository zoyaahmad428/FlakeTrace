"""Tests for evidence/extract.py (Member 1): lifecycle attribution (Phase 2), call depth (Phase 3), pairs (Phase 4),
ground truth (Phase 5).

Input: Member 1's own test classes in evidence/tests/resources/m1-selftest/ (not a
project fixture). Compile them first, with JDK 8 like the rest of the project:

    mvn -B -q -f evidence/tests/resources/m1-selftest/pom.xml test-compile

Expected offsets were read by hand from JDK 8 `javap -c -p` output of those classes
(recorded in docs/evidence-m1.md). Run from the repository root:

    python3 -m unittest evidence.tests.test_extract -v

Tests that need compiled classes or javap skip when they are missing. Set
FLAKETRACE_REQUIRE_JVM=1 (CI does) to make them fail instead, so a broken setup
can never pass silently.
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
FIXTURE_TARGET = os.path.join(REPO_ROOT, "fixtures", "od-fixture", "target")
FIXTURE_DIRS = [os.path.join(FIXTURE_TARGET, "classes"), os.path.join(FIXTURE_TARGET, "test-classes")]


REQUIRE_JVM = os.environ.get("FLAKETRACE_REQUIRE_JVM") == "1"


def needs(condition, reason):
    """Skip the test class when `condition` is false, or fail it under FLAKETRACE_REQUIRE_JVM=1."""
    if condition or not REQUIRE_JVM:
        return unittest.skipUnless(condition, reason)

    def fail_class(cls):
        def setUpClass(klass):
            raise AssertionError("FLAKETRACE_REQUIRE_JVM=1 but " + reason)
        cls.setUpClass = classmethod(setUpClass)
        return cls
    return fail_class


def need_javap(test):
    """Inside a test: skip (or fail under FLAKETRACE_REQUIRE_JVM=1) when javap is missing."""
    if not shutil.which(extract.javap_command()):
        if REQUIRE_JVM:
            test.fail("FLAKETRACE_REQUIRE_JVM=1 but javap not found")
        test.skipTest("javap not found")


HAS_JAVAP = bool(shutil.which(extract.javap_command()))
NO_JAVAP = "javap not found (need a JDK 8+)"
NO_SELFTEST = ("self-test classes not compiled: run mvn -B -q -f "
               "evidence/tests/resources/m1-selftest/pom.xml test-compile")


def summary(accesses):
    """(access, resource_id, class, method, offset, via) tuples, easy to compare."""
    return [(a["access"], a["resource_id"], a["class"], a["method"], a["bytecode_offset"], a["via"])
            for a in accesses]


@needs(os.path.isdir(TEST_CLASSES), NO_SELFTEST)
@needs(HAS_JAVAP, NO_JAVAP)
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


def path_of(access):
    """'Class.method@offset > ...' for an access's call_path, without the package."""
    return " > ".join("%s.%s@%d" % (f["class"].split(".")[-1], f["method"], f["bytecode_offset"])
                      for f in access["call_path"])


@needs(os.path.isdir(TEST_CLASSES), NO_SELFTEST)
@needs(HAS_JAVAP, NO_JAVAP)
class CallDepthTest(unittest.TestCase):
    """Phase 3. Expected values read by hand from JDK 8 javap of M1DepthSelfTest."""

    def analyse(self, test_id, depth):
        return extract.analyse_test(extract.Project([CLASSES, TEST_CLASSES]), test_id, depth)

    def paths(self, test_id, depth):
        return [(a["access"], a["resource_id"], a["depth"], path_of(a))
                for a in self.analyse(test_id, depth)["accesses"]]

    def kinds(self, test_id, depth):
        return [(u["kind"], u["method"], u["bytecode_offset"])
                for u in self.analyse(test_id, depth)["unsupported_observations"]]

    def test_access_two_calls_down_appears_only_at_depth_3(self):
        test = "m1selftest.M1DepthSelfTest#callsDown"
        write2 = ("WRITE", "m1selftest.SelfTestState#counter", 2,
                  "M1DepthSelfTest.callsDown@0 > M1DepthSelfTest.level2@2")
        write3 = ("WRITE", "sysprop:m1.selftest.deep", 3,
                  "M1DepthSelfTest.callsDown@0 > M1DepthSelfTest.level2@5 > M1DepthSelfTest.level3@4")
        self.assertEqual(self.paths(test, 1), [])
        self.assertEqual(self.paths(test, 2), [write2])
        self.assertEqual(self.paths(test, 3), [write2, write3])     # level4 (depth 4) never

    def test_depth_limit_is_reported_where_the_walk_stops(self):
        test = "m1selftest.M1DepthSelfTest#callsDown"
        self.assertEqual(self.kinds(test, 1), [("DEPTH_LIMIT", "callsDown", 0)])
        self.assertEqual(self.kinds(test, 3), [("DEPTH_LIMIT", "level3", 8)])

    def test_recursion_terminates(self):
        self.assertEqual(self.paths("m1selftest.M1DepthSelfTest#recursion", 3), [
            ("WRITE", "m1selftest.SelfTestState#counter", 3,
             "M1DepthSelfTest.recursion@1 > M1DepthSelfTest.ping@7 > M1DepthSelfTest.pong@1")])

    def test_virtual_dispatch_follows_only_the_named_target_and_says_so(self):
        test = "m1selftest.M1DepthSelfTest#dispatch"
        self.assertEqual(self.paths(test, 3), [
            ("WRITE", "m1selftest.SelfTestState#counter", 2,
             "M1DepthSelfTest.dispatch@9 > SelfTestBase.work@2")])   # SelfTestChild's write not claimed
        self.assertIn(("VIRTUAL_DISPATCH", "dispatch", 9), self.kinds(test, 3))

    def test_in_process_default_depth_is_2(self):
        result = extract.analyse_test(extract.Project([CLASSES, TEST_CLASSES]),
                                      "m1selftest.M1DepthSelfTest#callsDown")
        self.assertEqual([a["depth"] for a in result["accesses"]], [2])

    def test_depth_1_results_are_unchanged(self):
        self.assertEqual(len(self.analyse("m1selftest.M1SelfTest#writesAndReads", 3)["accesses"]), 4)


def edge_summary(pair):
    """[(resource_id, [write 'Class.method@offset'], [read 'Class.method@offset'])] for a pair."""
    def loc(access):
        return "%s.%s@%d" % (access["class"].split(".")[-1], access["method"], access["bytecode_offset"])
    return [(e["resource_id"], [loc(a) for a in e["polluter_write_locations"]],
             [loc(a) for a in e["victim_read_locations"]]) for e in pair["edges"]]


def analyse_pair(class_dirs, polluter, victim, depth=extract.DEFAULT_DEPTH):
    project = extract.Project(class_dirs)
    return extract.find_edges(polluter, extract.analyse_test(project, polluter, depth),
                              victim, extract.analyse_test(project, victim, depth))


@needs(os.path.isdir(TEST_CLASSES), NO_SELFTEST)
@needs(HAS_JAVAP, NO_JAVAP)
class PairSelfTest(unittest.TestCase):
    """Phase 4 on Member 1's own test classes."""

    def test_write_in_one_test_read_in_anothers_lifecycle_is_an_edge(self):
        pair = analyse_pair([CLASSES, TEST_CLASSES], "m1selftest.M1SelfTest#writesAndReads",
                            "m1selftest.M1LifecycleSelfTest#emptyBody")
        self.assertEqual(edge_summary(pair), [
            ("m1selftest.SelfTestState#counter", ["M1SelfTest.writesAndReads@1"],
             ["M1LifecycleSelfTest.afterAll@0"])])
        self.assertEqual(pair["edges"][0]["victim_read_locations"][0]["via"], "AFTER_CLASS")
        self.assertFalse(pair["no_supported_resource_evidence"])

    def test_no_shared_resource_gives_empty_edges_and_the_flag(self):
        pair = analyse_pair([CLASSES, TEST_CLASSES], "m1selftest.M1Junit3SelfTest#testNothing",
                            "m1selftest.M1UnsupportedSelfTest#tricky")
        self.assertEqual(pair["edges"], [])
        self.assertTrue(pair["no_supported_resource_evidence"])
        self.assertIn("Missing evidence is not proof of independence.", pair["limitations"])
        self.assertEqual(len(pair["limitations"]), 7)
        sides = {(o["side"], o["kind"]) for o in pair["unsupported_observations"]}
        self.assertIn(("victim", "SYSPROP_NON_CONSTANT_KEY"), sides)
        self.assertIn(("victim", "REFLECTION"), sides)

    def test_a_write_by_the_victim_is_not_an_edge(self):
        # M1LifecycleSelfTest's @After clears m1.selftest.key (a WRITE); M1SelfTest writes it too,
        # but nobody READS it in the victim, so it must not appear.
        pair = analyse_pair([CLASSES, TEST_CLASSES], "m1selftest.M1SelfTest#writesAndReads",
                            "m1selftest.M1LifecycleSelfTest#emptyBody")
        self.assertNotIn("sysprop:m1.selftest.key", [e["resource_id"] for e in pair["edges"]])


@needs(os.path.isdir(FIXTURE_DIRS[1]),
       "fixture not compiled: run mvn -B -q -f fixtures/od-fixture/pom.xml test-compile")
@needs(HAS_JAVAP, NO_JAVAP)
class FixturePairTest(unittest.TestCase):
    """Phase 4 on Member 3's fixture. Offsets read by hand from JDK 8 javap (docs/evidence-m1.md)."""

    def pair(self, polluter, victim, depth=extract.DEFAULT_DEPTH):
        return analyse_pair(FIXTURE_DIRS, "odfixture." + polluter, "odfixture." + victim, depth)

    def test_f1_exactly_one_edge_on_config_mode(self):
        pair = self.pair("ConfigPolluterTest#pollute", "ConfigVictimTest#expectsDefaultMode")
        self.assertEqual(edge_summary(pair), [
            ("odfixture.Config#mode", ["ConfigPolluterTest.pollute@1"],
             ["ConfigVictimTest.expectsDefaultMode@1"])])

    def test_f2_edge_needs_depth_2(self):
        args = ("FeaturePolluterTest#enableTurbo", "FeatureVictimTest#expectsTurboDisabled")
        at_depth_1 = self.pair(*args, depth=1)
        self.assertEqual(at_depth_1["edges"], [])
        self.assertTrue(at_depth_1["no_supported_resource_evidence"])
        self.assertIn(("victim", "DEPTH_LIMIT"),
                      [(o["side"], o["kind"]) for o in at_depth_1["unsupported_observations"]])
        self.assertEqual(edge_summary(self.pair(*args, depth=2)), [
            ("sysprop:odfixture.turbo", ["FeaturePolluterTest.enableTurbo@4"],
             ["FeatureFlags.isTurboEnabled@2"])])

    def test_f3_each_polluter_has_its_own_flag_edge(self):
        self.assertEqual(edge_summary(self.pair("ToggleAPolluterTest#setFlagA",
                                                "ToggleVictimTest#expectsNotBothFlagsSet")),
                         [("odfixture.Toggles#flagA", ["ToggleAPolluterTest.setFlagA@1"],
                           ["ToggleVictimTest.expectsNotBothFlagsSet@0"])])
        self.assertEqual(edge_summary(self.pair("ToggleBPolluterTest#setFlagB",
                                                "ToggleVictimTest#expectsNotBothFlagsSet")),
                         [("odfixture.Toggles#flagB", ["ToggleBPolluterTest.setFlagB@1"],
                           ["ToggleVictimTest.expectsNotBothFlagsSet@6"])])

    def test_unrelated_pair_has_no_supported_evidence(self):
        pair = self.pair("ConfigPolluterTest#pollute", "FeatureVictimTest#expectsTurboDisabled")
        self.assertEqual(pair["edges"], [])
        self.assertTrue(pair["no_supported_resource_evidence"])

    def test_report_fields_fit_member3_schema(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed (pip install -r eval/requirements.txt)")
        with open(os.path.join(REPO_ROOT, "eval", "schema", "report.schema.json")) as f:
            defs = json.load(f)["$defs"]
        f2 = extract.report_fields(self.pair("FeaturePolluterTest#enableTurbo",
                                             "FeatureVictimTest#expectsTurboDisabled"))
        self.assertEqual(f2["shared_resource"], {"kind": "system-property", "key": "odfixture.turbo"})
        self.assertEqual(f2["victim_read_location"],
                         {"class": "odfixture.FeatureFlags", "method": "isTurboEnabled", "bytecode_offset": 2})
        none = extract.report_fields(self.pair("ConfigPolluterTest#pollute",
                                               "FeatureVictimTest#expectsTurboDisabled"))
        for fields in (f2, none):
            jsonschema.validate(fields["shared_resource"], {"$defs": defs, "$ref": "#/$defs/sharedResource"})
            for key in ("polluter_write_location", "victim_read_location"):
                jsonschema.validate(fields[key], {"$defs": defs, "$ref": "#/$defs/codeLocation"})
        self.assertIsNone(none["shared_resource"])


@needs(os.path.isdir(FIXTURE_DIRS[1]),
       "fixture not compiled: run mvn -B -q -f fixtures/od-fixture/pom.xml test-compile")
@needs(HAS_JAVAP, NO_JAVAP)
class GroundTruthTest(unittest.TestCase):
    """Phase 5: compare edges with Member 3's fixtures/od-fixture/ground_truth.json (read, never edited).

    Every fixture test is tried as polluter against every other test as victim, at the
    default depth. Edges must appear for exactly the ground-truth polluter→victim pairs,
    on the ground-truth resource, and nowhere else (N1, N2 and the noise tests included).
    """

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(REPO_ROOT, "fixtures", "od-fixture", "ground_truth.json")) as f:
            truth = json.load(f)
        cls.cases, noise = truth["cases"], truth["benign_noise_tests"]
        name = lambda t: t["class"] + "#" + t["method"]
        tests = set()
        for case in cls.cases:
            tests.add(name(case["victim"]))
            tests.update(name(p) for p in case["polluters"])
        for group in noise:
            tests.update(group["class"] + "#" + m for m in group["methods"])
        project = extract.Project(FIXTURE_DIRS)
        cls.results = {t: extract.analyse_test(project, t) for t in sorted(tests)}
        cls.name = staticmethod(name)

    def edges(self, polluter, victim):
        return extract.find_edges(polluter, self.results[polluter], victim, self.results[victim])

    def test_edges_appear_for_exactly_the_ground_truth_pairs(self):
        expected = {(self.name(p), self.name(c["victim"])) for c in self.cases for p in c["polluters"]}
        found = {(p, v) for p in self.results for v in self.results
                 if p != v and self.edges(p, v)["edges"]}
        self.assertEqual(found, expected)

    def test_each_edge_is_on_the_ground_truth_resource(self):
        for case in self.cases:
            truth = case["shared_resource"]
            for polluter in case["polluters"]:
                with self.subTest(case=case["id"], polluter=polluter["method"]):
                    pair = self.edges(self.name(polluter), self.name(case["victim"]))
                    got = extract.report_fields(pair)["shared_resource"]
                    if case["polluter_combination"] == "single":
                        self.assertEqual(got, truth)
                    else:
                        # F3: the ground truth names both fields in one free-text value
                        # ("flagA and flagB (both required)"), so match kind and class
                        # exactly and require this polluter's field to be one it names.
                        self.assertEqual((got["kind"], got["class"]), (truth["kind"], truth["class"]))
                        self.assertIn(got["field"], truth["field"].split())

    def test_victims_without_polluters_get_no_edge_from_any_test(self):
        for case in self.cases:
            if case["shared_resource"] is None:
                victim = self.name(case["victim"])
                for polluter in self.results:
                    if polluter != victim:
                        with self.subTest(case=case["id"], polluter=polluter):
                            pair = self.edges(polluter, victim)
                            self.assertEqual(pair["edges"], [])
                            self.assertTrue(pair["no_supported_resource_evidence"])


@needs(os.path.isdir(TEST_CLASSES), NO_SELFTEST)
class CommandLineTest(unittest.TestCase):

    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "evidence.extract", *args],
                              capture_output=True, text=True, cwd=REPO_ROOT)

    def test_prints_contract_json_on_stdout(self):
        need_javap(self)
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

    def test_pair_mode_prints_edges(self):
        need_javap(self)
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--polluter", "m1selftest.M1SelfTest#writesAndReads",
                            "--victim", "m1selftest.M1LifecycleSelfTest#emptyBody")
        self.assertEqual(done.returncode, 0, done.stderr)
        output = json.loads(done.stdout)
        self.assertEqual(len(output["tests"]), 2)
        self.assertEqual([e["resource_id"] for e in output["pair"]["edges"]],
                         ["m1selftest.SelfTestState#counter"])

    def test_pair_mode_needs_both_tests(self):
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--polluter", "m1selftest.M1SelfTest#writesAndReads")
        self.assert_input_error(done, "needs both --polluter and --victim")

    def test_test_and_pair_mode_cannot_be_combined(self):
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1SelfTest#writesAndReads",
                            "--polluter", "a.B#c", "--victim", "a.B#d")
        self.assert_input_error(done, "not both")

    def test_missing_class_directory_is_an_input_error(self):
        done = self.run_cli("--classes", "/no/such/dir", "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1SelfTest#writesAndReads", "--depth", "1")
        self.assert_input_error(done, "class directory not found")

    def test_unknown_test_method_is_an_input_error(self):
        need_javap(self)
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1SelfTest#noSuchMethod", "--depth", "1")
        self.assert_input_error(done, "test method not found")

    def test_default_depth_is_2(self):
        need_javap(self)
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1DepthSelfTest#callsDown")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["analysis"]["depth"], 2)

    def test_unsupported_depth_is_an_input_error(self):
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1SelfTest#writesAndReads", "--depth", "4")
        self.assert_input_error(done, "--depth must be 1, 2 or 3")


if __name__ == "__main__":
    unittest.main()
