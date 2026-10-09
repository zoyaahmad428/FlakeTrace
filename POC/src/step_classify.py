#!/usr/bin/env python3
"""Section 7.6 strengthening evidence: per-case cause classification.

For each reproduced case, decide -- from evidence, not narrative -- which
mechanism carries the interference, by asking what the static-field model can
actually see about the CONFIRMED OD-relevant candidates:

  A  DIRECT-PUTSTATIC   some confirmed candidate PUTSTATICs a field the target
                        reads, within the declared depth.
  B  VIA-STATIC-REF     no confirmed candidate PUTSTATICs such a field, but one
                        TOUCHES a static the target reads -- i.e. pollution
                        flows through mutation of state reachable from a static
                        reference, which a putstatic-only model cannot express.
  C  UNSUPPORTED        no confirmed candidate shares any static with the target
                        at any swept depth. Recorded as UNSUPPORTED, never as
                        evidence of absence.

Writes results/cause_classification.csv
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft, extract_static

DEPTHS = [1, 2, 3, 4]

def main():
    cases = {c["case_id"]: c for c in ft.load_cases()}
    direction = {r["case_id"]: r["direction"] for r in
                 csv.DictReader(open(os.path.join(ft.POC, "results", "alone.csv")))}
    out = []
    for depth in DEPTHS:
        extract_static.HOPS = depth
        cache = {}
        for cid, case in cases.items():
            p = os.path.join(ft.POC, "results", "scan_%s.csv" % cid)
            if not os.path.exists(p):
                continue
            scan = list(csv.DictReader(open(p)))
            rel = [r["candidate"] for r in scan if r["od_relevant"] == "YES"]
            if not rel:
                continue
            proj = case["project"]
            if proj not in cache:
                cache[proj] = extract_static.collect(proj)
            R = cache[proj]
            v = case["victim_spec"]
            vread = set(R.get(v, {}).get("reads", {}))

            shared_w, shared_t = set(), set()
            for c in rel:
                w = set(R.get(c, {}).get("writes", {}))
                t = w | set(R.get(c, {}).get("reads", {}))
                shared_w |= (w & vread)
                shared_t |= (t & vread)

            cause = "A_DIRECT_PUTSTATIC" if shared_w else \
                    "B_VIA_STATIC_REF"  if shared_t else "C_UNSUPPORTED"
            out.append({
                "case_id": cid, "project": proj, "direction": direction.get(cid, ""),
                "depth": depth, "cause": cause,
                "n_relevant": len(rel),
                "shared_written_fields": len(shared_w),
                "shared_touched_fields": len(shared_t),
                "example_field": sorted(shared_w or shared_t)[0] if (shared_w or shared_t) else "",
            })
    pth = os.path.join(ft.POC, "results", "cause_classification.csv")
    with open(pth, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    print("wrote", pth, "\n")
    print("%-7s %-6s %-20s %-9s %s" % ("case","depth","cause","shared","example field"))
    for r in out:
        print("%-7s %-6s %-20s %d/%-7d %s" % (r["case_id"], r["depth"], r["cause"],
              r["shared_written_fields"], r["shared_touched_fields"],
              r["example_field"][:64]))

if __name__ == "__main__":
    main()
