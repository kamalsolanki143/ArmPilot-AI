# Memory Profiling for LLM Inference

How ArmPilot-AI measures, analyzes, and reports memory usage during LLM inference on Arm Neoverse platforms.

## Memory Landscape in LLM Inference

LLM inference consumes memory across four distinct regions:

```
┌─────────────────────────────────────────────────────┐
│                    Process Memory                     │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   Model     │  │  KV-Cache   │  │  Activation  │  │
│  │   Weights   │  │  (grows     │  │  Buffers     │  │
│  │  (static)   │  │  with ctx)  │  │  (scratch)   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │              Runtime Overhead                    │  │
│  │  (Python, tokenizer, scheduler, allocator)       │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Memory Budget Formula

```
Total Memory = Model Weights + KV-Cache + Activation Buffers + Runtime Overhead

For a 7B model with 4K context, Q4_K_M quantization:
- Weights:    4.0 GB
- KV-Cache:   0.5 GB (8 layers, 32 heads, 128 dim, 4K context, FP16)
- Activation: 0.2 GB (batch_size=1)
- Runtime:    0.3 GB (Python + tokenizer + allocator overhead)
- Total:     ~5.0 GB
```

## Memory Collection Methods

### Process-Level Collection

```python
import os
import resource
import psutil

class MemoryProfiler:
    """Collects process-level memory metrics during inference."""
    
    def __init__(self, pid: int = None):
        self.pid = pid or os.getpid()
        self.process = psutil.Process(self.pid)
        self.samples = []
        self.peak_rss = 0
        self.peak_vms = 0
    
    def sample(self) -> dict:
        """Take a single memory snapshot."""
        mem_info = self.process.memory_info()
        mem_full = self.process.memory_full_info()
        
        sample = {
            "timestamp_ns": time.monotonic_ns(),
            "rss_bytes": mem_info.rss,
            "vms_bytes": mem_info.vms,
            "shared_bytes": getattr(mem_full, "shared", 0),
            "text_bytes": getattr(mem_full, "text", 0),
            "lib_bytes": getattr(mem_full, "lib", 0),
            "data_bytes": getattr(mem_full, "data", 0),
            "dirty_bytes": getattr(mem_full, "dirty", 0),
        }
        
        self.samples.append(sample)
        self.peak_rss = max(self.peak_rss, sample["rss_bytes"])
        self.peak_vms = max(self.peak_vms, sample["vms_bytes"])
        
        return sample
    
    def start_continuous_collection(self, interval_ms: int = 100):
        """Start background memory sampling."""
        import threading
        
        self._stop_event = threading.Event()
        
        def _collect_loop():
            while not self._stop_event.is_set():
                self.sample()
                self._stop_event.wait(interval_ms / 1000.0)
        
        self._thread = threading.Thread(target=_collect_loop, daemon=True)
        self._thread.start()
    
    def stop_continuous_collection(self):
        """Stop background memory sampling."""
        self._stop_event.set()
        self._thread.join(timeout=5.0)
    
    def summary(self) -> dict:
        """Summarize collected memory samples."""
        if not self.samples:
            return {}
        
        rss_values = [s["rss_bytes"] for s in self.samples]
        data_values = [s["data_bytes"] for s in self.samples if s["data_bytes"] > 0]
        
        return {
            "peak_rss_mb": self.peak_rss / (1024 * 1024),
            "avg_rss_mb": statistics.mean(rss_values) / (1024 * 1024),
            "min_rss_mb": min(rss_values) / (1024 * 1024),
            "final_rss_mb": rss_values[-1] / (1024 * 1024),
            "rss_growth_mb": (rss_values[-1] - rss_values[0]) / (1024 * 1024),
            "sample_count": len(self.samples),
        }
```

### Linux-Specific Collection via /proc

```python
class ProcMemoryProfiler:
    """Detailed memory profiling via /proc/self/."""
    
    def read_smaps_rollup(self) -> dict:
        """Read /proc/self/smaps_rollup for aggregated memory stats."""
        with open("/proc/self/smaps_rollup", "r") as f:
            stats = {}
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(":")
                value_kb = int(parts[1])
                stats[key] = value_kb * 1024  # Convert to bytes
            return stats
    
    def read_status(self) -> dict:
        """Read /proc/self/status for VmRSS, VmHWM, etc."""
        stats = {}
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith(("VmSize:", "VmRSS:", "VmHWM:", 
                                   "VmData:", "VmStk:", "VmLib:")):
                    parts = line.split()
                    key = parts[0].rstrip(":")
                    value_kb = int(parts[1])
                    stats[key] = value_kb * 1024
        return stats
    
    def read_numa_stats(self) -> dict:
        """Read per-NUMA-node memory allocation."""
        numa_stats = {}
        try:
            with open("/proc/self/numa_maps", "r") as f:
                for line in f:
                    if line.startswith("N"):
                        parts = line.split()
                        node = parts[0]
                        # Parse dirty/writeback pages
                        if node not in numa_stats:
                            numa_stats[node] = {"pages": 0}
                        numa_stats[node]["pages"] += 1
        except FileNotFoundError:
            pass
        return numa_stats
