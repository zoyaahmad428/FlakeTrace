"""Reproduction-confidence statistics for FlakeTrace evaluation.

Dependency-free (standard library only). Computes a Wilson score confidence
interval for a reproduction rate (successes out of n repeated runs) and
compares a sequence's reproduction rate against the victim-alone rate.
"""

import math
from dataclasses import dataclass
from typing import Tuple


def _norm_ppf(p: float) -> float:
    """Inverse CDF (quantile function) of the standard normal distribution.

    Implements Peter Acklam's rational approximation. Accurate to about
    1.15e-9 relative error over (0, 1), which is far more precision than
    this module needs for confidence levels like 0.90/0.95/0.99.
    """
    if not (0.0 < p < 1.0):
        raise ValueError(f"_norm_ppf requires 0 < p < 1, got {p!r}")

    # Coefficients for the rational approximation.
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]

    p_low = 0.02425
    p_high = 1 - p_low

    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    elif p <= p_high:
        q = p - 0.5
        r = q * q
        return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
               (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    else:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
                ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Wilson score confidence interval for a binomial proportion.

    Args:
        successes: number of successful outcomes (0 <= successes <= n).
        n: number of trials.
        confidence: two-sided confidence level, e.g. 0.95 for 95%.

    Returns:
        (lower, upper) bounds, each in [0, 1].

    Raises:
        ValueError: if n <= 0, successes is out of [0, n], or confidence is
            not strictly between 0 and 1.
    """
    if n <= 0:
        raise ValueError(f"wilson_interval requires n > 0, got n={n!r}")
    if not (0 <= successes <= n):
        raise ValueError(
            f"wilson_interval requires 0 <= successes <= n, got successes={successes!r}, n={n!r}"
        )
    if not (0.0 < confidence < 1.0):
        raise ValueError(f"wilson_interval requires 0 < confidence < 1, got confidence={confidence!r}")

    z = _norm_ppf(1 - (1 - confidence) / 2)
    z2 = z * z
    phat = successes / n

    denom = 1 + z2 / n
    center = phat + z2 / (2 * n)
    margin = z * math.sqrt(phat * (1 - phat) / n + z2 / (4 * n * n))

    lower = (center - margin) / denom
    upper = (center + margin) / denom

    # Guard against floating-point drift at the 0/n and n/n edges.
    lower = max(0.0, min(1.0, lower))
    upper = max(0.0, min(1.0, upper))
    return (lower, upper)


@dataclass(frozen=True)
class ReproductionComparison:
    """Structured comparison of a sequence's reproduction rate against the
    victim-alone (isolation) rate, each with its own Wilson interval."""

    sequence_successes: int
    sequence_n: int
    sequence_rate: float
    sequence_interval: Tuple[float, float]

    isolation_successes: int
    isolation_n: int
    isolation_rate: float
    isolation_interval: Tuple[float, float]

    confidence: float
    summary: str


def compare_sequence_to_isolation(
    sequence_successes: int,
    sequence_n: int,
    isolation_successes: int,
    isolation_n: int,
    confidence: float = 0.95,
) -> ReproductionComparison:
    """Compare a sequence's reproduction rate against the victim-alone rate.

    "Successes" on each side means "the victim's reference failure signature
    was observed." Both counts get their own Wilson interval at the given
    confidence level; this function does not decide VERIFIED/CANDIDATE/
    UNRESOLVED on its own, it only produces the structured record that the
    outcome logic (Phase 3) consumes.
    """
    seq_lower, seq_upper = wilson_interval(sequence_successes, sequence_n, confidence)
    iso_lower, iso_upper = wilson_interval(isolation_successes, isolation_n, confidence)

    summary = (
        f"sequence reproduced {sequence_successes}/{sequence_n}, "
        f"victim alone {isolation_successes}/{isolation_n}"
    )

    return ReproductionComparison(
        sequence_successes=sequence_successes,
        sequence_n=sequence_n,
        sequence_rate=sequence_successes / sequence_n,
        sequence_interval=(seq_lower, seq_upper),
        isolation_successes=isolation_successes,
        isolation_n=isolation_n,
        isolation_rate=isolation_successes / isolation_n,
        isolation_interval=(iso_lower, iso_upper),
        confidence=confidence,
        summary=summary,
    )
