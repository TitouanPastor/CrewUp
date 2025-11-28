# Group & Chat Service

Production-ready microservice for group management and real-time chat in the CrewUp platform.

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org/)
[![WebSocket](https://img.shields.io/badge/WebSocket-RFC%206455-green.svg)](https://tools.ietf.org/html/rfc6455)

---

## Features

- ✅ **Group CRUD** - Create, read, update groups for events.
- ✅ **Membership** - Join, leave, member lists with admin roles
- ✅ **Real-time Chat** - WebSocket-based messaging with typing indicators
- ✅ **Message History** - Paginated retrieval with filtering
- ✅ **Rate Limiting** - Spam protection (5 msg/min per user)
- ✅ **Authentication** - Keycloak JWT integration
- ✅ **Production Ready** - Kubernetes deployment, health checks, metrics

---

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/crewup"
export KEYCLOAK_SERVER_URL="https://keycloak.example.com"
export KEYCLOAK_REALM="crewup"
export KEYCLOAK_CLIENT_ID="crewup-frontend"

# Run service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

Service available at: `http://localhost:8002`  
API Documentation: `http://localhost:8002/api/v1/groups/docs`

### Docker

```bash
docker build -t group-service:latest .
docker run -p 8002:8002 \
  -e DATABASE_URL="postgresql://..." \
  -e KEYCLOAK_SERVER_URL="https://..." \
  group-service:latest
```

### Kubernetes

```bash
cd ../helm/crewup
helm upgrade --install crewup . -n crewup
kubectl get pods -n crewup -l app=group-service
```

---

## API Endpoints

### Health & Documentation
- `GET /api/v1/groups/health` - Health check (no auth)
- `GET /api/v1/groups/docs` - Swagger UI
- `GET /api/v1/groups/openapi.json` - OpenAPI schema

### Groups
- `POST /api/v1/groups` - Create group
- `GET /api/v1/groups` - List groups (filter by event_id)
- `GET /api/v1/groups/{id}` - Get group details
- `PUT /api/v1/groups/{id}` - Update group (admin only)
- `DELETE /api/v1/groups/{id}` - Delete group (admin only)

### Membership
- `POST /api/v1/groups/{id}/join` - Join group
- `DELETE /api/v1/groups/{id}/leave` - Leave group
- `GET /api/v1/groups/{id}/members` - List members

### Messages
- `GET /api/v1/groups/{id}/messages` - Get message history (paginated)

### WebSocket Chat
```
WS /api/v1/ws/groups/{id}?token={jwt}
```

**Message Format:**
```json
// Send
{"type": "message", "content": "Hello!"}

// Receive
{
  "type": "message",
  "id": "uuid",
  "user_id": "uuid", 
  "username": "user@example.com",
  "content": "Hello!",
  "timestamp": "2025-11-15T12:00:00Z"
}
```

---

## Testing

### Quick Test

```bash
# Run all tests
./run_tests.sh all

# Unit tests only (fast, no DB)
./run_tests.sh unit

# Integration tests only (requires service + DB)
./run_tests.sh integration
```

### Manual Testing with Pytest

```bash
# All tests with coverage
pytest --cov=app --cov-report=html -v

# Specific test file
pytest tests/test_api.py -v

# Specific test
pytest tests/test_integration.py::TestGroupCRUD::test_create_group -v
```

### Test Configuration

Create `.env.test`:
```bash
KEYCLOAK_SERVER_URL=https://keycloak.ltu-m7011e-3.se
KEYCLOAK_REALM=crewup
KEYCLOAK_CLIENT_ID=crewup-frontend
TEST_USER1_EMAIL=test.user.1@test.com
TEST_USER1_PASSWORD=test
TEST_USER2_EMAIL=test.user.2@test.com
TEST_USER2_PASSWORD=test
GROUP_SERVICE_URL=http://localhost:8002
DATABASE_URL=postgresql://crewup:crewup_dev_password@localhost:5432/crewup
```

**Prerequisites:**
1. Service running: `uvicorn app.main:app --port 8002`
2. Database accessible: `docker ps | grep crewup-db`
3. Test users created in Keycloak

**Coverage**: Current ~75% | View report: `htmlcov/index.html`

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `KEYCLOAK_SERVER_URL` | Yes | - | Keycloak base URL |
| `KEYCLOAK_REALM` | Yes | `crewup` | Keycloak realm name |
| `KEYCLOAK_CLIENT_ID` | Yes | `crewup-frontend` | OAuth2 client ID |
| `ENVIRONMENT` | No | `development` | Environment name |
| `LOG_LEVEL` | No | `INFO` | Logging level |
| `RATE_LIMIT_MESSAGES` | No | `5` | Max messages per minute |
| `RATE_LIMIT_WINDOW` | No | `60` | Rate limit window (seconds) |

---

## Database Schema

```sql
CREATE TABLE groups (
    id UUID PRIMARY KEY,
    event_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    max_members INTEGER DEFAULT 10,
    is_private BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE group_members (
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    is_admin BOOLEAN DEFAULT false,
    PRIMARY KEY (group_id, user_id)
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL,
    content TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_groups_event ON groups(event_id);
CREATE INDEX idx_members_user ON group_members(user_id);
CREATE INDEX idx_messages_group_time ON messages(group_id, sent_at DESC);
```

---

## Production Deployment

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: group-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: group-service
        image: group-service:latest
        ports:
        - containerPort: 8002
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: crewup-secrets
              key: database-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/groups/health
            port: 8002
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/v1/groups/health
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Ingress for WebSocket

**Critical**: Add these annotations for WebSocket support:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: crewup-ingress
  annotations:
    nginx.ingress.kubernetes.io/websocket-services: "group-service"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  rules:
  - host: crewup.example.com
    http:
      paths:
      - path: /api/v1/groups
        pathType: Prefix
        backend:
          service:
            name: group-service
            port:
              number: 8002
      - path: /api/v1/ws/groups
        pathType: Prefix
        backend:
          service:
            name: group-service
            port:
              number: 8002
```

### Health Monitoring

```bash
# Health check
curl http://service/api/v1/groups/health

# Logs
kubectl logs -n crewup -l app=group-service --tail=100 -f

# Metrics (if Prometheus enabled)
curl http://service/metrics
```

---

## Architecture

```
┌─────────────────┐
│   Kubernetes    │
│    Ingress      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────┐
│  Group Service  │◄────►│  Keycloak    │
│   (FastAPI)     │      │  (Auth)      │
└────────┬────────┘      └──────────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│   (Database)    │
└─────────────────┘
```

**Request Flow:**
1. Client authenticates with Keycloak → Gets JWT
2. Client sends request with `Authorization: Bearer {token}`
3. Middleware validates JWT, extracts user_id from `sub` claim
4. Router processes request, checks permissions
5. Database executes queries via SQLAlchemy
6. Response returns JSON or WebSocket message

---

## Project Structure

```
group/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Environment configuration
│   ├── db/
│   │   ├── models.py        # SQLAlchemy ORM models
│   │   └── database.py      # Database connection
│   ├── models/
│   │   └── group.py         # Pydantic validation schemas
│   ├── routers/
│   │   ├── groups.py        # REST API endpoints
│   │   └── chat.py          # WebSocket endpoint
│   ├── middleware/
│   │   └── auth.py          # JWT authentication
│   ├── services/
│   │   └── chat_manager.py  # WebSocket connection manager
│   └── utils/
│       ├── logging.py       # Logging configuration
│       └── exceptions.py    # Custom exceptions
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_api.py          # Unit tests (6 tests)
│   └── test_integration.py  # Integration tests (14 tests)
├── Dockerfile
├── requirements.txt
├── run_tests.sh             # Test runner script
└── README.md
```

---

## Troubleshooting

### Service won't start
```bash
# Check database
docker ps | grep crewup-db
psql $DATABASE_URL -c "SELECT 1"

# Check logs
kubectl logs -n crewup -l app=group-service
```

### Tests failing
```bash
# Verify service running
curl http://localhost:8002/api/v1/groups/health

# Check test config
cat .env.test

# Verbose output
pytest -vv -s
```

### WebSocket not connecting
```bash
# Check ingress
kubectl get ingress crewup-ingress -o yaml | grep websocket

# Test locally
wscat -c "ws://localhost:8002/api/v1/ws/groups/{id}?token={jwt}"
```

---

## License

MIT License

---

**Status**: Production Ready ✅  
**Version**: 1.0.0  
**Last Updated**: November 2025
