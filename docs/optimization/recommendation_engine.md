# Recommendation Engine for Arm64 LLM Optimization

## Overview

The recommendation engine automatically selects optimal configuration
parameters for LLM inference on Arm64 hardware. It profiles the device,
analyzes model characteristics, and recommends quantization format,
thread count, batch size, and KV-cache strategy.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│               Recommendation Engine                 │
├─────────────┬─────────────┬─────────────┬───────────┤
│   Device    │   Model     │  Workload   │  Output   │
│  Profiler   │  Analyzer   │  Predictor  │  Generator│
└──────┬──────┴──────┬──────┴──────┬──────┴─────┬─────┘
       │             │             │            │
  ┌────▼────┐  ┌─────▼────┐  ┌────▼────┐  ┌────▼────┐
  │ Hardware│  │ Model    │  │ Memory  │  │ Config  │
  │ Features│  │ Metadata │  │ Model   │  │ Profile │
  └─────────┘  └──────────┘  └─────────┘  └─────────┘
```

---

## Device Profiling

### Hardware Detection

```c
typedef struct {
    int n_cores;
    int n_big_cores;
    int n_mid_cores;
    int n_little_cores;
    int big_core_capacity;
    size_t total_memory;
    size_t available_memory;
    size_t l3_cache_size;
    float memory_bandwidth_gb_s;
    int numa_nodes;
    bool has_sve;
    bool has_sve2;
    int sve_vector_bits;
    char soc_name[128];
} device_profile_t;

