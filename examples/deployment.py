"""
ArmPilot-AI — Deployment Example
Demonstrates loading a model and starting the inference server programmatically.
"""

import signal
import sys

from app.services.inference_service import inference_service
from app.schemas.inference import ChatCompletionRequest, ChatMessage
from app.utils.hardware import get_hardware_info, get_system_metrics


def main() -> None:
    model_id = "llama-3.2-1b-instruct"
    host = "0.0.0.0"
    port = 8000

    # Print hardware info
    hw = get_hardware_info()
    print("Hardware:")
    print(f"  Architecture: {hw['architecture']}")
    print(f"  CPU: {hw['cpu_model']}")
    print(f"  Memory: {hw['memory_total_gb']} GB")
    print(f"  ARM64: {'Yes' if hw['is_arm64'] else 'No'}")
    print()

    # Load the model
    print(f"Loading model '{model_id}'...")
    try:
        inference_service.load_model(
            model_id,
            n_threads=4,
            n_batch=512,
            n_ctx=2048,
        )
    except Exception as e:
        print(f"Failed to load model: {e}")
        print("Place a .gguf model file in the models/ directory and try again.")
        return

    print(f"Model loaded successfully.\n")

    # Verify the model works
    print("Verifying model with a test prompt...")
    request = ChatCompletionRequest(
        model=model_id,
        messages=[ChatMessage(role="user", content="Hello! Respond with one sentence.")],
        max_tokens=50,
    )
    response = inference_service.chat_completion(request)
    print(f"Test response: {response.choices[0].message.content}")
    print(f"  Tokens: {response.usage.total_tokens}\n")

    # Show service status
    status = inference_service.get_status()
    print("Service Status:")
    print(f"  Model loaded: {status['model_loaded']}")
    print(f"  Runtime: {status['runtime']}")
    if status.get("model_info"):
        info = status["model_info"]
        print(f"  File size: {info.get('file_size_mb', 'N/A')} MB")
    print()

    # Start the server
    print(f"Starting API server on {host}:{port}...")
    print(f"  API docs: http://{host}:{port}/docs")
    print(f"  Health: http://{host}:{port}/api/health")
    print(f"  Press Ctrl+C to stop.\n")

    import uvicorn

    def shutdown_handler(sig, frame):
        print("\nShutting down...")
        inference_service.unload()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
