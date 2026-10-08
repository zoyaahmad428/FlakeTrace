#!/usr/bin/env python3
"""FlakeTrace local backend.

Serves the prototype UI and does the work that is genuinely doable offline:
acquiring a project, reading its git history, statically analysing its test
sources for shared-state pollution, and driving EvoSuite when a JDK is present.

Anything that needs a JVM is reported as unavailable rather than faked.

  GET  /                        the UI
  GET  /api/health              toolchain probe
  GET  /api/projects            selectable projects (demo, local repos, zips)
  POST /api/source              acquire a project: demo | local | github | zip
  GET  /api/git-extract         commit metadata + discovered tests
  GET  /api/analyze             static shared-state analysis
  GET  /api/run                 execute a test order (needs a JDK)
  GET  /api/evosuite-generate   EvoSuite suite generation (needs a JDK + jar)
"""
import json
import os
import re
import shutil
import subprocess
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE = Path(__file__).resolve().parent
HOME = Path.home()
UI_FILE = BASE / "flaketrace.html"
DEMO_PROJECT = BASE / "demo-project" / "demo-project"
WORKDIR = HOME / ".flaketrace-work"
DEFAULT_ROOTS = [DEMO_PROJECT, HOME / "workspace", HOME / "flaketrace", HOME]
PORT = 8765

EVOSUITE_JAR_CANDIDATES = [
    Path("/opt/evosuite/evosuite.jar"),
    Path("/usr/local/lib/evosuite.jar"),
    HOME / "evosuite.jar",
    HOME / "tools" / "evosuite.jar",
]
TEST_FILE_GLOBS = ["*Test.java", "*Tests.java", "*TestCase.java", "*IT.java"]


# ---------------------------------------------------------------- git helpers
def run_git(repo_root: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo_root), *args],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "git command failed")
    return r.stdout.strip()


def find_git_root(repo_path: str | None) -> Path:
    if repo_path:
        p = Path(repo_path).expanduser()
        try:
            p = p.resolve()
        except Exception:
            pass
        # An explicit path that does not exist is an error, never a cue to
        # silently analyse some other project found under the default roots.
        if not p.exists():
            raise FileNotFoundError(f"path does not exist: {p}")
        try:
            return Path(run_git(p, "rev-parse", "--show-toplevel")).resolve()
        except Exception:
            return p
    for c in DEFAULT_ROOTS:
        if not c.exists():
            continue
        try:
            return Path(run_git(c, "rev-parse", "--show-toplevel")).resolve()
        except Exception:
            continue
    raise FileNotFoundError("no git repository found")


def repo_name(root: Path) -> str:
    try:
        remote = run_git(root, "config", "--get", "remote.origin.url")
    except Exception:
        remote = ""
    if remote:
        return remote.rstrip("/").split("/")[-1].replace(".git", "")
    return root.name


def module_hint(root: Path) -> str:
    best = None
    for marker in ("pom.xml", "build.gradle", "build.gradle.kts"):
        for f in sorted(root.rglob(marker)):
            if ".git" in f.parts or "target" in f.parts:
                continue
            rel = f.parent.relative_to(root)
            # prefer a module that actually holds test sources
            if (f.parent / "src" / "test" / "java").is_dir():
                return str(rel).replace(os.sep, "/") if str(rel) != "." else "."
            if best is None:
                best = str(rel).replace(os.sep, "/") if str(rel) != "." else "."
    return best or "."


# --------------------------------------------------------------- java parsing
def strip_code_noise(text: str) -> str:
    """Blank out comments and string literals, preserving offsets and line breaks.

    Without this, a javadoc line that merely mentions @AfterEach or names a
    field counts as real code -- which silently inverts the analysis.
    """
    out, i, n, state = [], 0, len(text), None
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if state is None:
            if c == "/" and nxt == "/":
                state, i = "line", i + 2
                out.append("  ")
            elif c == "/" and nxt == "*":
                state, i = "block", i + 2
                out.append("  ")
            elif c == '"':
                state, i = "str", i + 1
                out.append('"')
            elif c == "'":
                state, i = "char", i + 1
                out.append("'")
            else:
                out.append(c)
                i += 1
        elif state == "line":
            if c == "\n":
                state = None
                out.append("\n")
            else:
                out.append(" ")
            i += 1
        elif state == "block":
            if c == "*" and nxt == "/":
                state, i = None, i + 2
                out.append("  ")
            else:
                out.append("\n" if c == "\n" else " ")
                i += 1
        else:  # str / char
            closer = '"' if state == "str" else "'"
            if c == "\\":
                out.append("  ")
                i += 2
            elif c == closer:
                state, i = None, i + 1
                out.append(closer)
            elif c == "\n":
                state, i = None, i + 1
                out.append("\n")
            else:
                out.append(" ")
                i += 1
    return "".join(out)


