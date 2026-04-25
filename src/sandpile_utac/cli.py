"""sandpile-utac CLI — run simulations, scan phase diagrams, plot the CREP spectrum."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="sandpile-utac",
    help=("BTW/Manna sandpile SOC as UTAC continuous phase transition (GenesisAeon Package 22)."),
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()
err = Console(stderr=True)


# ── run ───────────────────────────────────────────────────────────────────────


@app.command()
def run(
    model: Annotated[str, typer.Option("--model", "-m", help="'btw' or 'manna'")] = "btw",
    L: Annotated[int, typer.Option("--L", help="Grid side length")] = 128,
    grains: Annotated[int, typer.Option("--grains", "-g", help="Grain additions")] = 50_000,
    warmup: Annotated[int, typer.Option("--warmup", help="Warmup grains (discarded)")] = 10_000,
    seed: Annotated[int, typer.Option("--seed", help="RNG seed")] = 42,
) -> None:
    """Run a sandpile simulation and report CREP / UTAC state."""
    from .system import SandpileUTAC

    console.print(
        Panel(
            f"[bold green]sandpile-utac[/bold green] — "
            f"model=[cyan]{model.upper()}[/cyan]  L=[cyan]{L}[/cyan]  "
            f"grains=[cyan]{grains:,}[/cyan]",
            expand=False,
        )
    )

    sp = SandpileUTAC(model=model, L=L, seed=seed)
    result = sp.run_cycle(n_grains=grains, warmup_grains=warmup)

    crep = result["crep"]
    utac = result["utac"]
    meta = result["meta"]

    t = Table(show_header=False, box=None, padding=(0, 2))
    t.add_row("[bold]CREP state[/bold]", "")
    t.add_row("  C (spatial correlation)", f"{crep['C']:.4f}")
    t.add_row("  R (resonance/power-law)", f"{crep['R']:.4f}")
    t.add_row("  E (emergence)", f"{crep['E']:.4f}")
    t.add_row("  P (permutation entropy)", f"{crep['P']:.4f}")
    t.add_row("  [bold]Gamma[/bold]", f"[bold yellow]{crep['Gamma']:.4f}[/bold yellow]")
    t.add_row("  eta (H/K)", f"{crep['eta']:.4f}")
    t.add_row("", "")
    t.add_row("[bold]UTAC state[/bold]", "")
    t.add_row("  H  (density)", f"{utac['H']:.4f}")
    t.add_row("  H* (fixed point)", f"{utac['H_star']:.4f}")
    t.add_row("  K  (threshold)", f"{utac['K_eff']:.0f}")
    t.add_row("", "")
    t.add_row("Phase events (avalanches)", f"{result['n_events']:,}")
    t.add_row("Elapsed", f"{meta['elapsed_s']:.2f} s")
    console.print(t)


# ── phase-diagram ─────────────────────────────────────────────────────────────


@app.command(name="phase-diagram")
def phase_diagram(
    model: Annotated[str, typer.Option("--model", "-m")] = "btw",
    L: Annotated[int, typer.Option("--L")] = 64,
    rho_min: Annotated[float, typer.Option("--rho-min")] = 0.10,
    rho_max: Annotated[float, typer.Option("--rho-max")] = 0.95,
    n_points: Annotated[int, typer.Option("--n-points")] = 20,
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """Scan drop density vs. order parameter (activity)."""
    from .phase_diagram import PhaseDiagramScanner

    console.print(
        Panel(
            f"Phase diagram sweep — model={model.upper()}  L={L}  "
            f"η ∈ [{rho_min:.2f}, {rho_max:.2f}]  {n_points} points",
            expand=False,
        )
    )
    scanner = PhaseDiagramScanner(L=L, seed=seed)
    result = scanner.scan(model=model, rho_min=rho_min, rho_max=rho_max, n_points=n_points)

    console.print(
        f"  Critical density estimate η_c ≈ "
        f"[bold yellow]{result['critical_density_estimate']:.3f}[/bold yellow]"
    )
    t = Table("η", "Activity (topplings/grain)", show_header=True, box=None, padding=(0, 3))
    for eta, act in zip(result["rho_values"], result["activity"], strict=True):
        t.add_row(f"{eta:.3f}", f"{act:.1f}")
    console.print(t)


# ── crep-spectrum ─────────────────────────────────────────────────────────────


@app.command(name="crep-spectrum")
def crep_spectrum(
    plot: Annotated[bool, typer.Option("--plot/--no-plot", help="Show bar chart")] = False,
    save: Annotated[str | None, typer.Option("--save", help="Save plot to file")] = None,
) -> None:
    """Print the CREP Criticality Spectrum atlas (all GenesisAeon packages)."""
    from .crep_spectrum import CREPSpectrumAtlas

    atlas = CREPSpectrumAtlas()
    atlas.update_from_live()
    console.print(atlas.summary_table())

    if plot or save:
        try:
            atlas.plot(save_path=save)
            if save:
                console.print(f"[green]Saved to {save}[/green]")
        except ImportError:
            err.print("[yellow]matplotlib not installed — skipping plot.[/yellow]")


# ── benchmark ─────────────────────────────────────────────────────────────────


@app.command()
def benchmark(
    L: Annotated[int, typer.Option("--L")] = 64,
    grains: Annotated[int, typer.Option("--grains")] = 50_000,
    seed: Annotated[int, typer.Option("--seed")] = 42,
) -> None:
    """Run the full benchmark suite and report pass/fail against targets."""
    from .benchmark import run_benchmark

    console.print(Panel(f"Benchmark  L={L}  grains={grains:,}", expand=False))
    result = run_benchmark(L=L, n_grains=grains, warmup=grains // 5, seed=seed, verbose=True)

    if result["all_passed"]:
        console.print("[bold green]All targets passed.[/bold green]")
    else:
        n_fail = sum(not v for v in result["passed"].values())
        console.print(f"[bold red]{n_fail} target(s) failed.[/bold red]")
        raise typer.Exit(code=1)


# ── version ───────────────────────────────────────────────────────────────────


@app.command()
def version() -> None:
    """Show sandpile-utac version."""
    from . import __version__

    console.print(f"sandpile-utac [bold]{__version__}[/bold]")


if __name__ == "__main__":
    app()
