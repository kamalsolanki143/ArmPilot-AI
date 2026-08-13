# KV-Cache Optimization for Arm64 LLM Inference

## Overview

The key-value (KV) cache stores intermediate attention states across
decoder steps, avoiding redundant computation. For a 7B model with
2048 context length, the KV cache alone can consume 1-4 GB of memory.
This guide covers optimization strategies specific to Arm64 hardware.

---

## KV-Cache Structure

### Per-Token Memory Cost

Each token in the KV cache stores key and value vectors for every
attention layer and head:

```
KV_cache_per_token = 2 × n_layers × n_heads × head_dim × bytes_per_element

For a 7B model (32 layers, 32 heads, 128 dim):
  FP16: 2 × 32 × 32 × 128 × 2 bytes = 524,288 bytes = 512 KB/token
  INT8: 2 × 32 × 32 × 128 × 1 byte  = 262,144 bytes = 256 KB/token
  INT4: 2 × 32 × 32 × 128 × 0.5 bytes = 131,072 bytes = 128 KB/token
```

### Memory Scaling

| Context Length | FP16 KV Cache | INT8 KV Cache | INT4 KV Cache |
|----------------|---------------|---------------|---------------|
| 512            | 256 MB        | 128 MB        | 64 MB         |
| 1024           | 512 MB        | 256 MB        | 128 MB        |
| 2048           | 1 GB          | 512 MB        | 256 MB        |
| 4096           | 2 GB          | 1 GB          | 512 MB        |
| 8192           | 4 GB          | 2 GB          | 1 GB          |
| 32768          | 16 GB         | 8 GB          | 4 GB          |

At long context lengths, KV cache dominates memory usage. Optimization
is critical for enabling long-context inference on memory-constrained
Arm64 devices.

---

## KV-Cache Quantization

### Per-Channel Quantization

Quantize each attention head's K and V independently with per-channel
scales:

```c
typedef struct {
    int8_t *data;        // Quantized KV cache
    float *scales;       // Per-head quantization scales
    int n_heads;
    int head_dim;
    int seq_len;
    int max_seq_len;
} quantized_kv_cache_t;

void kv_cache_quantize_head(quantized_kv_cache_t *cache, int head_idx,
                            float *fp16_kv, int seq_len) {
    float abs_max = 0.0f;
    for (int i = 0; i < seq_len * cache->head_dim; i++) {
        float val = fabsf(fp16_kv[i]);
        if (val > abs_max) abs_max = val;
    }

    float scale = abs_max / 127.0f;
    cache->scales[head_idx] = scale;
    float inv_scale = 1.0f / scale;

    for (int i = 0; i < seq_len * cache->head_dim; i++) {
        int8_t q = (int8_t)roundf(fp16_kv[i] * inv_scale);
        cache->data[head_idx * cache->max_seq_len * cache->head_dim + i] = q;
    }
}
```

### Asymmetric KV Quantization

Keys benefit from asymmetric quantization (non-zero zero-point) because
their distributions are often shifted. Values tend to be more symmetric:

```c
void kv_cache_quantize_asymmetric(int8_t *out, float *scales,
                                  float *zero_points, float *input,
                                  int n_elements, int group_size) {
    for (int g = 0; g < n_elements; g += group_size) {
        float min_val = FLT_MAX, max_val = -FLT_MAX;
        for (int i = g; i < g + group_size && i < n_elements; i++) {
            if (input[i] < min_val) min_val = input[i];
            if (input[i] > max_val) max_val = input[i];
        }
        float scale = (max_val - min_val) / 255.0f;
        float zp = min_val;

        scales[g / group_size] = scale;
        zero_points[g / group_size] = zp;

        for (int i = g; i < g + group_size && i < n_elements; i++) {
            out[i] = (uint8_t)roundf((input[i] - zp) / scale);
        }
    }
}
```

---

## PagedAttention

### Concept

PagedAttention divides the KV cache into fixed-size pages (blocks),
similar to virtual memory paging. This eliminates memory fragmentation
and enables dynamic allocation:

```
Traditional KV Cache:
┌──────────────────────────────────────┐
│ Pre-allocated for max_seq_len        │
│ [used][used][free][free][free]...    │  ← Wasted memory
└──────────────────────────────────────┘

PagedAttention:
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Page 0   │ │ Page 1   │ │ Page 2   │  ← Allocated on demand
│ [used]   │ │ [used]   │ │ [used]   │
└──────────┘ └──────────┘ └──────────┘
     ↑
     Block table maps logical → physical
```

### Implementation for Arm64

```c
#define PAGE_SIZE 16  // tokens per page

typedef struct {
    int16_t block_id;      // Physical page index
    int8_t tokens_used;    // Tokens stored in this page
} page_entry_t;

typedef struct {
    int8_t *physical_pages;  // Contiguous memory pool
    page_entry_t *block_table;  // Logical → physical mapping
    int n_pages;
    int page_size;
    int bytes_per_token;
} paged_kv_cache_t;

paged_kv_cache_t* paged_kv_cache_create(int max_seq_len,
                                         int bytes_per_token,
                                         int n_layers_n_heads_dim) {
    int n_pages = (max_seq_len + PAGE_SIZE - 1) / PAGE_SIZE;
    paged_kv_cache_t *cache = malloc(sizeof(paged_kv_cache_t));

    cache->n_pages = n_pages;
    cache->page_size = PAGE_SIZE;
    cache->bytes_per_token = bytes_per_token * n_layers_n_heads_dim;

    // Allocate physical pages
    posix_memalign((void**)&cache->physical_pages, 64,
                   n_pages * PAGE_SIZE * cache->bytes_per_token);

    // Allocate block table
    cache->block_table = calloc(n_pages, sizeof(page_entry_t));

    return cache;
}

void* paged_kv_cache_get(paged_kv_cache_t *cache, int layer,
                         int token_idx) {
    int page_idx = token_idx / cache->page_size;
    int offset = token_idx % cache->page_size;

    int physical = cache->block_table[page_idx].block_id;
    return cache->physical_pages +
           (physical * cache->page_size + offset) * cache->bytes_per_token;
}
```