def java_files(root: Path, test_only: bool = False) -> list[Path]:
    out = []
    for p in sorted(root.rglob("*.java")):
        parts = set(p.parts)
        if parts & {".git", "target", "build", "harness", "node_modules"}:
            continue
        if test_only and not any(p.match(g) for g in TEST_FILE_GLOBS):
            continue
        out.append(p)
    return out


METHOD_DECL = re.compile(
    r"^[ \t]*"
    r"(?:(?:public|private|protected|static|final|synchronized|abstract|native)[ \t]+)*"
    r"(?:<[^>\n]{0,80}>[ \t]+)?"
    r"[\w.$]+(?:<[^>\n]{0,120}>)?(?:\[\])*[ \t]+"
    r"(\w+)[ \t]*\([^;{)\n]{0,400}\)[ \t]*(?:throws[\w\s,.]{0,200})?\{",
    re.M,
)


def parse_java(path: Path) -> dict | None:
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    code = strip_code_noise(raw)

    pkg = ""
    m = re.search(r"^\s*package\s+([\w.]+)\s*;", code, re.M)
    if m:
        pkg = m.group(1)

    m = re.search(r"(?:^|\n)\s*(?:public\s+|final\s+|abstract\s+)*"
                  r"(?:class|enum|interface|record)\s+(\w+)", code)
    cls = m.group(1) if m else path.stem

    def line_of(idx: int) -> int:
        return code[:idx].count("\n") + 1

    def annotated_methods(tags: str) -> list[tuple[str, int]]:
        """Method names carrying one of these annotations.

        Two-step instead of one big regex: find the annotation, then take the
        first `void name(` after it. Survives same-line declarations and
        stacked annotations without any backtracking risk.
        """
        found, anno = [], re.compile(r"@(?:" + tags + r")\b")
        marks = [m.start() for m in anno.finditer(code)]
        for k, pos in enumerate(marks):
            stop = marks[k + 1] if k + 1 < len(marks) else len(code)
            window = code[pos:min(stop, pos + 400)]
            m2 = re.search(r"\bvoid\s+(\w+)\s*\(", window)
            if m2:
                found.append((m2.group(1), code[:pos].count("\n") + 1))
        return found

    test_methods = []
    for name, line in annotated_methods("Test|ParameterizedTest|RepeatedTest"):
        if name not in [x["name"] for x in test_methods]:
            test_methods.append({"name": name, "line": line})

    all_methods = []
    for mm in METHOD_DECL.finditer(code):
        name = mm.group(1)
        if name in ("if", "for", "while", "switch", "catch", "synchronized", "return"):
            continue
        start, depth, j = mm.end(), 1, mm.end()
        while j < len(code) and depth:
            if code[j] == "{":
                depth += 1
            elif code[j] == "}":
                depth -= 1
            j += 1
        all_methods.append({"name": name, "line": line_of(mm.start(1)),
                            "body_start": start, "body": code[start:j - 1]})

    teardown = [n for n, _ in annotated_methods("AfterEach|After|AfterAll|AfterClass")]

    static_fields = []
    for mm in re.finditer(
        r"\b(?:public|protected|private)?[ \t]*static[ \t]+(?!final\b)"
        r"([\w.$]+(?:<[^>\n]{0,80}>)?(?:\[\])*)[ \t]+(\w+)[ \t]*(?:=|;)",
        code,
    ):
        static_fields.append({"type": mm.group(1).strip(), "name": mm.group(2),
                              "line": line_of(mm.start())})

    # METHOD_DECL is line-anchored, so a method declared on the same line as
    # its class is invisible to it. Merge in the annotated methods so line ->
    # enclosing-method lookups still resolve.
    merged = sorted({(m["line"], m["name"]) for m in all_methods}
                    | {(m["line"], m["name"]) for m in test_methods})
    scope_methods = [{"line": ln, "name": nm} for ln, nm in merged]

    return {
        "path": str(path), "package": pkg, "class": cls,
        "fqcn": f"{pkg}.{cls}" if pkg else cls,
        "methods": test_methods, "all_methods": all_methods,
        "scope_methods": scope_methods,
        "teardown": teardown, "static_fields": static_fields,
        "raw_lines": raw.splitlines(), "code_lines": code.splitlines(),
        "code": code, "is_test": bool(test_methods),
    }


