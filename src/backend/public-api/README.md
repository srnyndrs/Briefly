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
- Apply feed filtering and chronological ordering to read-model data.

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

`GET /feed` returns the newest eligible posts from the caller's subscribed
sources, subject to saved languages and visibility exclusions. `GET /explore`
returns global posts with explicit category, language, source, date, and
optional full-text search filters; it applies the same visibility exclusions
without applying saved languages or subscriptions. `source_ids` is repeatable,
and `query` searches projected title, description, and keywords (not full
content). Title matches rank ahead of description matches, which rank ahead of
keyword-only matches. Search uses web-style syntax, has no prefix/autocomplete
matching, and relevance ordering means `sort` cannot be combined with `query`.
Both routes
support page-number pagination. Explore also supports an opt-in
`include_filter_options=true` response field for available categories,
languages, authors, and keywords; Explore additionally returns source options.

For example:

```text
/explore?source_ids=...&source_ids=...&query=%22climate+change%22&include_filter_options=true
```

The disposable PostgreSQL search-index and query-plan verification is a
deployment validation step; it must be rerun after rebuilding the local schema.

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
