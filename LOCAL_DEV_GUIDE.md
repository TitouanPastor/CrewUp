# Local Development Guide

## Prerequisites
- PostgreSQL running locally
- Python 3.11+
- Node.js 20+
- Keycloak test client configured (`crewup-test`)

---

## Option 1: Run in Terminals (Development Mode)

### Terminal 1: PostgreSQL Database
```bash
# If using system PostgreSQL (already running):
sudo systemctl status postgresql

# Create database if not exists:
psql -U postgres -c "CREATE DATABASE crewup;"
psql -U postgres -c "CREATE USER crewup WITH PASSWORD 'crewup_dev_password';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE crewup TO crewup;"

# Load schema:
psql -U crewup -d crewup -f database/schema.sql
```

### Terminal 2: User Service Backend
```bash
cd user/

# Create virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run service
uvicorn app.main:app --reload --port 8001

# Service will be available at: http://localhost:8001
# OpenAPI docs: http://localhost:8001/docs
```

### Terminal 3: Frontend
```bash
cd frontend/

# Install dependencies (first time only)
npm install

# Create .env file (already done)
# It should contain:
# VITE_API_URL=http://localhost:8001/api/v1
# VITE_KEYCLOAK_CLIENT_ID=crewup-test

# Run dev server
npm run dev

# Frontend will be available at: http://localhost:3000
```

### Access the App
Open **http://localhost:3000** in your browser:
1. You'll be redirected to Keycloak login
2. Login with your test user
3. Profile page will auto-create your user profile
4. You can edit bio and interests

---

## Option 2: Run with Docker Compose (Production-like)

### Build all services
```bash
# Build all Docker images
./build-all.sh
```

### Run with Docker Compose
```bash
# Start all services
docker-compose up

# Or in detached mode:
docker-compose up -d

# View logs:
docker-compose logs -f

# Stop all services:
docker-compose down
```

### Services running:
- **PostgreSQL**: localhost:5432
- **User Service**: http://localhost:8001
- **Event Service**: http://localhost:8002
- **Group Service**: http://localhost:8003
- **Rating Service**: http://localhost:8004
- **Safety Service**: http://localhost:8005
- **Frontend**: http://localhost:3000

---

## Current Development Status

### ✅ Completed
- **User Service Backend**: Full CRUD API with authentication
- **User Service Frontend**: Profile page with real API integration

### 🔄 In Progress
- Testing User Service integration

### 🔴 TODO
- Event Service implementation
- Group Service implementation
- Rating Service implementation
- Safety Service implementation

---

## Testing the User Service

### Backend API Tests
```bash
cd user/
source venv/bin/activate
pytest --cov=app --cov-report=term-missing tests/

# Expected: 11 tests passing, 79% coverage
```

### Manual API Testing
```bash
# Get Keycloak token
export TOKEN=$(curl -X POST "https://keycloak.ltu-m7011e-3.se/realms/crewup/protocol/openid-connect/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_EMAIL" \
  -d "password=YOUR_PASSWORD" \
  -d "grant_type=password" \
  -d "client_id=crewup-test" \
  | jq -r '.access_token')

# Create/Get user profile
curl -X POST http://localhost:8001/api/v1/users \
  -H "Authorization: Bearer $TOKEN"

# Get your profile
curl http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN"

# Update profile
curl -X PUT http://localhost:8001/api/v1/users/me \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"bio": "Test bio", "interests": ["music", "sports"]}'
```

See `user/TEST_COMMANDS.md` for more examples.

---

## Environment Variables

### Frontend (.env)
```bash
# Local development
VITE_API_URL=http://localhost:8001/api/v1
VITE_KEYCLOAK_URL=https://keycloak.ltu-m7011e-3.se
VITE_KEYCLOAK_REALM=crewup
VITE_KEYCLOAK_CLIENT_ID=crewup-test  # Use test client for local dev
```

### Backend (user/app/config.py)
```python
# Uses environment variables with defaults:
POSTGRES_HOST=localhost  # or "postgres" in Docker
POSTGRES_PORT=5432
POSTGRES_DB=crewup
POSTGRES_USER=crewup
POSTGRES_PASSWORD=crewup_dev_password
```

---

## Common Issues

### Port already in use
```bash
# Kill process on port 8001
lsof -ti:8001 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### Database connection error
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -U postgres -l | grep crewup
```

### Keycloak token expired
Tokens expire after 5 minutes. Just re-run the token request.

### CORS errors
Make sure User Service backend is running and CORS origins include `http://localhost:3000`.

---

## Next Steps

After User Service is complete:
1. Merge to main
2. Start Event Service (Sprint 2.1)
3. Implement frontend Events page
4. Continue with Group, Rating, Safety services

---

**Last Updated**: November 13, 2024
