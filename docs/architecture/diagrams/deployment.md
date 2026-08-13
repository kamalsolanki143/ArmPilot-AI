# Deployment Diagram

Shows how ArmPilot-AI is deployed across infrastructure.

```mermaid
C4Deployment
    title Deployment Diagram - ArmPilot-AI

    Deployment_Node(dev, "Development") {
        Container(dev_app, "ArmPilot-AI", "Docker Compose", "Full stack development environment")
    }

    Deployment_Node(arm_server, "ARM64 Server", "Neoverse N1/V2") {
        Deployment_Node(docker, "Docker") {
            Container(api_server, "API Server", "FastAPI + Uvicorn", "Backend API")
            Container(nginx, "Nginx", "Reverse Proxy", "Static files and API routing")
            Container(worker, "Worker", "Background Tasks", "Benchmark and optimization jobs")
        }
        Deployment_Node(data, "Data") {
            ContainerDb(sqlite, "SQLite", "Database", "Benchmarks, optimizations, configs")
            Container filesystem, "Filesystem", "Model Storage", "GGUF model files")
        }
    }

    Deployment_Node(edge, "Edge Device", "Cortex-A76") {
        Container(edge_app, "ArmPilot-AI", "Docker", "Lightweight inference node")
    }

    Deployment_Node(cloud, "Cloud", "GitHub Actions") {
        Container(ci, "CI/CD", "GitHub Actions", "Automated testing and deployment")
    }

    Rel(dev_app, api_server, "Develops against", "HTTP")
    Rel(nginx, api_server, "Proxies requests", "HTTP")
    Rel(api_server, sqlite, "Reads/Writes", "SQLAlchemy")
    Rel(api_server, filesystem, "Loads models", "File I/O")
    Rel(worker, sqlite, "Reads/Writes", "SQLAlchemy")
    Rel(edge_app, api_server, "Syncs data", "HTTPS")
    Rel(ci, api_server, "Deploys", "SSH/Docker")
```

## Deployment Options

### Development

```bash
docker compose up
```

- Single container with all services
- Hot reload for development
- SQLite database

### Production (ARM64 Server)

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

- Separate API, worker, and Nginx containers
- Persistent volumes for models and data
- Health checks and auto-restart

### Edge Deployment

- Lightweight Docker image
- Optimized for Cortex-A76
- Reduced thread count and batch size

## Infrastructure Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores ARM64 | 8+ cores Neoverse |
| RAM | 8 GB | 16+ GB |
| Storage | 20 GB | 100+ GB (for models) |
| Network | 100 Mbps | 1 Gbps |

## Ports

| Service | Port | Protocol |
|---------|------|----------|
| Nginx | 80/443 | HTTP/HTTPS |
| API Server | 8000 | HTTP |
| Dashboard | 3000 | HTTP (dev) |
