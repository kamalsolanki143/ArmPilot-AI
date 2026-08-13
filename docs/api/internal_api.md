# Internal API Reference

ArmPilot-AI's internal (non-OpenAI) API endpoints for benchmarks, optimization, recommendations, and system management.

## Base URL

```
http://localhost:8000
```

## Authentication

Most internal endpoints are publicly accessible by default. To enable authentication, see [Authentication Guide](authentication.md).

## Benchmark API

### Run Benchmark (Async)

```
POST /api/benchmark/run
```

Start a benchmark in the background. Returns immediately with a pending status.

**Request:**

```json
{
  "config": {
    "model": "llama-3.2-3b",
    "runtime": "llama.cpp",
    "threads": 8,
    "batch_size": 512,
    "concurrency": 1,
    "num_requests": 10,
    "max_tokens": 128,
    "warmup_requests": 3,
    "prompt": "Explain ARM64 architecture benefits."
  }
}
```

**Response:**

```json
{
  "success": true,
  "benchmark_id": "pending",
  "message": "Benchmark started. Poll /api/benchmark/latest for results."
}
```

### Run Benchmark (Sync)

```
POST /api/benchmark/run/sync
```

Run a benchmark synchronously. Blocks until completion.

**Response:**

```json
{
  "success": true,
  "result": {
    "id": "RUN-0042",
    "status": "completed",
    "ttft_ms": 48.2,
    "tokens_per_second": 34.7,
    "latency": { "p50_ms": 62.0, "p95_ms": 104.0, "p99_ms": 162.0 },
    "cpu_utilization_percent": 84.0,
    "memory_mb": 3200.0
  },
  "recommendations": [
    {
      "type": "quantization",
      "current": "FP16",
      "recommended": "Q4_K_M",
      "reasoning": "Reduces memory by 67% with negligible quality loss.",
      "expected_improvement": "+169% throughput"
    }
  ]
}
```

### Get Benchmark Result

```
GET /api/benchmark/{benchmark_id}
```

### Get Latest Benchmark

```
GET /api/benchmark/latest
```

### List All Benchmarks

```
GET /api/benchmarks
```

**Response:**

```json
{
  "success": true,
  "results": [...],
  "total": 42
}
```

## Optimization API

### Run Optimization (Async)

```
POST /api/optimization/run
```

Start an optimization sweep in the background.

**Request:**

```json
{
  "config": {
    "model": "llama-3.2-3b",
    "objective": "throughput",
    "quantization_options": ["FP16", "Q8_0", "Q4_K_M"],
    "batch_sizes": [1, 4, 8, 16],
    "thread_counts": [2, 4, 8],
    "max_candidates": 8,
    "benchmark_per_candidate": 5,
    "max_tokens": 128
  }
}
```

**Response:**

```json
{
  "success": true,
  "optimization_id": "OPT-0001",
  "message": "Optimization started. Poll /api/optimization/{id} for progress."
}
```

### Poll Progress

```
GET /api/optimization/progress
```

**Response:**

```json
{
  "success": true,
  "running": true,
  "progress": 45,
  "current_candidate": "Q4_K_M-B8-T4",
  "candidates_tested": 4,
  "total_candidates": 8
}
```

### Get Optimization Result

```
GET /api/optimization/{opt_id}
```

### List Optimizations

```
GET /api/optimizations
```

## System API

### Health Check

```
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "app": "ArmPilot-AI",
  "version": "0.1.0",
  "model_loaded": true,
  "current_model": "llama-3.2-3b",
  "architecture": "aarch64",
  "is_arm64": true
}
```

### System Metrics

```
GET /api/metrics
```

**Response:**

```json
{
  "success": true,
  "hardware": {
    "architecture": "aarch64",
    "cpu_model": "Neoverse-N1",
    "cpu_count": 64,
    "cpu_count_physical": 64,
    "memory_total_gb": 128.0,
    "is_arm64": true,
    "platform": "linux"
  },
  "system": {
    "cpu_percent": 42.0,
    "memory_used_gb": 12.4,
    "memory_percent": 9.7,
    "load_average": [1.2, 0.8, 0.6]
  },
  "inference": {
    "model_loaded": true,
    "current_model": { "id": "llama-3.2-3b" }
  }
}
```

## WebSocket API

### Live Updates

```
WS /ws
```

Subscribe to real-time events for benchmark progress, optimization progress, and inference status.

**Events:**

```json
{"event": "benchmark_progress", "data": {"progress": 45, "ttft": 52.1}}
{"event": "optimization_progress", "data": {"candidate": "Q4_K_M-B8-T4", "score": 0.87}}
{"event": "inference_status", "data": {"model": "llama-3.2-3b", "status": "generating"}}
```
