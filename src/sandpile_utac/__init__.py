"""
sandpile-utac — BTW/Manna Sandpile SOC as UTAC Continuous Phase Transition.

GenesisAeon Package 22  ·  MIT licence  ·  seed=42
Reference: Phys. Rev. E 111, 024111 (2025)  DOI: 10.1103/PhysRevE.111.024111
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Johann Römer / MOR Research Collective"
__license__ = "MIT"

from .btw import BTWSandpile
from .crep_sandpile import CREPSandpile
from .crep_spectrum import CREPSpectrumAtlas
from .manna import MannaSandpile
from .system import EthicsGateLight, SandpileUTAC

__all__ = [
    "BTWSandpile",
    "MannaSandpile",
    "CREPSandpile",
    "CREPSpectrumAtlas",
    "SandpileUTAC",
    "EthicsGateLight",
    "__version__",
]
