# ArmPilot-AI

An Arm64-first AI inference optimization platform for deploying, benchmarking, and auto-tuning open-source LLMs on ARM architecture with intelligent performance recommendations.

## Overview

ArmPilot-AI is purpose-built for Arm Neoverse and Cortex processors, providing a complete pipeline from model deployment through automated performance optimization. It combines an OpenAI-compatible inference API, a comprehensive benchmarking suite, and a smart optimization engine that explores quantization, threading, and memory configurations to find the optimal settings for your specific hardware.

### Key Features

- **OpenAI-Compatible API** — Drop-in replacement for `/v1/chat/completions` with streaming support
- **Multi-Runtime Inference** — Supports llama.cpp (GGUF), MLX, and ONNX Runtime backends
- **Automated Benchmarking** — TTFT, throughput, latency percentiles, CPU/memory profiling
- **Smart Optimization** — Auto-tunes quantization, batch size, thread count, and KV cache
- **Arm Hardware Profiles** — Pre-configured profiles for Cortex-A76, Neoverse N1, Neoverse V2
- **AI Recommendations** — Analyzes bottlenecks and suggests configuration changes with reasoning
- **Full-Stack Dashboard** — React frontend with real-time charts and dark/light themes
- **REST API + CLI** — Both programmatic and command-line interfaces

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  Dashboard · Inference · Benchmark · Optimization · Reports  │
│                     Vite + Tailwind CSS                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                     FastAPI Backend                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐   │
│  │ Inference│ │Benchmark │ │Optimize  │ │Recommendation│   │
│  │   API    │ │   API    │ │   API    │ │     API      │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬───────┘   │
│       │             │            │               │           │
│  ┌────▼─────┐ ┌─────▼────┐ ┌───▼──────┐ ┌──────▼───────┐  │
│  │ Runtime  │ │ Runner   │ │Optimizer │ │    Engine    │  │
│  │ Manager  │ │          │ │          │ │              │  │
│  └────┬─────┘ └─────┬────┘ └───┬──────┘ └──────┬───────┘  │
│       │             │          │                 │          │
│  ┌────▼─────────────▼──────────▼─────────────────▼───────┐  │
│  │              llama.cpp / MLX / ONNX Runtime            │  │
│  └────────────────────────────────────────────────────────┘  │
│       │                                                      │
│  ┌────▼──────────────────────────────────────────────────┐  │
│  │          Arm64 Hardware (NEON/SVE2/Neoverse)          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Pydantic v2, Uvicorn |
| Frontend | React 19, Vite 8, Tailwind CSS v4, Recharts |
| Inference | llama.cpp (llama-cpp-python), MLX, ONNX Runtime |
| CLI | Click |
| Auth | JWT (HS256), OAuth2 (GitHub) |
| Database | SQLite (via SQLAlchemy) |
| Container | Docker, Docker Compose, Nginx |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend)
- pnpm (for frontend)
- A `.gguf` model file (e.g., TinyLlama, Phi-2, Mistral)

### Setup

```bash
# Clone the repository
git clone https://github.com/krrishyaduka/ArmPilot-AI.git
cd ArmPilot-AI

# Run the setup script
bash scripts/setup.sh

# Place a model file
cp /path/to/model.gguf models/

# Start the server
bash scripts/run_server.sh
```

### Verify Installation

```bash
# Check system info
python3 -m app.cli.main info

# List available models
python3 -m app.cli.main models

# Open API docs
open http://localhost:8000/docs
```

## Installation

### Backend

```bash
cd backend
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

### Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

## API Reference

### Base URL

```
http://localhost:8000
```

### Authentication

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "user", "password": "pass123"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'
```

### Chat Completions (OpenAI-Compatible)

```bash
# List models
curl http://localhost:8000/v1/models

# Load a model
curl -X POST http://localhost:8000/v1/models/llama-3.2-3b/load

# Chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.2-3b",
    "messages": [
      {"role": "user", "content": "What are the advantages of ARM64 for AI?"}
    ],
    "max_tokens": 256,
    "temperature": 0.7
  }'

# Streaming
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.2-3b",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

### Benchmarks

```bash
# Run benchmark
curl -X POST http://localhost:8000/api/benchmark/run \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "model": "llama-3.2-3b",
      "threads": 8,
      "batch_size": 512,
      "num_requests": 10,
      "max_tokens": 128
    }
  }'

# Get results
curl http://localhost:8000/api/benchmark/latest
```

### Optimization

```bash
# Run optimization
curl -X POST http://localhost:8000/api/optimization/run \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "model": "llama-3.2-3b",
      "objective": "throughput",
      "max_candidates": 8,
      "benchmark_per_candidate": 5
    }
  }'

