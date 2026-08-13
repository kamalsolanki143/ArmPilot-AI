# System Architecture

High-level overview of ArmPilot-AI's system architecture.

## System Context

ArmPilot-AI sits between the user (via browser or CLI) and Arm64 hardware, providing an intelligent layer for LLM inference optimization. It is designed as a self-contained platform that can run entirely on a single Arm64 server.

```
┌─────────────────────────────────────────────────────────┐
│                      Users                               │
│  Browser (Dashboard) · CLI · API Clients · CI/CD         │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTPS / HTTP
┌───────────────────────▼─────────────────────────────────┐
│                  ArmPilot-AI Platform                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   Web UI    │  │  REST API   │  │    CLI (Click)  │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
│         │                │                   │          │
│  ┌──────▼────────────────▼───────────────────▼────────┐ │
│  │              Application Layer                      │ │
│  │  ┌──────────┐ ┌──────────┐ ┌────────────────────┐ │ │
│  │  │ Inference│ │Benchmark │ │   Optimization     │ │ │
│  │  │ Service  │ │ Service  │ │     Service        │ │ │
│  │  └────┬─────┘ └────┬─────┘ └─────────┬──────────┘ │ │
│  │       │             │                  │            │ │
│  │  ┌────▼─────────────▼──────────────────▼──────────┐ │ │
│  │  │           Recommendation Engine                │ │ │
│  │  └────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────┘ │
│                        │                                 │
│  ┌─────────────────────▼──────────────────────────────┐  │
│  │              Runtime Layer                          │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │  │
│  │  │llama.cpp │  │   MLX    │  │  ONNX Runtime    │  │  │
│  │  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │  │
│  └───────┼──────────────┼─────────────────┼────────────┘  │
└──────────┼──────────────┼─────────────────┼───────────────┘
           │              │                 │
┌──────────▼──────────────▼─────────────────▼───────────────┐
│              Arm64 Hardware (NEON / SVE2)                   │
│  Cortex-A76 · Neoverse N1 · Neoverse V2 · Apple Silicon   │
└────────────────────────────────────────────────────────────┘
```

## Core Subsystems

| Subsystem | Responsibility | Key Files |
|-----------|---------------|-----------|
| **Inference** | Model loading, chat completions, streaming | `backend/app/inference/`, `backend/app/api/inference.py` |
| **Benchmarking** | Performance measurement and profiling | `backend/app/benchmark/`, `backend/app/api/benchmark.py` |
| **Optimization** | Auto-tuning parameters for best performance | `backend/app/optimization/`, `backend/app/api/optimization.py` |
| **Recommendation** | Bottleneck analysis and config suggestions | `backend/app/recommendation/`, `backend/app/api/recommendation.py` |
| **Reports** | Export results as Markdown, HTML, PDF | `backend/app/reports/` |
| **Auth** | JWT authentication, OAuth2 (GitHub) | `backend/app/auth/`, `backend/app/api/auth.py` |
| **Monitoring** | Health checks, metrics, profiling | `backend/app/monitoring/`, `backend/app/api/health.py` |
| **CLI** | Command-line interface for all operations | `backend/app/cli/` |
| **Database** | SQLite-based persistence | `backend/app/database/` |

## Data Flow

1. **User submits inference request** → API validates → Runtime executes on hardware → Response streamed back
2. **Benchmark triggered** → Runner sends N requests → Collects metrics → Stores results → Triggers recommendations
3. **Optimization started** → Generates candidate configs → Benchmarks each → Ranks results → Saves best config
4. **Recommendation generated** → Analyzes metrics → Applies rules → Produces reasoning → User applies or exports

## Design Principles

1. **Arm64-First** — All defaults and profiles target ARM architecture; x86 is a secondary path
2. **OpenAI-Compatible** — The inference API is a drop-in replacement for OpenAI's chat completions
3. **Zero-Config Defaults** — Sensible defaults work out of the box; advanced users can tune everything
4. **Async Background Tasks** — Long-running operations (benchmarks, optimizations) execute in background with polling
5. **Modular Runtime** — Inference backends are pluggable; add new runtimes by implementing the runtime interface
