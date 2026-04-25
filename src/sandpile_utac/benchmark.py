"""
Benchmark suite — validate simulated Γ / τ values against SANDPILE_TARGETS.

Reference: Phys. Rev. E 111, 024111 (2025, Feb 12).
"""

from __future__ import annotations

import numpy as np

from .avalanche_stats import fit_power_law_mle
from .btw import BTWSandpile
from .constants import SANDPILE_TARGETS, SIGMA
from .crep_spectrum import CREPSpectrumAtlas
from .manna import MannaSandpile


def _run_sandpile(
    model: str,
    L: int,
    n_grains: int,
    warmup: int,
    seed: int = 42,
) -> BTWSandpile:
    """Helper: run a sandpile and return it with accumulated history."""
    SandpileClass = BTWSandpile if model == "btw" else MannaSandpile
    sp = SandpileClass(L=L, seed=seed)
    for _ in range(warmup):
        sp.add_grain()
        sp.relax()
    for _ in range(n_grains):
        sp.add_grain()
        sp.relax()
    return sp


def run_benchmark(
    L: int = 64,
    n_grains: int = 100_000,
    warmup: int = 20_000,
    seed: int = 42,
    verbose: bool = False,
) -> dict:
    """
    Run BTW and Manna sandpiles and compare key observables against targets.

    Returns a dict with keys:
      measured  — {target_name: measured_value}
      passed    — {target_name: bool}
      all_passed — bool
    """
    # ── BTW run ───────────────────────────────────────────────────────────────
    btw = _run_sandpile("btw", L, n_grains, warmup, seed)
    btw_sizes = btw.recent_sizes()
    btw_durs = btw.recent_durations()
    btw_tau_s, _ = fit_power_law_mle(btw_sizes)
    btw_tau_d, _ = fit_power_law_mle(btw_durs)
    btw_eta = float(np.clip(btw.density() / btw.z_c, 1e-6, 1.0 - 1e-6))
    btw_gamma = float(np.arctanh(btw_eta) / SIGMA)

    # ── Manna run ─────────────────────────────────────────────────────────────
    manna = _run_sandpile("manna", L, n_grains, warmup, seed)
    manna_sizes = manna.recent_sizes()
    manna_tau_s, _ = fit_power_law_mle(manna_sizes)
    manna_eta = float(np.clip(manna.density() / manna.z_c, 1e-6, 1.0 - 1e-6))
    manna_gamma = float(np.arctanh(manna_eta) / SIGMA)

    # ── Spectrum monotonicity ─────────────────────────────────────────────────
    atlas = CREPSpectrumAtlas()
    spectrum_ok = atlas.is_monotonic()

    measured = {
        "btw_tau_size":         btw_tau_s,
        "btw_tau_duration":     btw_tau_d,
        "btw_critical_density": btw_eta,
        "manna_tau_size":       manna_tau_s,
        "gamma_btw":            btw_gamma,
        "gamma_manna":          manna_gamma,
        "spectrum_monotonic":   spectrum_ok,
    }

    passed: dict[str, bool] = {}
    for key, (target, rel_tol) in SANDPILE_TARGETS.items():
        val = measured[key]
        if rel_tol is None:
            passed[key] = bool(val) == bool(target)
        else:
            if isinstance(val, float) and np.isfinite(val):
                passed[key] = abs(val - target) <= rel_tol * abs(target) + 1e-9
            else:
                passed[key] = False

    if verbose:
        _print_report(measured, passed)

    return {
        "measured": measured,
        "passed": passed,
        "all_passed": all(passed.values()),
    }


def _print_report(measured: dict, passed: dict) -> None:
    print("\nSandpile-UTAC Benchmark Report")
    print("=" * 50)
    for key, (target, _tol) in SANDPILE_TARGETS.items():
        val = measured[key]
        ok = passed[key]
        mark = "✓" if ok else "✗"
        print(f"  {mark}  {key:<30} measured={val!s:<10}  target={target}")
    n_pass = sum(passed.values())
    n_total = len(passed)
    print(f"\n  {n_pass}/{n_total} targets passed")