def method_at(info: dict, line: int, key: str = "scope_methods") -> str:
    best = ""
    for m in info[key]:
        if m["line"] <= line:
            best = m["name"]
    return best


def body_of(info: dict, name: str) -> str:
    for m in info["all_methods"]:
        if m["name"] == name:
            return m["body"]
    return ""


def methods_touching(prod: list[dict], pattern: re.Pattern) -> set[str]:
    """Production methods that reach the field, directly or through a call.

    UserServiceTest never names UserCache.currentUser -- it calls
    resolveCurrent(), which reads it. Without this closure the victim of an
    order-dependent failure is invisible.
    """
    touching = set()
    for p in prod:
        for m in p["all_methods"]:
            if pattern.search(body_of(p, m["name"])):
                touching.add(m["name"])

    for _ in range(8):  # fixpoint, bounded against mutual recursion
        grew = False
        for p in prod:
            for m in p["all_methods"]:
                if m["name"] in touching:
                    continue
                body = body_of(p, m["name"])
                for callee in touching:
                    if re.search(r"\b" + re.escape(callee) + r"\s*\(", body):
                        touching.add(m["name"])
                        grew = True
                        break
        if not grew:
            break
    return touching


def analyze_project(root: Path, module: str) -> dict:
    """Find shared mutable state and the tests that write and read it.

    Source-level analysis: it proposes candidates and says how each was
    attributed. It never claims verification -- that needs execution.
    """
    base = root / module if module and module != "." else root
    if not base.exists():
        base = root

    parsed = [p for p in (parse_java(f) for f in java_files(base)) if p]
    prod = [p for p in parsed if not p["is_test"]]
    tests = [p for p in parsed if p["is_test"]]

    resources = []
    for p in prod:
        for f in p["static_fields"]:
            resources.append({
                "owner": p["class"], "owner_fqcn": p["fqcn"],
                "field": f["name"], "type": f["type"],
                "declared_at": f"{Path(p['path']).name}:{f['line']}",
                "id": f"{p['class']}.{f['name']}",
            })

    findings = []
    for res in resources:
        wr = re.compile(rf"\b{re.escape(res['owner'])}\.{re.escape(res['field'])}\s*=(?!=)")
        rd = re.compile(rf"\b{re.escape(res['owner'])}\.{re.escape(res['field'])}\b(?!\s*=(?!=))")

        # production methods that reach the field, so indirect access is seen
        writer_methods = methods_touching(prod, wr)
        reader_methods = methods_touching(prod, rd) - writer_methods

        def call_re(names):
            return (re.compile(r"\.(?:" + "|".join(map(re.escape, sorted(names))) + r")\s*\(")
                    if names else None)

        w_call, r_call = call_re(writer_methods), call_re(reader_methods)

        writers, readers = [], []
        for t in tests:
            for i, cline in enumerate(t["code_lines"], start=1):
                raw = t["raw_lines"][i - 1].strip() if i <= len(t["raw_lines"]) else ""
                hit = {"test": t["fqcn"], "method": method_at(t, i),
                       "file": Path(t["path"]).name, "line": i, "code": raw}
                if wr.search(cline):
                    writers.append({**hit, "attribution": "direct",
                                    "how": "assignment to the field"})
                elif w_call and w_call.search(cline):
                    call = w_call.search(cline).group(0).strip(".( ")
                    writers.append({**hit, "attribution": "indirect",
                                    "how": f"via {call}(), which writes the field"})
                elif rd.search(cline):
                    readers.append({**hit, "attribution": "direct",
                                    "how": "reads the field"})
                elif r_call and r_call.search(cline):
                    call = r_call.search(cline).group(0).strip(".( ")
                    readers.append({**hit, "attribution": "indirect",
                                    "how": f"via {call}(), which reads the field"})

        # does the class reset the field in teardown?
        restoring = set()
        for t in tests:
            for td in t["teardown"]:
                body = body_of(t, td)
                if wr.search(body) or (w_call and w_call.search(body)):
                    restoring.add(t["fqcn"])
                    break
        for w in writers:
            w["restores"] = w["test"] in restoring

        polluters = [w for w in writers if not w["restores"]]
        writing_methods = {(w["test"], w["method"]) for w in writers}
        victims = [r for r in readers if (r["test"], r["method"]) not in writing_methods]

        if polluters and victims:
            sev, verdict = "bad", "order dependence"
            summary = (f"{polluters[0]['test'].split('.')[-1]} writes "
                       f"{res['id']} and never restores it; "
                       f"{victims[0]['test'].split('.')[-1]} reads it")
        elif writers and not polluters:
            sev, verdict = "ok", "restored"
            summary = "every writer resets the field in teardown"
        elif polluters:
            sev, verdict = "warn", "unrestored write"
            summary = "written without teardown, but no test reads it back"
        else:
            continue

        findings.append({"resource": res, "verdict": verdict, "severity": sev,
                         "summary": summary, "writers": writers, "readers": readers,
                         "polluters": polluters, "victims": victims})

    findings.sort(key=lambda f: {"bad": 0, "warn": 1, "ok": 2}[f["severity"]])

    suggested = None
    for f in findings:
        if f["severity"] != "bad":
            continue
        direct = [p for p in f["polluters"] if p["attribution"] == "direct"]
        p = (direct or f["polluters"])[0]
        v = f["victims"][0]
        suggested = {
            "polluter": f"{p['test']}#{p['method']}",
            "victim": f"{v['test']}#{v['method']}",
            "resource": f["resource"]["id"],
            "polluter_at": f"{p['file']}:{p['line']}",
            "victim_at": f"{v['file']}:{v['line']}",
            "order": [f"{p['test']}#{p['method']}", f"{v['test']}#{v['method']}"],
        }
        break

    return {
        "status": "ok", "repo_path": str(root), "module": module,
        "analysis": "static (source level) -- candidates proposed, not verified",
        "counts": {"production_classes": len(prod), "test_classes": len(tests),
                   "test_methods": sum(len(t["methods"]) for t in tests),
                   "shared_statics": len(resources)},
        "findings": findings, "suggested": suggested,
        "test_classes": [t["fqcn"] for t in tests],
        "test_methods": [f"{t['fqcn']}#{m['name']}" for t in tests for m in t["methods"]],
    }


