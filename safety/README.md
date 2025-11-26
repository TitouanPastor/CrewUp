# Safety Service 🚨

Emergency alert service for CrewUp events. Enables users to send safety alerts to their group during active events.

## Features

- ✅ Emergency alerts with GPS location
- ✅ Real-time WebSocket broadcast to group members
- ✅ JWT authentication (Keycloak)
- ✅ Alert resolution tracking
- ✅ Event-based validation (alerts only during active events)

## Quick Start

### Development

```bash
# Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run service
python app.py
# Service runs on http://localhost:8004
```

### Docker

```bash
docker-compose up -d safety
# Service runs on http://localhost:8004
```

### Testing

```bash
# Run all tests
./run_tests.sh all

# Unit tests only (fast, no dependencies)
./run_tests.sh unit

# Integration tests (requires running service + Keycloak)
./run_tests.sh integration
```

**Coverage: 82%** (47 tests passing)

## API Endpoints

### Public
- `GET /health` - Service health check

### Authenticated (requires JWT)
- `POST /api/v1/safety` - Create alert
- `GET /api/v1/safety` - List alerts (with filters)
- `GET /api/v1/safety/{id}` - Get specific alert
- `PATCH /api/v1/safety/{id}/resolve` - Mark alert as resolved/unresolved

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

# Service
PORT=8004  # Default: 8004
DEBUG=false
```

## Architecture

```
User → Safety Service → Validates → Stores in DB
                     ↓
              Broadcasts to Group Service
                     ↓
              WebSocket → All Group Members
```

**Key Components:**
- `app/routers/` - REST API endpoints
- `app/middleware/` - JWT authentication
- `app/db/` - Database models & connection
- `app/models/` - Request/response schemas
- `app/utils/` - Logging & error handling

## Alert Flow

1. **Create Alert**: User sends POST with location + message
2. **Validation**: 
   - Check user is group member
   - Verify event is active (started, not ended, not cancelled)
3. **Storage**: Save to PostgreSQL
4. **Broadcast**: Notify all group members via WebSocket
5. **Resolution**: Alert creator or responder marks as resolved

## Testing

### Unit Tests (24 tests)
- Mock authentication & database (SQLite in-memory)
- Fast, no external dependencies
- `tests/test_api.py`, `tests/test_alerts.py`

### Integration Tests (7 tests)
- Real Keycloak authentication
- PostgreSQL database
- Running service required
- `tests/test_integration_auth.py`

### Edge Case Tests (16 tests)
- Event validation (not started, ended, cancelled)
- Alert types and resolution
- Exception handling
- `tests/test_edge_cases.py`

## Production Deployment

Service is deployed via Helm chart in `helm/crewup/`:
- Kubernetes deployment with health checks
- Ingress route: `/api/v1/safety`
- ConfigMap for environment variables
- Secrets for sensitive data

## Development

```bash
# Format code
black app/ tests/

# Lint
flake8 app/ tests/

# Type check
mypy app/

# Run with auto-reload
uvicorn app.main:app --reload --port 8004
```

## Dependencies

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **psycopg2-binary** - PostgreSQL driver
- **python-jose** - JWT handling
- **httpx** - Async HTTP client (for group service)
- **pytest** - Testing framework

## License

MIT
