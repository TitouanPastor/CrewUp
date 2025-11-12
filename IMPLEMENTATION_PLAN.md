# CrewUp - Iterative Implementation Plan

**Project**: CrewUp - Student Event & Safety Platform  
**Team**: Titouan Pastor, Damien Lanusse  
**Course**: Design of Dynamic Web Systems (M7011E)  
**Start Date**: November 6, 2024  
**Methodology**: Feature-by-feature incremental development with production-ready quality standards

---

## 📋 Development Principles

### API Quality Standards (Production-Ready)
All API endpoints must follow these requirements:

1. **HTTP Status Codes** - Proper semantic codes:
   - `200 OK` - Successful GET/PUT/PATCH
   - `201 Created` - Successful POST with resource creation
   - `204 No Content` - Successful DELETE
   - `400 Bad Request` - Validation errors, malformed request
   - `401 Unauthorized` - Missing/invalid authentication
   - `403 Forbidden` - Valid auth but insufficient permissions
   - `404 Not Found` - Resource doesn't exist
   - `409 Conflict` - Duplicate resource, constraint violation
   - `422 Unprocessable Entity` - Semantic validation errors
   - `500 Internal Server Error` - Unexpected server errors
   - `503 Service Unavailable` - Service temporarily down

2. **Error Response Format** - Consistent JSON structure:
   ```json
   {
     "error": {
       "code": "VALIDATION_ERROR",
       "message": "Invalid input data",
       "details": [
         {
           "field": "email",
           "message": "Invalid email format"
         }
       ],
       "timestamp": "2024-11-12T10:30:00Z",
       "request_id": "req_abc123"
     }
   }
   ```

3. **Input Validation** - Pydantic models with:
   - Type checking
   - Field constraints (min/max length, regex patterns)
   - Required vs optional fields
   - Custom validators for business logic

4. **Request/Response Logging** - Structured logs:
   - Request ID for tracing
   - User ID for audit trails
   - Execution time metrics
   - Error stack traces (dev only)

5. **API Documentation** - OpenAPI/Swagger with:
   - All endpoints documented
   - Request/response schemas
   - Example payloads
   - Error responses

6. **Rate Limiting** - Protection against abuse:
   - Per-user limits (e.g., 100 req/min)
   - Per-IP limits for unauthenticated endpoints
   - Proper `429 Too Many Requests` responses

7. **Security Headers** - FastAPI middleware:
   - CORS with strict origins
   - Content-Security-Policy
   - X-Content-Type-Options: nosniff
   - X-Frame-Options: DENY

---

## ✅ Phase 0 - Infrastructure & Authentication (COMPLETED)

## ✅ Phase 0 - Infrastructure & Authentication (COMPLETED)

### Sprint 0.1 - Infrastructure Setup ✅
**Completed**: November 6-10, 2024

- [x] Kubernetes cluster (k3s) deployed
- [x] PostgreSQL database configured
- [x] Keycloak authentication server with SSL certificates
- [x] Keycloak deployed via Helm chart
- [x] Custom Keycloak theme (Keycloakify + shadcn/ui, matching frontend design)
- [x] CI/CD pipeline with GitHub Actions (Docker build + GHCR push)

### Sprint 0.2 - Frontend Foundation ✅
**Completed**: November 10-12, 2024

- [x] React + Vite + TypeScript setup
- [x] shadcn/ui integration (15+ components)
- [x] Dark mode with next-themes (soft matte dark colors)
- [x] Responsive layout (desktop navbar + mobile bottom navigation)
- [x] Keycloak auto-redirect (login-required mode)
- [x] 404 NotFound page for invalid routes
- [x] Zustand stores (authStore, appStore)
- [x] Environment configuration (production vs development)

### Sprint 0.3 - Microservices Skeleton ✅
**Completed**: November 12, 2024

- [x] User Service (FastAPI + PostgreSQL)
- [x] Event Service (FastAPI + PostgreSQL)
- [x] Group Service (FastAPI + PostgreSQL)
- [x] Rating Service (FastAPI + PostgreSQL)
- [x] Safety Service (FastAPI + PostgreSQL)
- [x] Dockerfiles for all services
- [x] Helm chart with service definitions
- [x] Basic health check endpoints

---

## 🔄 Phase 1 - User Service

**Goal**: User profile management with Keycloak authentication integration

### Sprint 1.1 - Backend User Service API
**Status**: 🔴 TODO  
**Estimated Duration**: 2-3 days

#### Database Schema
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  keycloak_id VARCHAR(255) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  first_name VARCHAR(100),
  last_name VARCHAR(100),
  bio TEXT,
  profile_picture_url TEXT,
  interests TEXT[],
  reputation_score DECIMAL(3,2) DEFAULT 0.0,
  total_ratings INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_keycloak_id ON users(keycloak_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_reputation ON users(reputation_score DESC);
```

#### API Endpoints (Production-Ready)

**1. Create/Get Current User Profile**
```http
POST /api/v1/users
Authorization: Bearer <keycloak_token>
Content-Type: application/json

# Auto-creates user from Keycloak token if not exists
# Returns existing user if already created

Response 201 Created:
{
  "id": "uuid",
  "keycloak_id": "keycloak-uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "bio": null,
  "interests": [],
  "reputation_score": 0.0,
  "created_at": "2024-11-12T10:00:00Z"
}

Response 400 Bad Request:
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Keycloak token is malformed or expired",
    "timestamp": "2024-11-12T10:00:00Z",
    "request_id": "req_xyz"
  }
}
```

**2. Get Current User Profile**
```http
GET /api/v1/users/me
Authorization: Bearer <keycloak_token>

