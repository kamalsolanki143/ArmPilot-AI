# Thread Optimization for Arm64 LLM Inference

## Overview

Arm64 processors use heterogeneous core architectures (big.LITTLE,
DynamIQ) where cores have different performance characteristics. Thread
optimization for LLM inference requires understanding core topology,
scheduling policies, and the memory access patterns of transformer
workloads.

---

## Arm64 Core Architectures

### big.LITTLE and DynamIQ

Arm's big.LITTLE architecture pairs high-performance ("big") cores with
energy-efficient ("LITTLE") cores on the same die. DynamIQ improves this
by allowing mixed cluster configurations:

| Architecture | Big Cores       | LITTLE Cores    |典型设备                   |
|--------------|-----------------|-----------------|--------------------------|
| big.LITTLE   | Cortex-A76/A78  | Cortex-A55/A510 | Snapdragon 845/888      |
| DynamIQ      | Cortex-A715/A720| Cortex-A520     | Snapdragon 8 Gen 2/3    |
| DSU-110      | Cortex-X3/X4    | Cortex-A520     | Server/automotive       |

### Core Characteristics

| Core Type | L1 Cache | L2 Cache | Out-of-Order Width | Typical Clock |
|-----------|----------|----------|--------------------:|--------------|
| Cortex-X4 | 64 KB I  | 1 MB     | 10-wide             | 3.3 GHz      |
| Cortex-A720 | 64 KB I | 512 KB  | 8-wide              | 2.8 GHz      |
| Cortex-A520 | 32 KB I | 128 KB  | 5-wide              | 2.0 GHz      |

**Key insight**: A single Cortex-X4 core can be 2-3x faster than a
Cortex-A520 core for single-threaded workloads. Thread placement
matters enormously.

---

## LLM Inference Thread Patterns

### Pre-Fill Phase (Prompt Processing)

Pre-fill processes the entire prompt in parallel. This is an
embarrassingly parallel workload that benefits from maximum thread
count:

```
Token count: 2048
Layers: 32
Attention heads: 32
Batch size: 1

Pre-fill parallelism: tokens × layers (across pipeline)
```

**Optimal strategy**: Use all available cores, prefer big cores for
the outer token dimension.

### Decode Phase (Token Generation)

Decode generates one token at a time. Each token requires a full
forward pass through all layers, but within each layer, the operations
are:

- **Attention**: QK^T is (seq_len × head_dim) — small, bandwidth-bound
- **FFN**: Up-projection is (hidden_dim × ff_dim) — compute-bound
- **FFN**: Down-projection is (ff_dim × hidden_dim) — bandwidth-bound

**Optimal strategy**: Fewer threads, each with high single-thread
performance. Memory bandwidth is the bottleneck.

---

## Thread Pool Configuration

### llama.cpp Thread Model

llama.cpp uses a thread pool with configurable `--threads` and
`--threads-batch` parameters:

```bash
# Pre-fill: use all cores
./llama-cli -m model.gguf \
  --threads 8 \
  --threads-batch 8 \
  --prompt "Hello world"

# Decode: use big cores only
./llama-cli -m model.gguf \
  --threads 4 \
  --threads-batch 8 \
  --prompt "Hello world"
```

**Rule of thumb**:
- `--threads-batch` (pre-fill): Set to total core count
- `--threads` (decode): Set to big core count only

### Custom Thread Pool Implementation

```c
#include <pthread.h>
#include <sched.h>

typedef struct {
    int thread_id;
    int core_id;
    cpu_set_t affinity_mask;
    void *(*work_fn)(void *);
    void *work_arg;
} thread_config_t;

void* worker_thread(void *arg) {
    thread_config_t *config = (thread_config_t *)arg;

    // Pin to specific core
    pthread_setaffinity_np(pthread_self(),
                           sizeof(cpu_set_t),
                           &config->affinity_mask);

    // Set high priority for big cores
    if (config->core_id < NUM_BIG_CORES) {
        struct sched_param param;
        param.sched_priority = sched_get_priority_max(SCHED_FIFO);
        pthread_setschedparam(pthread_self(), SCHED_FIFO, &param);
    }

    return config->work_fn(config->work_arg);
}
```

---

## Core Affinity Strategies

### Strategy 1: Static Pinning

Pin specific threads to specific cores at startup. Simple and
deterministic but doesn't adapt to system load.

```c
// Pin decode threads to big cores (cores 0-3)
void pin_decode_threads(pthread_t *threads, int n_threads) {
    for (int i = 0; i < n_threads; i++) {
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(i, &cpuset);  // Cores 0-3 are big
        pthread_setaffinity_np(threads[i], sizeof(cpu_set_t), &cpuset);
    }
}
```

### Strategy 2: NUMA-Aware Pinning

On multi-socket Arm64 servers (e.g., Ampere Altra), threads should be
pinned to cores on the same NUMA node as their working memory:

