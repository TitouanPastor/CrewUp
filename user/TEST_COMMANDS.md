# Manual Testing Guide for User Service with curl

## Prerequisites
Server running locally:
```bash
cd /home/titouan/CrewUp/user
source venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

## 1. Get Keycloak Token

```bash
# Replace USERNAME and PASSWORD with your credentials
# Add -k flag to skip SSL verification for self-signed certs
TOKEN=$(curl -k -s -X POST https://keycloak.ltu-m7011e-3.se/realms/crewup/protocol/openid-connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password' \
  -d 'client_id=crewup-frontend' \
  -d 'username=YOUR_USERNAME' \
  -d 'password=YOUR_PASSWORD' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Verify token was retrieved
echo $TOKEN
```

## 2. Test Health Endpoint (no auth required)

```bash
curl http://localhost:8001/health 2>/dev/null | python3 -m json.tool
```

**Expected result:**
```json
{
    "status": "healthy"
}
```

## 3. Test POST /api/v1/users - Create User Profile

```bash
curl -X POST http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  2>/dev/null | python3 -m json.tool
```

**Expected result (first time):** HTTP 201
```json
{
    "id": "uuid-here",
    "keycloak_id": "your-keycloak-id",
    "email": "your-email@example.com",
    "first_name": "Your_FirstName",
    "last_name": "Your_LastName",
    "bio": null,
    "profile_picture_url": null,
    "interests": [],
    "reputation": 0.0,
    "is_active": true,
    "created_at": "2025-11-13T...",
    "updated_at": "2025-11-13T..."
}
```

**Expected result (second time - idempotent):** HTTP 200
Same JSON, but status 200 instead of 201.

## 4. Test POST /api/v1/users (second time - idempotence)

```bash
# Run the same command again
curl -X POST http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -v 2>&1 | grep -E "(< HTTP|{)"
```

**Expected result:** HTTP 200 (not 201)

## 5. Test GET /api/v1/users/me - Get Current User Profile

```bash
curl http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  2>/dev/null | python3 -m json.tool
```

**Expected result:** HTTP 200
```json
{
    "id": "uuid-here",
    "keycloak_id": "your-keycloak-id",
    "email": "your-email@example.com",
    "first_name": "Your_FirstName",
    "last_name": "Your_LastName",
    "bio": null,
    "profile_picture_url": null,
    "interests": [],
    "reputation": 0.0,
    "is_active": true,
    "created_at": "2025-11-13T...",
    "updated_at": "2025-11-13T..."
}
```

## 6. Test PUT /api/v1/users/me - Update User Profile

```bash
curl -X PUT http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "I am a developer passionate about travel and code!",
    "interests": ["coding", "hiking", "photography", "music"]
  }' \
  2>/dev/null | python3 -m json.tool
```

**Expected result:** HTTP 200
```json
{
    "id": "uuid-here",
    "keycloak_id": "your-keycloak-id",
    "email": "your-email@example.com",
    "first_name": "Your_FirstName",
    "last_name": "Your_LastName",
    "bio": "I am a developer passionate about travel and code!",
    "profile_picture_url": null,
    "interests": ["coding", "hiking", "photography", "music"],
    "reputation": 0.0,
    "is_active": true,
    "created_at": "2025-11-13T...",
    "updated_at": "2025-11-13T..."
}
```

## 7. Test PUT /api/v1/users/me - Validation Error (bio too long)

```bash
curl -X PUT http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"bio\": \"$(python3 -c 'print("x"*501)')\"}" \
  -v 2>&1 | grep -E "(< HTTP|detail)"
