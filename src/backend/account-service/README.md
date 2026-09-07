# Account Service

## Role

The account service is Briefly's authority for user identity and account data.
It helps users create accounts, sign in securely, manage their profiles and
preferences, and follow feed sources.

## Responsibilities

- Register and authenticate users.
- Protect passwords and manage token lifecycle.
- Manage user profiles.
- Manage reading preferences and source subscriptions.
- Publish selected account changes for downstream services.

## Does not own

- News sources, fetched feeds, or stored posts.
- Personalized feed queries or recommendations.
- The client-facing API gateway.

The public API handles client-facing authorization and forwards account
operations to this service. Account-service remains the authoritative writer
for account data.

## Integration

The service receives account operations from the public API. It stores account
data in PostgreSQL and publishes selected changes through RabbitMQ so other
services can update their read models.

It exposes HTTP endpoints for authentication, account data, profiles,
preferences, subscriptions, and health checks. When it is running, use `/docs`
for the current API documentation.

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
poetry run ruff format --check src tests
```
