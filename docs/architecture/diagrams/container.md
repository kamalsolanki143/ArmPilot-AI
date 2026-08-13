# Container Diagram

Shows the high-level technical building blocks and their interactions.

```mermaid
C4Container
    title Container Diagram - ArmPilot-AI

    Person(user, "User", "Developer, Researcher, or Operator")

    Container_Boundary(armpilot, "ArmPilot-AI Platform") {
        Container(frontend, "Web Dashboard", "React 19, Vite 8, Tailwind CSS", "Real-time visualization of inference, benchmarks, and optimization results")
        Container(backend, "API Server", "FastAPI, Python 3.10+", "OpenAI-compatible inference API, benchmark orchestration, optimization engine")
        Container(cli, "CLI Tool", "Click, Python", "Command-line interface for all platform operations")
        Container(db, "Database", "SQLite, SQLAlchemy", "Persistent storage for benchmarks, optimizations, and configurations")
    }

    Container_Boundary(runtimes, "Inference Runtimes") {
        Container(llama_cpp, "llama.cpp", "C++ with Python bindings", "GGUF model inference with NEON/SVE2 SIMD")
        Container(mlx, "MLX", "Apple ML framework", "macOS ARM64 Metal-accelerated inference")
        Container(onnx, "ONNX Runtime", "Microsoft framework", "Cross-platform quantized model inference")
    }

    System_Ext(hardware, "ARM64 Hardware", "Neoverse, Cortex-A76, Apple Silicon")
    System_Ext(models, "GGUF Models", "TinyLlama, Phi-2, Mistral, Llama-3")

    Rel(user, frontend, "Uses", "HTTPS")
    Rel(user, cli, "Commands", "Terminal")
    Rel(frontend, backend, "API calls", "HTTP/WebSocket")
    Rel(cli, backend, "API calls", "HTTP")
    Rel(backend, db, "Reads/Writes", "SQLAlchemy")
    Rel(backend, llama_cpp, "Loads models", "Python bindings")
    Rel(backend, mlx, "Loads models", "Python bindings")
    Rel(backend, onnx, "Loads models", "Python bindings")
    Rel(llama_cpp, hardware, "Executes", "NEON/SVE2")
    Rel(mlx, hardware, "Executes", "Metal")
    Rel(onnx, hardware, "Executes", "CPU/GPU")
    Rel(backend, models, "Downloads", "HTTPS")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Containers

| Container | Technology | Purpose |
|-----------|------------|---------|
| Web Dashboard | React 19, Vite 8, Tailwind CSS | Real-time visualization |
| API Server | FastAPI, Python 3.10+ | Core business logic |
| CLI Tool | Click, Python | Command-line interface |
| Database | SQLite, SQLAlchemy | Persistent storage |

## Inference Runtimes

| Runtime | Platform | Model Format | Acceleration |
|---------|----------|--------------|--------------|
| llama.cpp | All (ARM64 native) | GGUF | NEON/SVE2 SIMD |
| MLX | macOS ARM64 | GGUF, Safetensors | Metal GPU |
| ONNX Runtime | Cross-platform | ONNX | CPU/GPU |

## Data Flow

1. **User → Frontend/CLI** — HTTP/CLI requests
2. **Frontend/CLI → Backend** — API calls
3. **Backend → Database** — Persistence
4. **Backend → Runtimes** — Model loading and inference
5. **Runtimes → Hardware** — Optimized execution
