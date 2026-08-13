# Inference Pipeline

How requests flow through the inference engine from prompt to generated tokens.

## Pipeline Overview

```
POST /v1/chat/completions
         │
         ▼
┌─────────────────┐
│ Schema Validate │  Pydantic: ChatCompletionRequest
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load Model (if  │  Check model_id matches loaded model
│ not loaded)     │  Load GGUF via llama-cpp-python
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Tokenize Prompt │  Count prompt tokens
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│  Sync  │ │Stream  │
│  Mode  │ │ Mode   │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌─────────────────┐
│  Generate       │  llama.cpp completion
│  Tokens         │  with sampling params
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ Format │ │ SSE    │
│Response│ │Chunks  │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌─────────────────┐
│  Return to      │  JSON or text/event-stream
│  Client         │
└─────────────────┘
```

## Model Loading

```
list_models()
    │
    ▼
Search paths (models/, ~/.cache/armpilot/, /opt/models/)
    │
    ▼
Filter by extension (.gguf)
    │
    ▼
Extract metadata (name, size, quantization)
    │
    ▼
Return ModelInfo list
```

### Loading a Model

```python
inference_service.load_model(
    model_id="llama-3.2-3b",
    n_threads=8,
    n_ctx=2048,
    n_batch=512,
)
```

The loader:
1. Locates the `.gguf` file by model ID
2. Creates a `Llama` instance with the specified parameters
3. Sets thread affinity if configured
4. Stores the loaded model in the runtime manager
5. Updates the model status

## Token Generation

### Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| `temperature` | 0.7 | 0.0–2.0 | Sampling temperature |
| `top_p` | 0.9 | 0.0–1.0 | Nucleus sampling |
| `max_tokens` | 256 | 1–4096 | Maximum output tokens |
| `stop` | [] | — | Stop sequences |
| `frequency_penalty` | 0.0 | -2.0–2.0 | Frequency penalty |
| `presence_penalty` | 0.0 | -2.0–2.0 | Presence penalty |

### Streaming Mode

When `stream: true`:
1. Generator yields token chunks as `ChatCompletionChunk` objects
2. Each chunk contains a delta with the new token(s)
3. Chunks are serialized as SSE: `data: {json}\n\n`
4. Stream ends with `data: [DONE]\n\n`

## Runtime Backends

| Runtime | Format | Platform | Features |
|---------|--------|----------|----------|
| llama.cpp | `.gguf` | All (Arm64 native) | Streaming, batch, quantization |
| MLX | `.safetensors`, `.gguf` | macOS ARM64 | Metal acceleration, streaming |
| ONNX | `.onnx` | All | Quantized models, multi-executor |

## Hardware Optimization

- **Thread Pinning** — Threads bound to physical cores via `cpu_affinity`
- **NEON/SVE2 SIMD** — llama.cpp auto-detects Arm SIMD extensions
- **Memory-Mapped I/O** — GGUF files memory-mapped for fast model loading
- **KV Cache** — Quantized KV cache (Q8_0) reduces memory pressure
