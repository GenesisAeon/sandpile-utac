# sandpile-utac

> GenesisAeon Package 22 — BTW & Manna Sandpile as Continuous Phase Transition

[![GenesisAeon](https://img.shields.io/badge/GenesisAeon-Package%2022-blueviolet)](https://github.com/GenesisAeon)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19645351.svg)](https://doi.org/10.5281/zenodo.19645351)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Reference](https://img.shields.io/badge/Ref-PhysRevE%202025-red)](https://doi.org/10.1103/PhysRevE.111.024111)

**Bak–Tang–Wiesenfeld & Manna sandpiles as UTAC phase transitions.**

**Key result**: BTW Γ ≈ 0.296, Manna Γ ≈ 0.376 — anchors the CREP criticality spectrum.

## Installation

```bash
pip install -e ".[dev]"
```

## Quickstart

```bash
sandpile-utac run --model btw --L 256
sandpile-utac phase-diagram
sandpile-utac crep-spectrum
```

## Integration in genesis-os

```python
from genesis_os import GenesisOS
os = GenesisOS()
sandpile = os.load_package(22)
results = sandpile.run_cycle(n_grains=10_000_000)
```

## Benchmark

Validated against Phys. Rev. E (2025).

## Falsifiable Prediction

Systems with η = 50 % converge to Γ ≈ 0.25 across all domains.

## License

Code: MIT • Docs & Data: CC BY 4.0
