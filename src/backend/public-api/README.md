# Public API (Gateway & CQRS Read Side)

## Purpose
`public-api` acts as the primary API Gateway and CQRS read model layer. It handles client JWT validation, proxies pass-through writes to internal microservices, projects async RabbitMQ events into read models, and executes fast personalized feed queries (category array overlap, ranking, search).

## Port
`8000`

## Database Schema & Tables
- **Schema:** `query`
- **Tables:**
  - `article_projections`: Projected article read models with `ARRAY(Text)` GIN indexes.
  - `user_preferences_projections`: Projected user category/language preferences and blocklists.
  - `user_subscription_projections`: Projected user source subscriptions.
  - `processed_events`: Idempotency tracking table for event processing.

## Events Consumed
- `article.parsed.v1`
- `preferences.updated.v1`
- `subscription.created.v1`
- `subscription.deleted.v1`
(Queue: `public-api.query.v1`)

## Testing
Run unit tests using Poetry:
```bash
poetry run pytest
```
