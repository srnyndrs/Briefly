# Public API

## Role

The public API is Briefly's client-facing entry point. It authenticates
requests, coordinates access to the internal services, and provides fast feed
queries for users.

It also maintains local read models from account and content changes. This
keeps common feed queries fast while allowing the owning services to remain
responsible for their own data.

The query projector consumes `post.enriched.v1` with `schema_version=1` and the
current `category_ids` payload. It validates distinct supported IDs (zero to two),
standalone `other`, result status and positive article/enrichment revisions.
The publisher's label stays in `source_category`; public `categories` is always
a list. Missing, stale, abstained and failed enrichment gives `[]`.
Results may precede their article without creating an empty article. Only matching
post revisions apply, ordered by `enrichment_revision` within that revision.
Article updates clear old categories; enrichment never changes feed timestamps.

Category selections match any assigned category, and muting any assigned category
hides the article. Filters return each article once with stable pagination.
Category options count each eligible article once per category and preserve the
existing source, language, keyword, date and headline eligibility rules.

## Responsibilities

- Authenticate requests and enforce client-facing access rules.
- Provide the public HTTP API for accounts, sources, posts, and feeds.
- Forward commands and immediate reads to the service that owns the data.
- Build local read models from selected asynchronous events.
- Apply feed filtering and chronological ordering to read-model data.

## Does not own

- User accounts, credentials, or subscriptions.
- Feed discovery, source scheduling, or feed fetching.
- Canonical post storage or article processing.

Account-service, crawler-service, and content-service remain the authoritative
owners of those domains. Public-api provides access to them and stores only
the read-side data needed for fast queries.

## Integration

Client applications call public-api over HTTP. The service communicates with
the account, crawler, and content services for operations that belong to
those services. It also consumes selected RabbitMQ events and stores local
query data in PostgreSQL.

Read models are updated asynchronously, so a recent account or content change
may become visible to feed queries shortly after the original operation.

The current public API is available through FastAPI's `/docs` endpoint when
the service is running.

`GET /feed` returns the newest eligible posts from the caller's subscribed
sources, subject to saved languages and visibility exclusions. `GET /explore`
returns posts from verified Sources only, with explicit category, language,
source, date, and optional full-text search filters; it applies the same
visibility exclusions without applying saved languages or subscriptions.
Before each Explore query, public-api fetches current verified Source IDs from
crawler-service and applies them as a hard allowlist to items, totals, and
filter options. Repeatable `source_ids` selections intersect that allowlist;
they cannot expose unverified Sources. An empty verified catalog returns an
empty result and empty filter options. Personal `/feed` remains subscription-based
and may include posts from unverified Sources. `source_ids` is repeatable,
and `query` searches projected title, description, and keywords (not full
content). Title matches rank ahead of description matches, which rank ahead of
keyword-only matches. Search uses web-style syntax, has no prefix/autocomplete
matching, and relevance ordering means `sort` cannot be combined with `query`.
Both routes
support page-number pagination. Explore also supports an opt-in
`include_filter_options=true` response field for available categories,
languages, authors, and keywords; Explore additionally returns source options.

Source creation is a synchronous gateway operation. `POST /sources` accepts a
feed URL and optional display metadata; public-api derives the submitter ID
from the authenticated user. The client cannot set `verified` or submitter ID.
Crawler-service validates fields without fetching the feed again, and
user-created Sources are unverified. `POST /sources/discover` returns only
validated direct or explicitly advertised feed candidates. Overall and
category feeds can coexist; if they contain the same article, each feed keeps
its own projected post.

Admins use `PATCH /sources/{source_id}` to update metadata and set or clear
Explore verification. The gateway requires an admin-scoped access token;
Source creation remains available to authenticated users and always creates
unverified Sources. `GET /admin/feed` lists projected posts across all Sources,
and `GET /admin/posts/{post_id}` returns canonical post details. Source delete
and separate admin post list/count routes are not exposed by the gateway.

For example:

```text
/explore?source_ids=...&source_ids=...&query=%22climate+change%22&include_filter_options=true
```

The disposable PostgreSQL search-index and query-plan verification is a
deployment validation step; it must be rerun after rebuilding the local schema.

## Testing approach

The default suite runs locally without Docker. HTTP tests use FastAPI's
`TestClient`, an in-memory SQLite database for query projections, and small
stand-ins for calls to the owning services. Repository tests check feed query
rules against stored posts. Projection tests check the two event snapshots;
the projector test checks duplicate delivery acknowledgement.

Add a test for an observable route, query, or event contract when behavior
changes. Prefer one representative workflow per responsibility over separate
tests for every input variant or internal helper call. Keep PostgreSQL and
RabbitMQ smoke checks separate from the fast default suite.

## Development

For an existing development database, remove the URL uniqueness constraint
before processing overlapping feeds:

```sql
ALTER TABLE query.post_projections
DROP CONSTRAINT uq_post_projection_canonical_url;
```

New databases are created with the current schema by `init_db()`.

For an existing development database, apply this one-time query schema update
before starting the Step 6 projector:

```sql
ALTER TABLE query.post_projections
  ADD COLUMN IF NOT EXISTS post_revision INTEGER NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS source_category VARCHAR(128);
UPDATE query.post_projections
SET source_category = category, category = NULL
WHERE source_category IS NULL;
CREATE TABLE IF NOT EXISTS query.post_enrichments (
  post_id VARCHAR(64) PRIMARY KEY,
  post_revision INTEGER NOT NULL,
  taxonomy_version VARCHAR(64) NOT NULL,
  status VARCHAR(16) NOT NULL,
  category_id VARCHAR(32)
);
```

Then replay saved content posts in bounded batches after the query binding is
active. Existing publisher labels remain in `source_category`; unenriched posts
remain visible in All with a null public category, so they do not appear in
category facets. Keep the enrichment consumer disabled on the normal local
stack until real classifications and operational controls are ready.

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
poetry run ruff format --check src tests
```

## Current development schema and operations

The current query models store `post_projections.categories` and
`post_enrichments.category_ids` as text arrays; results also store
`enrichment_revision`. `create_all()` creates missing tables and does not alter
existing columns. Inspect affected local tables with consumers stopped, then
apply scoped ALTER TABLE operations directly when changing the development schema.
Keep canonical content and account tables. No startup conversion or migration
script is provided.

The durable `public-api.query.v1` queue owns the `post.enriched.v1` binding on
`enrichment.events`. Establish this queue/binding before enrichment consumes input.
Inspect pending messages and saved result envelopes before removing obsolete
bindings or unused sink queues. Superseded disposable development results/messages
can be cleared and rebuilt locally; runtime accepts only the current payload.
The October 9 local inspection found no enrichment queues, bindings or saved
results to clear, so no broker purge or result reset was needed.

The Android client currently defaults its scalar category to null and ignores
unknown JSON keys. Articles remain readable, with category presentation deferred
to Step 6's collection adaptation. No scalar calculated-category alias is exposed.
The admin canonical detail response retains the owning content service's publisher
category field; it is separate from calculated public categories.

For isolated PostgreSQL collection/filter tests, set PUBLIC_API_TEST_DATABASE_URL
and run pytest. The test creates/removes its own query_test_<random> schema and
requires the normal query.keywords_to_search_text function established by init_db.
