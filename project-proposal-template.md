# Project Proposal Template

**Course**: Design of Dynamic Web Systems (M7011E)  
**Team Members**: Titouan Pastor, Damien Lanusse 
**Date**: 06/11/2025 

---

## 1. Problem Statement & Solution

**Problem**: Students often want to attend nightlife/events but don’t want to go alone. Coordination is fragmented (DMs, group chats), safety concerns exist (harassment, spiked drinks), and trust is hard to establish.

**Solution**: CrewUp is a lightweight web app where users discover nearby events, see people also interested, form a small group chat, and rate fellow attendees afterward. A “Party Mode” adds a Help button for quick group alerts and venue safety pings.

**Why Dynamic?**: Feeds and recommendations adapt to user location/interests/history; group chats and attendance rosters update in real-time; safety alerts propagate live to group members.

## 2. Core Features

**Main Features** (4-5 key capabilities):
1. **Accounts & Profiles**: bio, interests, verified email; basic reputation (post-event ratings + short comments).
2. **Events & Attendance**: create/list/inspect local events; RSVP “Going with a group”.
3. **Group Formation & Chat**: create/join a small group for an event; real-time messaging.
4. **Party Mode (Safety)**: one-tap Help alert to notify group & log incident timestamp/location.
4. **Post-Event Feedback**: rate group members + optional short review to build trust.

## 3. Target Users

**Primary Users**: Students/young adults attending campus bars/clubs/events.

**Key User Journey**: User logs in → sees tonight’s events near them → joins a small group → chats to meet up → uses Help if needed → after the night, leaves quick ratings.

## 4. Technology Stack

**Backend**: Python with FastAPI - *Justification: typed, fast dev, built-in OpenAPI*
**Database**: PostgreSQL - *Justification: relational data with clear relationships: users, events, groups, memberships, ratings*
**Frontend**: React *(minimal implementation)*

## 5. System Architecture

**Architecture Overview**:
```
[React SPA] ──> [API Gateway/Edge] ──> [User Svc] ─┐
                         │                         ├─> PostgreSQL (schemas per service)
                         ├─> [Event Svc] ──────────┘
                         ├─> [Group/Chat Svc (WS)]
                         ├─> [Rating Svc]
                         └─> [Safety Svc]
         (All behind Keycloak; inter-svc events via RabbitMQ)

```

**Microservices Plan**:
- **User Service**: profiles, roles, reputation summary.
- **Event Service**: events, RSVPs, geo filters.
- **Group/Chat Service**: group lifecycle + WebSocket chat + presence.
- **Rating Service**: post-event star + comment; aggregates reputation.
- **Safety Service**: Party Mode “Help” alerts, audit log.

## 6. Requirements Fulfillment

**Core Requirements**: All REQ1-REQ39 will be implemented through:
- Dynamic content via personalized event feed + real-time chat/alerts.
- Microservices architecture with :
    * **User Service** — profiles, roles, auth integration (Keycloak), reputation summary.
    * **Event Service** — events CRUD, search/filters, RSVPs.
    * **Group/Chat Service** — group lifecycle, WebSocket chat, presence, message history.
    * **Rating Service** — post-event ratings/comments, reputation aggregation.
    * **Safety Service** — Party Mode “Help” alerts, logging/audit, group notifications.
    * **Message Broker** — RabbitMQ for intra-service events (`ratings.created`, `safety.help.emitted`, `groups.member_joined`).
    * **PostgreSQL** — primary data store (schemas per bounded context).
- Testing strategy achieving 50%+ coverage
- Kubernetes deployment with monitoring

**Advanced Feature**: **Option E (Advanced Real-time features)**:
To ensure the correct working of the safety service and hopefully optimize the reaction time to an alert, we plan to implement connection resilience in our application. This would also ensure that the discussion service would remain up-to-date and available should the user leave the website. This will likely be implemented by regularly checking the connection to the server through pings.
We also plan to use websocket scaling through kubernetes so as to handle communication among massive groups of people (for events such as concerts for example).

**Target Grade**: **4**
The ideal target 5, is not realistic given that the group is composed of only 2 students, both of whom are exchange students that will leave Lulea before christmas.
The target 4 however, is realistic given that the advanced feature we plan to implement is something we would have already started. There would always have been somewhat advanced real time features, what with a safety service that would be working during an event, and we will only need to push those elements further. 

## 7. Development Plan
Example of development timeline:
**Weeks 1-2**: Database schema, basic services, authentication, Kubernetes setup
**Weeks 3-4**: Core features, API implementation, CI/CD pipeline
**Weeks 5**: Advanced feature, comprehensive testing, security
**Weeks 6-7**: Documentation, performance analysis, final polish, final presentation

## 8. Risk Assessment
**Main Risks**:
- **Technical**: 
  - **Risk**: WebSocket scaling and connection resilience across Kubernetes pods will be difficult, especially for real-time safety alerts where message delivery is critical.
  - **Mitigation**: We will start with a simple single-pod WebSocket setup, then incrementally add Redis/RabbitMQ for pub/sub messaging between pods. Implement connection retry logic early and add heartbeat/ping mechanisms. Have a fallback polling mechanism if WebSocket connections fail.

- **Scope**: 
  - **Risk**: Microservices architecture with 5 services + message broker + Kubernetes + advanced real-time features is ambitious for a 2-person team with limited timeframe.
  - **Mitigation**: We will prioritize core features first (users, events, groups, chats) and start with minimal viable implementation of each microservice, then enhance iteratively. We'll use Docker Compose for local development to speed up testing. We will time-box the advanced features to Week 5 only - if we are behind on schedule, we shall simplify WebSocket scaling to basic implementation and reduce Kubernetes complexity (e.g., manual scaling instead of auto-scaling).

**Fallback Plan (Minimum viable features for Grade 3)**:
- Simplified architecture: 2-3 combined services instead of 5 microservices
- Basic WebSocket chat without advanced scaling or connection resilience
- Remove Party Mode safety alerts; keep only basic group chat
- Simple star ratings without detailed reputation system

## 9. Team Organization

**[Member 1]**: [Primary responsibility area]
**[Member 2]**: [Primary responsibility area]

---

**Approval Request**: We request approval to proceed with this project concept and technology stack.

