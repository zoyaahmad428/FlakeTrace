"""Static resource-evidence extractor (Member 1, FlakeTrace Iteration 1).

Reads compiled .class files with `javap` and reports which shared resources a
test method reads and writes: static fields (getstatic/putstatic) and system
properties with a constant key (System.setProperty/getProperty and friends).
It never runs tests and never writes to the class directories.

Output format: docs/contracts/resource-evidence.md (Output 1).
Design decisions: docs/03-Design/decisions/ADR-002-evidence-extractor-implementation.md.

Status (Phase 4): depth 1-3 (the test method and its lifecycle methods, plus
calls into the project's own classes up to --depth); single-test mode (Output 1)
and pair mode (Output 2: resources the polluter writes and the victim reads).

Usage (from the repository root):
    python3 -m evidence.extract --classes DIR --test-classes DIR --test Class#method [--depth N]
    python3 -m evidence.extract --classes DIR --test-classes DIR \
        --polluter Class#method --victim Class#method [--depth N]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field

CONTRACT = "flaketrace.resource-evidence/v0-draft"
DEFAULT_DEPTH = 2              # contract default (ADR-002)
IMPLEMENTED_DEPTHS = {1, 2, 3}

# (owner, method) -> access, for the system-property calls we understand.
SYSPROP_CALLS = {
    ("java/lang/System", "setProperty"): "WRITE",
    ("java/lang/System", "clearProperty"): "WRITE",
    ("java/lang/System", "getProperty"): "READ",
    ("java/lang/Integer", "getInteger"): "READ",
    ("java/lang/Long", "getLong"): "READ",
    ("java/lang/Boolean", "getBoolean"): "READ",
}
# Calls that touch the whole Properties object; individual keys are not modelled.
SYSPROP_BULK = {("java/lang/System", "setProperties"), ("java/lang/System", "getProperties")}

LIFECYCLE_ANNOTATIONS = {
    "org/junit/Before": "BEFORE",
    "org/junit/After": "AFTER",
    "org/junit/BeforeClass": "BEFORE_CLASS",
    "org/junit/AfterClass": "AFTER_CLASS",
}
RULE_ANNOTATIONS = {"org/junit/Rule", "org/junit/ClassRule"}
RUNWITH_ANNOTATION = "org/junit/runner/RunWith"
JUNIT3_BASE = "junit.framework.TestCase"

# Always emitted with a pair (contract: "Fixed limitations").
FIXED_LIMITATIONS = [
    "Static analysis only; no runtime evidence (Iteration 2).",
    "Calls into JDK classes and third-party jars are not followed.",
    "Virtual dispatch to subclasses and reflection are not resolved (see VIRTUAL_DISPATCH, REFLECTION).",
    "Only static fields and constant-key system properties are modelled. Files, environment variables, "
    "network, databases, singletons reached through instance fields, etc. are not.",
    "Written values are not modelled: a polluter that writes and then restores the original value "
    "still produces a WRITE.",
    "Execution timing is not modelled (e.g. a victim <clinit> read that happens before the polluter runs).",
    "Missing evidence is not proof of independence.",
]

# Execution order of the roots; used to sort output deterministically.
VIA_ORDER = ["CLINIT", "BEFORE_CLASS", "SETUP", "BEFORE", "TEST_METHOD",
             "AFTER", "TEARDOWN", "AFTER_CLASS"]

# Instructions that push exactly one value and nothing else (used to find a
# constant system-property key among a call's arguments).
SIMPLE_PUSH = re.compile(r"^(ldc|ldc_w|ldc2_w|aconst_null|iconst_\w+|lconst_\d|"
                         r"fconst_\d|dconst_\d|bipush|sipush)$")

# javap -v line patterns
RX_CONSTANT = re.compile(r"^\s*#(\d+) = Utf8\s*(.*)$")
RX_CLASS = re.compile(r"^[\w ]*?\b(class|interface|enum) ([\w.$]+)(?: extends ([\w.$]+))?")
RX_MEMBER = re.compile(r"^  (\S.*);$")
RX_INSTRUCTION = re.compile(r"^\s+(\d+): (\w+)\b(.*)$")
RX_SWITCH_BODY = re.compile(r"^\s+(\d+: \d+|default: \d+|})\s*$")
RX_ANNOTATION = re.compile(r"^\s+\d+: #(\d+)\(")
RX_REF = re.compile(r"//\s*(Field|Method|InterfaceMethod|String|InvokeDynamic|class)\s+(.*)$")


class ExtractError(Exception):
    """An input problem (exit code 2) or an internal problem (exit code 1)."""

    def __init__(self, message, exit_code):
        super().__init__(message)
        self.exit_code = exit_code


@dataclass
class Instruction:
    offset: int
    opcode: str
    ref_kind: str = ""      # Field / Method / InterfaceMethod / String / InvokeDynamic
    owner: str = ""         # dotted class name, "" if javap omitted it (same class)
    name: str = ""          # field or method name, or the string constant
    descriptor: str = ""


@dataclass
class Method:
    name: str
    descriptor: str = ""
    flags: str = ""                                    # e.g. "ACC_PUBLIC, ACC_STATIC"
    annotations: list = field(default_factory=list)   # internal names, e.g. org/junit/Before
    instructions: list = field(default_factory=list)


@dataclass
class ClassInfo:
    name: str
    super_name: str = ""
    flags: str = ""
    methods: list = field(default_factory=list)
    fields: dict = field(default_factory=dict)          # field name -> annotations
    annotations: list = field(default_factory=list)     # class-level annotations


# ---------------------------------------------------------------- javap

def javap_command():
    """javap executable; FLAKETRACE_JAVAP overrides the one on PATH (used in tests)."""
    return os.environ.get("FLAKETRACE_JAVAP", "javap")


def run_javap(args):
    try:
        done = subprocess.run([javap_command()] + args, capture_output=True, text=True)
    except FileNotFoundError:
        raise ExtractError("javap not found (need a JDK 8+ on PATH)", 1)
    if done.returncode != 0:
        raise ExtractError("javap failed: " + (done.stderr or done.stdout).strip(), 1)
    return done.stdout


def javap_version():
    out = run_javap(["-version"]).strip()
    return out.splitlines()[0] if out else "unknown"


# ---------------------------------------------------------------- parsing

def member_name(header):
    """'public void after()' -> 'after'; 'static {}' -> '<clinit>'; constructor -> '<init>'."""
    if header.startswith("static {}"):
        return "<clinit>"
    match = re.search(r"([\w$]+)\(", header)
    return match.group(1) if match else None


def parse_ref(text):
    """Split a javap '// Field a/b/C.f:I' style comment into its parts."""
    match = RX_REF.search(text)
    if not match:
        return "", "", "", ""
    kind, body = match.groups()
    if kind == "String":
        return kind, "", body, ""
    if kind == "InvokeDynamic":
        return kind, "", body, ""
    if kind == "class":                     # `new` instruction: the class being instantiated
        return kind, body.replace("/", "."), "", ""
    target, _, descriptor = body.partition(":")
    owner, dot, name = target.rpartition(".")
    if not dot:                       # same-class reference: javap omits the owner
        owner, name = "", target
    return kind, owner.replace("/", "."), name.strip('"'), descriptor


def parse_class(text):
    """Parse `javap -v -p -c` output for one class."""
    constants = {}
    for line in text.splitlines():
        match = RX_CONSTANT.match(line)
        if match:
            constants[match.group(1)] = match.group(2)

    def annotation_name(line):
        match = RX_ANNOTATION.match(line)
        if not match:
            return None
        descriptor = constants.get(match.group(1), "")        # e.g. Lorg/junit/Before;
        return descriptor[1:-1] if descriptor.startswith("L") else descriptor

    info = None
    member = None          # current Method, or ("field", name)
    in_body = False        # between the class's "{" and "}"
    in_code = False
    in_annotations = False
    for line in text.splitlines():
        if info is None:
            match = RX_CLASS.match(line)
            if match:
                info = ClassInfo(name=match.group(2))
                if match.group(1) == "class":
                    info.super_name = match.group(3) or "java.lang.Object"
            continue
        if line == "{":
            in_body = True
            continue
        if line == "}":
            in_body, member, in_code, in_annotations = False, None, False, False
            continue

        if in_code:
            match = RX_INSTRUCTION.match(line)
            if match:
                kind, owner, name, descriptor = parse_ref(match.group(3))
                member.instructions.append(Instruction(
                    int(match.group(1)), match.group(2), kind, owner, name, descriptor))
                continue
            if RX_SWITCH_BODY.match(line) or line.strip().startswith("stack="):
                continue
            in_code = False

        if in_annotations:
            name = annotation_name(line)
            if name:
                if member is None:
                    info.annotations.append(name)
                elif isinstance(member, Method):
                    member.annotations.append(name)
                else:
                    info.fields[member[1]].append(name)
                continue
            if line.startswith("        ") and not line.strip().endswith(":"):
                continue            # JDK 9+ prints the decoded annotation name too
            in_annotations = False

        stripped = line.strip()
        if not in_body and stripped.startswith("flags:") and not info.flags:
            info.flags = stripped.split(":", 1)[1].strip()
        if stripped == "RuntimeVisibleAnnotations:":
            in_annotations = True
            continue
        if not in_body:
            continue
        match = RX_MEMBER.match(line)
        if match:
            header = match.group(1)
            if "(" in header or header.startswith("static {}"):
                member = Method(name=member_name(header))
                if member.name == info.name.rsplit(".", 1)[-1].rsplit("$", 1)[-1]:
                    member.name = "<init>"
                info.methods.append(member)
            else:
                field_name = header.split()[-1]
                info.fields[field_name] = []
                member = ("field", field_name)
            continue
        if stripped.startswith("descriptor:") and isinstance(member, Method):
            member.descriptor = stripped.split(":", 1)[1].strip()
        elif stripped.startswith("flags:") and isinstance(member, Method):
            member.flags = stripped.split(":", 1)[1].strip()
        elif stripped == "Code:":
            in_code = True
    if info is None:
        raise ExtractError("could not parse javap output", 1)
    return info


def parameter_count(descriptor):
    """Number of parameters in a JVM method descriptor, e.g. '(Ljava/lang/String;I)V' -> 2."""
    params = descriptor[1:descriptor.index(")")]
    count, i = 0, 0
    while i < len(params):
        while params[i] == "[":
            i += 1
        i = params.index(";", i) + 1 if params[i] == "L" else i + 1
        count += 1
    return count


# ---------------------------------------------------------------- project classes

class Project:
    """The target project's compiled classes; loads and caches them via javap."""

    def __init__(self, class_dirs):
        for d in class_dirs:
            if not os.path.isdir(d):
                raise ExtractError("class directory not found: " + d, 2)
        self.class_dirs = class_dirs
        self.cache = {}

    def contains(self, class_name):
        path = class_name.replace(".", os.sep) + ".class"
        return any(os.path.isfile(os.path.join(d, path)) for d in self.class_dirs)

    def load(self, class_name):
        if class_name not in self.cache:
            if not self.contains(class_name):
                raise ExtractError("class not found in project classes: " + class_name, 2)
            text = run_javap(["-v", "-p", "-c", "-cp",
                              os.pathsep.join(self.class_dirs), class_name])
            self.cache[class_name] = parse_class(text)
        return self.cache[class_name]

    def superclass_chain(self, class_name):
        """The class and its superclasses, as long as they are project classes."""
        chain = []
        while class_name and self.contains(class_name):
            info = self.load(class_name)
            chain.append(info)
            class_name = info.super_name
        return chain

    def declaring_class(self, owner, field_name):
        """The project class that declares a static field referenced via `owner`."""
        name = owner
        while name and self.contains(name):
            info = self.load(name)
            if field_name in info.fields:
                return name
            name = info.super_name
        return owner

    def resolve_method(self, owner, name, descriptor):
        """(ClassInfo, Method) that a call to owner.name(descriptor) names, or None.

        Looks in `owner` and then its project superclasses, the way the JVM resolves
        the statically named target. It cannot know which subclass override runs.
        """
        class_name = owner
        while class_name and self.contains(class_name):
            info = self.load(class_name)
            for method in info.methods:
                if method.name == name and method.descriptor == descriptor:
                    return info, method
            class_name = info.super_name
        return None

    def has_clinit(self, class_name):
        return (self.contains(class_name)
                and any(m.name == "<clinit>" for m in self.load(class_name).methods))


