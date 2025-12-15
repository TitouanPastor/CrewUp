# CrewUp System Report

This folder contains comprehensive documentation of the CrewUp system architecture and design.

## Contents

1. **motivation.md** - Explains what makes CrewUp a dynamic web system
2. **architecture.md** - High-level architecture diagrams and explanations
   - Microservices architecture
   - GitOps CI/CD pipeline
   - Security model and request flow
   - Monitoring and observability setup
3. **database-schema.md** - Database schema documentation with diagrams
4. **diagrams/** - Visual architecture diagrams (Mermaid format)

## Quick Overview

CrewUp is a microservice-based event and group discovery application that enables users to:
- Discover and create events
- Form groups for events
- Communicate via real-time chat
- Share safety alerts
- Rate and build reputation

The system is built with:
- 6 backend microservices (FastAPI/Python)
- 1 frontend application (React)
- PostgreSQL database
- RabbitMQ message broker
- Keycloak for authentication
- GitOps deployment with ArgoCD
- Comprehensive monitoring with Prometheus & Grafana
