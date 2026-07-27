#!/usr/bin/env bash
# Local quality gate — run before committing

set -e

echo "🧹 Running quality checks..."
echo ""

# Lint
echo "→ Ruff check..."
uv run --no-build ruff check .
echo "✓ Lint passed"
echo ""

# Format
echo "→ Ruff format (check)..."
uv run --no-build ruff format --check .
echo "✓ Format OK"
echo ""

# Types
echo "→ MyPy strict..."
uv run --no-build mypy .
echo "✓ Types OK"
echo ""

# Architecture
echo "→ Import-linter..."
uv run --no-build lint-imports
echo "✓ Architecture OK"
echo ""

# Tests
echo "→ Pytest..."
uv run --no-build pytest
echo "✓ Tests passed"
echo ""

echo "✅ All checks passed! Ready to commit."
