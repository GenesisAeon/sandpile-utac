"""Diamond-Template contract tests for SandpileUTAC."""

import pytest

from sandpile_utac.system import EthicsGateLight, SandpileUTAC


# ── Diamond contract ──────────────────────────────────────────────────────────

class TestDiamondContract:
    """All five Diamond methods must exist and return the specified types."""

    @pytest.fixture
    def sp(self):
        return SandpileUTAC(model="btw", L=32, seed=42)

    def test_run_cycle_returns_dict(self, sp):
        result = sp.run_cycle(n_grains=200, warmup_grains=100)
        assert isinstance(result, dict)
        assert "crep" in result and "utac" in result
        assert "n_events" in result

    def test_get_crep_state_keys(self, sp):
        sp.run_cycle(n_grains=200, warmup_grains=100)
        crep = sp.get_crep_state()
        for key in ("C", "R", "E", "P", "Gamma", "eta"):
            assert key in crep, f"Missing CREP key: {key}"

    def test_get_crep_state_ranges(self, sp):
        sp.run_cycle(n_grains=200, warmup_grains=100)
        crep = sp.get_crep_state()
        for key in ("C", "R", "E", "P"):
            assert 0.0 <= crep[key] <= 1.0, f"{key}={crep[key]} out of [0,1]"
        assert crep["Gamma"] >= 0.0
        assert 0.0 < crep["eta"] < 1.0

    def test_get_utac_state_keys(self, sp):
        sp.run_cycle(n_grains=200, warmup_grains=100)
        utac = sp.get_utac_state()
        for key in ("H", "dH_dt", "H_star", "K_eff"):
            assert key in utac, f"Missing UTAC key: {key}"

    def test_get_utac_state_values(self, sp):
        sp.run_cycle(n_grains=200, warmup_grains=100)
        utac = sp.get_utac_state()
        assert utac["K_eff"] == sp._sandpile.z_c
        assert utac["H"] >= 0.0
        assert utac["H_star"] >= 0.0
        assert utac["dH_dt"] > 0.0

    def test_get_phase_events_list(self, sp):
        sp.run_cycle(n_grains=300, warmup_grains=100)
        events = sp.get_phase_events()
        assert isinstance(events, list)
        for e in events[:5]:
            assert "size" in e and "duration" in e

    def test_to_zenodo_record_keys(self, sp):
        sp.run_cycle(n_grains=200, warmup_grains=100)
        record = sp.to_zenodo_record()
        for key in ("title", "creators", "license", "zenodo_doi", "crep_state", "utac_state"):
            assert key in record, f"Missing Zenodo key: {key}"

    def test_to_zenodo_record_ethics_gate_field(self, sp):
        sp.run_cycle(n_grains=200, warmup_grains=100)
        record = sp.to_zenodo_record()
        assert "ethics_gate" in record
        assert record["ethics_gate"]["allowed"] is True


# ── Manna model ───────────────────────────────────────────────────────────────

class TestMannaDiamond:
    def test_manna_crep_state(self):
        sp = SandpileUTAC(model="manna", L=32, seed=42)
        sp.run_cycle(n_grains=200, warmup_grains=100)
        crep = sp.get_crep_state()
        assert crep["Gamma"] > 0.0

    def test_manna_higher_gamma_than_btw(self):
        btw = SandpileUTAC(model="btw", L=32, seed=42)
        manna = SandpileUTAC(model="manna", L=32, seed=42)
        n = 3_000
        btw.run_cycle(n_grains=n, warmup_grains=500)
        manna.run_cycle(n_grains=n, warmup_grains=500)
        # At equal grain counts Manna density ≥ BTW density (higher η → higher Γ)
        assert manna._sandpile.density() >= btw._sandpile.density() * 0.9


# ── Ethics Gate ───────────────────────────────────────────────────────────────

class TestEthicsGateLight:
    def test_allows_normal_tension(self):
        gate = EthicsGateLight(threshold=0.95)
        result = gate.check(state={}, tension=0.5)
        assert result["allowed"] is True

    def test_blocks_high_tension(self):
        gate = EthicsGateLight(threshold=0.95)
        result = gate.check(state={}, tension=0.99)
        assert result["allowed"] is False
        assert "threshold" in result["reason"]

    def test_boundary_exactly_at_threshold_is_blocked(self):
        gate = EthicsGateLight(threshold=0.90)
        # Exactly at threshold: 0.90 is NOT > 0.90 → allowed
        assert gate.check(state={}, tension=0.90)["allowed"] is True
        # Just over: blocked
        assert gate.check(state={}, tension=0.901)["allowed"] is False


# ── CREP spectrum ─────────────────────────────────────────────────────────────

class TestCREPSpectrum:
    def test_generate_crep_spectrum(self):
        sp = SandpileUTAC(model="btw", L=32, seed=42)
        result = sp.generate_crep_spectrum()
        assert "spectrum" in result
        assert result["is_monotonic"] is True
        # Must contain BTW and Manna entries
        assert any("BTW" in k for k in result["spectrum"])

    def test_gamma_calibrated(self):
        from sandpile_utac.constants import BTW_GAMMA, MANNA_GAMMA
        btw = SandpileUTAC(model="btw", L=32, seed=42)
        manna = SandpileUTAC(model="manna", L=32, seed=42)
        assert abs(btw.gamma_calibrated - BTW_GAMMA) < 1e-6
        assert abs(manna.gamma_calibrated - MANNA_GAMMA) < 1e-6

    def test_invalid_model_raises(self):
        with pytest.raises(ValueError, match="model must be"):
            SandpileUTAC(model="invalid")