# ------------------------------------------------------------------ toolchain
def find_evosuite_jar() -> Path | None:
    env = os.environ.get("EVOSUITE_JAR")
    if env and Path(env).expanduser().is_file():
        return Path(env).expanduser()
    for c in EVOSUITE_JAR_CANDIDATES:
        if c.is_file():
            return c
    return None


def toolchain() -> dict:
    java, javac, mvn = shutil.which("java"), shutil.which("javac"), shutil.which("mvn")
    jar = find_evosuite_jar()
    return {
        "java": java or "", "javac": javac or "", "mvn": mvn or "",
        "evosuite_jar": str(jar) if jar else "",
        "can_run_tests": bool(javac and java),
        "can_run_maven": bool(mvn and java),
        "can_run_evosuite": bool(java and jar),
        "missing": [m for m, ok in [
            ("JDK (javac + java on PATH)", bool(javac and java)),
            ("Maven", bool(mvn)),
            ("EvoSuite jar (set EVOSUITE_JAR)", bool(jar)),
        ] if not ok],
    }


# -------------------------------------------------------- source acquisition
def list_projects() -> dict:
    items = []
    if DEMO_PROJECT.exists():
        items.append({
            "id": "demo", "kind": "demo", "name": "demo-project",
            "path": str(DEMO_PROJECT),
            "note": "bundled worked example — a real order-dependent failure",
        })
    seen = {str(DEMO_PROJECT)}
    for base in [HOME, HOME / "flaketrace", HOME / "workspace", WORKDIR]:
        if not base.exists():
            continue
        for gitdir in sorted(base.glob("*/.git")):
            root = gitdir.parent.resolve()
            if str(root) in seen or root.name.startswith("."):
                continue
            seen.add(str(root))
            items.append({
                "id": str(root), "kind": "local", "name": root.name,
                "path": str(root), "note": "local git repository",
            })
    zips = []
    for base in [HOME, HOME / "flaketrace"]:
        if base.exists():
            zips += [p for p in sorted(base.glob("*.zip"))]
    for z in zips:
        items.append({
            "id": str(z), "kind": "zip", "name": z.name, "path": str(z),
            "note": f"zip archive · {z.stat().st_size // 1024} KB",
        })
    return {"status": "ok", "projects": items}


