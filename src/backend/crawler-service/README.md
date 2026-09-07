# Crawler Service

## Role

The crawler service keeps Briefly's catalog of feed sources current and
delivers fresh feed content to downstream services. This lets Briefly collect
news from external publishers without coupling feed fetching to post
processing.

## Responsibilities

- Discover feed URLs from websites.
- Register and manage feed sources.
- Fetch registered feeds on a schedule.
- Hand fetched content to the content service for processing.

## Does not own

- Article parsing or post storage.
- User accounts or authentication.
- Personalized feeds or recommendations.

## Integration

The service receives website and feed URLs through its HTTP API. It uses
PostgreSQL for source state and RabbitMQ to deliver fetched feed content to
the content service.

The service exposes endpoints for source discovery, source management, and
health checks. When it is running, use `/docs` for the current API
documentation.

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
```
