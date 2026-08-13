"""
ArmPilot-AI — Main CLI Entry Point
"""

import sys

import click

from app.core.config import settings

__version__ = settings.app_version


@click.group()
@click.version_option(version=__version__, prog_name="ArmPilot-AI")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """ArmPilot-AI — Arm64 LLM Inference Optimization & Benchmarking Platform."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    if verbose:
        click.echo(f"ArmPilot-AI v{__version__}")


# Import and register subcommands
from app.cli.benchmark import benchmark  # noqa: E402
from app.cli.optimize import optimize  # noqa: E402
from app.cli.deploy import deploy  # noqa: E402
from app.cli.report import report  # noqa: E402
from app.cli.lab import lab  # noqa: E402
from app.cli.cleanup import cleanup  # noqa: E402

cli.add_command(benchmark)
cli.add_command(optimize)
cli.add_command(deploy)
cli.add_command(report)
cli.add_command(lab)
cli.add_command(cleanup)


@cli.command()
def info() -> None:
    """Show ArmPilot-AI installation and hardware info."""
    from app.utils.hardware import get_hardware_info

    click.echo("ArmPilot-AI v" + __version__)
    click.echo(f"Config: host={settings.host}:{settings.port}, log_level={settings.log_level}")
    click.echo(f"Models dir: {settings.models_dir}")
    click.echo(f"Reports dir: {settings.reports_dir}")
    click.echo()

    hw = get_hardware_info()
    click.echo("Hardware:")
    click.echo(f"  Architecture: {hw['architecture']}")
    click.echo(f"  CPU: {hw['cpu_model']}")
    click.echo(f"  Cores: {hw['cpu_count']} logical, {hw['cpu_count_physical']} physical")
    click.echo(f"  Memory: {hw['memory_total_gb']} GB")
    click.echo(f"  ARM64: {'Yes' if hw['is_arm64'] else 'No'}")
    click.echo(f"  Platform: {hw['platform']}")


@cli.command()
def models() -> None:
    """List available models."""
    from app.services.inference_service import inference_service

    model_list = inference_service.list_models()
    if not model_list:
        click.echo("No models found. Place .gguf files in the models/ directory.")
        return

    click.echo(f"Found {len(model_list)} model(s):\n")
    click.echo(f"  {'ID':<30} {'Name':<25} {'Size':<12} {'Runtime':<15} {'Status'}")
    click.echo(f"  {'─'*30} {'─'*25} {'─'*12} {'─'*15} {'─'*10}")
    for m in model_list:
        size = f"{m.size_mb:.0f} MB" if m.size_mb else "N/A"
        status = "loaded" if m.loaded else "available"
        click.echo(f"  {m.id:<30} {m.name:<25} {size:<12} {m.runtime:<15} {status}")


@cli.command()
@click.option("--host", default=None, help="Override host.")
@click.option("--port", default=None, type=int, help="Override port.")
@click.option("--reload", is_flag=True, help="Enable auto-reload.")
def serve(host: str | None, port: int | None, reload: bool) -> None:
    """Start the ArmPilot-AI API server."""
    import uvicorn

    h = host or settings.host
    p = port or settings.port
    click.echo(f"Starting ArmPilot-AI server on {h}:{p}...")
    uvicorn.run(
        "main:app",
        host=h,
        port=p,
        reload=reload or settings.debug,
        log_level=settings.log_level.lower(),
    )


def main() -> None:
    """CLI entry point for pyproject.toml / console_scripts."""
    cli(obj={})


if __name__ == "__main__":
    main()