def acquire_source(params: dict) -> dict:
    kind = params.get("kind", "demo")
    WORKDIR.mkdir(parents=True, exist_ok=True)

    if kind == "demo":
        if not DEMO_PROJECT.exists():
            return {"status": "error", "error": f"demo project missing at {DEMO_PROJECT}"}
        root = DEMO_PROJECT

    elif kind == "local":
        raw = (params.get("path") or "").strip()
        if not raw:
            return {"status": "error", "error": "no path given"}
        root = Path(raw).expanduser()
        if not root.exists():
            return {"status": "error", "error": f"path does not exist: {root}"}

    elif kind == "github":
        url = (params.get("url") or "").strip()
        if not url:
            return {"status": "error", "error": "no repository URL given"}
        if not re.match(r"^(https://|git@)", url):
            return {"status": "error", "error": "expected an https:// or git@ URL"}
        name = url.rstrip("/").split("/")[-1].replace(".git", "")
        root = WORKDIR / name
        if root.exists():
            try:
                run_git(root, "fetch", "--depth", "50", "origin")
                return {"status": "ok", "kind": kind, "path": str(root),
                        "note": f"reused existing clone at {root}"}
            except Exception:
                shutil.rmtree(root, ignore_errors=True)
        r = subprocess.run(
            ["git", "clone", "--depth", "50", url, str(root)],
            capture_output=True, text=True, timeout=300,
        )
        if r.returncode != 0:
            return {"status": "error",
                    "error": (r.stderr.strip() or "clone failed")[-400:]}

    elif kind == "zip":
        raw = (params.get("path") or "").strip()
        if not raw:
            return {"status": "error", "error": "no zip path given"}
        zp = Path(raw).expanduser()
        if not zp.is_file():
            return {"status": "error", "error": f"not a file: {zp}"}
        dest = WORKDIR / zp.stem
        shutil.rmtree(dest, ignore_errors=True)
        dest.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(zp) as zf:
                names = zf.namelist()
                for n in names:
                    # refuse absolute paths and traversal
                    if n.startswith("/") or ".." in Path(n).parts:
                        return {"status": "error",
                                "error": f"refusing unsafe archive entry: {n}"}
                zf.extractall(dest)
        except zipfile.BadZipFile:
            return {"status": "error", "error": f"not a valid zip archive: {zp.name}"}
        # if the zip wrapped everything in one folder, descend into it
        entries = [p for p in dest.iterdir()]
        root = entries[0] if len(entries) == 1 and entries[0].is_dir() else dest

    else:
        return {"status": "error", "error": f"unknown source kind: {kind}"}

    root = root.resolve()
    is_git = (root / ".git").exists()
    tests = [p for p in java_files(root, test_only=True)]
    return {
        "status": "ok", "kind": kind, "path": str(root),
        "name": root.name, "is_git": is_git,
        "module": module_hint(root),
        "java_files": len(java_files(root)),
        "test_files": len(tests),
        "note": "acquired",
    }


# ------------------------------------------------------------- git extraction
def resolve_ref(root: Path, source: str, ref: str) -> tuple[str, str]:
    ref = (ref or "HEAD").strip() or "HEAD"
    if source == "merge-base":
        for b in [x for x in (ref, "origin/main", "main", "origin/master", "master")
                  if x != "HEAD"]:
            try:
                return run_git(root, "merge-base", "HEAD", b), f"merge-base with {b}"
            except Exception:
                continue
        return "HEAD", "no merge-base found — using HEAD"
    if source == "manual-sha":
        try:
            run_git(root, "rev-parse", "--verify", f"{ref}^{{commit}}")
            return ref, f"revision {ref}"
        except Exception as e:
            raise RuntimeError(f"'{ref}' does not resolve: {e}")
    if source == "ci-failure":
        globs = [f"*{g}" for g in TEST_FILE_GLOBS]
        try:
            rev = run_git(root, "log", "-n", "1", "--format=%H", ref, "--", *globs)
            if rev:
                return rev, "last commit touching test sources"
        except Exception:
            pass
        return ref, "no test-source commit — using the given ref"
    return ref, f"tip of {ref}"


def git_extract(params: dict) -> dict:
    root = find_git_root(params.get("repoPath") or "")
    if not (root / ".git").exists():
        return {"status": "no_git", "repo": root.name, "repo_path": str(root),
                "module": module_hint(root),
                "error": "not a git repository — commit history unavailable"}

    rev, note = resolve_ref(root, params.get("source", "last-failing"),
                            params.get("ref", "HEAD"))
    sha_full = run_git(root, "rev-parse", rev)

    commits = []
    try:
        raw = run_git(root, "log", "-n", "6", "--format=%h\x1f%s\x1f%ar", rev)
        for line in raw.splitlines():
            h, _, rest = line.partition("\x1f")
            subj, _, when = rest.partition("\x1f")
            commits.append([h, subj, when])
    except Exception:
        pass

    try:
        branch = run_git(root, "rev-parse", "--abbrev-ref", "HEAD")
    except Exception:
        branch = "HEAD"

    module = module_hint(root)
    analysis = analyze_project(root, module)

    return {
        "status": "ok", "repo": repo_name(root), "repo_path": str(root),
        "sha": sha_full[:7], "sha_full": sha_full, "branch": branch,
        "ref": params.get("ref", "HEAD"), "mode_note": note,
        "module": module, "commits": commits,
        "test_files": len([p for p in java_files(root, test_only=True)]),
        "test_methods": analysis["test_methods"],
        "test_classes": analysis["test_classes"],
        "suggested": analysis["suggested"],
    }


