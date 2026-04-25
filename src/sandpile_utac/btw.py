"""BTW 2-D sandpile — numpy-vectorised parallel-update implementation."""

from __future__ import annotations

from collections import deque

import numpy as np


class BTWSandpile:
    """
    2-D Bak-Tang-Wiesenfeld sandpile (numpy-optimised).

    Grid L×L, toppling threshold z_c = 4 (open boundary: grains that leave
    the grid are lost).  Each parallel toppling step is a single numpy pass.

    Drop density  ρ = total_grains / L²  maps to the UTAC state variable H(t),
    normalised by K = z_c.  At the self-organised critical density ρ_c ≈ 0.58·z_c
    the avalanche-size distribution follows a power law with exponent τ ≈ 1.06.
    """

    z_c: int = 4  # subclasses may override

    def __init__(self, L: int = 128, seed: int = 42, max_history: int = 50_000) -> None:
        self.L = L
        self.rng = np.random.default_rng(seed)
        self.grid: np.ndarray = np.zeros((L, L), dtype=np.int32)
        self._recent_events: deque[dict] = deque(maxlen=max_history)
        self._total_grains: int = 0
        self._total_avalanches: int = 0

    # ── grain addition ───────────────────────────────────────────────────────

    def add_grain(self, x: int | None = None, y: int | None = None) -> None:
        """Add one grain at (x, y); random site if not specified."""
        if x is None:
            x = int(self.rng.integers(0, self.L))
        if y is None:
            y = int(self.rng.integers(0, self.L))
        self.grid[x, y] += 1
        self._total_grains += 1

    # ── relaxation ───────────────────────────────────────────────────────────

    def relax(self) -> dict:
        """Relax to stability, collecting avalanche statistics."""
        size = 0       # total site-topplings
        duration = 0   # number of parallel steps
        while True:
            n = self.topple()
            if n == 0:
                break
            size += n
            duration += 1
        event: dict = {"size": size, "duration": duration}
        if size > 0:
            self._recent_events.append(event)
            self._total_avalanches += 1
        return event

    def topple(self) -> int:
        """One vectorised parallel toppling step. Returns sites that toppled."""
        unstable = self.grid >= self.z_c
        n = int(np.sum(unstable))
        if n == 0:
            return 0
        self.grid[unstable] -= self.z_c
        # Scatter gains to the four neighbours (open boundary = grains that
        # leave the grid are simply lost, so no wrapping).
        gain = np.zeros_like(self.grid)
        gain[1:, :]  += unstable[:-1, :]  # row below receives from row above
        gain[:-1, :] += unstable[1:, :]   # row above receives from row below
        gain[:, 1:]  += unstable[:, :-1]  # col right receives from col left
        gain[:, :-1] += unstable[:, 1:]   # col left receives from col right
        self.grid += gain
        return n

    # ── observables ─────────────────────────────────────────────────────────

    def density(self) -> float:
        """Average particles per site  ρ = Σgrid / L²."""
        return float(np.sum(self.grid)) / (self.L * self.L)

    def recent_events(self) -> list[dict]:
        """Return copy of recent avalanche event list."""
        return list(self._recent_events)

    def recent_sizes(self) -> np.ndarray:
        """Avalanche sizes from recent history."""
        return np.array([e["size"] for e in self._recent_events if e["size"] > 0],
                        dtype=np.int64)

    def recent_durations(self) -> np.ndarray:
        """Avalanche durations from recent history."""
        return np.array([e["duration"] for e in self._recent_events if e["duration"] > 0],
                        dtype=np.int64)

    # ── bulk seeding (fast fill to target density) ───────────────────────────

    def seed_to_density(self, target_rho: float, relax_each: bool = False) -> None:
        """Fill grid to approximately target_rho grains / site."""
        target_total = int(target_rho * self.L * self.L)
        current = int(np.sum(self.grid))
        to_add = max(0, target_total - current)
        xs = self.rng.integers(0, self.L, size=to_add)
        ys = self.rng.integers(0, self.L, size=to_add)
        for x, y in zip(xs, ys):
            self.grid[int(x), int(y)] += 1
            self._total_grains += 1
            if relax_each:
                self.relax()
        if not relax_each:
            # single bulk relax
            while np.any(self.grid >= self.z_c):
                self.topple()

    def __repr__(self) -> str:
        return (
            f"BTWSandpile(L={self.L}, density={self.density():.3f}, "
            f"grains={self._total_grains}, avalanches={self._total_avalanches})"
        )
