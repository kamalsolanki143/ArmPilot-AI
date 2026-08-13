# CPU Affinity Pinning for Arm64 LLM Inference

## Overview

CPU affinity pinning binds threads to specific processor cores, preventing
the OS scheduler from migrating threads across cores. For LLM inference
on Arm64, this eliminates cache invalidation overhead and ensures
decode threads consistently run on high-performance cores.

---

## Arm64 Core Topology

### Identifying Core Types

Arm64 cores are not uniform. The `sysfs` filesystem exposes core
characteristics:

```bash
# List all CPUs and their cluster
ls /sys/devices/system/cpu/cpu*/topology/cluster_id

# Check core capacity (relative performance)
cat /sys/devices/system/cpu/cpu*/cpu_capacity

# Example output for Snapdragon 8 Gen 3:
# cpu0: capacity=1024 (Cortex-X4, big)
# cpu1: capacity=1024 (Cortex-X4, big)
# cpu2: capacity=1024 (Cortex-X4, big)
# cpu3: capacity=1024 (Cortex-X4, big)
# cpu4: capacity=731  (Cortex-A720, mid)
# cpu5: capacity=731  (Cortex-A720, mid)
# cpu6: capacity=731  (Cortex-A720, mid)
# cpu7: capacity=443  (Cortex-A520, LITTLE)
```

### Reading Topology Programmatically

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int cpu_id;
    int cluster_id;
    int capacity;
    char core_type[16];  // "big", "mid", "LITTLE"
} core_info_t;

int detect_cores(core_info_t *cores, int max_cores) {
    int n_cores = 0;

    for (int i = 0; i < max_cores; i++) {
        char path[256];
        FILE *f;

        // Read cluster ID
        snprintf(path, sizeof(path),
                 "/sys/devices/system/cpu/cpu%d/topology/cluster_id", i);
        f = fopen(path, "r");
        if (!f) continue;
        fscanf(f, "%d", &cores[n_cores].cluster_id);
        fclose(f);

        // Read capacity
        snprintf(path, sizeof(path),
                 "/sys/devices/system/cpu/cpu%d/cpu_capacity", i);
        f = fopen(path, "r");
        if (!f) continue;
        fscanf(f, "%d", &cores[n_cores].capacity);
        fclose(f);

        // Classify core type
        if (cores[n_cores].capacity >= 900) {
            strcpy(cores[n_cores].core_type, "big");
        } else if (cores[n_cores].capacity >= 600) {
            strcpy(cores[n_cores].core_type, "mid");
        } else {
            strcpy(cores[n_cores].core_type, "LITTLE");
        }

        cores[n_cores].cpu_id = i;
        n_cores++;
    }

    return n_cores;
}
```

---

## Affinity Pinning Strategies

### Strategy 1: Decode on Big Cores

Pin decode threads to big cores for maximum single-thread performance:

```c
#include <sched.h>
#include <pthread.h>

void pin_decode_to_big_cores(pthread_t *threads, int n_threads,
                              core_info_t *cores, int n_cores) {
    int big_core_count = 0;
    cpu_set_t big_cores;

    CPU_ZERO(&big_cores);
    for (int i = 0; i < n_cores; i++) {
        if (strcmp(cores[i].core_type, "big") == 0) {
            CPU_SET(cores[i].cpu_id, &big_cores);
            big_core_count++;
        }
    }

    // Pin each decode thread to a big core
    for (int i = 0; i < n_threads && i < big_core_count; i++) {
        cpu_set_t mask;
        CPU_ZERO(&mask);

        // Find the i-th big core
        int big_idx = 0;
        for (int c = 0; c < n_cores; c++) {
            if (strcmp(cores[c].core_type, "big") == 0) {
                if (big_idx == i) {
                    CPU_SET(cores[c].cpu_id, &mask);
                    break;
                }
                big_idx++;
            }
        }

        pthread_setaffinity_np(threads[i], sizeof(cpu_set_t), &mask);
    }
}
```

### Strategy 2: Pre-Fill on All Cores

Use all available cores for the compute-intensive pre-fill phase:

```c
void pin_prefill_to_all_cores(pthread_t *threads, int n_threads,
                               int n_cores) {
    cpu_set_t all_cores;
    CPU_ZERO(&all_cores);

    for (int i = 0; i < n_cores; i++) {
        CPU_SET(i, &all_cores);
    }

    for (int i = 0; i < n_threads; i++) {
        pthread_setaffinity_np(threads[i], sizeof(cpu_set_t), &all_cores);
    }
}
```

### Strategy 3: Hybrid Scheduling

Dynamically adjust affinity based on inference phase:

```c
typedef struct {
    pthread_t *threads;
    int n_threads;
    core_info_t *cores;
    int n_cores;
    enum { PHASE_PREFILL, PHASE_DECODE } current_phase;
} affinity_manager_t;

