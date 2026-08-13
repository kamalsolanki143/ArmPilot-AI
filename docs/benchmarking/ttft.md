# Time-to-First-Token (TTFT) Measurement

TTFT is the most critical latency metric for interactive LLM applications. This document covers measurement methodology, the components that contribute to TTFT, and Arm-specific optimization considerations.

## Definition

```
TTFT = first_token_emission_timestamp - request_submission_timestamp
```

TTFT encompasses all processing from the moment a user's prompt enters the inference pipeline until the first output token is streamed back.

## TTFT Component Breakdown

```
┌─────────────────────────────────────────────────────────────┐
│                        TTFT                                  │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Network  │  │ Tokenize │  │ Prefill  │  │  Decode    │ │
│  │ Overhead │  │ + Batch  │  │ (input   │  │  (first    │ │
│  │          │  │ Prepare  │  │  tokens) │  │   token)   │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │
│     1-5ms        1-10ms       50-500ms        15-30ms       │
└─────────────────────────────────────────────────────────────┘
```

| Component | Typical Range | Bottleneck Type |
|-----------|--------------|-----------------|
| Network/IPC overhead | 1-5 ms | System |
| Tokenization | 1-10 ms | CPU |
| Batch preparation | 1-5 ms | CPU |
| Prefill (attention) | 50-500 ms | Compute (CPU/GPU) |
| First token decode | 15-30 ms | Memory bandwidth |
| Streaming overhead | 1-2 ms | System |

## Measurement Implementation

### Streaming Inference Measurement

The most accurate TTFT measurement uses streaming mode, capturing the timestamp at first token yield:

```python
import time
import httpx

class TTFTMeasurer:
    """Measures TTFT via streaming API with high-resolution timestamps."""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
        self.clock_source = "CLOCK_MONOTONIC_RAW"
    
    def measure_ttft(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.0,
    ) -> dict:
        """Measure TTFT for a single request using streaming.
        
        Returns dict with ttft_ms, first_token_text, and raw timestamps.
        """
        request_start = time.monotonic_ns()
        first_token_received = False
        ttft_ns = None
        first_token_text = ""
        token_count = 0
        
        with httpx.stream(
            "POST",
            f"{self.api_url}/v1/chat/completions",
            json={
                "model": "local",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            },
            timeout=60.0,
        ) as response:
            for line in response.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                
                data = line[6:]  # Strip "data: " prefix
                if data.strip() == "[DONE]":
                    break
                
                import json
                chunk = json.loads(data)
                
                if chunk["choices"][0]["delta"].get("content"):
                    if not first_token_received:
                        ttft_ns = time.monotonic_ns()
                        first_token_received = True
                        first_token_text = chunk["choices"][0]["delta"]["content"]
                    token_count += 1
        
        if not first_token_received:
            raise TimeoutError("No tokens received within timeout")
        
        return {
            "ttft_ms": (ttft_ns - request_start) / 1e6,
            "first_token": first_token_text,
            "total_tokens": token_count,
            "request_start_ns": request_start,
            "first_token_ns": ttft_ns,
        }
```

### Non-Streaming Measurement

For non-streaming endpoints, TTFT must be estimated by subtracting decode time from total latency:

```python
def estimate_ttft_non_streaming(
    total_latency_ms: float,
    output_tokens: int,
    tpot_ms: float,
) -> float:
    """Estimate TTFT from non-streaming response.
    
    TTFT ≈ Total Latency - (TPOT × output_tokens)
    Note: This is an approximation; streaming measurement is preferred.
    """
    decode_time_ms = tpot_ms * output_tokens
    return total_latency_ms - decode_time_ms
```

### High-Precision Measurement with C Extension

For sub-millisecond precision, use a C extension with `clock_gettime`:

```c
// ttft_clock.c - High-precision timestamp capture
#include <time.h>
#include <stdint.h>

#define CLOCK_MONOTONIC_RAW 4

typedef struct {
    int64_t seconds;
    int64_t nanoseconds;
} Timestamp;

Timestamp get_timestamp(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC_RAW, &ts);
    Timestamp result;
    result.seconds = ts.tv_sec;
    result.nanoseconds = ts.tv_nsec;
    return result;
}

int64_t timestamp_diff_ns(Timestamp start, Timestamp end) {
    int64_t diff_sec = end.seconds - start.seconds;
    int64_t diff_ns = end.nanoseconds - start.nanoseconds;
    return diff_sec * 1000000000LL + diff_ns;
}
```