Response 200 OK:
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Student at LTU",
  "interests": ["music", "sports"],
  "reputation_score": 4.5,
  "total_ratings": 12,
  "created_at": "2024-11-12T10:00:00Z"
}

Response 401 Unauthorized:
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Missing or invalid authentication token"
  }
}

Response 404 Not Found:
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User profile not found. Please create one first."
  }
}
```

**3. Update User Profile**
```http
PUT /api/v1/users/me
Authorization: Bearer <keycloak_token>
Content-Type: application/json

{
  "bio": "Updated bio text",
  "interests": ["music", "sports", "travel"]
}

Response 200 OK:
{
  "id": "uuid",
  "bio": "Updated bio text",
  "interests": ["music", "sports", "travel"],
  "updated_at": "2024-11-12T10:30:00Z"
}

Response 400 Bad Request:
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": [
      {
        "field": "bio",
        "message": "Bio must be less than 500 characters"
      }
    ]
  }
}

Response 422 Unprocessable Entity:
{
  "error": {
    "code": "INVALID_INTERESTS",
    "message": "Interests array must contain 1-10 items"
  }
}
```

**4. Get Public User Profile**
```http
GET /api/v1/users/{user_id}
Authorization: Bearer <keycloak_token>

Response 200 OK:
{
  "id": "uuid",
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Student at LTU",
  "interests": ["music", "sports"],
  "reputation_score": 4.5,
  "total_ratings": 12
  // Note: email and keycloak_id are NOT exposed
}

Response 404 Not Found:
{
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with id 'uuid' not found"
  }
}
```

**5. Health Check**
```http
GET /api/v1/health

Response 200 OK:
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-11-12T10:00:00Z"
}

Response 503 Service Unavailable:
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Connection timeout"
}
```

#### Implementation Tasks
- [ ] Pydantic models with validators:
  ```python
  class UserUpdate(BaseModel):
      bio: Optional[str] = Field(None, max_length=500)
      interests: Optional[List[str]] = Field(None, min_items=1, max_items=10)
      
      @validator('interests')
      def validate_interests(cls, v):
          if v:
              for interest in v:
                  if len(interest) > 50:
                      raise ValueError('Each interest must be < 50 chars')
          return v
  ```

- [ ] JWT token validation middleware:
  ```python
  async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
      try:
          payload = jwt.decode(token, verify=False)  # Keycloak validates
          keycloak_id = payload.get("sub")
          if not keycloak_id:
              raise HTTPException(401, detail={"error": {...}})
          return await get_user_by_keycloak_id(keycloak_id)
      except JWTError:
          raise HTTPException(401, detail={"error": {...}})
  ```

- [ ] Database session management with rollback on errors
- [ ] Logging with correlation IDs
- [ ] Exception handlers for all error types
- [ ] Rate limiting (100 req/min per user)
- [ ] OpenAPI documentation with examples
- [ ] Unit tests (pytest) - coverage > 60%:
  - Test valid requests
  - Test validation errors
  - Test authentication errors
  - Test database errors
  - Test edge cases (duplicate users, concurrent updates)

#### Acceptance Criteria
- [ ] All endpoints return proper HTTP status codes
- [ ] Error responses follow standard format
- [ ] Input validation prevents invalid data
- [ ] Logs include request_id and user_id
- [ ] Swagger UI accessible at `/docs`
- [ ] Health check endpoint works
- [ ] Tests pass with > 60% coverage
- [ ] Manual API testing with curl/Postman successful

#### Validation Commands
```bash
# Create user (auto from token)
curl -X POST http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer $KEYCLOAK_TOKEN"

# Get current user
curl http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $KEYCLOAK_TOKEN"

# Update profile
curl -X PUT http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $KEYCLOAK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bio": "Test bio", "interests": ["music"]}'

# Get public profile
curl http://localhost:8001/api/v1/users/{uuid} \
  -H "Authorization: Bearer $KEYCLOAK_TOKEN"

# Health check
curl http://localhost:8001/api/v1/health

# Run tests
cd user/
pytest --cov=app --cov-report=term-missing tests/
```

#### Git Workflow
```bash
git checkout -b feature/user-service-api
# ... implement ...
git add user/
git commit -m "feat(user): implement production-ready user profile API

