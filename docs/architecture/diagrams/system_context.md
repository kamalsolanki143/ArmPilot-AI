# System Context Diagram

High-level view showing ArmPilot-AI's position in the ecosystem and its interactions with external actors.

```mermaid
C4Context
    title System Context Diagram - ArmPilot-AI

    Person(developer, "Developer", "Deploys and configures LLM inference on ARM hardware")
    Person(researcher, "ML Researcher", "Benchmarks and optimizes model performance")
    Person(ops, "Platform Operator", "Monitors and manages production inference")

    System(armpilot, "ArmPilot-AI Platform", "Arm64-first AI inference optimization platform for deploying, benchmarking, and auto-tuning open-source LLMs")

    System_Ext(llm_models, "LLM Model Hub", "Hugging Face, GGUF repositories")
    System_Ext(arm_hw, "ARM64 Hardware", "Neoverse, Cortex-A76, Apple Silicon")
    System_Ext(ci_cd, "CI/CD Pipeline", "GitHub Actions, automated testing")
    System_Ext(monitoring, "External Monitoring", "Prometheus, Grafana, Datadog")

    Rel(developer, armpilot, "Configures models and settings", "CLI / Dashboard")
    Rel(researcher, armpilot, "Runs benchmarks and optimizations", "REST API / Dashboard")
    Rel(ops, armpilot, "Monitors performance", "Dashboard / API")

    Rel(armpilot, llm_models, "Downloads GGUF models", "HTTPS")
    Rel(armpilot, arm_hw, "Executes inference", "NEON/SVE2 SIMD")
    Rel(ci_cd, armpilot, "Triggers benchmarks", "API")
    Rel(armpilot, monitoring, "Exports metrics", "Prometheus format")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Actors

| Actor | Role | Interface |
|-------|------|-----------|
| Developer | Deploys and configures LLM inference | CLI, Dashboard |
| ML Researcher | Benchmarks and optimizes model performance | REST API, Dashboard |
| Platform Operator | Monitors and manages production inference | Dashboard, API |

## External Systems

| System | Purpose | Integration |
|--------|---------|-------------|
| LLM Model Hub | Source for GGUF model files | HTTPS download |
| ARM64 Hardware | Target inference platform | NEON/SVE2 SIMD |
| CI/CD Pipeline | Automated testing and deployment | API triggers |
| External Monitoring | Observability stack | Prometheus metrics |

## Key Interactions

1. **Model Acquisition** — Platform downloads GGUF models from external repositories
2. **Inference Execution** — Direct hardware access for optimized ARM64 inference
3. **Metrics Export** — Prometheus-compatible metrics for external monitoring
4. **CI/CD Integration** — API-driven benchmark triggers for automated testing