# ---------------------------------------------------------------------- patch
def build_patch(params: dict) -> dict:
    """Generate a real unified diff that restores the polluted field.

    The fix is mechanical: capture the field before each test, put it back
    after. It touches only the polluter's test class -- never the victim,
    never an assertion, never production source.
    """
    import difflib

    root = Path(params.get("repoPath") or str(DEMO_PROJECT)).expanduser()
    module = params.get("module") or module_hint(root)
    analysis = analyze_project(root, module)

    bad = [f for f in analysis["findings"] if f["severity"] == "bad"]
    if not bad:
        return {"status": "nothing_to_fix",
                "error": "no unrestored write with a reader was found"}

    finding = bad[0]
    res = finding["resource"]
    direct = [w for w in finding["polluters"] if w["attribution"] == "direct"]
    if not direct:
        return {"status": "not_attributable",
                "error": ("the write is only reachable through a helper, so it "
                          "cannot be attributed to one test class"),
                "resource": res["id"]}

    polluter = direct[0]
    base = root / module if module and module != "." else root
    target_file = None
    for f in java_files(base, test_only=True):
        if f.name == polluter["file"]:
            target_file = f
            break
    if target_file is None:
        return {"status": "error", "error": f"cannot locate {polluter['file']}"}

    original = target_file.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    code = strip_code_noise(original)

    m = re.search(r"(?:^|\n)\s*(?:public\s+|final\s+|abstract\s+)*class\s+\w+[^{]*\{",
                  code)
    if not m:
        return {"status": "error", "error": "cannot find the class body"}
    insert_at = code[:m.end()].count("\n") + 1

    field, owner, ftype = res["field"], res["owner"], res["type"]
    cap = field[0].upper() + field[1:]
    block = [
        "\n",
        f"    // FlakeTrace: {owner}.{field} is left set by this class; capture and restore it.\n",
        f"    private {ftype} flakeTracePrevious{cap};\n",
        "\n",
        "    @org.junit.jupiter.api.BeforeEach\n",
        f"    void flakeTraceCapture() {{ flakeTracePrevious{cap} = {owner}.{field}; }}\n",
        "\n",
        "    @org.junit.jupiter.api.AfterEach\n",
        f"    void flakeTraceRestore() {{ {owner}.{field} = flakeTracePrevious{cap}; }}\n",
    ]
    patched = lines[:insert_at] + block + lines[insert_at:]

    rel = str(target_file.relative_to(root))
    diff = list(difflib.unified_diff(lines, patched,
                                     fromfile="a/" + rel, tofile="b/" + rel, n=3))

    if str(params.get("apply", "")).lower() == "true":
        target_file.write_text("".join(patched), encoding="utf-8")
        applied = True
    else:
        applied = False

    return {
        "status": "ok", "applied": applied, "file": rel,
        "abs_path": str(target_file), "resource": res["id"],
        "polluter": f"{polluter['test']}#{polluter['method']}",
        "polluter_at": f"{polluter['file']}:{polluter['line']}",
        "victim": (f"{finding['victims'][0]['test']}#{finding['victims'][0]['method']}"
                   if finding["victims"] else ""),
        "diff": "".join(diff),
        "added_lines": len(block),
        "strategy": "capture-and-restore-static-field",
        "policy": [
            ["test code only", True, f"1 file under src/test/java: {rel}"],
            ["no assertion changed", True, "0 assertions added, removed or weakened"],
            ["target test untouched", True, "the victim's source is not in the diff"],
            ["no @Disabled / @Ignore", True, "0 occurrences added"],
            ["no retries or reruns", True, "no @RepeatedTest, no rerunFailingTestsCount"],
            ["no new dependencies", True, "pom.xml not in the diff"],
            ["production source untouched", True, "src/main/java not in the diff"],
            ["within size budget", True, f"{len(block)} lines of a 40-line limit"],
        ],
    }


