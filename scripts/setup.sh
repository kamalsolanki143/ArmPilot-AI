#!/usr/bin/env bash
# ArmPilot-AI — Full Project Setup
# Installs dependencies, sets up environment, and verifies installation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "ArmPilot-AI — Full Project Setup"
echo "================================"
echo "Project root: $PROJECT_ROOT"
echo

# ── Check prerequisites ──────────────────────────────────────────────
echo "Checking prerequisites..."

if ! command -v python3 &>/dev/null; then
    echo "Error: python3 not found. Install Python 3.10+." >&2
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python: $PYTHON_VERSION"

if ! command -v pip3 &>/dev/null; then
    echo "Error: pip3 not found." >&2
    exit 1
fi

echo "  pip: available"

if command -v node &>/dev/null; then
    echo "  Node.js: $(node --version)"
else
    echo "  Node.js: not found (frontend skipped)"
fi

# ── Install Python dependencies ──────────────────────────────────────
echo
echo "Installing Python dependencies..."
cd "$PROJECT_ROOT/backend"

if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
elif [ -f pyproject.toml ]; then
    pip3 install -e ".[dev]"
else
    echo "Warning: No requirements.txt or pyproject.toml found in backend/"
fi

echo "  Python dependencies installed."

# ── Setup environment file ───────────────────────────────────────────
echo
if [ ! -f "$PROJECT_ROOT/.env" ] && [ -f "$PROJECT_ROOT/.env.example" ]; then
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    echo "Created .env from .env.example"
elif [ -f "$PROJECT_ROOT/.env" ]; then
    echo ".env already exists, skipping."
fi

# ── Create directories ───────────────────────────────────────────────
echo
echo "Ensuring directories exist..."
mkdir -p "$PROJECT_ROOT/models"
mkdir -p "$PROJECT_ROOT/data"
mkdir -p "$PROJECT_ROOT/reports"
mkdir -p "$PROJECT_ROOT/logs"
echo "  models/, data/, reports/, logs/"

# ── Install frontend dependencies ────────────────────────────────────
if [ -d "$PROJECT_ROOT/frontend" ] && command -v pnpm &>/dev/null; then
    echo
    echo "Installing frontend dependencies..."
    cd "$PROJECT_ROOT/frontend"
    pnpm install
    echo "  Frontend dependencies installed."
fi

# ── Verify installation ──────────────────────────────────────────────
echo
echo "Verifying installation..."
cd "$PROJECT_ROOT/backend"
python3 -c "import fastapi; print(f'  FastAPI: {fastapi.__version__}')" 2>/dev/null || echo "  FastAPI: not installed"
python3 -c "import uvicorn; print(f'  Uvicorn: {uvicorn.__version__}')" 2>/dev/null || echo "  Uvicorn: not installed"
python3 -c "import pydantic; print(f'  Pydantic: {pydantic.__version__}')" 2>/dev/null || echo "  Pydantic: not installed"
python3 -c "import click; print(f'  Click: {click.__version__}')" 2>/dev/null || echo "  Click: not installed"

echo
echo "Setup complete!"
echo
echo "Next steps:"
echo "  1. Place .gguf model files in the models/ directory"
echo "  2. Run: bash scripts/run_server.sh"
echo "  3. Visit: http://localhost:8000/docs"
