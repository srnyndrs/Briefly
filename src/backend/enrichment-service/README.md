# Enrichment Service

FastAPI service for storing post enrichment results. PostgreSQL is required for
startup and persistence. The durable parsed-post consumer is disabled by
default and requires an injected classifier before it can start.

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

Step 4b adds `post_revision` to the existing enrichment table. Apply this
one-time update to a database created before the field was added; fresh
databases get the column from SQLAlchemy table creation:

```sql
ALTER TABLE enrichment.post_enrichments
ADD COLUMN IF NOT EXISTS post_revision INTEGER NOT NULL DEFAULT 1;
```

The RabbitMQ consumer queue is `enrichment.posts.v1`, bound to
`post.parsed.v1` on `content.parsed`. Consumption remains off unless
`POST_CONSUMER_ENABLED=true` and a classifier-backed `post_event_processor` is
configured on `app.state` before startup. The `PostEventProcessor` object is
callable and can be used for isolated fixture runs. Enabling consumption without
one now fails startup clearly. Malformed and failed deliveries are dead-lettered
to `enrichment.posts.v1.dlq` through `enrichment.failed`.

Open `http://localhost:8005/health` to check that the service is running.

## Container startup

From the repository root, run:

```powershell
docker compose --profile enrichment up --build enrichment-service
```

The service listens on port 8005 and waits for PostgreSQL to become healthy.
