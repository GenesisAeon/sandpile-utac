"""
CREP Criticality Spectrum Atlas — the central scientific output of Package 22.

Collects Γ values from all GenesisAeon packages and exposes the complete
cross-domain CREP atlas.  Other packages (18-21) are imported when available;
otherwise the hardcoded calibrated values from the whitepaper are used.

Expected spectrum (Γ values):
  Solar flares:       0.014  — ultra-sensitive, barely supercritical
  Cygnus X-1 jets:    0.046  — low CREP, hair-trigger sensitivity
  Amazon forest:      0.116  — fragile, near tipping point
  AMOC ocean:         0.251  — homeostatic setpoint (η = 50 %)
  Neural criticality: 0.251  — same! cross-domain universality at η = 50 %
  BTW sandpile:       0.296  — robust classical SOC
  Manna sandpile:     0.376  — denser stochastic SOC
  ERA5 Arctic:        0.920  — near-saturated, tipping-zone climate
"""

from __future__ import annotations

import numpy as np

from .constants import CREP_SPECTRUM


class CREPSpectrumAtlas:
    """
    Cross-domain CREP Criticality Spectrum.

    Instantiate to get the hardcoded calibrated spectrum, or call
    `update_from_live()` to overwrite individual entries from installed
    sibling packages (amoc-utac, amazon-utac, …).
    """

    def __init__(self) -> None:
        self._spectrum: dict[str, float] = dict(CREP_SPECTRUM)

    # ── queries ───────────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, float]:
        """Return a sorted copy of the spectrum dict."""
        return dict(sorted(self._spectrum.items(), key=lambda kv: kv[1]))

    def is_monotonic(self) -> bool:
        """True iff spectrum values are non-decreasing when sorted by value."""
        vals = sorted(self._spectrum.values())
        return all(vals[i] <= vals[i + 1] for i in range(len(vals) - 1))

    def gamma_for(self, domain_key: str) -> float:
        """Return Γ for a domain key (partial match accepted)."""
        for k, v in self._spectrum.items():
            if domain_key.lower() in k.lower():
                return v
        raise KeyError(f"Domain '{domain_key}' not found in CREP spectrum.")

    def universality_pairs(self) -> list[tuple[str, str, float]]:
        """Return pairs of domains that share the same Γ (cross-domain universality)."""
        items = list(self._spectrum.items())
        pairs = []
        for i, (k1, v1) in enumerate(items):
            for k2, v2 in items[i + 1 :]:
                if abs(v1 - v2) < 0.005:
                    pairs.append((k1, k2, v1))
        return pairs

    # ── optional live update ──────────────────────────────────────────────────

    def update_from_live(self) -> dict[str, str]:
        """
        Try to import sibling packages and pull their live Γ values.
        Returns a dict of {package: status} ('updated' | 'not_installed').
        """
        status: dict[str, str] = {}

        _imports = [
            ("amoc_utac", "AMOC ocean (P18)"),
            ("amazon_utac", "Amazon forest (P19)"),
            ("neural_avalanche_utac", "Neural criticality (P20)"),
            ("solar_flare_utac", "Solar flares (P21)"),
        ]

        for module_name, spectrum_key in _imports:
            try:
                mod = __import__(module_name)
                inst = mod.__dict__.get("__main_class__")
                if inst is not None:
                    live_gamma = inst().get_crep_state()["Gamma"]
                    self._spectrum[spectrum_key] = float(live_gamma)
                    status[module_name] = "updated"
                else:
                    status[module_name] = "not_installed"
            except ImportError:
                status[module_name] = "not_installed"

        return status

    # ── formatted output ──────────────────────────────────────────────────────

    def summary_table(self) -> str:
        """Return a formatted ASCII table of the spectrum."""
        lines = [
            "CREP Criticality Spectrum — GenesisAeon Cross-Domain Atlas",
            "─" * 65,
            f"{'Domain':<35} {'Γ':>8}  {'η (%)':>8}  {'Character'}",
            "─" * 65,
        ]
        sorted_items = sorted(self._spectrum.items(), key=lambda kv: kv[1])
        for name, gamma in sorted_items:
            eta_pct = 100.0 * float(np.tanh(gamma * 2.2))
            if gamma < 0.05:
                char = "Ultra-sensitive"
            elif gamma < 0.15:
                char = "Fragile"
            elif gamma < 0.28:
                char = "Homeostatic"
            elif gamma < 0.45:
                char = "Robust SOC"
            else:
                char = "Near-saturated"
            lines.append(f"{name:<35} {gamma:>8.3f}  {eta_pct:>7.1f}%  {char}")
        lines.append("─" * 65)
        pairs = self.universality_pairs()
        if pairs:
            lines.append("Cross-domain universality pairs:")
            for k1, k2, g in pairs:
                lines.append(f"  Γ ≈ {g:.3f}: {k1}  ⟺  {k2}")
        return "\n".join(lines)

    def plot(self, save_path: str | None = None) -> None:
        """
        Plot the CREP spectrum as a horizontal bar chart.

        Requires matplotlib.  If save_path is given the figure is saved
        there; otherwise plt.show() is called.
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError as exc:
            raise ImportError("matplotlib is required for plotting.") from exc

        sorted_items = sorted(self._spectrum.items(), key=lambda kv: kv[1])
        names = [k for k, _ in sorted_items]
        gammas = [v for _, v in sorted_items]

        fig, ax = plt.subplots(figsize=(9, 5))
        colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(gammas)))
        bars = ax.barh(names, gammas, color=colors, edgecolor="black", linewidth=0.5)
        ax.set_xlabel("CREP parameter Γ", fontsize=12)
        ax.set_title(
            "CREP Criticality Spectrum — GenesisAeon Atlas\n"
            r"$\Gamma = \tanh^{-1}(\eta) / \sigma$",
            fontsize=12,
        )
        for bar, g in zip(bars, gammas, strict=True):
            ax.text(
                g + 0.005,
                bar.get_y() + bar.get_height() / 2,
                f"{g:.3f}",
                va="center",
                fontsize=9,
            )
        ax.axvline(
            0.251, color="red", linestyle="--", linewidth=1.2, label="η = 50% homeostatic setpoint"
        )
        ax.legend(fontsize=9)
        ax.set_xlim(0, max(gammas) * 1.15)
        plt.tight_layout()
        if save_path:
            plt.savefig(save_path, dpi=150)
        else:
            plt.show()
        plt.close(fig)

    def __repr__(self) -> str:
        return f"CREPSpectrumAtlas(n_domains={len(self._spectrum)})"