```

**Expected result:** HTTP 422 (Validation Error)

## 8. Test GET /api/v1/users/{id} - Public Profile

```bash
# First, get your user ID
USER_ID=$(curl -s http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Then, get the public profile
curl http://localhost:8001/api/v1/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  2>/dev/null | python3 -m json.tool
```

**Expected result:** HTTP 200
```json
{
    "id": "uuid-here",
    "first_name": "Your_FirstName",
    "last_name": "Your_LastName",
    "bio": "I am a developer passionate...",
    "profile_picture_url": null,
    "interests": ["coding", "hiking", "photography", "music"],
    "reputation": 0.0,
    "created_at": "2025-11-13T..."
}
```

**Important note:** Public profile does NOT include:
- `email`
- `keycloak_id`
- `is_active`
- `updated_at`

## 9. Test GET /api/v1/users/{id} - Non-existent User

```bash
curl http://localhost:8001/api/v1/users/00000000-0000-0000-0000-000000000000 \
  -H "Authorization: Bearer $TOKEN" \
  -v 2>&1 | grep -E "(< HTTP|detail)"
```

**Expected result:** HTTP 404

## 10. Test Without Authorization Header

```bash
curl http://localhost:8001/api/v1/users/me \
  -v 2>&1 | grep "< HTTP"
```

**Expected result:** HTTP 403 (Forbidden)

## 11. Verify Database

```bash
# Connect to PostgreSQL (if using local instance)
python3 << 'EOF'
import psycopg2
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="crewup",
    user="crewup",
    password="crewup_dev_password"
)
cursor = conn.cursor()
cursor.execute("SELECT id, email, first_name, last_name, bio, array_length(interests, 1) as nb_interests, reputation, created_at FROM users")
for row in cursor.fetchall():
    print(row)
cursor.close()
conn.close()
EOF
```

## 12. View Server Logs

JSON logs appear in the terminal where uvicorn is running.

## Interactive API Documentation

Visit: http://localhost:8001/docs

You'll see the complete OpenAPI documentation with the ability to test each endpoint directly from the browser!

## HTTP Status Codes Summary

| Endpoint | Method | Auth | Success | Errors |
|----------|---------|------|---------|--------|
| `/health` | GET | ❌ | 200 | 503 (DB down) |
| `/` | GET | ❌ | 200 | - |
| `/api/v1/users` | POST | ✅ | 201, 200 | 400, 401, 409, 500, 503 |
| `/api/v1/users/me` | GET | ✅ | 200 | 401, 404 |
| `/api/v1/users/me` | PUT | ✅ | 200 | 401, 404, 422 |
| `/api/v1/users/{id}` | GET | ✅ | 200 | 401, 404 |

## Complete Test Script

```bash
#!/bin/bash
# test_user_service.sh

# 1. Get token
echo "🔐 Getting Keycloak token..."
read -p "Username: " USERNAME
read -sp "Password: " PASSWORD
echo

TOKEN=$(curl -k -s -X POST https://keycloak.ltu-m7011e-3.se/realms/crewup/protocol/openid-connect/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=password' \
  -d 'client_id=crewup-frontend' \
  -d "username=$USERNAME" \
  -d "password=$PASSWORD" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

if [ -z "$TOKEN" ]; then
    echo "❌ Error: Unable to get token"
    exit 1
fi

echo "✅ Token retrieved"
echo

# 2. Health check
echo "🏥 Test Health Check..."
curl -s http://localhost:8001/health | python3 -m json.tool
echo

# 3. Create profile
echo "👤 Test POST /api/v1/users (create)..."
curl -s -X POST http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo

# 4. Idempotence
echo "🔄 Test POST /api/v1/users (idempotence)..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer $TOKEN")
echo "HTTP Status: $HTTP_CODE (expected: 200)"
echo

# 5. Get profile
echo "📖 Test GET /api/v1/users/me..."
curl -s http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo

# 6. Update profile
echo "✏️ Test PUT /api/v1/users/me..."
curl -s -X PUT http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Test bio from script",
    "interests": ["testing", "automation"]
  }' | python3 -m json.tool
echo

# 7. Get public profile
echo "🌍 Test GET /api/v1/users/{id} (public profile)..."
USER_ID=$(curl -s http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
curl -s http://localhost:8001/api/v1/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo

echo "✅ Tests completed!"
```

**To run the script:**
```bash
chmod +x test_user_service.sh
./test_user_service.sh
```
