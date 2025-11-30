#!/bin/bash
# Event Service - Test Runner
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
echo "Event Service - Test Suite"
echo "============================================================"
echo ""

# Function to run unit tests
run_unit_tests() {
    echo -e "${YELLOW}Running unit tests (no external services required)...${NC}"
    
    # Override DATABASE_URL if not set (for GitHub Actions)
    export DATABASE_URL="${DATABASE_URL:-postgresql://crewup:crewup_dev_password@localhost:5432/crewup}"
    export TESTING="true"
    
    pytest tests/test_api.py tests/test_routes_comprehensive.py \
        tests/test_auth.py tests/test_events_coverage.py \
        tests/test_exceptions.py -v \
        --cov=app \
        --cov-report=html \
        --cov-report=term-missing:skip-covered \
        --tb=short \
        --color=yes
    echo ""
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${YELLOW}[1/4] Checking service health...${NC}"
    if ! curl -s http://localhost:8001/api/v1/events/health > /dev/null; then
        echo -e "${RED}✗ Service is not running on localhost:8001${NC}"
        echo "Start it with: uvicorn app.main:app --host 0.0.0.0 --port 8001"
        exit 1
    fi
    echo -e "${GREEN}✓ Service is running${NC}"
    echo ""

    echo -e "${YELLOW}[2/4] Checking configuration...${NC}"
    if [ ! -f .env.test ]; then
        echo -e "${RED}✗ .env.test not found${NC}"
        echo "Create it from .env.test.example with real Keycloak credentials"
        exit 1
    fi
    echo -e "${GREEN}✓ Found .env.test${NC}"
    echo ""

    echo -e "${YELLOW}[3/4] Checking database connection...${NC}"
    # Load DATABASE_URL from .env.test
    export $(grep -v '^#' .env.test | xargs)
    
    if ! command -v psql &> /dev/null; then
        echo -e "${YELLOW}⚠ psql not found, skipping DB check${NC}"
    else
        # Extract connection details from DATABASE_URL
        DB_URL="${DATABASE_URL:-postgresql://crewup:crewup_dev_password@localhost:5432/crewup}"
        if psql "$DB_URL" -c "SELECT 1" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Database connection OK${NC}"
        else
            echo -e "${RED}✗ Cannot connect to database${NC}"
            echo "Check DATABASE_URL in .env.test"
            exit 1
        fi
    fi
    echo ""

    echo -e "${YELLOW}[4/4] Running integration tests with coverage...${NC}"
    pytest tests/test_integration.py -v \
        --cov=app \
        --cov-report=html \
        --cov-report=term-missing:skip-covered \
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
        # Check if running in CI
        if [ "$CI" = "true" ]; then
            echo -e "${YELLOW}CI detected: running unit tests only${NC}"
            run_unit_tests
        else
            # Check if integration tests are possible
            if [ -f .env.test ] && curl -s http://localhost:8001/api/v1/events/health > /dev/null 2>&1; then
                echo -e "${YELLOW}Running full test suite (unit + integration)...${NC}"
                echo ""
                
                # Load env vars
                export $(grep -v '^#' .env.test | xargs)
                
                # Remove old coverage data
                rm -f .coverage
                
                # Run all tests together for combined coverage
                pytest tests/ -v \
                    --cov=app \
                    --cov-report=html \
                    --cov-report=term-missing:skip-covered \
                    --tb=short \
                    --color=yes
            else
                echo -e "${YELLOW}Integration tests not available (service not running or .env.test missing)${NC}"
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
    echo "View with: open htmlcov/index.html (Mac) or xdg-open htmlcov/index.html (Linux)"
else
    echo -e "${GREEN}✓ Unit tests completed!${NC}"
    if [ "$TEST_TYPE" = "all" ] && [ "$CI" != "true" ]; then
        echo ""
        echo -e "${YELLOW}Tip: To run integration tests:${NC}"
        echo "1. Start the service: uvicorn app.main:app --port 8001"
        echo "2. Create .env.test from .env.test.example"
        echo "3. Run: ./run_tests.sh integration"
    fi
fi
echo "============================================================"
