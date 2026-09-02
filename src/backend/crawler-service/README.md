# Crawler Service (Feed Ingestion)

## Purpose
`crawler-service` manages global feed discovery, feed registration, and periodic scheduled feed crawling via APScheduler. PostgreSQL's `crawler.sources` table is the durable source of truth for crawl scheduling and ETag/Last-Modified validators. Sources/feeds are global resources.

## Port
`8001`

## Database Schema & Tables
- **Schema:** `crawler`
- **Tables:**
  - `crawler.sources`: Registered RSS/Atom feed metadata, scheduled crawl times, failure counters, retry backoff state.

## Events Produced
- `feed.raw_fetched.v1` (Exchange: `feed.content`)

## Testing
Run unit tests using Poetry:
```bash
poetry run pytest
```
