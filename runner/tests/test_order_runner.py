import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from eval.baseline import TestIdentifier
from runner.order_runner import (
    OrderRunner,
    maven_test_classpath,
    normalise_message,
    normalise_stack,
    parse_env,
    parse_results,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "od-fixture"
CONTROL = Path(__file__).resolve().parent / "resources" / "lifecycle-control"

POLLUTER = TestIdentifier("odfixture.ConfigPolluterTest", "pollute")
VICTIM = TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode")
JUNIT3_POLLUTER = TestIdentifier("LegacyJUnit3Test", "testPollute")
JUNIT3_VICTIM = TestIdentifier("LegacyJUnit3Test", "testVictim")

JDK21_FRAMES = [
    "org.junit.Assert.fail:89",
    "org.junit.Assert.assertEquals:633",
    "odfixture.ConfigVictimTest.expectsDefaultMode:10",
    "jdk.internal.reflect.DirectMethodHandleAccessor.invoke:103",
    "java.lang.reflect.Method.invoke:580",
    "org.junit.runners.model.FrameworkMethod$1.runReflectiveCall:59",
    "FtHarness.main:24",
]
JDK8_FRAMES = [
    "org.junit.Assert.fail:89",
    "org.junit.Assert.assertEquals:633",
    "odfixture.ConfigVictimTest.expectsDefaultMode:10",
    "sun.reflect.NativeMethodAccessorImpl.invoke0:-2",
    "sun.reflect.NativeMethodAccessorImpl.invoke:62",
    "java.lang.reflect.Method.invoke:498",
    "org.junit.runners.model.FrameworkMethod$1.runReflectiveCall:50",
]


class TestNormalisation(unittest.TestCase):
    def test_stack_is_cut_at_the_first_framework_frame(self):
        self.assertEqual(
            normalise_stack(JDK21_FRAMES),
            "org.junit.Assert.fail:89\norg.junit.Assert.assertEquals:633\n"
            "odfixture.ConfigVictimTest.expectsDefaultMode:10",
        )

    def test_jdk8_and_jdk21_give_the_same_stack(self):
        self.assertEqual(normalise_stack(JDK8_FRAMES), normalise_stack(JDK21_FRAMES))

    def test_message_keeps_first_line_and_masks_numbers(self):
        self.assertEqual(
            normalise_message("expected:<0> but was:<1>\nsecond line"),
            "expected:<<N>> but was:<<N>>",
        )

    def test_message_masks_object_ids(self):
        self.assertEqual(normalise_message("from Request@4c3e4790"), "from Request@<ID>")


class TestParseResults(unittest.TestCase):
    def test_pass_and_fail_lines(self):
        text = (
            "0\todfixture.ConfigPolluterTest#pollute\tPASS\t\t\t\n"
            "1\todfixture.ConfigVictimTest#expectsDefaultMode\tFAIL\tjava.lang.AssertionError\t"
            "expected:<0> but was:<1>\t" + "|".join(JDK21_FRAMES) + "\n"
        )
        results = parse_results(text, [POLLUTER, VICTIM], "flaketrace.JvmCrash", "")
        self.assertTrue(results[POLLUTER].passed)
        signature = results[VICTIM].failure_signature
        self.assertEqual(signature.exception_type, "java.lang.AssertionError")
        self.assertEqual(signature.message, "expected:<<N>> but was:<<N>>")
        self.assertTrue(signature.stack_trace.endswith("odfixture.ConfigVictimTest.expectsDefaultMode:10"))

    def test_escaped_tab_and_newline_in_message_are_restored(self):
        text = "0\tA#a\tFAIL\tjava.lang.Exception\tfirst\\tpart\\nsecond line\tA.a:1\n"
        test = TestIdentifier("A", "a")
        results = parse_results(text, [test], "flaketrace.JvmCrash", "")
        self.assertEqual(results[test].failure_signature.message, "first\tpart")

    def test_test_without_a_result_line_is_reported_with_the_missing_type(self):
        text = "0\todfixture.ConfigPolluterTest#pollute\tPASS\t\t\t\n"
        results = parse_results(text, [POLLUTER, VICTIM], "flaketrace.JvmCrash", "JVM exited with code 1")
        self.assertEqual(set(results), {POLLUTER, VICTIM})
        self.assertFalse(results[VICTIM].passed)
        self.assertEqual(results[VICTIM].failure_signature.exception_type, "flaketrace.JvmCrash")

    def test_truncated_last_line_is_treated_as_missing(self):
        text = "0\todfixture.ConfigPolluterTest#pollute\tPASS\t\t\t\n1\todfixture.Config"
        results = parse_results(text, [POLLUTER, VICTIM], "flaketrace.JvmCrash", "")
        self.assertEqual(results[VICTIM].failure_signature.exception_type, "flaketrace.JvmCrash")

    def test_unterminated_last_line_is_treated_as_missing(self):
        text = "0\tA#a\tFAIL\tjava.lang.Exception\tmsg\tA.a:1|A.b:2|fra"
        test = TestIdentifier("A", "a")
        results = parse_results(text, [test], "flaketrace.Timeout", "")
        self.assertEqual(results[test].failure_signature.exception_type, "flaketrace.Timeout")

    def test_skipped_test_is_a_failure_not_a_pass(self):
        text = "0\todfixture.ConfigVictimTest#expectsDefaultMode\tSKIP\t\t\t\n"
        results = parse_results(text, [VICTIM], "flaketrace.JvmCrash", "")
        self.assertFalse(results[VICTIM].passed)
        self.assertEqual(results[VICTIM].failure_signature.exception_type, "flaketrace.NotExecuted")

    def test_env_lines_become_a_dict_without_parsing_the_values(self):
        text = "java.version\t1.8.0_452\ntimezone\tGMT+05:00\nlocale\ten\nfile.encoding\tCp1252\njunit.version\t4.13.2\n"
        self.assertEqual(parse_env(text), {"java.version": "1.8.0_452", "timezone": "GMT+05:00", "locale": "en",
                                           "file.encoding": "Cp1252", "junit.version": "4.13.2"})

    def test_env_ignores_a_cut_off_last_line(self):
        self.assertEqual(parse_env("locale\ten_US\njunit.ver"), {"locale": "en_US"})


class TestOrderRunnerOnF1(unittest.TestCase):
    """Runs real JVMs on fixtures/od-fixture. Needs java, javac and mvn on PATH."""

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        cls.runner = OrderRunner(maven_test_classpath(FIXTURE))

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

    def test_victim_passes_alone(self):
        self.assertTrue(self.runner.run_ordered([VICTIM])[VICTIM].passed)

    def test_victim_fails_after_polluter_in_one_jvm(self):
        results = self.runner.run_ordered([POLLUTER, VICTIM])
        self.assertTrue(results[POLLUTER].passed)
        self.assertFalse(results[VICTIM].passed)
        signature = results[VICTIM].failure_signature
        self.assertEqual(signature.exception_type, "java.lang.AssertionError")
        self.assertTrue(signature.stack_trace.endswith("odfixture.ConfigVictimTest.expectsDefaultMode:10"))

    def test_order_is_honoured_victim_first_passes(self):
        results = self.runner.run_ordered([VICTIM, POLLUTER])
        self.assertTrue(results[VICTIM].passed)
        self.assertTrue(results[POLLUTER].passed)

    def test_each_call_gets_a_fresh_jvm(self):
        self.runner.run_ordered([POLLUTER, VICTIM])
        self.assertTrue(self.runner.run_ordered([VICTIM])[VICTIM].passed)

    def test_unknown_method_and_class_are_reported_as_failures(self):
        no_method = TestIdentifier("odfixture.ConfigVictimTest", "noSuchMethod")
        no_class = TestIdentifier("odfixture.NoSuchClass", "x")
        results = self.runner.run_ordered([no_method, no_class, VICTIM])
        self.assertEqual(results[no_method].failure_signature.exception_type, "java.lang.Exception")
        self.assertEqual(results[no_class].failure_signature.exception_type, "java.lang.ClassNotFoundException")
        self.assertTrue(results[VICTIM].passed)

    def test_duplicate_test_in_order_is_rejected(self):
        with self.assertRaises(ValueError):
            self.runner.run_ordered([VICTIM, VICTIM])

    def test_empty_order_returns_empty_result(self):
        self.assertEqual(self.runner.run_ordered([]), {})

    def test_timeout_reports_every_test_as_failed(self):
        runner = OrderRunner(self.runner.classpath, timeout_s=0.01)
        results = runner.run_ordered([POLLUTER, VICTIM])
        self.assertEqual(
            {r.failure_signature.exception_type for r in results.values()}, {"flaketrace.Timeout"}
        )


class TestOrderRunnerOnProbes(unittest.TestCase):
    """Real JVM runs of runner/tests/resources/ProbeTest.java, compiled against the fixture's JUnit."""

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        jars = maven_test_classpath(FIXTURE)[2:]
        cls.probe_dir = tempfile.mkdtemp(prefix="flaketrace-probe-")
        subprocess.run(
            [shutil.which("javac"), "-d", cls.probe_dir]
            + [str(Path(__file__).parent / "resources" / name) for name in
               ("ProbeTest.java", "LegacyJUnit3Test.java", "OrderProbeTest.java", "BrokenSetupProbeTest.java",
                "StaticInitProbeTest.java", "AssumeSetupProbeTest.java")],
            env=dict(os.environ, CLASSPATH=os.pathsep.join(jars)),
            check=True,
        )
        cls.classpath = [cls.probe_dir] + jars
        cls.runner = OrderRunner(cls.classpath)
        cls.grouped = OrderRunner(cls.classpath, lifecycle="class-grouped")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.probe_dir, ignore_errors=True)

    def test_message_with_form_feed_is_a_failure_not_a_crash(self):
        probe = TestIdentifier("ProbeTest", "failsWithFormFeed")
        signature = self.runner.run_ordered([probe])[probe].failure_signature
        self.assertEqual(signature.exception_type, "java.lang.AssertionError")

    def test_tests_run_in_the_given_working_directory(self):
        probe = TestIdentifier("ProbeTest", "needsPomInWorkingDir")
        runner = OrderRunner(self.classpath, working_dir=FIXTURE)
        self.assertTrue(runner.run_ordered([probe])[probe].passed)

    def test_jvm_exit_mid_order_reports_the_rest_as_crashed(self):
        exits = TestIdentifier("ProbeTest", "exitsTheJvm")
        results = self.runner.run_ordered([exits, VICTIM])
        self.assertEqual(results[exits].failure_signature.exception_type, "flaketrace.JvmCrash")
        self.assertIn("code 3", results[VICTIM].failure_signature.message)

    def test_ignored_test_is_reported_not_executed(self):
        probe = TestIdentifier("ProbeTest", "ignored")
        signature = self.runner.run_ordered([probe])[probe].failure_signature
        self.assertEqual(signature.exception_type, "flaketrace.NotExecuted")

    def test_junit3_methods_are_listed(self):
        self.assertEqual(self.runner.list_methods(["LegacyJUnit3Test"]),
                         [JUNIT3_POLLUTER, JUNIT3_VICTIM])

    def test_junit3_victim_passes_alone_and_fails_after_its_polluter(self):
        self.assertTrue(self.runner.run_ordered([JUNIT3_VICTIM])[JUNIT3_VICTIM].passed)
        outcome = self.runner.run_ordered([JUNIT3_POLLUTER, JUNIT3_VICTIM])[JUNIT3_VICTIM]
        self.assertFalse(outcome.passed)
        self.assertEqual(outcome.failure_signature.exception_type, "junit.framework.AssertionFailedError")
        self.assertTrue(outcome.failure_signature.stack_trace.endswith("LegacyJUnit3Test.testVictim:12"),
                        outcome.failure_signature.stack_trace)

    # W22 job 3, ADR-012 section 2: class-grouped execution.
    def test_grouped_block_runs_in_the_requested_order(self):
        a, b = TestIdentifier("OrderProbeTest", "a"), TestIdentifier("OrderProbeTest", "b")
        backwards = self.grouped.run_ordered([b, a])
        self.assertFalse(backwards[b].passed)
        self.assertTrue(backwards[a].passed)
        forwards = self.grouped.run_ordered([a, b])
        self.assertTrue(forwards[a].passed and forwards[b].passed)

    def test_grouped_setup_failure_fails_every_test_of_the_block(self):
        tests = [TestIdentifier("BrokenSetupProbeTest", "a"), TestIdentifier("BrokenSetupProbeTest", "b")]
        results = self.grouped.run_ordered(tests)
        for test in tests:
            self.assertEqual(results[test].failure_signature.exception_type, "java.lang.IllegalStateException", test)

    def test_grouped_unknown_method_is_a_real_failure(self):
        nope, a = TestIdentifier("OrderProbeTest", "nope"), TestIdentifier("OrderProbeTest", "a")
        results = self.grouped.run_ordered([nope, a])
        self.assertEqual(results[nope].failure_signature.exception_type, "java.lang.Exception")
        self.assertTrue(results[a].passed)

    def test_grouped_junit3_keeps_the_requested_order(self):
        order = [JUNIT3_VICTIM, JUNIT3_POLLUTER]
        self.assertEqual(self.grouped.run_ordered(order), self.runner.run_ordered(order))
        self.assertTrue(self.grouped.run_ordered(order)[JUNIT3_VICTIM].passed)

    def test_grouped_class_in_two_blocks_runs_both(self):
        a, b = TestIdentifier("OrderProbeTest", "a"), TestIdentifier("OrderProbeTest", "b")
        between = TestIdentifier("ProbeTest", "needsPomInWorkingDir")
        results = OrderRunner(self.classpath, working_dir=FIXTURE, lifecycle="class-grouped").run_ordered([a, between, b])
        self.assertTrue(results[a].passed and results[between].passed and results[b].passed)

    def test_grouped_class_that_cannot_load_fails_every_test(self):
        tests = [TestIdentifier("NoSuchClass", "x"), TestIdentifier("NoSuchClass", "y")]
        results = self.grouped.run_ordered(tests)
        for test in tests:
            self.assertEqual(results[test].failure_signature.exception_type, "java.lang.ClassNotFoundException", test)

    def test_grouped_static_initializer_failure_keeps_its_cause(self):
        tests = [TestIdentifier("StaticInitProbeTest", "a"), TestIdentifier("StaticInitProbeTest", "b")]
        grouped = self.grouped.run_ordered(tests)
        self.assertEqual(grouped[tests[0]].failure_signature.exception_type, "java.lang.ExceptionInInitializerError")
        self.assertEqual(grouped, self.runner.run_ordered(tests))

    def test_grouped_assumption_failing_in_class_setup_is_not_executed(self):
        tests = [TestIdentifier("AssumeSetupProbeTest", "a"), TestIdentifier("AssumeSetupProbeTest", "b")]
        grouped = self.grouped.run_ordered(tests)
        for test in tests:
            self.assertEqual(grouped[test].failure_signature.exception_type, "flaketrace.NotExecuted", test)
        self.assertEqual(grouped, self.runner.run_ordered(tests))

    def test_grouped_crash_mid_block_keeps_finished_results(self):
        a, exits, b = (TestIdentifier("OrderProbeTest", m) for m in ("a", "exits", "b"))
        results = self.grouped.run_ordered([a, exits, b])
        self.assertTrue(results[a].passed)
        self.assertEqual(results[exits].failure_signature.exception_type, "flaketrace.JvmCrash")
        self.assertEqual(results[b].failure_signature.exception_type, "flaketrace.JvmCrash")


