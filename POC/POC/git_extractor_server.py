#!/usr/bin/env python3
"""Local backend for the FlakeTrace prototype.

Endpoints
  GET/POST /api/git-extract       real git metadata for the "Extract from git" panel
  GET/POST /api/evosuite-generate EvoSuite regression-suite generation (screen 09)
  GET      /api/health            toolchain + repo availability probe

The page is normally opened from file://, so every response carries permissive
CORS headers; without them the browser blocks the reply and the UI silently
falls back to canned data.
"""
import json
import os
import re
import shutil
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

DEFAULT_ROOTS = [
    Path(__file__).resolve().parent / "demo-project" / "demo-project",
    Path.home() / "workspace",
    Path.home() / "flaketrace",
    Path.home(),
]
PORT = 8765

# Where an EvoSuite jar may live. EVOSUITE_JAR wins if it is set.
EVOSUITE_JAR_CANDIDATES = [
    Path("/opt/evosuite/evosuite.jar"),
    Path("/usr/local/lib/evosuite.jar"),
    Path.home() / "evosuite.jar",
    Path.home() / "tools" / "evosuite.jar",
    Path.home() / "flaketrace" / "evosuite.jar",
]

TEST_FILE_GLOBS = ["*Test.java", "*Tests.java", "*TestCase.java", "*IT.java"]


def run_git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def is_git_repo(path: Path) -> bool:
    try:
        run_git(path, "rev-parse", "--show-toplevel")
        return True
    except Exception:
        return False


def find_git_root(repo_path: str | None) -> Path:
    if repo_path:
        p = Path(repo_path).expanduser()
        try:
            p = p.resolve()
        except Exception:
            pass
        if p.exists():
            try:
                return Path(run_git(p, "rev-parse", "--show-toplevel")).resolve()
            except Exception:
                pass

    for candidate in DEFAULT_ROOTS:
        if not candidate.exists():
            continue
        try:
            return Path(run_git(candidate, "rev-parse", "--show-toplevel")).resolve()
        except Exception:
            continue

    for base in DEFAULT_ROOTS:
        if not base.exists():
            continue
        for gitdir in sorted(base.rglob(".git")):
            if gitdir.is_dir():
                return gitdir.parent.resolve()
    raise FileNotFoundError("No git repository found under the configured project roots")


def repo_name(repo_root: Path) -> str:
    try:
        remote = run_git(repo_root, "config", "--get", "remote.origin.url")
    except Exception:
        remote = ""
    if remote:
        return remote.rstrip("/").split("/")[-1].replace(".git", "")
    return repo_root.name


def module_hint(repo_root: Path) -> str:
    for marker in ("pom.xml", "build.gradle", "build.gradle.kts"):
        for found in sorted(repo_root.rglob(marker)):
            if ".git" in found.parts:
                continue
            rel = found.parent.relative_to(repo_root)
            return str(rel).replace(os.sep, "/") if str(rel) != "." else "."
    return "."


def list_test_files(repo_root: Path) -> list[str]:
    """Tracked Java test files. git ls-files matches these globs at any depth."""
    try:
        raw = run_git(repo_root, "ls-files", "--", *TEST_FILE_GLOBS)
    except Exception:
        return []
    return [line for line in raw.splitlines() if line.strip()]


