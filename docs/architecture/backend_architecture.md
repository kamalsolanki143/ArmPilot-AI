# Backend Architecture

Detailed breakdown of the Python backend module layout.

## Module Structure

```
backend/
├── main.py                    # FastAPI app factory and entry point
├── requirements.txt           # Python dependencies
├── app/
│   ├── __init__.py
│   ├── api/                   # HTTP route handlers
│   │   ├── router.py          # Central API router
│   │   ├── auth.py            # Auth endpoints (register, login, OAuth)
│   │   ├── inference.py       # OpenAI-compatible inference API
│   │   ├── benchmark.py       # Benchmark run/management API
│   │   ├── optimization.py    # Optimization run/management API
│   │   ├── recommendation.py  # Recommendation query API
│   │   ├── reports.py         # Report generation/export API
│   │   ├── health.py          # Health check and system metrics
│   │   ├── history.py         # Run history API
│   │   ├── metrics.py         # Detailed metrics API
│   │   ├── settings.py        # Runtime settings API
│   │   └── websocket.py       # WebSocket for live updates
│   ├── auth/                  # Authentication subsystem
│   │   ├── authentication.py  # get_current_user dependency
│   │   ├── jwt.py             # JWT token creation/verification
│   │   ├── oauth.py           # OAuth2 GitHub flow
│   │   ├── password.py        # Password hashing (bcrypt)
│   │   └── permissions.py     # Role-based access control
│   ├── benchmark/             # Benchmarking engine
│   │   ├── runner.py          # Benchmark orchestrator
│   │   ├── latency.py         # Latency measurement
│   │   ├── throughput.py      # Throughput measurement
│   │   ├── ttft.py            # Time-to-first-token measurement
│   │   ├── cpu_usage.py       # CPU utilization tracking
│   │   ├── memory.py          # Memory usage tracking
│   │   ├── load_test.py       # Concurrent load testing
│   │   └── exporter.py        # Result export utilities
│   ├── cache/                 # Caching layer
│   ├── cli/                   # Click CLI commands
│   │   ├── main.py            # CLI group and entry point
│   │   ├── benchmark.py       # Benchmark CLI commands
│   │   ├── optimize.py        # Optimization CLI commands
│   │   ├── deploy.py          # Deployment CLI commands
│   │   ├── report.py          # Report CLI commands
│   │   ├── lab.py             # Experimental lab commands
│   │   └── cleanup.py         # Data cleanup commands
│   ├── core/                  # Core infrastructure
│   │   ├── config.py          # Pydantic Settings (env + .env)
│   │   ├── events.py          # Application events
│   │   ├── exceptions.py      # Custom exception classes + handlers
│   │   ├── logger.py          # Logger singleton
│   │   ├── logging_config.py  # Logging configuration loader
│   │   ├── middleware.py       # CORS + request timing middleware
│   │   ├── scheduler.py       # Background task scheduler
│   │   ├── security.py        # Security utilities
│   │   ├── startup.py         # Startup event handler
│   │   └── shutdown.py        # Shutdown event handler
│   ├── database/              # Data persistence
│   │   ├── base.py            # SQLAlchemy base model
│   │   ├── database.py        # Database engine/session
│   │   ├── migrations.py      # Schema migrations
│   │   ├── seed.py            # Seed data
│   │   ├── session.py         # Session management
│   │   └── storage.py         # File-based JSON storage
│   ├── inference/             # Inference engine
│   │   ├── runtime.py         # Runtime abstraction layer
│   │   ├── loader.py          # Model file discovery/loading
│   │   ├── generator.py       # Token generation
│   │   ├── pipeline.py        # Inference pipeline
│   │   ├── streaming.py       # SSE streaming support
│   │   ├── batching.py        # Request batching
│   │   ├── tokenizer.py       # Token counting
│   │   ├── scheduler.py       # Request scheduling
│   │   ├── request_handler.py # Request preprocessing
│   │   └── response_handler.py# Response postprocessing
│   ├── integrations/          # External service integrations
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── user.py            # User model
│   │   ├── benchmark.py       # Benchmark result model
│   │   ├── inference.py       # Inference session model
│   │   ├── optimization.py    # Optimization run model
│   │   ├── model_profile.py   # Model hardware profile
│   │   ├── history.py         # Run history model
│   │   ├── report.py          # Report model
│   │   └── settings.py        # Settings model
│   ├── monitoring/            # Observability
│   │   ├── health_monitor.py  # Health check logic
│   │   ├── metrics.py         # System metrics collection
│   │   ├── profiler.py        # Performance profiling
│   │   ├── telemetry.py       # Usage telemetry
│   │   └── tracing.py         # Request tracing
│   ├── optimization/          # Auto-tuning engine
│   │   ├── optimizer.py       # Optimization orchestrator
│   │   ├── auto_tuner.py      # Auto-tuning logic
│   │   ├── arm_profiles.py    # Arm hardware profiles
│   │   ├── profile_manager.py # Profile selection logic
│   │   ├── quantization.py    # Quantization search
│   │   ├── batch_optimizer.py # Batch size optimization
│   │   ├── thread_optimizer.py# Thread count optimization
│   │   ├── kv_cache_optimizer.py # KV cache tuning
│   │   ├── cpu_affinity.py    # CPU affinity optimization
│   │   └── runtime_optimizer.py  # Runtime selection
│   ├── performix/             # Performance index
│   ├── recommendation/        # AI recommendation engine
│   │   ├── engine.py          # Recommendation orchestrator
│   │   ├── analyzer.py        # Metric analysis
│   │   ├── advisor.py         # Advice generation
│   │   ├── rules.py           # Rule definitions
│   │   ├── scorer.py          # Recommendation scoring
│   │   └── profile_selector.py# Hardware profile selection
│   ├── reports/               # Report generation
│   │   ├── report_builder.py  # Report orchestrator
│   │   ├── markdown.py        # Markdown export
│   │   ├── html.py            # HTML export
│   │   ├── pdf.py             # PDF export
│   │   ├── csv.py             # CSV export
│   │   ├── charts.py          # Chart generation
│   │   └── exporter.py        # Export manager
│   ├── schemas/               # Pydantic request/response schemas
│   │   ├── auth.py            # Auth schemas
│   │   ├── inference.py       # Inference schemas (OpenAI-compatible)
│   │   ├── benchmark.py       # Benchmark schemas
│   │   ├── optimization.py    # Optimization schemas
│   │   ├── recommendation.py  # Recommendation schemas
│   │   ├── reports.py         # Report schemas
│   │   ├── metrics.py         # Metrics schemas
│   │   ├── history.py         # History schemas
│   │   └── settings.py        # Settings schemas
│   ├── services/              # Business logic layer
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── inference_service.py# Inference orchestration
│   │   ├── benchmark_service.py# Benchmark orchestration
│   │   ├── optimization_service.py# Optimization orchestration
│   │   ├── recommendation_service.py# Recommendation logic
│   │   ├── report_service.py  # Report generation logic
│   │   ├── model_service.py   # Model management
│   │   ├── metrics_service.py # Metrics collection
│   │   ├── history_service.py # History management
│   │   ├── deployment_service.py# Deployment automation
│   │   └── performix_service.py# Performance index
│   ├── utils/                 # Utility functions
│   │   └── hardware.py        # Hardware detection (ARM, CPU, RAM)
│   └── workers/               # Background workers
```

## Request Flow

```
HTTP Request
    │
    ▼
┌──────────────┐
│  Middleware   │  CORS, Request Timing
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  API Router  │  Routes to sub-router by prefix
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Route Handler│  Input validation (Pydantic)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Service    │  Business logic
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Subsystem   │  Inference / Benchmark / Optimization
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Storage    │  SQLite + JSON files
└──────────────┘
```

## Key Patterns

- **Service Layer** — All business logic lives in `services/`; API handlers are thin
- **Pydantic Schemas** — Every request/response has a typed schema
- **Background Tasks** — Long operations use FastAPI's `BackgroundTasks`
- **Singleton Services** — Services are instantiated as module-level singletons
- **Custom Exceptions** — All errors derive from `ArmPilotError` with structured codes
