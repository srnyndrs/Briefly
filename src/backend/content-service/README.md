# Content Service

## Purpose
`content-service` consumes raw fetched feed events (`feed.raw_fetched.v1`), parses RSS/Atom XML payloads, extracts article content, stores articles in PostgreSQL, and emits parsed article events. It also provides an admin replay endpoint for backfilling projections via event streams.

## Port
`8002`

## Database Schema & Tables
- **Schema:** `content`
- **Tables:**
  - `articles`: Stored articles with extracted full text, metadata, keywords, categories, and timestamps.

## Events Consumed
- `feed.raw_fetched.v1` (Queue: `feed.raw_fetched.v1.parser`)

## Events Produced
- `article.parsed.v1` (Exchange: `content.parsed`)

## Admin Endpoints
- `POST /admin/articles/replay`: Streams replayed `article.parsed.v1` events with correlation ID `replay-<uuid>` to re-derive projections. Protected by optional `x-admin-token` header.

## Testing
Run unit tests using Poetry:
```bash
poetry run pytest
```
