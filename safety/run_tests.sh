#!/bin/bash
# Safety Service - Test Runner
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
echo "Safety Service - Test Suite"
echo "============================================================"
echo ""

# Function to run unit tests
run_unit_tests() {
    echo -e "${YELLOW}Running unit tests (no external services required)...${NC}"
    
    # Override DATABASE_URL if not set (for GitHub Actions)
    export DATABASE_URL="${DATABASE_URL:-postgresql://crewup:crewup_dev_password@localhost:5432/crewup}"
    export TESTING="true"
    
    pytest tests/test_api.py tests/test_alerts.py tests/test_edge_cases.py -v \
        --cov=app \
        --cov-report=html \
        --cov-report=term-missing:skip-covered \
        --tb=short \
        --color=yes 2>/dev/null || \
    pytest tests/ -v --ignore=tests/test_integration_auth.py \
        --cov=app \
        --cov-report=html \
        --cov-report=term-missing:skip-covered \
        --tb=short \
        --color=yes
    echo ""
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${YELLOW}[1/3] Checking service health...${NC}"
    if ! curl -s http://localhost:8004/api/v1/safety/health > /dev/null; then
        echo -e "${RED}✗ Service is not running on localhost:8004${NC}"
        echo "Start it with: docker-compose up safety"
        exit 1
    fi
    echo -e "${GREEN}✓ Service is running${NC}"
    echo ""

    echo -e "${YELLOW}[2/3] Checking configuration...${NC}"
    if [ ! -f .env.test ]; then
        echo -e "${RED}✗ .env.test not found${NC}"
        echo "Create it with required environment variables"
        exit 1
    fi
    echo -e "${GREEN}✓ Configuration found${NC}"
    echo ""

    echo -e "${YELLOW}[3/3] Running integration tests...${NC}"
    pytest tests/test_integration_auth.py \
        -v \
        --tb=short \
        --color=yes
    echo ""
}

# Main execution
case "$TEST_TYPE" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    all)
        if [ "$CI" = "true" ]; then
            echo -e "${YELLOW}CI detected: running unit tests only${NC}"
            run_unit_tests
        else
            # Check if integration tests are possible
            if [ -f .env.test ] && curl -s http://localhost:8004/health > /dev/null 2>&1; then
                echo -e "${YELLOW}Running full test suite (unit + integration)...${NC}"
                echo ""
                export $(grep -v '^#' .env.test | xargs)
                rm -f .coverage
                
                pytest tests/ -v \
                    --cov=app \
                    --cov-report=html \
                    --cov-report=term-missing:skip-covered \
                    --tb=short \
                    --color=yes
            else
                echo -e "${YELLOW}Integration tests not available${NC}"
                echo -e "${YELLOW}Running unit tests only${NC}"
                echo ""
                run_unit_tests
            fi
        fi
        ;;
    *)
        echo -e "${RED}Invalid option: $TEST_TYPE${NC}"
        echo "Usage: ./run_tests.sh [unit|integration|all]"
        exit 1
        ;;
esac

# Summary
echo "============================================================"
if [ "$TEST_TYPE" = "integration" ] || ([ "$TEST_TYPE" = "all" ] && [ "$CI" != "true" ] && [ -f .env.test ]); then
    echo -e "${GREEN}✓ Tests completed!${NC}"
    echo ""
    echo "Coverage report: htmlcov/index.html"
else
    echo -e "${GREEN}✓ Unit tests completed!${NC}"
    if [ "$TEST_TYPE" = "all" ] && [ "$CI" != "true" ]; then
        echo ""
        echo -e "${YELLOW}Tip: To run integration tests:${NC}"
        echo "1. Start the service: docker-compose up safety"
        echo "2. Create .env.test with DATABASE_URL"
        echo "3. Run: ./run_tests.sh integration"
    fi
fi
echo "============================================================"

