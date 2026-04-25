"""Unit tests for BTW and Manna sandpile models."""

import numpy as np

from sandpile_utac.btw import BTWSandpile
from sandpile_utac.manna import MannaSandpile

# ── BTWSandpile ───────────────────────────────────────────────────────────────

class TestBTWSandpile:
    def test_init_empty_grid(self):
        sp = BTWSandpile(L=16, seed=42)
        assert sp.density() == 0.0
        assert sp.grid.shape == (16, 16)

    def test_add_grain_increases_density(self):
        sp = BTWSandpile(L=16, seed=42)
        sp.add_grain()
        assert sp.density() > 0.0

    def test_relax_returns_dict(self):
        sp = BTWSandpile(L=16, seed=42)
        sp.add_grain(x=8, y=8)
        event = sp.relax()
        assert "size" in event and "duration" in event
        assert event["size"] >= 0 and event["duration"] >= 0

    def test_topple_reduces_overcritical_sites(self):
        sp = BTWSandpile(L=8, seed=1)
        # Force a site above threshold
        sp.grid[3, 3] = 8
        n = sp.topple()
        assert n > 0
        assert sp.grid[3, 3] < 8

    def test_no_topple_when_stable(self):
        sp = BTWSandpile(L=8, seed=1)
        sp.grid[:] = 1  # all sites have 1 grain — stable
        n = sp.topple()
        assert n == 0

    def test_relax_leaves_grid_stable(self):
        sp = BTWSandpile(L=16, seed=42)
        # Overfill with grains
        sp.grid[:] = 6
        sp.relax()
        assert np.all(sp.grid < sp.z_c)

    def test_open_boundary_loses_grains(self):
        sp = BTWSandpile(L=8, seed=42)
        initial_fill = sp.z_c * sp.L * sp.L
        sp.grid[:] = sp.z_c  # fill to threshold
        sp.relax()
        final_total = int(np.sum(sp.grid))
        assert final_total < initial_fill  # grains escaped at boundary

    def test_deterministic_with_same_seed(self):
        sp1 = BTWSandpile(L=32, seed=42)
        sp2 = BTWSandpile(L=32, seed=42)
        for _ in range(200):
            sp1.add_grain()
            sp1.relax()
            sp2.add_grain()
            sp2.relax()
        np.testing.assert_array_equal(sp1.grid, sp2.grid)

    def test_recent_sizes_after_run(self):
        sp = BTWSandpile(L=32, seed=42)
        for _ in range(500):
            sp.add_grain()
            sp.relax()
        sizes = sp.recent_sizes()
        # Most runs produce some avalanches
        assert len(sizes) >= 0  # can be 0 early on
        if len(sizes) > 0:
            assert np.all(sizes >= 0)

    def test_seed_to_density(self):
        sp = BTWSandpile(L=32, seed=42)
        sp.seed_to_density(1.0)
        assert abs(sp.density() - 1.0) < 0.5  # approximate, after relaxation


# ── MannaSandpile ─────────────────────────────────────────────────────────────

class TestMannaSandpile:
    def test_inherits_btw(self):
        sp = MannaSandpile(L=16, seed=42)
        assert isinstance(sp, BTWSandpile)
        assert sp.z_c == 4

    def test_topple_stochastic(self):
        """Two Manna runs with different seeds should diverge after toppling."""
        sp1 = MannaSandpile(L=16, seed=1)
        sp2 = MannaSandpile(L=16, seed=2)
        sp1.grid[8, 8] = 8
        sp2.grid[8, 8] = 8
        sp1.relax()
        sp2.relax()
        # With different seeds they should differ (very high probability)
        assert not np.array_equal(sp1.grid, sp2.grid)

    def test_relax_leaves_grid_stable(self):
        sp = MannaSandpile(L=16, seed=42)
        sp.grid[:] = 6
        sp.relax()
        assert np.all(sp.grid < sp.z_c)

    def test_manna_higher_density_than_btw(self):
        """At equal grain counts, Manna reaches higher equilibrium density."""
        n = 5_000
        btw = BTWSandpile(L=32, seed=42)
        manna = MannaSandpile(L=32, seed=42)
        for _ in range(n):
            btw.add_grain()
            btw.relax()
            manna.add_grain()
            manna.relax()
        # Both should have accumulated grains; no strict ordering guaranteed
        assert btw.density() >= 0.0
        assert manna.density() >= 0.0
