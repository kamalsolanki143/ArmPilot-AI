# Deployment Pipeline

How ArmPilot-AI is deployed across different environments.

## Deployment Options

```
┌─────────────────────────────────────────────────┐
│              Deployment Targets                   │
├─────────────┬──────────────┬────────────────────┤
│    Local    │    Docker    │   AWS Graviton      │
│ Development │  Compose     │   Production        │
└──────┬──────┴──────┬───────┴─────────┬──────────┘
       │             │                 │
       ▼             ▼                 ▼
┌──────────┐  ┌──────────┐    ┌──────────────┐
│  Python  │  │  Docker  │    │  EC2 / ECS   │
│  venv +  │  │  Image + │    │  Graviton +  │
│  uvicorn │  │  Nginx   │    │  ALB + EFS   │
└──────────┘  └──────────┘    └──────────────┘
```

## Local Development

```bash
# Setup
bash scripts/setup.sh

# Run server (auto-reload)
bash scripts/run_server.sh

# Or manually
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Hot Reload

- Backend: Uvicorn `--reload` watches Python files
- Frontend: Vite dev server with HMR on port 8443

## Docker Deployment

### Development

```bash
docker compose up
```

### Production

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

### Image Build

```bash
# Backend image
docker build -t armpilot-backend -f docker/Dockerfile.backend .

# Frontend image
docker build -t armpilot-frontend -f docker/Dockerfile.frontend .

# Full stack
docker compose build
```

### Docker Compose Services

| Service | Port | Description |
|---------|------|-------------|
| `backend` | 8000 | FastAPI application |
| `frontend` | 3000 | Next.js dashboard |
| `nginx` | 80/443 | Reverse proxy + static files |

### Nginx Configuration

- Proxies `/api/*` and `/v1/*` to backend
- Serves frontend static files
- Handles SSL termination (production)
- Gzip compression enabled

## AWS Graviton Deployment

### Architecture

```
┌─────────────────────────────────────────┐
│                 ALB                      │
│         (Application Load Balancer)      │
└─────────────┬───────────────────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
    ▼                   ▼
┌──────────┐      ┌──────────┐
│ EC2      │      │ EC2      │
│ Graviton │      │ Graviton │
│ (c7g)    │      │ (c7g)    │
└────┬─────┘      └────┬─────┘
     │                 │
     └────────┬────────┘
              │
    ┌─────────▼─────────┐
    │   EFS / S3        │
    │  (Model Storage)  │
    └───────────────────┘
```

### Instance Recommendations

| Workload | Instance | vCPU | Memory | Storage |
|----------|----------|------|--------|---------|
| Development | c7g.medium | 2 | 4 GB | 50 GB gp3 |
| Small team | c7g.xlarge | 4 | 8 GB | 100 GB gp3 |
| Production | c7g.2xlarge | 8 | 16 GB | 200 GB gp3 |
| High-throughput | c7g.4xlarge | 16 | 32 GB | 500 GB gp3 |

### Deployment Steps

```bash
# 1. Launch Graviton instance
aws ec2 run-instances \
  --instance-type c7g.2xlarge \
  --image-id ami-0c55b159cbfafe1f0 \
  --architecture arm64

# 2. Install dependencies
sudo apt update && sudo apt install -y python3-pip nodejs npm

# 3. Deploy application
git clone https://github.com/krrishyaduka/ArmPilot-AI.git
cd ArmPilot-AI
bash scripts/setup.sh

# 4. Start as systemd service
sudo cp deploy/armpilot.service /etc/systemd/system/
sudo systemctl enable armpilot
sudo systemctl start armpilot
```

### Model Storage

- **S3** — Store model files in S3, mount via `s3fs` or download on startup
- **EFS** — Shared model storage across multiple EC2 instances
- **Instance Store** — NVMe for highest throughput (c7ggd instances)

## Production Checklist

- [ ] Set `ARMPILOT_JWT_SECRET_KEY` to a strong random value
- [ ] Configure CORS origins for your domain
- [ ] Set `ARMPILOT_DEBUG=false`
- [ ] Set `ARMPILOT_LOG_LEVEL=WARNING`
- [ ] Enable rate limiting (60 req/min default)
- [ ] Configure health check endpoint
- [ ] Set up log rotation
- [ ] Place model files on fast storage (NVMe/EFS)
- [ ] Configure SSL/TLS termination
- [ ] Set up monitoring and alerting

## Environment Comparison

| Setting | Development | Production |
|---------|-------------|------------|
| `debug` | `true` | `false` |
| `log_level` | `DEBUG` | `WARNING` |
| `reload` | `true` | `false` |
| `threads` | 2 | 8 |
| `batch_size` | 256 | 512 |
| `context_length` | 1024 | 2048 |
| `benchmark_requests` | 3 | 50 |
| `max_candidates` | 3 | 8 |
| `rate_limiting` | disabled | 60/min |