- Add complete CRUD endpoints with proper status codes
- Implement Keycloak JWT validation middleware
- Add comprehensive error handling and logging
- Add Pydantic validation with business rules
- Add unit tests with 60%+ coverage
- Add OpenAPI documentation"
git push origin feature/user-service-api
# ... merge to main after review ...
```

---

### Sprint 1.2 - Frontend User Profile Integration
**Status**: 🟡 PARTIAL (UI exists, not connected to backend)  
**Estimated Duration**: 1-2 days

---

### Sprint 1.2 - Frontend User Profile Integration
**Status**: 🟡 PARTIAL (UI exists, not connected to backend)  
**Estimated Duration**: 1-2 days

#### Implementation Tasks
- [ ] API service layer `src/services/api.ts`:
  ```typescript
  import axios from 'axios';
  import keycloak from '../keycloak';
  
  const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '/api/v1',
    timeout: 10000,
  });
  
  // Request interceptor: add auth token
  api.interceptors.request.use(async (config) => {
    if (keycloak.token) {
      config.headers.Authorization = `Bearer ${keycloak.token}`;
    }
    return config;
  });
  
  // Response interceptor: handle errors
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        keycloak.login();
      }
      return Promise.reject(error);
    }
  );
  
  export default api;
  ```

- [ ] User service `src/services/userService.ts`:
  ```typescript
  import api from './api';
  import { User } from '../types';
  
  export const userService = {
    getMe: async (): Promise<User> => {
      const { data } = await api.get('/users/me');
      return data;
    },
    
    updateProfile: async (update: Partial<User>): Promise<User> => {
      const { data } = await api.put('/users/me', update);
      return data;
    },
    
    getUserById: async (id: string): Promise<User> => {
      const { data } = await api.get(`/users/${id}`);
      return data;
    },
    
    createProfile: async (): Promise<User> => {
      const { data} = await api.post('/users');
      return data;
    }
  };
  ```

- [ ] Update ProfilePage.tsx to use real API
- [ ] Add loading states (Skeleton components)
- [ ] Add error handling with toast notifications
- [ ] Add form validation before submit
- [ ] Update authStore to fetch user on login

#### Acceptance Criteria
- [ ] ProfilePage loads real user data
- [ ] Bio editing persists to database
- [ ] Error messages displayed for API failures
- [ ] Loading states shown during API calls
- [ ] Form validation prevents invalid inputs

---

## 🔄 Phase 2 - Event Service

**Goal**: Create, list, search events with geolocation and attendance tracking

### Sprint 2.1 - Backend Event Service API
**Status**: 🔴 TODO  
**Estimated Duration**: 3-4 days

#### Database Schema
```sql
CREATE TABLE events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  creator_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  event_type VARCHAR(50) NOT NULL, -- party, concert, bar, club, other
  event_start TIMESTAMP NOT NULL,
  event_end TIMESTAMP,
  location_lat DECIMAL(10, 8),
  location_lng DECIMAL(11, 8),
  location_name VARCHAR(200),
  max_attendees INTEGER,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT valid_dates CHECK (event_end IS NULL OR event_end > event_start),
  CONSTRAINT valid_max_attendees CHECK (max_attendees IS NULL OR max_attendees > 0)
);

