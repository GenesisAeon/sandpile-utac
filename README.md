# sandpile-utac

> GenesisAeon Package 22 — BTW & Manna Sandpile as Continuous Phase Transition

<p align="center">
  <a href="https://doi.org/10.5281/zenodo.19645351"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.19645351.svg" alt="DOI (GenesisAeon Whitepaper)"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-GPLv3-blue.svg" alt="GPLv3 License"/></a>
  <a href="https://creativecommons.org/licenses/by/4.0/"><img src="https://img.shields.io/badge/docs-CC%20BY%204.0-lightblue.svg" alt="CC BY 4.0"/></a>
  <a href="https://github.com/GenesisAeon/genesis-os"><img src="https://img.shields.io/badge/part%20of-genesis--os-blueviolet" alt="Part of genesis-os"/></a>
  <img src="https://img.shields.io/badge/UTAC-package%2020-orange" alt="Package 20"/>
</p>

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
