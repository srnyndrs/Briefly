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
