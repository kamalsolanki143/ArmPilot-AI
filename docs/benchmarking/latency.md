# Latency Measurement and Percentile Calculations

How ArmPilot-AI measures, computes, and reports latency distributions for LLM inference on Arm Neoverse.

## Latency Components

LLM inference latency consists of three sequential phases:

```
┌──────────┐    ┌──────────────┐    ┌─────────────┐
│ Prefill  │───▶│  First Token │───▶│   Decode    │
│ (input   │    │  Emitted     │    │  (per-token │
│  tokens) │    │              │    │   generation)│
└──────────┘    └──────────────┘    └─────────────┘
     │                                     │
     ▼                                     ▼
  TTFT (includes prefill)         ITL × output_tokens
```

| Component | Symbol | Definition |
|-----------|--------|------------|
| Time to First Token | TTFT | Request submission → first token emitted |
| Inter-Token Latency | ITL | Average time between consecutive decode tokens |
| Time Per Output Token | TPOT | Average single-token decode time |
| Total Request Latency | TRL | TTFT + (TPOT × output_token_count) |

## High-Resolution Timing

### Clock Source Selection

ArmPilot-AI uses `CLOCK_MONOTONIC_RAW` for measurement, which is not subject to NTP adjustments or leap second corrections.

```python
import ctypes
import ctypes.util

# Linux clock_gettime with CLOCK_MONOTONIC_RAW (id=4)
CLOCK_MONOTONIC_RAW = 4

class HighResClock:
    """Microsecond-resolution monotonic clock for latency measurement."""
    
    def __init__(self):
        self._clock_gettime = ctypes.CDLL(
            ctypes.util.find_library("c"),
            use_errno=True
        ).clock_gettime
        self._clock_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_timespec)]
        self._clock_gettime.restype = ctypes.c_int
    
    def now_ns(self) -> int:
        ts = ctypes.c_timespec()
        self._clock_gettime(CLOCK_MONOTONIC_RAW, ctypes.byref(ts))
        return ts.tv_sec * 1_000_000_000 + ts.tv_nsec

clock = HighResClock()

def measure_latency(func, *args, **kwargs):
    """Wrap a function call with high-resolution timing."""
    start_ns = clock.now_ns()
    result = func(*args, **kwargs)
    end_ns = clock.now_ns()
    return result, (end_ns - start_ns) / 1e6  # Return milliseconds
```

### Streaming Token Timestamps

For streaming inference, capture a timestamp at each token emission:

```python
class TokenTimestampCollector:
    """Collects per-token timestamps during streaming inference."""
    
    def __init__(self):
        self.timestamps_ns = []
    
    def on_token(self, token: str):
        self.timestamps_ns.append(clock.now_ns())
    
    @property
    def ttft_ms(self) -> float:
        if len(self.timestamps_ns) < 2:
            return 0.0
        return (self.timestamps_ns[0] - self.request_start_ns) / 1e6
    
    @property
    def itl_values_ms(self) -> list[float]:
        if len(self.timestamps_ns) < 2:
            return []
        return [
            (self.timestamps_ns[i+1] - self.timestamps_ns[i]) / 1e6
            for i in range(len(self.timestamps_ns) - 1)
        ]
    
    @property
    def tpot_ms(self) -> float:
        itl = self.itl_values_ms
        return sum(itl) / len(itl) if itl else 0.0
    
    @property
    def total_latency_ms(self) -> float:
        if not self.timestamps_ns:
            return 0.0
        return (self.timestamps_ns[-1] - self.request_start_ns) / 1e6
```

## Percentile Calculation

### Methodology

ArmPilot-AI uses the nearest-rank method for percentile computation, which is deterministic and reproducible across runs.

```python
import math

def calculate_percentiles(values: list[float], percentiles: list[int]) -> dict[int, float]:
    """Compute percentiles using the nearest-rank method.
    
    For percentile p, the value at rank r = ceil(p/100 * N) is returned,
    where N is the number of samples.
    """
    sorted_values = sorted(values)
    n = len(sorted_values)
    result = {}
    
    for p in percentiles:
        if n == 0:
            result[p] = 0.0
        else:
            rank = math.ceil(p / 100.0 * n)
            rank = min(rank, n)  # Clamp to maximum index
            result[p] = sorted_values[rank - 1]  # 0-indexed
    
    return result
```

### Alternative: Linear Interpolation

For smoother percentile curves (e.g., for CDF visualization), use linear interpolation:

```python
def percentile_interpolated(values: list[float], p: float) -> float:
    """Compute percentile using linear interpolation between ranks."""
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n == 0:
        return 0.0
    if n == 1:
        return sorted_values[0]
    
    # Virtual index: p/100 * (N-1)
    virtual_index = p / 100.0 * (n - 1)
    lower_index = int(math.floor(virtual_index))
    upper_index = min(lower_index + 1, n - 1)
    fraction = virtual_index - lower_index
    
    return sorted_values[lower_index] + fraction * (sorted_values[upper_index] - sorted_values[lower_index])
```

### Recommended Percentiles

| Percentile | Use Case | Why |
|------------|----------|-----|
| P50 | Typical user experience | Median latency for most requests |
| P90 | SLA monitoring | Captures the slow 10% |
| P95 | Performance budget | Identifies tail latency before P99 |
| P99 | Outlier detection | Catches worst-case without extreme outliers |
| P99.9 | SRE alerting | Extreme outliers that indicate system issues |

## Latency Collection Pipeline

### Per-Request Measurement

