# Content Service

`content-service` consumes fetched RSS/Atom feeds, turns their entries into
posts, stores them in PostgreSQL, and publishes parsed-post events for the
public API projection.

## Runtime

- **Port:** `8002`
- **PostgreSQL table:** `content.posts`
- **Consumes:** `feed.raw_fetched.v1` from `feed.content` through the durable
  `feed.raw_fetched.v1.parser` queue
- **Publishes:** `post.parsed.v1` to `content.parsed`

The service persists `source_title` with each post. Its one post identity is
`(source_id, item_guid)`; a later feed item with the same identity updates the
stored URL and metadata.

## HTTP API

- `GET /health`
- `GET /posts/count`
- `GET /posts`
- `GET /posts/{post_id}`
- `POST /admin/posts/replay`

When `ADMIN_TOKEN` is configured, replay requires the matching
`x-admin-token` header. Replay republishes stored `post.parsed.v1` events for
rebuilding the public API projection.

## Development

```bash
poetry install
poetry run python -m pytest -p no:cacheprovider -q
poetry run ruff check --no-cache src tests
```

Read [DESIGN.md](DESIGN.md) for the architecture, event contracts, and a
recommended code-reading order.
