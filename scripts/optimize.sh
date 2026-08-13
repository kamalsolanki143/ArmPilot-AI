#!/usr/bin/env bash
# ArmPilot-AI — Run Optimization Sweep

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

MODEL="${1:-llama-3.2-1b-instruct}"
OBJECTIVE="${OBJECTIVE:-throughput}"
MAX_CANDIDATES="${MAX_CANDIDATES:-8}"
BENCH_PER="${BENCH_PER:-5}"
MAX_TOKENS="${MAX_TOKENS:-128}"
OUTPUT="${OUTPUT:-}"

echo "ArmPilot-AI — Optimization"
echo "  Model: $MODEL"
echo "  Objective: $OBJECTIVE"
echo "  Max candidates: $MAX_CANDIDATES"
echo "  Benchmarks per candidate: $BENCH_PER"
echo

cd "$BACKEND_DIR"

OUTPUT_FLAG=""
if [ -n "$OUTPUT" ]; then
    OUTPUT_FLAG="--output $OUTPUT"
fi

python3 -m app.cli.main optimize run \
    --model "$MODEL" \
    --objective "$OBJECTIVE" \
    --max-candidates "$MAX_CANDIDATES" \
    --benchmarks-per "$BENCH_PER" \
    --max-tokens "$MAX_TOKENS" \
    $OUTPUT_FLAG
