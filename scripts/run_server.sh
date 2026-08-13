#!/usr/bin/env bash
# ArmPilot-AI — Start the API Server

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

HOST="${ARMPILOT_HOST:-0.0.0.0}"
PORT="${ARMPILOT_PORT:-8000}"
LOG_LEVEL="${ARMPILOT_LOG_LEVEL:-info}"
RELOAD="${RELOAD:-false}"

echo "ArmPilot-AI — Starting Server"
echo "  Host: $HOST"
echo "  Port: $PORT"
echo "  Log level: $LOG_LEVEL"
echo "  Reload: $RELOAD"
echo

cd "$BACKEND_DIR"

if [ "$RELOAD" = "true" ] || [ "$RELOAD" = "1" ]; then
    exec python3 -m uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level "$LOG_LEVEL"
else
    exec python3 -m uvicorn main:app \
        --host "$HOST" \
        --port "$PORT" \
        --log-level "$LOG_LEVEL"
fi
