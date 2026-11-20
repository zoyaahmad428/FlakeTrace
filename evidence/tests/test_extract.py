"""Tests for evidence/extract.py (Member 1): lifecycle attribution (Phase 2), call depth (Phase 3), pairs (Phase 4),
ground truth (Phase 5), setUp/<clinit> polluter edges and pair-mode input errors (Phase 6), auto-deepening (ADR-006).

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
CONTROLS_TARGET = os.path.join(HERE, "resources", "ft005-controls", "target")
CONTROLS_DIRS = [os.path.join(CONTROLS_TARGET, "classes"), os.path.join(CONTROLS_TARGET, "test-classes")]
NO_CONTROLS = ("FT005 controls not compiled: run mvn -B -q -f "
               "evidence/tests/resources/ft005-controls/pom.xml test-compile")


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

    def test_polluter_write_in_junit3_setup_is_an_edge(self):
        pair = analyse_pair([CLASSES, TEST_CLASSES], "m1selftest.M1Junit3SelfTest#testNothing",
                            "m1selftest.M1SelfTest#writesAndReads")
        self.assertEqual(edge_summary(pair), [
            ("m1selftest.SelfTestState#counter", ["M1Junit3SelfTest.setUp@1"],
             ["M1SelfTest.writesAndReads@4"])])
        self.assertEqual(pair["edges"][0]["polluter_write_locations"][0]["via"], "SETUP")

    def test_polluter_write_in_test_class_clinit_is_an_edge(self):
        pair = analyse_pair([CLASSES, TEST_CLASSES], "m1selftest.M1LifecycleSelfTest#emptyBody",
                            "m1selftest.M1ClinitReaderSelfTest#readsClinitProperty")
        self.assertEqual(edge_summary(pair), [
            ("sysprop:m1.selftest.clinit", ["M1LifecycleSelfTest.<clinit>@4"],
             ["M1ClinitReaderSelfTest.readsClinitProperty@2"])])
        self.assertEqual(pair["edges"][0]["polluter_write_locations"][0]["via"], "CLINIT")


@needs(os.path.isdir(TEST_CLASSES), NO_SELFTEST)
@needs(HAS_JAVAP, NO_JAVAP)
class DeepeningTest(unittest.TestCase):
    """ADR-006: pair mode goes one level deeper only while there is no edge and a walk was cut off.

    M1DepthSelfTest.callsDown reads SelfTestState.counter only in level4 (depth 4); M1SelfTest
    writes it at depth 1. Offsets read by hand from JDK 8 javap (docs/evidence-m1.md).
    """

    def pair(self, polluter, victim, **options):
        return extract.analyse_pair(extract.Project([CLASSES, TEST_CLASSES]),
                                    "m1selftest." + polluter, "m1selftest." + victim, **options)

    def test_deepens_to_the_first_depth_with_an_edge(self):
        pair = self.pair("M1SelfTest#writesAndReads", "M1DepthSelfTest#callsDown")
        self.assertEqual((pair["depth_requested"], pair["depth_used"]), (2, 4))
        self.assertEqual(edge_summary(pair), [
            ("m1selftest.SelfTestState#counter", ["M1SelfTest.writesAndReads@1"],
             ["M1DepthSelfTest.level4@0"])])

    def test_no_deepen_analyses_at_exactly_the_requested_depth(self):
        pair = self.pair("M1SelfTest#writesAndReads", "M1DepthSelfTest#callsDown", deepen=False)
        self.assertEqual((pair["depth_requested"], pair["depth_used"]), (2, 2))
        self.assertEqual(pair["edges"], [])
        self.assertIn("DEPTH_LIMIT", [o["kind"] for o in pair["unsupported_observations"]])

    def test_nothing_cut_off_means_no_deepening(self):
        pair = self.pair("M1Junit3SelfTest#testNothing", "M1UnsupportedSelfTest#tricky")
        self.assertEqual((pair["depth_requested"], pair["depth_used"]), (2, 2))
        self.assertEqual(pair["edges"], [])
        self.assertNotIn("DEPTH_LIMIT", [o["kind"] for o in pair["unsupported_observations"]])

    def test_report_names_evidence_deeper_than_the_default(self):
        fields = extract.report_fields(self.pair("M1SelfTest#writesAndReads", "M1DepthSelfTest#callsDown"))
        self.assertIn("This evidence is 3 calls deep (depth 4, above the default 2); deeper evidence is "
                      "more likely to be code that is reachable but never runs.", fields["limitations"])


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

    def test_ground_truth_pairs_are_found_without_deepening(self):
        project = extract.Project(FIXTURE_DIRS)
        for case in self.cases:
            for polluter in case["polluters"]:
                with self.subTest(case=case["id"], polluter=polluter["method"]):
                    pair = extract.analyse_pair(project, self.name(polluter), self.name(case["victim"]))
                    self.assertEqual(pair["depth_used"], 2)
                    self.assertNotIn("calls deep", " ".join(extract.report_fields(pair)["limitations"]))


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

    def test_unknown_victim_in_pair_mode_is_an_input_error(self):
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--polluter", "m1selftest.M1SelfTest#writesAndReads",
                            "--victim", "m1selftest.NoSuchTest#nothing")
        self.assert_input_error(done, "test class not found")

    def test_default_depth_is_2(self):
        need_javap(self)
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1DepthSelfTest#callsDown")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["analysis"]["depth"], 2)

    def test_unsupported_depth_is_an_input_error(self):
        done = self.run_cli("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                            "--test", "m1selftest.M1SelfTest#writesAndReads", "--depth", "6")
        self.assert_input_error(done, "--depth must be between 1 and 5")

    def test_pair_mode_deepens_and_no_deepen_stops_it(self):
        args = ("--classes", CLASSES, "--test-classes", TEST_CLASSES,
                "--polluter", "m1selftest.M1SelfTest#writesAndReads",
                "--victim", "m1selftest.M1DepthSelfTest#callsDown")
        deep = json.loads(self.run_cli(*args).stdout)["pair"]
        self.assertEqual((deep["depth_requested"], deep["depth_used"]), (2, 4))
        self.assertEqual([e["resource_id"] for e in deep["edges"]], ["m1selftest.SelfTestState#counter"])
        flat = json.loads(self.run_cli(*args, "--no-deepen").stdout)["pair"]
        self.assertEqual((flat["depth_requested"], flat["depth_used"]), (2, 2))
        self.assertEqual(flat["edges"], [])



def fake_access(resource_id, resource, access, cls, method, offset, depth):
    """One access in analyse_test's shape, for tests of report_fields that need no JVM."""
    return {"resource_id": resource_id, "resource": resource, "access": access,
            "class": cls, "method": method, "bytecode_offset": offset, "depth": depth}