# ---------------------------------------------------------------- roots

def find_roots(project, test_class, test_method):
    """(via, ClassInfo, Method) for the test method and every lifecycle method that runs with it."""
    chain = project.superclass_chain(test_class)
    if not chain:
        raise ExtractError("test class not found in project classes: " + test_class, 2)
    junit3 = chain[-1].super_name == JUNIT3_BASE

    roots, defined = [], set()
    for info in chain:                      # most-derived class first
        for method in info.methods:
            if method.name == "<clinit>":
                roots.append(("CLINIT", info, method))
                continue
            key = (method.name, method.descriptor)
            if key in defined:              # overridden in a subclass: never runs
                continue
            defined.add(key)
            via = next((LIFECYCLE_ANNOTATIONS[a] for a in method.annotations
                        if a in LIFECYCLE_ANNOTATIONS), None)
            if junit3 and method.descriptor == "()V" and method.name in ("setUp", "tearDown"):
                via = "SETUP" if method.name == "setUp" else "TEARDOWN"
            if method.name == test_method and method.descriptor == "()V":
                via = "TEST_METHOD"
            if via:
                roots.append((via, info, method))
    if not any(via == "TEST_METHOD" for via, _, _ in roots):
        raise ExtractError("test method not found: %s#%s" % (test_class, test_method), 2)
    return chain, roots


