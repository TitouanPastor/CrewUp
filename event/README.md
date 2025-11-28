# CrewUp Event Service

Event management microservice for the CrewUp application. Handles event creation, RSVP, search, and participant management.

## Features

- **Event CRUD**: Create, read, update, and delete events.
- **RSVP System**: Join/leave events with status (going, interested, not_going)
- **Event Search**: Text-based and location-based event search
- **Event Listing**: Filter events by type, date, creator, and more
- **Participant Management**: Track and retrieve event participants
- **Authentication**: JWT-based authentication with Keycloak

## Architecture

```
event/
├── app/
│   ├── db/                 # Database models and connection
│   │   ├── database.py     # SQLAlchemy setup
│   │   └── models.py       # ORM models (Event, EventAttendee)
│   ├── middleware/         # Request middleware
│   │   └── auth.py         # JWT authentication
│   ├── models/             # Pydantic validation models
│   │   └── event.py        # Request/response schemas
│   ├── routers/            # API endpoints
│   │   └── events.py       # Event REST API
│   ├── utils/              # Utilities
│   │   ├── logging.py      # Structured logging
│   │   └── exceptions.py   # Error handlers
│   └── main.py             # FastAPI app
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── test_api.py         # Unit tests
│   └── test_integration.py # Integration tests
├── app.py                  # Development entry point
├── config.py               # Configuration
├── Dockerfile              # Container definition
├── requirements.txt        # Dependencies
└── run_tests.sh           # Test runner
```

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Keycloak (for authentication)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the service:
```bash
# Development
python app.py

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Docker

```bash
docker build -t crewup-event-service .
docker run -p 8001:8001 crewup-event-service
```

## API Endpoints

### Health Check
- `GET /api/v1/events/health` - Service health check

### Event CRUD
- `POST /api/v1/events` - Create event
- `GET /api/v1/events/{id}` - Get event details
- `PUT /api/v1/events/{id}` - Update event
- `DELETE /api/v1/events/{id}` - Delete event

### RSVP
- `POST /api/v1/events/{id}/join` - Join event (RSVP)
- `DELETE /api/v1/events/{id}/leave` - Leave event

### Listing & Search
- `GET /api/v1/events` - List events with filters
- `GET /api/v1/events/search` - Search events

### Participants
- `GET /api/v1/events/{id}/participants` - Get participant counts and list

## Testing

Run tests with the test runner script:

```bash
# Run unit tests only (no DB required)
./run_tests.sh unit

# Run integration tests (requires running service + DB + Keycloak)
./run_tests.sh integration

# Run all tests
./run_tests.sh all
```

Or run pytest directly:

```bash
# Unit tests
pytest tests/test_api.py -v

# Integration tests
pytest tests/test_integration.py -v

# All tests with coverage
pytest tests/ -v --cov=app --cov-report=html
```

### Integration Test Setup

1. Create `.env.test` with test credentials:
```bash
KEYCLOAK_SERVER_URL=https://keycloak.ltu-m7011e-3.se
KEYCLOAK_REALM=crewup
KEYCLOAK_CLIENT_ID=crewup-test
TEST_USER1_EMAIL=user1@example.com
TEST_USER1_PASSWORD=password123
TEST_USER2_EMAIL=user2@example.com
TEST_USER2_PASSWORD=password123
EVENT_SERVICE_URL=http://localhost:8001
```

2. Ensure service is running:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

3. Run integration tests:
```bash
./run_tests.sh integration
```

## Configuration

Configuration is managed through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection URL | (constructed from individual vars) |
| `POSTGRES_HOST` | Database host | `localhost` |
| `POSTGRES_PORT` | Database port | `5432` |
| `POSTGRES_USER` | Database user | `crewup` |
| `POSTGRES_PASSWORD` | Database password | `crewup_dev_password` |
| `POSTGRES_DB` | Database name | `crewup` |
| `KEYCLOAK_SERVER_URL` | Keycloak server URL | `https://keycloak.ltu-m7011e-3.se` |
| `KEYCLOAK_REALM` | Keycloak realm | `crewup` |
| `KEYCLOAK_CLIENT_ID` | Keycloak client ID | `crewup-client` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEBUG` | Debug mode | `false` |

## API Documentation

Once running, view the interactive API documentation:

- Swagger UI: http://localhost:8001/api/v1/events/docs
- ReDoc: http://localhost:8001/api/v1/events/redoc
- OpenAPI JSON: http://localhost:8001/api/v1/events/openapi.json

## Development

### Code Style

Follow PEP 8 guidelines. Key conventions:
- Use type hints
- Document all public functions with docstrings
- Keep functions focused and testable
- Use Pydantic models for validation

### Adding New Endpoints

1. Define Pydantic models in `app/models/event.py`
2. Add ORM models in `app/db/models.py` if needed
3. Implement endpoint in `app/routers/events.py`
4. Add unit tests in `tests/test_api.py`
5. Add integration tests in `tests/test_integration.py`

## License

MIT License - See LICENSE file for details