class ResourceEdgesTest(unittest.TestCase):
    """W21 / ADR-010: report_fields lists every edge, not only the first (FT005).

    Pure function test: the pair is built by hand, so no javap or compiled classes are needed.
    """

    A = {"kind": "static-field", "class": "p.State", "field": "a"}
    B = {"kind": "static-field", "class": "p.State", "field": "b"}

    def two_edge_pair(self):
        def edge(resource_id, resource, read_depth):
            return {"resource_id": resource_id, "resource": resource,
                    "polluter_write_locations": [
                        fake_access(resource_id, resource, "WRITE", "p.PolluterTest", "pollute", 3, 1),
                        fake_access(resource_id, resource, "WRITE", "p.PolluterTest", "pollute", 9, 1)],
                    "victim_read_locations": [
                        fake_access(resource_id, resource, "READ", "p.VictimTest", "check", 4, read_depth)]}
        # Already in the contract's order: combined depth, then resource_id.
        return {"edges": [edge("p.State#a", self.A, 1), edge("p.State#b", self.B, 3)],
                "limitations": list(extract.FIXED_LIMITATIONS)}

    def test_every_edge_is_listed_in_contract_order_with_its_depth(self):
        fields = extract.report_fields(self.two_edge_pair())
        self.assertEqual(fields["resource_edges"], [
            {"shared_resource": self.A,
             "polluter_write_location": {"class": "p.PolluterTest", "method": "pollute", "bytecode_offset": 3},
             "victim_read_location": {"class": "p.VictimTest", "method": "check", "bytecode_offset": 4},
             "depth": 1},
            {"shared_resource": self.B,
             "polluter_write_location": {"class": "p.PolluterTest", "method": "pollute", "bytecode_offset": 3},
             "victim_read_location": {"class": "p.VictimTest", "method": "check", "bytecode_offset": 4},
             "depth": 3}])

    def test_shared_resource_is_still_the_first_edge(self):
        fields = extract.report_fields(self.two_edge_pair())
        self.assertEqual(fields["shared_resource"], fields["resource_edges"][0]["shared_resource"])
        self.assertEqual(fields["polluter_write_location"],
                         fields["resource_edges"][0]["polluter_write_location"])

    def test_a_second_edge_is_named_as_listed_not_as_hidden(self):
        # A2 (M2's W21 verification, 2026-11-20): since schema v2 every edge is in resource_edges,
        # so a limitation must not say the second resource is "not shown in this report".
        fields = extract.report_fields(self.two_edge_pair())
        self.assertIn("Shared resource p.State#b is not the headline resource; it is listed in resource_edges",
                      fields["limitations"])
        self.assertFalse([line for line in fields["limitations"] if "p.State#b" in line
                          and "not shown in this report" in line])

    def test_no_edge_gives_an_empty_list(self):
        fields = extract.report_fields({"edges": [], "limitations": list(extract.FIXED_LIMITATIONS)})
        self.assertEqual(fields["resource_edges"], [])
        self.assertIsNone(fields["shared_resource"])



