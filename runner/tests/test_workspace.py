import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

from runner.workspace import WORKSPACES, WorkspaceError, workspace


def make_project() -> Path:
    project = Path(tempfile.mkdtemp(prefix="flaketrace-ws-test-")) / "my project"
    for relative, text in (("pom.xml", "<project/>"), ("src/A.java", "class A {}"), ("target/x.class", "x"),
                           (".git/HEAD", "ref"), ("sub/target/keep.txt", "keep")):
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return project


class TestWorkspace(unittest.TestCase):
    def test_modes(self):
        self.assertEqual(WORKSPACES, ("copy", "in-place"))

    def test_copy_leaves_out_top_level_target_and_git(self):
        project = make_project()
        with workspace(project, "copy") as work:
            self.assertNotEqual(work.resolve(), project.resolve())
            self.assertEqual(work.name, "my project")
            self.assertEqual((work / "src" / "A.java").read_text(encoding="utf-8"), "class A {}")
            self.assertTrue((work / "pom.xml").is_file())
            self.assertTrue((work / "sub" / "target" / "keep.txt").is_file())
            self.assertFalse((work / "target").exists())
            self.assertFalse((work / ".git").exists())

    def test_copy_is_deleted_afterwards(self):
        with workspace(make_project(), "copy") as work:
            pass
        self.assertFalse(work.exists())
        self.assertFalse(work.parent.exists())

    def test_copy_is_deleted_when_the_body_raises(self):
        with self.assertRaises(RuntimeError):
            with workspace(make_project(), "copy") as work:
                raise RuntimeError("boom")
        self.assertFalse(work.parent.exists())

    def test_in_place_is_the_project_itself_and_deletes_nothing(self):
        project = make_project()
        with workspace(project, "in-place") as work:
            self.assertEqual(work, project)
        self.assertTrue((project / "target" / "x.class").is_file())

    def test_unknown_mode_is_refused(self):
        with self.assertRaises(ValueError):
            with workspace(make_project(), "elsewhere"):
                pass


class TestWorkspaceFailures(unittest.TestCase):
    """Fixes from the W22 job 4 review."""

    def test_copy_is_made_inside_a_given_parent(self):
        parent = Path(tempfile.mkdtemp(prefix="flaketrace-ws-parent-")) / "work"
        with workspace(make_project(), "copy", parent=parent) as work:
            self.assertIn(parent.resolve(), work.resolve().parents)
        self.assertEqual(list(parent.iterdir()), [])

    def test_a_copy_that_cannot_be_deleted_is_named_on_stderr(self):
        err = io.StringIO()
        real_rmtree = shutil.rmtree
        with redirect_stderr(err), mock.patch("runner.workspace.shutil.rmtree"):
            with workspace(make_project(), "copy") as work:
                pass
        self.addCleanup(real_rmtree, work.parent, ignore_errors=True)  # the faked failure really left it
        self.assertIn("could not be deleted", err.getvalue())
        self.assertIn(str(work.parent), err.getvalue())

    def test_a_copy_that_cannot_be_made_is_a_workspace_error(self):
        project = make_project()
        with mock.patch("runner.workspace.shutil.copytree", side_effect=OSError("file is locked")):
            with self.assertRaises(WorkspaceError) as raised:
                with workspace(project, "copy"):
                    pass
        self.assertIn(str(project), str(raised.exception))
        self.assertIn("--workspace in-place", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