```c
#include <numa.h>

void numa_aware_pin(int thread_id, int total_threads) {
    int node = thread_id / (total_threads / numa_num_configured_nodes());
    struct bitmask *nodemask = numa_allocate_nodemask();
    numa_bitmask_setbit(nodemask, node);
    numa_run_on_node_mask(nodemask);
    numa_free_nodemask(nodemask);
}
```

### Strategy 3: Work-Stealing

Allow threads to steal work from other threads' queues when idle.
Adapts to varying per-token compute across layers:

```c
// Lock-free work-stealing queue (Chase-Lev deque)
typedef struct {
    _Atomic size_t bottom;
    _Atomic size_t top;
    void **tasks;
    size_t mask;
} work_stealing_queue_t;

void* wsq_pop(work_stealing_queue_t *q) {
    size_t b = atomic_load_explicit(&q->bottom, memory_order_relaxed);
    size_t t = atomic_load_explicit(&q->top, memory_order_acquire);
    if (b <= t) {
        void *task = q->tasks[t & q->mask];
        if (atomic_compare_exchange_strong(&q->top, &t, t + 1)) {
            atomic_store_explicit(&q->bottom, b + 1, memory_order_release);
            return task;
        }
    }
    return NULL;  // Steal from another thread
}
```

---

## Thread Count Tuning

### Memory Bandwidth Saturation

Each core adds memory bandwidth pressure. On Arm64 devices, the memory
controller has finite bandwidth:

| Device            | Memory BW | Optimal Threads (INT4 7B) |
|-------------------|-----------|---------------------------|
| Snapdragon 8 Gen 3| ~51 GB/s  | 4-6                       |
| Apple M2 (comparison) | ~100 GB/s | 6-8                    |
| Ampere Altra      | ~200 GB/s | 16-32                     |
| AWS Graviton3      | ~150 GB/s | 12-24                     |

**Diminishing returns**: Beyond the bandwidth saturation point,
adding threads increases latency due to contention.

### L2 Cache Contention

Multiple threads sharing L2 cache cause eviction storms. Each thread
should have enough working set space:

```
L2 cache per big core: 512 KB - 1 MB
Working set per decode step: ~50-100 KB (INT4, 7B model)
Max threads before L2 contention: L2_size / working_set ≈ 5-10
```

### Measurement

```bash
# Monitor cache misses during inference
perf stat -e cache-misses,cache-references \
  ./llama-cli -m model.gguf --threads 4

# Compare across thread counts
for t in 1 2 4 6 8; do
  echo "Threads: $t"
  perf stat -e L1-dcache-load-misses,cycles,instructions \
    ./llama-cli -m model.gguf --threads $t --prompt "test" -n 100 2>&1 | \
    grep -E "cache|cycle|instruction"
done
```

---

## Asymmetric Threading

### Pre-Fill vs Decode

The two phases of inference have different optimal thread counts:

```
┌─────────────────────────────────────────────┐
│ Pre-fill: 8 threads × Cortex-X4 cores      │
│   └─ All tokens processed in parallel       │
│   └─ Bottleneck: compute throughput         │
├─────────────────────────────────────────────┤
│ Decode: 4 threads × Cortex-X4 cores        │
│   └─ One token at a time                    │
│   └─ Bottleneck: memory bandwidth           │
└─────────────────────────────────────────────┘
```

### Implementation

```c
void llm_inference_config(int phase, inference_config_t *config) {
    if (phase == PHASE_PREFILL) {
        config->n_threads = total_cores;           // Use all cores
        config->thread_priority = PRIORITY_NORMAL;  // Throughput mode
        config->batch_size = 512;                   // Large batches
    } else {  // PHASE_DECODE
        config->n_threads = big_core_count;         // Big cores only
        config->thread_priority = PRIORITY_HIGH;    // Latency mode
        config->batch_size = 1;                     // Single token
    }
}
```

---

## Best Practices

1. **Profile before tuning.** Use `perf` or `simpleperf` to identify
   whether your workload is compute-bound or bandwidth-bound.
2. **Match thread count to memory bandwidth**, not core count. More
   cores doesn't always mean faster inference.
3. **Pre-fill benefits from many threads; decode benefits from fast
   threads.** Use asymmetric thread counts for each phase.
4. **Pin decode threads to big cores.** LITTLE cores are 2-3x slower
   and will bottleneck the pipeline.
5. **Avoid over-subscription.** Running more threads than physical
   cores causes context switching overhead.
6. **Use NUMA-aware pinning on servers.** Cross-node memory access
   adds 100-200ns latency per access.
7. **Consider thread priorities.** Use `SCHED_FIFO` for decode threads
   to prevent preemption during latency-critical token generation.
8. **Test across core counts** to find the bandwidth saturation point
   for your specific hardware and model size.
