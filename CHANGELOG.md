# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.0] - 2026
### Added
- Initial v1.0.0 release as part of the GenesisAeon ecosystem-wide 1.0.0
  milestone.
- Standardized release tooling: updated `.zenodo.json`, GitHub Actions
  release workflow (`.github/workflows/release.yml`), `RELEASE_GUIDE.md`,
  `CONTRIBUTING.md`, issue/PR templates.

### Changed
- Project metadata (`pyproject.toml`) bumped from `0.1.0` to `1.0.0`.

### Fixed
- Corrected a licensing inconsistency: `LICENSE`, `pyproject.toml`,
  `CITATION.cff`, `.zenodo.json`, and `README.md` now consistently
  specify GPL-3.0-or-later for code and CC BY 4.0 for documentation/data
  — the package's intended (copyleft) license. An intermediate revision
  had incorrectly drifted to MIT; this restores the correct license.
