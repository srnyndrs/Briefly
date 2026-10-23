# Content Service

Turns fetched RSS/Atom feeds into normalized, stored articles.

## Responsibilities

- Consume raw feed events from crawler-service.
- Parse entries and extract article content from publisher websites.
- Store canonical posts and publish parsed-post events.
- Provide internal post reads and explicit replay operations.

Uses PostgreSQL and RabbitMQ; parsed posts feed public-api and enrichment-service.

## Commands

Run from this service's directory:

- `make quickstart` — install dependencies.
- `make test` — run tests.
- `make lint` / `make format` — check lint and formatting.
- `make lint-fix` / `make format-fix` — apply fixes.
