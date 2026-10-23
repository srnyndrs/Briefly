# Enrichment Service

Adds optional AI category classification to parsed posts using Ollama.
Core ingestion and article reads work without it.

## Responsibilities

- Consume parsed-post events from content-service.
- Classify articles against the supported category taxonomy.
- Store reusable, versioned results and publish enrichment events for public-api.

Uses PostgreSQL, RabbitMQ, and Ollama. Local port: **8005**.
Liveness endpoint: [/health](http://localhost:8005/health).

## Commands

Run from this service's directory:

- `make quickstart` — install dependencies.
- `make test` — run tests.
- `make lint` / `make format` — check lint and formatting.
- `make lint-fix` / `make format-fix` — apply fixes.
