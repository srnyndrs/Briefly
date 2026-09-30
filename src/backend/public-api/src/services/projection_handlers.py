import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from src.models.read_models import (
    PostProjection,
    UserPreferencesProjection,
)

logger = logging.getLogger("public-api.projections")


def _require_source_value(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a nonblank string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must be nonblank")
    return normalized


def _require_source_title(value: Any) -> str:
    title = _require_source_value(value, "source_title")
    if len(title) > 255:
        raise ValueError("source_title must be at most 255 characters")
    return title


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
    source_id = _require_source_value(payload.get("source_id"), "source_id")
    source_title = _require_source_title(payload.get("source_title"))
    post_id = payload.get("post_id")
    if not post_id:
        return

    published_at_raw = payload["published_at"]
    published_at = _parse_dt(published_at_raw)

    logger.info(
        "ProjectPost: post_id=%s, published_at_raw=%s, final_published_at=%s",
        post_id,
        published_at_raw,
        published_at,
    )

    existing = db.get(PostProjection, post_id)
    if existing is None:
        existing = PostProjection(post_id=post_id)
        db.add(existing)

    existing.source_id = source_id
    existing.source_title = source_title
    existing.canonical_url = payload["url"]
    existing.title = payload["title"]
    existing.description = payload["description"]
    existing.category = payload["category"]
    existing.content = payload["content"]
    existing.author = payload["author"]
    existing.language = payload["language"]
    existing.keywords = payload["keywords"]
    existing.image_ref = payload["image_url"]
    existing.published_at = published_at


def project_user_preferences(db: Session, payload: dict[str, Any]) -> None:
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
    prefs.blocked_source_ids = payload.get("blocked_source_ids") or []
    prefs.languages = payload.get("languages") or []
    prefs.updated_at = _parse_dt(payload.get("updated_at")) or prefs.updated_at
