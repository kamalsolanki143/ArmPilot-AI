#!/usr/bin/env bash
# ArmPilot-AI — Clean Build Artifacts, Caches, and Temporary Files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

DRY_RUN="${DRY_RUN:-false}"

echo "ArmPilot-AI — Clean"
if [ "$DRY_RUN" = "true" ]; then
    echo "(dry run — no files will be deleted)"
fi
echo

# ── Python caches ────────────────────────────────────────────────────
echo "Python caches:"
find "$PROJECT_ROOT" -type d -name "__pycache__" | while read -r dir; do
    if [ "$DRY_RUN" = "true" ]; then
        echo "  [dry-run] Would remove: $dir"
    else
        rm -rf "$dir"
        echo "  Removed: $dir"
    fi
done

find "$PROJECT_ROOT" -type d -name ".pytest_cache" | while read -r dir; do
    if [ "$DRY_RUN" = "true" ]; then
        echo "  [dry-run] Would remove: $dir"
    else
        rm -rf "$dir"
        echo "  Removed: $dir"
    fi
done

find "$PROJECT_ROOT" -type d -name ".mypy_cache" | while read -r dir; do
    if [ "$DRY_RUN" = "true" ]; then
        echo "  [dry-run] Would remove: $dir"
    else
        rm -rf "$dir"
        echo "  Removed: $dir"
    fi
done

# ── Build artifacts ──────────────────────────────────────────────────
echo
echo "Build artifacts:"
for pattern in "*.egg-info" "dist" "build" ".eggs"; do
    find "$PROJECT_ROOT" -maxdepth 3 -name "$pattern" -type d | while read -r dir; do
        if [ "$DRY_RUN" = "true" ]; then
            echo "  [dry-run] Would remove: $dir"
        else
            rm -rf "$dir"
            echo "  Removed: $dir"
        fi
    done
done

# ── Coverage reports ─────────────────────────────────────────────────
echo
echo "Coverage reports:"
for f in "$PROJECT_ROOT/backend/htmlcov" "$PROJECT_ROOT/backend/.coverage"; do
    if [ -e "$f" ]; then
        if [ "$DRY_RUN" = "true" ]; then
            echo "  [dry-run] Would remove: $f"
        else
            rm -rf "$f"
            echo "  Removed: $f"
        fi
    fi
done

# ── Temp files ───────────────────────────────────────────────────────
echo
echo "Temp files:"
find "$PROJECT_ROOT" -maxdepth 3 \( -name "*.tmp" -o -name "*.bak" -o -name "*~" -o -name "*.swp" \) -type f | while read -r f; do
    if [ "$DRY_RUN" = "true" ]; then
        echo "  [dry-run] Would remove: $f"
    else
        rm -f "$f"
        echo "  Removed: $f"
    fi
done

# ── Log files (optional) ────────────────────────────────────────────
echo
echo "Log files:"
if [ -d "$PROJECT_ROOT/logs" ]; then
    find "$PROJECT_ROOT/logs" -name "*.log*" -type f | while read -r f; do
        if [ "$DRY_RUN" = "true" ]; then
            echo "  [dry-run] Would remove: $f"
        else
            rm -f "$f"
            echo "  Removed: $f"
        fi
    done
fi

echo
echo "Clean complete."