@needs(os.path.isdir(CONTROLS_DIRS[1]), NO_CONTROLS)
@needs(HAS_JAVAP, NO_JAVAP)
class Ft005ControlsTest(unittest.TestCase):
    """W21 / FT005: two controls where the static edge is not why the victim fails.

    Expected results were written in resources/ft005-controls/EXPECTED.md before the first run.
    """

    def pair(self, polluter, victim):
        return analyse_pair(CONTROLS_DIRS, "controls." + polluter, "controls." + victim)

    def test_write_then_restore_gives_an_edge_on_the_restored_field_only(self):
        pair = self.pair("RestoringPolluterTest#pollute", "RestoringVictimTest#check")
        self.assertEqual([e["resource_id"] for e in pair["edges"]], ["controls.State#restored"])
        self.assertIn(("polluter", "REFLECTION"),
                      [(o["side"], o["kind"]) for o in pair["unsupported_observations"]])

    def test_write_then_restore_is_reported_as_overlap_only(self):
        fields = extract.report_fields(self.pair("RestoringPolluterTest#pollute", "RestoringVictimTest#check"))
        self.assertEqual(fields["shared_resource"],
                         {"kind": "static-field", "class": "controls.State", "field": "restored"})
        self.assertIn("Written values are not modelled: a polluter that writes and then restores the "
                      "original value still produces a WRITE.", fields["limitations"])

    def test_unrelated_overlap_lists_both_edges_and_shows_the_first_by_name(self):
        fields = extract.report_fields(self.pair("TwoFieldPolluterTest#pollute", "TwoFieldVictimTest#check"))
        self.assertEqual([e["shared_resource"]["field"] for e in fields["resource_edges"]], ["a", "b"])
        self.assertEqual(fields["shared_resource"],
                         {"kind": "static-field", "class": "controls.State", "field": "a"})
        self.assertIn("Shared resource controls.State#b is not the headline resource; it is listed in "
                      "resource_edges", fields["limitations"])