```

### Memory Bandwidth Measurement

```python
class MemoryBandwidthProfiler:
    """Measure memory bandwidth utilization during inference."""
    
    def __init__(self):
        self.bandwidth_samples = []
    
    def measure_stream_bandwidth(self, array_size_mb: int = 256, iterations: int = 10) -> float:
        """Measure achieved memory bandwidth using STREAM-like operations.
        
        Returns bandwidth in GB/s.
        """
        import numpy as np
        
        n_elements = (array_size_mb * 1024 * 1024) // 4  # float32
        a = np.ones(n_elements, dtype=np.float32)
        b = np.ones(n_elements, dtype=np.float32) * 2.0
        c = np.zeros(n_elements, dtype=np.float32)
        
        start = time.monotonic_ns()
        for _ in range(iterations):
            c[:] = a + b  # Triad: a[i] + b[i] -> c[i]
        end = time.monotonic_ns()
        
        total_bytes = iterations * n_elements * 4 * 3  # read a, read b, write c
        duration_s = (end - start) / 1e9
        
        bandwidth_gbps = total_bytes / duration_s / (1024**3)
        return bandwidth_gbps
```

## KV-Cache Memory Profiling

### Static Estimation

```python
def estimate_kv_cache_memory(
    num_layers: int,
    num_heads: int,
    head_dim: int,
    context_length: int,
    dtype_bytes: int = 2,  # FP16 = 2 bytes
    num_key_value_heads: int = None,
) -> int:
    """Estimate KV-cache memory in bytes.
    
    KV-cache stores keys and values for all layers, all heads,
    for the current context length.
    """
    if num_key_value_heads is None:
        num_key_value_heads = num_heads  # Full attention
    
    # Two tensors (K and V) per layer
    bytes_per_layer = 2 * num_key_value_heads * head_dim * context_length * dtype_bytes
    total_bytes = num_layers * bytes_per_layer
    
    return total_bytes
```

### Dynamic KV-Cache Monitoring

```python
class KVCacheProfiler:
    """Monitor KV-cache memory usage during inference."""
    
    def __init__(self, model_config: dict):
        self.config = model_config
        self.kv_cache_bytes = 0
        self.history = []
    
    def on_context_change(self, new_context_length: int):
        """Called when context length changes (new tokens added)."""
        self.kv_cache_bytes = estimate_kv_cache_memory(
            num_layers=self.config["num_layers"],
            num_heads=self.config["num_attention_heads"],
            head_dim=self.config["head_dim"],
            context_length=new_context_length,
            dtype_bytes=self.config.get("dtype_bytes", 2),
            num_key_value_heads=self.config.get("num_key_value_heads"),
        )
        self.history.append({
            "timestamp_ns": time.monotonic_ns(),
            "context_length": new_context_length,
            "kv_cache_bytes": self.kv_cache_bytes,
        })
    
    def summary(self) -> dict:
        if not self.history:
            return {"kv_cache_bytes": 0, "peak_context_length": 0}
        
        return {
            "final_kv_cache_mb": self.kv_cache_bytes / (1024 * 1024),
            "peak_kv_cache_mb": max(h["kv_cache_bytes"] for h in self.history) / (1024 * 1024),
            "peak_context_length": max(h["context_length"] for h in self.history),
            "kv_cache_growth_rate_mb_per_token": self._growth_rate(),
        }
    
    def _growth_rate(self) -> float:
        """MB of KV-cache per additional context token."""
        if len(self.history) < 2:
            return 0.0
        
        first = self.history[0]
        last = self.history[-1]
        delta_bytes = last["kv_cache_bytes"] - first["kv_cache_bytes"]
        delta_tokens = last["context_length"] - first["context_length"]
        
        if delta_tokens == 0:
            return 0.0
        return delta_bytes / delta_tokens / (1024 * 1024)
```

## Memory Leak Detection

```python
class MemoryLeakDetector:
    """Detect memory leaks during long-running inference benchmarks."""
    
    def __init__(self, baseline_samples: int = 100, check_interval_s: float = 30.0):
        self.baseline_samples = baseline_samples
        self.check_interval_s = check_interval_s
        self.rss_history = []
        self.leak_detected = False
    
    def analyze(self, profiler: MemoryProfiler) -> dict:
        """Analyze memory samples for leak patterns."""
        rss_values = [s["rss_bytes"] for s in profiler.samples]
        
        if len(rss_values) < self.baseline_samples * 2:
            return {"status": "insufficient_data"}
        
        # Split into baseline and observation windows
        baseline = rss_values[:self.baseline_samples]
        recent = rss_values[-self.baseline_samples:]
        
        baseline_avg = statistics.mean(baseline)
        recent_avg = statistics.mean(recent)
        
        # Check for consistent growth
        growth_rate = (recent_avg - baseline_avg) / len(rss_values)
        
        # Linear regression for trend detection
        x = list(range(len(rss_values)))
        slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(x, rss_values)
        
        self.leak_detected = (
            slope > 1024 * 1024 and  # > 1MB/s growth
            r_value ** 2 > 0.8 and    # Strong linear trend
            p_value < 0.05             # Statistically significant
        )
        
        return {
            "leak_detected": self.leak_detected,
            "growth_rate_mb_per_s": slope / (1024 * 1024),
            "r_squared": r_value ** 2,
            "p_value": p_value,
            "baseline_avg_mb": baseline_avg / (1024 * 1024),
            "recent_avg_mb": recent_avg / (1024 * 1024),
        }