# ---------------------------------------------------------------- scanning

def constant_key(instructions, index):
    """The constant string key of the system-property call at `index`, or None.

    The key is the call's first argument. We only trust it when every argument
    is pushed by one simple instruction right before the call and the first one
    is a string constant; anything else is reported as unsupported.
    """
    call = instructions[index]
    count = parameter_count(call.descriptor)
    window = instructions[index - count:index] if count <= index else []
    if len(window) != count or not all(SIMPLE_PUSH.match(i.opcode) for i in window):
        return None
    first = window[0]
    return first.name if first.ref_kind == "String" else None


def observation(kind, info, method, instruction, detail):
    return {"kind": kind, "class": info.name, "method": method.name,
            "bytecode_offset": instruction.offset, "detail": detail}


def make_access(category, resource, access, via, info, method, offset, path):
    if category == "static-field":
        resource_id = "%s#%s" % (resource["class"], resource["field"])
    else:
        resource_id = "sysprop:" + resource["key"]
    return {"category": category, "resource_id": resource_id, "resource": resource,
            "access": access, "class": info.name, "method": method.name,
            "descriptor": method.descriptor, "bytecode_offset": offset,
            "via": via, "depth": len(path) + 1,
            "call_path": path + [{"class": info.name, "method": method.name,
                                  "bytecode_offset": offset}]}


