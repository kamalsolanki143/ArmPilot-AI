# Throughput Measurement Methodology

How ArmPilot-AI measures, validates, and reports LLM inference throughput on Arm Neoverse platforms.

## Definitions

### Output Throughput (TPS)

Tokens generated per second during the decode phase. This is the primary throughput metric for user-facing inference.

### Prompt Throughput (Prompt TPS)

Tokens processed per second during the prefill phase. Relevant for long-context workloads where prefill dominates total latency.

### Sustained Throughput

TPS measured over a fixed window (default 60 seconds) under constant load, excluding warmup. Captures steady-state performance including batching, scheduling, and memory effects.

## Measurement Architecture

```
┌─────────────────────────────────────────────────┐
│                  Benchmark Driver                │
│  ┌───────────┐  ┌───────────┐  ┌─────────────┐ │
│  │ Request    │  │ Response  │  │ Metric      │ │
│  │ Generator  │  │ Collector │  │ Aggregator  │ │
│  └─────┬─────┘  └─────┬─────┘  └──────┬──────┘ │
│        │               │               │         │
│  ┌─────▼───────────────▼───────────────▼──────┐ │
│  │           Timestamp Collector               │ │
│  │  (CLOCK_MONOTONIC_RAW, 1μs resolution)     │ │
│  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## Measurement Protocol

### Phase 1: Warmup

Run 10 inference requests (excluded from measurements) to stabilize:
- JIT compiled kernels (llama.cpp, vLLM custom ops)
- CPU cache state (L1/L2/L3 populated with model weights)
- Memory allocator state (jemalloc/tcmalloc arenas warmed)
- OS page cache

```python
import time
import statistics

class ThroughputBenchmark:
    def __init__(self, client, config):
        self.client = client
        self.warmup_samples = config.get("warmup_samples", 10)
        self.min_duration_s = config.get("min_measurement_duration_s", 60)
        self.collection_interval_ms = config.get("collection_interval_ms", 100)
    
    def warmup(self, prompt: str, max_tokens: int):
        for _ in range(self.warmup_samples):
            self.client.generate(prompt, max_tokens=max_tokens)
```

### Phase 2: Steady-State Measurement

Collect throughput data over the minimum measurement window with a fixed request rate.

```python
def measure_throughput(self, prompt: str, max_tokens: int) -> dict:
    results = []
    start_time = time.monotonic_ns()
    
    while (time.monotonic_ns() - start_time) < self.min_duration_s * 1e9:
        request_start = time.monotonic_ns()
        
        response = self.client.generate(
            prompt, 
            max_tokens=max_tokens,
            stream=True
        )
        
        token_count = 0
        first_token_time = None
        
        for token in response:
            current_time = time.monotonic_ns()
            token_count += 1
            if first_token_time is None:
                first_token_time = current_time
        
        request_end = time.monotonic_ns()
        
        decode_duration_s = (request_end - first_token_time) / 1e9
        output_tps = (token_count - 1) / decode_duration_s if decode_duration_s > 0 else 0
        
        results.append({
            "output_tokens": token_count,
            "decode_duration_s": decode_duration_s,
            "output_tps": output_tps,
            "total_latency_s": (request_end - request_start) / 1e9,
        })
    
    return self._aggregate(results)
```

### Phase 3: Aggregation

Compute summary statistics from per-request measurements.

```python
def _aggregate(self, results: list) -> dict:
    tps_values = [r["output_tps"] for r in results]
    latencies = [r["total_latency_s"] for r in results]
    
    return {
        "output_tps": {
            "mean": statistics.mean(tps_values),
            "median": statistics.median(tps_values),
            "stdev": statistics.stdev(tps_values) if len(tps_values) > 1 else 0,
            "min": min(tps_values),
            "max": max(tps_values),
            "p5": sorted(tps_values)[int(len(tps_values) * 0.05)],
            "p95": sorted(tps_values)[int(len(tps_values) * 0.95)],
        },
        "total_requests": len(results),
        "total_output_tokens": sum(r["output_tokens"] for r in results),
        "avg_latency_s": statistics.mean(latencies),
        "sustained_tps": sum(r["output_tokens"] for r in results) / sum(r["decode_duration_s"] for r in results),
    }
