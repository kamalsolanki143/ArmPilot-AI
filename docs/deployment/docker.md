# Docker Deployment

Deploy ArmPilot-AI using Docker and Docker Compose.

## Prerequisites

- Docker 24+
- Docker Compose v2+
- At least 8 GB RAM (for model inference)

## Quick Start

```bash
# Build and start
docker compose up

# Detached mode
docker compose up -d

# View logs
docker compose logs -f backend
```

## Docker Compose Configuration

### Development (`docker-compose.yml`)

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models
      - ./data:/app/data
      - ./reports:/app/reports
    environment:
      - ARMPILOT_HOST=0.0.0.0
      - ARMPILOT_PORT=8000
      - ARMPILOT_DEBUG=true

  frontend:
    build:
      context: frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### Production (`docker-compose.prod.yml`)

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - armpilot-models:/app/models
      - armpilot-data:/app/data
    environment:
      - ARMPILOT_DEBUG=false
      - ARMPILOT_LOG_LEVEL=WARNING
      - ARMPILOT_JWT_SECRET_KEY=${ARMPILOT_JWT_SECRET_KEY}
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 16G
        reservations:
          memory: 4G

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  armpilot-models:
  armpilot-data:
```

## Dockerfile

### Backend

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for llama.cpp
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install
COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
```

## Model Storage

### Option 1: Bind Mount (Development)

```bash
# Models directory is mounted into the container
docker compose up
```

### Option 2: Named Volume (Production)

```bash
# Copy models into the volume
docker compose -f docker-compose.prod.yml up -d
docker compose cp models/ backend:/app/models/
```

### Option 3: S3/Cloud Storage

```bash
# Download models at startup
# Add to your entrypoint script:
aws s3 cp s3://my-bucket/models/ /app/models/
```

## Nginx Configuration

The included `docker/nginx.conf` provides:

- Reverse proxy for API requests
- Static file serving for frontend
- Gzip compression
- Security headers
- Rate limiting

## Commands

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Remove volumes
docker compose down -v

# Scale backend (production)
docker compose -f docker-compose.prod.yml up -d --scale backend=3
```

## Resource Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Backend | 2 GB RAM, 2 vCPU | 8 GB RAM, 4 vCPU |
| Model (3B) | 2 GB RAM | 4 GB RAM |
| Model (7B) | 4 GB RAM | 8 GB RAM |
| Frontend | 256 MB RAM | 512 MB RAM |

## Troubleshooting

### Container exits immediately

```bash
docker compose logs backend
# Check for missing model files or dependency errors
```

### Out of memory

Increase Docker memory limit or use a smaller model (e.g., TinyLlama 1.1B instead of Mistral 7B).

### Port conflicts

Change ports in `docker-compose.yml`:

```yaml
ports:
  - "8001:8000"  # Use port 8001 instead
```
