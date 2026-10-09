#!/usr/bin/env python3
"""Hour 2a: isolation behaviour and OD-direction classification.

Runs each target 10x alone in a fresh JVM under the frozen execution context.

  passes 10/10 -> VICTIM  (a polluter must make it fail)
  fails 10/10 with one stable signature -> BRITTLE (a state-setter must make it pass)
  anything else -> UNSTABLE (excluded; the frozen rules admit neither direction)

Writes results/alone.csv
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft

REPS = 10


def main():
    cases = ft.load_cases()
    out = []
    for project in sorted({c["project"] for c in cases}):
        pcases = [c for c in cases if c["project"] == project]
        orders = []
        for c in pcases:
            for i in range(REPS):
                orders.append(("%s__r%d" % (c["case_id"], i), [c["victim_spec"]]))

        print("== %s: %d isolation runs" % (project, len(orders)))
        res, proc = ft.run_batch(project, orders, timeout=120, tag="alone")
        with open(os.path.join(ft.POC, "logs", "raw",
                               "alone_%s.tsv" % project), "w") as f:
            f.write(proc.stdout)

        for c in pcases:
            passes, sigs = 0, {}
            for i in range(REPS):
                recs = res.get("%s__r%d" % (c["case_id"], i), [])
                vr = ft.victim_record(recs, c["victim_spec"])
                if vr is None:
                    sigs["<no-result>"] = sigs.get("<no-result>", 0) + 1
                elif vr["status"] == "PASS":
                    passes += 1
                else:
                    s = ft.sig_str(ft.signature(vr["exc"], vr["msg"],
                                                vr["frames"], project))
                    sigs[s] = sigs.get(s, 0) + 1

            if passes == REPS:
                direction, target_sig = ft.VICTIM, ""
            elif passes == 0 and len(sigs) == 1:
                direction, target_sig = ft.BRITTLE, list(sigs)[0]
            else:
                direction, target_sig = "UNSTABLE", ""

            out.append({
                "case_id": c["case_id"], "project": project,
                "victim": c["victim_spec"], "alone_passes": passes,
                "reps": REPS, "direction": direction,
                "alone_signature": target_sig,
            })
            print("   %-6s %2d/%d  %s" % (c["case_id"], passes, REPS, direction))

    p = os.path.join(ft.POC, "results", "alone.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("\nwrote", p)
    for d in (ft.VICTIM, ft.BRITTLE, "UNSTABLE"):
        n = [o["case_id"] for o in out if o["direction"] == d]
        print("  %-8s %d  %s" % (d, len(n), " ".join(n)))


if __name__ == "__main__":
    main()
