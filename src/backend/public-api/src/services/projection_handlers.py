import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from src.models.read_models import (
    PostEnrichmentProjection,
    PostProjection,
    UserPreferencesProjection,
)

logger = logging.getLogger("public-api.projections")

SUPPORTED_CATEGORIES = frozenset(
    {
        "politics",
        "business",
        "technology",
        "science",
        "health",
        "environment",
        "culture",
        "sports",
        "society",
        "other",
    }
)


def _public_category(result: PostEnrichmentProjection | None) -> str | None:
    if (
        result is not None
        and result.taxonomy_version == "categories-v1"
        and result.status == "completed"
        and result.category_id in SUPPORTED_CATEGORIES
    ):
        return result.category_id
    return None


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

    revision = payload["post_revision"]
    existing = db.get(PostProjection, post_id)
    if existing is not None and existing.post_revision > revision:
        return

    published_at_raw = payload["published_at"]
    published_at = _parse_dt(published_at_raw)

    logger.info(
        "ProjectPost: post_id=%s, published_at_raw=%s, final_published_at=%s",
        post_id,
        published_at_raw,
        published_at,
    )

    result = db.get(PostEnrichmentProjection, post_id)
    if existing is None:
        existing = PostProjection(post_id=post_id)
        db.add(existing)

    existing.post_revision = revision
    existing.category = (
        _public_category(result)
        if result is not None and result.post_revision == revision
        else None
    )
    existing.source_id = source_id
    existing.source_title = source_title
    existing.canonical_url = payload["url"]
    existing.title = payload["title"]
    existing.description = payload["description"]
    existing.source_category = payload["category"]
    existing.content = payload["content"]
    existing.author = payload["author"]
    existing.language = payload["language"]
    existing.keywords = payload["keywords"]
    existing.image_ref = payload["image_url"]
    existing.published_at = published_at


def project_enrichment(db: Session, payload: dict[str, Any]) -> None:
    post_id = payload["post_id"]
    revision = payload["post_revision"]
    result = db.get(PostEnrichmentProjection, post_id)
    if result is not None and result.post_revision > revision:
        return
    if result is None:
        result = PostEnrichmentProjection(post_id=post_id)
        db.add(result)

    result.post_revision = revision
    result.taxonomy_version = payload["taxonomy_version"]
    result.status = payload["status"]
    result.category_id = payload.get("category_id")

    post = db.get(PostProjection, post_id)
    if post is not None and post.post_revision == revision:
        post.category = _public_category(result)


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
