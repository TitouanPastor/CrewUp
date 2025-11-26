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
TEST_TYPE="${1:-unit}"

echo "============================================================"
echo "Safety Service - Test Suite"
echo "============================================================"
echo ""

# Function to run unit tests
run_unit_tests() {
    echo -e "${YELLOW}Running unit tests (no DB required)...${NC}"
    pytest tests/test_api.py tests/test_alerts.py -v \
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
        # Run combined test suite so coverage is computed across unit+integration
        echo -e "${YELLOW}[0/3] Preparing combined coverage run...${NC}"
        # Ensure .env.test and service are available for integration parts
        if [ ! -f .env.test ]; then
            echo -e "${RED}✗ .env.test not found${NC}"
            echo "Create it with required environment variables"
            exit 1
        fi
        if ! curl -s http://localhost:8004/health > /dev/null; then
            echo -e "${RED}✗ Service is not running on localhost:8004${NC}"
            echo "Start it with: docker-compose up safety"
            exit 1
        fi
        echo -e "${GREEN}✓ Preconditions OK${NC}"
        echo ""

        echo -e "${YELLOW}Running full test suite (unit + integration) with combined coverage...${NC}"
        # Remove old coverage data to ensure a clean report
        rm -f .coverage
        pytest tests/ -v \
            --cov=app \
            --cov-report=html \
            --cov-report=term-missing:skip-covered \
            --tb=short \
            --color=yes
        ;;
    *)
        echo -e "${RED}Invalid option: $TEST_TYPE${NC}"
        echo "Usage: ./run_tests.sh [unit|integration|all]"
        exit 1
        ;;
esac

# Summary
echo "============================================================"
if [ "$TEST_TYPE" = "integration" ] || [ "$TEST_TYPE" = "all" ]; then
    echo -e "${GREEN}✓ Tests completed!${NC}"
    echo ""
    echo "Coverage report: htmlcov/index.html"
    echo "View with: open htmlcov/index.html (Mac) or xdg-open htmlcov/index.html (Linux)"
else
    echo -e "${GREEN}✓ Unit tests completed!${NC}"
fi
echo "============================================================"
