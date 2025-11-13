# User Service

User profile management service with Keycloak authentication.

## Features

- ✅ User profile creation from Keycloak JWT tokens
- ✅ Profile management (bio, interests)
- ✅ Public profile viewing
- ✅ JWT authentication middleware
- ✅ Production-ready error handling
- ✅ Structured JSON logging
- ✅ OpenAPI documentation
- ✅ Unit tests (pytest)

## Architecture

```
app/
├── models/          # Pydantic validation models
├── routers/         # API endpoints
├── db/              # SQLAlchemy ORM
├── middleware/      # JWT authentication
├── utils/           # Logging, error handlers
└── main.py          # FastAPI app
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/users` | Create user profile | ✅ |
| GET | `/api/v1/users/me` | Get current user | ✅ |
| PUT | `/api/v1/users/me` | Update profile | ✅ |
| GET | `/api/v1/users/{id}` | Get public profile | ✅ |
| GET | `/health` | Health check | ❌ |

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL running (via Docker Compose)

### Setup

```bash
# Install dependencies
cd user/
pip install -r requirements.txt

# Set environment variables (optional, has defaults)
export DATABASE_URL="postgresql://crewup:crewup_dev_password@localhost:5432/crewup"
export KEYCLOAK_SERVER_URL="https://keycloak.ltu-m7011e-3.se"

# Run server
uvicorn app.main:app --reload --port 8001
```

### Run Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing tests/

# Run specific test file
pytest tests/test_users.py -v
```

### API Documentation

Once running, visit:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- OpenAPI JSON: http://localhost:8001/openapi.json

## Testing with curl

```bash
# Get Keycloak token (replace with your credentials)
TOKEN=$(curl -X POST https://keycloak.ltu-m7011e-3.se/realms/crewup/protocol/openid-connect/token \
  -d "client_id=crewup-frontend" \
  -d "username=youruser" \
  -d "password=yourpass" \
  -d "grant_type=password" | jq -r .access_token)

# Create user profile
curl -X POST http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer $TOKEN"

# Get current user
curl http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Update profile
curl -X PUT http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bio": "Test bio", "interests": ["music", "coding"]}'

# Get public profile (replace UUID)
curl http://localhost:8001/api/v1/users/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $TOKEN"
```

## Configuration

Environment variables (see `config.py`):

- `DATABASE_URL` - PostgreSQL connection string
- `POSTGRES_HOST` - Database host (default: localhost)
- `POSTGRES_USER` - Database user (default: crewup)
- `POSTGRES_PASSWORD` - Database password
- `POSTGRES_DB` - Database name (default: crewup)
- `KEYCLOAK_SERVER_URL` - Keycloak server URL
- `KEYCLOAK_REALM` - Keycloak realm (default: crewup)
- `KEYCLOAK_CLIENT_ID` - Client ID for JWT validation
- `LOG_LEVEL` - Logging level (default: INFO)
- `DEBUG` - Debug mode (default: false)

## Production Deployment

The service is automatically deployed to Kubernetes when pushed to `main`:

1. GitHub Actions builds Docker image
2. Image pushed to GHCR
3. ArgoCD syncs Helm chart
4. Kubernetes deploys new version

Health checks: http://crewup.ltu-m7011e-3.se/api/users/health

## Database Schema

See `database/schema.sql` for the complete schema. Key fields:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keycloak_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    bio TEXT,
    profile_picture_url TEXT,
    interests TEXT[],
    reputation DECIMAL(3, 2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Error Handling

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": [...]
  }
}
```

HTTP status codes:
- `200` - Success (GET, PUT)
- `201` - Created (POST)
- `400` - Bad Request
- `401` - Unauthorized (invalid token)
- `404` - Not Found
- `409` - Conflict (duplicate user)
- `422` - Validation Error (Pydantic)
- `500` - Internal Server Error
- `503` - Service Unavailable (DB down)
