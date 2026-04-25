"""
SandpileUTAC — Diamond-Template interface for Package 22.

Diamond contract (mandatory):
  run_cycle()         → dict
  get_crep_state()    → dict   {C, R, E, P, Gamma}
  get_utac_state()    → dict   {H, dH_dt, H_star, K_eff}
  get_phase_events()  → list
  to_zenodo_record()  → dict

Extension methods:
  generate_crep_spectrum()       → dict
  finite_size_scaling(L_values)  → dict

Ethics-Gate Light (Phase H):
  Raises RuntimeError if the normalised density exceeds ETHICS_TENSION_THRESHOLD
  (default 0.95), preventing runaway near-saturation states.

Genesis-OS imports are gracefully stubbed when the package is absent.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from .btw import BTWSandpile
from .constants import (
    BTW_GAMMA,
    ETHICS_TENSION_THRESHOLD,
    MANNA_GAMMA,
    PACKAGE_REGISTRY,
    SIGMA,
)
from .crep_sandpile import CREPSandpile
from .crep_spectrum import CREPSpectrumAtlas
from .finite_size import FiniteSizeScaler
from .manna import MannaSandpile

# ── Optional genesis-os imports (stub when absent) ─────────────────────────

try:
    from genesis.core.crep import CREPTensor  # type: ignore[import]
    from genesis.core.lagrangian import UnifiedLagrangian  # type: ignore[import]
    from genesis.core.utac import UTAC_ODE, UTACParams  # type: ignore[import]
    from genesis.mirror.phase_loop import PhaseTransitionLoop  # type: ignore[import]
    _GENESIS_AVAILABLE = True
except ImportError:
    _GENESIS_AVAILABLE = False

    class UTAC_ODE:  # type: ignore[no-redef]
        """Stub UTAC_ODE."""
        def __init__(self, r: float, K: float, sigma: float) -> None:
            self.r, self.K, self.sigma = r, K, sigma
        def fixed_point(self, Gamma: float) -> float:
            return self.K * float(np.tanh(self.sigma * Gamma))

    class UTACParams:  # type: ignore[no-redef]
        def __init__(self, **kw: Any) -> None:
            self.__dict__.update(kw)

    class CREPTensor:  # type: ignore[no-redef]
        pass

    class PhaseTransitionLoop:  # type: ignore[no-redef]
        pass

    class UnifiedLagrangian:  # type: ignore[no-redef]
        pass


# ── Ethics Gate ────────────────────────────────────────────────────────────

class EthicsGateLight:
    """
    Lightweight safety gate (Phase H of GenesisAeon ethics protocol).

    Blocks simulation continuation when the system tension (H/K) exceeds a
    configurable threshold, preventing near-saturation states that could
    produce physically misleading results.
    """

    def __init__(self, threshold: float = ETHICS_TENSION_THRESHOLD) -> None:
        self.threshold = threshold

    def check(self, state: dict, tension: float) -> dict:
        if tension > self.threshold:
            return {
                "allowed": False,
                "reason": (
                    f"system tension η={tension:.4f} exceeds "
                    f"Ethics-Gate threshold {self.threshold}"
                ),
            }
        return {"allowed": True, "reason": "ok"}


# ── SandpileUTAC ─────────────────────────────────────────────────────────────

class SandpileUTAC:
    """
    BTW / Manna sandpile SOC modelled as a UTAC continuous phase transition.

    Physical mapping:
      H(t)   ← drop density ρ (grains / site) ∈ [0, z_c]
      K      ← z_c = toppling threshold  (4 for BTW, 4 for Manna)
      H*     ← critical density ρ_c ≈ η_c · z_c
      Γ(t)   ← arctanh(ρ / z_c) / σ   (from CREP tensor)
      r      ← grain addition rate  (1 / L²  per relaxation)
      σ      ← CREP coupling = 2.2

    At criticality:
      BTW:   Γ ≈ 0.296,  η_c ≈ 0.58
      Manna: Γ ≈ 0.376,  η_c ≈ 0.68

    Reference: Phys. Rev. E 111, 024111 (2025).
    """

    SIGMA: float = SIGMA

    def __init__(
        self,
        model: str = "btw",
        L: int = 128,
        seed: int = 42,
        max_history: int = 50_000,
    ) -> None:
        if model not in ("btw", "manna"):
            raise ValueError(f"model must be 'btw' or 'manna', got '{model}'")
        self.model = model
        self.L = L
        self.seed = seed

        SandpileClass = BTWSandpile if model == "btw" else MannaSandpile
        self._sandpile: BTWSandpile = SandpileClass(L=L, seed=seed, max_history=max_history)
        self._crep = CREPSandpile(sigma=self.SIGMA)
        self._ethics_gate = EthicsGateLight()
        self._utac_ode = UTAC_ODE(
            r=1.0 / (L * L),
            K=float(self._sandpile.z_c),
            sigma=self.SIGMA,
        )
        self._phase_events: list[dict] = []
        self._run_done: bool = False
        self._run_meta: dict = {}

    # ── Diamond interface ─────────────────────────────────────────────────────

    def run_cycle(self, n_grains: int = 50_000, warmup_grains: int = 10_000) -> dict:
        """
        Drive the sandpile for n_grains additions and collect phase events.

        warmup_grains: initial transient discarded before recording.
        """
        t0 = time.perf_counter()

        # Warmup
        for _ in range(warmup_grains):
            self._sandpile.add_grain()
            self._sandpile.relax()

        # Measurement
        for _ in range(n_grains):
            self._sandpile.add_grain()
            event = self._sandpile.relax()
            if event["size"] > 0:
                self._phase_events.append(event)

        # Mark done BEFORE calling get_crep_state to avoid mutual recursion
        self._run_done = True

        crep = self.get_crep_state()
        utac = self.get_utac_state()

        # Ethics-Gate Light (Phase H)
        tension = crep["eta"]
        ethics_result = self._ethics_gate.check(state=utac, tension=tension)
        if not ethics_result["allowed"]:
            raise RuntimeError(f"EthicsGate blocked: {ethics_result['reason']}")

        elapsed = time.perf_counter() - t0
        self._run_meta = {
            "n_grains": n_grains,
            "warmup_grains": warmup_grains,
            "elapsed_s": elapsed,
            "model": self.model,
            "L": self.L,
        }

        return {
            "crep":     crep,
            "utac":     utac,
            "n_events": len(self._phase_events),
            "meta":     self._run_meta,
        }

    def get_crep_state(self) -> dict:
        """Return {C, R, E, P, Gamma, eta} from the current sandpile state."""
        if not self._run_done:
            # Quick initialisation run so the interface is always callable
            self.run_cycle(n_grains=5_000, warmup_grains=2_000)
        return self._crep.compute(self._sandpile, self._phase_events)

    def get_utac_state(self) -> dict:
        """
        Return {H, dH_dt, H_star, K_eff} for the UTAC ODE representation.

        H      ← current density ρ
        dH_dt  ← approximate: 1 grain / (L² grains) per step
        H_star ← UTAC fixed point = K · tanh(σ · Γ)
        K_eff  ← toppling threshold z_c
        """
        crep = self._crep.compute(self._sandpile, self._phase_events)
        Gamma = crep["Gamma"]
        K_eff = float(self._sandpile.z_c)
        H = self._sandpile.density()
        H_star = self._utac_ode.fixed_point(Gamma)
        dH_dt = 1.0 / (self.L * self.L)
        return {
            "H":      H,
            "dH_dt":  dH_dt,
            "H_star": H_star,
            "K_eff":  K_eff,
        }

    def get_phase_events(self) -> list[dict]:
        """Return list of all recorded avalanche phase-transition events."""
        return list(self._phase_events)

    def to_zenodo_record(self) -> dict:
        """
        Serialise the current run state as a Zenodo-compatible metadata record.

        Includes CREP/UTAC state and Ethics-Gate result for provenance.
        """
        if not self._run_done:
            self.run_cycle(n_grains=5_000, warmup_grains=2_000)

        crep = self.get_crep_state()
        utac = self.get_utac_state()
        tension = crep["eta"]
        ethics = self._ethics_gate.check(state=utac, tension=tension)

        record: dict = {
            "title": f"sandpile-utac Package 22 — {self.model.upper()} L={self.L}",
            "description": (
                "BTW/Manna sandpile SOC as UTAC continuous phase transition. "
                "GenesisAeon Package 22. "
                "Reference: Phys. Rev. E 111, 024111 (2025)."
            ),
            "creators": [{"name": "Johann Römer", "affiliation": "MOR Research Collective"}],
            "license": "MIT",
            "zenodo_doi": PACKAGE_REGISTRY[22]["zenodo"],
            "package": PACKAGE_REGISTRY[22],
            "crep_state": crep,
            "utac_state": utac,
            "run_meta": self._run_meta,
            "ethics_gate": ethics,
            "n_phase_events": len(self._phase_events),
        }

        # Ethics-Gate Light (Phase H) — block export of unsafe states
        if not ethics["allowed"]:
            raise RuntimeError(f"EthicsGate blocked Zenodo export: {ethics['reason']}")

        return record

    # ── Extension methods ─────────────────────────────────────────────────────

    def generate_crep_spectrum(self) -> dict:
        """
        Produce the complete cross-domain CREP Criticality Spectrum.

        Attempts to import sibling packages (18-21); falls back to hardcoded
        calibrated values from the GenesisAeon whitepaper.

        Returns the spectrum dict and a table string.
        """
        atlas = CREPSpectrumAtlas()
        live_status = atlas.update_from_live()
        return {
            "spectrum": atlas.to_dict(),
            "is_monotonic": atlas.is_monotonic(),
            "universality_pairs": atlas.universality_pairs(),
            "live_status": live_status,
            "table": atlas.summary_table(),
        }

    def finite_size_scaling(
        self, L_values: list[int] | None = None
    ) -> dict:
        """
        Finite-size scaling analysis across multiple grid sizes.

        Default L_values = [32, 64, 128]; for production use [32,64,128,256,512].
        """
        if L_values is None:
            L_values = [32, 64, 128]
        scaler = FiniteSizeScaler(seed=self.seed)
        return scaler.run(model=self.model, L_values=L_values)

    # ── Convenience ──────────────────────────────────────────────────────────

    @property
    def gamma_calibrated(self) -> float:
        """Calibrated CREP Γ for this model (from spec constants)."""
        return BTW_GAMMA if self.model == "btw" else MANNA_GAMMA

    def __repr__(self) -> str:
        return (
            f"SandpileUTAC(model={self.model!r}, L={self.L}, "
            f"run_done={self._run_done})"
        )
