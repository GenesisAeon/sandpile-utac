# sandpile-utac

> GenesisAeon Package 22 — BTW & Manna Sandpile as Continuous Phase Transition

<p align="center">
  <a href="https://doi.org/10.5281/zenodo.19645351"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.19645351.svg" alt="DOI (GenesisAeon Whitepaper)"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="MIT License"/></a>
  <a href="https://github.com/GenesisAeon/genesis-os"><img src="https://img.shields.io/badge/part%20of-genesis--os-blueviolet" alt="Part of genesis-os"/></a>
  <img src="https://img.shields.io/badge/UTAC-package%2022-orange" alt="Package 22"/>
</p>

**Bak–Tang–Wiesenfeld & Manna sandpiles as UTAC phase transitions.**

**Key result**: BTW Γ ≈ 0.296, Manna Γ ≈ 0.376 — anchors the CREP criticality spectrum.

## Installation

```bash
pip install sandpile-utac
```

For development:

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

## Role in the GenesisAeon Ecosystem

`sandpile-utac` is GenesisAeon Package **P22**, in the **statistical
mechanics / self-organized criticality** domain. It validates the UTAC
(Universal Threshold Activation Criticality) methodology against the
canonical Bak–Tang–Wiesenfeld and Manna sandpile models — the
prototypical self-organized-criticality benchmark — anchoring the CREP
Criticality Spectrum at Γ ≈ 0.296 (BTW) and Γ ≈ 0.376 (Manna).

## Citation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.PLACEHOLDER.svg)](https://doi.org/10.5281/zenodo.PLACEHOLDER)

DOI will be assigned automatically on first GitHub Release once
Zenodo–GitHub integration is enabled for this repo.

## License

MIT — see [LICENSE](LICENSE).
