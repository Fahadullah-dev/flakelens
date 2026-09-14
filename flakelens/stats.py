"""Classifies a test's pass/fail history using a Wilson score interval.

A raw failure rate (k/n) is misleading at low sample counts: 0 failures in
2 runs looks identical to 0 failures in 200, but the true failure rate could
still be high in the first case. The Wilson interval accounts for that.
"""

import math
from dataclasses import dataclass

MIN_RUNS = 5
CONFIDENCE_Z = 1.96  # 95%


@dataclass
class Verdict:
    status: str  # flaky | stable-pass | broken | insufficient-data
    runs: int
    failures: int
    failure_rate: float
    ci_low: float
    ci_high: float


def wilson_interval(k, n, z=CONFIDENCE_Z):
    if n == 0:
        return 0.0, 1.0
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return max(0.0, center - margin), min(1.0, center + margin)


def classify(runs, failures):
    if runs < MIN_RUNS:
        lo, hi = wilson_interval(failures, runs)
        return Verdict("insufficient-data", runs, failures, failures / runs if runs else 0.0, lo, hi)

    lo, hi = wilson_interval(failures, runs)
    rate = failures / runs

    if failures == 0:
        return Verdict("stable-pass", runs, failures, rate, lo, hi)
    if failures == runs:
        return Verdict("broken", runs, failures, rate, lo, hi)
    return Verdict("flaky", runs, failures, rate, lo, hi)
