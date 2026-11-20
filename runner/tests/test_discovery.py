import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from eval.baseline import TestIdentifier
from runner.discovery import (
    DEFAULT_SELECTION,
    project_selection,
    DiscoveryConfigError,
    SurefireSelection,
    discover_order,
    is_selected,
    surefire_selection,
    test_class_names,
)
from runner.order_runner import OrderRunner, maven_test_classpath

FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "od-fixture"
CUSTOM = Path(__file__).resolve().parent / "resources" / "custom-includes"
BVT = SurefireSelection(includes=("**/bvt/**/*.java",), excludes=())
NS = 'xmlns="http://maven.apache.org/POM/4.0.0"'


def effective_pom(plugin_configuration="", execution_configuration=""):
    """A minimal effective POM, namespaced like Maven's help:effective-pom output."""
    execution = (f"<executions><execution><id>default-test</id><configuration>{execution_configuration}"
                 f"</configuration></execution></executions>") if execution_configuration else ""
    return (f'<project xmlns="http://maven.apache.org/POM/4.0.0"><build><plugins><plugin>'
            f"<artifactId>maven-surefire-plugin</artifactId>{execution}"
            f"<configuration>{plugin_configuration}</configuration></plugin></plugins></build></project>")


class TestClassSelection(unittest.TestCase):
    def test_surefire_default_patterns(self):
        for path in ("TestFoo.class", "a/FooTest.class", "FooTests.class", "FooTestCase.class"):
            self.assertTrue(is_selected(path, DEFAULT_SELECTION), path)
        for path in ("Foo.class", "FooTestHelper.class", "FooTest$Inner.class", "Testing$1.class"):
            self.assertFalse(is_selected(path, DEFAULT_SELECTION), path)

    def test_fastjson_bvt_include(self):
        self.assertTrue(is_selected("com/alibaba/json/bvt/serializer/SerializeWriterTest_14.class", BVT))
        self.assertFalse(is_selected("com/alibaba/json/other/FooTest.class", BVT))

    def test_project_excludes_replace_the_default_inner_class_exclude(self):
        selection = SurefireSelection(includes=("**/bvt/**/*.java",), excludes=("**/bvt/**/Skip*.java",))
        self.assertFalse(is_selected("x/bvt/SkipMe.class", selection))
        self.assertTrue(is_selected("x/bvt/Outer$Inner.class", selection))

    def test_regex_pattern_is_refused(self):
        # Surefire's own %regex input differs between versions and from a plain path (review, A1).
        pom = effective_pom("<includes><include>%regex[.*Plain.*]</include></includes>")
        with self.assertRaises(DiscoveryConfigError):
            surefire_selection(pom)

    def test_pattern_without_leading_double_star_applies_in_any_folder(self):
        self.assertTrue(is_selected("a/b/FooTest.class", SurefireSelection(("*Test.java",), ())))
        excluding = SurefireSelection(DEFAULT_SELECTION.includes, ("*Slow*.java",))
        self.assertFalse(is_selected("pkg/a/SlowThingTest.class", excluding))

    def test_dotted_class_name_pattern(self):
        self.assertTrue(is_selected("pkg/a/Bar.class", SurefireSelection(("pkg.a.Bar",), ())))
        self.assertFalse(is_selected("pkg/a/Baz.class", SurefireSelection(("pkg.a.Bar",), ())))

    def test_plugin_management_is_not_the_build_configuration(self):
        pom = (f'<project {NS}><build><pluginManagement><plugins><plugin>'
               "<artifactId>maven-surefire-plugin</artifactId><version>2.22.2</version>"
               "<configuration><includes><include>**/FromManagement*.java</include></includes></configuration>"
               "</plugin></plugins></pluginManagement><plugins><plugin>"
               "<artifactId>maven-surefire-plugin</artifactId>"
               "<configuration><includes><include>**/bvt/**/*.java</include></includes></configuration>"
               "</plugin></plugins></build></project>")
        self.assertEqual(surefire_selection(pom).includes, ("**/bvt/**/*.java",))
        version_only = (f'<project {NS}><build><pluginManagement><plugins><plugin>'
                        "<artifactId>maven-surefire-plugin</artifactId><version>2.22.2</version>"
                        "</plugin></plugins></pluginManagement><plugins><plugin>"
                        "<artifactId>maven-surefire-plugin</artifactId>"
                        "<configuration><includes><include>**/bvt/**/*.java</include></includes></configuration>"
                        "</plugin></plugins></build></project>")
        self.assertEqual(surefire_selection(version_only).includes, ("**/bvt/**/*.java",))

    def test_reactor_effective_pom_is_refused(self):
        with self.assertRaises(DiscoveryConfigError):
            surefire_selection(f'<projects><project {NS}><build><plugins/></build></project></projects>')

    def test_more_suite_changing_settings_are_refused(self):
        for setting in ("<excludedGroups>slow</excludedGroups>", "<testClassesDirectory>x</testClassesDirectory>",
                        "<dependenciesToScan><dependency>a:b</dependency></dependenciesToScan>",
                        "<skipTests>true</skipTests>", "<skip>true</skip>"):
            with self.assertRaises(DiscoveryConfigError, msg=setting):
                surefire_selection(effective_pom(setting))
        self.assertEqual(surefire_selection(effective_pom("<skipTests>false</skipTests>")), DEFAULT_SELECTION)

    def test_double_star_inside_a_name_stays_in_one_folder(self):
        # Surefire treats ** as "any folders" only as a whole path segment (review minor, A1).
        selection = SurefireSelection(("pkg/**Test.java",), ())
        self.assertTrue(is_selected("pkg/FooTest.class", selection))
        self.assertFalse(is_selected("pkg/a/FooTest.class", selection))

    def test_patterns_that_differ_between_surefire_versions_are_refused(self):
        for pattern in ("**/*Test.*", "/pkg/a/*.java"):
            with self.assertRaises(DiscoveryConfigError, msg=pattern):
                surefire_selection(effective_pom(f"<includes><include>{pattern}</include></includes>"))

    def test_method_filter_is_refused(self):
        with self.assertRaises(DiscoveryConfigError):
            surefire_selection(effective_pom("<includes><include>**/FooTest.java#bar</include></includes>"))

    def test_unresolved_property_is_named(self):
        with self.assertRaises(DiscoveryConfigError) as raised:
            surefire_selection(effective_pom("<includes><include>${test.pattern}</include></includes>"))
        self.assertIn("${test.pattern}", str(raised.exception))

    def test_selection_must_be_given(self):
        # No silent default: a caller that forgets the project's selection fails loudly.
        with self.assertRaises(TypeError):
            test_class_names(Path(tempfile.mkdtemp()))

    def test_an_extra_test_execution_is_refused(self):
        pom = (f'<project {NS}><build><plugins><plugin><artifactId>maven-surefire-plugin</artifactId>'
               "<executions><execution><id>default-test</id><goals><goal>test</goal></goals></execution>"
               "<execution><id>slow-tests</id><goals><goal>test</goal></goals></execution></executions>"
               "</plugin></plugins></build></project>")
        with self.assertRaises(DiscoveryConfigError):
            surefire_selection(pom)

    def test_windows_separators(self):
        self.assertTrue(is_selected("com\\alibaba\\json\\bvt\\A.class", BVT))

    def test_plugin_level_includes(self):
        pom = effective_pom("<includes><include>**/bvt/**/*.java</include></includes>")
        # Excludes not set by the project: Surefire keeps its default exclude of inner classes.
        self.assertEqual(surefire_selection(pom), SurefireSelection(("**/bvt/**/*.java",), ("**/*$*",)))

    def test_default_test_execution_overrides_plugin_level(self):
        pom = effective_pom("<includes><include>**/old/*.java</include></includes>",
                            "<includes><include>**/bvt/**/*.java</include></includes>")
        self.assertEqual(surefire_selection(pom).includes, ("**/bvt/**/*.java",))

    def test_comma_separated_include(self):
        pom = effective_pom("<includes><include>a/**/*.java,b/**/*.java</include></includes>")
        self.assertEqual(surefire_selection(pom).includes, ("a/**/*.java", "b/**/*.java"))

    def test_no_surefire_plugin_gives_the_defaults(self):
        pom = '<project xmlns="http://maven.apache.org/POM/4.0.0"><build><plugins/></build></project>'
        self.assertEqual(surefire_selection(pom), DEFAULT_SELECTION)

    def test_unsupported_setting_is_refused(self):
        with self.assertRaises(DiscoveryConfigError) as raised:
            surefire_selection(effective_pom("<test>FooTest</test>"))
        self.assertIn("test", str(raised.exception))

    def test_class_names_follow_the_selection(self):
        root = Path(tempfile.mkdtemp(prefix="flaketrace-classes-"))
        for rel in ("a/bvt/Plain.class", "a/OtherTest.class"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_bytes(b"")
        self.assertEqual(test_class_names(root, BVT), ["a.bvt.Plain"])

    def test_class_names_are_fully_qualified_and_sorted(self):
        root = Path(tempfile.mkdtemp(prefix="flaketrace-classes-"))
        for rel in ("b/ZTest.class", "a/x/YTest.class", "a/Helper.class", "a/x/YTest$1.class",
                    "a/notes.txt", "TestTop.class"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_bytes(b"")
        self.assertEqual(test_class_names(root, DEFAULT_SELECTION), ["TestTop", "a.x.YTest", "b.ZTest"])

    def test_missing_test_classes_folder_gives_no_classes(self):
        self.assertEqual(test_class_names(Path(tempfile.mkdtemp()) / "target" / "test-classes", DEFAULT_SELECTION), [])


class TestDiscoveryOnFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        runner = OrderRunner(maven_test_classpath(FIXTURE), working_dir=FIXTURE)
        cls.order = discover_order(runner, FIXTURE / "target" / "test-classes", DEFAULT_SELECTION)  # fixture sets none

    def test_every_fixture_test_method_once_in_alphabetical_class_order(self):
        # Expected set read from the fixture's sources (every @Test method), independent of the
        # discovery code under test, so adding a fixture case does not break this.
        expected = set()
        for source in (FIXTURE / "src" / "test" / "java").rglob("*.java"):
            text = source.read_text(encoding="utf-8")
            package = re.search(r"^package\s+([\w.]+);", text, re.M).group(1)
            for method in re.findall(r"@Test\s+public\s+void\s+(\w+)\s*\(", text):
                expected.add(TestIdentifier(f"{package}.{source.stem}", method))
        self.assertGreater(len(expected), 0)
        self.assertEqual(len(self.order), len(set(self.order)))
        self.assertEqual(set(self.order), expected)
        classes = [t.class_name for t in self.order]
        self.assertEqual(classes, sorted(classes))

    def test_class_with_two_methods_lists_both(self):
        math = [t.method for t in self.order if t.class_name == "odfixture.MathUtilTest"]
        self.assertEqual(sorted(math), ["addsTwoNumbers", "squaresANumber"])

    def test_class_without_tests_or_unloadable_is_left_out(self):
        runner = OrderRunner(maven_test_classpath(FIXTURE), working_dir=FIXTURE)
        self.assertEqual(runner.list_methods(["odfixture.Config", "odfixture.NoSuchTest"]), [])


class TestDiscoveryOnCustomIncludes(unittest.TestCase):
    """A1: a project whose Surefire includes replace the default test names (as fastjson's do)."""

    @classmethod
    def setUpClass(cls):
        missing = [tool for tool in ("java", "javac", "mvn") if shutil.which(tool) is None]
        if missing:
            if os.environ.get("FLAKETRACE_REQUIRE_JVM"):
                raise RuntimeError(f"FLAKETRACE_REQUIRE_JVM is set but {missing} not on PATH")
            raise unittest.SkipTest(f"{missing} not on PATH")
        cls.before = sorted(p.relative_to(CUSTOM).as_posix() for p in CUSTOM.rglob("*")
                            if "target" not in p.relative_to(CUSTOM).parts)
        cls.pom = Path(tempfile.mkdtemp(prefix="flaketrace-pom-")) / "effective-pom.xml"
        runner = OrderRunner(maven_test_classpath(CUSTOM, effective_pom=cls.pom), working_dir=CUSTOM)
        cls.order = discover_order(runner, CUSTOM / "target" / "test-classes", project_selection(cls.pom))

    def test_only_the_projects_includes_are_discovered(self):
        # Methods come in JUnit's own order (not alphabetical), so compare the set.
        self.assertEqual(sorted(self.order, key=str), [TestIdentifier("pkg.bvt.PlainCase", "first"),
                                                       TestIdentifier("pkg.bvt.PlainCase", "second")])

    def test_effective_pom_is_written_outside_the_project(self):
        self.assertTrue(self.pom.is_file())
        after = sorted(p.relative_to(CUSTOM).as_posix() for p in CUSTOM.rglob("*")
                       if "target" not in p.relative_to(CUSTOM).parts)
        self.assertEqual(after, self.before)


if __name__ == "__main__":
    unittest.main()
