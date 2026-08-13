"""
ArmPilot-AI — Deployment CLI Commands
"""

import click


@click.group()
def deploy() -> None:
    """Manage model deployment and serving."""


@deploy.command("start")
@click.option("--model", "-m", required=True, help="Model ID to deploy.")
@click.option("--host", default="0.0.0.0", help="Bind host.")
@click.option("--port", "-p", default=8000, type=int, help="Bind port.")
@click.option("--threads", "-t", default=4, type=int, help="Thread count.")
@click.option("--batch-size", "-b", default=512, type=int, help="Batch size.")
@click.option("--context-length", "-c", default=2048, type=int, help="Context length.")
@click.option("--reload", is_flag=True, help="Enable auto-reload (dev mode).")
def start_model(
    model: str,
    host: str,
    port: int,
    threads: int,
    batch_size: int,
    context_length: int,
    reload: bool,
) -> None:
    """Load a model and start the inference API server."""
    import uvicorn

    click.echo(f"Deploying model '{model}'...")
    click.echo(f"  Server: {host}:{port}")
    click.echo(f"  Threads: {threads}, Batch: {batch_size}, Context: {context_length}")

    # Pre-load the model
    click.echo("\nLoading model...")
    try:
        from app.services.inference_service import inference_service
        inference_service.load_model(
            model,
            n_threads=threads,
            n_batch=batch_size,
            n_ctx=context_length,
        )
        click.echo(f"Model '{model}' loaded successfully.")
    except Exception as e:
        click.echo(f"Failed to load model: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"\nStarting API server on {host}:{port}...")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


@deploy.command("status")
def deploy_status() -> None:
    """Show deployment status and loaded model info."""
    from app.services.inference_service import inference_service

    status = inference_service.get_status()

    click.echo("Deployment Status")
    click.echo(f"  Model loaded: {status['model_loaded']}")
    click.echo(f"  Runtime: {status['runtime'] or 'N/A'}")

    if status["current_model"]:
        m = status["current_model"]
        click.echo(f"  Model: {m['name']} ({m['id']})")
        click.echo(f"  Quantization: {m.get('quantization', 'N/A')}")
        click.echo(f"  Context length: {m.get('context_length', 'N/A')}")
    else:
        click.echo("  No model loaded.")

    if status.get("model_info"):
        info = status["model_info"]
        click.echo(f"  File size: {info.get('file_size_mb', 'N/A')} MB")
        click.echo(f"  Parameters: {info.get('parameters', 'N/A')}")


@deploy.command("stop")
def stop_model() -> None:
    """Unload the currently loaded model."""
    from app.services.inference_service import inference_service

    if inference_service.current_model:
        name = inference_service.current_model.name
        inference_service.unload()
        click.echo(f"Model '{name}' unloaded.")
    else:
        click.echo("No model is currently loaded.")


@deploy.command("health")
@click.option("--url", default="http://localhost:8000", help="Server URL to check.")
def health_check(url: str) -> None:
    """Check API server health."""
    import urllib.request
    import json

    try:
        req = urllib.request.Request(f"{url}/api/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            click.echo(f"Server is healthy: {json.dumps(data, indent=2)}")
    except Exception as e:
        click.echo(f"Health check failed: {e}", err=True)
        raise SystemExit(1)
