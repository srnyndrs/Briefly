# Content Service

## Role

The content service turns fetched feed data into readable, stored posts for
Briefly. It enriches feed entries when article pages are available and makes
processed posts available to downstream services and internal API consumers.

## Responsibilities

- Consume fetched feed content.
- Parse feed entries into normalized posts.
- Enrich posts from linked article pages when possible.
- Store processed posts.
- Publish processed post content for downstream services.
- Provide internal post reads and replay operations.

## Does not own

- Feed discovery or scheduled feed fetching.
- Feed source registration.
- User accounts or authentication.
- Personalized feed ranking or recommendations.

## Integration

The service receives fetched feed content from the crawler service. It uses
PostgreSQL to store posts, accesses publisher websites for optional content
extraction, and sends processed posts to the public API's read model.

The service also exposes HTTP endpoints for health checks, internal post reads,
and replay operations. When it is running, use `/docs` for the current API
documentation.

## Article extraction

Stored posts with the same source, item identity and URL reuse their extraction
results. RSS metadata updates still propagate. New items and changed URLs make
one extraction attempt; failures preserve useful stored fields and RSS metadata.
Partial results are also reused on subsequent crawls.

`ARTICLE_REQUEST_TIMEOUT_SECONDS` sets the article HTTP request timeout
(default: 5 seconds; must be positive and finite). It limits socket waits, not
total parsing time or response size. Extraction retains RSS and HTML metadata
image URLs without downloading images for validation. A small Article override
also skips newspaper4k's fallback image selection, which can otherwise download
images even with `fetch_images=False`.

Article links must be HTTP(S) URLs with a host and no credentials. Surrounding
whitespace is trimmed; query strings and URL punctuation are preserved. Invalid
links make no request and produce RSS-based posts with an empty URL. This check
does not restrict destinations or provide full SSRF protection.

Logs report article host, extraction outcome (`success`, `empty`, `failed`) and
duration. A feed summary reports event/source/correlation IDs, age at processing
start, total duration, entry count, attempted extractions, reused results,
partial results. `partial` counts entries with missing
content, an invalid/missing link, or a failed extraction even if stored content
was retained. `completed` means the processing loop returned normally; it is
not a broker acknowledgement or proof of downstream projection. Application
logs omit query values and raw exception/HTML responses; newspaper's own logs
are controlled separately.

## Post revisions and replay

Each stored post has a monotonic `post_revision`. A new post starts at revision 1.
An existing post advances once when a canonical merged article field changes:
URL, source title, title, description, RSS category, content, author, publication
time, image URL, language or keywords. Equality uses the normalized values
produced by the current feed and extraction rules.

A repeated feed observation that leaves those fields unchanged returns and
republishes the stored snapshot at its existing revision. It does not update
`crawled_at` or `parsed_at`; those timestamps describe the saved snapshot. A
meaningful change updates the snapshot timestamps and revision. Extraction reuse
for the same source, item identity and URL remains in effect.

Posts are committed before their broker publication. If publication fails after
a commit, replaying the feed or using post replay publishes the saved snapshot
again with its stored revision. Duplicate events are expected; publisher confirms
show broker acceptance and do not make the database write and publication atomic.
The admin post replay endpoint republishes stored revisions without fetching
article pages.

## Feed failures and RabbitMQ

Expected article extraction failures still save and publish RSS-based posts.
Invalid feed events and unexpected processing, database or publication failures
reject the original feed to `feed.raw_fetched.v1.parser.dlq`. No automatic retry
is configured. A lost connection leaves unacknowledged feeds for broker redelivery.

The consumer acknowledges a feed only after saving and publishing every entry.
Publications use publisher confirms and mandatory routing, including the existing
post replay endpoint. A queue must bind `post.parsed.v1` on `content.parsed`
before processing starts. Confirms establish broker acceptance, not downstream
processing or atomicity with the database. Replaying a partially processed feed
reuses stored extraction and publishes snapshots again.

Prefetch is 1. The consumer services RabbitMQ I/O between entries on its own
thread. `RABBITMQ_BLOCKED_TIMEOUT_SECONDS` defaults to 15 seconds and must be
positive and finite. Heartbeats remain enabled. One long download, parse or
database operation can still prevent timely heartbeat handling.

### DLQ setup

The root Compose configuration builds the RabbitMQ image from
`scripts/rabbitmq/Dockerfile`, which includes the definitions and broker
configuration. RabbitMQ imports the definitions on startup on Windows and Unix
hosts. They create the durable `content.failed` exchange, the DLQ and its binding,
and a policy that routes
rejected feeds from `feed.raw_fetched.v1.parser` to that DLQ. No host script is
needed. The definitions also seed the local Compose `guest` account and `/`
vhost on a fresh RabbitMQ volume; they are local development credentials.
On a fresh checkout, `docker compose up -d --build` starts this setup.

For an existing Compose broker, rebuild and recreate its container once without
removing its named volume:

```bash
docker compose build rabbitmq
docker compose up -d --no-deps --force-recreate rabbitmq
```

