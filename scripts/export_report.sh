#!/usr/bin/env bash
# ArmPilot-AI — Export Reports

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

BENCHMARK_ID="${1:-}"
FORMAT="${FORMAT:-markdown}"
OUTPUT="${OUTPUT:-}"

if [ -z "$BENCHMARK_ID" ]; then
    echo "Usage: $0 <benchmark-id>"
    echo
    echo "Environment variables:"
    echo "  FORMAT  — Output format: markdown, html, json, csv (default: markdown)"
    echo "  OUTPUT  — Output file path (default: stdout)"
    echo
    echo "Examples:"
    echo "  $0 bench-a1b2c3d4"
    echo "  FORMAT=html OUTPUT=report.html $0 bench-a1b2c3d4"
    echo "  FORMAT=json OUTPUT=results.json $0 bench-a1b2c3d4"
    exit 1
fi

echo "ArmPilot-AI — Export Report"
echo "  Benchmark ID: $BENCHMARK_ID"
echo "  Format: $FORMAT"
echo

cd "$BACKEND_DIR"

OUTPUT_FLAG=""
if [ -n "$OUTPUT" ]; then
    OUTPUT_FLAG="--output $OUTPUT"
fi

python3 -m app.cli.main report export "$BENCHMARK_ID" \
    --format "$FORMAT" \
    $OUTPUT_FLAG
