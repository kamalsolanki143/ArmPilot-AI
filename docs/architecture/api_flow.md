# API Flow

Request/response lifecycle through the ArmPilot-AI backend.

## HTTP Request Lifecycle

```
Client Request
     │
     ▼
┌─────────────────┐
│   Nginx/Docker  │  Reverse proxy (production only)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Uvicorn       │  ASGI server
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CORSMiddleware  │  Origin validation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RequestTiming   │  Start timer, log method/path
│   Middleware     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  API Router     │  Route matching by prefix
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│  Auth  │ │ Public │
│  Gate  │ │ Route  │
└───┬────┘ └───┬────┘
    │          │
    ▼          │
┌──────────┐   │
│ JWT      │   │
│ Verify   │   │
└───┬──────┘   │
    │          │
    ▼          ▼
┌─────────────────┐
│  Route Handler  │  Pydantic validation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Service      │  Business logic
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Subsystem     │  Inference/Benchmark/Optimize
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Storage      │  SQLite + JSON
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  JSON Response  │  + X-Process-Time-Ms header
└─────────────────┘
```

## API Endpoints Summary

### Public Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc documentation |

### Auth Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/auth/register` | No | Create account |
| `POST` | `/auth/login` | No | Get tokens |
| `POST` | `/auth/refresh` | No | Refresh tokens |
| `POST` | `/auth/logout` | Yes | Revoke refresh token |
| `GET` | `/auth/me` | Yes | Get profile |
| `POST` | `/auth/change-password` | Yes | Change password |
| `GET` | `/auth/oauth/github` | No | GitHub OAuth redirect |
| `GET` | `/auth/oauth/github/callback` | No | GitHub OAuth callback |

### Inference Endpoints (OpenAI-Compatible)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/v1/models` | No | List available models |
| `POST` | `/v1/models/{id}/load` | No | Load a model |
| `POST` | `/v1/models/unload` | No | Unload current model |
| `GET` | `/v1/models/status` | No | Model/inference status |
| `POST` | `/v1/chat/completions` | No | Chat completion (stream or sync) |

### Benchmark Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/benchmark/run` | No | Start benchmark (async) |
| `POST` | `/api/benchmark/run/sync` | No | Run benchmark (sync) |
| `GET` | `/api/benchmark/{id}` | No | Get benchmark result |
| `GET` | `/api/benchmark/latest` | No | Get latest result |
| `GET` | `/api/benchmarks` | No | List all benchmarks |

### Optimization Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/optimization/run` | No | Start optimization (async) |
| `GET` | `/api/optimization/progress` | No | Poll progress |
| `GET` | `/api/optimization/{id}` | No | Get optimization result |
| `GET` | `/api/optimizations` | No | List all optimizations |

### Other Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/metrics` | System metrics |
| Various | `/api/reports/*` | Report generation/export |
| Various | `/api/history/*` | Run history |

## Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "MODEL_NOT_FOUND",
    "message": "Model 'xyz' not found."
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `MODEL_NOT_FOUND` | 404 | Requested model does not exist |
| `MODEL_NOT_LOADED` | 503 | No model is loaded |
| `RUNTIME_NOT_AVAILABLE` | 503 | Requested runtime not installed |
| `BENCHMARK_RUNNING` | 409 | A benchmark is already running |
| `OPTIMIZATION_RUNNING` | 409 | An optimization is already running |
| `BENCHMARK_NOT_FOUND` | 404 | Benchmark run not found |
| `OPTIMIZATION_NOT_FOUND` | 404 | Optimization run not found |
| `INFERENCE_ERROR` | 500 | Inference execution failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

## Streaming Response Format

For `POST /v1/chat/completions` with `stream: true`:

```
data: {"id":"...","object":"chat.completion.chunk","choices":[{"delta":{"content":"Hello"}}]}
data: {"id":"...","object":"chat.completion.chunk","choices":[{"delta":{"content":" world"}}]}
data: [DONE]
```