CREATE TABLE event_attendees (
  event_id UUID REFERENCES events(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  status VARCHAR(20) NOT NULL DEFAULT 'going', -- going, interested, maybe
  joined_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (event_id, user_id)
);

CREATE INDEX idx_events_creator ON events(creator_id);
CREATE INDEX idx_events_start_date ON events(event_start);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_location ON events USING GIST (
  ll_to_earth(location_lat, location_lng)
);
CREATE INDEX idx_event_attendees_user ON event_attendees(user_id);
```

#### Key API Endpoints (Summary)

All endpoints follow the same production-ready standards:
- Proper HTTP status codes (200, 201, 400, 401, 403, 404, 409, 422, 500)
- Consistent error response format
- Pydantic validation
- OpenAPI documentation
- Request/response logging
- Rate limiting

**Core Endpoints**:
- `POST /api/v1/events` - Create event (auth required)
- `GET /api/v1/events` - List events with filters (type, date range, geo)
- `GET /api/v1/events/{id}` - Get event details with attendee count
- `PUT /api/v1/events/{id}` - Update event (creator only)
- `DELETE /api/v1/events/{id}` - Delete event (creator only)
- `POST /api/v1/events/{id}/attend` - RSVP to event
- `DELETE /api/v1/events/{id}/attend` - Cancel RSVP
- `GET /api/v1/events/nearby` - Geo search (lat, lng, radius)
- `GET /api/v1/events/{id}/attendees` - List attendees

#### Special Features
- Geo-distance calculation using PostGIS or earth_distance
- Pagination for list endpoints (limit/offset)
- Filtering by date range, event type
- Sorting by date, popularity (attendee count), distance
- Prevent RSVP if max_attendees reached (409 Conflict)

---

### Sprint 2.2 - Frontend Events Discovery
**Status**: 🟡 PARTIAL (UI exists, mock data)  
**Estimated Duration**: 2-3 days

#### Implementation Tasks
- [ ] Event service `src/services/eventService.ts`
- [ ] Connect EventsPage to backend API
- [ ] Connect EventDetailPage to backend API
- [ ] Implement real geolocation (navigator.geolocation)
- [ ] Leaflet map with real event markers
- [ ] Functional Attend/Unattend button
- [ ] Real-time attendee count updates

---

## 🔄 Phase 3 - Group & Chat Service

**Goal**: Event-based groups with real-time WebSocket chat

### Sprint 3.1 - Backend Group Service API
**Status**: 🔴 TODO  
**Estimated Duration**: 4-5 days

#### Database Schema
```sql
CREATE TABLE groups (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID REFERENCES events(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  creator_id UUID REFERENCES users(id) ON DELETE CASCADE,
  max_members INTEGER DEFAULT 10,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT valid_max_members CHECK (max_members > 1 AND max_members <= 50)
);

CREATE TABLE group_members (
  group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL DEFAULT 'member', -- creator, member
  joined_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (group_id, user_id)
);

CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
  sender_id UUID REFERENCES users(id) ON DELETE SET NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  CONSTRAINT non_empty_content CHECK (length(trim(content)) > 0)
);

CREATE INDEX idx_groups_event ON groups(event_id);
CREATE INDEX idx_messages_group ON messages(group_id, created_at DESC);
```

#### REST API Endpoints
- `POST /api/v1/groups` - Create group for event
- `GET /api/v1/groups?event_id={uuid}` - List groups for event
- `GET /api/v1/groups/{id}` - Get group details
- `POST /api/v1/groups/{id}/join` - Join group
- `DELETE /api/v1/groups/{id}/leave` - Leave group
- `GET /api/v1/groups/{id}/members` - List members
- `GET /api/v1/groups/{id}/messages` - Message history (paginated)

#### WebSocket Endpoint
```
WS /api/v1/ws/groups/{group_id}?token={jwt}

# Client -> Server messages:
{
  "type": "message",
  "content": "Hello everyone!",
  "timestamp": "2024-11-12T10:00:00Z"
}

{
  "type": "typing",
  "is_typing": true
}

# Server -> Client messages:
{
  "type": "message",
  "id": "msg_uuid",
  "sender_id": "user_uuid",
  "sender_name": "John Doe",
  "content": "Hello everyone!",
  "timestamp": "2024-11-12T10:00:00Z"
}

{
  "type": "member_joined",
  "user_id": "uuid",
  "user_name": "Jane Doe",
  "timestamp": "2024-11-12T10:01:00Z"
}

{
  "type": "member_left",
  "user_id": "uuid",
  "user_name": "Jane Doe",
  "timestamp": "2024-11-12T10:05:00Z"
}

{
  "type": "error",
  "code": "MESSAGE_TOO_LONG",
  "message": "Message must be < 1000 characters"
}
```

#### Production Requirements
- WebSocket connection authentication via JWT
- Message persistence in database
- Broadcast to all group members
- Handle disconnections gracefully
- Prevent spam (rate limit messages per user)
- Input sanitization (XSS prevention)

---

### Sprint 3.2 - Frontend Group Chat
**Status**: 🟡 PARTIAL (UI exists, no WebSocket)  
**Estimated Duration**: 2-3 days

---

## 🔄 Phase 4 - Rating Service

**Goal**: Post-event peer ratings with reputation system

### Sprint 4.1 - Backend Rating Service API
**Status**: 🔴 TODO  
**Estimated Duration**: 2 days

#### Database Schema
```sql
CREATE TABLE ratings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_id UUID REFERENCES events(id) ON DELETE CASCADE,
  rater_id UUID REFERENCES users(id) ON DELETE CASCADE,
  rated_id UUID REFERENCES users(id) ON DELETE CASCADE,
  stars INTEGER NOT NULL CHECK (stars >= 1 AND stars <= 5),
  comment TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(event_id, rater_id, rated_id),
  CONSTRAINT no_self_rating CHECK (rater_id != rated_id)
);

CREATE INDEX idx_ratings_rated ON ratings(rated_id);
CREATE INDEX idx_ratings_event ON ratings(event_id);
```

#### API Endpoints
- `POST /api/v1/ratings` - Submit rating (one per user per event)
- `GET /api/v1/ratings/user/{user_id}` - Get ratings received
- `GET /api/v1/users/{id}/reputation` - Calculate avg score

#### Business Logic
- Update users.reputation_score via database trigger or async event
- Prevent duplicate ratings (409 Conflict)
- Only allow rating after event ends
- Comment moderation (profanity filter - optional)

---

## 🔄 Phase 5 - Safety Service (Party Mode)

**Goal**: Emergency Help button with real-time group alerts

### Sprint 5.1 - Backend Safety Service API
**Status**: 🔴 TODO  
**Estimated Duration**: 2-3 days

#### Database Schema
```sql
CREATE TABLE safety_alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
  event_id UUID REFERENCES events(id) ON DELETE CASCADE,
  alert_type VARCHAR(50) NOT NULL, -- help, check_in, emergency
  location_lat DECIMAL(10, 8),
  location_lng DECIMAL(11, 8),
  resolved BOOLEAN DEFAULT FALSE,
  resolved_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_alerts_group ON safety_alerts(group_id);
