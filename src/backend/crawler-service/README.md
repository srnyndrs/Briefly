# Crawler Service (Feed Ingestion)

## Purpose
`crawler-service` manages global feed discovery, feed registration, ETag/Last-Modified caching, and periodic scheduled feed crawling via APScheduler. Sources/feeds are global resources.

## Port
`8001`

## Database Schema & Tables
- **Schema:** `crawler`
- **Tables:**
  - `feeds`: Registered RSS/Atom feed metadata, scheduled crawl times, failure counters, health scores.

## Events Produced
- `feed.raw_fetched.v1` (Exchange: `feed.content`)

## Testing
Run unit tests using Poetry:
```bash
poetry run pytest
```
