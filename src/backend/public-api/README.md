# Public API

## Role

The public API is Briefly's client-facing entry point. It authenticates
requests, coordinates access to the internal services, and provides fast feed
queries for users.

It also maintains local read models from account and content changes. This
keeps common feed queries fast while allowing the owning services to remain
responsible for their own data.

## Responsibilities

- Authenticate requests and enforce client-facing access rules.
- Provide the public HTTP API for accounts, sources, posts, and feeds.
- Forward commands and immediate reads to the service that owns the data.
- Build local read models from selected asynchronous events.
- Apply feed filtering, personalization, and ranking to read-model data.

## Does not own

- User accounts, credentials, or subscriptions.
- Feed discovery, source scheduling, or feed fetching.
- Canonical post storage or article processing.

Account-service, crawler-service, and content-service remain the authoritative
owners of those domains. Public-api provides access to them and stores only
the read-side data needed for fast queries.

## Integration

Client applications call public-api over HTTP. The service communicates with
the account, crawler, and content services for operations that belong to
those services. It also consumes selected RabbitMQ events and stores local
query data in PostgreSQL.

Read models are updated asynchronously, so a recent account or content change
may become visible to feed queries shortly after the original operation.

The current public API is available through FastAPI's `/docs` endpoint when
the service is running.

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
poetry run pytest -p no:cacheprovider -q
poetry run ruff check --no-cache src tests
poetry run ruff format --check src tests
```
