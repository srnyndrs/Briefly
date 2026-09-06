# Public API (Gateway & CQRS Read Side)

## Purpose
`public-api` acts as the primary API Gateway and CQRS read model layer. It handles client JWT validation, proxies pass-through writes to internal microservices, projects async RabbitMQ events into read models, and executes fast personalized feed queries (category array overlap, ranking, search).

## Port
`8000`

## Database Schema & Tables
- **Schema:** `query`
- **Tables:**
  - `post_projections`: Projected post read models with `ARRAY(Text)` GIN indexes.
  - `user_preferences_projections`: Projected user category/language preferences and blocklists.
  - `processed_events`: Idempotency tracking table for event processing.

## Events Consumed
- `post.parsed.v1`
- `preferences.updated.v1`
(Queue: `public-api.query.v1`)

## Development schema reset

`create_all()` creates missing tables but does not remove tables deleted by a
refactor. After pulling the removal of `user_subscription_projections`, reset
the local development database before starting the platform again:

```powershell
docker compose down --volumes --remove-orphans
docker compose up --build
```

This deletes local Docker volumes, including development data. Do not run it
against data you need to keep.

## Testing
Run unit tests using Poetry:
```bash
poetry run pytest
```
