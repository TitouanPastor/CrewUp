# CrewUp System Report

Comprehensive documentation for the CrewUp system.

## Contents

| Document | Description |
|----------|-------------|
| [motivation.md](motivation.md) | Dynamic web system characteristics |
| [architecture.md](architecture.md) | System architecture, CI/CD, monitoring |
| [database-schema.md](database-schema.md) | Database design and relationships |
| [SECURITY.md](SECURITY.md) | Authentication, SQL/XSS protection, TLS |
| [GDPR.md](GDPR.md) | Data privacy compliance analysis |
| [ETHICS.md](ETHICS.md) | Ethical considerations for sensitive data |

## System Overview

CrewUp is a microservice-based event discovery and safety platform:

- **5 Backend Services**: Event, Group, User, Safety, Moderation (FastAPI/Python)
- **Frontend**: React SPA with real-time features
- **Database**: PostgreSQL with complex relational schema
- **Messaging**: RabbitMQ for async communication
- **Auth**: Keycloak (OAuth 2.0 / OIDC)
- **Deployment**: Kubernetes + Helm + ArgoCD (GitOps)
- **Monitoring**: Prometheus + Grafana

## Test Coverage

| Service | Coverage |
|---------|----------|
| Event | 95% |
| User | 94% |
| Moderation | 92% |
| Safety | 90% |
| Group | 83% |
