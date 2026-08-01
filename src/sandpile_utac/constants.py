"""Physical constants and benchmark targets for sandpile-utac (Package 22)."""

from __future__ import annotations

from typing import Any

# ── Global ──────────────────────────────────────────────────────────────────
SEED: int = 42
SIGMA: float = 2.2  # CREP coupling constant (GenesisAeon default)

# ── BTW model ────────────────────────────────────────────────────────────────
BTW_Z_C: int = 4  # toppling threshold
BTW_TAU_SIZE: float = 1.06  # avalanche-size power-law exponent (2D)
BTW_TAU_DURATION: float = 1.50  # avalanche-duration exponent
BTW_ETA_CRITICAL: float = 0.58  # ρ_c / z_c at criticality
BTW_GAMMA: float = 0.296  # CREP Γ  = arctanh(η_c) / σ

# ── Manna model ───────────────────────────────────────────────────────────────
MANNA_Z_C: int = 4  # toppling threshold (stochastic redistribution)
MANNA_TAU_SIZE: float = 1.28  # Manna universality class
MANNA_ETA_CRITICAL: float = 0.68  # ρ_c / z_c
MANNA_GAMMA: float = 0.376  # CREP Γ for Manna

# ── CREP Criticality Spectrum (all GenesisAeon packages) ────────────────────
CREP_SPECTRUM: dict[str, float] = {
    "Solar flares (P21)": 0.014,
    "Cygnus X-1 jets (P17)": 0.046,
    "Amazon forest (P19)": 0.116,
    "AMOC ocean (P18)": 0.251,
    "Neural criticality (P20)": 0.251,
    "BTW sandpile (P22)": 0.296,
    "Manna sandpile (P22)": 0.376,
    "ERA5 Arctic (P01)": 0.920,
}

# ── Benchmark targets  (value, relative_tolerance) ───────────────────────────
SANDPILE_TARGETS: dict[str, tuple[Any, Any]] = {
    "btw_tau_size": (1.06, 0.05),
    "btw_tau_duration": (1.50, 0.05),
    "btw_critical_density": (0.58, 0.03),
    "manna_tau_size": (1.28, 0.05),
    "gamma_btw": (0.296, 0.03),
    "gamma_manna": (0.376, 0.03),
    "spectrum_monotonic": (True, None),
}

# ── GenesisAeon package registry entry ───────────────────────────────────────
PACKAGE_REGISTRY: dict[int, dict[str, str]] = {
    22: {
        "name": "sandpile-utac",
        "class": "SandpileUTAC",
        "domain": "statistical-mechanics",
        "scale": "universal",
        "zenodo": "10.5281/zenodo.20842804",
        "reference": "10.1103/PhysRevE.111.024111",
    }
}

# ── Ethics-Gate threshold ─────────────────────────────────────────────────────
ETHICS_TENSION_THRESHOLD: float = 0.95  # block if H/K > this value
