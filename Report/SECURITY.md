# Security Documentation

## Overview

CrewUp implements multiple layers of security to protect user data and ensure system integrity.

## Authentication & Authorization

### Keycloak Integration
- **Protocol**: OpenID Connect (OIDC) with OAuth 2.0
- **Token Type**: JWT with RS256 signature
- **Flow**: Authorization Code + PKCE for frontend
- **Token Validation**: Each microservice independently verifies JWT signatures using Keycloak's JWKS endpoint

### Role-Based Access Control (RBAC)
- **User**: Standard operations (create events, join groups, chat)
- **Moderator**: Ban/unban users, view all user data
- **Admin**: Full system access via Keycloak console

### Ban System
- Moderators can ban users via the Moderation Service
- Ban events propagate asynchronously via RabbitMQ to all services
- Banned users receive `403 Forbidden` on all write operations

## SQL Injection Prevention

### ORM Protection
All database queries use **SQLAlchemy ORM** with parameterized queries:

```python
# Safe - parameterized query
user = db.query(User).filter(User.keycloak_id == keycloak_id).first()
event = db.query(Event).filter(Event.id == event_id).first()
```

No raw SQL queries are used. All user inputs are validated through Pydantic models before reaching the database layer.

### Input Validation
- **Pydantic Models**: All API inputs validated with type checking, length constraints, and regex patterns
- **Field Validators**: Custom validation for business logic (e.g., event dates, coordinates)

## XSS Prevention

### Frontend Protection
- **React**: Automatic escaping of rendered content
- **No `dangerouslySetInnerHTML`**: User content is never rendered as raw HTML
- **Content Security Policy**: Configured via Nginx headers

### Backend Protection
- All user inputs sanitized before storage
- API responses use `application/json` content type
- No server-side HTML rendering with user content

## Transport Security

### TLS/HTTPS
- **Certificate Authority**: Let's Encrypt
- **Certificate Manager**: cert-manager with automatic renewal
- **Renewal**: Certificates auto-renew 30 days before expiration
- **Verification**: `kubectl get certificate -n crewup-production`

### Internal Communication
- Services communicate via Kubernetes internal DNS
- RabbitMQ uses internal cluster networking
- Database accessible only within cluster

## Secrets Management

- Database credentials stored in Kubernetes Secrets
- RabbitMQ credentials stored in Kubernetes Secrets
- No hardcoded secrets in code or configuration files
- Environment variables injected at runtime

## Test Coverage Summary

| Service | Coverage |
|---------|----------|
| Event | 95% |
| User | 94% |
| Moderation | 92% |
| Safety | 90% |
| Group | 83% |

All services include dedicated security tests:
- `test_auth.py`: JWT validation, token expiration, invalid tokens
- `test_banned_users.py`: Ban enforcement across endpoints
- `test_user_search.py`: SQL injection protection tests
