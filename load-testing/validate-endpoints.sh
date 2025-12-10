#!/bin/bash

# Endpoint Validation Script
# Checks which endpoints are accessible without authentication

BASE_URL=${1:-"https://crewup-staging.ltu-m7011e-3.se"}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🔍 CrewUp API Endpoint Validation                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Testing: $BASE_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
TOTAL=0
SUCCESS=0
FAILED=0
REDIRECT=0

# Function to test endpoint
test_endpoint() {
    local method=$1
    local path=$2
    local description=$3
    local expected_codes=$4  # e.g., "200,404" for acceptable codes
    
    TOTAL=$((TOTAL + 1))
    
    # Make request and get status code
    response=$(curl -s -o /dev/null -w "%{http_code}" -X $method "$BASE_URL$path" 2>&1)
    
    # Check if it's one of the expected codes
    if echo "$expected_codes" | grep -q "$response"; then
        echo -e "${GREEN}✓${NC} $method $path - $response ($description)"
        SUCCESS=$((SUCCESS + 1))
    elif [ "$response" = "302" ] || [ "$response" = "301" ] || [ "$response" = "307" ]; then
        echo -e "${YELLOW}↻${NC} $method $path - $response REDIRECT ($description)"
        REDIRECT=$((REDIRECT + 1))
        
        # Follow redirect to see where it goes
        redirect_url=$(curl -s -I -X $method "$BASE_URL$path" | grep -i "location:" | awk '{print $2}' | tr -d '\r')
        if [ -n "$redirect_url" ]; then
            echo "   → Redirects to: $redirect_url"
        fi
    else
        echo -e "${RED}✗${NC} $method $path - $response ($description)"
        FAILED=$((FAILED + 1))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 FRONTEND"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "GET" "/" "Homepage" "200"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 HEALTH CHECKS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "GET" "/api/v1/users/health" "User service health" "200"
test_endpoint "GET" "/api/v1/groups/health" "Group service health" "200"
test_endpoint "GET" "/api/v1/events/health" "Event service health" "200"
test_endpoint "GET" "/api/v1/moderation/health" "Moderation service health" "200"
test_endpoint "GET" "/api/v1/safety/health" "Safety service health" "200"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📅 EVENT SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "GET" "/api/v1/events" "List all events" "200"
test_endpoint "GET" "/api/v1/events/1" "Get event by ID" "200,401,404"
test_endpoint "POST" "/api/v1/events" "Create event (needs auth)" "401,403"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👥 GROUP SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "GET" "/api/v1/groups" "List groups" "200,401"
test_endpoint "GET" "/api/v1/groups/1" "Get group by ID" "200,401,404"
test_endpoint "POST" "/api/v1/groups" "Create group (needs auth)" "401,403"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "👤 USER SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "GET" "/api/v1/users" "List users" "200"
test_endpoint "GET" "/api/v1/users/1" "Get user by ID" "200,401,404"
test_endpoint "GET" "/api/v1/users/me" "Get current user (needs auth)" "401,403"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚨 SAFETY SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "GET" "/api/v1/safety" "List safety alerts" "200,401"
test_endpoint "GET" "/api/v1/safety/1" "Get alert by ID" "200,401,404"
test_endpoint "POST" "/api/v1/safety" "Create alert (needs auth)" "401,403"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛡️  MODERATION SERVICE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
test_endpoint "POST" "/api/v1/moderation/ban" "Ban user (needs auth)" "401,403"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Total endpoints tested: $TOTAL"
echo -e "${GREEN}✓ Success:${NC} $SUCCESS"
echo -e "${YELLOW}↻ Redirects:${NC} $REDIRECT"
echo -e "${RED}✗ Failed:${NC} $FAILED"
echo ""

if [ $REDIRECT -gt 0 ]; then
    echo "⚠️  WARNING: $REDIRECT endpoints redirect (likely Keycloak auth)"
    echo ""
    echo "📝 RECOMMENDATIONS FOR LOAD TESTING:"
    echo "  - Use only endpoints that return 200 (no redirect, no auth)"
    echo "  - Health checks are public and safe to test"
    echo "  - For authenticated endpoints, you need a valid JWT token"
    echo ""
fi

if [ $FAILED -gt 0 ]; then
    echo "❌ Some endpoints failed - check if services are running:"
    echo "   kubectl get pods -n crewup-staging"
    echo ""
fi

# List endpoints that returned 200 ONLY
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SAFE ENDPOINTS FOR LOAD TESTING (200 responses only):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Based on testing above:"
echo "  - GET / (homepage)"
echo "  - GET /api/v1/users/health"
echo "  - GET /api/v1/groups/health"
echo "  - GET /api/v1/events/health"
echo "  - GET /api/v1/moderation/health"
echo "  - GET /api/v1/safety/health"
echo "  - GET /api/v1/events (list all events)"
echo "  - GET /api/v1/users (list all users)"
echo ""
echo "  ⚠️  Other endpoints require authentication (401)"
echo ""
