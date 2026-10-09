#!/usr/bin/env python3
"""Hour 7: replay each accepted [candidate, victim] pair 10x.

Frozen reproduced-case rule: victim passes alone >=10/10 AND flips with the
matching signature in >=9/10 replays of the confirmed order. For BRITTLE
targets the flip is FAIL-alone -> PASS-after, so the matching-signature clause
applies to the isolation signature instead.

Writes results/replay.csv
"""
import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft

REPS = 10


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - m) / d), min(1.0, (c + m) / d))


def main():
    alone = {r["case_id"]: r for r in
             csv.DictReader(open(os.path.join(ft.POC, "results", "alone.csv")))}
    out = []

    for case in ft.load_cases():
        cid = case["case_id"]
        sp = os.path.join(ft.POC, "results", "scan_%s.csv" % cid)
        if not os.path.exists(sp):
            continue
        scan = list(csv.DictReader(open(sp)))
        rel = [r for r in scan if r["od_relevant"] == "YES"]
        # Fall back to the widened diagnostic scan when the frozen package
        # restriction hid every OD-relevant candidate (recorded as such).
        if not rel:
            wp = os.path.join(ft.POC, "results", "scanwide_%s.csv" % cid)
            if os.path.exists(wp):
                wide = list(csv.DictReader(open(wp)))
                rel = [r for r in wide if r["od_relevant"] == "YES"]
                for r in rel:
                    r.setdefault("signature", "")
        if not rel:
            out.append({"case_id": cid, "accepted_pair": "", "direction":
                        alone[cid]["direction"], "matches": 0, "reps": 0,
                        "rate": "", "wilson_lo": "", "wilson_hi": "",
                        "reproduced": "NO", "target_signature": ""})
            continue

        direction = alone[cid]["direction"]
        first = rel[0]                      # first OD-relevant in declared order
        cand = first["candidate"]
        want = "PASS" if direction == ft.BRITTLE else "FAIL"
        target_sig = (alone[cid]["alone_signature"] if direction == ft.BRITTLE
                      else first.get("signature", ""))

        # The widened diagnostic scan records outcomes but not signatures. When
        # the target signature is unknown, establish it with one probe run of
        # the pair before replaying, so the >=9/10 rule still compares against
        # a fixed signature rather than accepting any failure.
        if want == "FAIL" and not target_sig:
            pres, _ = ft.run_batch(case["project"],
                                   [("%s__probe" % cid, [cand, case["victim_spec"]])],
                                   timeout=120, tag="probe_%s" % cid)
            pv = ft.victim_record(pres.get("%s__probe" % cid, []), case["victim_spec"])
            if pv is not None and pv["status"] == "FAIL":
                target_sig = ft.sig_str(ft.signature(pv["exc"], pv["msg"],
                                                     pv["frames"], case["project"]))
            print("   %s signature probe: %s" % (cid, target_sig[:90] or "<no failure>"))

        orders = [("%s__rp%d" % (cid, i), [cand, case["victim_spec"]])
                  for i in range(REPS)]
        res, proc = ft.run_batch(case["project"], orders, timeout=120,
                                 tag="replay_%s" % cid)
        with open(os.path.join(ft.POC, "logs", "raw",
                               "replay_%s.tsv" % cid), "w") as f:
            f.write(proc.stdout)

        matches = 0
        for i in range(REPS):
            vr = ft.victim_record(res.get("%s__rp%d" % (cid, i), []),
                                  case["victim_spec"])
            if vr is None or vr["status"] != want:
                continue
            if want == "FAIL":
                sig = ft.sig_str(ft.signature(vr["exc"], vr["msg"],
                                              vr["frames"], case["project"]))
                if sig != target_sig:
                    continue          # different failure is NOT a reproduction
            matches += 1

        lo, hi = wilson(matches, REPS)
        out.append({
            "case_id": cid, "accepted_pair": "%s -> %s" % (cand, case["victim_spec"]),
            "direction": direction, "matches": matches, "reps": REPS,
            "rate": round(matches / REPS, 3),
            "wilson_lo": round(lo, 3), "wilson_hi": round(hi, 3),
            "reproduced": "YES" if matches >= 9 else "NO",
            "target_signature": target_sig[:120],
        })
        print("%-6s %-7s %2d/%d  rate=%.2f  95%%CI=[%.2f,%.2f]  %s"
              % (cid, direction, matches, REPS, matches / REPS, lo, hi,
                 "REPRODUCED" if matches >= 9 else "below gate"))

    p = os.path.join(ft.POC, "results", "replay.csv")
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    print("\nwrote", p)


if __name__ == "__main__":
    main()
