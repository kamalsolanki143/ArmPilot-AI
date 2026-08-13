#!/usr/bin/env bash
# ArmPilot-AI — Run All Tests

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "ArmPilot-AI — Running All Tests"
echo

cd "$BACKEND_DIR"

# Run pytest with verbose output
if command -v python3 &>/dev/null; then
    echo "Running pytest..."
    python3 -m pytest tests/ \
        -v \
        --tb=short \
        --cov=app \
        --cov-report=term-missing \
        -x \
        "$@"
    PYTEST_EXIT=$?
else
    echo "Error: python3 not found." >&2
    exit 1
fi

# Run linting if available
echo
if command -v ruff &>/dev/null; then
    echo "Running ruff linter..."
    ruff check app/ tests/
    LINT_EXIT=$?
elif command -v flake8 &>/dev/null; then
    echo "Running flake8 linter..."
    flake8 app/ tests/
    LINT_EXIT=$?
else
    echo "No linter found (ruff/flake8). Skipping."
    LINT_EXIT=0
fi

# Run type checking if available
echo
if command -v mypy &>/dev/null; then
    echo "Running mypy type checker..."
    mypy app/ --ignore-missing-imports
    TYPE_EXIT=$?
elif command -v pyright &>/dev/null; then
    echo "Running pyright type checker..."
    pyright app/
    TYPE_EXIT=$?
else
    echo "No type checker found (mypy/pyright). Skipping."
    TYPE_EXIT=0
fi

# Summary
echo
echo "================================"
echo "Test Results:"
echo "  Pytest:   $([ "$PYTEST_EXIT" -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "  Linting:  $([ "$LINT_EXIT" -eq 0 ] && echo 'PASS' || echo 'FAIL')"
echo "  Typing:   $([ "$TYPE_EXIT" -eq 0 ] && echo 'PASS' || echo 'FAIL')"

OVERALL_EXIT=$((PYTEST_EXIT + LINT_EXIT + TYPE_EXIT))
if [ "$OVERALL_EXIT" -gt 0 ]; then
    echo
    echo "Some checks failed."
    exit 1
fi

echo
echo "All checks passed!"
