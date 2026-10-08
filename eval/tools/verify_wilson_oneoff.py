"""One-off verification: compare eval.stats.wilson_interval against an
independent implementation (statsmodels.stats.proportion.proportion_confint,
method="wilson").

Not part of the test suite and not a project dependency -- statsmodels is
NOT installed for normal use. Run this manually, in a throwaway virtualenv,
whenever wilson_interval's formula changes and needs re-checking against an
outside source:

    python3 -m venv /tmp/ft_verify_venv
    source /tmp/ft_verify_venv/bin/activate
    pip install statsmodels
    python3 eval/tools/verify_wilson_oneoff.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from eval.stats import wilson_interval  # noqa: E402

try:
    from statsmodels.stats.proportion import proportion_confint
except ImportError:
    print("statsmodels is not installed; see module docstring for setup.")
    raise

CASES = [
    (17, 20, 0.95),
    (0, 20, 0.95),
    (20, 20, 0.95),
    (10, 20, 0.95),
    (1, 20, 0.95),
    (19, 20, 0.95),
    (10, 20, 0.90),
    (10, 20, 0.99),
    (0, 1, 0.95),
    (1, 1, 0.95),
    (3, 20, 0.95),
]

if __name__ == "__main__":
    max_diff = 0.0
    for successes, n, confidence in CASES:
        mine = wilson_interval(successes, n, confidence)
        theirs = proportion_confint(successes, n, alpha=1 - confidence, method="wilson")
        diff = max(abs(mine[0] - theirs[0]), abs(mine[1] - theirs[1]))
        max_diff = max(max_diff, diff)
        print(
            f"successes={successes:>2} n={n:>2} confidence={confidence:<5} "
            f"mine={mine}  statsmodels={theirs}  max_abs_diff={diff:.3e}"
        )
    print(f"\nOverall max absolute difference across {len(CASES)} cases: {max_diff:.3e}")
