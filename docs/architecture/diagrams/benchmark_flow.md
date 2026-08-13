# Benchmark Pipeline Flow

Detailed flow of how benchmarks are executed and results collected.

```mermaid
flowchart TD
    Start([Benchmark Trigger]) --> Config[Load Configuration]
    Config --> Validate[Validate Parameters]
    Validate --> Init[Initialize Metrics Collection]

    Init --> Loop{For Each Request}
    Loop --> |More Requests| Send[Send Inference Request]
    Send --> Collect[Collect Metrics]
    Collect --> |TTFT| TTFT[Time to First Token]
    Collect --> |Latency| Latency[End-to-End Latency]
    Collect --> |Throughput| Throughput[Tokens per Second]
    Collect --> |Memory| Memory[Memory Usage]
    Collect --> |CPU| CPU[CPU Utilization]

    TTFT --> Store[Store Results]
    Latency --> Store
    Throughput --> Store
    Memory --> Store
    CPU --> Store

    Store --> Loop

    Loop --> |Complete| Aggregate[Aggregate Metrics]
    Aggregate --> Calculate[Calculate Statistics]
    Calculate --> |Mean| Mean[Average Values]
    Calculate --> |P50| P50[Median Values]
    Calculate --> |P95| P95[95th Percentile]
    Calculate --> |P99| P99[99th Percentile]

    Mean --> Save[Save to Database]
    P50 --> Save
    P95 --> Save
    P99 --> Save

    Save --> Recommend[Trigger Recommendations]
    Recommend --> Done([Benchmark Complete])

    style Start fill:#4caf50,color:white
    style Done fill:#2196f3,color:white
```

## Benchmark Metrics

### Latency Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| TTFT | Time to first token | < 100ms |
| Latency (P50) | Median response time | < 500ms |
| Latency (P95) | 95th percentile | < 1000ms |
| Latency (P99) | 99th percentile | < 2000ms |

### Throughput Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Tokens/sec | Generation speed | > 50 tokens/sec |
| Requests/sec | Concurrent handling | > 10 req/sec |
| Batch efficiency | Batch vs sequential | > 80% |

### Resource Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| CPU Usage | Processor utilization | < 90% |
| Memory Usage | RAM consumption | < 80% |
| Memory Peak | Maximum memory | < 90% |

## Benchmark Configuration

```yaml
benchmark:
  model: "llama-3.2-3b"
  threads: 8
  batch_size: 512
  num_requests: 10
  max_tokens: 128
  context_length: 2048
  warmup_runs: 3
  timeout: 30
```

## Results Storage

```mermaid
erDiagram
    BenchmarkRun ||--o{ BenchmarkResult : contains
    BenchmarkRun ||--o{ SystemMetrics : includes
    BenchmarkRun ||--|| ModelInfo : uses

    BenchmarkRun {
        string id PK
        string model_name
        datetime created_at
        json config
        string status
    }

    BenchmarkResult {
        string id PK
        string run_id FK
        string metric_type
        float value
        int request_index
    }

    SystemMetrics {
        string id PK
        string run_id FK
        float cpu_usage
        float memory_usage
        float memory_peak
    }
```

## Benchmark Scenarios

| Scenario | Description | Use Case |
|----------|-------------|----------|
| Latency | Single request response time | Interactive chat |
| Throughput | Concurrent request handling | Production load |
| Memory | Memory usage under load | Resource planning |
| Endurance | Long-running stability | Production readiness |
