"""Sandpile-specific CREP tensor — maps simulation state to {C, R, E, P, Gamma}."""

from __future__ import annotations

import numpy as np

from .avalanche_stats import (
    fit_power_law_mle,
    permutation_entropy,
    spatial_autocorrelation,
    tau_proximity,
)
from .btw import BTWSandpile
from .constants import BTW_TAU_SIZE, SIGMA


class CREPSandpile:
    """
    Compute the CREP tensor for a sandpile system.

    The four diagnostic components each live in [0, 1]:

      C  — spatial autocorrelation of the grid height field (coherence)
      R  — proximity of the measured size-exponent τ to its theoretical value
           (resonance with the SOC power-law)
      E  — largest recent avalanche / L²   (supra-additive emergence)
      P  — normalised permutation entropy of the avalanche-size time series

    The primary CREP parameter Γ is derived directly from the physics:

        Γ = arctanh(η) / σ ,    η = ρ / z_c  (normalised density)

    At criticality η → η_c ≈ 0.58  →  Γ_BTW ≈ 0.296.
    """

    def __init__(
        self,
        sigma: float = SIGMA,
        tau_theory: float = BTW_TAU_SIZE,
        history_window: int = 10_000,
    ) -> None:
        self.sigma = sigma
        self.tau_theory = tau_theory
        self.history_window = history_window

    # ── main entry point ──────────────────────────────────────────────────────

    def compute(self, sandpile: BTWSandpile, avalanche_history: list[dict]) -> dict:
        """Return full CREP state dict for the given sandpile and history."""
        H = sandpile.density()
        K = float(sandpile.z_c)
        eta = float(np.clip(H / K, 1e-6, 1.0 - 1e-6))
        Gamma = float(np.arctanh(eta) / self.sigma)

        # Use most recent window of events
        recent = avalanche_history[-self.history_window :]
        sizes = np.array([e["size"] for e in recent if e["size"] > 0], dtype=np.int64)

        C = self._correlation(sandpile)
        R = self._resonance(sizes)
        E = self._emergence(sizes, sandpile.L)
        P = self._entropy(sizes)

        return {
            "C": C,
            "R": R,
            "E": E,
            "P": P,
            "Gamma": Gamma,
            "eta": eta,
        }

    # ── CREP components ───────────────────────────────────────────────────────

    def _correlation(self, sandpile: BTWSandpile) -> float:
        """C: spatial autocorrelation of grid height at lag 1."""
        return spatial_autocorrelation(sandpile.grid)

    def _resonance(self, sizes: np.ndarray) -> float:
        """R: proximity of measured τ to theoretical τ_SOC."""
        if len(sizes) < 50:
            return 0.5
        tau, _ = fit_power_law_mle(sizes)
        return tau_proximity(tau, self.tau_theory)

    def _emergence(self, sizes: np.ndarray, L: int) -> float:
        """E: largest avalanche normalised to system size L²."""
        if len(sizes) == 0:
            return 0.0
        return float(np.clip(float(np.max(sizes)) / (L * L), 0.0, 1.0))

    def _entropy(self, sizes: np.ndarray) -> float:
        """P: normalised permutation entropy of avalanche-size series."""
        if len(sizes) < 6:
            return 0.5
        return permutation_entropy(sizes, order=3)
