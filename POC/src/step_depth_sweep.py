#!/usr/bin/env python3
"""Section 7.6 strengthening evidence: resource-depth sweep.

Sweeps the callee-expansion depth and, at each depth, evaluates two scoring
definitions against the committed outcome tables. Nothing is re-executed --
this is a pure re-analysis of the single exhaustive scan.

  W_R  |writes(c) INTERSECT reads(v)|              the frozen definition
  LEX  (|writes(c) INTERSECT reads(v)|,            writes first, then any touch
        |touches(c) INTERSECT reads(v)|)

LEX exists because two different pollution mechanisms appear in the data: a
direct PUTSTATIC of a field the target reads (visible to W_R once the depth
reaches the read), and mutation of state reachable THROUGH a static reference,
where the polluter never executes PUTSTATIC at all and W_R is structurally
blind to it.

Writes results/depth_sweep.csv
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft
import extract_static

DEPTHS = [1, 2, 3, 4]


def scan_rows(cid):
    for name in ("scan_%s.csv" % cid,):
        p = os.path.join(ft.POC, "results", name)
        if os.path.exists(p):
            return list(csv.DictReader(open(p)))
    return None


def evaluate(declared, relevant, score):
    order = sorted(declared, key=lambda x: (score(x), declared.index(x)))
    first = next((i for i, x in enumerate(order, 1) if x in relevant), None)
    return first


def main():
    cases = {c["case_id"]: c for c in ft.load_cases()}
    rows = []

    for depth in DEPTHS:
        extract_static.HOPS = depth
        res_cache = {}
        for cid, case in cases.items():
            scan = scan_rows(cid)
            if not scan:
                continue
            declared = [r["candidate"] for r in scan]
            relevant = {r["candidate"] for r in scan if r["od_relevant"] == "YES"}
            if not relevant:
                rows.append({"case_id": cid, "project": case["project"], "depth": depth,
                             "scoring": "-", "candidates": len(declared), "relevant": 0,
                             "obo": "", "first_rank": "", "saving_pct": "",
                             "best_score": "", "relevant_with_signal": "",
                             "reproduced": "NO"})
                continue

            proj = case["project"]
            if proj not in res_cache:
                print("  extracting %s at depth %d ..." % (proj, depth), flush=True)
                res_cache[proj] = extract_static.collect(proj)
            R = res_cache[proj]

            v = case["victim_spec"]
            vread = set(R.get(v, {}).get("reads", {}))
            obo = next(i for i, x in enumerate(declared, 1) if x in relevant)

            def parts(x):
                w = set(R.get(x, {}).get("writes", {}))
                t = w | set(R.get(x, {}).get("reads", {}))
                return len(w & vread), len(t & vread)

            for tag, key in (("W_R", lambda x: (-parts(x)[0],)),
                             ("LEX", lambda x: (-parts(x)[0], -parts(x)[1]))):
                first = evaluate(declared, relevant, key)
                best = max(parts(x)[0] if tag == "W_R" else max(parts(x))
                           for x in declared)
                withsig = sum(1 for x in relevant
                              if (parts(x)[0] if tag == "W_R" else max(parts(x))) > 0)
                rows.append({
                    "case_id": cid, "project": proj, "depth": depth, "scoring": tag,
                    "candidates": len(declared), "relevant": len(relevant),
                    "obo": obo, "first_rank": first,
                    "saving_pct": round(100.0 * (obo - first) / obo, 1),
                    "best_score": best, "relevant_with_signal": withsig,
                    "reproduced": "YES",
                })

    p = os.path.join(ft.POC, "results", "depth_sweep.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("\nwrote", p)

    # console summary: median saving and gate arms per depth/scoring
    repro = sorted({r["case_id"] for r in rows if r["reproduced"] == "YES"})
    print("\nreproduced cases:", " ".join(repro))
    print("\n%-6s %-5s %s" % ("depth", "score",
          "".join("%12s" % c for c in repro) + "   median   gate2  gate3"))
    for depth in DEPTHS:
        for tag in ("W_R", "LEX"):
            sel = [r for r in rows if r["depth"] == depth and r["scoring"] == tag]
            if not sel:
                continue
            by = {r["case_id"]: r for r in sel}
            cells, savs, t5, t20 = "", [], 0, 0
            for c in repro:
                r = by[c]
                cells += "%12s" % ("%d (%.0f%%)" % (r["first_rank"], r["saving_pct"]))
                savs.append(r["saving_pct"])
                if r["first_rank"] <= 5:
                    t5 += 1
                if r["first_rank"] <= max(1, r["candidates"] // 5):
                    t20 += 1
            s = sorted(savs)
            med = s[len(s)//2] if len(s) % 2 else (s[len(s)//2-1]+s[len(s)//2])/2
            print("%-6s %-5s %s   %6.1f%%   %s   %s" % (
                depth, tag, cells, med,
                "PASS" if max(t5, t20) >= 3 else "fail",
                "PASS" if med >= 30 else "fail"))


if __name__ == "__main__":
    main()
