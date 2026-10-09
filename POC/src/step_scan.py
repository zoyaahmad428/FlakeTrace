#!/usr/bin/env python3
"""Hours 2b/5/6 (single-scan protocol): exhaustive [candidate, victim] scan.

Per manifest/definitions.md the exhaustive scan is run ONCE per case. Ground
truth, the OBO baseline, the random baselines and the resource-ranked strategy
are all computed offline from this one outcome table -- no strategy re-runs.

Writes results/scan_<case_id>.csv and logs/raw/scan_<case_id>.tsv
"""
import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft

DIRECTION = {}   # case_id -> VICTIM | BRITTLE, from results/alone.csv


def load_directions():
    import csv as _csv
    with open(os.path.join(ft.POC, "results", "alone.csv"), newline="") as f:
        for r in _csv.DictReader(f):
            DIRECTION[r["case_id"]] = r["direction"]


CHUNK = 300  # orders per container invocation, keeps logs and memory bounded


def candidate_set(case):
    """Frozen rule: module test methods; if module > 300, restrict to the
    victim's package. Both subjects exceed 300, so both are package-restricted.
    The victim itself is never its own candidate."""
    return [s for s in ft.candidates(case["project"])
            if s.rsplit("#", 1)[0].rsplit(".", 1)[0] == case["victim_pkg"]
            and s != case["victim_spec"]]


def scan_case(case):
    project = case["project"]
    cid = case["case_id"]
    cands = candidate_set(case)
    outp = os.path.join(ft.POC, "results", "scan_%s.csv" % cid)
    logp = os.path.join(ft.POC, "logs", "raw", "scan_%s.tsv" % cid)

    if os.path.exists(outp):
        print("   %s already scanned, skipping" % cid)
        return

    direction = DIRECTION.get(cid, ft.VICTIM)
    print("== %s [%s] victim=%s candidates=%d"
          % (cid, direction, case["victim_spec"], len(cands)))
    t0 = time.time()
    rows = []
    logf = open(logp, "w")

    for start in range(0, len(cands), CHUNK):
        chunk = cands[start:start + CHUNK]
        orders = [("c%d" % (start + i), [c, case["victim_spec"]])
                  for i, c in enumerate(chunk)]
        res, proc = ft.run_batch(project, orders, timeout=120,
                                 tag="scan_%s" % cid)
        logf.write(proc.stdout)

        for i, c in enumerate(chunk):
            recs = res.get("c%d" % (start + i), [])
            cand_rec = next((r for r in recs if r["spec"] == c), None)
            vr = ft.victim_record(recs, case["victim_spec"])

            if vr is None:
                # victim never ran: candidate aborted the JVM (timeout/crash)
                aborted = recs[0]["exc"] if recs else "NoOutput"
                rows.append({
                    "candidate": c, "victim_status": "NOT_RUN",
                    "exc": aborted, "msg_norm": "", "top_frame": "",
                    "signature": "<victim-not-run>", "ms": 0,
                    "cand_status": cand_rec["status"] if cand_rec else "",
                })
                continue

            sig = ft.signature(vr["exc"], vr["msg"], vr["frames"], project)
            rows.append({
                "candidate": c, "victim_status": vr["status"],
                "exc": sig[0], "msg_norm": sig[1], "top_frame": sig[2],
                "signature": ft.sig_str(sig) if vr["status"] == "FAIL" else "",
                "ms": vr["ms"],
                "cand_status": cand_rec["status"] if cand_rec else "",
            })

        done = min(start + CHUNK, len(cands))
        print("   %s  %d/%d  (%.1f min)" % (cid, done, len(cands),
                                            (time.time() - t0) / 60), flush=True)

    logf.close()

    # An OD-relevant candidate flips the target away from its isolation
    # behaviour: a polluter makes a VICTIM fail; a state-setter makes a
    # BRITTLE target pass. Labelled before writing so the table is complete.
    want = "PASS" if direction == ft.BRITTLE else "FAIL"
    for r in rows:
        r["od_relevant"] = "YES" if r["victim_status"] == want else "NO"
    rel = [r for r in rows if r["od_relevant"] == "YES"]

    with open(outp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("   %s DONE: %d/%d OD-relevant candidates (target -> %s)  (%.1f min)"
          % (cid, len(rel), len(rows), want, (time.time() - t0) / 60), flush=True)


def main():
    load_directions()
    only = sys.argv[1:] or None
    for case in ft.load_cases():
        if only and case["case_id"] not in only:
            continue
        scan_case(case)


if __name__ == "__main__":
    main()