```python
# Python binding
import ctypes

_ttft_lib = ctypes.CDLL("./ttft_clock.so")
_ttft_lib.get_timestamp.restype = ctypes.c_int64 * 2
_ttft_lib.timestamp_diff_ns.argtypes = [ctypes.c_int64 * 2, ctypes.c_int64 * 2]
_ttft_lib.timestamp_diff_ns.restype = ctypes.c_int64

def get_timestamp_ns() -> int:
    ts = _ttft_lib.get_timestamp()
    return ts[0] * 1_000_000_000 + ts[1]

def timestamp_diff_ms(start_ns: int, end_ns: int) -> float:
    return (end_ns - start_ns) / 1e6
```

## TTFT Distribution Analysis

### Reporting Percentiles

```python
def ttft_report(ttft_values: list[float]) -> dict:
    """Generate TTFT distribution report."""
    sorted_vals = sorted(ttft_values)
    n = len(sorted_vals)
    
    return {
        "count": n,
        "mean_ms": statistics.mean(sorted_vals),
        "median_ms": statistics.median(sorted_vals),
        "stdev_ms": statistics.stdev(sorted_vals) if n > 1 else 0,
        "min_ms": sorted_vals[0],
        "max_ms": sorted_vals[-1],
        "p50_ms": sorted_vals[int(n * 0.50)],
        "p90_ms": sorted_vals[int(n * 0.90)],
        "p95_ms": sorted_vals[int(n * 0.95)],
        "p99_ms": sorted_vals[int(n * 0.99)],
        "p999_ms": sorted_vals[min(int(n * 0.999), n-1)],
    }
```

### TTFT vs Input Length Relationship

TTFT scales linearly with input token count during the prefill phase:

```
TTFT ≈ prefill_base + (tokens_per_input × input_token_count)
```

Measure at multiple input lengths to characterize:

```python
def ttft_scaling_analysis(client, prompt_generator, input_lengths):
    """Measure TTFT scaling across input lengths."""
    results = []
    
    for length in input_lengths:
        prompt = prompt_generator(target_tokens=length)
        measurements = [client.measure_ttft(prompt) for _ in range(10)]
        ttft_values = [m["ttft_ms"] for m in measurements]
        
        results.append({
            "input_tokens": length,
            "ttft_mean_ms": statistics.mean(ttft_values),
            "ttft_p95_ms": sorted(ttft_values)[int(len(ttft_values) * 0.95)],
            "ttft_stdev_ms": statistics.stdev(ttft_values),
        })
    
    return results
```

## Arm-Specific TTFT Optimization

### Prefill Compute on Arm NEON

The prefill phase processes all input tokens in parallel through the attention mechanism. On Arm Neoverse:

```c
// NEON-optimized attention prefill (simplified)
// Processes 4 float32 values per cycle with FMLA
void attention_prefill_neon(
    const float* queries,    // [seq_len, head_dim]
    const float* keys,       // [seq_len, head_dim]
    const float* values,     // [seq_len, head_dim]
    float* output,           // [seq_len, head_dim]
    int seq_len,
    int head_dim
) {
    for (int i = 0; i < seq_len; i++) {
        float32x4_t acc = vdupq_n_f32(0.0f);
        for (int j = 0; j < head_dim; j += 4) {
            float32x4_t q = vld1q_f32(&queries[i * head_dim + j]);
            float32x4_t k = vld1q_f32(&keys[i * head_dim + j]);
            acc = vfmaq_f32(acc, q, k);  // Fused multiply-accumulate
        }
        // Reduction and softmax...
    }
}
```

### SVE2 Optimization for Longer Sequences

For sequences >512 tokens, SVE2's variable-length vectors provide better utilization:

```c
// SVE2 attention with variable vector length
void attention_prefill_sve2(
    const float* queries,
    const float* keys, 
    const float* values,
    float* output,
    int seq_len,
    int head_dim
) {
    // SVE automatically uses 128-256 bit vectors based on hardware
    for (int i = 0; i < seq_len; i++) {
        svbool_t pg = svptrue_b32();
        svfloat32_t acc = svdup_f32(0.0f);
        
        for (int j = 0; j < head_dim; j += svcntw()) {
            svfloat32_t q = svld1(pg, &queries[i * head_dim + j]);
            svfloat32_t k = svld1(pg, &keys[i * head_dim + j]);
            acc = svmla(pg, acc, q, k);
        }
        // Horizontal reduction and softmax...
    }
}
```

### Quantized Prefill

INT8 quantization of the prefill computation reduces TTFT by ~40% on Arm:

```python
# Quantized attention prefill configuration
quantized_prefill_config = {
    "quantize_weights": "int8",
    "quantize_activations": "int8",
    "dequantize_output": "fp16",
    "expected_ttft_reduction": "35-45%",
    "arm_specific": {
        "use_sme": True,  # Arm Scalable Matrix Extension for matrix ops
        "use_sve": True,
        "vector_length": "auto",
    }
}
```

### Batch Prefill

Process multiple requests' prefill phases simultaneously to amortize memory bandwidth:

```python
def batched_prefill_ttft(prompts: list[str], batch_size: int = 4) -> list[float]:
    """Measure TTFT with batched prefill.
    
    Batching increases prefill throughput but may increase individual TTFT
    due to memory contention. Optimal batch size depends on model size
    and available memory bandwidth.
    """
    ttft_values = []
    
    for i in range(0, len(prompts), batch_size):
        batch = prompts[i:i+batch_size]
        batch_start = time.monotonic_ns()
        
        # Process entire batch through prefill
        prefill_results = model.batch_prefill(batch)
        
        batch_end = time.monotonic_ns()
        batch_ttft = (batch_end - batch_start) / 1e6
        
        # Individual TTFT within batch (all complete at batch end)
        for _ in batch:
            ttft_values.append(batch_ttft)
    
    return ttft_values
```

## TTFT Benchmarks on Arm Platforms

| Platform | Model | Quant | Input Tokens | TTFT (ms) |
|----------|-------|-------|-------------|-----------|
| Graviton3 | Llama-3-8B | Q4_K_M | 128 | 85 |
| Graviton3 | Llama-3-8B | Q4_K_M | 512 | 210 |
| Graviton3 | Llama-3-8B | Q4_K_M | 2048 | 680 |
| Graviton4 | Llama-3-8B | Q4_K_M | 128 | 62 |
| Graviton4 | Llama-3-8B | Q4_K_M | 512 | 155 |
| Graviton4 | Llama-3-8B | Q4_K_M | 2048 | 490 |
| Cobalt 100 | Llama-3-8B | Q4_K_M | 128 | 68 |
| Axion | Llama-3-8B | Q4_K_M | 128 | 72 |

## Validation

### Correctness Check

Verify TTFT measurement accuracy by comparing with expected prefill time:

```python
def validate_ttft_measurement(ttft_ms, input_tokens, model_config):
    """Validate that measured TTFT is physically plausible."""
    # Minimum possible TTFT: at least 1 compute cycle per token
    min_ttft_ms = input_tokens * 0.001  # 1μs per token minimum
    
    # Maximum reasonable TTFT: 1 second per 1000 tokens (very conservative)
    max_ttft_ms = input_tokens * 1.0
    
    if ttft_ms < min_ttft_ms:
        raise ValueError(f"TTFT {ttft_ms}ms too fast for {input_tokens} tokens")
    if ttft_ms > max_ttft_ms:
        raise ValueError(f"TTFT {ttft_ms}ms unreasonably slow for {input_tokens} tokens")
    
    return True
```

### Instrumentation Overhead

The measurement overhead should be < 0.1ms (100μs) for TTFT to be meaningful:

```python
# Measure instrumentation overhead
overhead_samples = []
for _ in range(1000):
    start = time.monotonic_ns()
    # Simulate token reception (no actual inference)
    time.sleep(0)
    end = time.monotonic_ns()
    overhead_samples.append((end - start) / 1e6)

print(f"Measurement overhead: {statistics.mean(overhead_samples):.3f}ms")
# Should be < 0.01ms
```