CREATE INDEX idx_alerts_user ON safety_alerts(user_id);
```

#### API Endpoints
- `POST /api/v1/safety/alert` - Trigger Help alert
- `GET /api/v1/safety/alerts?group_id={uuid}` - List group alerts
- `PUT /api/v1/safety/alerts/{id}/resolve` - Mark resolved

#### Integration
- Publish RabbitMQ event `safety.help.emitted`
- WebSocket broadcast to group members
- Log all alerts for audit trail

---

## 🔄 Phase 6 - Advanced Features (Grade 4 Target)

### Sprint 6.1 - WebSocket Connection Resilience
**Status**: 🔴 TODO

- [ ] Auto-reconnection with exponential backoff
- [ ] Heartbeat/ping-pong mechanism
- [ ] Offline message queueing
- [ ] Connection status UI indicator
- [ ] Fallback to HTTP polling if WS fails

### Sprint 6.2 - WebSocket Horizontal Scaling (Kubernetes)
**Status**: 🔴 TODO

- [ ] Redis Pub/Sub for cross-pod message broadcasting
- [ ] Sticky session configuration (session affinity)
- [ ] WebSocket health checks
- [ ] Horizontal Pod Autoscaler (HPA) configuration
- [ ] Load testing with multiple replicas

---

## 🔄 Phase 7 - Testing & Security

### Sprint 7.1 - Comprehensive Testing
**Status**: 🔴 TODO

**Backend**:
- [ ] Unit tests (pytest) - > 60% coverage all services
- [ ] Integration tests with test database
- [ ] API contract tests (Postman/Newman)
- [ ] Load testing (Locust or k6)

**Frontend**:
- [ ] Component tests (Vitest + React Testing Library)
- [ ] E2E tests (Playwright) - critical user flows
- [ ] Accessibility testing (axe-core)

### Sprint 7.2 - Security Hardening
**Status**: 🔴 TODO

- [ ] Rate limiting all endpoints (FastAPI Limiter)
- [ ] Input sanitization (prevent XSS, SQL injection)
- [ ] Security headers (CSP, HSTS, X-Frame-Options)
- [ ] CORS strict configuration
- [ ] Dependency vulnerability scanning (safety, npm audit)
- [ ] Secrets management (Kubernetes Secrets)
- [ ] API key rotation strategy

---

## 🔄 Phase 8 - Documentation & Observability

### Sprint 8.1 - Documentation
**Status**: 🔴 TODO

- [ ] README.md with setup instructions
- [ ] Architecture diagrams (C4 model or similar)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] User guide with screenshots
- [ ] Developer onboarding guide
- [ ] Database schema documentation

### Sprint 8.2 - Monitoring & Performance
**Status**: 🔴 TODO

- [ ] Prometheus metrics (custom + default)
- [ ] Grafana dashboards (requests, latency, errors)
- [ ] Centralized logging (Loki or ELK)
- [ ] Database query optimization (indexes, EXPLAIN ANALYZE)
- [ ] Frontend bundle size optimization (code splitting)
- [ ] Lighthouse performance audit (> 90 score)

---

## 📊 Progress Tracking

| Phase | Status | Start Date | Completion Date | Notes |
|-------|--------|------------|----------------|-------|
| Phase 0: Infrastructure | ✅ DONE | Nov 6, 2024 | Nov 12, 2024 | All infrastructure ready |
| Phase 1: User Service | 🔄 IN PROGRESS | Nov 12, 2024 | - | Next: Backend API |
| Phase 2: Event Service | 🔴 TODO | - | - | - |
| Phase 3: Group & Chat | 🔴 TODO | - | - | - |
| Phase 4: Rating Service | 🔴 TODO | - | - | - |
| Phase 5: Safety Service | 🔴 TODO | - | - | - |
| Phase 6: Advanced Features | 🔴 TODO | - | - | Grade 4 target |
| Phase 7: Testing & Security | 🔴 TODO | - | - | - |
| Phase 8: Documentation | 🔴 TODO | - | - | - |

---

## 🎯 Definition of Done (DoD)

Every feature must meet ALL criteria before being considered complete:

### Code Quality
- [ ] Code follows project style guide (PEP 8 for Python, ESLint for TypeScript)
- [ ] No linter warnings or errors
- [ ] All variables/functions have meaningful names
- [ ] Complex logic has explanatory comments

### Functionality
- [ ] Feature works as specified in requirements
- [ ] All happy paths tested manually
- [ ] Edge cases handled gracefully
- [ ] Error messages are user-friendly

### API Standards (Backend)
- [ ] Proper HTTP status codes used
- [ ] Error responses follow standard format
- [ ] Input validation with Pydantic
- [ ] OpenAPI documentation complete
- [ ] Request/response logging implemented
- [ ] Rate limiting configured

### Testing
- [ ] Unit tests written and passing
- [ ] Code coverage > 60% for backend
- [ ] Integration tests for critical paths
- [ ] Manual testing completed

### Documentation
- [ ] API endpoints documented in OpenAPI/Swagger
- [ ] Code comments for complex logic
- [ ] README updated if needed
- [ ] Database migrations documented

### Security
- [ ] Authentication/authorization implemented
- [ ] Input sanitized to prevent XSS/SQL injection
- [ ] Secrets not hardcoded
- [ ] Security headers configured

### DevOps
- [ ] Code committed with descriptive message
- [ ] CI/CD pipeline passes (tests + build)
- [ ] Docker image builds successfully
- [ ] Deployed to k3s cluster
- [ ] Health checks passing in production

### Review
- [ ] Code review completed (pair programming or PR review)
- [ ] No blocking issues from review
- [ ] Approved by at least 1 team member

---

## 🚀 Quick Start: Next Feature

**Current Focus**: Sprint 1.1 - Backend User Service API

### Step-by-Step Implementation

```bash
# 1. Create feature branch
git checkout -b feature/user-service-api