def parse_test_file(path: Path) -> tuple[str, str, list[str]]:
    """Return (package, class, [methods]) for one Java test file."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return "", "", []
    if "@Test" not in text and "@ParameterizedTest" not in text:
        return "", "", []

    pkg = ""
    m_pkg = re.search(r"^\s*package\s+([A-Za-z0-9_.]+)\s*;", text, re.M)
    if m_pkg:
        pkg = m_pkg.group(1)

    cls = ""
    m_cls = re.search(
        r"(?:public\s+|final\s+|abstract\s+)*class\s+([A-Za-z0-9_]+)", text
    )
    if m_cls:
        cls = m_cls.group(1)
    if not cls:
        return pkg, "", []

    methods = re.findall(
        r"@(?:Test|ParameterizedTest|RepeatedTest)\b[^\n]*\n(?:\s*@[^\n]*\n)*"
        r"\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+)*void\s+([A-Za-z0-9_]+)\s*\(",
        text,
    )
    # de-duplicate, keep source order
    seen, ordered = set(), []
    for m in methods:
        if m not in seen:
            seen.add(m)
            ordered.append(m)
    return pkg, cls, ordered


def test_targets(repo_root: Path, limit: int = 8) -> list[str]:
    out: list[str] = []
    for rel in list_test_files(repo_root):
        path = repo_root / rel
        if not path.exists():
            continue
        pkg, cls, methods = parse_test_file(path)
        if not cls or not methods:
            continue
        for method in methods[:3]:
            out.append(f"{pkg}.{cls}#{method}" if pkg else f"{cls}#{method}")
            if len(out) >= limit:
                return out
    return out


def test_classes(repo_root: Path, limit: int = 40) -> list[str]:
    """Fully qualified test class names — used to seed the EvoSuite target."""
    out: list[str] = []
    for rel in list_test_files(repo_root):
        path = repo_root / rel
        if not path.exists():
            continue
        pkg, cls, _ = parse_test_file(path)
        if not cls:
            continue
        out.append(f"{pkg}.{cls}" if pkg else cls)
        if len(out) >= limit:
            break
    return out


def resolve_source_ref(repo_root: Path, source: str, ref: str) -> tuple[str, str]:
    """Map the UI's 'Extract from' mode onto a real commit. Returns (rev, note)."""
    ref = (ref or "HEAD").strip() or "HEAD"

    if source == "merge-base":
        # HEAD is not a useful merge-base partner with itself.
        bases = [b for b in (ref, "origin/main", "main", "origin/master", "master")
                 if b != "HEAD"]
        for base in bases:
            try:
                rev = run_git(repo_root, "merge-base", "HEAD", base)
                return rev, f"merge-base of HEAD and {base}"
            except Exception:
                continue
        return "HEAD", "merge-base unavailable — fell back to HEAD"

    if source == "manual-sha":
        try:
            run_git(repo_root, "rev-parse", "--verify", f"{ref}^{{commit}}")
            return ref, f"manual revision {ref}"
        except Exception as exc:
            raise RuntimeError(f"revision '{ref}' does not resolve: {exc}") from exc

    if source == "ci-failure":
        globs = [f"*{g}" for g in TEST_FILE_GLOBS]
        try:
            rev = run_git(repo_root, "log", "-n", "1", "--format=%H", ref, "--", *globs)
            if rev:
                return rev, "most recent commit touching test sources"
        except Exception:
            pass
        return ref, "no test-source commit found — fell back to the given ref"

    return ref, f"tip of {ref}"


def commit_rows(repo_root: Path, rev: str, note: str) -> list[list[str]]:
    rows: list[list[str]] = []

    def subject(target: str) -> tuple[str, str]:
        try:
            line = run_git(repo_root, "log", "-n", "1", "--format=%h\x1f%s", target)
            short, _, subj = line.partition("\x1f")
            return short, subj
        except Exception:
            return "unknown", ""

    short, subj = subject(rev)
    rows.append(["HEAD", short, subj or note])

    p_short, p_subj = subject(f"{rev}^")
    if p_short != "unknown":
        rows.append(["parent", p_short, p_subj or "parent commit"])

    globs = [f"*{g}" for g in TEST_FILE_GLOBS]
    try:
        line = run_git(
            repo_root, "log", "-n", "1", "--format=%h\x1f%s", rev, "--", *globs
        )
        if line:
            t_short, _, t_subj = line.partition("\x1f")
            rows.append(["last test change", t_short, t_subj or "touched test sources"])
    except Exception:
        pass

    if len(rows) < 3:
        rows.append(["mode", "—", note])
    return rows[:4]


def extract_payload(source: str, ref: str, repo_path: str | None) -> dict:
    repo_root = find_git_root(repo_path)
    rev, note = resolve_source_ref(repo_root, source, ref)

    sha_full = run_git(repo_root, "rev-parse", rev)
    short_sha = sha_full[:7]

    try:
        branch = run_git(repo_root, "rev-parse", "--abbrev-ref", "HEAD")
    except Exception:
        branch = "HEAD"

    targets = test_targets(repo_root)
    discovered = bool(targets)
    if not targets:
        targets = [
            "com.example.UserServiceTest#shouldRejectAnonymousUser",
            "com.example.LoginTest#shouldLoginUser",
            "com.example.SessionTest#shouldExpireStaleSession",
        ]

    classes = test_classes(repo_root)

    return {
        "source": source,
        "mode_note": note,
        "ref": ref or "HEAD",
        "repo": repo_name(repo_root),
        "repo_path": str(repo_root),
        "sha": short_sha,
        "sha_full": sha_full,
        "module": module_hint(repo_root),
        "target": targets[0],
        "order": "\n".join(targets[:5]),
        "branch": branch,
        "commits": commit_rows(repo_root, rev, note),
        "test_files": len(list_test_files(repo_root)),
        "test_classes": classes,
        "targets_discovered": discovered,
        "status": "ok",
    }


