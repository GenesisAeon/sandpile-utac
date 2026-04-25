"""
Benchmark / smoke tests — verify key observables are in the right ballpark.

These tests use small L and few grains so they run quickly.  The full benchmark
(L=64, 100k grains) is exposed via `sandpile-utac benchmark` CLI.
"""

import numpy as np

from sandpile_utac.avalanche_stats import fit_power_law_mle, permutation_entropy
from sandpile_utac.benchmark import run_benchmark
from sandpile_utac.btw import BTWSandpile
from sandpile_utac.constants import BTW_GAMMA, SIGMA
from sandpile_utac.crep_sandpile import CREPSandpile

# ── avalanche_stats helpers ───────────────────────────────────────────────────

class TestAvalancheStats:
    def test_power_law_mle_synthetic(self):
        rng = np.random.default_rng(42)
        tau_true = 1.5
        # Sample from discrete power law via inverse CDF approximation
        u = rng.uniform(size=2_000)
        x_min = 1.0
        data = x_min * (1.0 - u) ** (-1.0 / (tau_true - 1))
        data = np.maximum(data, x_min).astype(int)
        tau_est, ks = fit_power_law_mle(data.astype(float), x_min=1.0)
        assert np.isfinite(tau_est)
        assert abs(tau_est - tau_true) < 0.4  # generous tolerance for small sample

    def test_power_law_mle_nan_on_tiny_data(self):
        tau, ks = fit_power_law_mle(np.array([1.0, 2.0]))
        assert not np.isfinite(tau)

    def test_permutation_entropy_uniform(self):
        rng = np.random.default_rng(0)
        series = rng.uniform(size=1000)
        pe = permutation_entropy(series, order=3)
        assert 0.8 < pe <= 1.0  # should be near max for random

    def test_permutation_entropy_constant(self):
        series = np.ones(100)
        pe = permutation_entropy(series, order=3)
        assert pe <= 0.5  # ordered → low entropy

    def test_permutation_entropy_short_returns_neutral(self):
        pe = permutation_entropy(np.array([1.0, 2.0]), order=3)
        assert pe == 0.5


# ── CREP tensor ───────────────────────────────────────────────────────────────

class TestCREPSandpile:
    def test_crep_returns_correct_keys(self):
        sp = BTWSandpile(L=32, seed=42)
        for _ in range(500):
            sp.add_grain()
            sp.relax()
        crep = CREPSandpile()
        state = crep.compute(sp, sp.recent_events())
        for k in ("C", "R", "E", "P", "Gamma", "eta"):
            assert k in state

    def test_crep_gamma_positive(self):
        sp = BTWSandpile(L=32, seed=42)
        for _ in range(500):
            sp.add_grain()
            sp.relax()
        crep = CREPSandpile()
        state = crep.compute(sp, sp.recent_events())
        assert state["Gamma"] > 0.0

    def test_crep_components_in_range(self):
        sp = BTWSandpile(L=32, seed=42)
        for _ in range(500):
            sp.add_grain()
            sp.relax()
        crep = CREPSandpile()
        state = crep.compute(sp, sp.recent_events())
        for key in ("C", "R", "E", "P"):
            assert 0.0 <= state[key] <= 1.0, f"{key} out of range: {state[key]}"

    def test_gamma_calibration_formula(self):
        # Verify Γ = arctanh(η) / σ
        sp = BTWSandpile(L=32, seed=42)
        sp.seed_to_density(float(BTW_GAMMA) * SIGMA * 1.0)  # approx rho
        crep = CREPSandpile(sigma=SIGMA)
        state = crep.compute(sp, [])
        eta = sp.density() / sp.z_c
        expected_gamma = float(np.arctanh(np.clip(eta, 1e-6, 1-1e-6)) / SIGMA)
        assert abs(state["Gamma"] - expected_gamma) < 1e-9


# ── Benchmark smoke ───────────────────────────────────────────────────────────

class TestBenchmarkSmoke:
    def test_run_benchmark_returns_structure(self):
        result = run_benchmark(L=32, n_grains=3_000, warmup=500, seed=42, verbose=False)
        assert "measured" in result
        assert "passed" in result
        assert "all_passed" in result
        assert len(result["measured"]) == 7

    def test_benchmark_gamma_btw_positive(self):
        result = run_benchmark(L=32, n_grains=3_000, warmup=500, seed=42)
        assert result["measured"]["gamma_btw"] > 0.0

    def test_benchmark_gamma_ordering(self):
        result = run_benchmark(L=32, n_grains=3_000, warmup=500, seed=42)
        gamma_btw = result["measured"]["gamma_btw"]
        gamma_manna = result["measured"]["gamma_manna"]
        # Manna should have higher density → higher Γ
        assert gamma_manna >= gamma_btw * 0.8  # allow some margin at small L

    def test_benchmark_spectrum_monotonic(self):
        result = run_benchmark(L=32, n_grains=1_000, warmup=200, seed=42)
        assert result["measured"]["spectrum_monotonic"] is True
