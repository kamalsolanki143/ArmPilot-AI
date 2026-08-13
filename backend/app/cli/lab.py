"""
ArmPilot-AI — Interactive Lab CLI
Provides an interactive REPL for experimentation.
"""

import click


@click.group()
def lab() -> None:
    """Interactive experimentation lab."""


@lab.command()
@click.option("--model", "-m", required=True, help="Model to load.")
@click.option("--threads", "-t", default=4, type=int, help="Thread count.")
def repl(model: str, threads: int) -> None:
    """Start an interactive chat session with a loaded model."""
    click.echo(f"ArmPilot-AI Interactive Lab")
    click.echo(f"Loading model '{model}'...")

    try:
        from app.services.inference_service import inference_service
        inference_service.load_model(model, n_threads=threads)
        click.echo(f"Model loaded. Type your messages below. 'quit' to exit.\n")
    except Exception as e:
        click.echo(f"Failed to load model: {e}", err=True)
        raise SystemExit(1)

    from app.schemas.inference import ChatCompletionRequest, ChatMessage

    while True:
        try:
            user_input = click.prompt("You", prompt_suffix="> ")
        except (EOFError, KeyboardInterrupt):
            click.echo("\nExiting lab.")
            break

        if user_input.strip().lower() in ("quit", "exit", "q"):
            click.echo("Exiting lab.")
            break

        if not user_input.strip():
            continue

        request = ChatCompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=user_input)],
            max_tokens=512,
            temperature=0.7,
        )

        try:
            response = inference_service.chat_completion(request)
            assistant_msg = response.choices[0].message.content
            usage = response.usage

            click.echo(f"\nAssistant: {assistant_msg}")
            click.echo(
                f"  [{usage.prompt_tokens}+{usage.completion_tokens} tokens, "
                f"{usage.total_tokens} total]\n"
            )
        except Exception as e:
            click.echo(f"  Error: {e}\n")


@lab.command()
@click.option("--model", "-m", required=True, help="Model to benchmark.")
@click.option("--prompt", "-p", default="What is ARM64?", help="Prompt to use.")
@click.option("--max-tokens", default=128, type=int, help="Max tokens to generate.")
@click.option("--repeat", "-r", default=5, type=int, help="Number of iterations.")
def timing(model: str, prompt: str, max_tokens: int, repeat: int) -> None:
    """Quick timing test — measure latency for a single prompt."""
    import time

    click.echo(f"Quick timing test: model={model}, repeat={repeat}")
    click.echo(f"Prompt: \"{prompt[:60]}{'...' if len(prompt) > 60 else ''}\"\n")

    try:
        from app.services.inference_service import inference_service
        inference_service.load_model(model)
    except Exception as e:
        click.echo(f"Failed to load model: {e}", err=True)
        raise SystemExit(1)

    from app.schemas.inference import ChatCompletionRequest, ChatMessage

    latencies = []
    for i in range(repeat):
        request = ChatCompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=prompt)],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        start = time.perf_counter()
        response = inference_service.chat_completion(request)
        elapsed = (time.perf_counter() - start) * 1000
        latencies.append(elapsed)

        tokens = response.usage.completion_tokens
        tps = (tokens / elapsed * 1000) if elapsed > 0 else 0
        click.echo(f"  Run {i+1}: {elapsed:.1f}ms, {tokens} tokens, {tps:.1f} tok/s")

    import statistics
    avg = statistics.mean(latencies)
    std = statistics.stdev(latencies) if len(latencies) > 1 else 0
    click.echo(f"\n  Average: {avg:.1f}ms (std={std:.1f}ms)")
    click.echo(f"  Min: {min(latencies):.1f}ms  Max: {max(latencies):.1f}ms")


@lab.command()
def hardware() -> None:
    """Display detailed hardware information."""
    from app.utils.hardware import get_hardware_info, get_system_metrics

    hw = get_hardware_info()
    sys_m = get_system_metrics()

    click.echo("Hardware Information")
    click.echo(f"  Architecture:  {hw['architecture']}")
    click.echo(f"  ARM64:         {'Yes' if hw['is_arm64'] else 'No'}")
    click.echo(f"  CPU:           {hw['cpu_model']}")
    click.echo(f"  Logical cores: {hw['cpu_count']}")
    click.echo(f"  Physical cores:{hw['cpu_count_physical']}")
    click.echo(f"  CPU freq:      {hw.get('cpu_freq_mhz', 'N/A')} MHz")
    click.echo(f"  Memory:        {hw['memory_total_gb']} GB total, {hw['memory_available_gb']} GB available")
    click.echo(f"  Platform:      {hw['platform']} {hw.get('platform_version', '')}")
    click.echo(f"  Python:        {hw['python_version']}")
    click.echo()
    click.echo("System Utilization")
    click.echo(f"  CPU:  {sys_m['cpu_utilization_percent']:.1f}%")
    click.echo(f"  RAM:  {sys_m['memory_used_mb']:.0f} / {sys_m['memory_total_mb']:.0f} MB ({sys_m['memory_used_percent']:.1f}%)")
