# Account Service

## Purpose
`account-service` is the identity, profile, preferences, subscription, and authentication authority for Briefly. It handles user registration, Argon2 password hashing, JWT issuance/refresh, profile management, subscription tracking, and user preference storage.

## Port
`8003`

## Database Schema & Tables
- **Schema:** `account`
- **Tables:**
  - `accounts`: User authentication credentials and status.
  - `profiles`: Display name, bio, avatar URL.
  - `user_preferences`: Preferred categories/languages, excluded languages, blocked source IDs.
  - `subscriptions`: User-to-source subscription mappings.
  - `refresh_tokens`: Token versioning and refresh token tracking.

## Events Produced
- `preferences.updated.v1` (Exchange: `account.events`)

## Testing
Run unit tests using Poetry:
```bash
poetry run pytest
```
