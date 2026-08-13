# Batch Size Optimization for Arm64 LLM Inference

## Overview

Batching groups multiple inference requests or tokens together to
improve hardware utilization. For LLM inference on Arm64, batch size
selection involves a three-way trade-off between throughput, latency,
and memory bandwidth. This guide covers batch size optimization for
both pre-fill and decode phases.

---

## Batching Phases

### Pre-Fill Batching

Pre-fill processes all prompt tokens simultaneously. The batch dimension
is the number of tokens in the prompt (or chunk of a long prompt):

```
Input shape: [batch=1, seq_len=2048, hidden=4096]
GEMM shape:  [2048, 4096] × [4096, 4096] = [2048, 4096]
```

Large pre-fill batches saturate compute units efficiently because the
matrix dimensions are large enough to use all SIMD lanes.

### Decode Batching

Decode generates one token per request. Batching groups multiple
requests processed in parallel:

```
Input shape: [batch=4, seq_len=1, hidden=4096]
GEMM shape:  [4, 4096] × [4096, 4096] = [4, 4096]
```

Decode batches are small, making the workload memory-bandwidth-bound.

---

## Memory Bandwidth Analysis

### The Bandwidth Equation

For each forward pass, the model reads all weights from memory:

```
Bytes_read = 2 × n_params × bytes_per_weight
Tokens_per_second = Memory_BW / Bytes_read
```

For a 7B parameter model:

| Precision | Bytes/Weight | Total Read | At 50 GB/s | At 200 GB/s |
|-----------|-------------|------------|------------|-------------|
| FP32      | 4           | 28 GB      | 0.57 tok/s | 2.28 tok/s |
| FP16      | 2           | 14 GB      | 1.14 tok/s | 4.57 tok/s |
| INT8      | 1           | 7 GB       | 2.28 tok/s | 9.14 tok/s |
| INT4      | 0.5         | 3.5 GB     | 4.57 tok/s | 18.28 tok/s |

**Critical observation**: For decode, throughput is almost entirely
determined by memory bandwidth, not batch size. Increasing batch size
from 1 to 4 multiplies throughput by ~4x only if memory bandwidth
is not saturated.

### Bandwidth Saturation Point

```
Max_useful_batch = Memory_BW / (Bytes_per_token × Latency_budget)
```

For a 50 GB/s device with 3.5 GB weight read per token:
- Single token: 140 ms per token
- Batch of 4: 560 ms for 4 tokens = 140 ms/token (no improvement)
- Batch of 8: 1120 ms for 8 tokens = 140 ms/token (bandwidth saturated)

Beyond the saturation point, batch size only increases latency without
improving per-token throughput.

---

## Continuous Batching

### Static vs Continuous

**Static batching**: All requests in a batch must complete before the
next batch starts. Wastes compute when requests have different lengths.

**Continuous batching**: New requests join the batch as others complete.
Also called "in-flight batching" or "iteration-level scheduling."

```
Time ──────────────────────────────────────────────►

Static:
  [Req A, Req B, Req C] ──── wait ──── [Req D, Req E]

Continuous:
  [Req A, Req B, Req C]
  [Req A, Req B, Req D]  ← C finished, D joins
  [Req A, Req E, Req D]  ← B finished, E joins
```

### Implementation

```c
typedef struct {
    int64_t request_id;
    int seq_len;
    int max_tokens;
    bool is_active;
    float *kv_cache;
} batch_entry_t;

typedef struct {
    batch_entry_t entries[MAX_BATCH_SIZE];
    int active_count;
    int max_batch_size;
} continuous_batch_t;

void continuous_batch_add(continuous_batch_t *batch, int64_t req_id,
                          int max_tokens) {
    for (int i = 0; i < batch->max_batch_size; i++) {
        if (!batch->entries[i].is_active) {
            batch->entries[i] = (batch_entry_t){
                .request_id = req_id,
                .seq_len = 0,
                .max_tokens = max_tokens,
                .is_active = true,
                .kv_cache = allocate_kv_cache(max_tokens),
            };
            batch->active_count++;
            return;
        }
    }
    // Batch full — queue the request
    queue_push(&pending_queue, req_id);
}

void continuous_batch_step(continuous_batch_t *batch, llm_model_t *model) {
    int n_active = 0;
    int active_indices[MAX_BATCH_SIZE];

    for (int i = 0; i < batch->max_batch_size; i++) {
        if (batch->entries[i].is_active) {
            active_indices[n_active++] = i;
        }
    }

    if (n_active == 0) return;

    // Run forward pass for active requests only
    forward_batch(model, batch->entries, active_indices, n_active);

    // Check which requests completed
    for (int i = 0; i < batch->max_batch_size; i++) {
        if (batch->entries[i].is_active &&
            batch->entries[i].seq_len >= batch->entries[i].max_tokens) {
            batch->entries[i].is_active = false;
            batch->active_count--;
            free_kv_cache(batch->entries[i].kv_cache);

            // Replace with pending request if available
            int64_t new_req;
            if (queue_pop(&pending_queue, &new_req)) {
                continuous_batch_add(batch, new_req, DEFAULT_MAX_TOKENS);
            }
        }
    }
}
```