```python
class LatencyCollector:
    """Collects latency metrics across all inference requests."""
    
    def __init__(self):
        self.ttft_values = []
        self.itl_values = []
        self.tpot_values = []
        self.total_latency_values = []
        self.token_counts = []
    
    def record_request(self, collector: TokenTimestampCollector, token_count: int):
        self.ttft_values.append(collector.ttft_ms)
        self.tpot_values.append(collector.tpot_ms)
        self.total_latency_values.append(collector.total_latency_ms)
        self.token_counts.append(token_count)
        
        for itl in collector.itl_values_ms:
            self.itl_values.append(itl)
    
    def summary(self, percentiles: list[int] = [50, 90, 95, 99]) -> dict:
        return {
            "ttft": {
                "mean_ms": statistics.mean(self.ttft_values),
                "stdev_ms": statistics.stdev(self.ttft_values) if len(self.ttft_values) > 1 else 0,
                "percentiles_ms": calculate_percentiles(self.ttft_values, percentiles),
            },
            "tpot": {
                "mean_ms": statistics.mean(self.tpot_values),
                "stdev_ms": statistics.stdev(self.tpot_values) if len(self.tpot_values) > 1 else 0,
                "percentiles_ms": calculate_percentiles(self.tpot_values, percentiles),
            },
            "total_latency": {
                "mean_ms": statistics.mean(self.total_latency_values),
                "stdev_ms": statistics.stdev(self.total_latency_values) if len(self.total_latency_values) > 1 else 0,
                "percentiles_ms": calculate_percentiles(self.total_latency_values, percentiles),
            },
            "sample_count": len(self.ttft_values),
        }
```

### Confidence Intervals

Report 95% confidence intervals for mean latency estimates:

```python
import scipy.stats

def mean_confidence_interval(values: list[float], confidence: float = 0.95) -> tuple[float, float]:
    """Compute 95% CI for the mean using t-distribution."""
    n = len(values)
    if n < 2:
        return (statistics.mean(values), statistics.mean(values))
    
    mean = statistics.mean(values)
    sem = scipy.stats.sem(values)  # Standard error of mean
    ci = sem * scipy.stats.t.ppf((1 + confidence) / 2, df=n-1)
    
    return (mean - ci, mean + ci)
```

## Arm-Specific Latency Considerations

### Clock Resolution

Arm Neoverse counters run at the CPU core frequency (typically 2.6-3.3 GHz). Verify counter resolution:

```bash
# Check CPU frequency
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq

# Verify clock resolution
sudo perf stat -e cpu-cycles:u -a sleep 0.001
```

### Interrupt Latency

Background OS interrupts can cause P99 spikes. Mitigate with:

```bash
# Isolate benchmark cores from kernel scheduling
sudo systemctl set-property user-$(id -u) CPUAffinity=4-7

# Disable turbo boost for consistent frequencies
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### SVE Vector Length Effects

On Arm Neoverse V2, SVE vector length (128-256 bits) affects compute latency:

| SVE VL | Attention Latency (ms) | Impact |
|--------|----------------------|--------|
| 128-bit | 45.2 | Baseline |
| 192-bit | 34.8 | -23% |
| 256-bit | 28.1 | -38% |

Report SVE vector length alongside latency measurements.

### Prefill vs Decode Latency Split

Arm Neoverse's wide decode pipeline (6-8 wide on V2) benefits decode more than prefill. When analyzing latency:

- **Prefill latency** scales with `O(input_length)` and is compute-bound
- **Decode latency** scales with `O(1)` per token but is memory-bound for large models
- On Arm, decode benefits more from SIMD optimization than prefill

## Latency Report Format

```json
{
  "latency_report": {
    "benchmark_id": "run_20260813_001",
    "sample_count": 150,
    "ttft_ms": {
      "mean": 125.4,
      "stdev": 12.3,
      "min": 98.2,
      "max": 210.5,
      "p50": 122.1,
      "p90": 145.3,
      "p95": 158.7,
      "p99": 198.4,
      "ci_95": [123.1, 127.7]
    },
    "tpot_ms": {
      "mean": 23.4,
      "stdev": 2.1,
      "min": 19.8,
      "max": 31.2,
      "p50": 22.9,
      "p90": 26.1,
      "p95": 27.8,
      "p99": 29.9,
      "ci_95": [23.1, 23.7]
    },
    "total_latency_ms": {
      "mean": 1890.2,
      "stdev": 245.6,
      "min": 1200.0,
      "max": 3200.0,
      "p50": 1820.0,
      "p90": 2280.0,
      "p95": 2560.0,
      "p99": 3050.0,
      "ci_95": [1850.0, 1930.0]
    },
    "platform": {
      "cpu": "Neoverse-V2",
      "clock_freq_ghz": 3.0,
      "sve_vl_bits": 256
    }
  }
}
```

## Validation

To validate latency measurements:

1. **Round-trip consistency**: Measure loopback latency (no model) to establish baseline instrumentation overhead
2. **Repeatability**: Run 3+ times with identical parameters; coefficient of variation should be < 5%
3. **Clock drift**: Compare against wall clock over 60+ second runs; drift should be < 0.01%
4. **Token counting**: Verify token count matches tokenizer output for the same prompt

```bash
# Quick validation script
python -c "
from benchmark import LatencyCollector, HighResClock
import time

clock = HighResClock()
# Measure overhead of timing itself
start = clock.now_ns()
for _ in range(10000):
    clock.now_ns()
end = clock.now_ns()
print(f'Clock overhead: {(end-start)/10000:.1f} ns per call')
"
```
