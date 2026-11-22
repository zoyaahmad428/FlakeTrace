"""Evidence bundle (W23, ADR-013, Interface 8): one diagnosis as five files that travel — the report,
its record, the environment and the commands to check it — with personal paths removed."""

import collections
import getpass
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Dict, Optional

FILES = ("report.json", "record.jsonl", "replay.md", "environment.txt")
# ADR-012 section 1, "Supported execution contract", the two reset rows, verbatim.
RESET_ASSUMPTIONS = ("Reset between orders: JVM state only: static fields, system properties, loaded classes, threads. "
                     "Not reset: Files anywhere, the working directory, environment variables, network and external "
                     "services, the system clock and timezone.")

Bundle = collections.namedtuple("Bundle", "manifest report header")


class BundleError(Exception):
    """A bundle that cannot be written or read safely (Interface 8)."""


def _forms(path: str):
    """A path as it can appear in a file: as written, with / and with \\, and JSON-escaped."""
    plain = {path, path.replace("\\", "/"), path.replace("/", "\\")}
    return sorted(plain | {form.replace("\\", "\\\\") for form in plain}, key=len, reverse=True)


MIN_USER = 3  # a one- or two-letter user name is not matched: as a path part it would also hit "\\n" escapes


def _user_component(user: str):
    return re.compile(r"(?<=[\\/])" + re.escape(user) + r"(?=[\\/])", re.IGNORECASE)


def _path(form: str):
    """A path form, in any case (Windows paths are case-insensitive), ending at a path boundary, so the home
    C:\\Users\\al never matches inside C:\\Users\\alice."""
    return re.compile(re.escape(form) + r"(?![A-Za-z0-9_.-])", re.IGNORECASE)


def redact(text: str, paths: Dict[str, str], home: str, user: str) -> str:
    """Interface 8: each absolute path in `paths` becomes its placeholder, longest first, then the home
    folder `<home>`, then the user name — only as a path component — `<user>`."""
    for path, placeholder in sorted(paths.items(), key=lambda item: len(item[0]), reverse=True):
        for form in _forms(path):
            text = _path(form).sub(lambda _: placeholder, text)
    for form in _forms(home):
        text = _path(form).sub(lambda _: "<home>", text)
    return _user_component(user).sub("<user>", text) if user and len(user) >= MIN_USER else text


def assert_clean(text: str, home: str, user: str) -> None:
    """The check on the final bytes: no home path, and no user name as a path component, in any case."""
    if any(_path(form).search(text) for form in _forms(home)) or (
            user and len(user) >= MIN_USER and _user_component(user).search(text)):
        raise BundleError("the bundle would still contain the home folder or the user name; nothing was written")


def clean_url(url: Optional[str]) -> Optional[str]:
    """A repository URL without any user[:password]@ part, so no token reaches a committed bundle."""
    if not url:
        return None
    url = url.strip()
    if re.match(r"^[a-z][a-z0-9+.-]*://", url, re.IGNORECASE):
        return re.sub(r"^([a-z][a-z0-9+.-]*://)[^/]*@", r"\1", url, flags=re.IGNORECASE)
    return re.sub(r"^[^/@:]+@", "", url)  # scp form, git@github.com:a/b.git


def _version(text: Optional[str]) -> Optional[str]:
    """The version number in a tool's banner ("Apache Maven 3.10.0 (…)" -> "3.10.0"); the text itself if none."""
    found = re.search(r"\d+(?:\.\d+)+", text) if text else None
    return found.group(0) if found else text


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest(header: dict, *, kind: str, repository: Optional[str], module_path: Optional[str],
             replay_of: Optional[str], files: Dict[str, str]) -> dict:
    """Interface 8's manifest, every key present, from the record header (W22 fields)."""
    jvm = header.get("jvm") or {}
    budget = header.get("budget") or {}
    return {
        "bundle_version": 1,
        "kind": kind,
        "tool": {"commit": header.get("tool_commit"), "dirty": header.get("tool_dirty")},
        "subject": {"repository": repository, "commit": header.get("project_commit"),
                    "dirty": header.get("project_dirty"), "module_path": module_path},
        "victim": header.get("victim"),
        "command": header.get("command"),
        "parameters": {"n": header.get("n"), "shuffles": header.get("shuffles"), "seed": header.get("seed_base"),
                       "budget": {"limit_invocations": budget.get("limit_invocations"),
                                  "limit_seconds": budget.get("limit_seconds")},
                       "policy": header.get("policy"), "scope": header.get("scope"),
                       "lifecycle": header.get("lifecycle"), "workspace": header.get("workspace")},
        "environment": {"os": header.get("os"), "jdk": jvm.get("java.version"), "maven": _version(header.get("maven_version")),
                        "junit": jvm.get("junit.version"), "python": header.get("python_version"),
                        "timezone": jvm.get("timezone"), "locale": jvm.get("locale"),
                        "encoding": jvm.get("file.encoding"), "container_image": header.get("container_image")},
        "reset_assumptions": RESET_ASSUMPTIONS,
        "fresh_run": True,
        "run_date": (header.get("started") or "")[:10] or None,
        "replay_of": replay_of,
        "files": files,
    }