# --------------------------------------------------------------------------
# EvoSuite
# --------------------------------------------------------------------------

def find_evosuite_jar() -> Path | None:
    env = os.environ.get("EVOSUITE_JAR")
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return p
    for candidate in EVOSUITE_JAR_CANDIDATES:
        if candidate.is_file():
            return candidate
    return None


def find_project_cp(repo_root: Path, module: str) -> str:
    """Best-effort compiled-classes classpath for -projectCP."""
    base = repo_root / module if module and module != "." else repo_root
    parts = []
    for rel in ("target/classes", "target/test-classes", "build/classes/java/main",
                "build/classes/java/test", "out/production/classes"):
        p = base / rel
        if p.is_dir():
            parts.append(str(p))
    return os.pathsep.join(parts)


def evosuite_toolchain() -> dict:
    java = shutil.which("java")
    jar = find_evosuite_jar()
    missing = []
    if not java:
        missing.append("java (JDK 8+ on PATH)")
    if not jar:
        missing.append("EvoSuite jar (set EVOSUITE_JAR, or drop evosuite.jar in ~/ or /opt/evosuite/)")
    return {
        "java": java or "",
        "jar": str(jar) if jar else "",
        "missing": missing,
        "available": not missing,
    }


def build_evosuite_command(tool: dict, opts: dict) -> list[str]:
    cmd = [tool["java"] or "java", "-jar", tool["jar"] or "evosuite.jar"]
    cmd += ["-class", opts["target_class"]]
    if opts["project_cp"]:
        cmd += ["-projectCP", opts["project_cp"]]
    cmd += ["-criterion", opts["criteria"]]
    cmd += [f"-Dsearch_budget={opts['search_budget']}"]
    cmd += [f"-Dassertion_strategy={opts['assertion_strategy']}"]
    cmd += [f"-Dtest_dir={opts['test_dir']}"]
    cmd += ["-Dassertions=true", "-Djunit_check=true", "-Dminimize=true"]
    cmd += [f"-seed={opts['seed']}"]
    if opts["deterministic"]:
        # EvoSuite emits wall-clock and randomness-dependent code unless told not to.
        cmd += ["-Dno_runtime_dependency=true", "-Dreplace_calls=false",
                "-Dvirtual_fs=false", "-Dvirtual_net=false"]
    return cmd


def evosuite_payload(params: dict) -> dict:
    repo_path = params.get("repoPath") or ""
    module = params.get("module") or "."
    target_class = (params.get("targetClass") or "").strip()
    criteria = params.get("criteria") or "branch:line:exception"
    assertion_strategy = params.get("assertionStrategy") or "mutation"
    deterministic = str(params.get("deterministic", "true")).lower() != "false"
    execute = str(params.get("execute", "false")).lower() == "true"

    try:
        search_budget = max(10, min(600, int(params.get("searchBudget") or 60)))
    except (TypeError, ValueError):
        search_budget = 60
    try:
        seed = int(params.get("seed") or 1)
    except (TypeError, ValueError):
        seed = 1

    try:
        repo_root = find_git_root(repo_path)
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "toolchain": evosuite_toolchain(),
            "executed": False,
        }

    if not target_class:
        classes = test_classes(repo_root, limit=1)
        target_class = classes[0] if classes else "com.example.UserService"

    module_root = repo_root / module if module and module != "." else repo_root
    test_dir = str(module_root / "src" / "test" / "java")
    project_cp = find_project_cp(repo_root, module)

    tool = evosuite_toolchain()
    opts = {
        "target_class": target_class,
        "project_cp": project_cp,
        "criteria": criteria,
        "search_budget": search_budget,
        "assertion_strategy": assertion_strategy,
        "test_dir": test_dir,
        "seed": seed,
        "deterministic": deterministic,
    }
    cmd = build_evosuite_command(tool, opts)

    payload = {
        "repo": repo_name(repo_root),
        "repo_path": str(repo_root),
        "module": module,
        "target_class": target_class,
        "criteria": criteria,
        "search_budget": search_budget,
        "assertion_strategy": assertion_strategy,
        "seed": seed,
        "deterministic": deterministic,
        "project_cp": project_cp,
        "test_dir": test_dir,
        "suite_class": target_class + "_ESTest",
        "suite_path": os.path.join(
            test_dir, *target_class.split(".")[:-1], target_class.split(".")[-1] + "_ESTest.java"
        ),
        "command": " ".join(cmd),
        "toolchain": tool,
        "executed": False,
        "generated_files": [],
        "log": "",
    }

    if not tool["available"]:
        payload["status"] = "unavailable"
        payload["error"] = "EvoSuite toolchain not present: " + "; ".join(tool["missing"])
        return payload

    if not project_cp:
        payload["status"] = "not_compiled"
        payload["error"] = (
            "No compiled classes under "
            f"{module_root} (looked for target/classes, build/classes/...). "
            "Build the module before generating a suite."
        )
        return payload

    if not execute:
        payload["status"] = "ready"
        return payload

    try:
        proc = subprocess.run(
            cmd, cwd=str(module_root), capture_output=True, text=True,
            timeout=search_budget + 180,
        )
        tail = (proc.stdout or "")[-4000:] + (proc.stderr or "")[-2000:]
        payload["log"] = tail.strip()
        payload["executed"] = True
        payload["exit_code"] = proc.returncode
        suite_dir = Path(test_dir)
        if suite_dir.exists():
            payload["generated_files"] = [
                str(p.relative_to(repo_root))
                for p in sorted(suite_dir.rglob("*_ESTest*.java"))
            ][:20]
        payload["status"] = "ok" if proc.returncode == 0 else "failed"
        if proc.returncode != 0:
            payload["error"] = f"EvoSuite exited with code {proc.returncode}"
    except subprocess.TimeoutExpired:
        payload["status"] = "timeout"
        payload["error"] = f"EvoSuite exceeded {search_budget + 180}s and was killed"
    except Exception as exc:
        payload["status"] = "error"
        payload["error"] = str(exc)
    return payload