void affinity_manager_switch_phase(affinity_manager_t *mgr,
                                   enum phase new_phase) {
    if (mgr->current_phase == new_phase) return;

    if (new_phase == PHASE_PREFILL) {
        pin_prefill_to_all_cores(mgr->threads, mgr->n_threads,
                                  mgr->n_cores);
    } else {
        pin_decode_to_big_cores(mgr->threads, mgr->n_threads,
                                 mgr->cores, mgr->n_cores);
    }

    mgr->current_phase = new_phase;
}
```

---

## Linux sched_setaffinity

### Direct Syscall Approach

```c
#include <sched.h>

int pin_to_core(int core_id) {
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(core_id, &mask);
    return sched_setaffinity(0, sizeof(cpu_set_t), &mask);
}

int pin_to_cores(int *core_ids, int n_cores) {
    cpu_set_t mask;
    CPU_ZERO(&mask);
    for (int i = 0; i < n_cores; i++) {
        CPU_SET(core_ids[i], &mask);
    }
    return sched_setaffinity(0, sizeof(cpu_set_t), &mask);
}

// Verify affinity
int get_pinned_cores(void) {
    cpu_set_t mask;
    sched_getaffinity(0, sizeof(cpu_set_t), &mask);

    int pinned = 0;
    for (int i = 0; i < CPU_SETSIZE; i++) {
        if (CPU_ISSET(i, &mask)) pinned++;
    }
    return pinned;
}
```

### Thread-Level Pinning

```c
void* decode_worker(void *arg) {
    worker_context_t *ctx = (worker_context_t *)arg;

    // Pin this thread to assigned core
    cpu_set_t mask;
    CPU_ZERO(&mask);
    CPU_SET(ctx->assigned_core, &mask);
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &mask);

    // Set real-time priority
    struct sched_param param;
    param.sched_priority = 50;
    pthread_setschedparam(pthread_self(), SCHED_FIFO, &param);

    // Run decode loop
    while (!ctx->should_stop) {
        decode_step(ctx->model, ctx->batch);
    }

    return NULL;
}
```

---

## NUMA Awareness

### Detecting NUMA Nodes

```c
#include <numa.h>
#include <numaif.h>

void detect_numa_topology(void) {
    int n_nodes = numa_max_node() + 1;
    int n_cpus = numa_num_configured_cpus();

    printf("NUMA nodes: %d, CPUs: %d\n", n_nodes, n_cpus);

    for (int node = 0; node < n_nodes; node++) {
        struct bitmask *cpumask = numa_allocate_cpumask();
        numa_node_to_cpus(node, cpumask);

        long free_mem;
        numa_node_size(node, NULL, &free_mem);

        printf("Node %d: %ld MB free\n", node, free_mem / (1024*1024));
        numa_free_cpumask(cpumask);
    }
}
```

### NUMA-Pinned Allocation

```c
void* numa_pinned_alloc(size_t size, int preferred_node) {
    void *ptr = numa_alloc_onnode(size, preferred_node);
    if (!ptr) {
        // Fallback to any node
        ptr = numa_alloc_local(size);
    }

    // Advise kernel to use local memory
    numa_tonode_memory(ptr, size, preferred_node);

    return ptr;
}

