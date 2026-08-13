# Benchmark Metrics Reference

Complete definitions for every metric collected during LLM inference benchmarking on Arm Neoverse platforms.

## Overview

ArmPilot-AI measures inference performance across five dimensions: throughput, latency, time-to-first-token, memory, and compute utilization. Each metric is collected via a combination of application-level timestamps and hardware performance counters exposed through Arm Statistical Profiling Extension (SPE) and perf events.

All metrics are reported with 95% confidence intervals unless otherwise noted. Measurements are taken after a 10-sample warmup phase to exclude cold-start effects such as model loading, weight dequantization, and JIT compilation.

## Throughput Metrics

### Tokens Per Second (TPS)

The number of output tokens generated per second during the decode phase. This is the primary throughput metric for autoregressive LLM inference.

```
TPS = output_token_count / decode_duration_seconds
```

- **Scope**: Measured per-request and aggregated across concurrent requests
- **Unit**: tokens/second
- **Collection**: Application-level counter incremented on each token emission
- **Arm consideration**: TPS scales non-linearly with core count on Neoverse due to shared L3 cache contention. Report TPS at the optimal concurrency level for the target platform (typically 1-4 concurrent requests on Graviton3).

### Prompt Tokens Per Second

The number of input tokens processed per second during the prefill phase.

```
prompt_tps = input_token_count / prefill_duration_seconds
```

- **Scope**: Per-request, during prefill only
- **Unit**: tokens/second
- **Collection**: Application-level counter on prompt processing completion
- **Arm consideration**: Prefill is compute-bound on Arm NEON/SVE pipelines. This metric correlates strongly with FLOPS utilization.

### Sustained Throughput

Throughput measured over a 60-second window under constant load, excluding the first 10 seconds (warmup).

```
sustained_tps = total_output_tokens / (measurement_end - measurement_start)
```

- **Scope**: System-level, all concurrent requests
- **Unit**: tokens/second
- **Collection**: Aggregated from per-request counters over the measurement window

## Latency Metrics

### Time to First Token (TTFT)

Elapsed time from prompt submission to the emission of the first output token. See `ttft.md` for detailed measurement methodology.

```
TTFT = first_token_timestamp - request_submission_timestamp
```

- **Scope**: Per-request
- **Unit**: milliseconds
- **Collection**: High-resolution monotonic clock (CLOCK_MONOTONIC) at request entry and first token yield
- **Arm consideration**: TTFT is dominated by prefill compute. On Neoverse V2, SVE2 vectorization of the attention prefill reduces TTFT by 30-40% compared to scalar implementations.

### Inter-Token Latency (ITL)

Average time between consecutive output tokens during the decode phase.

```
ITL = (last_token_timestamp - first_token_timestamp) / (output_token_count - 1)
```

- **Scope**: Per-request
- **Unit**: milliseconds
- **Collection**: Timestamps at each token emission, averaged over the decode phase

### Time Per Output Token (TPOT)

The average decode time for a single token, including KV-cache attention computation and sampling.

```
TPOT = decode_duration / output_token_count
```

- **Scope**: Per-request
- **Unit**: milliseconds
- **Collection**: Decode phase duration divided by output token count

### Total Request Latency

End-to-end time from request submission to response completion.

```
total_latency = TTFT + (TPOT * output_token_count)
```

- **Scope**: Per-request
- **Unit**: milliseconds
- **Collection**: Difference between request submission and response completion timestamps

### Latency Percentiles

Aggregate latency distributions across all requests in a measurement window.

| Percentile | Description | Target (Interactive) | Target (Batch) |
|------------|-------------|---------------------|----------------|
| P50        | Median latency | < 500ms | < 5000ms |
| P90        | 90th percentile | < 1500ms | < 15000ms |
| P95        | 95th percentile | < 2500ms | < 25000ms |
| P99        | 99th percentile | < 5000ms | < 50000ms |

- **Collection**: All request latencies collected, sorted, and interpolated at each percentile boundary
- **Arm consideration**: P99 outliers on Arm servers often correlate with NUMA node crossings or background OS interrupts. Isolate benchmark cores using `taskset` or cgroup cpuset to reduce variance.

## Memory Metrics

### Peak RSS (Resident Set Size)

Maximum physical memory consumed by the inference process during the benchmark run.

```
peak_rss = max(/proc/[pid]/status VmRSS samples)
```

- **Scope**: Process-level
- **Unit**: Megabytes (MB)
- **Collection**: Periodic sampling at 100ms intervals via `/proc/self/status` or `getrusage()`
- **Arm consideration**: On Neoverse with 64KB pages, RSS includes page table overhead not present with 4KB pages. Report page size alongside RSS.

### Working Set Size

Memory accessed during a representative inference window, excluding cold pages.

```
working_set = pages_touched during measurement window * page_size
```

- **Scope**: Process-level
- **Unit**: Megabytes (MB)
- **Collection**: Via `mincore()` or `/proc/[pid]/smaps` sampling

### KV-Cache Memory

Memory consumed by the key-value cache for the current context.

```
kv_cache_bytes = 2 * num_layers * num_heads * head_dim * context_length * dtype_size
```

- **Scope**: Model-level
- **Unit**: Megabytes (MB)
- **Collection**: Computed from model configuration and measured context length
- **Arm consideration**: BF16 weights on Arm SVE use 2 bytes per element. KV-cache memory is the primary scaling bottleneck for long-context inference.

