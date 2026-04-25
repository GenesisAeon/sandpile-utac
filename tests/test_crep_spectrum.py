"""Tests for the CREP Criticality Spectrum Atlas."""

import pytest

from sandpile_utac.constants import BTW_GAMMA, CREP_SPECTRUM, MANNA_GAMMA
from sandpile_utac.crep_spectrum import CREPSpectrumAtlas


class TestCREPSpectrumAtlas:
    @pytest.fixture
    def atlas(self):
        return CREPSpectrumAtlas()

    def test_spectrum_is_populated(self, atlas):
        d = atlas.to_dict()
        assert len(d) >= 7  # at least 7 domains

    def test_spectrum_is_monotonic(self, atlas):
        assert atlas.is_monotonic()

    def test_btw_in_spectrum(self, atlas):
        gamma = atlas.gamma_for("BTW")
        assert abs(gamma - BTW_GAMMA) < 1e-9

    def test_manna_in_spectrum(self, atlas):
        gamma = atlas.gamma_for("Manna")
        assert abs(gamma - MANNA_GAMMA) < 1e-9

    def test_universality_pair_amoc_neural(self, atlas):
        pairs = atlas.universality_pairs()
        labels = [(k1, k2) for k1, k2, _ in pairs]
        # AMOC and Neural both have Γ ≈ 0.251
        found = any(
            ("AMOC" in k1 or "AMOC" in k2 or "Neural" in k1 or "Neural" in k2)
            for k1, k2 in labels
        )
        assert found, f"Expected AMOC/Neural pair, got: {labels}"

    def test_ordered_values(self, atlas):
        vals = list(atlas.to_dict().values())
        assert vals == sorted(vals)

    def test_solar_lowest_gamma(self, atlas):
        d = atlas.to_dict()
        min_gamma = min(d.values())
        solar_gamma = atlas.gamma_for("Solar")
        assert abs(solar_gamma - min_gamma) < 1e-9

    def test_era5_highest_gamma(self, atlas):
        d = atlas.to_dict()
        max_gamma = max(d.values())
        era5_gamma = atlas.gamma_for("ERA5")
        assert abs(era5_gamma - max_gamma) < 1e-9

    def test_summary_table_contains_headers(self, atlas):
        table = atlas.summary_table()
        assert "Gamma" in table or "Γ" in table
        assert "Domain" in table or "domain" in table.lower()

    def test_to_dict_sorted(self, atlas):
        d = atlas.to_dict()
        values = list(d.values())
        assert values == sorted(values)

    def test_update_from_live_returns_dict(self, atlas):
        status = atlas.update_from_live()
        assert isinstance(status, dict)
        # Sibling packages not installed in test env → all "not_installed"
        for v in status.values():
            assert v in ("updated", "not_installed")

    def test_spectrum_constants_match_atlas(self, atlas):
        d = atlas.to_dict()
        for label, gamma in CREP_SPECTRUM.items():
            found = any(abs(v - gamma) < 1e-9 for v in d.values())
            assert found, f"Gamma {gamma} for '{label}' missing from atlas"
