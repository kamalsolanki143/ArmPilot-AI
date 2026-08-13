# Benchmark Pipeline

How benchmarking works from configuration to results.

## Pipeline Overview

```
BenchmarkConfig
     │
     ▼
┌─────────────────┐
│ Validate Config │  Check model exists, params in range
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load Model      │  Load with specified threads/batch
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Warmup Phase    │  Send warmup_requests (default: 3)
│                 │  Discard results
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Benchmark Loop  │  Send num_requests sequentially/concurrently
│                 │  Measure per-request metrics
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Collect System  │  CPU usage, memory, hardware info
│ Metrics         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Compute         │  Percentiles, averages, totals
│ Aggregates      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate        │  Analyze metrics, produce recommendations
│ Recommendations │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Store Result    │  Save to SQLite + JSON
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Result   │  BenchmarkResult with all metrics
└─────────────────┘
```

## Metrics Collected

### Latency

| Metric | Description |
|--------|-------------|
| TTFT | Time to first token (ms) |
| P50 / P75 / P90 / P95 / P99 | Latency percentiles |
| Avg / Min / Max | Average, minimum, maximum latency |

### Throughput

| Metric | Description |
|--------|-------------|
| Tokens/sec | Output tokens per second |
| Requests/sec | Completed requests per second |
| Total tokens | Total tokens generated |
| Duration | Total benchmark duration |

### Resources

| Metric | Description |
|--------|-------------|
| CPU utilization % | Average CPU usage during benchmark |
| Memory (MB) | Current memory usage |
| Memory peak (MB) | Peak memory usage |
| Model size (MB) | Size of the loaded model |

## Benchmark Scenarios

| Scenario | Requests | Concurrency | Max Tokens | Use Case |
|----------|----------|-------------|------------|----------|
| `quick_check` | 5 | 1 | 16 | Sanity check |
| `latency_focused` | 50 | 1 | 32 | Latency measurement |
| `throughput_focused` | 100 | 4 | 128 | Throughput measurement |
| `memory_stress` | 20 | 1 | 512 | Memory profiling |

## Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| TTFT | 200ms | 500ms |
| Throughput | <10 TPS | — |
| P99 Latency | 1000ms | — |
| Memory | 4000MB | — |
| CPU Saturation | 95% | — |

## Output Format

```json
{
  "id": "RUN-0042",
  "status": "completed",
  "config": { "model": "llama-3.2-3b", "threads": 8, ... },
  "ttft_ms": 48.2,
  "tokens_per_second": 34.7,
  "requests_per_second": 1.8,
  "total_tokens": 640,
  "latency": {
    "p50_ms": 62.0,
    "p95_ms": 104.0,
    "p99_ms": 162.0
  },
  "cpu_utilization_percent": 84.0,
  "memory_mb": 3200.0,
  "duration_seconds": 60.0
}
```