def walk_root(project, chain_names, via, root_info, root_method, max_depth, result):
    """Scan one root method and, breadth-first, the project methods it calls, up to max_depth.

    Breadth-first means every access is reported at the shortest depth it can be
    reached. Each method is scanned at most once per root, which also stops
    recursion and call cycles.
    """
    queue = [(root_info, root_method, [])]          # (class, method, caller frames)
    visited = {(root_info.name, root_method.name, root_method.descriptor)}
    while queue:
        info, method, path = queue.pop(0)
        walk = {"via": via, "path": path, "max_depth": max_depth,
                "queue": queue, "visited": visited}
        scan_method(project, chain_names, info, method, walk, result)


def scan_method(project, chain_names, info, method, walk, result):
    """Record the accesses and unsupported observations in one method's bytecode."""
    for index, ins in enumerate(method.instructions):
        owner = ins.owner or info.name
        if ins.opcode in ("getstatic", "putstatic"):
            declaring = project.declaring_class(owner, ins.name)
            resource = {"kind": "static-field", "class": declaring, "field": ins.name}
            access = "READ" if ins.opcode == "getstatic" else "WRITE"
            result["accesses"].append(make_access("static-field", resource, access, walk["via"],
                                                  info, method, ins.offset, walk["path"]))
            note_implicit_clinit(project, chain_names, declaring, info, method, ins, result)
        elif ins.opcode == "new" and ins.ref_kind == "class":
            note_implicit_clinit(project, chain_names, ins.owner, info, method, ins, result)
        elif ins.opcode == "invokedynamic":
            result["unsupported"].append(observation(
                "INVOKEDYNAMIC", info, method, ins, "invokedynamic not followed: " + ins.name))
        elif ins.opcode.startswith("invoke"):
            scan_call(project, chain_names, info, method, index, owner, walk, result)