```

## Concurrent Throughput Measurement

For production-like scenarios, measure aggregate throughput under concurrent load.

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def measure_concurrent_throughput(
    client, 
    prompt: str, 
    max_tokens: int,
    concurrency: int,
    duration_s: int,
) -> dict:
    semaphore = asyncio.Semaphore(concurrency)
    results = []
    stop_event = asyncio.Event()
    
    async def worker():
        while not stop_event.is_set():
            async with semaphore:
                start = time.monotonic_ns()
                response = await client.async_generate(
                    prompt, max_tokens=max_tokens
                )
                end = time.monotonic_ns()
                results.append({
                    "tokens": response.token_count,
                    "latency_s": (end - start) / 1e9,
                })
    
    tasks = [asyncio.create_task(worker()) for _ in range(concurrency)]
    
    await asyncio.sleep(duration_s)
    stop_event.set()
    await asyncio.gather(*tasks)
    
    total_tokens = sum(r["tokens"] for r in results)
    total_time = sum(r["latency_s"] for r in results)
    
    return {
        "concurrency": concurrency,
        "aggregate_tps": total_tokens / duration_s,
        "avg_per_request_tps": total_tokens / total_time,
        "total_requests": len(results),
    }
```

## Arm-Specific Throughput Considerations

### Core Affinity

Bind inference threads to specific cores to avoid scheduler noise:

```bash
# Pin inference process to cores 4-7 (performance cores on Graviton3)
taskset -c 4-7 python benchmark.py --model llama-3-8b

# Or use cgroup cpuset
echo "4-7" > /sys/fs/cgroup/benchmark/cpuset.cpus
```

### Memory Channel Saturation

Arm Neoverse memory bandwidth varies by platform:

| Platform | Channels | Peak BW (GB/s) | TPS Sweet Spot |
|----------|----------|-----------------|----------------|
| Graviton3 | 8 | 307 | 2-4 concurrent |
| Graviton4 | 8 | 307 | 2-4 concurrent |
| Cobalt 100 | 8 | 307 | 2-4 concurrent |
| Axion | 8 | 307 | 2-4 concurrent |

Exceeding the sweet spot increases memory contention without proportional TPS gains.

### NUMA Awareness

On multi-socket Arm systems, pin threads to the same NUMA node as the model weights:

```bash
# Check NUMA topology
numactl --hardware

# Run on NUMA node 0
numactl --cpunodebind=0 --membind=0 python benchmark.py
```

### Quantization Impact on Throughput

| Quantization | Model Size | TPS (Graviton3, 1 instance) | TTFT (ms) |
|-------------|-----------|----------------------------|-----------|
| FP16 | 16 GB | 28 | 180 |
| Q8_0 | 8.5 GB | 38 | 140 |
| Q4_K_M | 4.9 GB | 52 | 105 |
| Q3_K_M | 3.8 GB | 61 | 90 |
| Q2_K | 3.0 GB | 68 | 82 |

## Validation Checklist

Before reporting throughput numbers, verify:

1. **Warmup complete**: First 10+ requests excluded from measurement
2. **Steady state**: TPS coefficient of variation < 10% across the measurement window
3. **No OOM**: Peak RSS stayed below available memory
4. **Clock source**: Using `CLOCK_MONOTONIC_RAW` (not `CLOCK_MONOTONIC` which is NTP-adjusted)
5. **No thermal throttling**: CPU frequency stable throughout measurement (check via `cpupower frequency-info`)
6. **Consistent prompt**: Same prompt template used across all runs for comparability
7. **Model weights loaded**: No page faults during measurement phase

## Common Pitfalls

### Reporting Prefill TPS as Decode TPS

Prefill is 10-30x faster than decode in tokens/second. Always report decode TPS as the primary throughput metric.

### Ignoring Token Counting Differences

Different tokenizers produce different token counts for the same text. When comparing across models, normalize by character count or report tokenizer details.

### Measuring Single-Request Throughput

Single-request TPS reflects the model's sequential generation speed. Production throughput depends on batching and concurrency. Report both.

### Temperature and Sampling Effects

High temperature or top-p sampling adds negligible overhead but changes output length. Fix sampling parameters (`temperature=0.0`) for reproducible throughput measurements.
