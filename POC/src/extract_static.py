#!/usr/bin/env python3
"""Hours 3-4: bounded static-field resource extractor.

Implements the frozen POC resource scope:

  "ownerInternalName.fieldName:descriptor, static fields only (GETSTATIC /
   PUTSTATIC), direct references plus one hop into project-owned callees.
   Attribution per test method includes the method itself, the class's setUp()
   and tearDown(), and the class's <clinit>."

Reads javap -c -p dumps, emits results/resources_<project>.json:

  {"<pkg.Class#method>": {"reads": {res: [locs]}, "writes": {res: [locs]}}}

Each location is "<owner>.<method>@<bytecode-offset>", satisfying the POC
evidence-integrity gate that every overlap names the exact field and bytecode
location.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft

# Callee-expansion depth. 1 = frozen POC scope ("one hop"); >1 are ablations.
HOPS = int(os.environ.get("FT_HOPS", "1"))

# "  public void test_0() throws java.lang.Exception;"  /  "  static {};"
RX_MEMBER = re.compile(r"^\s{2}(\S.*);\s*$")
# "      12: putstatic     #5   // Field com/alibaba/fastjson/JSON.defaultTimeZone:Ljava/util/TimeZone;"
RX_FIELD = re.compile(
    r"^\s*(\d+):\s+(getstatic|putstatic)\s+#\d+\s+//\s*Field\s+(\S+)\s*$")
# "      15: invokestatic  #7   // Method com/alibaba/fastjson/JSON.parseObject:(...)V"
# Constructor call sites appear as  Owner."<init>":()V  -- javap QUOTES the
# name, so the quotes must be optional or every constructor edge is dropped.
RX_INVOKE = re.compile(
    r"^\s*(\d+):\s+invoke\w+\s+#\d+\s+//\s*(?:Method|InterfaceMethod)\s+"
    r"([\w/$]+)\.\"?([\w$<>]+)\"?:")
RX_CLASS = re.compile(r"^(?:public |final |abstract |static )*"
                      r"(?:class|interface|enum)\s+([\w.$]+)")


def method_name(sig):
    """Extract a bare method name from a javap member signature line."""
    if sig.startswith("static {}"):
        return "<clinit>"
    m = re.search(r"([\w$<>]+)\s*\(", sig)
    return m.group(1) if m else None


def parse_dump(path):
    """-> {class_internal_name: {method: {"fields": [...], "calls": [...]}}}"""
    out, cls, mth = {}, None, None
    with open(path, errors="replace") as f:
        for line in f:
            cm = RX_CLASS.match(line)
            if cm:
                cls = cm.group(1).replace(".", "/")
                out.setdefault(cls, {})
                mth = None
                continue
            if cls is None:
                continue
            mm = RX_MEMBER.match(line)
            if mm and "Code:" not in line:
                n = method_name(mm.group(1).strip())
                # javap DECLARES a constructor by the class's own name
                # ("public com.foo.Bar();") while call sites reference it as
                # "<init>". Normalise, or constructor bodies are never reached.
                if n and n == cls.rsplit("/", 1)[-1].rsplit("$", 1)[-1]:
                    n = "<init>"
                mth = n
                if n:
                    out[cls].setdefault(n, {"fields": [], "calls": []})
                continue
            if mth is None:
                continue
            fm = RX_FIELD.match(line)
            if fm:
                off, op, ref = fm.groups()
                # javap omits the owner when the field is declared in the class
                # being disassembled ("DEFAULT_GENERATE_FEATURE:I"). Qualify it,
                # or same-named fields in different classes collide into one
                # bogus shared resource.
                if "." not in ref.split(":", 1)[0]:
                    ref = "%s.%s" % (cls, ref)
                out[cls][mth]["fields"].append((op, ref, int(off)))
                continue
            im = RX_INVOKE.match(line)
            if im:
                off, owner, callee = im.groups()
                out[cls][mth]["calls"].append((owner, callee, int(off)))
    return out


def collect(project):
    workdir = os.path.join(ft.POC, "runner", project)
    pkg_prefix = ft.PROJECT_PKG[project].replace(".", "/")

    test_dump = parse_dump(os.path.join(workdir, "javap_test.txt"))
    main_dump = parse_dump(os.path.join(workdir, "javap_main.txt"))

    def direct(cls, mth):
        """(reads, writes) for one method body, as {res: [loc]}."""
        reads, writes = {}, {}
        info = (test_dump.get(cls) or main_dump.get(cls) or {}).get(mth)
        if not info:
            return reads, writes
        for op, ref, off in info["fields"]:
            tgt = reads if op == "getstatic" else writes
            tgt.setdefault(ref, []).append("%s.%s@%d" % (cls, mth, off))
        return reads, writes

    def merge(dst, src):
        for k, v in src.items():
            dst.setdefault(k, []).extend(v)

    result = {}
    for cls, methods in test_dump.items():
        for mth in methods:
            if not mth.startswith("test"):
                continue
            reads, writes = {}, {}
            # attribution: the method itself + setUp + tearDown + <clinit>,
            # then HOPS levels of expansion into project-owned callees.
            # HOPS=1 is the frozen POC scope; deeper settings are ablations.
            for m in (mth, "setUp", "tearDown", "<clinit>"):
                frontier, seen = [(cls, m)], {(cls, m)}
                for _depth in range(HOPS + 1):
                    nxt = []
                    for ocls, omth in frontier:
                        r, w = direct(ocls, omth)
                        merge(reads, r)
                        merge(writes, w)
                        info = ((test_dump.get(ocls) or main_dump.get(ocls) or {})
                                .get(omth))
                        for owner, callee, _off in (info or {}).get("calls", []):
                            if not owner.startswith(pkg_prefix):
                                continue
                            if (owner, callee) in seen:
                                continue
                            seen.add((owner, callee))
                            nxt.append((owner, callee))
                    frontier = nxt
                    if not frontier:
                        break
            spec = cls.replace("/", ".") + "#" + mth
            result[spec] = {"reads": reads, "writes": writes}
    return result


def main():
    for project in ("jsoniter", "fastjson", "ormlite"):
        workdir = os.path.join(ft.POC, "runner", project)
        # which test classes to disassemble: every candidate + victim class
        classes = sorted({s.split("#")[0] for s in ft.candidates(project)})
        with open(os.path.join(workdir, "javap_targets.txt"), "w") as f:
            f.write("\n".join(classes) + "\n")

        for which in ("test", "main"):
            dump = os.path.join(workdir, "javap_%s.txt" % which)
            if os.path.exists(dump) and os.path.getsize(dump) > 0:
                print("   %s/%s dump cached" % (project, which))
                continue
            cmd = ["docker", "run", "--rm",
                   "-v", "%s:/root/.m2" % ft.MVN_VOLUME,
                   "-v", "%s:/w" % os.path.join(ft.POC, "subjects", project),
                   "-v", "%s:/src:ro" % os.path.join(ft.POC, "src"),
                   "-v", "%s:/out" % workdir,
                   "-w", "/w", ft.IMAGE,
                   "sh", "/src/javap_dump.sh", which]
            p = subprocess.run(cmd, capture_output=True, text=True)
            print("   %s/%s: %s" % (project, which, p.stdout.strip().replace("\n", " | ")))

        res = collect(project)
        outp = os.path.join(ft.POC, "results", "resources_%s%s.json" % (project, "" if HOPS == 1 else "_h%d" % HOPS))
        with open(outp, "w") as f:
            json.dump(res, f)
        nz = sum(1 for v in res.values() if v["reads"] or v["writes"])
        allw = set()
        for v in res.values():
            allw |= set(v["writes"])
        print("== %s: %d test methods, %d with static-field evidence, "
              "%d distinct written fields" % (project, len(res), nz, len(allw)))


if __name__ == "__main__":
    main()