def scan_call(project, chain_names, info, method, index, owner, walk, result):
    ins = method.instructions[index]
    internal = owner.replace(".", "/")
    if (internal, ins.name) in SYSPROP_CALLS:
        key = constant_key(method.instructions, index)
        if key is None:
            result["unsupported"].append(observation(
                "SYSPROP_NON_CONSTANT_KEY", info, method, ins,
                "%s.%s key is not a constant string" % (owner, ins.name)))
        else:
            resource = {"kind": "system-property", "key": key}
            result["accesses"].append(make_access(
                "system-property", resource, SYSPROP_CALLS[(internal, ins.name)],
                walk["via"], info, method, ins.offset, walk["path"]))
    elif (internal, ins.name) in SYSPROP_BULK:
        result["unsupported"].append(observation(
            "SYSPROP_BULK", info, method, ins, "%s.%s (whole Properties object)" % (owner, ins.name)))
    elif internal.startswith("java/lang/reflect/"):
        result["unsupported"].append(observation(
            "REFLECTION", info, method, ins, "%s.%s target not resolved" % (owner, ins.name)))
    elif project.contains(owner):
        if ins.opcode == "invokestatic":
            note_implicit_clinit(project, chain_names, owner, info, method, ins, result)
        follow_call(project, info, method, ins, owner, walk, result)
    else:
        result["external"].add(owner)


def follow_call(project, info, method, ins, owner, walk, result):
    """Queue the statically named project target of a call, if depth allows."""
    target_name = "%s#%s%s" % (owner, ins.name, ins.descriptor)
    resolved = project.resolve_method(owner, ins.name, ins.descriptor)
    if resolved is None:
        result["unsupported"].append(observation(
            "UNRESOLVED_CALL", info, method, ins, target_name + " not found in project classes"))
        return
    target_info, target = resolved
    if ins.opcode in ("invokevirtual", "invokeinterface") and may_be_overridden(target_info, target):
        key = (target_info.name, target.name, target.descriptor)
        if key not in result["dispatch_noted"]:
            result["dispatch_noted"].add(key)
            result["unsupported"].append(observation(
                "VIRTUAL_DISPATCH", info, method, ins,
                "%s: only %s.%s is followed; subclass overrides are not"
                % (target_name, target_info.name, target.name)))
    if not target.instructions:             # abstract or native: nothing to scan
        return
    key = (target_info.name, target.name, target.descriptor)
    if key in walk["visited"]:
        return
    if len(walk["path"]) + 1 >= walk["max_depth"]:
        result["unsupported"].append(observation(
            "DEPTH_LIMIT", info, method, ins,
            "%s not followed: --depth %d reached" % (target_name, walk["max_depth"])))
        return
    walk["visited"].add(key)
    frame = {"class": info.name, "method": method.name, "bytecode_offset": ins.offset}
    walk["queue"].append((target_info, target, walk["path"] + [frame]))


