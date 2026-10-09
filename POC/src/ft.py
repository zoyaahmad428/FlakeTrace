#!/usr/bin/env python3
"""FlakeTrace POC driver (host side).

Owns case loading, container batch execution, and failure-signature
normalisation exactly as frozen in manifest/definitions.md.
"""
import csv
import os
import re
import subprocess
import sys

POC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE = "maven:3.9-eclipse-temurin-8"
MVN_VOLUME = "ftm2"

# Project-owned package prefixes, used for "topmost stack frame inside the
# project package" in the frozen failure-signature definition.
PROJECT_PKG = {"jsoniter": "com.jsoniter", "fastjson": "com.alibaba",
               "ormlite": "com.j256.ormlite"}

# Execution context: the project's declared suite setup, invoked before each
# order. jsoniter's Surefire runs suite classes, never test classes directly.
PROJECT_SETUP = {
    "jsoniter": "com.jsoniter.suite.StreamingTests",
    "fastjson": "-",   # plain Surefire, no suite wrapper
    "ormlite":  "-",   # plain Surefire, JUnit 4
}

# No per-project environment overrides.
#
# An earlier revision set TZ=Asia/Shanghai for fastjson because FJ-01/FJ-02 fail
# alone under the container's UTC default. That was WRONG and is retained here
# as a recorded methodological finding: those tests fail alone because they
# require JSON.defaultTimeZone to have been set by a predecessor
# (e.g. DateFieldTest8.setUp writes it globally and never restores it). They are
# BRITTLE tests, not victims. Forcing TZ=Asia/Shanghai makes the state-setter's
# write a no-op and erases the very order-dependence under measurement.
PROJECT_ENV = {
    "jsoniter": {},
    "fastjson": {},
    "ormlite": {},
}

# OD direction, determined empirically from isolation behaviour:
#   VICTIM  - passes alone, a polluter makes it fail
#   BRITTLE - fails alone, a state-setter makes it pass
VICTIM, BRITTLE = "VICTIM", "BRITTLE"


def project_of(url):
    if "json-iterator" in url:
        return "jsoniter"
    if "ormlite" in url:
        return "ormlite"
    return "fastjson"


def load_cases():
    with open(os.path.join(POC, "manifest", "cases.csv"), newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["project"] = project_of(r["project_url"])
        cls, mth = r["victim_fqn"].rsplit(".", 1)
        r["victim_spec"] = cls + "#" + mth
        r["victim_class"] = cls
        r["victim_pkg"] = cls.rsplit(".", 1)[0]
    return rows


def candidates(project):
    p = os.path.join(POC, "runner", project, "ft_tests.txt")
    with open(p) as f:
        return [l.strip() for l in f if l.strip()]


# --------------------------------------------------------------------------
# failure signature
# --------------------------------------------------------------------------

_MASKS = [
    (re.compile(r"0x[0-9a-fA-F]+"), "<HEX>"),
    (re.compile(r"@[0-9a-fA-F]{4,}"), "@<ID>"),
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}\S*"), "<TS>"),
    (re.compile(r"/tmp/\S+"), "<TMP>"),
    (re.compile(r"(/[\w.\-]+){2,}"), "<PATH>"),
    (re.compile(r"\d+"), "<N>"),
]


def normalise_msg(msg):
    """First line of the message, with volatile content masked."""
    if not msg:
        return ""
    s = msg.replace("\\n", "\n").split("\n")[0].strip()
    for rx, rep in _MASKS:
        s = rx.sub(rep, s)
    return s[:200]


def top_project_frame(frames, project):
    """Topmost stack frame inside the project package."""
    pkg = PROJECT_PKG[project]
    for fr in (frames or "").split("|"):
        if fr.startswith(pkg):
            return fr
    return ""


def signature(exc, msg, frames, project):
    """The frozen 3-tuple. Non-assertion outcomes stay distinguishable."""
    return (exc or "", normalise_msg(msg), top_project_frame(frames, project))


def sig_str(sig):
    return " || ".join(sig)


# --------------------------------------------------------------------------
# container execution
# --------------------------------------------------------------------------

def run_batch(project, orders, timeout=120, tag="batch"):
    """orders: list of (order_id, [spec, ...]).  Returns {order_id: [rec, ...]}.

    One container for the whole batch; one fresh JVM per order.
    """
    workdir = os.path.join(POC, "runner", project)
    ofile = os.path.join(workdir, "orders_%s.tsv" % tag)
    with open(ofile, "w") as f:
        for oid, specs in orders:
            f.write("%s\t%s\n" % (oid, " ".join(specs)))

    envargs = []
    for k, v in PROJECT_ENV.get(project, {}).items():
        envargs += ["-e", "%s=%s" % (k, v)]

    cmd = [
        "docker", "run", "--rm",
    ] + envargs + [
        "-v", "%s:/root/.m2" % MVN_VOLUME,
        "-v", "%s:/w" % os.path.join(POC, "subjects", project),
        "-v", "%s:/src:ro" % os.path.join(POC, "src"),
        "-v", "%s:/out" % workdir,
        "-w", "/w", IMAGE,
        "sh", "/src/run_orders.sh", "/out/orders_%s.tsv" % tag, str(timeout),
        PROJECT_SETUP.get(project, "-"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    results = {}
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) < 9 or parts[1] != "FT":
            continue
        oid, _, idx, spec, status, exc, msg, frames, ms = parts[:9]
        results.setdefault(oid, []).append({
            "idx": int(idx), "spec": spec, "status": status,
            "exc": exc, "msg": msg, "frames": frames, "ms": int(ms),
        })
    return results, proc


def victim_record(recs, victim_spec):
    """The record for the victim within one order (it runs last)."""
    for r in recs:
        if r["spec"] == victim_spec:
            return r
    return None
