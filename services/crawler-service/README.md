# Crawler Service

Maintains Briefly's feed-source catalog and fetches fresh RSS/Atom content.

## Responsibilities

- Discover feeds from website or feed URLs.
- Register sources and manage their metadata and verification status.
- Schedule feed fetching with conditional requests and failure backoff.
- Publish fetched feed content for content-service.

Uses PostgreSQL for source state and RabbitMQ for feed events.

## Commands

Run from this service's directory:

- `make quickstart` — install dependencies.
- `make test` — run tests.
- `make lint` / `make format` — check lint and formatting.
- `make lint-fix` / `make format-fix` — apply fixes.
- `make seed-sources` — load curated sources.
- `make check-feed URL="https://example.com/feed"` — inspect a feed.
