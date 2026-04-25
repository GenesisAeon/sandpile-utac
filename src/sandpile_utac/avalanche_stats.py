"""Power-law fitting and scaling analysis for avalanche statistics."""

from __future__ import annotations

import numpy as np


# ── Maximum-likelihood power-law estimator ────────────────────────────────────

def fit_power_law_mle(data: np.ndarray, x_min: float | None = None) -> tuple[float, float]:
    """
    Clauset–Shalizi–Newman MLE estimator for a discrete power-law exponent.

    Returns (tau, ks_statistic).  tau is NaN if fewer than 10 data points
    survive the x_min filter.
    """
    data = np.asarray(data, dtype=float)
    data = data[data > 0]
    if x_min is None:
        x_min = max(1.0, float(np.min(data)))
    data = data[data >= x_min]
    n = len(data)
    if n < 10:
        return float("nan"), float("nan")
    # Hill MLE for discrete power law (x_min continuous approximation)
    tau = 1.0 + n / np.sum(np.log(data / (x_min - 0.5)))
    ks = _ks_statistic(data, tau, x_min)
    return float(tau), float(ks)


def _ks_statistic(data: np.ndarray, tau: float, x_min: float) -> float:
    """KS distance between empirical CDF and fitted power-law CDF."""
    n = len(data)
    if n == 0:
        return float("nan")
    data_sorted = np.sort(data)
    ecdf = np.arange(1, n + 1) / n
    # Theoretical CDF: 1 - (x / x_min)^(1-tau)   [truncated]
    with np.errstate(invalid="ignore"):
        tcdf = 1.0 - (data_sorted / x_min) ** (1.0 - tau)
    tcdf = np.clip(tcdf, 0.0, 1.0)
    return float(np.max(np.abs(ecdf - tcdf)))


# ── Permutation entropy ───────────────────────────────────────────────────────

def permutation_entropy(series: np.ndarray, order: int = 3) -> float:
    """
    Normalised permutation entropy of a 1-D time series.

    Returns a value in [0, 1]:  0 = perfectly ordered, 1 = maximum disorder.
    """
    series = np.asarray(series, dtype=float)
    n = len(series)
    if n < order + 1:
        return 0.5  # insufficient data — return neutral value
    patterns: dict[tuple, int] = {}
    for i in range(n - order + 1):
        key = tuple(int(k) for k in np.argsort(series[i : i + order]))
        patterns[key] = patterns.get(key, 0) + 1
    counts = np.array(list(patterns.values()), dtype=float)
    counts /= counts.sum()
    entropy = -float(np.sum(counts * np.log(counts + 1e-14)))
    import math
    max_entropy = math.log(math.factorial(order))
    return entropy / max_entropy if max_entropy > 0 else 0.0


# ── Spatial correlation ───────────────────────────────────────────────────────

def spatial_autocorrelation(grid: np.ndarray) -> float:
    """
    Mean spatial autocorrelation at lag-1 in x and y directions.

    Returns a value in [0, 1]:  0 = uncorrelated,  1 = maximally correlated.
    """
    std = float(np.std(grid))
    if std < 1e-10:
        return 0.5
    g = (grid - np.mean(grid)) / std
    cx = float(np.mean(g[:-1, :] * g[1:, :]))
    cy = float(np.mean(g[:, :-1] * g[:, 1:]))
    raw = (cx + cy) / 2.0
    return float(np.clip((raw + 1.0) / 2.0, 0.0, 1.0))


# ── Proximity measure (how close tau is to theory) ───────────────────────────

def tau_proximity(tau_measured: float, tau_theory: float, scale: float = 0.3) -> float:
    """
    Soft proximity measure in [0, 1]:  1 when tau == tau_theory, decays
    with |tau - tau_theory| / scale.
    """
    if not np.isfinite(tau_measured):
        return 0.5
    return float(np.clip(np.exp(-abs(tau_measured - tau_theory) / scale), 0.0, 1.0))
