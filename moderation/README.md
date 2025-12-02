# Moderation Service ⚖️

Content moderation and user management service for CrewUp. Enables moderators to ban/unban users and enforce platform guidelines.

## Features

- ✅ User ban/unban functionality.
- ✅ Role-based access control (Moderator role required)
- ✅ JWT authentication (Keycloak)
- ✅ RabbitMQ event publishing for ban actions
- ✅ Comprehensive moderation action logging
- ✅ Edge case handling (self-ban prevention, duplicate ban checks)

## Quick Start

### Development

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run service
python -m app.main
# Service runs on http://localhost:8006
```

### Docker

```bash
docker-compose up -d moderation
# Service runs on http://localhost:8000
```

### Testing

```bash
# Run all tests with coverage
./run_tests.sh

# Tests require 90% minimum coverage
```

**Coverage: >90%** (50+ tests passing)

## API Endpoints

### Public
- `GET /` - Service information
- `GET /api/v1/moderation/health` - Service health check

### Authenticated (requires Moderator role)
- `POST /api/v1/moderation/moderation/ban` - Ban or unban a user

## Ban Endpoint

### Request
```json
POST /api/v1/moderation/moderation/ban
Authorization: Bearer <jwt_token>

{
  "user_keycloak_id": "uuid-of-user-to-ban",
  "ban": true,  // true to ban, false to unban
  "reason": "Violated community guidelines repeatedly"
}
```

### Response
```json
{
  "success": true,
  "message": "User user@example.com has been banned successfully.",
  "moderation_action_id": 123
}
```

### Validation Rules
- Reason must be 10-255 characters
- Moderators cannot ban themselves
- Cannot ban already banned users (or unban non-banned users)
- Returns 503 if RabbitMQ is unavailable (with retry message)

## Configuration

Set via environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db
# Or individual vars:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=crewup
POSTGRES_PASSWORD=password
POSTGRES_DB=crewup

# Keycloak
KEYCLOAK_SERVER_URL=https://keycloak.example.com
KEYCLOAK_REALM=crewup
KEYCLOAK_CLIENT_ID=crewup-backend
KEYCLOAK_CLIENT_SECRET=your-secret

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

# Service
DEBUG=false
LOG_LEVEL=INFO
```

## Architecture

```
Moderator → Moderation Service → Validates → RabbitMQ
                                ↓
                          Logs Action to DB
                                ↓
                        User Service (consumer)
                                ↓
                        Updates is_banned flag
```

**Key Components:**
- `app/routers/` - REST API endpoints (ban/unban)
- `app/middleware/` - JWT authentication + role checking
- `app/services/` - RabbitMQ publisher
- `app/db/` - Database models & connection
- `app/models/` - Request/response schemas
- `app/utils/` - Logging & error handling

## Ban Workflow

1. **Authentication**: Verify JWT token and Moderator role
2. **Validation**:
   - Check moderator exists in database
   - Prevent self-banning
   - Check target user exists
   - Verify user doesn't already have requested ban status
3. **Publish Event**: Send ban/unban message to RabbitMQ
4. **Log Action**: Store moderation action in database
5. **Response**: Return success with action ID

### Edge Cases Handled

- **Self-ban prevention**: Moderators cannot ban themselves (400 Bad Request)
- **Duplicate ban check**: Cannot ban already banned users (400 Bad Request)
- **RabbitMQ unavailable**: Returns 503 with "try again later" message
- **Partial failure**: If RabbitMQ succeeds but DB logging fails, still returns success
- **Reason validation**: 10-255 characters enforced

## Testing

### Unit Tests (40+ tests)
- Authentication middleware (`tests/test_auth.py`)
- RabbitMQ publisher (`tests/test_rabbitmq.py`)
- Ban endpoint logic (`tests/test_ban_endpoint.py`)
- Mock all external dependencies

### Integration Tests (10+ tests)
- Full ban/unban workflow (`tests/test_integration.py`)
- Database transaction handling
- Authentication flow
- Model validation

### Test Coverage
All tests use SQLite in-memory database for speed. No external services required.

```bash
# View coverage report
./run_tests.sh
open htmlcov/index.html
```

## RabbitMQ Message Format

### Ban Event
```json
{
  "user_keycloak_id": "uuid-of-banned-user",
  "moderator_keycloak_id": "uuid-of-moderator",
  "reason": "Community guidelines violation",
  "action": "ban_user",
  "ban": true
}
```

### Unban Event
```json
{
  "user_keycloak_id": "uuid-of-unbanned-user",
  "moderator_keycloak_id": "uuid-of-moderator",
  "reason": "Ban appeal approved",
  "action": "unban_user",
  "ban": false
}
```

**Exchange**: `user.ban` (direct)
**Queue**: `user.ban.queue`
**Routing Key**: `user.ban`

## Database Schema

### moderation_actions
```sql
CREATE TABLE moderation_actions (
    id SERIAL PRIMARY KEY,
    moderator_id VARCHAR NOT NULL,      -- Keycloak user ID
    action_type VARCHAR NOT NULL,        -- 'ban_user' | 'unban_user'
    target_type VARCHAR NOT NULL,        -- 'user'
    target_id VARCHAR NOT NULL,          -- Keycloak user ID
    reason TEXT NOT NULL,
    details TEXT,                        -- Additional context
    created_at TIMESTAMP DEFAULT NOW()
);
```

### users (read-only)
```sql
-- Managed by user service
-- Moderation service reads to verify user existence
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    keycloak_id VARCHAR UNIQUE NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    is_banned BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Production Deployment

Service is deployed via Helm chart in `helm/crewup/`:
- Kubernetes deployment with health checks
- Ingress route: `/api/moderation`
- ConfigMap for environment variables
- Secrets for Keycloak and RabbitMQ credentials

## Development

```bash
# Format code
black app/ tests/

# Lint
flake8 app/ tests/

# Type check
mypy app/

# Run with auto-reload
uvicorn app.main:app --reload --port 8000
```

## Dependencies

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **psycopg2-binary** - PostgreSQL driver
- **python-jose** - JWT handling
- **pika** - RabbitMQ client
- **requests** - HTTP client
- **pytest** - Testing framework

## Security Considerations

1. **Authentication**: All endpoints require valid JWT from Keycloak
2. **Authorization**: Only users with "Moderator" role can access ban endpoints
3. **Audit Trail**: All moderation actions are logged with moderator ID, reason, and timestamp
4. **Message Persistence**: RabbitMQ messages are persistent (delivery_mode=2)
5. **Self-Protection**: Moderators cannot ban themselves

## Error Responses

### 400 Bad Request
- Self-ban attempt
- User already has requested ban status
- Validation errors (reason too short/long)

### 401 Unauthorized
- Missing or invalid JWT token

### 403 Forbidden
- User lacks Moderator role

### 404 Not Found
- Moderator or target user not found in database

### 422 Unprocessable Entity
- Invalid request payload
- Missing required fields

### 503 Service Unavailable
- RabbitMQ connection failed (retry later)

## License

MIT
