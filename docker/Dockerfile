# ══════════════════════════════════════════════════════════════════════════════
# ArmPilot-AI — Multi-Stage Production Dockerfile
# ══════════════════════════════════════════════════════════════════════════════

# ── Stage 1: Build frontend ─────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

COPY package.json pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile

COPY vite.config.ts tsconfig.json index.html ./
COPY src/ ./src/
RUN pnpm build

# ── Stage 2: Python dependencies ────────────────────────────────────────────
FROM python:3.12-slim AS python-builder

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 3: Production image ───────────────────────────────────────────────
FROM python:3.12-slim AS production

LABEL org.opencontainers.image.title="ArmPilot-AI"
LABEL org.opencontainers.image.description="Arm64-first LLM inference optimization and benchmarking platform"
LABEL org.opencontainers.image.version="1.0.0"

# Install system dependencies for llama-cpp-python / ARM inference
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r armuser && useradd -r -g armuser -d /app -s /sbin/nologin armuser

# Copy Python packages from builder
COPY --from=python-builder /install /usr/local

WORKDIR /app

# Copy backend
COPY backend/ ./backend/
COPY scripts/ ./scripts/

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist/ ./static/frontend/

# Create runtime directories
RUN mkdir -p models data reports logs && \
    chown -R armuser:armuser /app

USER armuser

# Environment defaults
ENV ARMPILOT_HOST=0.0.0.0 \
    ARMPILOT_PORT=8000 \
    ARMPILOT_DEBUG=false \
    ARMPILOT_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1

WORKDIR /app/backend

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
