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

Startup creates missing tables from the current SQLAlchemy models. During
development, apply schema changes directly or recreate the affected disposable
tables after stopping their consumers. `create_all()` does not alter existing
tables. Keep schema maintenance scoped to the affected service.

The RabbitMQ consumer queue is `enrichment.posts.v1`, bound to
`post.parsed.v1` on `content.parsed`. Consumption remains off unless
`POST_CONSUMER_ENABLED=true` and a classifier-backed `post_event_processor` is
configured on `app.state` before startup. The `PostEventProcessor` object is
callable and can be used for isolated fixture runs. Enabling consumption without
one now fails startup clearly. Malformed and failed deliveries are dead-lettered
to `enrichment.posts.v1.dlq` through `enrichment.failed`.
When production provider composition is added, pass an `enrichment_version`
that identifies its provider, model, prompt, taxonomy and bounded input policy.
The default version is for the current injected classifier seam.

When enabled, the consumer creates a durable `enrichment.results.v1` sink on
`enrichment.events` before reading parsed posts. It saves each `post.enriched.v2`
event with its result, publishes with mandatory routing and confirms, then
acknowledges the incoming delivery. A publication failure leaves the event
pending and sends the input to the enrichment DLQ. Republish one saved event
without classification using:

```powershell
poetry run python -m src.scripts.republish_result <post-uuid>
```

The command can also republish an already delivered result with the same event
ID. Downstream consumers must deduplicate that ID. To populate results for
existing articles, first establish the result binding, then call content-service's
bounded `/admin/posts/replay?limit=...` endpoint. The replayed post keeps its
stored revision. A crash after a classifier call but before the result save can
repeat the call; this flow does not guarantee exactly-once classification.

Open `http://localhost:8005/health` to check that the service is running.

## Container startup

From the repository root, run:

```powershell
docker compose --profile enrichment up --build enrichment-service
```

The service listens on port 8005 and waits for PostgreSQL to become healthy.

## Compare classification providers (multi-category Phase 1)

Follow the [manual evaluation guide](EVALUATION_GUIDE.md) to build a small
labelled set, run bounded Gemini or Ollama calls, and compare the results.
Use `make evaluate-help` for flags and `make evaluate` to run the
script. This command uses neither RabbitMQ nor the enrichment database.