# 2. Navigate to service
cd user/

# 3. Implement database schema
# Edit: user/app/db/schema.sql
# Run migrations

# 4. Implement Pydantic models
# Create: user/app/models/user.py

# 5. Implement API endpoints
# Create: user/app/routers/users.py

# 6. Add authentication middleware
# Create: user/app/middleware/auth.py

# 7. Add error handlers
# Edit: user/app/main.py

# 8. Write tests
# Create: user/tests/test_users.py

# 9. Run tests
pytest --cov=app --cov-report=term-missing tests/
# Target: > 60% coverage

# 10. Run service locally
uvicorn app.main:app --reload --port 8001

# 11. Test manually
curl -X POST http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer $TOKEN"

# 12. Verify OpenAPI docs
# Open: http://localhost:8001/docs

# 13. Commit changes
git add .
git commit -m "feat(user): implement production-ready user API

- Add PostgreSQL schema with proper indexes
- Implement CRUD endpoints with proper HTTP codes
- Add Keycloak JWT validation middleware
- Implement comprehensive error handling
- Add Pydantic models with validation
- Add unit tests with 60%+ coverage
- Add OpenAPI documentation with examples
- Add request/response logging
- Configure rate limiting"

# 14. Push to remote
git push origin feature/user-service-api

# 15. Create Pull Request (if using PR workflow)
# OR merge directly to main

# 16. Deploy to k3s
kubectl rollout restart deployment/user-service -n crewup

# 17. Verify health check
curl https://api.ltu-m7011e-3.se/users/health

# 18. Mark sprint as DONE in progress tracker
```

---

## 📝 Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, missing semi-colons, etc)
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `perf`: Performance improvement
- `test`: Adding missing tests
- `chore`: Changes to build process or auxiliary tools

**Examples**:
```bash
feat(user): add user profile update endpoint

- Implement PUT /api/v1/users/me
- Add Pydantic validation for bio and interests
- Add unit tests with 70% coverage

Closes #123
```

```bash
fix(auth): handle expired JWT tokens gracefully

- Add proper error handling for token expiration
- Return 401 with clear error message
- Add test case for expired tokens

Fixes #456
```

---

## 🔗 Useful Resources

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [Pydantic Validation](https://docs.pydantic.dev/)
- [PostgreSQL Index Tuning](https://www.postgresql.org/docs/current/indexes.html)
- [WebSocket Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/)

---

**Document Version**: 1.0  
**Last Updated**: November 12, 2024  
**Next Review**: After each sprint completion  
**Maintained By**: Titouan Pastor, Damien Lanusse
- [ ] Schema PostgreSQL pour events
  ```sql
  CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID REFERENCES users(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    event_type VARCHAR(50), -- party, concert, bar, club
    event_start TIMESTAMP NOT NULL,
    event_end TIMESTAMP,
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    location_name VARCHAR(200),
    max_attendees INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
  );
  
  CREATE TABLE event_attendees (
    event_id UUID REFERENCES events(id),
    user_id UUID REFERENCES users(id),
    status VARCHAR(20), -- going, interested, maybe
    PRIMARY KEY (event_id, user_id)
  );
  ```
- [ ] Endpoints FastAPI:
  - `POST /api/events` - Créer événement
  - `GET /api/events` - Lister avec filtres (type, date, geo)
  - `GET /api/events/{id}` - Détail événement
  - `POST /api/events/{id}/attend` - RSVP
  - `GET /api/events/nearby?lat=&lng=&radius=` - Événements proches
- [ ] Filtres et tri (date, popularité, distance)
- [ ] Tests unitaires

#### Validation:
- [ ] Créer event via API fonctionne
- [ ] Filtres par type/date fonctionnent
- [ ] Geo search retourne events triés par distance
- [ ] Tests > 50% coverage

---

### Sprint 2.2 - Frontend Events Discovery
**Status**: 🟡 PARTIEL (UI existe, mock data)

#### Tâches:
- [ ] Service API `src/services/eventService.ts`
- [ ] Connecter EventsPage au backend
- [ ] Connecter EventDetailPage au backend
- [ ] Intégrer vraie géolocalisation (navigator.geolocation)
- [ ] Carte Leaflet avec vrais événements
- [ ] Bouton "Attend" fonctionnel

#### Validation:
- [ ] Liste d'événements charge depuis API
- [ ] Filtres/recherche fonctionnent
- [ ] Carte affiche les bons markers
- [ ] RSVP persiste en base

---

## 🔄 Phase 3 - Group & Chat Service

**Objectif**: Groupes pour événements + chat temps réel

### Sprint 3.1 - Backend Group Service
**Status**: 🔴 TODO

#### Tâches:
- [ ] Schema PostgreSQL pour groups
  ```sql
  CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id),
    name VARCHAR(100),
    creator_id UUID REFERENCES users(id),
    max_members INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT NOW()
  );
  
  CREATE TABLE group_members (
    group_id UUID REFERENCES groups(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) DEFAULT 'member', -- creator, member
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (group_id, user_id)
  );
  
  CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id UUID REFERENCES groups(id),
    sender_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] Endpoints FastAPI:
  - `POST /api/groups` - Créer groupe pour un event
  - `GET /api/groups?event_id=` - Lister groupes d'un event
  - `POST /api/groups/{id}/join` - Rejoindre groupe
  - `GET /api/groups/{id}/messages` - Historique messages
  - `GET /api/groups/{id}/members` - Liste membres
