"""Random-order baseline (eval.baseline.run_random_order_baseline), run for real against
F1-F4, using the real runner.order_runner.OrderRunner -- not eval/tests/fake_runner.py.

One-off script, not part of the unit test suite (it shells out to real Maven/JDK and takes a
few minutes). Run manually:

    py eval/tools/run_baseline_real.py

For each case: runs [polluters..., victim] once in a fresh JVM to capture the real reference
failure signature (the same mechanism runner.diagnose uses, without the rest of its pipeline),
then calls run_random_order_baseline with 4 independent trials (base seeds 0/100/200/300,
max_runs=50 each) against a candidate pool of that case's polluter(s) plus the fixture's 4
benign noise tests (odfixture.MathUtilTest, odfixture.StringUtilTest -- see
fixtures/od-fixture/ground_truth.json's benign_noise_tests). Shuffling groups by class first
(eval/baseline.py, 2026-10-11): never an order JUnitCore could not actually run.

Writes eval/reports/baseline_results.json -- genuinely produced by calling the real pipeline,
not hand-written. See docs/07-Defense/claims-ledger.md (B11) and docs/evidence-m3.md.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.baseline import TestIdentifier, run_random_order_baseline
from runner.order_runner import OrderRunner, maven_test_classpath

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = REPO_ROOT / "fixtures" / "od-fixture"
REPORTS_DIR = REPO_ROOT / "eval" / "reports"

NOISE = [
    TestIdentifier("odfixture.MathUtilTest", "addsTwoNumbers"),
    TestIdentifier("odfixture.MathUtilTest", "squaresANumber"),
    TestIdentifier("odfixture.StringUtilTest", "reversesAString"),
    TestIdentifier("odfixture.StringUtilTest", "detectsPalindrome"),
]

BASE_SEEDS = (0, 100, 200, 300)
MAX_RUNS = 50

CASES = {
    "F1": dict(
        victim=TestIdentifier("odfixture.ConfigVictimTest", "expectsDefaultMode"),
        polluters=[TestIdentifier("odfixture.ConfigPolluterTest", "pollute")],
    ),
    "F2": dict(
        victim=TestIdentifier("odfixture.FeatureVictimTest", "expectsTurboDisabled"),
        polluters=[TestIdentifier("odfixture.FeaturePolluterTest", "enableTurbo")],
    ),
    "F3": dict(
        victim=TestIdentifier("odfixture.ToggleVictimTest", "expectsNotBothFlagsSet"),
        polluters=[
            TestIdentifier("odfixture.ToggleAPolluterTest", "setFlagA"),
            TestIdentifier("odfixture.ToggleBPolluterTest", "setFlagB"),
        ],
    ),
    "F4": dict(
        victim=TestIdentifier("odfixture.AlwaysEarlyVictimTest", "expectsLateFlagUnset"),
        polluters=[TestIdentifier("odfixture.ZzzLatePolluterTest", "setLateFlag")],
    ),
}


def run_case(runner: OrderRunner, case_id: str, victim, polluters) -> dict:
    print(f"=== {case_id}: capturing the real reference signature ({polluters} then {victim}) ===")
    outcomes = runner.run_ordered(polluters + [victim])
    victim_outcome = outcomes[victim]
    if victim_outcome.passed:
        raise RuntimeError(f"{case_id}: victim passed after its polluter(s) -- ground truth is wrong")
    reference_signature = victim_outcome.failure_signature
    print(f"=== {case_id}: reference signature = {reference_signature} ===")

    trials = []
    for base_seed in BASE_SEEDS:
        print(f"=== {case_id}: random-order baseline trial, base_seed={base_seed}, max_runs={MAX_RUNS} ===")
        result = run_random_order_baseline(
            runner=runner,
            victim=victim,
            candidates=list(polluters) + NOISE,
            reference_signature=reference_signature,
            max_runs=MAX_RUNS,
            base_seed=base_seed,
        )
        print(f"    found={result.found} runs_attempted={result.runs_attempted}")
        trials.append({
            "base_seed": base_seed,
            "found": result.found,
            "runs_attempted": result.runs_attempted,
        })

    return {
        "victim": victim.to_dict(),
        "polluters": [p.to_dict() for p in polluters],
        "candidate_pool_size": len(polluters) + 1 + len(NOISE),
        "max_runs_per_trial": MAX_RUNS,
        "trials": trials,
    }


if __name__ == "__main__":
    REPORTS_DIR.mkdir(exist_ok=True)
    classpath = maven_test_classpath(FIXTURE)
    runner = OrderRunner(classpath, working_dir=str(FIXTURE))

    results = {}
    for case_id, kwargs in CASES.items():
        results[case_id] = run_case(runner, case_id, **kwargs)

    (REPORTS_DIR / "baseline_results.json").write_text(
        json.dumps(results, indent=2) + "\n", encoding="utf-8"
    )

    print("\n=== SUMMARY (runs_attempted per trial, base seeds 0/100/200/300) ===")
    for case_id, data in results.items():
        runs = [t["runs_attempted"] for t in data["trials"]]
        print(f"{case_id}: {runs}")
