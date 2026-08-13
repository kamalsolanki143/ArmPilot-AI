# Component Diagram

Detailed view of the backend API server internals.

```mermaid
C4Component
    title Component Diagram - ArmPilot-AI Backend

    Container_Ext(frontend, "Web Dashboard", "React frontend")
    Container_Ext(cli, "CLI Tool", "Click commands")

    Container_Boundary(backend, "FastAPI Backend") {
        Component(api, "API Layer", "FastAPI Routes", "REST endpoints for inference, benchmark, optimization")
        Component(auth, "Auth Module", "JWT, OAuth2", "Authentication and authorization")
        Component(inference, "Inference Service", "Runtime Manager", "Model loading, chat completions, streaming")
        Component(benchmark, "Benchmark Service", "Runner, Metrics", "Performance measurement and profiling")
        Component(optimization, "Optimization Service", "Optimizer", "Auto-tuning parameters for best performance")
        Component(recommendation, "Recommendation Engine", "Rules, Scorer", "Bottleneck analysis and config suggestions")
        Component(reports, "Report Generator", "MD, HTML, PDF", "Export results in multiple formats")
        Component(monitoring, "Monitoring Module", "Health, Metrics", "System health and performance metrics")
        Component(database, "Database Layer", "SQLAlchemy", "SQLite persistence for all data")
        Component(workers, "Background Workers", "Async Tasks", "Long-running benchmark and optimization jobs")
    }

    System_Ext(runtimes, "Inference Runtimes", "llama.cpp, MLX, ONNX")
    System_Ext(hardware, "ARM64 Hardware", "Neoverse, Cortex")

    Rel(frontend, api, "API calls", "HTTP/WebSocket")
    Rel(cli, api, "API calls", "HTTP")
    Rel(api, auth, "Validates tokens")
    Rel(api, inference, "Handles requests")
    Rel(api, benchmark, "Triggers benchmarks")
    Rel(api, optimization, "Starts optimization")
    Rel(api, recommendation, "Gets recommendations")
    Rel(api, reports, "Generates reports")
    Rel(api, monitoring, "Health checks")
    Rel(inference, runtimes, "Loads models")
    Rel(benchmark, workers, "Spawns jobs")
    Rel(optimization, workers, "Spawns jobs")
    Rel(benchmark, database, "Stores results")
    Rel(optimization, database, "Stores results")
    Rel(recommendation, database, "Reads metrics")
    Rel(reports, database, "Reads data")
    Rel(monitoring, hardware, "Collects metrics")

    UpdateLayoutConfig($c4ShapeInRow="4", $c4BoundaryInRow="1")
```

## Components

| Component | Responsibility | Key Files |
|-----------|---------------|-----------|
| API Layer | REST endpoints | `backend/app/api/` |
| Auth Module | JWT/OAuth2 authentication | `backend/app/auth/` |
| Inference Service | Model loading and inference | `backend/app/inference/` |
| Benchmark Service | Performance measurement | `backend/app/benchmark/` |
| Optimization Service | Auto-tuning parameters | `backend/app/optimization/` |
| Recommendation Engine | Bottleneck analysis | `backend/app/recommendation/` |
| Report Generator | Export results | `backend/app/reports/` |
| Monitoring Module | Health and metrics | `backend/app/monitoring/` |
| Database Layer | SQLite persistence | `backend/app/database/` |
| Background Workers | Async task execution | `backend/app/workers/` |

## Interactions

1. **Request Flow** — API Layer routes to appropriate service
2. **Authentication** — Auth Module validates JWT tokens
3. **Inference** — Service loads models via runtime backends
4. **Benchmarking** — Workers execute long-running jobs
5. **Optimization** — Workers explore parameter space
6. **Recommendation** — Engine analyzes metrics and applies rules
7. **Reporting** — Generator creates formatted output
