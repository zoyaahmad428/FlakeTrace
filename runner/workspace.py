"""Where a diagnosis runs (W22, ADR-012 section 4). With "copy", the project is copied to a
temporary folder, everything is built and run there, and the copy is deleted afterwards -- so the
user's project folder is never written to by FlakeTrace. "in-place" is the Mid behaviour."""

import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

WORKSPACES = ("copy", "in-place")

# The same folders the integrity check leaves out: build output is rebuilt in the copy, and git
# metadata is read from the original project.
_LEFT_OUT = {"target", ".git"}


class WorkspaceError(OSError):
    """The project could not be copied (a locked file, a broken link, a path too long)."""


@contextmanager
def workspace(project: Path, mode: str, parent: Optional[Path] = None) -> Iterator[Path]:
    """Yield the folder to diagnose in: `project` itself, or a fresh copy inside `parent` (default:
    the system temp folder) that is removed on exit, also when the body raises. A copy that cannot
    be removed is named on stderr instead of being left behind silently."""
    if mode not in WORKSPACES:
        raise ValueError(f"workspace must be one of {WORKSPACES}, got {mode!r}")
    if mode == "in-place":
        yield project
        return
    root = Path(project).resolve()
    if parent is not None:
        Path(parent).mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="flaketrace-work-", dir=parent))
    try:
        copy = tmp / root.name
        try:
            shutil.copytree(root, copy, ignore=lambda folder, names: [
                name for name in names if Path(folder).resolve() == root and name in _LEFT_OUT])
        except (OSError, shutil.Error) as error:
            raise WorkspaceError(f"could not copy {project} to a temporary folder ({error}); "
                                 "use --workspace in-place to diagnose it where it is") from error
        yield copy
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if tmp.exists():
            print(f"warning: the temporary copy {tmp} could not be deleted (a file may still be in use); "
                  "delete it by hand", file=sys.stderr)