def may_be_overridden(info, method):
    """False when the JVM rules out an override (static, private, final method or final class)."""
    flags = method.flags + ", " + info.flags
    return not any(f in flags for f in ("ACC_STATIC", "ACC_PRIVATE", "ACC_FINAL"))


def note_implicit_clinit(project, chain_names, class_name, info, method, ins, result):
    """A static member of a project class with a <clinit> is used: its initialiser may run here."""
    if class_name in chain_names or class_name in result["clinit_noted"]:
        return
    if project.has_clinit(class_name):
        result["clinit_noted"].add(class_name)
        result["unsupported"].append(observation(
            "IMPLICIT_CLINIT", info, method, ins,
            "%s.<clinit> may run here on first use and is not analysed" % class_name))


def note_rules_and_runners(chain, result):
    for info in chain:
        if RUNWITH_ANNOTATION in info.annotations:
            result["unsupported"].append({"kind": "JUNIT_RULE_OR_RUNNER", "class": info.name,
                                          "method": None, "bytecode_offset": None,
                                          "detail": "@RunWith runner is not analysed"})
        for field_name, annotations in sorted(info.fields.items()):
            if RULE_ANNOTATIONS.intersection(annotations):
                result["unsupported"].append({"kind": "JUNIT_RULE_OR_RUNNER", "class": info.name,
                                              "method": None, "bytecode_offset": None,
                                              "detail": "rule field %s is not analysed" % field_name})


def analyse_test(project, test_id, depth=1):
    """Output 1 of the contract for one test method."""
    if "#" not in test_id:
        raise ExtractError("test must be Class#method, got: " + test_id, 2)
    test_class, test_method = test_id.split("#", 1)
    chain, roots = find_roots(project, test_class, test_method)
    chain_names = {info.name for info in chain}
    result = {"accesses": [], "unsupported": [], "external": set(),
              "clinit_noted": set(), "dispatch_noted": set()}
    for via, info, method in roots:
        walk_root(project, chain_names, via, info, method, depth, result)
    note_rules_and_runners(chain, result)

    def order(a):
        return (a["depth"], VIA_ORDER.index(a["via"]), a["class"], a["method"], a["bytecode_offset"])
    return {
        "test": {"class": test_class, "method": test_method},
        "accesses": sorted(result["accesses"], key=order),
        "unsupported_observations": result["unsupported"],
        "external_calls_not_followed": sorted(result["external"]),
    }


# ---------------------------------------------------------------- pairs (Output 2)

