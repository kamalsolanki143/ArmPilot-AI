# ArmPilot-AI Backend - Cloud Run Production Image

FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Application directory
WORKDIR /app

# Install Python dependencies first for Docker layer caching
COPY backend/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend application
COPY backend/ ./backend/

# Create runtime directories
RUN mkdir -p \
    /app/models \
    /app/data \
    /app/reports \
    /app/logs

# Non-root user
RUN groupadd -r armuser && \
    useradd -r -g armuser -d /app -s /usr/sbin/nologin armuser && \
    chown -R armuser:armuser /app

USER armuser

# Runtime configuration
ENV ARMPILOT_HOST=0.0.0.0 \
    ARMPILOT_DEBUG=false \
    ARMPILOT_LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Cloud Run provides PORT
EXPOSE 8080

WORKDIR /app/backend

# Single worker because inference workloads can be memory-heavy
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]