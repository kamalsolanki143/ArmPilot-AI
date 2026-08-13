#!/usr/bin/env bash
# ArmPilot-AI — Run Benchmarks

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

MODEL="${1:-llama-3.2-1b-instruct}"
THREADS="${THREADS:-4}"
BATCH_SIZE="${BATCH_SIZE:-512}"
NUM_REQUESTS="${NUM_REQUESTS:-10}"
MAX_TOKENS="${MAX_TOKENS:-128}"
CONCURRENCY="${CONCURRENCY:-1}"
OUTPUT="${OUTPUT:-}"

echo "ArmPilot-AI — Benchmark"
echo "  Model: $MODEL"
echo "  Threads: $THREADS"
echo "  Batch size: $BATCH_SIZE"
echo "  Requests: $NUM_REQUESTS"
echo "  Concurrency: $CONCURRENCY"
echo "  Max tokens: $MAX_TOKENS"
echo

cd "$BACKEND_DIR"

OUTPUT_FLAG=""
if [ -n "$OUTPUT" ]; then
    OUTPUT_FLAG="--output $OUTPUT"
fi

python3 -m app.cli.main benchmark run \
    --model "$MODEL" \
    --threads "$THREADS" \
    --batch-size "$BATCH_SIZE" \
    --num-requests "$NUM_REQUESTS" \
    --max-tokens "$MAX_TOKENS" \
    --concurrency "$CONCURRENCY" \
    $OUTPUT_FLAG
