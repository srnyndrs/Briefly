# Enrichment Service

FastAPI service for storing post enrichment results. PostgreSQL is required for
startup and persistence; RabbitMQ, credentials, and a model provider are not
required yet.

## Local startup

From the repository root, start PostgreSQL:

```powershell
docker compose up -d postgres
```

Then, from this service directory, start the API:

```powershell
poetry install
poetry run uvicorn src.app:app --host 0.0.0.0 --port 8005 --reload
```

The default database URL targets the repository's local PostgreSQL container.
Set `DATABASE_URL` in `.env` to use another PostgreSQL instance.

Open `http://localhost:8005/health` to check that the service is running.

## Container startup

From the repository root, run:

```powershell
docker compose --profile enrichment up --build enrichment-service
```

The service listens on port 8005 and waits for PostgreSQL to become healthy.