```

## Arm-Specific Memory Considerations

### Page Size Effects

Arm Neoverse supports both 4KB and 64KB pages. Larger pages reduce TLB pressure but increase per-page overhead:

```bash
# Check page size
getconf PAGE_SIZE  # Returns 4096 or 65536

# For LLM inference, 64KB pages are recommended on Arm
# Reduce TLB misses for large model weight access
```

| Page Size | TLB Entries | TLB Coverage | Model Weights TLB Misses |
|-----------|-------------|--------------|-------------------------|
| 4 KB | 64 | 256 KB | High (8B model ≈ 2M entries) |
| 64 KB | 64 | 4 MB | 16x fewer |

### NUMA-Aware Memory Allocation

```bash
# Pin memory allocation to same NUMA node as inference cores
numactl --membind=0 --cpunodebind=0 python benchmark.py

# For multi-NUMA systems, distribute model across nodes
numactl --membind=0,1 python benchmark.py  # If model spans 2 nodes
```

### Transparent Huge Pages (THP)

```bash
# Check THP status
cat /sys/kernel/mm/transparent_hugepage/enabled

# For LLM inference, THP can reduce TLB pressure
# But may cause latency spikes during compaction
# Recommended: always madvise
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled
```

### Memory Allocator Tuning

```python
# jemalloc configuration for LLM inference
import os

# Prefer jemalloc for better multi-threaded allocation
os.environ["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libjemalloc.so.2"
os.environ["MALLOC_CONF"] = (
    "background_thread:true,"      # Background thread for purging
    "narenas:4,"                    # One arena per NUMA node
    "dirty_decay_ms:5000,"         # Delay dirty page purging
    "muzzy_decay_ms:10000,"        # Delay muzzy page purging
    "thp:always"                   # Use transparent huge pages
)
```

## Memory Report Format

```json
{
  "memory_report": {
    "benchmark_id": "run_20260813_001",
    "process": {
      "peak_rss_mb": 5840,
      "avg_rss_mb": 5200,
      "final_rss_mb": 5100,
      "rss_growth_mb": 120,
      "peak_vms_mb": 12400
    },
    "components": {
      "model_weights_mb": 4096,
      "kv_cache": {
        "final_mb": 512,
        "peak_mb": 512,
        "peak_context_length": 4096,
        "growth_rate_mb_per_token": 0.00125
      },
      "activation_buffers_mb": 256,
      "runtime_overhead_mb": 320
    },
    "system": {
      "page_size_kb": 64,
      "numa_node": 0,
      "allocator": "jemalloc",
      "huge_pages": true
    },
    "bandwidth": {
      "achieved_gbps": 42.5,
      "peak_gbps": 51.2,
      "utilization_pct": 83.0
    },
    "leak_detection": {
      "leak_detected": false,
      "growth_rate_mb_per_s": 0.05,
      "r_squared": 0.12
    }
  }
}
```

## Validation

### OOM Boundary Testing

Determine the maximum context length before out-of-memory:

```python
def find_max_context_length(model_config, available_memory_mb, safety_margin=0.8):
    """Find maximum context length before OOM."""
    for ctx_len in [256, 512, 1024, 2048, 4096, 8192, 16384, 32768]:
        kv_cache_mb = estimate_kv_cache_memory(
            **model_config, context_length=ctx_len
        ) / (1024 * 1024)
        
        total_mb = model_config["weights_mb"] + kv_cache_mb + model_config["overhead_mb"]
        
        if total_mb > available_memory_mb * safety_margin:
            return ctx_len // 2  # Return last safe value
    
    return 32768
```

### Weight Loading Verification

Verify model weights are fully resident in memory before benchmarking:

```python
def verify_weights_loaded(profiler: ProcMemoryProfiler, expected_weights_mb: float):
    """Verify model weights are loaded into physical memory."""
    status = profiler.read_status()
    rss_mb = status.get("VmRSS", 0) / (1024 * 1024)
    
    if rss_mb < expected_weights_mb * 0.9:
        raise RuntimeError(
            f"Weights not fully loaded: RSS {rss_mb:.0f}MB < "
            f"expected {expected_weights_mb:.0f}MB"
        )
```
