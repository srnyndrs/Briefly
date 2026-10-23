# Public API

Provides Briefly's client-facing HTTP API and read models for article queries.

## Responsibilities

- Authenticate requests and enforce user and admin access rules.
- Forward account, source, and post operations to their owning services.
- Build read models from account, parsed-post, and enrichment events.
- Serve personalized feeds and Explore searches with filtering and pagination.

Uses PostgreSQL, RabbitMQ, and the account, crawler, and content services.

## Commands

Run from this service's directory:

- `make quickstart` — install dependencies.
- `make test` — run tests.
- `make lint` / `make format` — check lint and formatting.
- `make lint-fix` / `make format-fix` — apply fixes.
