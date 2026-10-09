"""Source-integrity check (W7, ADR-004): hash the analysed project's files before and after a
diagnosis. Build output (target/) and git metadata (.git/) are left out."""

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

EXCLUDED_DIRS = {"target", ".git"}


@dataclass(frozen=True)
class SourceIntegrity:
    passed: bool
    details: str


def snapshot(project_dir) -> Dict[str, str]:
    """SHA-256 of every file under project_dir except target/ and .git/, keyed by relative path."""
    root = Path(project_dir)
    hashes = {}
    for folder, subfolders, files in os.walk(root):
        if Path(folder) == root:
            subfolders[:] = [d for d in subfolders if d not in EXCLUDED_DIRS]
        for name in files:
            path = Path(folder) / name
            hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def compare(before: Dict[str, str], after: Dict[str, str]) -> SourceIntegrity:
    changed = sorted(p for p in before.keys() & after.keys() if before[p] != after[p])
    added = sorted(after.keys() - before.keys())
    removed = sorted(before.keys() - after.keys())
    if not (changed or added or removed):
        return SourceIntegrity(True, f"{len(before)} files hashed (SHA-256) before and after; all identical")
    parts = [f"{label}: {', '.join(paths)}" for label, paths in
             (("changed", changed), ("added", added), ("removed", removed)) if paths]
    return SourceIntegrity(False, "; ".join(parts))
