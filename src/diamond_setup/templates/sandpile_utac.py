"""sandpile-utac template — GenesisAeon Package 22 Diamond scaffold."""

import copy

from diamond_setup._types import TemplateDict

from .genesis import TEMPLATE as GENESIS_TEMPLATE

_extra_files: dict[str, str] = {
    # ── core physics modules ─────────────────────────────────────────────────
    "src/${name_snake}/constants.py": """\
\"\"\"Physical constants for ${name}.\"\"\"
from __future__ import annotations

SEED: int = 42
SIGMA: float = 2.2
Z_C: int = 4
ETA_CRITICAL: float = 0.58
GAMMA_CRITICAL: float = 0.296
""",
    "src/${name_snake}/btw.py": """\
\"\"\"BTW 2-D sandpile — numpy-vectorised parallel-update implementation.\"\"\"
from __future__ import annotations
from collections import deque
import numpy as np


class BTWSandpile:
    z_c: int = 4

    def __init__(self, L: int = 128, seed: int = 42) -> None:
        self.L = L
        self.rng = np.random.default_rng(seed)
        self.grid: np.ndarray = np.zeros((L, L), dtype=np.int32)
        self._recent_events: deque[dict] = deque(maxlen=50_000)

    def add_grain(self) -> None:
        x, y = self.rng.integers(0, self.L, size=2)
        self.grid[int(x), int(y)] += 1

    def relax(self) -> dict:
        size, duration = 0, 0
        while True:
            n = self.topple()
            if n == 0:
                break
            size += n
            duration += 1
        event = {"size": size, "duration": duration}
        if size > 0:
            self._recent_events.append(event)
        return event

    def topple(self) -> int:
        unstable = self.grid >= self.z_c
        n = int(np.sum(unstable))
        if n == 0:
            return 0
        self.grid[unstable] -= self.z_c
        gain = np.zeros_like(self.grid)
        gain[1:, :]  += unstable[:-1, :]
        gain[:-1, :] += unstable[1:, :]
        gain[:, 1:]  += unstable[:, :-1]
        gain[:, :-1] += unstable[:, 1:]
        self.grid += gain
        return n

    def density(self) -> float:
        return float(np.sum(self.grid)) / (self.L * self.L)
""",
    "src/${name_snake}/system.py": """\
\"\"\"${name} — Diamond-Template interface.\"\"\"
from __future__ import annotations
import numpy as np
from .btw import BTWSandpile
from .constants import SIGMA


class ${name_snake.replace('_', ' ').title().replace(' ', '')}UTAC:
    \"\"\"Diamond-Template interface for ${name}.\"\"\"

    SIGMA = SIGMA

    def __init__(self, L: int = 128, seed: int = 42) -> None:
        self.L = L
        self._sandpile = BTWSandpile(L=L, seed=seed)
        self._phase_events: list[dict] = []
        self._run_done = False

    def run_cycle(self, n_grains: int = 50_000) -> dict:
        for _ in range(n_grains):
            self._sandpile.add_grain()
            event = self._sandpile.relax()
            if event["size"] > 0:
                self._phase_events.append(event)
        self._run_done = True
        return {"crep": self.get_crep_state(), "utac": self.get_utac_state()}

    def get_crep_state(self) -> dict:
        eta = float(np.clip(self._sandpile.density() / self._sandpile.z_c, 1e-6, 1-1e-6))
        Gamma = float(np.arctanh(eta) / self.SIGMA)
        return {"C": 0.5, "R": 0.5, "E": 0.5, "P": 0.5, "Gamma": Gamma}

    def get_utac_state(self) -> dict:
        K = float(self._sandpile.z_c)
        Gamma = self.get_crep_state()["Gamma"]
        H = self._sandpile.density()
        return {"H": H, "dH_dt": 1.0/(self.L*self.L),
                "H_star": K*float(np.tanh(self.SIGMA*Gamma)), "K_eff": K}

    def get_phase_events(self) -> list[dict]:
        return list(self._phase_events)

    def to_zenodo_record(self) -> dict:
        return {
            "title": "${name}",
            "crep_state": self.get_crep_state(),
            "utac_state": self.get_utac_state(),
        }
""",
    # ── tests ─────────────────────────────────────────────────────────────────
    "tests/test_diamond_interface.py": """\
\"\"\"Diamond-Template contract tests for ${name}.\"\"\"
import pytest


def test_diamond_interface():
    from ${name_snake}.system import *  # noqa: F401, F403
    # Import smoke test — all five Diamond methods must exist
    import importlib
    mod = importlib.import_module("${name_snake}.system")
    cls = [v for v in vars(mod).values()
           if isinstance(v, type) and hasattr(v, "run_cycle")]
    assert cls, "No Diamond class found"
    inst = cls[0]()
    for method in ("run_cycle", "get_crep_state", "get_utac_state",
                   "get_phase_events", "to_zenodo_record"):
        assert callable(getattr(inst, method, None)), f"Missing {method}"
""",
    # ── data directory ────────────────────────────────────────────────────────
    "data/.gitkeep": "",
    "notebooks/.gitkeep": "",
}

_sandpile_utac: TemplateDict = copy.deepcopy(GENESIS_TEMPLATE)
_sandpile_utac["name"] = "sandpile-utac"
_sandpile_utac["description"] = (
    "GenesisAeon Package 22 — BTW/Manna sandpile SOC as UTAC phase transition "
    "(Diamond-Template scaffold)"
)
_sandpile_utac["variables"] = GENESIS_TEMPLATE["variables"] + ["domain"]
_sandpile_utac["defaults"] = {
    **GENESIS_TEMPLATE["defaults"],
    "domain": "statistical-mechanics",
    "metrics": "crep,gamma,tau",
}
_sandpile_utac["files"] = {**GENESIS_TEMPLATE["files"], **_extra_files}

TEMPLATE: TemplateDict = _sandpile_utac
