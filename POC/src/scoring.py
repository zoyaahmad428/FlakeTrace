#!/usr/bin/env python3
"""Mechanism-aware candidate scoring (amendment A8).

The v2 lexicographic score covers mechanisms A and B only. Class D --
the polluter writes field f, a class initialiser reads f while building a
static, and the target reads THAT static -- links a write and a read on
DIFFERENT fields and is invisible to any writes-intersect-reads model.

Score is a tuple, ordered by strength of evidence, not by fitted weights:

    s1  |writes(c) INTERSECT reads(v)|      A: direct write -> read
    s3  1 if a clinit-transported link exists  D: write -> <clinit> -> read
    s2  |touches(c) INTERSECT reads(v)|      B: shared static, direction unknown

A is the strongest claim (the target reads exactly what the candidate wrote);
D is a specific, traceable dataflow; B is the weakest (co-touching a static).
Ties fall back to declared order, as in every other strategy.
"""

CLINIT_DEPTH = 3


def clinit_index(main_dump, pkg_prefix):
    """-> {field: {class whose <clinit> transitively reads it}}

    Built once per project. A class initialiser that reads a field is the
    transport mechanism for class D: whatever the initialiser stores into its
    own statics carries the polluted value forward.
    """
    index = {}

    def reads_of(cls, mth, depth, seen):
        if depth < 0 or (cls, mth) in seen:
            return set()
        seen.add((cls, mth))
        info = main_dump.get(cls, {}).get(mth)
        if not info:
            return set()
        out = {ref for op, ref, _ in info["fields"] if op == "getstatic"}
        for owner, callee, _ in info["calls"]:
            if owner.startswith(pkg_prefix):
                out |= reads_of(owner, callee, depth - 1, seen)
        return out

    for cls in main_dump:
        if "<clinit>" not in main_dump[cls]:
            continue
        for f in reads_of(cls, "<clinit>", CLINIT_DEPTH, set()):
            index.setdefault(f, set()).add(cls)
    return index


def make_scorer(resources, victim, clinit_idx, mode="MECH"):
    """Return score(candidate) -> sort key (lower sorts first).

    mode "W_R"  : v1 frozen score, mechanism A only
    mode "LEX"  : v2 score, mechanisms A then B
    mode "MECH" : A8 score, mechanisms A then D then B
    """
    vread = set(resources.get(victim, {}).get("reads", {}))
    # classes owning a static the victim reads -- the far end of a D link
    victim_owners = {f.split(".")[0] for f in vread}

    def parts(c):
        w = set(resources.get(c, {}).get("writes", {}))
        t = w | set(resources.get(c, {}).get("reads", {}))
        s1 = len(w & vread)
        s2 = len(t & vread)
        s3 = 0
        if mode == "MECH":
            for f in w:
                if victim_owners & clinit_idx.get(f, set()):
                    s3 = 1
                    break
        return s1, s2, s3

    def score(c):
        s1, s2, s3 = parts(c)
        if mode == "W_R":
            return (-s1,)
        if mode == "LEX":
            return (-s1, -s2)
        return (-s1, -s3, -s2)

    return score, parts