def _replay_md(header: dict, folder_name: str, out_folder, repository: Optional[str],
               module_path: Optional[str]) -> str:
    """Commands that run as written from the FlakeTrace folder, in cmd or a shell (M1's W23 reproduction, #159):
    the bundle's real path, quoted (every name has a #), and --project from the subject; no < or > in a command.
    An absolute output folder is not written (it would be a personal path): shared bundles live in eval/bundles."""
    parent = Path(out_folder)
    bundle = f"{(Path('eval/bundles') if parent.is_absolute() else parent).as_posix()}/{folder_name}"
    commit = header.get("project_commit")
    if repository == "fixture":
        project = module_path or "."
        subject = f"The subject is FlakeTrace's own {module_path or 'repository'}"
    else:
        project = f'"CHECKOUT/{module_path}"' if module_path else '"CHECKOUT"'
        subject = f"CHECKOUT is your clone of {clean_url(repository) if repository else 'the subject'} at commit {commit}"
    return (f"# Check and re-run this bundle\n\n"
            f"Made with FlakeTrace commit: {header.get('tool_commit')}\n"
            f"Subject commit: {commit}\n\n"
            "1. Use any FlakeTrace commit that has eval/bundle.py (for example the current main); `replay` prints\n"
            f"   any difference from the commit above. {subject}.\n"
            "   Run them from the FlakeTrace folder (on Windows, `py` instead of `python`).\n"
            f"2. Recount the evidence from the record alone:\n\n"
            f'       python -m eval.bundle verify "{bundle}"\n\n'
            f"3. Re-run the kept sequence, the victim alone and the deletion checks:\n\n"
            f'       python -m runner replay "{bundle}" --project {project}\n')


def write_bundle(out_folder, report: dict, record_path, *, paths: Dict[str, str], home: Optional[str] = None,
                 user: Optional[str] = None, environment_text: str = "", repository: Optional[str] = None,
                 module_path: Optional[str] = None, kind: str = "diagnosis", replay_of: Optional[str] = None,
                 extra_md: str = "") -> Path:
    """Writes Interface 8's five files into <out_folder>/<record name>/ and returns that folder."""
    home = home if home is not None else str(Path.home())
    user = user if user is not None else getpass.getuser()
    record_path = Path(record_path)
    folder = Path(out_folder) / record_path.stem
    if folder.exists():
        raise BundleError(f"bundle folder {folder.name} already exists; evidence is never overwritten")
    lines = record_path.read_text(encoding="utf-8").splitlines()
    header = json.loads(lines[0])
    texts = {
        "report.json": json.dumps(dict(report, execution_record_reference="record.jsonl"), indent=2) + "\n",
        "record.jsonl": "".join(line + "\n" for line in lines),
        "replay.md": _replay_md(header, folder.name, out_folder, repository, module_path) + extra_md,
        "environment.txt": environment_text.replace("\r\n", "\n"),
    }
    texts = {name: redact(text, paths, home, user) for name, text in texts.items()}
    redacted_header = json.loads(texts["record.jsonl"].splitlines()[0])
    files = {name: _sha256(texts[name].encode("utf-8")) for name in FILES}
    repository = redact(clean_url(repository), paths, home, user) if repository else repository
    texts["manifest.json"] = json.dumps(manifest(redacted_header, kind=kind, repository=repository,
                                                 module_path=module_path, replay_of=replay_of, files=files),
                                        indent=2) + "\n"
    for text in texts.values():
        assert_clean(text, home, user)
    # Written into a side folder and renamed at the end, so a failed write never leaves half a bundle.
    partial = folder.with_name(folder.name + ".partial")
    shutil.rmtree(partial, ignore_errors=True)
    partial.mkdir(parents=True)
    try:
        for name, text in texts.items():
            (partial / name).write_bytes(text.encode("utf-8"))
        partial.rename(folder)
    except BaseException:
        shutil.rmtree(partial, ignore_errors=True)
        raise
    return folder


def read_bundle(folder) -> Bundle:
    """A bundle's manifest, report and record header — only after every checksum matches."""
    folder = Path(folder)
    try:
        man = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
        if not isinstance(man, dict) or not isinstance(man.get("files"), dict):
            raise BundleError(f"{folder} has no valid manifest.json")
        for name in FILES:
            if _sha256((folder / name).read_bytes()) != man["files"][name]:
                raise BundleError(f"{name} does not match its checksum in manifest.json; the bundle was changed")
        report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
        header = json.loads((folder / "record.jsonl").read_text(encoding="utf-8").splitlines()[0])
    except (OSError, KeyError, ValueError, IndexError, TypeError, AttributeError) as error:
        raise BundleError(f"{folder} is not a readable bundle: {error}") from error
    return Bundle(man, report, header)
