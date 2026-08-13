# Inference Pipeline Flow

Detailed flow of how inference requests are processed.

```mermaid
flowchart TD
    Start([Client Request]) --> Validate{Validate Request}
    Validate -->|Invalid| Error400[Return 400 Error]
    Validate -->|Valid| CheckModel{Model Loaded?}

    CheckModel -->|No| LoadModel[Load GGUF Model]
    LoadModel -->|Success| Tokenize
    LoadModel -->|Error| Error500[Return 500 Error]

    CheckModel -->|Yes| Tokenize[Tokenize Prompt]

    Tokenize --> CheckStream{Stream Mode?}

    CheckStream -->|No| SyncGen[Generate Tokens<br/>Synchronous]
    CheckStream -->|Yes| StreamGen[Generate Tokens<br/>Streaming]

    SyncGen --> FormatJSON[Format JSON Response]
    StreamGen --> FormatSSE[Format SSE Chunks]

    FormatJSON --> Return[Return to Client]
    FormatSSE --> Return

    style Start fill:#4caf50,color:white
    style Error400 fill:#f44336,color:white
    style Error500 fill:#f44336,color:white
    style Return fill:#2196f3,color:white
```

## Detailed Steps

### 1. Request Validation

```python
# Pydantic schema validation
ChatCompletionRequest(
    model: str,
    messages: List[Message],
    max_tokens: int = 256,
    temperature: float = 0.7,
    stream: bool = False
)
```

### 2. Model Loading

```python
# Runtime manager loads model
def load_model(model_id, n_threads, n_ctx, n_batch):
    # 1. Locate GGUF file
    # 2. Create Llama instance
    # 3. Set thread affinity
    # 4. Store in runtime manager
    # 5. Update model status
```

### 3. Token Generation

| Mode | Method | Output |
|------|--------|--------|
| Sync | `llama.create_completion()` | JSON response |
| Stream | `llama.create_completion(stream=True)` | SSE chunks |

### 4. Streaming Protocol

```
data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"}}]}

data: {"id":"chatcmpl-123","object":"chat.completion.chunk","choices":[{"delta":{"content":" world"}}]}

data: [DONE]
```

## Runtime Backends

```mermaid
flowchart LR
    subgraph Runtime["Runtime Selection"]
        R1[llama.cpp]
        R2[MLX]
        R3[ONNX]
    end

    subgraph Hardware["Hardware"]
        H1[ARM64 NEON]
        H2[Metal GPU]
        H3[CPU/GPU]
    end

    R1 -->|SIMD| H1
    R2 -->|Metal| H2
    R3 -->|Compute| H3

    style Runtime fill:#e3f2fd
    style Hardware fill:#e8f5e9
```

## Performance Optimizations

| Optimization | Description | Impact |
|--------------|-------------|--------|
| Thread Pinning | Bind threads to physical cores | +15% throughput |
| Memory Mapping | mmap GGUF files | -50% load time |
| KV Cache | Quantized cache (Q8_0) | -30% memory |
| Batch Processing | Parallel token generation | +20% throughput |
