docker-compose up
docker-compose build
docker-compose up
docker-compose up -d
docker exec -it crewup-db psql -U crewup -d crewup
docker-compose logs -f
docker-compose logs -f user
docker-compose logs -f postgres
docker-compose restart user
docker-compose down
docker-compose down -v
docker-compose build user
docker-compose up -d user
docker-compose logs
docker ps -a
docker-compose ps
docker-compose logs postgres
# CrewUp — Quick Development README

This repository contains a local development setup for CrewUp: a microservice-based event/group discovery app (React frontend + FastAPI microservices + PostgreSQL).

This README is a concise guide for getting the project running locally.

Requirements
------------
- Docker and Docker Compose
- 4GB+ RAM available

Quick start
-----------
1. Build containers (recommended):

```bash
./setup.sh
```

2. Start the stack:

```bash
docker-compose up
```

3. Open the frontend:

http://localhost:3000

Services and ports
------------------
- Frontend: http://localhost:3000
- Event API: http://localhost:8001
- Group API: http://localhost:8002
- Rating API: http://localhost:8003
- Safety API: http://localhost:8004
- User API: http://localhost:8005
- PostgreSQL: localhost:5432

Useful commands
---------------
- Tail logs: `docker-compose logs -f`
- Start detached: `docker-compose up -d`
- Stop: `docker-compose down`
- Remove volumes (reset DB): `docker-compose down -v`
- Rebuild: `docker-compose build`

Database
--------
The PostgreSQL container initializes with `database/schema.sql` on first run. To connect:

```bash
docker exec -it crewup-db psql -U crewup -d crewup
```

Notes and limitations
---------------------
- Many parts are currently mocked. The frontend still uses mock data in several places.
- Authentication is mocked.
- The chat is simulated (no WebSocket broker yet).

Next steps
----------
1. Wire services to PostgreSQL with real CRUD endpoints.
2. Replace frontend mocks with real API calls.
3. Add WebSocket-based chat and message broker.

Contributing
------------
- Create a branch, make changes, open a pull request describing the change.

Contact
-------
If you need help running the project, ping the maintainer.

---

Simple, focused, ready for local development.
