# Data Flow Diagram

Shows how data moves through the ArmPilot-AI system.

```mermaid
flowchart TD
    subgraph Users["User Actors"]
        U1[Developer]
        U2[Researcher]
        U3[Operator]
    end

    subgraph Interfaces["User Interfaces"]
        UI1[Web Dashboard]
        UI2[CLI Tool]
        UI3[REST API]
    end

    subgraph Core["Core Services"]
        S1[Inference Service]
        S2[Benchmark Service]
        S3[Optimization Service]
        S4[Recommendation Engine]
        S5[Report Generator]
    end

    subgraph Storage["Data Storage"]
        DB[(SQLite Database)]
        FS[Filesystem<br/>GGUF Models]
        LOG[Log Files]
    end

    subgraph External["External Systems"]
        EXT1[Model Hub]
        EXT2[ARM64 Hardware]
        EXT3[Monitoring]
    end

    U1 --> UI1
    U1 --> UI2
    U2 --> UI1
    U2 --> UI3
    U3 --> UI1

    UI1 -->|HTTP/WebSocket| S1
    UI1 -->|HTTP/WebSocket| S2
    UI1 -->|HTTP/WebSocket| S3
    UI2 -->|HTTP| S1
    UI2 -->|HTTP| S2
    UI2 -->|HTTP| S3
    UI3 -->|HTTP| S1
    UI3 -->|HTTP| S2
    UI3 -->|HTTP| S3

    S1 -->|Load Model| FS
    S1 -->|Execute| EXT2
    S2 -->|Store Results| DB
    S2 -->|Read Config| DB
    S3 -->|Store Configs| DB
    S3 -->|Trigger| S2
    S4 -->|Read Metrics| DB
    S4 -->|Apply Rules| S4
    S5 -->|Read Data| DB
    S5 -->|Export| EXT1

    S1 -->|Logs| LOG
    S2 -->|Logs| LOG
    S3 -->|Logs| LOG

    EXT2 -->|Metrics| EXT3
    S2 -->|Export| EXT3

    style Users fill:#e1f5fe
    style Interfaces fill:#f3e5f5
    style Core fill:#e8f5e8
    style Storage fill:#fff3e0
    style External fill:#fce4ec
```

## Data Flows

### Inference Flow

1. User sends chat completion request
2. API validates request schema
3. Inference Service loads model (if not loaded)
4. Model executes on ARM64 hardware
5. Response streamed back to user
6. Request logged to database

### Benchmark Flow

1. User triggers benchmark run
2. Benchmark Service reads configuration
3. Runner sends N requests to Inference Service
4. Metrics collected (latency, throughput, memory)
5. Results stored in database
6. Recommendations triggered

### Optimization Flow

1. User starts optimization sweep
2. Optimization Service generates candidate configs
3. For each candidate:
   - Config applied to Inference Service
   - Benchmark executed
   - Results recorded
4. Best config identified and saved
5. Recommendations generated

### Report Flow

1. User requests report generation
2. Report Generator reads benchmark/optimization data
3. Data formatted as Markdown/HTML/PDF
4. Report exported to filesystem or external system

## Data Models

| Entity | Description | Storage |
|--------|-------------|---------|
| BenchmarkRun | Complete benchmark execution | SQLite |
| BenchmarkResult | Individual metric result | SQLite |
| OptimizationSweep | Optimization experiment | SQLite |
| OptimizationCandidate | Parameter configuration | SQLite |
| Recommendation | AI-generated suggestion | SQLite |
| ModelInfo | GGUF model metadata | Filesystem |
| SystemProfile | Hardware configuration | SQLite |