### GPU Memory Utilization

If using discrete accelerators alongside Arm CPUs, measure GPU memory utilization.

```
gpu_mem_util = gpu_used_memory / gpu_total_memory * 100
```

- **Scope**: Device-level
- **Unit**: Percentage
- **Collection**: `nvidia-smi` or vendor-specific APIs

## CPU Utilization Metrics

### Core Utilization

Percentage of time CPU cores spend executing inference code (excluding idle, iowait, and system).

```
core_util = inference_cycles / total_cycles * 100
```

- **Scope**: Per-core and aggregate
- **Unit**: Percentage
- **Collection**: `/proc/stat` or perf event `cpu-cycles`

### SIMD Utilization

Ratio of NEON/SVE/SVE2 instructions to total instructions executed.

```
simd_ratio = simd_instructions / total_instructions * 100
```

- **Scope**: Process-level aggregate
- **Unit**: Percentage
- **Collection**: Arm SPE sampling or perf `inst-retired` with SIMD filter
- **Arm consideration**: Target >70% SIMD utilization for inference kernels. Low SIMD ratio indicates scalar bottlenecks that can be vectorized.

### Memory Bandwidth Utilization

Achieved memory bandwidth as a percentage of theoretical peak.

```
mem_bw_util = achieved_bandwidth / peak_bandwidth * 100
```

- **Scope**: System-level
- **Unit**: Percentage
- **Collection**: perf `arm_spe_0/ts_enable=1,load_filter=1,store_filter=1` or `likwid`

### Cache Hit Ratios

L1, L2, and L3 cache hit rates during inference.

```
cache_hit_ratio = cache_hits / (cache_hits + cache_misses) * 100
```

- **Scope**: Per-cache-level
- **Unit**: Percentage
- **Collection**: perf cache-miss events or Arm SPE
- **Arm consideration**: L3 hit ratio is critical for multi-threaded inference. On Neoverse N2, a 10% drop in L3 hit ratio can reduce TPS by 15-20%.

## Composite Metrics

### Inference Efficiency Score

A weighted composite score combining throughput, latency, and resource utilization.

```
efficiency = (0.4 * normalized_tps) + (0.3 * (1 - normalized_p99)) + (0.3 * core_util / 100)
```

- **Scope**: Run-level
- **Unit**: Dimensionless (0-1)
- **Collection**: Computed from component metrics after normalization

### Cost Per Million Tokens

Infrastructure cost normalized to output volume.

```
cost_per_mtoken = hourly_instance_cost / (sustained_tps * 3600 / 1_000_000)
```

- **Scope**: Run-level
- **Unit**: USD per million tokens
- **Collection**: Computed from sustained TPS and instance pricing

## Metric Collection Configuration

```yaml
# configs/benchmark.yaml
metrics:
  collection_interval_ms: 100
  warmup_samples: 10
  min_measurement_duration_s: 60
  clock_source: CLOCK_MONOTONIC_RAW
  
  throughput:
    measure_prompt_tps: true
    measure_output_tps: true
    measure_sustained: true
    sustained_window_s: 60
  
  latency:
    percentiles: [50, 90, 95, 99]
    measure_ttft: true
    measure_itl: true
    measure_tpot: true
  
  memory:
    sample_interval_ms: 100
    track_kv_cache: true
    track_working_set: true
  
  cpu:
    track_core_util: true
    track_simd_util: true
    track_cache_hits: true
    track_memory_bandwidth: true
```

## Reporting Format

All metrics are exported in JSON with the following structure:

```json
{
  "benchmark_id": "run_20260813_001",
  "platform": {
    "cpu": "Neoverse-V2",
    "cores": 8,
    "memory_gb": 32,
    "page_size_kb": 64
  },
  "model": {
    "name": "llama-3-8b-instruct",
    "quantization": "Q4_K_M",
    "parameters_b": 8.0
  },
  "metrics": {
    "throughput": {
      "prompt_tps": 1250.3,
      "output_tps": 42.7,
      "sustained_tps": 41.2
    },
    "latency": {
      "ttft_ms": 125.4,
      "itl_ms": 23.4,
      "tpot_ms": 23.4,
      "p50_ms": 1890.2,
      "p95_ms": 2340.1,
      "p99_ms": 4120.5
    },
    "memory": {
      "peak_rss_mb": 5840,
      "kv_cache_mb": 2048,
      "working_set_mb": 4200
    },
    "cpu": {
      "core_util_pct": 87.3,
      "simd_util_pct": 72.1,
      "l3_cache_hit_pct": 94.2,
      "mem_bw_util_pct": 68.5
    },
    "composite": {
      "efficiency_score": 0.82,
      "cost_per_mtoken_usd": 0.0042
    }
  },
  "confidence_intervals": {
    "level": 0.95,
    "output_tps_ci": [40.8, 43.6],
    "ttft_ms_ci": [118.2, 132.6]
  }
}
```

## References

- [Arm Topdown Methodology](https://developer.arm.com/documentation/109542/0100/)
- [Arm SPE Documentation](https://developer.arm.com/documentation/101378/latest/)
- [Arm Neoverse Performance Analysis Guide](https://developer.arm.com/documentation/PJDOC-466751330-590883/latest/)
- [MLPerf Inference Benchmark](https://mlcommons.org/benchmarks/inference/)
