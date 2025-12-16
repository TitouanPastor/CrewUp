# Mid-term Demo - M7011E

**Group Number**: 3  
**Team Members**: Titouan Pastor, Damien Lanusse  
**Date**: November 26, 2025

---

## Instructions
Mandatory Non-graded checkpoint. Be honest about your progress - we're here to help. You'll submit this template and do a brief demo of your deployed system.

---

## Part 1: Technical Infrastructure

### Repository & CI/CD
- [x] Git repository or repositories (if multirepo, use git org) with all members contributing
  - **Repo URL**: https://github.com/TitouanPastor/CrewUp

- [x] GitOps CI pipeline functional
  - **Link**: [.github/workflows/ci-cd.yaml, .github/workflows/promote.yaml](https://github.com/TitouanPastor/CrewUp/tree/main/.github/workflows)
  - **Status**: Builds + pushes images to registry (no automated tests yet)

- [x] ArgoCD setup for GitOps deployment (CD)
  - **Status**: Deploying automatically (3 apps: dev auto-sync, staging/prod manual via GitHub workflow)

### Kubernetes Deployment
- [x] Services deployed to K8s cluster
  - **Services deployed**: frontend, event, group, user, safety, postgres, keycloak
  - **Public URL(s)**: https://crewup.ltu-m7011e-3.se (prod), https://crewup-dev.ltu-m7011e-3.se (dev), https://crewup-staging.ltu-m7011e-3.se (staging)

- [x] HTTPS with certificates working
  - **Status**: Working (Let's Encrypt via Traefik)

- [ ] Monitoring/Observability setup
  - **Status**: Not started (Grafana, Prometheus, Jaeger planned for later)

### Backend Services
- [x] Microservices architecture implemented
  - **Service 1**: User Service - profiles, auth integration
  - **Service 2**: Event Service - events CRUD, search, RSVPs
  - **Service 3**: Group Service - group lifecycle, WebSocket chat, real-time messaging
  - **Service 4**: Safety Service - safety alerts, group notifications

- [x] Database deployed and accessible
  - **Type**: PostgreSQL
  - **Schema**: helm/crewup/config/schema.sql

- [x] Inter-service communication method
  - **Approach**: REST + WebSocket (HTTP for service-to-service, WS for real-time chat)
  - **Planned**: Migration to RabbitMQ for asynchronous resilient inter-service communication

### Testing
- [x] Backend tests written
  - **Link**: event/tests/, group/tests/, user/tests/, safety/tests/
  - **Coverage estimate**: 96% (event), ~60% (others - need to rework for CI/CD pipeline)

### Frontend
- [x] Frontend framework deployed
  - **Framework**: React + Vite + TypeScript
  - **Public URL**: https://crewup.ltu-m7011e-3.se
  - **Status**: Connected to backend (auth, events, groups, chat, profile, safety working - error handling implemented)

### Security & Auth
- [x] Keycloak integration status
  - **Status**: Full integration (runtime config per env, protected routes, JWT validation)

---

## Part 2: Feature Implementation

List your main features and current status:

1. **User Accounts & Profiles**
   - Status: Deployed and working
   - Can demo: Yes (signup, login, profile management)

2. **Event Discovery & RSVP**
   - Status: Deployed and working
   - Can demo: Yes (create events, search/filter, RSVP going/interested, real-time updates)

3. **Group Formation & Real-time Chat**
   - Status: Deployed and working
   - Can demo: Yes (create groups, join groups, WebSocket chat, live messaging)

4. **Safety Alert System**
   - Status: In progress
   - Can demo: Partially (should be finished for the demo)

---

## Part 3: Self-Assessment

**Overall progress:**
- [ ] Ahead of schedule
- [x] On track
- [ ] Slightly behind but manageable
- [ ] Significantly behind - need help

**What's working well:**
GitOps deployment pipeline is smooth (dev auto-deploys, staging/prod manual promotion via GitHub workflow). Microservices architecture is clean with good separation. Real-time features (WebSocket chat) working reliably. Frontend is polished with proper error handling.

**Biggest blocker so far:**
Need to implement automated tests in CI/CD pipeline (currently tests run locally only). Setting up test database for GitHub Actions workflow is the main challenge.

**What would help most:**
Guidance on: 1) Running backend tests in GitHub Actions with a test database (how to spin up PostgreSQL for tests), 2) WebSocket scaling strategies across Kubernetes pods for production load.

**Team dynamics:**
Good collaboration, clear task division, regular communication. No issues.

---

## Part 4: Demo Preparation

**For your live demo, prepare to show:**
- Your deployed system running (visit your public URL(s))
- One working feature end-to-end
- Your ArgoCD dashboard and deployment status (If applicable)
- Database schema and explain one design choice (To practice for the final seminar)

**Questions you should be ready to answer:**
- How does GitOps deployment work in your setup? (Or the plan if not ready yet)
- Explain your microservices architecture (Current status, planned architecture, any changes from the proposal)
- What's your next implementation priority?
