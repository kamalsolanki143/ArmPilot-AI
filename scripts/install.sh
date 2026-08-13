#!/usr/bin/env bash
# ArmPilot-AI — Install Dependencies

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "ArmPilot-AI — Install Dependencies"
echo "  Project root: $PROJECT_ROOT"
echo

# ── Python dependencies ──────────────────────────────────────────────
echo "Installing Python dependencies..."
cd "$PROJECT_ROOT/backend"

if command -v pip3 &>/dev/null; then
    PIP="pip3"
elif command -v pip &>/dev/null; then
    PIP="pip"
else
    echo "Error: pip not found. Install pip or ensure it's in PATH." >&2
    exit 1
fi

if [ -f requirements.txt ]; then
    $PIP install -r requirements.txt
    echo "  Installed from requirements.txt"
elif [ -f pyproject.toml ]; then
    $PIP install -e ".[dev]"
    echo "  Installed from pyproject.toml"
else
    echo "Warning: No requirements.txt or pyproject.toml found."
    echo "  Installing core dependencies manually..."
    $PIP install \
        fastapi \
        uvicorn[standard] \
        pydantic \
        pydantic-settings \
        psutil \
        click \
        httpx \
        python-dotenv
    echo "  Core dependencies installed."
fi

# ── Verify core imports ──────────────────────────────────────────────
echo
echo "Verifying core imports..."
python3 -c "import fastapi" 2>/dev/null && echo "  fastapi: OK" || echo "  fastapi: MISSING"
python3 -c "import uvicorn" 2>/dev/null && echo "  uvicorn: OK" || echo "  uvicorn: MISSING"
python3 -c "import pydantic" 2>/dev/null && echo "  pydantic: OK" || echo "  pydantic: MISSING"
python3 -c "import psutil" 2>/dev/null && echo "  psutil: OK" || echo "  psutil: MISSING"
python3 -c "import click" 2>/dev/null && echo "  click: OK" || echo "  click: MISSING"

# ── Frontend dependencies (optional) ─────────────────────────────────
if [ -d "$PROJECT_ROOT/frontend" ]; then
    echo
    if command -v pnpm &>/dev/null; then
        echo "Installing frontend dependencies..."
        cd "$PROJECT_ROOT/frontend"
        pnpm install
        echo "  Frontend dependencies installed."
    elif command -v npm &>/dev/null; then
        echo "Installing frontend dependencies (npm)..."
        cd "$PROJECT_ROOT/frontend"
        npm install
        echo "  Frontend dependencies installed."
    else
        echo "Skipping frontend: no pnpm or npm found."
    fi
fi

echo
echo "Installation complete."
