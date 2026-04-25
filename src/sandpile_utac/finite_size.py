"""
Finite-size scaling analysis for the BTW / Manna sandpile.

Runs simulations at multiple system sizes L and extracts the critical
exponents via data collapse: ρ_c(L) = ρ_c(∞) + a · L^(-1/ν).
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .avalanche_stats import fit_power_law_mle
from .btw import BTWSandpile
from .constants import SIGMA
from .manna import MannaSandpile


class FiniteSizeScaler:
    """Extract critical exponents from multi-scale sandpile runs."""

    def __init__(
        self,
        seed: int = 42,
        n_grains_per_size: int = 20_000,
        warmup_grains: int = 5_000,
    ) -> None:
        self.seed = seed
        self.n_grains = n_grains_per_size
        self.warmup = warmup_grains

    def run(
        self,
        model: str = "btw",
        L_values: list[int] | None = None,
    ) -> dict[str, Any]:
        """
        Run sandpiles for each L and return per-size statistics.

        Returns dict with keys:
          L_values, tau_size, tau_duration, gamma_values,
          critical_density, exponent_nu_estimate
        """
        if L_values is None:
            L_values = [32, 64, 128]

        SandpileClass = BTWSandpile if model == "btw" else MannaSandpile
        taus_size: list[float] = []
        taus_dur: list[float] = []
        gammas: list[float] = []
        rho_cs: list[float] = []

        for L in L_values:
            sp = SandpileClass(L=L, seed=self.seed)
            # Warmup to near-critical state
            for _ in range(self.warmup):
                sp.add_grain()
                sp.relax()
            # Measurement
            for _ in range(self.n_grains):
                sp.add_grain()
                sp.relax()

            sizes = sp.recent_sizes()
            durs = sp.recent_durations()

            tau_s, _ = fit_power_law_mle(sizes)
            tau_d, _ = fit_power_law_mle(durs)

            eta = np.clip(sp.density() / sp.z_c, 1e-6, 1.0 - 1e-6)
            gamma = float(np.arctanh(eta) / SIGMA)

            taus_size.append(float(tau_s))
            taus_dur.append(float(tau_d))
            gammas.append(gamma)
            rho_cs.append(sp.density() / sp.z_c)

        nu_estimate = self._estimate_nu(np.array(L_values), np.array(rho_cs))

        return {
            "L_values": L_values,
            "tau_size": taus_size,
            "tau_duration": taus_dur,
            "gamma_values": gammas,
            "critical_density": rho_cs,
            "exponent_nu_estimate": nu_estimate,
            "model": model,
        }

    # ── helpers ───────────────────────────────────────────────────────────────

    def _estimate_nu(self, Ls: np.ndarray, rho_cs: np.ndarray) -> float:
        """Fit ρ_c(L) = ρ_∞ + a·L^(-1/ν) via log-linear regression."""
        if len(Ls) < 3:
            return float("nan")
        log_L = np.log(Ls.astype(float))
        log_drho = np.log(np.abs(rho_cs - np.mean(rho_cs)) + 1e-8)
        if np.std(log_drho) < 1e-8:
            return float("nan")
        coeffs = np.polyfit(log_L, log_drho, 1)
        slope = float(coeffs[0])  # = -1/ν
        if abs(slope) < 1e-6:
            return float("nan")
        return float(-1.0 / slope)