def fallback_git_payload(source: str, ref: str, repo_path: str, error: str) -> dict:
    return {
        "source": source,
        "mode_note": "local extraction unavailable",
        "ref": ref or "HEAD",
        "repo": "unknown",
        "repo_path": repo_path or str(DEFAULT_ROOTS[0]),
        "sha": "unknown",
        "sha_full": "unknown",
        "module": ".",
        "target": "com.example.UserServiceTest#shouldRejectAnonymousUser",
        "order": "com.example.LoginTest#shouldLoginUser\n"
                 "com.example.UserServiceTest#shouldRejectAnonymousUser",
        "branch": "HEAD",
        "commits": [["error", "—", error]],
        "test_files": 0,
        "test_classes": [],
        "targets_discovered": False,
        "status": "fallback",
        "error": error,
    }


def health_payload() -> dict:
    repos = []
    for base in DEFAULT_ROOTS:
        if not base.exists():
            continue
        try:
            root = Path(run_git(base, "rev-parse", "--show-toplevel")).resolve()
            if str(root) not in repos:
                repos.append(str(root))
        except Exception:
            for gitdir in sorted(base.glob("*/.git")):
                if gitdir.is_dir() and str(gitdir.parent) not in repos:
                    repos.append(str(gitdir.parent.resolve()))
    return {
        "status": "ok",
        "git": bool(shutil.which("git")),
        "repos": repos[:10],
        "evosuite": evosuite_toolchain(),
    }


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        return

    # ---- helpers ----
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")

    def _send(self, payload: dict, code: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _params(self) -> dict:
        parsed = urlparse(self.path)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            try:
                body = json.loads(raw)
                if isinstance(body, dict):
                    params.update({k: v for k, v in body.items()})
            except json.JSONDecodeError:
                params.update({k: v[0] for k, v in parse_qs(raw).items()})
        return params

    # ---- verbs ----
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

        if path == "/api/health":
            self._params()
            self._send(health_payload())
            return

        if path == "/api/git-extract":
            params = self._params()
            source = params.get("source", "last-failing")
            ref = params.get("ref", "HEAD")
            repo_path = params.get("repoPath", "")
            try:
                self._send(extract_payload(source, ref, repo_path))
            except Exception as exc:
                self._send(fallback_git_payload(source, ref, repo_path, str(exc)))
            return

        if path == "/api/evosuite-generate":
            params = self._params()
            try:
                self._send(evosuite_payload(params))
            except Exception as exc:
                self._send({
                    "status": "error",
                    "error": str(exc),
                    "toolchain": evosuite_toolchain(),
                    "executed": False,
                })
            return

        self._params()
        self._send({"status": "not_found", "path": path}, code=404)


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"FlakeTrace backend on http://127.0.0.1:{PORT}")
    print("  GET /api/health")
    print("  GET /api/git-extract?source=last-failing&ref=HEAD[&repoPath=...]")
    print("  GET /api/evosuite-generate?targetClass=...&searchBudget=60[&execute=true]")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")
        server.shutdown()
