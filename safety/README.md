# Safety Service 🚨

Emergency alert and safety features service for CrewUp.

## Features

- ✅ **Emergency Alerts**: Users can send safety alerts during active events
- ✅ **Real-time Broadcast**: Alerts are instantly sent to all group members via WebSocket
- ✅ **Location Tracking**: Optional GPS coordinates for emergency response
- ✅ **Alert Resolution**: Track when issues are resolved
- ✅ **Access Control**: Only group members can send/view alerts
- ✅ **Event Validation**: Alerts only work during active events (between start and end time)
- ✅ **JWT Authentication**: Keycloak-based authentication with token validation

## Architecture

### Service Communication
```
User → Safety Service → Group Service → WebSocket → All Group Members
```

1. User sends alert via POST `/alerts`
2. Safety Service validates and stores alert
3. Safety Service calls Group Service internal endpoint `/internal/broadcast/{group_id}`
4. Group Service broadcasts to all connected WebSocket clients
5. All group members receive instant notification

### Tech Stack
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Keycloak** - Authentication
- **httpx** - Inter-service HTTP calls
- **pytest** - Testing (68% coverage)
- **requests** - Integration tests with real HTTP calls
- **python-jose** - JWT token validation

```
safety/
├── app/
│   ├── db/                 # Database models and connection
│   │   ├── database.py     # SQLAlchemy setup
│   │   └── models.py       # ORM models (SafetyAlert, User, Event, Group)
│   ├── middleware/         # Request middleware
│   │   └── auth.py         # JWT authentication with Keycloak
│   ├── models/             # Pydantic validation models
│   │   └── __init__.py     # Request/response schemas
│   ├── routers/            # API endpoints
│   │   └── __init__.py     # Safety alert REST API
│   ├── services/           # Business logic
│   │   ├── alert_service.py   # Alert service client
│   │   └── group_client.py    # Group service client
│   ├── utils/              # Utilities
│   │   ├── logging.py      # Structured logging
│   │   └── exceptions.py   # Error handlers
│   └── main.py             # FastAPI app
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── test_api.py         # Unit tests
│   ├── test_alerts.py      # Alert tests
│   └── test_integration_auth.py # Integration tests with real Keycloak
├── app.py                  # Development entry point
├── Dockerfile              # Container definition
├── requirements.txt        # Dependencies
└── run_tests.sh           # Test runner
```

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Keycloak (for authentication)

### Installation

1. Install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.test.example .env.test
# Edit .env.test with your configuration
```

3. Run the service:
```bash
# Development
python app.py

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

### Docker

```bash
docker build -t crewup-safety-service .
docker run -p 8003:8003 crewup-safety-service
```

## Testing

The service has comprehensive unit and integration tests with automatic database cleanup.

### Test Structure

- **Unit Tests** (`test_api.py`, `test_alerts.py`): Test API layer with mocked dependencies (in-memory SQLite)
- **Integration Tests** (`test_integration_auth.py`): Test with real Keycloak authentication and PostgreSQL database

### Running Tests

```bash
# Run unit tests (default)
./run_tests.sh
# or
./run_tests.sh unit

# Run all tests (unit + integration, requires service running)
./run_tests.sh all

# Run only integration tests (requires running service)
./run_tests.sh integration
```

### Unit Tests

Unit tests run in isolation with mocked authentication and an in-memory SQLite database:

```bash
./run_tests.sh unit
```

**Coverage: 68%** (24 tests)

Unit tests do NOT require:
- Running service
- PostgreSQL database
- Real Keycloak server

### Integration Tests

Integration tests validate real-world scenarios with actual Keycloak authentication:

1. Create `.env.test` with test credentials:
```bash
KEYCLOAK_SERVER_URL=https://keycloak.ltu-m7011e-3.se
KEYCLOAK_REALM=crewup
KEYCLOAK_CLIENT_ID=crewup-test
TEST_USER1_EMAIL=user1@example.com
TEST_USER1_PASSWORD=password123
TEST_USER2_EMAIL=user2@example.com
TEST_USER2_PASSWORD=password123
SAFETY_SERVICE_URL=http://localhost:8003
DATABASE_URL=postgresql://crewup:crewup_dev_password@localhost:5432/crewup
```