- [ ] WebSocket endpoint `/ws/groups/{group_id}`:
  - Messages temps réel
  - Notifications member_joined / member_left
  - Typing indicators (optionnel)
- [ ] Tests unitaires

#### Validation:
- [ ] Créer groupe fonctionne
- [ ] Rejoindre groupe met à jour members
- [ ] WebSocket envoie/reçoit messages
- [ ] Historique persiste en DB

---

### Sprint 3.2 - Frontend Group Chat
**Status**: 🟡 PARTIEL (UI existe, pas de WebSocket)

#### Tâches:
- [ ] Service API `src/services/groupService.ts`
- [ ] WebSocket client pour chat temps réel
- [ ] Connecter GroupChatPage au backend
- [ ] Afficher historique messages
- [ ] Envoyer messages via WebSocket
- [ ] Afficher membres en temps réel
- [ ] Notifications de connexion/déconnexion

#### Validation:
- [ ] Chat temps réel fonctionne entre 2+ users
- [ ] Messages persistent après refresh
- [ ] Notifications de nouveaux membres

---

## 🔄 Phase 4 - Rating Service

**Objectif**: Noter les autres membres après événement

### Sprint 4.1 - Backend Rating Service
**Status**: 🔴 TODO

#### Tâches:
- [ ] Schema PostgreSQL pour ratings
  ```sql
  CREATE TABLE ratings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID REFERENCES events(id),
    rater_id UUID REFERENCES users(id),
    rated_id UUID REFERENCES users(id),
    stars INTEGER CHECK (stars >= 1 AND stars <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(event_id, rater_id, rated_id)
  );
  ```
- [ ] Endpoints FastAPI:
  - `POST /api/ratings` - Créer rating
  - `GET /api/ratings/user/{user_id}` - Voir ratings reçus
  - `GET /api/users/{id}/reputation` - Calculer moyenne
- [ ] Calcul reputation_score (moyenne pondérée)
- [ ] Update users.reputation_score via trigger ou event
- [ ] Tests unitaires

#### Validation:
- [ ] Rating persiste en DB
- [ ] Reputation score se met à jour
- [ ] Cannot rate twice same person for same event

---

### Sprint 4.2 - Frontend Post-Event Ratings
**Status**: 🔴 TODO

#### Tâches:
- [ ] Page `RateGroupPage.tsx` (nouvelle)
- [ ] Liste membres du groupe après event
- [ ] Composant StarRating
- [ ] Textarea pour commentaire optionnel
- [ ] Submit ratings en batch
- [ ] Afficher reputation sur ProfilePage

#### Validation:
- [ ] Rating UI fonctionne
- [ ] Reputation visible sur profils
- [ ] Cannot submit invalid ratings

---

## 🔄 Phase 5 - Safety Service (Party Mode)

**Objectif**: Bouton Help + alertes groupe en temps réel

### Sprint 5.1 - Backend Safety Service
**Status**: 🔴 TODO

#### Tâches:
- [ ] Schema PostgreSQL pour safety
  ```sql
  CREATE TABLE safety_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    group_id UUID REFERENCES groups(id),
    event_id UUID REFERENCES events(id),
    alert_type VARCHAR(50), -- help, check_in
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
  );
  ```
- [ ] Endpoints FastAPI:
  - `POST /api/safety/alert` - Déclencher Help
  - `GET /api/safety/alerts?group_id=` - Voir alertes groupe
  - `PUT /api/safety/alerts/{id}/resolve` - Marquer résolu
- [ ] RabbitMQ producer pour événements `safety.help.emitted`
- [ ] WebSocket broadcast alert vers groupe
- [ ] Tests unitaires

#### Validation:
- [ ] Alert créé en DB avec timestamp/location
- [ ] Tous membres du groupe reçoivent notification WS
- [ ] Event RabbitMQ publié

---

### Sprint 5.2 - Frontend Party Mode
**Status**: 🟡 PARTIEL (UI bouton existe, pas fonctionnel)

