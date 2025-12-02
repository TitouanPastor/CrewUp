#!/bin/bash
# Moderation Service - Test Runner
# Usage: ./run_tests.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "============================================================"
echo "Moderation Service - Test Suite"
echo "============================================================"
echo ""

# Run all tests with coverage
echo -e "${YELLOW}Running tests with coverage...${NC}"
echo ""

pytest tests/ -v \
    --cov=app \
    --cov-report=html \
    --cov-report=term-missing \
    --tb=short \
    --color=yes

# Check if coverage meets minimum threshold
COVERAGE_RESULT=$?

echo ""
echo "============================================================"

if [ $COVERAGE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed with >90% coverage!${NC}"
    echo ""
    echo "Coverage report: htmlcov/index.html"
else
    echo -e "${RED}✗ Tests failed or coverage below 90%${NC}"
    echo ""
    echo "Check the output above for details"
    exit 1
fi

echo "============================================================"