2. Ensure service is running:
```bash
# Option 1: Docker (recommended)
docker-compose up safety

# Option 2: Local development
# In a separate terminal
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3. Run integration tests:
```bash
./run_tests.sh integration
# or run all tests (unit + integration)
./run_tests.sh all
```

**Note:** When using Docker, the service runs on port **8004** (mapped from container port 8000). Make sure `.env.test` has:
```bash
SAFETY_SERVICE_URL=http://localhost:8004
```

**Features:**
- Real JWT token acquisition from Keycloak
- Actual HTTP requests to running service
- PostgreSQL database validation
- Automatic cleanup of test data after each test

## API Endpoints

### Public Endpoints

#### `POST /alerts`
Create a safety alert.

**Request:**
```json
{
  "group_id": "uuid",
  "latitude": 65.584819,
  "longitude": 22.154984,
  "alert_type": "help",
  "message": "Need assistance"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "group_id": "uuid",
  "latitude": 65.584819,
  "longitude": 22.154984,
  "alert_type": "help",
  "message": "Need assistance",
  "created_at": "2025-11-25T12:00:00Z",
  "resolved_at": null,
  "user_first_name": "John",
  "user_last_name": "Doe"
}
```

#### `GET /alerts`
List safety alerts (filtered by user's group memberships).

**Query Parameters:**
- `group_id` (optional) - Filter by group
- `resolved` (optional) - Filter by resolution status
- `limit` (default: 50, max: 100)
- `offset` (default: 0)

#### `GET /alerts/{alert_id}`
Get specific alert details.

#### `PATCH /alerts/{alert_id}/resolve`
Mark alert as resolved (creator or group admin only).

**Request:**
```json
{
  "resolved": true
}
```

### Health Check

#### `GET /health`
Service health status.

## Business Rules

### Alert Creation
- ✅ User must have a profile in the database
- ✅ User must be a member of the target group
- ✅ Event must be currently in progress (between start and end time)
- ✅ Event must not be cancelled
- ✅ Alert type must be: `help`, `emergency`, or `other`

### Alert Resolution
- ✅ Only alert creator OR group admin can resolve
- ✅ Can be re-opened by setting `resolved: false`

### Alert Visibility
- ✅ Users can only see alerts from groups they are members of
- ✅ List endpoint automatically filters by membership

## Database Schema

Uses existing `safety_alerts` table from main schema:
```sql
CREATE TABLE safety_alerts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    group_id UUID REFERENCES groups(id),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    alert_type VARCHAR(50) DEFAULT 'help',
    message TEXT,
    created_at TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by_user_id UUID REFERENCES users(id)
);
```

## Development

### Setup

1. **Create virtual environment:**
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment:**
```bash
cp .env.test.example .env.test
# Edit .env.test with your settings
```

4. **Run tests:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

5. **Run service:**
```bash
python app.py
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://crewup:crewup_password@localhost:5432/crewup` |
| `KEYCLOAK_SERVER_URL` | Keycloak server URL | `http://localhost:8080` |
| `KEYCLOAK_REALM` | Keycloak realm name | `crewup` |
| `GROUP_SERVICE_URL` | Group service URL for broadcasts | `http://localhost:8002` |
| `EVENT_SERVICE_URL` | Event service URL | `http://localhost:8001` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |
| `DEBUG` | Enable debug logging | `false` |
| `PORT` | Service port | `8000` |

## Testing

### Run All Tests
```bash
./run_tests.sh
```

### Run Specific Test File
```bash
pytest tests/test_alerts.py -v
```

### Coverage Report
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Test Coverage Goals
- **Target:** 96%+ (matching event service)
- **Current:** Check `htmlcov/index.html` after running tests

## Deployment

### Docker Build
```bash
docker build -t crewup-safety:latest .
```

### Docker Run
```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  -e KEYCLOAK_SERVER_URL=http://... \
  -e GROUP_SERVICE_URL=http://... \
  crewup-safety:latest
```

### Kubernetes (via Helm)
Service is deployed as part of the main CrewUp Helm chart:
```yaml
# helm/crewup/values.yaml
safety:
  enabled: true
  replicas: 2
  image:
    repository: ghcr.io/titouanpastor/crewup-safety
    tag: latest
```

## Frontend Integration

### Sending an Alert

```typescript
// When user holds emergency button
const sendAlert = async (groupId: string, location: GeolocationPosition) => {
  const response = await fetch('/api/safety/alerts', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      group_id: groupId,
      latitude: location.coords.latitude,
      longitude: location.coords.longitude,
      alert_type: 'emergency',
      message: 'Emergency assistance needed'
    })
  });
  
  if (!response.ok) throw new Error('Failed to send alert');
  return response.json();
};
```

### Receiving Alerts (WebSocket)

```typescript
// In group chat WebSocket handler
socket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'safety_alert') {
    // Show emergency notification
    showEmergencyAlert({
      userName: data.user_name,
      alertType: data.alert_type,
      message: data.message,
      location: {
        lat: data.latitude,
        lng: data.longitude
      }
    });
  }
};
```

## Inter-Service Communication

### Safety → Group Broadcast Flow

1. **Safety Service** creates alert and calls:
```http
POST http://group-service:8002/internal/broadcast/{group_id}
Content-Type: application/json

{
  "type": "safety_alert",
  "alert_id": "uuid",
  "user_id": "uuid",
  "user_name": "John Doe",
  "alert_type": "emergency",
  "message": "Need help",
  "latitude": 65.5,
  "longitude": 22.1,
  "created_at": "2025-11-25T12:00:00Z"
}
```

2. **Group Service** receives and broadcasts via WebSocket to all connected members

3. **All clients** receive the alert message instantly

## Security Considerations

- ✅ JWT authentication required for all endpoints
- ✅ Group membership validation before creating/viewing alerts
- ✅ Event time validation (prevents spam outside events)
- ✅ Alert creator/admin authorization for resolution
- ✅ Internal broadcast endpoint has no auth (trusted network only)

## Future Enhancements

- 🔲 SMS/Email notifications for emergency alerts
- 🔲 Alert acknowledgment (members confirm they've seen it)
- 🔲 Escalation workflow (auto-notify authorities after X minutes)
- 🔲 Alert history and analytics
- 🔲 Geofencing (validate user is near event location)
- 🔲 Rate limiting (prevent alert spam)

## Troubleshooting

### Alerts not broadcasting
- Check Group Service is running and accessible
- Verify `GROUP_SERVICE_URL` is correct
- Check Group Service logs for internal endpoint errors

### Alerts rejected with "event not in progress"
- Verify event start/end times are correct
- Check server timezone configuration
- Event must be between start_time and end_time

### Permission errors
- Verify user has profile in database
- Check user is member of the target group
- For resolution: verify user is creator or group admin

## License

MIT License - Part of CrewUp project