device_profile_t profile_device(void) {
    device_profile_t profile = {0};

    // Detect core count and types
    core_info_t cores[MAX_CORES];
    profile.n_cores = detect_cores(cores, MAX_CORES);

    for (int i = 0; i < profile.n_cores; i++) {
        if (strcmp(cores[i].core_type, "big") == 0) {
            profile.n_big_cores++;
            profile.big_core_capacity = cores[i].capacity;
        } else if (strcmp(cores[i].core_type, "mid") == 0) {
            profile.n_mid_cores++;
        } else {
            profile.n_little_cores++;
        }
    }

    // Memory detection
    struct sysinfo si;
    sysinfo(&si);
    profile.total_memory = si.totalram * si.mem_unit;
    profile.available_memory = si.freeram * si.mem_unit;

    // Cache detection (parse /sys/devices/system/cpu/cpu0/cache/)
    profile.l3_cache_size = detect_l3_cache();

    // SVE detection
    profile.has_sve = check_sve_support();
    profile.has_sve2 = check_sve2_support();
    profile.sve_vector_bits = get_sve_vector_bits();

    // Memory bandwidth estimation
    profile.memory_bandwidth_gb_s = estimate_memory_bandwidth();

    // SoC name
    detect_soc_name(profile.soc_name, sizeof(profile.soc_name));

    return profile;
}
```

### Memory Bandwidth Estimation

```c
float estimate_memory_bandwidth(void) {
    // STREAM-like benchmark: read/write 32 MB
    const size_t size = 32 * 1024 * 1024;
    float *a = aligned_alloc(64, size);
    float *b = aligned_alloc(64, size);
    float *c = aligned_alloc(64, size);

    // Initialize
    for (size_t i = 0; i < size / sizeof(float); i++) {
        a[i] = 1.0f;
        b[i] = 2.0f;
        c[i] = 0.0f;
    }

    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    // Triad: c = a + scalar * b
    float scalar = 3.0f;
    size_t n = size / sizeof(float);
    for (size_t i = 0; i < n; i++) {
        c[i] = a[i] + scalar * b[i];
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;

    // 3 arrays read/written = 3 * size bytes
    float bw_gb_s = (3.0f * size) / (elapsed * 1e9f);

    free(a);
    free(b);
    free(c);

    return bw_gb_s;
}
```

---

## Model Analysis

### Model Metadata Extraction

```c
typedef struct {
    int n_params;          // Total parameters
    int n_layers;          // Transformer layers
    int hidden_dim;        // Hidden dimension
    int n_heads;           // Attention heads
    int head_dim;          // Per-head dimension
    int ff_dim;            // Feed-forward dimension
    int vocab_size;        // Vocabulary size
    bool has_gqa;          // Grouped Query Attention
    int n_kv_heads;        // KV heads (for GQA)
    float weights_per_token_gb;  // Memory per token (weights only)
    float kv_per_token_mb;       // Memory per token (KV cache)
    char architecture[64]; // e.g., "llama", "mistral", "phi"
} model_profile_t;

model_profile_t analyze_model(const char *model_path) {
    model_profile_t profile = {0};

    // Parse GGUF header
    FILE *f = fopen(model_path, "rb");
    if (!f) return profile;

    // Read GGUF magic and metadata
    uint32_t magic;
    fread(&magic, 4, 1, f);
    if (magic != 0x46554747) {  // "GGUF"
        fclose(f);
        return profile;
    }

    // Extract architecture-specific parameters
    // (Implementation depends on GGUF version)
    parse_gguf_metadata(f, &profile);

    // Compute derived metrics
    profile.weights_per_token_gb =
        (float)profile.n_params * 2 / (1024.0f * 1024.0f * 1024.0f);  // FP16
    profile.kv_per_token_mb =
        2.0f * profile.n_layers * profile.n_kv_heads *
        profile.head_dim * 2 / (1024.0f * 1024.0f);  // FP16

    fclose(f);
    return profile;
}
```

---

## Configuration Recommendation

### Decision Tree

```
Input: device_profile, model_profile, use_case
Output: recommended_config

1. Determine memory budget:
   budget = available_memory - system_reserve (2 GB)
   model_fp16 = model_profile.n_params * 2 bytes

2. Select quantization format:
   if budget >= model_fp16 * 1.5:
       quant = "fp16"          // Enough memory for FP16 + KV cache
   elif budget >= model_fp16 * 0.75:
       quant = "int8"          // Halve memory with minimal quality loss
   elif budget >= model_fp16 * 0.375:
       quant = "int4"          // Quarter memory, acceptable quality
   else:
       quant = "int4_gptq"     // Aggressive compression needed

3. Determine thread count:
   if use_case == "interactive":
       threads_decode = device_profile.n_big_cores
       threads_prefill = device_profile.n_cores
   elif use_case == "throughput":
       threads_decode = device_profile.n_cores
       threads_prefill = device_profile.n_cores

4. Select batch size:
   max_batch = budget / (model_profile.weights_per_token_gb * 1024)
   if use_case == "interactive":
       batch_size = 1
   elif use_case == "serving":
       batch_size = min(16, max_batch)

5. KV-cache strategy:
   if model_profile.has_gqa:
       kv_quant = "int8"       // GQA already reduces KV size
   elif model_profile.kv_per_token_mb > 10:
       kv_quant = "int4"       // Large KV cache needs compression
   else:
       kv_quant = "fp16"       // KV cache fits in memory
```

### Configuration Output

```c
typedef struct {
    // Quantization
    char quant_format[16];       // "fp16", "int8", "int4", "int4_gptq"
    char kv_quant_format[16];    // "fp16", "int8", "int4"

    // Threading
    int decode_threads;
    int prefill_threads;
    int decode_core_list[MAX_CORES];  // Specific cores to pin
    bool use_numa_aware;

    // Batching
    int max_batch_size;
    int prefill_chunk_size;
    bool use_continuous_batching;

    // KV-cache
    int max_context_length;
    bool use_paged_attention;
    int page_size;
    bool use_kv_eviction;
    char eviction_strategy[32];  // "h2o", "streaming_llm", "none"

    // Memory
    size_t kv_cache_budget_mb;
    bool use_mmap;
    bool use_direct_io;

    // Estimated performance
    float estimated_tok_per_sec;
    float estimated_ttft_ms;
    size_t estimated_memory_gb;
} inference_config_t;

inference_config_t recommend_config(device_profile_t *device,
                                     model_profile_t *model,
                                     const char *use_case) {
    inference_config_t config = {0};

    // --- Quantization ---
    size_t model_fp16_bytes = (size_t)model->n_params * 2;
    size_t budget = device->available_memory - 2UL * 1024 * 1024 * 1024;

    if (budget >= model_fp16_bytes * 3 / 2) {
        strcpy(config.quant_format, "fp16");
        config.estimated_memory_gb = model_fp16_bytes / (1024.0*1024*1024);
    } else if (budget >= model_fp16_bytes * 3 / 4) {
        strcpy(config.quant_format, "int8");
        config.estimated_memory_gb = model_fp16_bytes / (2.0*1024*1024*1024);
    } else {
        strcpy(config.quant_format, "int4");
        config.estimated_memory_gb = model_fp16_bytes / (4.0*1024*1024*1024);
    }

    // --- Threading ---
    if (strcmp(use_case, "interactive") == 0) {
        config.decode_threads = device->n_big_cores;
        config.prefill_threads = device->n_cores;
    } else {
        config.decode_threads = device->n_cores;
        config.prefill_threads = device->n_cores;
    }

    // Assign specific big cores for decode
    int idx = 0;
    for (int i = 0; i < device->n_cores && idx < config.decode_threads; i++) {
        // Cores with highest capacity are big cores
        config.decode_core_list[idx++] = i;
    }

    // --- Batching ---
    if (strcmp(use_case, "interactive") == 0) {
        config.max_batch_size = 1;
        config.prefill_chunk_size = 256;
    } else {
        size_t token_memory = (size_t)(config.estimated_memory_gb * 1024 *
                              1024 * 1024) / 2048;
        config.max_batch_size = MIN(16, budget / token_memory);
        config.prefill_chunk_size = 512;
    }

    // --- KV-cache ---
    config.max_context_length = 2048;
    config.use_paged_attention = (strcmp(use_case, "serving") == 0);
    config.page_size = 16;
    config.kv_cache_budget_mb = model->kv_per_token_mb *
                                 config.max_context_length;

    if (!model->has_gqa && model->kv_per_token_mb > 10) {
        strcpy(config.kv_quant_format, "int4");
        config.kv_cache_budget_mb /= 4;
    } else if (model->kv_per_token_mb > 5) {
        strcpy(config.kv_quant_format, "int8");
        config.kv_cache_budget_mb /= 2;
    } else {
        strcpy(config.kv_quant_format, "fp16");
    }

    // --- Performance estimates ---
    float weights_gb = config.estimated_memory_gb;
    config.estimated_tok_per_sec = device->memory_bandwidth_gb_s / weights_gb;
    config.estimated_ttft_ms = (model->n_layers * model->hidden_dim *
                                config.prefill_chunk_size * 2) /
                               (device->memory_bandwidth_gb_s * 1e6);

    return config;
}
```

---

## Workload Prediction

### Throughput Estimation

```c
typedef struct {
    float tokens_per_second;
    float time_to_first_token_ms;
    float memory_usage_gb;
    float memory_bandwidth_utilization;
} performance_estimate_t;

performance_estimate_t predict_performance(device_profile_t *device,
                                           inference_config_t *config,
                                           model_profile_t *model) {
    performance_estimate_t est = {0};

    // Decode throughput: bandwidth-limited
    float weights_gb = model->n_params * get_quant_bytes(config->quant_format)
                       / (1024.0f * 1024 * 1024);
    est.tokens_per_second = device->memory_bandwidth_gb_s / weights_gb;

    // Adjust for batch size (diminishing returns above bandwidth saturation)
    float batch_factor = 1.0f;
    if (config->max_batch_size > 1) {
        float utilization = weights_gb * config->max_batch_size /
                           device->memory_bandwidth_gb_s;
        if (utilization > 0.85f) {
            batch_factor = 0.85f / utilization;
        } else {
            batch_factor = 1.0f;
        }
    }
    est.tokens_per_second *= batch_factor * config->max_batch_size;

    // TTFT: compute-bound during prefill
    float flops_per_token = 2.0f * model->n_params;  // multiply-accumulate
    float compute_tflops = device->n_big_cores * 0.1f;  // Rough estimate
    est.time_to_first_token_ms = (flops_per_token * config->prefill_chunk_size)
                                 / (compute_tflops * 1e12) * 1000.0f;

    // Memory usage
    est.memory_usage_gb = weights_gb +
                          model->kv_per_token_mb * config->max_context_length
                          / 1024.0f;
    est.memory_bandwidth_utilization =
        weights_gb / device->memory_bandwidth_gb_s;

    return est;
}
```

---

## Runtime Adaptation

### Dynamic Reconfiguration

The engine monitors runtime metrics and adjusts configuration:

```c
typedef struct {
    float avg_tok_per_sec;
    float p99_tok_per_sec;
    float memory_usage_pct;
    float bandwidth_utilization;
    int active_requests;
    int dropped_requests;
} runtime_metrics_t;

void adaptive_reconfigure(inference_config_t *config,
                           runtime_metrics_t *metrics,
                           device_profile_t *device) {
    // Scale down if memory pressure is high
    if (metrics->memory_usage_pct > 90.0f) {
        if (config->max_batch_size > 1) {
            config->max_batch_size--;
        }
        if (config->max_context_length > 512) {
            config->max_context_length /= 2;
        }
    }

    // Scale up if resources are available
    if (metrics->memory_usage_pct < 70.0f &&
        metrics->bandwidth_utilization < 0.7f) {
        if (config->max_batch_size < 16) {
            config->max_batch_size++;
        }
    }

    // Switch quantization if consistently under memory pressure
    if (metrics->memory_usage_pct > 95.0f) {
        if (strcmp(config->quant_format, "fp16") == 0) {
            strcpy(config->quant_format, "int8");
        } else if (strcmp(config->quant_format, "int8") == 0) {
            strcpy(config->quant_format, "int4");
        }
    }
}
```

---

## Best Practices

1. **Profile the device first** before selecting any configuration.
   Core topology and memory bandwidth vary dramatically across Arm64 SoCs.
2. **Measure actual memory bandwidth** with a STREAM-like benchmark
   rather than relying on theoretical specifications.
3. **Use INT4 quantization as the default** for memory-constrained
   devices. Only upgrade to INT8/FP16 if memory allows.
4. **Pin decode threads to big cores** — this is the single highest-impact
   optimization for interactive use cases.
5. **Adapt batch size to load.** Use small batches for interactive
   latency, larger batches for throughput serving.
6. **Monitor runtime metrics** and adjust configuration dynamically
   as workload changes.
7. **Validate recommendations** with actual inference benchmarks.
   Models vary in their sensitivity to quantization and configuration.
8. **Cache device profiles** — hardware detection is expensive and
   the result doesn't change between runs.