class TestLifecycleControl(unittest.TestCase):
    """ADR-012 section 3: the control class under both harness modes (Surefire: CI and M1)."""

    FIRST = TestIdentifier("LifecycleControlTest", "first")
    SECOND = TestIdentifier("LifecycleControlTest", "second")

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        cls.classpath = maven_test_classpath(CONTROL)

    def test_per_method_runs_class_setup_per_test(self):
        results = OrderRunner(self.classpath).run_ordered([self.FIRST, self.SECOND])
        self.assertTrue(results[self.FIRST].passed)
        self.assertEqual(results[self.SECOND].failure_signature.exception_type, "java.lang.AssertionError")
        self.assertEqual(results[self.SECOND].failure_signature.message, "expected:<<N>> but was:<<N>>")

    def test_class_grouped_runs_class_setup_once(self):
        results = OrderRunner(self.classpath, lifecycle="class-grouped").run_ordered([self.FIRST, self.SECOND])
        self.assertTrue(results[self.FIRST].passed)
        self.assertTrue(results[self.SECOND].passed, results[self.SECOND].failure_signature)

    def test_unknown_lifecycle_is_refused(self):
        with self.assertRaises(ValueError):
            OrderRunner(self.classpath, lifecycle="per-class")


if __name__ == "__main__":
    unittest.main()