def revert_patch(params: dict) -> dict:
    root = Path(params.get("repoPath") or str(DEMO_PROJECT)).expanduser()
    if not (root / ".git").exists():
        return {"status": "error", "error": "not a git repository — cannot revert"}
    try:
        run_git(root, "checkout", "--", ".")
        return {"status": "ok", "note": "working tree restored with git checkout"}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ------------------------------------------------------------------- run tests
def run_order(params: dict) -> dict:
    root = Path(params.get("repoPath") or str(DEMO_PROJECT)).expanduser()
    order = [s for s in (params.get("order") or "").split("\n") if s.strip()]
    tool = toolchain()

    if not order:
        return {"status": "error", "error": "no test order given", "toolchain": tool}
    if not tool["can_run_tests"]:
        return {
            "status": "unavailable", "toolchain": tool, "order": order,
            "error": "No JDK on PATH — javac and java are required to execute tests.",
            "hint": "sudo apt install default-jdk   (or point PATH at an existing JDK)",
            "command": f"cd {root} && ./demo.sh",
        }

    harness = root / "harness"
    if not harness.is_dir():
        return {"status": "unsupported", "toolchain": tool,
                "error": "this project has no FlakeTrace harness; use Maven instead",
                "command": f"cd {root} && mvn test"}

    out = root / "build" / "classes"
    shutil.rmtree(root / "build", ignore_errors=True)
    out.mkdir(parents=True, exist_ok=True)
    srcs = ([str(p) for p in (harness / "org/junit/jupiter/api").glob("*.java")]
            + [str(harness / "FlakeDemo.java")]
            + [str(p) for p in java_files(root) if "harness" not in p.parts])
    c = subprocess.run([tool["javac"], "-nowarn", "-d", str(out), *srcs],
                       capture_output=True, text=True, timeout=180)
    if c.returncode != 0:
        return {"status": "compile_failed", "toolchain": tool,
                "error": (c.stderr or "")[-1500:]}

    r = subprocess.run([tool["java"], "-cp", str(out), "FlakeDemo", *order],
                       capture_output=True, text=True, timeout=180)
    return {
        "status": "ok", "toolchain": tool, "order": order,
        "exit_code": r.returncode,
        "passed": r.returncode == 0,
        "output": (r.stdout or "").strip(),
        "command": f"java -cp build/classes FlakeDemo {' '.join(order)}",
    }


# -------------------------------------------------------------------- evosuite
def find_project_cp(root: Path, module: str) -> str:
    base = root / module if module and module != "." else root
    parts = []
    for rel in ("target/classes", "target/test-classes", "build/classes/java/main",
                "build/classes/java/test", "build/classes", "out/production/classes"):
        p = base / rel
        if p.is_dir():
            parts.append(str(p))
    return os.pathsep.join(parts)


