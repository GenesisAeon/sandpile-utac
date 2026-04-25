"""
Drop-density sweep → order parameter (activity) as continuous phase transition.

Implements the framework from Phys. Rev. E 111, 024111 (2025):
the drop density ρ is a tunable control variable, and the time-averaged
activity a(ρ) = ⟨topplings per step⟩ serves as the order parameter.
a → 0 for ρ < ρ_c  (subcritical absorbing phase)
a > 0 for ρ > ρ_c  (active/supercritical phase)
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .btw import BTWSandpile
from .manna import MannaSandpile


class PhaseDiagramScanner:
    """
    Scan the order parameter as a function of drop density.

    For each sampled density value, the sandpile is initialised to that
    density, relaxed, and the activity (toppling events per added grain) is
    measured over a short steady-state window.
    """

    def __init__(
        self,
        L: int = 64,
        seed: int = 42,
        measure_grains: int = 2_000,
    ) -> None:
        self.L = L
        self.seed = seed
        self.measure_grains = measure_grains

    def scan(
        self,
        model: str = "btw",
        rho_min: float = 0.1,
        rho_max: float = 0.95,
        n_points: int = 40,
    ) -> dict[str, Any]:
        """
        Return {rho_values, activity, critical_density_estimate}.

        rho_values  — array of ρ / z_c  (normalised density η)
        activity    — mean toppling activity per grain at each η
        """
        if model not in ("btw", "manna"):
            raise ValueError(f"model must be 'btw' or 'manna', got '{model!r}'")
        etas = np.linspace(rho_min, rho_max, n_points)
        activities = np.zeros(n_points)

        SandpileClass = BTWSandpile if model == "btw" else MannaSandpile

        for i, eta in enumerate(etas):
            sp = SandpileClass(L=self.L, seed=self.seed + i)
            rho = eta * sp.z_c
            sp.seed_to_density(rho, relax_each=False)
            # Measure steady-state activity
            total_topplings = 0
            for _ in range(self.measure_grains):
                sp.add_grain()
                event = sp.relax()
                total_topplings += event["size"]
            activities[i] = total_topplings / self.measure_grains

        # Estimate critical density as the inflection point of activity(η)
        eta_c = self._estimate_critical_eta(etas, activities)

        return {
            "rho_values": etas,
            "activity": activities,
            "critical_density_estimate": eta_c,
            "model": model,
            "L": self.L,
        }

    # ── helpers ───────────────────────────────────────────────────────────────

    def _estimate_critical_eta(self, etas: np.ndarray, activity: np.ndarray) -> float:
        """Estimate η_c as the η where d²activity/dη² is maximised."""
        if len(activity) < 4:
            return float(np.median(etas))
        d2 = np.gradient(np.gradient(activity, etas), etas)
        idx = int(np.argmax(np.abs(d2)))
        return float(etas[idx])