# Poll progress
curl http://localhost:8000/api/optimization/progress
```

## CLI Usage

```bash
# Show system info
python3 -m app.cli.main info

# List models
python3 -m app.cli.main models

# Start API server
python3 -m app.cli.main serve --port 8000 --reload

# Run benchmark
python3 -m app.cli.main benchmark run \
  --model llama-3.2-3b \
  --threads 8 \
  --batch-size 512

# Run optimization sweep
python3 -m app.cli.main optimize run \
  --model llama-3.2-3b \
  --objective throughput \
  --max-candidates 8

# Generate report
python3 -m app.cli.main report generate --benchmark-id RUN-0042

# Cleanup old data
python3 -m app.cli.main cleanup --older-than 30d
```

### Shell Scripts

```bash
bash scripts/setup.sh              # Full project setup
bash scripts/run_server.sh         # Start API server
bash scripts/benchmark.sh          # Run benchmark
bash scripts/optimize.sh           # Run optimization
bash scripts/export_report.sh      # Export report
bash scripts/test_all.sh           # Run all tests
bash scripts/clean.sh              # Clean temp files
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ARMPILOT_HOST` | `0.0.0.0` | Server bind host |
| `ARMPILOT_PORT` | `8000` | Server port |
| `ARMPILOT_DEBUG` | `false` | Enable debug mode |
| `ARMPILOT_LOG_LEVEL` | `INFO` | Logging level |
| `ARMPILOT_MODELS_DIR` | `models` | Model files directory |
| `ARMPILOT_DEFAULT_RUNTIME` | `llama.cpp` | Default inference runtime |
| `ARMPILOT_DEFAULT_THREADS` | `4` | Default thread count |
| `ARMPILOT_DEFAULT_BATCH_SIZE` | `512` | Default batch size |
| `ARMPILOT_DEFAULT_CONTEXT_LENGTH` | `2048` | Default context window |
| `ARMPILOT_JWT_SECRET_KEY` | (required) | JWT signing secret |

### Configuration Files

| File | Purpose |
|------|---------|
| `configs/inference.yaml` | Inference runtime settings |
| `configs/benchmark.yaml` | Benchmark scenarios and thresholds |
| `configs/optimization.yaml` | Optimization search space and profiles |
| `configs/production.yaml` | Production environment settings |
| `configs/development.yaml` | Development environment settings |
| `configs/logging.yaml` | Python logging configuration |

### Hardware Profiles

| Profile | Max Threads | Recommended Batch | Quantizations |
|---------|-------------|-------------------|---------------|
| Cortex-A76 | 8 | 4, 8, 16 | Q4_K_M, Q5_K_M, Q8_0 |
| Neoverse N1 | 64 | 8, 16, 32, 64 | Q4_K_M, Q5_K_M |
| Neoverse V2 | 64 | 16, 32, 64, 128 | Q4_K_M, Q5_K_M, Q8_0 |

## Project Structure

```
ArmPilot-AI/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI route handlers
│   │   ├── auth/           # JWT/OAuth authentication
│   │   ├── benchmark/      # Benchmarking engine
│   │   ├── cli/            # Click CLI commands
│   │   ├── core/           # Config, middleware, exceptions
│   │   ├── database/       # SQLAlchemy storage
│   │   ├── inference/      # Model loading and inference
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── monitoring/     # Health, metrics, profiling
│   │   ├── optimization/   # Auto-tuning engine
│   │   ├── recommendation/ # AI recommendation engine
│   │   ├── reports/        # Report generation (MD, HTML, PDF)
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic services
│   │   └── utils/          # Hardware detection, helpers
│   ├── main.py             # FastAPI app entry point
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js dashboard (optional)
├── src/                    # Vite/React dashboard
│   ├── App.tsx             # Main React application
│   └── index.css           # Tailwind CSS entrypoint
├── configs/                # YAML configuration files
├── docker/                 # Docker and Nginx configs
├── examples/               # Python usage examples
├── scripts/                # Shell utility scripts
├── models/                 # GGUF model files (gitignored)
├── data/                   # Runtime data (gitignored)
├── reports/                # Generated reports (gitignored)
└── docs/                   # Documentation
```

## Docker

```bash
# Development
docker compose up

# Production
docker compose -f docker/docker-compose.prod.yml up -d
```

## Examples

See the `examples/` directory for Python usage:

- `examples/chat_completion.py` — Load a model and use the chat API
- `examples/benchmark.py` — Run a benchmark programmatically
- `examples/optimize.py` — Run an optimization sweep
- `examples/deployment.py` — Deployment automation
- `examples/report_generation.py` — Generate performance reports

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Kamal Solanki
