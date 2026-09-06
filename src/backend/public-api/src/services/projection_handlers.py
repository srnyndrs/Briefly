import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from src.models.read_models import (
    PostProjection,
    UserPreferencesProjection,
)

logger = logging.getLogger("public-api.projections")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def project_post(db: Session, payload: dict[str, Any]) -> None:
    """Project parsed post event into read model."""
    payload = payload or {}
    post_id = payload.get("post_id")
    if not post_id:
        return

    source_id = payload.get("source_id")
    published_at_raw = payload.get("published_at")
    parsed_at_raw = payload.get("parsed_at")
    published_at = _parse_dt(published_at_raw or parsed_at_raw)

    logger.info(
        "ProjectPost: post_id=%s, published_at_raw=%s, parsed_at_raw=%s, final_published_at=%s",
        post_id,
        published_at_raw,
        parsed_at_raw,
        published_at,
    )

    existing = db.get(PostProjection, post_id)
    if existing is None:
        existing = PostProjection(post_id=post_id)
        db.add(existing)

    existing.source_id = source_id
    existing.source_title = (
        payload.get("source_title") or existing.source_title
    )
    existing.canonical_url = payload.get(
        "canonical_url"
    ) or payload.get("url")
    existing.title = payload.get("title") or existing.title
    if "description" in payload:
        existing.description = payload.get("description")
    if "content" in payload and payload.get("content") is not None:
        existing.content = payload.get("content")
    existing.category = payload.get("category") or existing.category
    # Only set language on first parse event (immutable)
    if not existing.language and payload.get("language"):
        existing.language = payload.get("language")
    # Only set keywords on first parse event (immutable)
    keywords_payload = payload.get("keywords")
    if (
        not existing.keywords or existing.keywords == []
    ) and keywords_payload:
        existing.keywords = keywords_payload
    # Only set published_at on first parse event (immutable)
    if not existing.published_at and published_at:
        existing.published_at = published_at
    if "image_url" in payload or "image_ref" in payload:
        existing.image_ref = payload.get(
            "image_url"
        ) or payload.get("image_ref")


def project_user_preferences(
    db: Session, payload: dict[str, Any]
) -> None:
    """Project user preferences update event."""
    payload = payload or {}
    user_id = payload.get("user_id")
    if not user_id:
        return

    prefs = db.get(UserPreferencesProjection, user_id)
    if prefs is None:
        prefs = UserPreferencesProjection(user_id=user_id)
        db.add(prefs)

    prefs.muted_keywords = payload.get("muted_keywords") or []
    prefs.muted_categories = payload.get("muted_categories") or []
    prefs.blocked_source_ids = (
        payload.get("blocked_source_ids") or []
    )
    prefs.languages = payload.get("languages") or []
    prefs.category_interests = (
        payload.get("category_interests") or []
    )
    prefs.updated_at = (
        _parse_dt(payload.get("updated_at")) or prefs.updated_at
    )
