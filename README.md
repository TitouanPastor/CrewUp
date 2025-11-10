# CrewUp — Quick Development README

This repository contains a local development setup for CrewUp: a microservice-based event/group discovery app (React frontend + FastAPI microservices + PostgreSQL).

The README below includes a short Quickstart and troubleshooting tips so you or a teammate can run the stack locally.

Requirements
------------
- Docker and Docker Compose
- 4GB+ RAM available

Quickstart (2-minute run)
-------------------------
1. Build the containers (recommended):

```bash
./setup.sh
```

2. Start the stack:

```bash
docker-compose up
```

3. Open the frontend in your browser:

http://localhost:3000

Notes: the first build may take 5–10 minutes depending on your machine. Subsequent runs are much faster.

Services and ports
------------------
| Service    | Port  | URL                       |
|------------|-------|---------------------------|
| Frontend   | 3000  | http://localhost:3000     |
| Event API  | 8001  | http://localhost:8001     |
| Group API  | 8002  | http://localhost:8002     |
| Rating API | 8003  | http://localhost:8003     |
| Safety API | 8004  | http://localhost:8004     |
| User API   | 8005  | http://localhost:8005     |
| Postgres   | 5432  | localhost:5432            |

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

Quick troubleshooting
---------------------
- Frontend does not load:
	```bash
	docker logs crewup-frontend
	```
- A service fails to start:
	```bash
	docker-compose logs <service-name>
	```
- Port already used: edit `docker-compose.yaml` and change the host port (for example `3001:80`).
- Reset fully (including DB):
	```bash
	docker-compose down -v
	docker system prune -a
	./setup.sh
	docker-compose up
	```

Features to test
----------------
- Map interactive (click markers)
- Events list and detail view
- Create / Join group flows
- Group chat (simulated)
- Party mode (safety alert button)

Notes and limitations
---------------------
- Many parts are currently mocked; the frontend still uses mock data in several places.
- Authentication is mocked for local testing.
- The chat is simulated (no WebSocket broker yet).

Next steps (roadmap)
--------------------
1. Wire services to PostgreSQL with real CRUD endpoints.
2. Replace frontend mocks with real API calls.
3. Add WebSocket-based chat and a message broker.

Contributing
------------
- Create a branch, make changes, open a pull request describing the change.

Contact
-------
If you need help running the project, ping the maintainer.

---

Simple, focused, ready for local development.