The import adds missing definitions without clearing queued messages. The
consumer's queue declarations keep their existing arguments; changing those
arguments would require a queue migration. If the queue names, exchanges or
vhost change, update the definitions and service settings together.

### Inspect and recover

Use the RabbitMQ management UI at `http://localhost:15672`, or run from the
repository root:

```powershell
docker compose exec -T rabbitmq rabbitmqctl list_queues -p / name policy messages_ready messages_unacknowledged consumers
docker compose exec -T rabbitmq rabbitmqctl list_policies -p /
docker compose logs --since 10m content-service
```

Check ready/unacknowledged counts, consumer count, DLQ depth, feed durations,
`attempted` versus `reused`, event age and reconnect/error logs. HTTP health
checks alone do not establish consumer health. Observe actual source crawl
intervals; the one-minute scheduler check is not the source crawl interval.

For a failed feed, inspect the DLQ's next message using **Get messages** with
**Nack message requeue true**. Inspect its `event_id`, source/correlation IDs
and `x-death` headers; do not purge the queue. Fix the cause first. Then replay
that one event from the repository root:

```powershell
docker compose exec -T content-service python -m src.scripts.replay_failed_feed 'EVENT_ID'
```

The command requires the next DLQ message to match that ID and to be a raw-feed
event. It preserves the original body, correlation ID and message properties,
confirms mandatory publication to the feed exchange, then acknowledges the DLQ
delivery. A mismatch, malformed message or publish failure leaves it retained.
Replace `EVENT_ID` with the inspected event ID.
It does not search or drain the queue. A crash between publication and DLQ
acknowledgement can produce duplicate delivery; processing remains an upsert
and snapshot replay. Invalid JSON or invalid event types require inspection and
manual correction before publication; the command deliberately refuses them.

To refresh a stored post's body after a blocked site recovers, or after an edit
at an unchanged URL:

```powershell
docker compose exec -T content-service python -m src.scripts.reextract_post 'POST_ID'
```

Replace `POST_ID` with the actual stored ID. The command makes one explicit
extraction attempt and updates only the body and `parsed_at`, preserving stored
metadata and post identity. An extraction failure
or empty body leaves the stored post unchanged and exits unsuccessfully. A
publication failure also exits unsuccessfully, but the updated body may already
be committed. Republish that saved snapshot through the existing admin replay
endpoint after restoring the broker/binding; no further extraction is needed.
Use the command while that post is not undergoing another update.

`POST /admin/posts/replay?since=<ISO-timestamp>&limit=500` republishes stored
snapshots in ascending `parsed_at` order, without fetching article pages. Limit
is 1–5000. Supply `x-admin-token` when `ADMIN_TOKEN` is configured. This endpoint
does not consume the DLQ. Feed replay and post replay serve different recovery
cases; neither is automatic.

### Rollout

With PostgreSQL, RabbitMQ and the public API running, ensure RabbitMQ has
started with the definitions and verify the downstream
`post.parsed.v1` binding. Then rebuild only this service:

```bash
docker compose build content-service
docker compose up -d --no-deps --wait content-service
```

Preserve PostgreSQL/RabbitMQ volumes. Compare a warm feed with one containing
new items over at least three real source crawl cycles. A warm feed should show
`attempted=0`; new items still incur extraction time. If the backlog continues
growing, measure that remaining cost before adding workers. Concurrent replicas
can still race to extract the same unseen item or overwrite same-source updates.
Kubernetes can host additional consumers, but does not remove these costs.

## Development

Install dependencies:

```bash
poetry install
```

Run the service locally:

```bash
poetry run uvicorn src.app:app --reload
```

Run tests and lint checks:

```bash
poetry run python -m pytest -p no:cacheprovider -q
poetry run ruff check --no-cache src tests
poetry run ruff format --check src tests
```

Broker integration checks use a disposable Compose project. From the repository
root, start RabbitMQ and PostgreSQL with:

```powershell
docker compose -p briefly-content-check -f scripts/rabbitmq/compose.test.yml up -d --wait
```

Then, from this service directory:

```powershell
$env:RUN_RABBITMQ_INTEGRATION = '1'
$env:RUN_POSTGRES_INTEGRATION = '1'
poetry run python -m pytest -p no:cacheprovider -q tests/test_rabbitmq_integration.py tests/test_postgres_integration.py
Remove-Item Env:RUN_RABBITMQ_INTEGRATION
Remove-Item Env:RUN_POSTGRES_INTEGRATION
```

These checks import policies and purge queues on the disposable broker at ports
5673/15673. They use SQLite and mocked article extraction. Do not point them at
the application broker. The separate PostgreSQL check uses the disposable
`content_check` database at port 5433 to verify real commits, upsert identity,
metadata updates and preservation after failed extraction. Neither uses the
application database or publisher websites. Afterward, from the repository root:

```powershell
docker compose -p briefly-content-check -f scripts/rabbitmq/compose.test.yml down --volumes
```
