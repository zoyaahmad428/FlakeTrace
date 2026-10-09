#!/usr/bin/env python3
"""Diagnostic: widen the candidate set to the FULL module.

Not part of the frozen protocol -- used to establish whether a zero result is
caused by the >300 package restriction or is genuine for the pairwise model.
Writes results/scanwide_<case_id>.csv
"""
import csv, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft

CHUNK = 400

def main():
    direction = {r["case_id"]: r["direction"] for r in
                 csv.DictReader(open(os.path.join(ft.POC, "results", "alone.csv")))}
    for case in ft.load_cases():
        cid = case["case_id"]
        if sys.argv[1:] and cid not in sys.argv[1:]:
            continue
        outp = os.path.join(ft.POC, "results", "scanwide_%s.csv" % cid)
        if os.path.exists(outp):
            print("  %s cached" % cid); continue
        cands = [s for s in ft.candidates(case["project"]) if s != case["victim_spec"]]
        want = "PASS" if direction.get(cid) == ft.BRITTLE else "FAIL"
        print("== %s full module: %d candidates (want %s)" % (cid, len(cands), want), flush=True)
        t0, rows = time.time(), []
        for st in range(0, len(cands), CHUNK):
            ch = cands[st:st+CHUNK]
            orders = [("w%d" % (st+i), [c, case["victim_spec"]]) for i, c in enumerate(ch)]
            res, _ = ft.run_batch(case["project"], orders, timeout=120, tag="wide_%s" % cid)
            for i, c in enumerate(ch):
                vr = ft.victim_record(res.get("w%d" % (st+i), []), case["victim_spec"])
                rows.append({"candidate": c,
                             "victim_status": vr["status"] if vr else "NOT_RUN",
                             "od_relevant": "YES" if vr and vr["status"] == want else "NO"})
            print("   %s %d/%d (%.1f min)" % (cid, min(st+CHUNK, len(cands)),
                                              len(cands), (time.time()-t0)/60), flush=True)
        with open(outp, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
        n = sum(1 for r in rows if r["od_relevant"] == "YES")
        print("   %s DONE: %d/%d OD-relevant (%.1f min)" % (cid, n, len(rows), (time.time()-t0)/60), flush=True)

if __name__ == "__main__":
    main()