if __name__ == "__main__":
    unittest.main()


SCHEMA_PATH = os.path.join(REPO_ROOT, "eval", "schema", "report.schema.json")
try:
    import jsonschema
    from referencing import Registry, Resource
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
NO_JSONSCHEMA = "jsonschema not installed: pip install -r eval/requirements.txt"


@needs(HAS_JSONSCHEMA, NO_JSONSCHEMA)
@needs(os.path.isdir(FIXTURE_DIRS[1]),
       "fixture not compiled: run mvn -B -q -f fixtures/od-fixture/pom.xml test-compile")
@needs(os.path.isdir(CONTROLS_DIRS[1]), NO_CONTROLS)
@needs(os.path.isdir(TEST_CLASSES), NO_SELFTEST)
@needs(HAS_JAVAP, NO_JAVAP)
class ReportSchemaContractTest(unittest.TestCase):
    """Every field report_fields returns is valid under the report schema (PR #106, schema v2).

    This is the M1 -> M3 boundary: Member 3's eval/report.py copies these fields into the
    report, so a field the schema rejects would break every report. The schema is read, never
    edited, here (docs/contracts/report-schema.md).
    """

    PAIRS = [  # (class dirs, polluter, victim, edges expected)
        (FIXTURE_DIRS, "odfixture.ConfigPolluterTest#pollute", "odfixture.ConfigVictimTest#expectsDefaultMode", 1),
        (FIXTURE_DIRS, "odfixture.FeaturePolluterTest#enableTurbo", "odfixture.FeatureVictimTest#expectsTurboDisabled", 1),
        (FIXTURE_DIRS, "odfixture.ToggleAPolluterTest#setFlagA", "odfixture.ToggleVictimTest#expectsNotBothFlagsSet", 1),
        (FIXTURE_DIRS, "odfixture.ZzzLatePolluterTest#setLateFlag", "odfixture.AlwaysEarlyVictimTest#expectsLateFlagUnset", 1),
        (CONTROLS_DIRS, "controls.RestoringPolluterTest#pollute", "controls.RestoringVictimTest#check", 1),
        (CONTROLS_DIRS, "controls.TwoFieldPolluterTest#pollute", "controls.TwoFieldVictimTest#check", 2),
        ([CLASSES, TEST_CLASSES], "m1selftest.M1SelfTest#writesAndReads", "m1selftest.M1LifecycleSelfTest#emptyBody", 1),
        # No edge: shared_resource and both locations are null, which the schema must also accept.
        ([CLASSES, TEST_CLASSES], "m1selftest.M1Junit3SelfTest#testNothing", "m1selftest.M1UnsupportedSelfTest#tricky", 0),
    ]

    @classmethod
    def setUpClass(cls):
        with open(SCHEMA_PATH) as f:
            cls.schema = json.load(f)
        cls.registry = Registry().with_resource("urn:report", Resource.from_contents(cls.schema))

    def errors(self, key, value):
        validator = jsonschema.Draft202012Validator({"$ref": "urn:report#/properties/" + key},
                                                    registry=self.registry)
        return [e.message for e in validator.iter_errors(value)]

    def test_every_field_is_a_schema_property_and_valid(self):
        for dirs, polluter, victim, expected_edges in self.PAIRS:
            with self.subTest(polluter=polluter, victim=victim):
                fields = extract.report_fields(analyse_pair(dirs, polluter, victim))
                self.assertEqual(len(fields["resource_edges"]), expected_edges)
                for key, value in fields.items():
                    self.assertIn(key, self.schema["properties"], "report_fields returns a field "
                                  "the schema does not have: " + key)
                    self.assertEqual(self.errors(key, value), [], key)


def fake_analysis(test_id, accesses):
    """analyse_test's shape for one test, built by hand (no JVM)."""
    test_class, test_method = test_id.split("#", 1)
    return {"test": {"class": test_class, "method": test_method}, "accesses": accesses,
            "unsupported_observations": [], "external_calls_not_followed": []}


