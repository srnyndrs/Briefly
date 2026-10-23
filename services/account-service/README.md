# Account Service

Owns Briefly's user identities and account data.

## Responsibilities

- Register users, authenticate sign-ins, and manage tokens and password resets.
- Store profiles, reading preferences, and source subscriptions.
- Publish account changes for downstream read models.

Uses PostgreSQL and RabbitMQ, plus SMTP for reset emails (Mailpit locally).

## Commands

Run from this service's directory:

- `make quickstart` — install dependencies.
- `make test` — run tests.
- `make lint` / `make format` — check lint and formatting.
- `make lint-fix` / `make format-fix` — apply fixes.
