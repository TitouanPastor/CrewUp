# Project Proposal Template

**Course**: Design of Dynamic Web Systems (M7011E)  
**Team Members**: Titouan Pastor, Damien Lanusse 
**Date**: 06/11/2025 

---

## 1. Problem Statement & Solution

**Problem**: Students often want to attend nightlife/events but don’t want to go alone. Coordination is fragmented (DMs, group chats), safety concerns exist (harassment, spiked drinks), and trust is hard to establish.

**Solution**: NightLink is a lightweight web app where users discover nearby events, see people also interested, form a small group chat, and rate fellow attendees afterward. A “Party Mode” adds a Help button for quick group alerts and venue safety pings.

**Why Dynamic?**: Feeds and recommendations adapt to user location/interests/history; group chats and attendance rosters update in real-time; safety alerts propagate live to group members.

## 2. Core Features

**Main Features** (4-5 key capabilities):
1. **Accounts & Profiles**: bio, interests, verified email; basic reputation (post-event ratings + short comments).
2. **Events & Attendance**: list/inspect local events; RSVP “Going with a group”.
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
- Microservices architecture with [service breakdown]
- Testing strategy achieving 50%+ coverage
- Kubernetes deployment with monitoring

**Advanced Feature**: **Option [A/B/C/D/E]** - [Brief implementation plan]

**Target Grade**: [3/4/5] - *Justification: [Why this target is realistic]*

## 7. Development Plan
Example of development timeline:
**Weeks 1-2**: Database schema, basic services, authentication, Kubernetes setup
**Weeks 3-4**: Core features, API implementation, CI/CD pipeline
**Weeks 5-6**: Advanced feature, comprehensive testing, security
**Weeks 7-8**: Documentation, performance analysis, final polish

## 8. Risk Assessment
**Main Risks**:
- **Technical**: [One key risk and mitigation]
- **Scope**: [One key risk and mitigation]

**Fallback Plan**: [Minimum viable features for Grade 3]
## 9. Team Organization

**[Member 1]**: [Primary responsibility area]
**[Member 2]**: [Primary responsibility area]
**[Member 3]**: [Primary responsibility area]

---

**Approval Request**: We request approval to proceed with this project concept and technology stack.