class RankCandidatesTest(unittest.TestCase):
    """W25 / ADR-014 section 5: the ranking rule, on hand-built analyses (no JVM).

    The rule: a candidate that WRITES more resources the victim READS comes first; ties go to the
    shallower edge; then to the original position. A candidate with no edge is kept, never dropped.
    These tests use no fixture and no real case: the rule is fixed before it meets ground truth
    (iteration-2-plan rule 4).
    """

    VICTIM = "p.VictimTest#check"

    def resource(self, name):
        return {"kind": "static-field", "class": "p.State", "field": name}

    def writer(self, test_id, writes):
        """A candidate that writes each (field, depth) in `writes`."""
        cls, method = test_id.split("#")
        return fake_analysis(test_id, [fake_access("p.State#" + f, self.resource(f), "WRITE", cls, method, i, d)
                                       for i, (f, d) in enumerate(writes)])

    def cache_with(self, candidates, victim_reads):
        """An AnalysisCache already holding the victim and every candidate, so nothing runs javap."""
        cache = extract.AnalysisCache()
        cache.put(self.VICTIM, extract.DEFAULT_DEPTH, fake_analysis(self.VICTIM, [
            fake_access("p.State#" + f, self.resource(f), "READ", "p.VictimTest", "check", i, d)
            for i, (f, d) in enumerate(victim_reads)]))
        for test_id, writes in candidates:
            cache.put(test_id, extract.DEFAULT_DEPTH, self.writer(test_id, writes))
        return cache

    def rank(self, candidates, victim_reads):
        cache = self.cache_with(candidates, victim_reads)
        return extract.rank_candidates(None, self.VICTIM, [t for t, _ in candidates], cache=cache)

    def test_the_only_candidate_with_an_edge_goes_first_the_rest_keep_their_order(self):
        # ADR-014's scripted case: the polluter is candidate 9 of 10 and the only one with an edge.
        candidates = [("p.T%d#t" % i, [("other%d" % i, 1)]) for i in range(1, 11)]
        candidates[8] = ("p.T9#t", [("x", 1)])
        ranked = self.rank(candidates, [("x", 1)])
        self.assertEqual([r.test for r in ranked],
                         ["p.T9#t"] + ["p.T%d#t" % i for i in (1, 2, 3, 4, 5, 6, 7, 8, 10)])
        self.assertEqual(ranked[0].score, (1, 1, 8))
        self.assertEqual([e["shared_resource"]["field"] for e in ranked[0].reasons], ["x"])

    def test_no_evidence_at_all_gives_exactly_the_original_order(self):
        candidates = [("p.T%d#t" % i, [("unread%d" % i, 1)]) for i in range(1, 6)]
        ranked = self.rank(candidates, [("x", 1)])
        self.assertEqual([r.test for r in ranked], [t for t, _ in candidates])
        self.assertTrue(all(r.reasons == [] and r.score[0] == 0 and r.score[1] is None for r in ranked))

    def test_more_shared_resources_first_then_shallower_then_earlier(self):
        candidates = [("p.Late#one", [("x", 1)]),           # 1 resource, depth 1, position 0
                      ("p.Deep#one", [("x", 2)]),           # 1 resource, depth 2
                      ("p.Two#both", [("x", 2), ("y", 2)]),  # 2 resources: strongest
                      ("p.Tie#one", [("y", 1)])]            # 1 resource, depth 1, position 3
        ranked = self.rank(candidates, [("x", 1), ("y", 1)])
        self.assertEqual([r.test for r in ranked], ["p.Two#both", "p.Late#one", "p.Tie#one", "p.Deep#one"])
        self.assertEqual([r.score for r in ranked], [(2, 2, 2), (1, 1, 0), (1, 1, 3), (1, 2, 1)])

    def test_edge_depth_is_the_deeper_side_of_the_edge(self):
        # Same definition as resource_edges' depth: write at depth 1, read at depth 2 -> depth 2.
        ranked = self.rank([("p.A#a", [("x", 1)])], [("x", 2)])
        self.assertEqual(ranked[0].score, (1, 2, 0))
        self.assertEqual(ranked[0].reasons[0]["depth"], 2)

    def test_ranking_changes_the_order_never_the_candidate_set(self):
        candidates = [("p.T%d#t" % i, [("x", 1)] if i % 3 == 0 else []) for i in range(1, 10)]
        ranked = self.rank(candidates, [("x", 1)])
        self.assertEqual(sorted(r.test for r in ranked), sorted(t for t, _ in candidates))
        self.assertEqual(len(ranked), len(candidates))

    def test_reasons_are_report_shaped_static_overlaps(self):
        ranked = self.rank([("p.A#a", [("x", 1)])], [("x", 1)])
        self.assertEqual(ranked[0].reasons, [{
            "shared_resource": self.resource("x"),
            "polluter_write_location": {"class": "p.A", "method": "a", "bytecode_offset": 0},
            "victim_read_location": {"class": "p.VictimTest", "method": "check", "bytecode_offset": 0},
            "depth": 1}])