---

## Batch Size Selection

### For Single-User (Interactive)

| Metric              | Target           | Batch Size |
|---------------------|------------------|------------|
| Time-to-first-token | < 200ms          | 1-2        |
| Inter-token latency | < 50ms           | 1          |
| Throughput          | N/A (single user)| 1          |

Interactive use requires minimal batch size for lowest latency.

### For Multi-User (Serving)

| Concurrent Users | Batch Size | Throughput (tok/s) | Latency (ms/tok) |
|------------------|------------|--------------------|--------------------|
| 1                | 1          | 18                 | 55                 |
| 4                | 4          | 65                 | 62                 |
| 8                | 8          | 110                | 73                 |
| 16               | 16         | 140                | 114                |
| 32               | 32         | 155                | 206                |

*Estimated for 7B INT4 on Snapdragon 8 Gen 3 (50 GB/s)*

**Optimal point**: Batch size 8-16 maximizes throughput while keeping
per-token latency under 100ms.

### Adaptive Batch Sizing

Dynamically adjust batch size based on current load:

```c
int compute_optimal_batch_size(inference_state_t *state) {
    float current_bandwidth_util = state->bw_measured / state->bw_max;
    int current_queue_depth = queue_length(&pending_queue);

    if (current_bandwidth_util > 0.85) {
        // Bandwidth saturated — don't add more requests
        return state->current_batch_size;
    }

    if (current_queue_depth > state->current_batch_size * 2) {
        // Long queue — increase batch size
        return MIN(state->current_batch_size + 2, MAX_BATCH_SIZE);
    }

    if (current_queue_depth < state->current_batch_size / 2) {
        // Short queue — decrease batch size for lower latency
        return MAX(state->current_batch_size - 1, 1);
    }

    return state->current_batch_size;
}
```

---

## Arm64-Specific Batch Considerations

### SIMD Utilization

NEON processes 16 INT8 elements or 8 FP16 elements per instruction.
Batch sizes that are multiples of these widths avoid partial-register
penalties:

```
Optimal batch sizes for NEON:
  INT8:  4, 8, 16, 32
  FP16:  2, 4, 8, 16
  FP32:  1, 2, 4, 8
```

### SVE Variable-Length Vectors

On Arm v9 with SVE, the hardware vector length is unknown at compile
time. The batch dimension should be independent of vector length:

```c
// SVE-agnostic batch processing
void process_batch_sve(float *input, float *output, int batch_size) {
    svbool_t predicate = svwhilelt_b32(0, batch_size);
    while (svptest_any(svptrue_b32(), predicate)) {
        svfloat32_t data = svld1_f32(predicate, input);
        svfloat32_t result = process(data);
        svst1_f32(predicate, output, result);
        predicate = svwhilelt_b32(0, batch_size);
    }
}
```

### L3 Cache Pressure

Large batch sizes cause weight data to be evicted from L3 cache.
For Arm64 devices with 4-8 MB L3 cache:

```
Max batch before L3 thrashing = L3_size / weight_per_token
  7B INT4: 8 MB / 3.5 GB = 0.002 tokens  (always bandwidth-bound)
  1B INT4: 8 MB / 0.5 GB = 0.016 tokens  (still bandwidth-bound)
```

LLM inference is almost always bandwidth-bound regardless of batch size.
Batching improves throughput by amortizing the weight load across
multiple requests.

---

## Prefill Chunking

Long prompts may exceed available memory or cause unacceptable latency.
Prefill chunking splits the prompt into manageable chunks:

```c
void chunked_prefill(llm_model_t *model, float *prompt_tokens,
                     int n_tokens, int chunk_size) {
    for (int i = 0; i < n_tokens; i += chunk_size) {
        int actual_chunk = MIN(chunk_size, n_tokens - i);

        // Process chunk
        forward_prefill(model, prompt_tokens + i * model->hidden_dim,
                        actual_chunk);

        // KV cache grows incrementally
        model->kv_cache_len += actual_chunk;

        // Optional: yield between chunks for continuous batching
        if (i + chunk_size < n_tokens) {
            check_pending_requests();
        }
    }
}
```

**Recommended chunk sizes**:
- Interactive: 128-256 tokens (balance latency and throughput)
- Background: 512-1024 tokens (maximize throughput)

---

## Best Practices

1. **For interactive use**, keep batch size at 1-2 to minimize latency.
2. **For serving**, target batch sizes of 8-16 to balance throughput
   and latency.
3. **Implement continuous batching** to avoid wasting compute on
   completed requests.
4. **Use adaptive batch sizing** to respond to varying load without
   manual tuning.
5. **Align batch dimensions** to SIMD width (16 for INT8, 8 for FP16)
   to maximize hardware utilization.
6. **Chunk prefill for long prompts** to maintain responsive latency.
7. **Monitor memory bandwidth utilization** — beyond 85% saturation,
   increasing batch size only adds latency.
8. **Profile with real workloads** — synthetic benchmarks may not
   reflect actual memory access patterns.
