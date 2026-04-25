"""Manna stochastic sandpile — different universality class from BTW."""

from __future__ import annotations

import numpy as np

from .btw import BTWSandpile


class MannaSandpile(BTWSandpile):
    """
    Manna (1991) stochastic sandpile variant.

    Same toppling threshold z_c = 4 as BTW but each toppling grain is
    redistributed to a *randomly chosen* neighbour (with replacement).
    This stochasticity shifts the universality class:
      τ_size ≈ 1.28,  τ_duration ≈ 1.50   (vs BTW 1.06 / 1.50)
    and raises the critical density: η_Manna ≈ 0.68 > η_BTW ≈ 0.58.

    The higher η maps to Γ_Manna ≈ 0.376  (vs Γ_BTW ≈ 0.296).
    """

    z_c: int = 4

    # Neighbour offsets (dy, dx)
    _DIRS = np.array([[-1, 0], [1, 0], [0, -1], [0, 1]], dtype=np.int32)

    def topple(self) -> int:
        """Vectorised stochastic toppling step."""
        unstable = self.grid >= self.z_c
        n = int(np.sum(unstable))
        if n == 0:
            return 0
        self.grid[unstable] -= self.z_c

        positions = np.argwhere(unstable)  # shape (n_sites, 2)
        # For each of the z_c grains per site, scatter to a random neighbour.
        for _ in range(self.z_c):
            dir_idx = self.rng.integers(0, 4, size=len(positions))
            dy = self._DIRS[dir_idx, 0]
            dx = self._DIRS[dir_idx, 1]
            ny = positions[:, 0] + dy
            nx = positions[:, 1] + dx
            valid = (ny >= 0) & (ny < self.L) & (nx >= 0) & (nx < self.L)
            np.add.at(self.grid, (ny[valid], nx[valid]), 1)

        return n

    def __repr__(self) -> str:
        return (
            f"MannaSandpile(L={self.L}, density={self.density():.3f}, "
            f"grains={self._total_grains}, avalanches={self._total_avalanches})"
        )