### Benefits

- **No pre-allocation**: Pages allocated only as tokens are generated
- **No fragmentation**: Physical pages can be non-contiguous
- **Efficient copy-on-write**: Shared prefix across requests shares pages
- **Memory savings**: 30-50% reduction for variable-length requests

---

## GQA/MQA KV-Cache Compression

### Grouped Query Attention (GQA)

GQA shares key-value heads across multiple query heads, reducing KV
cache size proportionally:

```
Multi-Head Attention (MHA):  32 Q heads, 32 KV heads → 100% KV cache
Grouped Query Attention (GQA): 32 Q heads, 8 KV heads  → 25% KV cache
Multi-Query Attention (MQA):  32 Q heads, 1 KV head   → 3.1% KV cache
```

| Config | KV Cache (7B, 2048 ctx) | Quality Impact |
|--------|------------------------|----------------|
| MHA    | 1 GB (FP16)            | Baseline       |
| GQA-8  | 256 MB (FP16)          | < 0.5% ppl     |
| GQA-4  | 128 MB (FP16)          | ~1% ppl        |
| MQA    | 32 MB (FP16)           | ~2-3% ppl      |

### KV-Cache Eviction

For very long contexts, evict less important KV pairs:

**H2O (Heavy-Hitter Oracle)**: Keep tokens with highest attention
accumulation scores:

```c
typedef struct {
    int *token_indices;      // Indices of kept tokens
    float *attention_scores; // Accumulated attention scores
    int n_kept;
    int max_kept;
} h2o_eviction_t;

void h2o_evict(h2o_eviction_t *h2o, float *new_scores, int seq_len,
               int budget) {
    // Update accumulated scores
    for (int i = 0; i < seq_len; i++) {
        h2o->attention_scores[i] += new_scores[i];
    }

    if (seq_len <= budget) return;

    // Find top-k tokens by attention score
    int top_k[budget];
    partial_argsort(h2o->attention_scores, seq_len, top_k, budget);

    // Update kept set
    h2o->n_kept = budget;
    memcpy(h2o->token_indices, top_k, budget * sizeof(int));
}
```

**StreamingLLM**: Keep first N tokens (attention sink) and last M
tokens (recent context):

```c
void streaming_llm_evict(int *keep_indices, int *n_keep,
                         int sink_size, int recent_size,
                         int seq_len) {
    *n_keep = 0;

    // Always keep sink tokens (first 4 tokens)
    for (int i = 0; i < sink_size && i < seq_len; i++) {
        keep_indices[(*n_keep)++] = i;
    }

    // Keep recent tokens
    int recent_start = seq_len - recent_size;
    if (recent_start < sink_size) recent_start = sink_size;
    for (int i = recent_start; i < seq_len; i++) {
        keep_indices[(*n_keep)++] = i;
    }
}
```

---

## KV-Cache Memory Layout

### Column-Major (Standard)

Store each head's K and V contiguously for efficient per-head access:

```
Layout: [layer][head][seq_len][head_dim]
Access pattern: K[layer][head][:][:] — contiguous in memory
```

### Row-Major (Batched)

Store tokens contiguously for efficient batched operations:

```
Layout: [layer][seq_len][n_heads][head_dim]
Access pattern: K[layer][:][head][dim] — strided access
```

### Arm64 Optimization

Column-major is preferred for Arm64 because NEON/SVE load 128+ bits
contiguously. Head-contiguous layout avoids gather operations:

```c
// Efficient column-major KV cache access
void attend_column_major(float *K, float *Q, float *output,
                         int seq_len, int n_heads, int head_dim) {
    for (int h = 0; h < n_heads; h++) {
        float *k_head = K + h * seq_len * head_dim;

        // All tokens for this head are contiguous
        for (int t = 0; t < seq_len; t += 8) {
            float32x8_t k_vec = vld1q_f32_x2(k_head + t * head_dim);
            // Process 8 tokens at once
        }
    }
}
```

---

## Best Practices

1. **Quantize KV cache separately from weights.** KV values have
   different distributions than weights and may need different precision.
2. **Use GQA/MQA** in model architecture to reduce KV cache size by
   4-32x with minimal quality loss.
3. **Implement PagedAttention** for serving workloads with variable
   sequence lengths to eliminate memory fragmentation.
4. **Use StreamingLLM** for infinite-length generation with constant
   memory: keep 4 sink tokens + recent context.
5. **Store KV cache in column-major order** for efficient per-head
   access on Arm64 NEON/SVE.
6. **Align KV cache pages to 64-byte boundaries** for optimal cache
   line utilization.
7. **Monitor KV cache memory** as a percentage of total memory — if it
   exceeds 30%, consider eviction or quantization.
8. **Profile attention computation** to identify whether KV cache
   access or attention score computation is the bottleneck.