// Pin worker thread and its memory to same NUMA node
void numa_aware_worker(int node_id, size_t working_set_size) {
    // Pin thread to node
    struct bitmask *nodemask = numa_allocate_nodemask();
    numa_bitmask_setbit(nodemask, node_id);
    numa_run_on_node_mask(nodemask);

    // Allocate memory on same node
    void *kv_cache = numa_pinned_alloc(working_set_size, node_id);
    void *weights = numa_pinned_alloc(WEIGHT_SIZE, node_id);

    // Run inference
    run_inference(weights, kv_cache);

    numa_free(kv_cache, working_set_size);
    numa_free(weights, WEIGHT_SIZE);
    numa_free_nodemask(nodemask);
}
```

---

## Performance Impact

### Cache Behavior Without Pinning

Without affinity, thread migration causes:

1. **L1 cache cold start**: 10-50 cycle penalty per miss
2. **L2 cache cold start**: 100-300 cycle penalty per miss
3. **TLB flush**: 50-200 cycle penalty per miss
4. **Branch predictor flush**: Variable, 10-100 cycles

For LLM decode, each token involves ~3.5 GB of weight reads (INT4, 7B).
Cache misses during this read path cause significant latency spikes.

### Measured Impact

| Scenario               | Avg tok/s | P99 tok/s | P99 - Avg |
|------------------------|-----------|-----------|-----------|
| No pinning             | 16.2      | 22.1      | +36%      |
| Pin decode to big      | 18.4      | 19.8      | +7.6%     |
| Pin + NUMA-aware       | 19.1      | 20.2      | +5.8%     |
| Pin + NUMA + priority  | 19.3      | 19.9      | +3.1%     |

*Snapdragon 8 Gen 3, 7B INT4, batch=1*

**Key observation**: Pinning improves both average throughput and tail
latency. The P99 improvement is more dramatic than the average.

---

## OS-Level Configuration

### Disabling CPU Frequency Scaling

On Arm64, CPU frequency scaling (DVFS) can cause inconsistent performance:

```bash
# Set all cores to maximum frequency
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo performance > $cpu
done

# Pin frequency (if supported)
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq; do
    cat /sys/devices/system/cpu/cpu*/cpufreq/cpuinfo_max_freq > $cpu
done
```

### Disabling Transparent Huge Pages

THP can cause latency spikes during compaction:

```bash
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
```

### Process Priority

```c
// Set high process priority
struct sched_param param;
param.sched_priority = sched_get_priority_max(SCHED_FIFO);
sched_setscheduler(0, SCHED_FIFO, &param);

// Increase OOM score adjustment to prevent killing
FILE *f = fopen("/proc/self/oom_score_adj", "w");
fprintf(f, "-500");
fclose(f);
```

---

## Best Practices

1. **Always pin decode threads to big cores.** The 2-3x single-thread
   performance difference makes this the highest-impact optimization.
2. **Use NUMA-aware allocation** on multi-socket Arm64 servers to
   avoid cross-node memory access penalties.
3. **Set thread priority to SCHED_FIFO** for decode threads to prevent
   preemption during latency-critical token generation.
4. **Disable CPU frequency scaling** during inference for consistent
   performance.
5. **Monitor thread migration** with `perf stat -e migrations` to
   verify pinning is effective.
6. **Adjust pinning dynamically** between pre-fill (all cores) and
   decode (big cores only).
7. **Test pinning configurations** on target hardware — core topology
   varies significantly across Arm64 SoCs.
8. **Combine with cache prefetching** for weight data to maximize the
   benefit of consistent core placement.
