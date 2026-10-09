import os
import shutil
import unittest
from pathlib import Path

from eval.baseline import TestIdentifier
from runner.order_runner import (
    OrderRunner,
    maven_test_classpath,
    normalise_message,
    normalise_stack,
    parse_results,
)

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "od-fixture"

POLLUTER = TestIdentifier("odfixture.ConfigPolluterTest", "pollute")
VICTIM = TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode")

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

    def test_skipped_test_is_a_failure_not_a_pass(self):
        text = "0\todfixture.ConfigVictimTest#expectsDefaultMode\tSKIP\t\t\t\n"
        results = parse_results(text, [VICTIM], "flaketrace.JvmCrash", "")
        self.assertFalse(results[VICTIM].passed)
        self.assertEqual(results[VICTIM].failure_signature.exception_type, "flaketrace.NotExecuted")


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


if __name__ == "__main__":
    unittest.main()
