"""
ArmPilot-AI — Cleanup CLI Commands
"""

import shutil

import click


@click.group()
def cleanup() -> None:
    """Clean up logs, reports, caches, and temporary files."""


@cleanup.command("all")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted without deleting.")
def clean_all(dry_run: bool) -> None:
    """Remove all generated artifacts (logs, reports, caches, temp files)."""
    from app.core.config import settings

    base = settings.base_dir
    targets = [
        (settings.resolve_path(settings.reports_dir), "reports"),
        (base / "logs", "logs"),
        (base / "__pycache__", "pycache"),
        (base / ".pytest_cache", "pytest cache"),
        (base / "data" / "cache", "data cache"),
    ]

    # Walk for __pycache__ dirs
    pycache_dirs = list(base.rglob("__pycache__"))
    targets.extend((d, str(d.relative_to(base))) for d in pycache_dirs)

    total_size = 0
    cleaned = 0
    for path, label in targets:
        if not path.exists():
            continue
        size = _dir_size(path) if path.is_dir() else path.stat().st_size
        if dry_run:
            click.echo(f"  [dry-run] Would remove: {path} ({_fmt_size(size)})")
        else:
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                click.echo(f"  Removed: {path} ({_fmt_size(size)})")
                cleaned += 1
            except Exception as e:
                click.echo(f"  Failed to remove {path}: {e}", err=True)
        total_size += size

    action = "Would remove" if dry_run else "Removed"
    click.echo(f"\n{action} {cleaned} items, {_fmt_size(total_size)} total.")


@cleanup.command("logs")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted.")
def clean_logs(dry_run: bool) -> None:
    """Remove log files."""
    from app.core.config import settings

    log_dir = settings.base_dir / "logs"
    if not log_dir.exists():
        click.echo("No logs directory found.")
        return

    files = list(log_dir.glob("*.log")) + list(log_dir.glob("*.log.*"))
    _clean_files(files, "logs", dry_run)


@cleanup.command("reports")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted.")
def clean_reports(dry_run: bool) -> None:
    """Remove generated reports."""
    from app.core.config import settings

    reports_dir = settings.resolve_path(settings.reports_dir)
    if not reports_dir.exists():
        click.echo("No reports directory found.")
        return

    files = list(reports_dir.glob("*.*"))
    _clean_files(files, "reports", dry_run)


@cleanup.command("cache")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted.")
def clean_cache(dry_run: bool) -> None:
    """Remove Python cache directories."""
    from app.core.config import settings

    base = settings.base_dir
    pycache_dirs = list(base.rglob("__pycache__"))
    total = 0
    for d in pycache_dirs:
        size = _dir_size(d)
        if dry_run:
            click.echo(f"  [dry-run] Would remove: {d}")
        else:
            try:
                shutil.rmtree(d)
                click.echo(f"  Removed: {d}")
                total += 1
            except Exception as e:
                click.echo(f"  Failed: {d}: {e}", err=True)

    click.echo(f"{'Would remove' if dry_run else 'Removed'} {total} cache directories.")


@cleanup.command("temp")
@click.option("--dry-run", is_flag=True, help="Show what would be deleted.")
def clean_temp(dry_run: bool) -> None:
    """Remove temporary files and directories."""
    from app.core.config import settings

    base = settings.base_dir
    temp_patterns = ["*.tmp", "*.temp", "*.bak", "*~", "*.swp"]
    files = []
    for pattern in temp_patterns:
        files.extend(base.rglob(pattern))

    _clean_files(files, "temp", dry_run)


def _clean_files(files: list, label: str, dry_run: bool) -> None:
    """Clean a list of files."""
    total_size = 0
    cleaned = 0
    for fp in files:
        size = fp.stat().st_size
        if dry_run:
            click.echo(f"  [dry-run] Would remove: {fp.name} ({_fmt_size(size)})")
        else:
            try:
                fp.unlink()
                click.echo(f"  Removed: {fp.name}")
                cleaned += 1
            except Exception as e:
                click.echo(f"  Failed: {fp.name}: {e}", err=True)
        total_size += size

    click.echo(f"\n{'Would remove' if dry_run else 'Removed'} {cleaned} {label} files ({_fmt_size(total_size)}).")


def _dir_size(path) -> int:
    """Get total size of a directory."""
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _fmt_size(size: int) -> str:
    """Format byte size to human-readable string."""
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.1f} GB"