def evosuite_generate(params: dict) -> dict:
    tool = toolchain()
    try:
        root = find_git_root(params.get("repoPath") or "")
    except Exception:
        root = Path(params.get("repoPath") or str(DEMO_PROJECT)).expanduser()

    module = params.get("module") or module_hint(root)
    target = (params.get("targetClass") or "").strip()
    if not target:
        a = analyze_project(root, module)
        target = a["test_classes"][0] if a["test_classes"] else "com.example.UserCache"

    try:
        budget = max(10, min(600, int(params.get("searchBudget") or 60)))
    except (TypeError, ValueError):
        budget = 60
    try:
        seed = int(params.get("seed") or 1)
    except (TypeError, ValueError):
        seed = 1

    criteria = params.get("criteria") or "branch:line:exception"
    strategy = params.get("assertionStrategy") or "mutation"
    deterministic = str(params.get("deterministic", "true")).lower() != "false"
    execute = str(params.get("execute", "false")).lower() == "true"

    mroot = root / module if module and module != "." else root
    test_dir = str(mroot / "src" / "test" / "java")
    cp = find_project_cp(root, module)

    cmd = [tool["java"] or "java", "-jar", tool["evosuite_jar"] or "evosuite.jar",
           "-class", target]
    if cp:
        cmd += ["-projectCP", cp]
    cmd += ["-criterion", criteria, f"-Dsearch_budget={budget}",
            f"-Dassertion_strategy={strategy}", f"-Dtest_dir={test_dir}",
            "-Dassertions=true", "-Djunit_check=true", "-Dminimize=true",
            f"-seed={seed}"]
    if deterministic:
        cmd += ["-Dno_runtime_dependency=true", "-Dreplace_calls=false",
                "-Dvirtual_fs=false", "-Dvirtual_net=false"]

    payload = {
        "repo_path": str(root), "module": module, "target_class": target,
        "criteria": criteria, "search_budget": budget, "seed": seed,
        "assertion_strategy": strategy, "deterministic": deterministic,
        "project_cp": cp, "test_dir": test_dir,
        "suite_class": target + "_ESTest",
        "suite_path": os.path.join(test_dir, *target.split(".")[:-1],
                                   target.split(".")[-1] + "_ESTest.java"),
        "command": " ".join(cmd), "toolchain": tool,
        "executed": False, "generated_files": [], "log": "",
    }

    if not tool["can_run_evosuite"]:
        need = []
        if not tool["java"]:
            need.append("java")
        if not tool["evosuite_jar"]:
            need.append("evosuite.jar (set EVOSUITE_JAR)")
        payload["status"] = "unavailable"
        payload["error"] = "EvoSuite cannot run here — missing: " + ", ".join(need)
        return payload
    if not cp:
        payload["status"] = "not_compiled"
        payload["error"] = (f"no compiled classes under {mroot}; "
                            "build the module first (mvn -q compile)")
        return payload
    if not execute:
        payload["status"] = "ready"
        return payload

    try:
        proc = subprocess.run(cmd, cwd=str(mroot), capture_output=True,
                              text=True, timeout=budget + 180)
        payload["executed"] = True
        payload["exit_code"] = proc.returncode
        payload["log"] = ((proc.stdout or "")[-4000:] + (proc.stderr or "")[-2000:]).strip()
        d = Path(test_dir)
        if d.exists():
            payload["generated_files"] = [
                str(p.relative_to(root)) for p in sorted(d.rglob("*_ESTest*.java"))
            ][:20]
        payload["status"] = "ok" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            payload["error"] = f"EvoSuite exited {proc.returncode}"
    except subprocess.TimeoutExpired:
        payload["status"] = "timeout"
        payload["error"] = f"exceeded {budget + 180}s"
    except Exception as e:
        payload["status"] = "error"
        payload["error"] = str(e)
    return payload


# ---------------------------------------------------------------------- server
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        return

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, payload, code=200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _html(self, path: Path):
        if not path.is_file():
            self._json({"status": "error", "error": f"missing {path}"}, 404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _params(self) -> dict:
        q = urlparse(self.path).query
        params = {k: v[0] for k, v in parse_qs(q).items()}
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            raw = self.rfile.read(n).decode("utf-8", "replace")
            try:
                b = json.loads(raw)
                if isinstance(b, dict):
                    params.update(b)
            except json.JSONDecodeError:
                params.update({k: v[0] for k, v in parse_qs(raw).items()})
        return params

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Content-Length", "0")
        self._cors()
        self.end_headers()

    def do_POST(self):
        self._route()

    def do_GET(self):
        self._route()

    def _route(self):
        path = urlparse(self.path).path.rstrip("/") or "/"

        if path in ("/", "/index.html", "/flaketrace.html"):
            self._params()
            self._html(UI_FILE)
            return

        p = self._params()
        try:
            if path == "/api/health":
                self._json({"status": "ok", "git": bool(shutil.which("git")),
                            "toolchain": toolchain(),
                            "demo_project": DEMO_PROJECT.exists()})
            elif path == "/api/projects":
                self._json(list_projects())
            elif path == "/api/source":
                self._json(acquire_source(p))
            elif path == "/api/git-extract":
                self._json(git_extract(p))
            elif path == "/api/analyze":
                root = find_git_root(p.get("repoPath") or "")
                self._json(analyze_project(root, p.get("module") or module_hint(root)))
            elif path == "/api/patch":
                self._json(build_patch(p))
            elif path == "/api/revert":
                self._json(revert_patch(p))
            elif path == "/api/run":
                self._json(run_order(p))
            elif path == "/api/evosuite-generate":
                self._json(evosuite_generate(p))
            else:
                self._json({"status": "not_found", "path": path}, 404)
        except Exception as e:
            self._json({"status": "error", "error": str(e)}, 200)


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"FlakeTrace backend  →  http://127.0.0.1:{PORT}/")
    t = toolchain()
    print(f"  JDK: {'yes' if t['can_run_tests'] else 'no'}   "
          f"Maven: {'yes' if t['mvn'] else 'no'}   "
          f"EvoSuite: {'yes' if t['can_run_evosuite'] else 'no'}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")
