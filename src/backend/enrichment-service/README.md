# Enrichment Service

FastAPI service for classifying parsed posts through Ollama and storing results.
Running the service starts its durable parsed-post consumer. PostgreSQL,
RabbitMQ and an explicitly provisioned Ollama model are required.

## Local startup

From the repository root, start PostgreSQL, RabbitMQ and standalone Ollama:

```powershell
docker compose up -d postgres rabbitmq
docker compose --profile ollama up -d ollama
docker compose exec ollama ollama pull YOUR_CHOSEN_MODEL_TAG
docker compose exec ollama ollama list
```

Set `OLLAMA_MODEL` in this service's `.env` to the chosen installed tag, then
start the service from this directory:

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
`post.parsed.v1` on `content.parsed`. Startup composes the Ollama provider,
category callable, enrichment service and event processor using `SessionLocal`.
`PostEventProcessor` remains callable for isolated fixture runs.
Malformed and failed deliveries are dead-lettered
to `enrichment.posts.v1.dlq` through `enrichment.failed`.
Runtime requires `OLLAMA_MODEL`; there is no default model selection.
`OLLAMA_TIMEOUT_SECONDS` defaults to 60 and accepts values greater than zero
up to 300. `OLLAMA_BASE_URL` defaults to `http://localhost:11434`.
Gemini is constructed only by explicit evaluation and its key is optional.

Startup resolves the installed model digest from `/api/tags`. The bounded
`enrichment_version` hashes provider, model tag, digest, taxonomy, prompt,
schema, generation options and input policy. Unchanged input and version reuse
saved results; a changed model or policy triggers classification again.
Record `ollama list` and the `/api/tags` digest alongside experiments. Restart
enrichment after repulling a tag so its identity reflects the installed contents.
Changes to normalization must bump `INPUT_POLICY_VERSION`.

The consumer uses prefetch=1 with one active inference worker. Normalization,
inference and persistence run off the Pika connection thread. Publication,
confirms and ack/nack stay on that thread, with completion returned through
`add_callback_threadsafe`. The confirmed event is marked published off that
thread before the input is acknowledged. Sessions belong to individual repository
operations; no transaction is held across inference.

The service declares `enrichment.events` but creates no result sink queue.
Public-api owns the durable query queue and its `post.enriched.v1` binding.
Its projector validates the current collection payload; establish the durable
query binding before enabling enrichment consumption.
Missing routing or a publication failure leaves the saved event pending and
sends the input to the enrichment DLQ. Republish one saved event
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

Provider failure saves a revisioned failed result with empty categories and a
pending v1 event. That event must be confirmed and marked published before the
input is rejected to the DLQ. Intentional abstention is acknowledged normally.
Pending failed events retain their identity on redelivery without repeating the
model call. After publication, explicit replay can retry classification.
Logs include bounded provider error details or the exception type, without
logging article text or raw model output. There is no automatic model retry or
Gemini fallback.

Startup checks the installed model before consuming. If Ollama goes down during
processing, restore it and restart enrichment, then replay an explicit bounded
sample of failed posts using content-service's replay endpoint. Republish pending
events first if downstream routing was unavailable. Shutdown closes the consumer
connection and leaves unfinished input unacknowledged; it does not wait for an
inference worker. Late completions cannot use a closed or replaced connection.
Workers are daemon threads and model requests retain the configured timeout.
After a broker disconnect, finish the active worker before accepting redelivery.

Open `http://localhost:8005/health` for HTTP liveness. It does not check broker
connectivity or classification success.

## Container startup

The optional Compose profile is the feature switch. Container broker/model
configuration and combined Ollama profile wiring are pending Step 4 of the
[implementation plan](../../../MULTI_CATEGORY_ENRICHMENT_IMPLEMENTATION_PLAN.md).
Complete container wiring and integrated backend verification before processing a backlog.

## Focused validation

Run `make test`, `make lint` and `make format` for local checks. Broker tests are
opt-in through `ENRICHMENT_TEST_RABBITMQ_URL` (an AMQP URL without query parameters).
They create and remove isolated test queues/exchanges, use a two-second heartbeat
and fake inference, and verify slow processing, shutdown/redelivery and missing
routing recovery. Point them at a disposable local RabbitMQ instance.
They do not use the platform backlog or call Ollama.

## Compare classification providers (multi-category Phase 1)

Follow the [manual evaluation guide](EVALUATION_GUIDE.md) to build a small
labelled set, run bounded Gemini or Ollama calls, and compare the results.
`src.scripts.export_evaluation` samples stored posts read-only;
`src.scripts.label_evaluation` walks through the saved sample and resumes manual
labelling. The evaluator's `--validate-only` checks the dataset before model calls.
Use `make evaluate-help` for flags and `make evaluate` to run the
script. This command uses neither RabbitMQ nor the enrichment database.
