#!/bin/bash
# User Service - Test Runner
# Usage: ./run_tests.sh [unit|integration|all]

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to all tests
TEST_TYPE="${1:-all}"

# Detect if running in CI
if [ "$CI" = "true" ]; then
    echo -e "${YELLOW}Running in CI environment - unit tests only${NC}"
    TEST_TYPE="unit"
fi

echo "============================================================"
echo "User Service - Test Suite"
echo "============================================================"
echo ""

# Function to run unit tests
run_unit_tests() {
    echo -e "${YELLOW}Running unit tests...${NC}"
    
    # Override DATABASE_URL if not set (for GitHub Actions)
    export DATABASE_URL="${DATABASE_URL:-postgresql://crewup:crewup_dev_password@localhost:5432/crewup}"
    export TEST_DATABASE_URL="${TEST_DATABASE_URL:-$DATABASE_URL}"
    export TESTING="true"
    
    pytest tests/ -v \
        --cov=app \
        --cov-report=html \
        --cov-report=term-missing:skip-covered \
        --tb=short \
        --color=yes
    echo ""
}

# Main execution
case "$TEST_TYPE" in
    unit|integration|all)
        run_unit_tests
        ;;
    *)
        echo -e "${RED}Invalid option: $TEST_TYPE${NC}"
        echo "Usage: ./run_tests.sh [unit|integration|all]"
        exit 1
        ;;
esac

# Summary
echo "============================================================"
echo -e "${GREEN}✓ Tests completed!${NC}"
echo ""
echo "Coverage report: htmlcov/index.html"
echo "============================================================"
