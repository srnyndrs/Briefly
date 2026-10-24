"""Build the account preferences updated event."""

from datetime import UTC
from typing import Any

from src.events.envelope import build_envelope
from src.models.account import UserPreferences


def build_preferences_updated_event(
    *, preferences: UserPreferences, correlation_id: str
) -> dict[str, Any]:
    return build_envelope(
        event_type="preferences.updated.v1",
        partition_key=f"user:{preferences.user_id}",
        correlation_id=correlation_id,
        payload={
            "user_id": str(preferences.user_id),
            "updated_at": (
                preferences.updated_at.replace(tzinfo=UTC)
                if preferences.updated_at.tzinfo is None
                else preferences.updated_at
            ).isoformat(),
            "muted_keywords": preferences.muted_keywords,
            "muted_categories": preferences.muted_categories,
            "blocked_source_ids": preferences.blocked_source_ids,
            "languages": preferences.languages,
        },
    )
