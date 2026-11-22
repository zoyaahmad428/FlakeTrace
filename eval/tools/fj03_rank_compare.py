"""ADR-014 evidence item 5: offline comparison of the product's rank_candidates against
POC/results/scan_FJ-03.csv's real, stored outcome -- no JVM runs, static analysis only.

One-off script, not part of the unit test suite (it needs a real fastjson checkout, built at
the pinned commit docs/05-Testing/real-case-protocol.md names, and takes a few minutes to warm
the analysis cache over 524 candidates). Run manually:

    py eval/tools/fj03_rank_compare.py <fastjson-checkout-dir>

Warms the AnalysisCache first, printing progress every 10 candidates (flushed immediately, so
progress can be read while this runs), then calls the real, unmodified rank_candidates against
the warm cache -- the scoring and sorting are 100% the product's own code, never reimplemented
here. See docs/evidence-m3.md's 2026-11-21 "W25 measurement" entry for the real result this
produced (zero evidence found; ranked position equals original position, 368 of 524)."""
import csv
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(REPO_ROOT))

from evidence.extract import AnalysisCache, DEFAULT_DEPTH, ExtractError, Project, rank_candidates  # noqa: E402

VICTIM = "com.alibaba.json.bvt.serializer.MaxBufSizeTest#test_max_buf"


def main(fastjson_dir: str) -> None:
    fj = Path(fastjson_dir)
    project = Project([str(fj / "target" / "classes"), str(fj / "target" / "test-classes")])

    with (REPO_ROOT / "POC" / "results" / "scan_FJ-03.csv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    candidates = [r["candidate"] for r in rows]
    relevant = {r["candidate"] for r in rows if r["od_relevant"] == "YES"}
    original_positions = {c: i + 1 for i, c in enumerate(candidates)}  # 1-indexed

    print(f"candidates: {len(candidates)}; relevant (od_relevant=YES): {len(relevant)}", flush=True)
    print(f"relevant candidates, original 1-indexed position: "
          f"{sorted(original_positions[c] for c in relevant)}", flush=True)

    cache = AnalysisCache()
    started = time.perf_counter()

    try:
        cache.get(project, VICTIM, DEFAULT_DEPTH)
    except ExtractError as error:
        print(f"VICTIM COULD NOT BE ANALYSED: {error}", flush=True)
        return
    print(f"progress: victim analysed, {time.perf_counter() - started:.1f}s elapsed", flush=True)

    for position, candidate in enumerate(candidates):
        try:
            cache.get(project, candidate, DEFAULT_DEPTH)
        except ExtractError:
            pass  # rank_candidates itself handles this candidate's ExtractError; just warming here
        if (position + 1) % 10 == 0 or position + 1 == len(candidates):
            print(f"progress: {position + 1}/{len(candidates)} candidates analysed, "
                  f"{time.perf_counter() - started:.1f}s elapsed", flush=True)

    print("progress: cache warm, calling the real rank_candidates", flush=True)
    ranked = rank_candidates(project, VICTIM, candidates, depth=DEFAULT_DEPTH, cache=cache)
    elapsed = time.perf_counter() - started

    ranked_positions = {rc.test: i + 1 for i, rc in enumerate(ranked)}  # 1-indexed
    unanalysable = sum(1 for rc in ranked if rc.note is not None)

    print(f"\nanalysis_seconds: {elapsed:.1f} (cache.analysed={cache.analysed}, "
          f"cache.seconds={cache.seconds:.1f})", flush=True)
    print(f"candidates that could not be analysed (rc.note is not None): {unanalysable}", flush=True)
    print(f"\n{'candidate':<70} {'original':>8} {'ranked':>8} {'score'}", flush=True)
    for c in sorted(relevant, key=lambda c: original_positions[c]):
        rc = next(rc for rc in ranked if rc.test == c)
        print(f"{c:<70} {original_positions[c]:>8} {ranked_positions[c]:>8} {rc.score} note={rc.note}", flush=True)

    first_relevant_original = min(original_positions[c] for c in relevant)
    first_relevant_ranked = min(ranked_positions[c] for c in relevant)
    print(f"\nFirst relevant candidate: original position {first_relevant_original} of "
          f"{len(candidates)}; ranked position {first_relevant_ranked} of {len(candidates)}.", flush=True)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(f"usage: py {sys.argv[0]} <fastjson-checkout-dir>")
    main(sys.argv[1])
