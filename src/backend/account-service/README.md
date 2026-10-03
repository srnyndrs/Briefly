# Account Service

## Role

The account service is Briefly's authority for user identity and account data.
It helps users create accounts, sign in securely, manage their display name and
preferences, and follow feed sources.

## Responsibilities

- Register and authenticate users.
- Protect passwords and manage token lifecycle.
- Manage account display names.
- Manage reading preferences and source subscriptions.
- Publish selected account changes for downstream services.

## Does not own

- News sources, fetched feeds, or stored posts.
- Personalized feed queries or recommendations.
- The client-facing API gateway.

The public API handles client-facing authorization and forwards account
operations to this service. Account-service remains the authoritative writer
for account data.

Password-reset requests always return `202 {"status":"accepted"}` without a
secret, whether or not the email exists. The service stores only a SHA-256
digest of one expiring reset secret per user and sends the raw secret through
the configured SMTP adapter. A successful reset revokes every refresh session;
access tokens remain valid until their normal 15-minute expiry.

Root Compose sends local reset emails to Mailpit at `http://localhost:8025`.
Non-local deployments must set an SMTP host, sender address, reset URL, and
TLS setting through environment variables.

Admin access uses `ADMIN_USER_IDS_CSV`. To provision an operator locally,
register a normal account, sign in, read its ID from `GET /me`, add that UUID
to the account-service `.env`, and sign in again to receive a new admin-scoped
access token. The list defaults to empty; choosing an email address during
registration does not grant admin access. Keep credentials and JWT signing
secrets in local service configuration, never in browser code.

## Integration

The service receives account operations from the public API. It stores account
data in PostgreSQL and publishes selected changes through RabbitMQ so other
services can update their read models.

It exposes HTTP endpoints for authentication, account data,
preferences, subscriptions, and health checks. When it is running, use `/docs`
for the current API documentation.

## Development

Copy `.env.example` to `.env` and adjust the local values. The example lists
all supported settings, including optional Sentry reporting and local Mailpit
delivery. JWT settings must match public-api. Root Compose loads `.env`, but
its explicit `environment` values take precedence.

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
