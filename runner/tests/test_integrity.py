import tempfile
import unittest
from pathlib import Path

from runner.integrity import compare, snapshot


class TestIntegrity(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="flaketrace-integrity-"))
        (self.root / "src" / "main").mkdir(parents=True)
        (self.root / "src" / "main" / "A.java").write_text("class A {}")
        (self.root / "pom.xml").write_text("<project/>")

    def test_unchanged_project_passes(self):
        before = snapshot(self.root)
        result = compare(before, snapshot(self.root))
        self.assertTrue(result.passed)
        self.assertIn("2 files", result.details)

    def test_changed_added_and_removed_files_are_named(self):
        before = snapshot(self.root)
        (self.root / "src" / "main" / "A.java").write_text("class A { int x; }")
        (self.root / "src" / "main" / "B.java").write_text("class B {}")
        (self.root / "pom.xml").unlink()
        result = compare(before, snapshot(self.root))
        self.assertFalse(result.passed)
        self.assertEqual(
            result.details, "changed: src/main/A.java; added: src/main/B.java; removed: pom.xml"
        )

    def test_target_and_git_are_ignored(self):
        before = snapshot(self.root)
        for folder in ("target/classes", ".git"):
            (self.root / folder).mkdir(parents=True)
            (self.root / folder / "x").write_text("build output")
        self.assertTrue(compare(before, snapshot(self.root)).passed)

    def test_nested_folder_named_target_is_still_hashed(self):
        (self.root / "src" / "target").mkdir()
        (self.root / "src" / "target" / "C.java").write_text("class C {}")
        self.assertIn("src/target/C.java", snapshot(self.root))


if __name__ == "__main__":
    unittest.main()