@needs(os.path.isdir(CONTROLS_DIRS[1]), NO_CONTROLS)
@needs(HAS_JAVAP, NO_JAVAP)
class RankCandidatesControlsTest(unittest.TestCase):
    """rank_candidates on M1's own FT005 control classes (not a fixture, no ground truth)."""

    VICTIM = "controls.RestoringVictimTest#check"
    CANDIDATES = ["controls.TwoFieldPolluterTest#pollute", "controls.TwoFieldVictimTest#check",
                  "controls.RestoringPolluterTest#pollute"]

    def test_the_candidate_with_a_static_overlap_goes_first(self):
        ranked = extract.rank_candidates(extract.Project(CONTROLS_DIRS), self.VICTIM, self.CANDIDATES)
        self.assertEqual([r.test for r in ranked], ["controls.RestoringPolluterTest#pollute",
                                                    "controls.TwoFieldPolluterTest#pollute",
                                                    "controls.TwoFieldVictimTest#check"])
        self.assertEqual(ranked[0].score, (1, 1, 2))
        self.assertEqual([e["shared_resource"]["field"] for e in ranked[0].reasons], ["restored"])
        # A static overlap ranks first even though this polluter restores the value: ranking orders
        # the search, it never says what caused the failure (ledger G3).

    def test_each_test_is_analysed_once_n_plus_one(self):
        cache = extract.AnalysisCache()
        project = extract.Project(CONTROLS_DIRS)
        extract.rank_candidates(project, self.VICTIM, self.CANDIDATES, cache=cache)
        self.assertEqual(cache.analysed, len(self.CANDIDATES) + 1)
        self.assertGreater(cache.seconds, 0.0)
        extract.rank_candidates(project, self.VICTIM, self.CANDIDATES, cache=cache)
        self.assertEqual(cache.analysed, len(self.CANDIDATES) + 1)   # second ranking: all cached

    def test_a_candidate_that_cannot_be_analysed_is_kept_with_a_note(self):
        ranked = extract.rank_candidates(extract.Project(CONTROLS_DIRS), self.VICTIM,
                                         ["controls.NoSuchTest#x", "controls.RestoringPolluterTest#pollute"])
        self.assertEqual([r.test for r in ranked], ["controls.RestoringPolluterTest#pollute",
                                                    "controls.NoSuchTest#x"])
        self.assertEqual(ranked[1].reasons, [])
        self.assertIn("class not found", ranked[1].note)
        self.assertIsNone(ranked[0].note)

    def test_a_victim_that_cannot_be_analysed_is_an_error(self):
        with self.assertRaises(extract.ExtractError):
            extract.rank_candidates(extract.Project(CONTROLS_DIRS), "controls.NoSuchTest#x", self.CANDIDATES)