def find_edges(polluter_id, polluter, victim_id, victim):
    """Output 2: every resource the polluter WRITES and the victim READS.

    `polluter` and `victim` are analyse_test() results. An empty edge list sets
    no_supported_resource_evidence; it never means the tests are independent.
    """
    writes, reads = {}, {}
    for access in polluter["accesses"]:
        if access["access"] == "WRITE":
            writes.setdefault(access["resource_id"], []).append(access)
    for access in victim["accesses"]:
        if access["access"] == "READ":
            reads.setdefault(access["resource_id"], []).append(access)

    edges = []
    for resource_id in writes.keys() & reads.keys():
        write_locations, read_locations = writes[resource_id], reads[resource_id]
        edges.append({"resource_id": resource_id,
                      "resource": write_locations[0]["resource"],
                      "polluter_write_locations": write_locations,     # already in contract order
                      "victim_read_locations": read_locations})

    def edge_order(edge):
        return (min(a["depth"] for a in edge["polluter_write_locations"])
                + min(a["depth"] for a in edge["victim_read_locations"]), edge["resource_id"])
    edges.sort(key=edge_order)

    unsupported = ([dict(o, side="polluter") for o in polluter["unsupported_observations"]]
                   + [dict(o, side="victim") for o in victim["unsupported_observations"]])
    return {"polluter": test_identifier(polluter_id), "victim": test_identifier(victim_id),
            "edges": edges,
            "no_supported_resource_evidence": not edges,
            "unsupported_observations": unsupported,
            "limitations": list(FIXED_LIMITATIONS)}


def test_identifier(test_id):
    test_class, test_method = test_id.split("#", 1)
    return {"class": test_class, "method": test_method}


def report_fields(pair):
    """The contract's projection of a pair into Member 3's report fields.

    The report holds one resource and one location per side, so only the first
    edge and its first locations fit; everything else is named in `limitations`.
    """
    def location(access):
        return {"class": access["class"], "method": access["method"],
                "bytecode_offset": access["bytecode_offset"]}

    fields = {"shared_resource": None, "polluter_write_location": None,
              "victim_read_location": None, "instrumentation_level": "static-only",
              "limitations": list(pair["limitations"])}
    if not pair["edges"]:
        return fields
    first = pair["edges"][0]
    fields["shared_resource"] = first["resource"]
    fields["polluter_write_location"] = location(first["polluter_write_locations"][0])
    fields["victim_read_location"] = location(first["victim_read_locations"][0])
    for edge in pair["edges"][1:]:
        fields["limitations"].append("Another shared resource is not shown in this report: "
                                     + edge["resource_id"])
    dropped = len(first["polluter_write_locations"]) - 1 + len(first["victim_read_locations"]) - 1
    if dropped:
        fields["limitations"].append("%d further write/read location(s) of %s are not shown in this report"
                                     % (dropped, first["resource_id"]))
    return fields


# ---------------------------------------------------------------- command line

def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m evidence.extract",
                                     description="Static resource evidence from compiled classes.")
    parser.add_argument("--classes", required=True)
    parser.add_argument("--test-classes", required=True)
    parser.add_argument("--test")
    parser.add_argument("--polluter")
    parser.add_argument("--victim")
    parser.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    args = parser.parse_args(argv)
    try:
        pair_mode = bool(args.polluter or args.victim)
        if pair_mode and args.test:
            raise ExtractError("give either --test, or --polluter and --victim, not both", 2)
        if pair_mode and not (args.polluter and args.victim):
            raise ExtractError("pair mode needs both --polluter and --victim", 2)
        if not pair_mode and not args.test:
            raise ExtractError("give --test Class#method, or --polluter and --victim", 2)
        if pair_mode and args.polluter == args.victim:
            raise ExtractError("--polluter and --victim must be different tests", 2)
        if args.depth not in IMPLEMENTED_DEPTHS:
            raise ExtractError("--depth must be 1, 2 or 3", 2)
        project = Project([args.classes, args.test_classes])
        test_ids = [args.polluter, args.victim] if pair_mode else [args.test]
        tests = {test_id: analyse_test(project, test_id, args.depth) for test_id in test_ids}
        output = {
            "contract": CONTRACT,
            "instrumentation_level": "static-only",
            "analysis": {"depth": args.depth,
                         "class_dirs": [args.classes, args.test_classes],
                         "javap_version": javap_version()},
            "tests": tests,
        }
        if pair_mode:
            output["pair"] = find_edges(args.polluter, tests[args.polluter],
                                        args.victim, tests[args.victim])
    except ExtractError as error:
        print("error: " + str(error), file=sys.stderr)
        return error.exit_code
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
