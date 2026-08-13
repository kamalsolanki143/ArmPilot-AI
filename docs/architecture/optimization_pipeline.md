# Optimization Pipeline

How the auto-tuning engine finds optimal model configurations.

## Pipeline Overview

```
OptimizationConfig
     │
     ▼
┌─────────────────┐
│ Load Hardware   │  Detect CPU, memory, architecture
│ Profile         │  Match to Arm profile (N1, V2, A76)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate        │  Combine quantization × batch × threads
│ Candidates      │  Apply profile-specific constraints
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Benchmark       │  For each candidate:
│ Candidate       │  1. Load model with config
│                 │  2. Run N benchmark iterations
│                 │  3. Record metrics
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Score & Rank    │  Weight metrics by objective
│ Candidates      │  (throughput/latency/memory/balanced)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Select Best     │  Pick top candidate
│ Configuration   │  Apply constraints (max memory, min TPS)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate        │  Reasoning for each parameter change
│ Recommendations │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Store Result    │  Save optimization run + best config
└─────────────────┘
```

## Optimization Objectives

| Objective | Priority Metrics | Description |
|-----------|-----------------|-------------|
| `throughput` | TPS, TTFT, Memory | Maximize tokens/sec |
| `latency` | TTFT, P95, TPS | Minimize time to first token |
| `memory` | Memory, TPS, TTFT | Minimize memory consumption |
| `balanced` | TPS, TTFT, P95, Memory | Balance all metrics |

## Search Space

### Quantization Options

| Format | Size Reduction | Quality Impact |
|--------|---------------|----------------|
| FP16 | Baseline | None |
| Q8_0 | ~50% | Negligible |
| Q5_K_M | ~65% | Minimal |
| Q4_K_M | ~75% | Low |
| Q3_K_M | ~80% | Moderate |

### Batch Sizes

`1, 2, 4, 8, 16, 32, 64, 128, 256, 512`

### Thread Counts

`1, 2, 4, 6, 8, 12, 16`

### Context Lengths

`512, 1024, 2048, 4096`

## Hardware Profiles

### ARM Cortex-A76

- Max threads: 8
- Recommended batch: 4, 8, 16
- Recommended quantization: Q4_K_M, Q5_K_M, Q8_0

### ARM Neoverse N1

- Max threads: 64
- Recommended batch: 8, 16, 32, 64
- Recommended quantization: Q4_K_M, Q5_K_M

### ARM Neoverse V2

- Max threads: 64
- Recommended batch: 16, 32, 64, 128
- Recommended quantization: Q4_K_M, Q5_K_M, Q8_0

## Constraints

| Constraint | Default |
|-----------|---------|
| Max memory | 8192 MB |
| Min throughput | 1.0 TPS |
| Max TTFT | 2000 ms |
| Thermal throttle CPU | 90% |

## Scoring Algorithm

For each candidate, compute a weighted score based on the objective:

```python
# Throughput objective
score = (
    0.6 * normalize(tps) +       # Higher is better
    0.25 * (1 - normalize(ttft)) +  # Lower is better
    0.15 * (1 - normalize(memory))  # Lower is better
)
```

Candidates are ranked by score; the highest-scoring configuration is recommended.

## Output

```json
{
  "id": "OPT-0001",
  "status": "completed",
  "objective": "throughput",
  "best_candidate": {
    "quantization": "Q4_K_M",
    "batch_size": 8,
    "threads": 32,
    "tokens_per_second": 34.7,
    "ttft_ms": 48.2,
    "memory_mb": 3200
  },
  "improvements": {
    "tokens_per_second": "+169%",
    "ttft_ms": "-62%",
    "memory_mb": "-53%"
  },
  "all_candidates": [...]
}
```
