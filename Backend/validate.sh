#!/usr/bin/env bash
# Local quality gate — run before committing

set -e

echo "🧹 Running quality checks..."
echo ""

# Lint
echo "→ Ruff check..."
uv run ruff check .
echo "✓ Lint passed"
echo ""

# Format
echo "→ Ruff format (check)..."
uv run ruff format --check .
echo "✓ Format OK"
echo ""

# Types
echo "→ MyPy strict..."
uv run mypy .
echo "✓ Types OK"
echo ""

# Architecture
echo "→ Import-linter..."
uv run lint-imports
echo "✓ Architecture OK"
echo ""

# Tests
echo "→ Pytest..."
uv run pytest
echo "✓ Tests passed"
echo ""

echo "✅ All checks passed! Ready to commit."
