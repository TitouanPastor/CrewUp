#!/bin/bash

# Safety Service Test Runner
# Runs all tests with coverage reporting

set -e

echo "🧪 Running Safety Service Tests..."
echo "================================="

# Load test environment
if [ -f .env.test ]; then
    export $(cat .env.test | grep -v '^#' | xargs)
    echo "✓ Test environment loaded from .env.test"
else
    echo "⚠️  Warning: .env.test not found, using .env.test.example"
    cp .env.test.example .env.test
    export $(cat .env.test | grep -v '^#' | xargs)
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Run tests with coverage
echo ""
echo "Running pytest with coverage..."
pytest tests/ \
    -v \
    --cov=app \
    --cov-report=html \
    --cov-report=term \
    --cov-report=term-missing \
    --asyncio-mode=auto

# Show coverage summary
echo ""
echo "================================="
echo "✅ Tests completed!"
echo ""
echo "📊 Coverage report generated in htmlcov/index.html"
echo ""

# Exit with pytest's exit code
exit $?
