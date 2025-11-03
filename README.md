# FastAPI Calculator (Module 9)

This repository contains a small FastAPI-based calculator application and a Docker Compose development stack (FastAPI app, PostgreSQL, and pgAdmin). It also includes the project's tests and supporting files.

What I added in this session
- `compose.yaml` — Docker Compose configuration defining three services: `app` (FastAPI), `db` (Postgres), and `pgadmin` (pgAdmin 4). The file uses an env file for secrets and named volumes for persistence.
- `.env` — local environment variables used by the Compose stack (DB credentials, pgAdmin credentials, etc.). Do NOT commit this file.
- `.env.example` — placeholder/example env file safe to commit.
- `.gitignore` — updated to ignore `.env` and common Python artifacts.
- `sql/` (optional) — you can create `sql/schema.sql` or `sql/seeds.sql` to store schema and seed data (recommended).

High-level overview
- FastAPI app: built from the repository `Dockerfile`, available on host port 8000 (mapped by Compose).
- PostgreSQL: Postgres 15 running in `postgres-db`, data persisted in a named Docker volume (`db_data`).
- pgAdmin: Web UI running in `pgadmin` and mapped to host port 5050 so you can open http://localhost:5050.

Environment files
- `.env` contains the runtime secrets/values used by Compose. Example variables:
	- POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
	- DATABASE_URL
	- PGADMIN_DEFAULT_EMAIL, PGADMIN_DEFAULT_PASSWORD
	- FASTAPI_HOST, FASTAPI_PORT
- Keep `.env` out of version control. Commit `.env.example` instead.

Basic commands
- Build and start the stack (detached):

```bash
docker compose up --build -d
```

- Stop the stack but keep volumes (safe):

```bash
docker compose down
```

- Stop the stack and remove volumes (destructive — deletes DB data):

```bash
docker compose down -v
```

- See running containers and port mappings:

```bash
docker ps
```

pgAdmin (web UI)
- Open: http://localhost:5050
- Default login comes from `.env` (PGADMIN_DEFAULT_EMAIL / PGADMIN_DEFAULT_PASSWORD). The admin account is created only on first initialization of the pgAdmin volume. Changing `.env` later will not overwrite an existing pgAdmin admin user unless you remove the `pgadmin` data volume and reinitialize.
- To add your Postgres server inside pgAdmin (from the pgAdmin UI):
	- Host: `db` (this resolves inside Docker; if connecting from your host, use `localhost`)
	- Port: `5432`
	- Username: `postgres` (or value from `.env`)
	- Password: value from `.env`

Working with the database (psql)
- Run SQL from a file:

```bash
docker exec -i postgres-db psql -U postgres -d calculator < sql/schema.sql
```

- Open an interactive psql shell:

```bash
docker exec -it postgres-db psql -U postgres -d calculator
```

- Export schema (schema-only SQL dump):

```bash
docker exec -t postgres-db pg_dump -U postgres -s calculator > sql/schema.sql
```

- Dump data backup:

```bash
docker exec -t postgres-db pg_dump -U postgres calculator > sql/calculator_dump.sql
```

Persistence and volumes
- The Postgres data is stored in a named Docker volume (declared in `compose.yaml` as `db_data`). Running `docker compose down` will not delete the volume by default. To destroy database data you must remove the volume explicitly or run `docker compose down -v`.

Troubleshooting notes from this session
- If Docker Desktop GUI doesn't open from WSL, start Docker Desktop from the Windows Start menu or system tray; WSL may not be able to launch the GUI directly.
- If you see extra unnamed containers (Docker gives random names such as `eager_jemison`), they are likely extra instances of the same image. Use `docker ps` and `docker inspect <name>` to inspect and `docker rm -f <name>` to remove if not needed.
- Browsing to http://localhost:5432 will not work — Postgres uses a binary protocol, not HTTP. Use pgAdmin or psql.

Git and remotes
- If `origin` already exists and you want to point this repository at a new remote, you can replace it:

```bash
git remote set-url origin git@github.com:youruser/your-new-repo.git
```

Or remove then add:

```bash
git remote remove origin
git remote add origin git@github.com:youruser/your-new-repo.git
```

Suggested next steps (optional)
- Commit `sql/schema.sql` and `sql/seeds.sql` into the repo so your schema and seed data are reproducible.
- Add Alembic migrations if your app uses SQLAlchemy and you expect schema changes.
- Create a small README section describing the DB schema (tables, relationships) for graders.

If you want, I can:
- Export the current schema to `sql/schema.sql` and add `sql/seeds.sql` with the current rows.
- Add a short section describing the tables and foreign key relationships discovered during this session.

----

Development quick start

1. Start stack:

```bash
docker compose up --build -d
```

2. Open app: http://localhost:8000
3. Open pgAdmin: http://localhost:5050 (login with `.env` credentials)
4. Connect to DB from pgAdmin using host `db` (or `localhost` from host)

Run tests locally:

```bash
pytest -q
```

License / notes
- This project is for educational purposes. Keep secrets out of source control and use stronger passwords for anything beyond local development.
