# Enrichment Service

Optional Ollama classification of parsed posts. Core ingestion and article reads
work without it. Gemini is available only through the explicit evaluation CLI.

## Startup and configuration

From the repository root, start the core platform:

```powershell
docker compose up -d --build
```

Compose defines `OLLAMA_MODEL` once as `qwen2.5:3b` via a YAML extension field
(`x-ollama-model`) and shares it between the `ollama` and `enrichment-service`
containers using a YAML anchor. Change that single value in `docker-compose.yml`
to select another model. `config/ollama/Dockerfile` downloads it during the image
build into `/opt/ollama/models`. Runtime uses the standard Ollama server command;
no model download or initialization container is needed. Enrichment waits for
the model health check. The first build downloads the model; subsequent builds
reuse Docker's cache. Changing the model requires rebuilding the Ollama image.

For Kubernetes, publish the built image and deploy it with the matching model
name supplied to Ollama and enrichment through a shared ConfigMap. Do not mount
a volume over `/opt/ollama/models`. The previous `ollama_data` volume is no longer
used; existing local model files are not deleted.

Ollama runs on the CPU. The `ollama` profile supports standalone experiments.

Enable or stop enrichment from the repository root:

```powershell
docker compose --profile enrichment up -d --build
docker compose stop enrichment-service ollama
```

The enrichment profile starts Ollama and enrichment alongside
the core services. Enrichment also waits for PostgreSQL, RabbitMQ, Ollama and
public-api health checks.
Core services have no optional-service dependency and require no Gemini key.
Plain `up` does not stop optional containers already running. Use the named `stop`
command to disable enrichment; profile `down` also stops core services.

| Setting | Runtime use |
| --- | --- |
| `OLLAMA_MODEL` | Compose selects `qwen2.5:3b`; required explicitly for host development. |
| `OLLAMA_TIMEOUT_SECONDS` | Request timeout greater than zero and at most 300 seconds; default 60. |
| `OLLAMA_BASE_URL` | Local default `http://localhost:11434`; Compose uses `http://ollama:11434`. |
| `DATABASE_URL` | Service PostgreSQL connection; Compose uses internal database DNS. |
| `RABBITMQ_URL` | Broker connection; Compose uses internal broker DNS. |
| `GEMINI_API_KEY` | Optional, explicit Gemini evaluation only. |

Compose overrides internal URLs and model selection, and loads other settings from the optional service
`.env`. Runtime uses the existing non-root `appuser` image and standard logs.
For host development, start core and Ollama first, then run from this directory:

```powershell
poetry install
poetry run uvicorn src.app:app --host 0.0.0.0 --port 8005 --reload
```

Startup checks the installed model digest before starting the consumer. Missing
configuration or model fails startup clearly. Ollama's container health check
runs `ollama list` to check server availability; it does not approve a model's
quality or confirm that your chosen tag exists. `/health` on port 8005 reports
HTTP liveness, not broker readiness or successful classification. Confirm the
consumer-start log and broker binding before processing a backlog.

## Contracts and persistence

Content owns text and `post_revision`. Enrichment consumes `post.parsed.v1` from
`content.parsed` through durable `enrichment.posts.v1`, and publishes
`post.enriched.v1` with `schema_version=1` and `category_ids`. Completed results
contain one or two distinct supported IDs; `other` stands alone. Intentional
abstention and failed results have empty categories and different statuses.
Public-api owns the durable `public-api.query.v1` binding on `enrichment.events`.
It exposes calculated `categories` as a list and keeps publisher labels separate.

Startup composes Ollama, the category callable, EnrichmentService and
PostProcessor with EnrichmentRepository(SessionLocal). The bounded result
version hashes provider, tag/digest, taxonomy, prompt, schema, generation options
and input policy. Unchanged input/version reuses saved results. Record the model
digest alongside experiments, restart after a repull, and bump
`INPUT_POLICY_VERSION` when changing normalization.

Startup creates missing tables. `create_all()` does not alter existing columns;
apply development schema changes directly with consumers stopped and scope them
to this service's derived tables.

## Queue behavior and recovery

Before the input binding exists, old posts require explicit bounded content replay
through content-service's `POST /admin/posts/replay?since=<timestamp>&limit=...`
(include `x-admin-token` if configured). Once the durable queue
exists, stopping enrichment leaves a backlog that resumes on restart. Disabling
the profile preserves valid saved categories. There is no automatic full-history
backfill, queue purge, TTL or scheduler.

The consumer uses prefetch=1 and one active inference worker. Model work and scoped
database operations run off the broker thread; publication/confirms and ack/nack
stay on it. No transaction spans inference. It confirms publication, marks the
saved event published, then acknowledges input. Failed classification publishes
its revisioned empty result before rejecting input to `enrichment.posts.v1.dlq`.
Malformed input also enters that DLQ. No automatic model retry or Gemini fallback
runs. Safe bounded provider details or exception types appear in logs.

Missing result routing or failed publication leaves the event pending. Restore the
binding, then republish the saved event without classification:

```powershell
poetry run python -m src.scripts.republish_result <post-uuid>
# Or from the repository root:
docker compose exec enrichment-service python -m src.scripts.republish_result <post-uuid>
```

Republishing retains the event ID; downstream consumers deduplicate it. Pending
failed events also retain identity on redelivery. After publication, explicit
bounded replay may retry classification. If Ollama fails during processing,
restore it, restart enrichment and replay the selected failed posts. Recovery can
repeat a call after a crash before persistence; there is no exactly-once claim.

Shutdown closes the broker connection without waiting for daemon inference
workers. Unfinished input can be redelivered; late completions cannot touch a
closed/replaced connection. After a broker disconnect, finish active work before
accepting redelivery. Model calls retain their configured timeout.

During trials, inspect ready/unacknowledged counts, consumer counts and broker disk
use. Measure backlog growth before choosing a bound:

```powershell
docker compose exec rabbitmq rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers
docker compose exec rabbitmq sh -c 'du -sh /var/lib/rabbitmq'
```
