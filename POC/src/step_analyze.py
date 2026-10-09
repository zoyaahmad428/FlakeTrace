#!/usr/bin/env python3
"""Hours 5-6: baselines and the resource-ranked strategy, computed OFFLINE.

Per the frozen single-scan protocol nothing is re-executed here: every strategy
is replayed against the one exhaustive outcome table per case.

Strategies (all consume the identical candidate set):
  obo         - declared/original candidate order, one-by-one
  random_s<n> - uniformly shuffled, 5 fixed seeds
  resource    - descending |writes(c) INTERSECT reads(victim)|, ties by declared order

Primary cost: candidate confirmations before the first true OD-relevant test.
Each confirmation = one [candidate, victim] order = 2 test-method invocations.

Writes results/strategies.csv and results/ranking.csv
"""
import csv
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ft

SEEDS = [1, 2, 3, 4, 5]


def load_scan(cid):
    p = os.path.join(ft.POC, "results", "scan_%s.csv" % cid)
    if not os.path.exists(p):
        return None
    with open(p, newline="") as f:
        return list(csv.DictReader(f))


def overlap_score(res, cand, victim):
    """|writes(candidate) INTERSECT reads(victim)| -- the POC's ranking signal."""
    w = set(res.get(cand, {}).get("writes", {}))
    r = set(res.get(victim, {}).get("reads", {}))
    return len(w & r)


def cost_to_first(order, relevant):
    """Confirmations until the first OD-relevant candidate is confirmed."""
    for i, c in enumerate(order, 1):
        if c in relevant:
            return i
    return None


def main():
    directions = {r["case_id"]: r["direction"]
                  for r in csv.DictReader(open(os.path.join(ft.POC, "results",
                                                            "alone.csv")))}
    resources = {p: json.load(open(os.path.join(ft.POC, "results",
                                                "resources_%s.json" % p)))
                 for p in ("jsoniter", "fastjson")}

    strat_rows, rank_rows = [], []

    for case in ft.load_cases():
        cid = case["case_id"]
        scan = load_scan(cid)
        if not scan:
            continue
        declared = [r["candidate"] for r in scan]
        relevant = {r["candidate"] for r in scan if r["od_relevant"] == "YES"}
        res = resources[case["project"]]
        victim = case["victim_spec"]

        if not relevant:
            strat_rows.append({
                "case_id": cid, "direction": directions.get(cid, ""),
                "candidates": len(declared), "relevant": 0,
                "strategy": "-", "cost_to_first": "", "reproduced": "NO",
            })
            continue

        scored = {c: overlap_score(res, c, victim) for c in declared}
        ranked = sorted(declared, key=lambda c: (-scored[c], declared.index(c)))

        orders = {"obo": declared, "resource": ranked}
        for s in SEEDS:
            sh = declared[:]
            random.Random(s).shuffle(sh)
            orders["random_s%d" % s] = sh

        for name, order in orders.items():
            strat_rows.append({
                "case_id": cid, "direction": directions.get(cid, ""),
                "candidates": len(declared), "relevant": len(relevant),
                "strategy": name, "cost_to_first": cost_to_first(order, relevant),
                "reproduced": "YES",
            })

        # ranking quality of the resource signal
        pos = [i for i, c in enumerate(ranked, 1) if c in relevant]
        rank_rows.append({
            "case_id": cid, "candidates": len(declared), "relevant": len(relevant),
            "top1": "YES" if ranked[0] in relevant else "NO",
            "top5": "YES" if any(c in relevant for c in ranked[:5]) else "NO",
            "top20pct": "YES" if any(c in relevant for c in
                                     ranked[:max(1, len(ranked) // 5)]) else "NO",
            "first_rank": pos[0], "mrr": round(1.0 / pos[0], 4),
            "best_score": max(scored.values()),
            "score_of_first_relevant": scored[ranked[pos[0] - 1]],
            "relevant_with_nonzero_overlap":
                sum(1 for c in relevant if scored[c] > 0),
        })

    for name, rows in (("strategies", strat_rows), ("ranking", rank_rows)):
        if not rows:
            continue
        p = os.path.join(ft.POC, "results", "%s.csv" % name)
        with open(p, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print("wrote", p)

    # console summary
    print("\n%-7s %-8s %6s %5s | %5s %5s %7s" %
          ("case", "dir", "cands", "rel", "obo", "res", "rand_md"))
    for cid in sorted({r["case_id"] for r in strat_rows}):
        rs = [r for r in strat_rows if r["case_id"] == cid]
        if rs[0]["reproduced"] == "NO":
            print("%-7s %-8s %6s %5s | %s" % (cid, rs[0]["direction"],
                                              rs[0]["candidates"], 0,
                                              "NOT REPRODUCED"))
            continue
        g = {r["strategy"]: r["cost_to_first"] for r in rs}
        rnd = sorted(g["random_s%d" % s] for s in SEEDS)
        med = (rnd[2] + rnd[3]) / 2 if len(rnd) % 2 == 0 else rnd[len(rnd) // 2]
        print("%-7s %-8s %6s %5s | %5s %5s %7s" %
              (cid, rs[0]["direction"], rs[0]["candidates"], rs[0]["relevant"],
               g["obo"], g["resource"], med))


if __name__ == "__main__":
    main()
