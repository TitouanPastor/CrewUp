# CrewUp

A microservice-based event discovery and safety platform for students.

**Course**: Design of Dynamic Web Systems (M7011E) - LTU  
**Team**: Titouan Pastor, Damien Lanusse

## Live Deployment

| Environment | URL |
|-------------|-----|
| Production | https://crewup.ltu-m7011e-3.se |
| Staging | https://crewup-staging.ltu-m7011e-3.se |
| Dev | https://crewup-dev.ltu-m7011e-3.se |

## Features

- **Event Discovery**: Create and find local events with map integration
- **Group Formation**: Form groups for events with real-time chat
- **Safety Alerts**: "Party Mode" emergency alert system with GPS
- **Reputation System**: Rate attendees after events
- **Moderation**: Ban/unban system for platform safety

## Architecture

```
┌─────────────┐     ┌─────────────────────────────────────────┐
│   Browser   │────▶│          Kubernetes Cluster             │
└─────────────┘     │  ┌─────────────────────────────────┐   │
                    │  │         Traefik Ingress          │   │
                    │  └──────────────┬──────────────────┘   │
                    │                 │                       │
                    │  ┌──────────────┼──────────────────┐   │
                    │  │   React      │   FastAPI APIs   │   │
                    │  │   Frontend   │                  │   │
                    │  │              ├── Event Service  │   │
                    │  │              ├── Group Service  │   │
                    │  │              ├── User Service   │   │
                    │  │              ├── Safety Service │   │
                    │  │              └── Moderation     │   │
                    │  └──────────────┬──────────────────┘   │
                    │                 │                       │
                    │  ┌──────────────┴──────────────────┐   │
                    │  │  PostgreSQL    │    RabbitMQ    │   │
                    │  └─────────────────────────────────┘   │
                    └─────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | FastAPI (Python 3.11), SQLAlchemy |
| Database | PostgreSQL 15 |
| Messaging | RabbitMQ |
| Auth | Keycloak (OAuth 2.0 / JWT) |
| Deployment | Kubernetes, Helm, ArgoCD |
| Monitoring | Prometheus, Grafana |
| CI/CD | GitHub Actions |

## Documentation

| Document | Description |
|----------|-------------|
| [Report/](Report/) | Full system documentation |
| [Report/architecture.md](Report/architecture.md) | Architecture diagrams |
| [Report/SECURITY.md](Report/SECURITY.md) | Security measures |
| [Report/GDPR.md](Report/GDPR.md) | Privacy compliance |
| [Report/ETHICS.md](Report/ETHICS.md) | Ethical analysis |
| [load-testing/](load-testing/) | Performance testing & results |

## Local Development

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM

### Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Services

| Service | Port | URL |
|---------|------|-----|
| Frontend | 3000 | http://localhost:3000 |
| Event API | 8001 | http://localhost:8001/docs |
| Group API | 8002 | http://localhost:8002/docs |
| User API | 8005 | http://localhost:8005/docs |
| Safety API | 8004 | http://localhost:8004/docs |
| Moderation API | 8006 | http://localhost:8006/docs |
| RabbitMQ UI | 15672 | http://localhost:15672 |

### Running Tests

```bash
# Run tests for a specific service
cd event && ./run_tests.sh

# Or with coverage
pytest tests/ --cov=app --cov-report=html
```

## Test Coverage

| Service | Coverage |
|---------|----------|
| Event | 95% |
| User | 94% |
| Moderation | 92% |
| Safety | 90% |
| Group | 83% |

## Project Structure

```
CrewUp/
├── frontend/          # React SPA
├── event/             # Event microservice
├── group/             # Group & Chat microservice
├── user/              # User microservice
├── safety/            # Safety alerts microservice
├── moderation/        # Moderation microservice
├── helm/              # Kubernetes Helm charts
│   ├── crewup/        # Main application
│   └── monitoring/    # Prometheus + Grafana
├── environments/      # Dev/Staging/Prod configs
├── load-testing/      # k6 performance tests
├── Report/            # Documentation
└── .github/workflows/ # CI/CD pipelines
```

## Requirements Compliance

This project fulfills all 27 course requirements. See [Report/](Report/) for detailed documentation on:
- Dynamic web system characteristics
- Microservices architecture
- Cloud-native deployment
- API design & communication
- Security & GDPR compliance
- Performance analysis
