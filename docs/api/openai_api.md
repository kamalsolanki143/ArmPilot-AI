# OpenAI-Compatible API

ArmPilot-AI provides a fully OpenAI-compatible inference API, allowing you to use existing OpenAI client libraries with a local Arm64-optimized backend.

## Base URL

```
http://localhost:8000
```

## Endpoints

### List Models

```
GET /v1/models
```

Returns all available models discovered in the models directory.

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "llama-3.2-3b",
      "object": "model",
      "name": "Llama 3.2 3B",
      "provider": "local",
      "parameters": "3.2B",
      "quantization": "Q4_K_M",
      "size_mb": 2100.0,
      "context_length": 2048,
      "runtime": "llama.cpp",
      "loaded": false
    }
  ]
}
```

### Load Model

```
POST /v1/models/{model_id}/load
```

Load a model into memory for inference.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_threads` | int | 4 | Number of CPU threads |
| `n_ctx` | int | 2048 | Context window size |
| `n_batch` | int | 512 | Batch size for prompt processing |

**Response:**

```json
{
  "success": true,
  "model": {
    "id": "llama-3.2-3b",
    "loaded": true,
    "runtime": "llama.cpp"
  }
}
```

### Unload Model

```
POST /v1/models/unload
```

Unload the currently loaded model to free memory.

**Response:**

```json
{
  "success": true,
  "message": "Model unloaded"
}
```

### Model Status

```
GET /v1/models/status
```

Get the current inference engine status.

**Response:**

```json
{
  "success": true,
  "model_loaded": true,
  "current_model": {
    "id": "llama-3.2-3b",
    "name": "Llama 3.2 3B"
  },
  "runtime": "llama.cpp",
  "threads": 8,
  "context_length": 2048
}
```

### Chat Completions

```
POST /v1/chat/completions
```

Create a chat completion. Supports both synchronous and streaming responses.

**Request Body:**

```json
{
  "model": "llama-3.2-3b",
  "messages": [
    {"role": "system", "content": "You are a helpful ARM64 hardware expert."},
    {"role": "user", "content": "What are the advantages of ARM64 for AI?"}
  ],
  "max_tokens": 256,
  "temperature": 0.7,
  "top_p": 0.9,
  "stream": false,
  "stop": [],
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

**Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `model` | string | required | — | Model ID to use |
| `messages` | array | required | 1+ | Chat messages (role + content) |
| `max_tokens` | int | 256 | 1–4096 | Maximum output tokens |
| `temperature` | float | 0.7 | 0.0–2.0 | Sampling temperature |
| `top_p` | float | 0.9 | 0.0–1.0 | Nucleus sampling |
| `stream` | bool | false | — | Enable SSE streaming |
| `stop` | array | null | — | Stop sequences |
| `frequency_penalty` | float | 0.0 | -2.0–2.0 | Frequency penalty |
| `presence_penalty` | float | 0.0 | -2.0–2.0 | Presence penalty |

**Synchronous Response:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1723392000,
  "model": "llama-3.2-3b",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The ARM64 architecture offers several key advantages..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 24,
    "completion_tokens": 156,
    "total_tokens": 180
  }
}
```

**Streaming Response (SSE):**

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1723392000,"model":"llama-3.2-3b","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1723392000,"model":"llama-3.2-3b","choices":[{"index":0,"delta":{"content":"The"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1723392000,"model":"llama-3.2-3b","choices":[{"index":0,"delta":{"content":" ARM64"},"finish_reason":null}]}

data: [DONE]
```

## Usage with OpenAI Python Client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="not-needed",  # Auth optional for inference
)

# List models
models = client.models.list()

# Chat completion
response = client.chat.completions.create(
    model="llama-3.2-3b",
    messages=[
        {"role": "user", "content": "Explain ARM64 NEON instructions."}
    ],
    max_tokens=256,
    temperature=0.7,
)
print(response.choices[0].message.content)

# Streaming
stream = client.chat.completions.create(
    model="llama-3.2-3b",
    messages=[{"role": "user", "content": "Hello"}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Usage with curl

```bash
# List models
curl http://localhost:8000/v1/models

# Load model
curl -X POST http://localhost:8000/v1/models/llama-3.2-3b/load

# Chat
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.2-3b",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 128
  }'
```