#### Tâches:
- [ ] Service API `src/services/safetyService.ts`
- [ ] Connecter bouton Alert de Navbar
- [ ] Modal confirmation avant envoi
- [ ] Récupérer géolocalisation avant envoi
- [ ] Toast notification aux membres du groupe
- [ ] Badge notification sur BottomNav si alerte active
- [ ] Page `SafetyAlertsPage.tsx` pour voir historique

#### Validation:
- [ ] Hold 2s sur bouton déclenche alerte
- [ ] Groupe reçoit notification immédiate
- [ ] Location capturée et envoyée

---

## 🔄 Phase 6 - Advanced Features (Grade 4)

**Objectif**: Connection resilience + WebSocket scaling

### Sprint 6.1 - WebSocket Resilience
**Status**: 🔴 TODO

#### Tâches:
- [ ] Reconnection automatique côté frontend
- [ ] Heartbeat/ping-pong pour détecter disconnects
- [ ] Queue messages offline et resend
- [ ] Indicateur connection status UI
- [ ] Fallback polling si WebSocket fail
- [ ] Tests de déconnexion réseau

#### Validation:
- [ ] Disconnect/reconnect ne perd pas de messages
- [ ] UI affiche "Reconnecting..."
- [ ] Offline messages envoyés au reconnect

---

### Sprint 6.2 - WebSocket Scaling (Kubernetes)
**Status**: 🔴 TODO

#### Tâches:
- [ ] Redis Pub/Sub pour broadcast cross-pods
- [ ] Sticky sessions ou session affinity
- [ ] Health checks WebSocket pods
- [ ] HPA (Horizontal Pod Autoscaler) config
- [ ] Tests load avec multiple replicas

#### Validation:
- [ ] Messages broadcast entre pods
- [ ] Scale up/down sans perte de connexions
- [ ] Load test 100+ concurrent users

---

## 🔄 Phase 7 - Testing & Security

### Sprint 7.1 - Comprehensive Testing
**Status**: 🔴 TODO

#### Tâches:
- [ ] Backend: pytest coverage > 50% tous services
- [ ] Frontend: Vitest/RTL tests composants critiques
- [ ] Integration tests API avec Postman/Newman
- [ ] E2E tests avec Playwright (user flows)
- [ ] Load testing avec k6 ou Locust

---

### Sprint 7.2 - Security Hardening
**Status**: 🔴 TODO

#### Tâches:
- [ ] Rate limiting sur tous endpoints
- [ ] Input validation stricte (Pydantic)
- [ ] XSS protection headers
- [ ] CORS configuration stricte
- [ ] SQL injection prevention audit
- [ ] Dependency vulnerability scan (npm audit, safety)
- [ ] Secrets management (Kubernetes Secrets)

---

## 🔄 Phase 8 - Documentation & Polish

### Sprint 8.1 - Documentation
**Status**: 🔴 TODO

#### Tâches:
- [ ] README.md complet avec setup instructions
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Architecture diagrams (draw.io ou Excalidraw)
- [ ] User guide screenshots
- [ ] Developer onboarding doc

---

### Sprint 8.2 - Performance & Monitoring
**Status**: 🔴 TODO

#### Tâches:
- [ ] Prometheus metrics tous services
- [ ] Grafana dashboards
- [ ] Logging centralisé (ELK ou Loki)
- [ ] Database indexes optimization
- [ ] Frontend bundle size optimization
- [ ] Lighthouse performance audit

---

## 📊 Progress Tracker

| Phase | Status | Start Date | End Date | Notes |
|-------|--------|------------|----------|-------|
| Phase 0 | ✅ DONE | 06/11/2024 | 12/11/2024 | Infrastructure OK |
| Phase 1 | 🔄 IN PROGRESS | 12/11/2024 | - | User Service next |
| Phase 2 | 🔴 TODO | - | - | - |
| Phase 3 | 🔴 TODO | - | - | - |
| Phase 4 | 🔴 TODO | - | - | - |
| Phase 5 | 🔴 TODO | - | - | - |
| Phase 6 | 🔴 TODO | - | - | Advanced features |
| Phase 7 | 🔴 TODO | - | - | - |
| Phase 8 | 🔴 TODO | - | - | - |

---

## 🎯 Définition of Done (DoD)

Pour chaque feature:
1. ✅ Code écrit et fonctionnel
2. ✅ Tests unitaires passent (> 50% coverage)
3. ✅ API documentation à jour
4. ✅ Validation manuelle OK
5. ✅ Code review (pair programming)
6. ✅ Git commit + push
7. ✅ CI/CD pipeline passe (build + tests)
8. ✅ Deployed sur cluster k3s et testé

---

## 🚀 Quick Start Next Feature

**Prochaine étape recommandée**: Sprint 1.1 - Backend User Service

```bash
# 1. Créer branche feature
git checkout -b feature/user-service-backend

# 2. Implémenter
cd user/
# ... code ...

# 3. Tester
pytest --cov=app tests/

# 4. Valider
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/users/me

# 5. Push
git add .
git commit -m "feat(user): implement user profile CRUD"
git push origin feature/user-service-backend

# 6. Merge to main
git checkout main
git merge feature/user-service-backend
git push
```

---

**Last Updated**: 12 Novembre 2024  
**Next Review**: Après chaque sprint completé
