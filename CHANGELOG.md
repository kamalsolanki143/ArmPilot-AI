# Changelog

All notable changes to ArmPilot-AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-08-11

### Added

- **Inference Engine**
  - OpenAI-compatible `/v1/chat/completions` endpoint
  - Streaming (SSE) support
  - Multi-runtime support (llama.cpp, MLX, ONNX Runtime)
  - Model auto-discovery from `models/` directory
  - Configurable threads, batch size, context length

- **Benchmarking Suite**
  - Time-to-first-token (TTFT) measurement
  - Latency percentile tracking (P50, P75, P90, P95, P99)
  - Throughput measurement (tokens/sec, requests/sec)
  - CPU utilization and memory profiling
  - Pre-configured scenarios (quick, latency, throughput, memory stress)
  - Async and synchronous benchmark execution

- **Optimization Engine**
  - Auto-tuning for quantization, batch size, thread count
  - Arm hardware profiles (Cortex-A76, Neoverse N1, Neoverse V2)
  - Multiple optimization objectives (throughput, latency, memory, balanced)
  - KV cache optimization
  - CPU affinity pinning
  - NUMA-aware scheduling

- **AI Recommendations**
  - Bottleneck detection (memory bandwidth, CPU saturation)
  - Configuration change suggestions with reasoning
  - Impact estimation (expected improvement percentages)
  - One-click apply from dashboard

- **REST API**
  - Full OpenAI-compatible inference API
  - Benchmark management API
  - Optimization management API
  - Health check and system metrics
  - WebSocket for live updates
  - Structured error responses with error codes

- **CLI**
  - `info` — System and hardware information
  - `models` — List available models
  - `serve` — Start API server
  - `benchmark run` — Run benchmarks
  - `optimize run` — Run optimization sweep
  - `report generate` — Generate performance reports
  - `cleanup` — Remove old data

- **Authentication**
  - JWT-based authentication (register, login, refresh)
  - GitHub OAuth2 integration
  - Password change and logout

- **Reports**
  - Markdown export
  - HTML export
  - PDF export
  - CSV data export
  - Before/after comparison charts

- **Dashboard**
  - Dark and light theme support
  - Real-time metric cards
  - Interactive charts (throughput, latency, CPU)
  - Model selection and inference playground
  - Benchmark configuration and results
  - Optimization parameter tuning
  - Recommendation display with reasoning

- **Deployment**
  - Docker Compose (development and production)
  - Nginx reverse proxy configuration
  - AWS Graviton deployment guide
  - Systemd service configuration

- **Configuration**
  - YAML-based configuration files
  - Environment variable support
  - Per-environment configs (development, production)
  - Logging configuration with rotation

### Changed

- N/A (initial release)

### Fixed

- N/A (initial release)

## [Unreleased]

### Planned

- Model quantization conversion pipeline
- Multi-model inference support
- Benchmark comparison (before/after UI)
- Team collaboration features
- API key management
- Webhook notifications
- Grafana/Prometheus integration
