import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.events.post_enriched import EnrichmentPayload
from src.models.read_models import (
    PostDeletionProjection,
    PostEnrichmentProjection,
    PostProjection,
    UserPreferencesProjection,
)

logger = logging.getLogger(__name__)


def _public_categories(result: PostEnrichmentProjection | None) -> list[str]:
    if result is not None and result.status == "completed":
        return list(result.category_ids)

    return []


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
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed
    except ValueError:
        return None


def project_post(db: Session, payload: dict[str, Any]) -> None:
    payload = payload or {}
    source_id = UUID(
        str(_require_source_value(payload.get("source_id"), "source_id"))
    )
    source_title = _require_source_title(payload.get("source_title"))
    post_id_value = payload.get("post_id")
    post_id = UUID(str(post_id_value)) if post_id_value else None
    if not post_id:
        return

    revision = payload["post_revision"]
    if db.get(PostDeletionProjection, post_id) is not None:
        return
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
    existing.categories = (
        _public_categories(result)
        if result is not None and result.post_revision == revision
        else []
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
    payload = EnrichmentPayload.model_validate(payload).model_dump()
    post_id = UUID(str(payload["post_id"]))
    revision = payload["post_revision"]
    if db.get(PostDeletionProjection, post_id) is not None:
        return
    result = db.get(PostEnrichmentProjection, post_id)
    post = db.get(PostProjection, post_id)
    if post is not None and post.is_deleted:
        return
    if post is not None and post.post_revision > revision:
        return

    if result is not None and (
        result.post_revision,
        result.enrichment_revision,
    ) >= (revision, payload["enrichment_revision"]):
        return
    if result is None:
        result = PostEnrichmentProjection(post_id=post_id)
        db.add(result)

    result.post_revision = revision
    result.status = payload["status"]
    result.enrichment_revision = payload["enrichment_revision"]
    result.category_ids = payload["category_ids"]

    if post is not None and post.post_revision == revision:
        post.categories = _public_categories(result)


def project_post_deleted(db: Session, payload: dict[str, Any]) -> None:
    post_id = UUID(_require_source_value(payload["post_id"], "post_id"))
    revision = payload["post_revision"]
    if type(revision) is not int or revision < 1:
        raise ValueError("post_revision must be a positive integer")
    deleted_at = _parse_dt(
        _require_source_value(payload["deleted_at"], "deleted_at")
    )
    if deleted_at is None:
        raise ValueError("deleted_at must be a valid timestamp")

    marker = db.get(PostDeletionProjection, post_id)
    if marker is None:
        db.add(
            PostDeletionProjection(
                post_id=post_id,
                post_revision=revision,
                deleted_at=deleted_at,
            )
        )
    else:
        marker.post_revision = max(marker.post_revision, revision)
        if marker.deleted_at.tzinfo is None:
            marker.deleted_at = marker.deleted_at.replace(tzinfo=UTC)
        marker.deleted_at = min(marker.deleted_at, deleted_at)

    post = db.get(PostProjection, post_id)
    if post is not None:
        post.is_deleted = True
        post.post_revision = max(post.post_revision, revision)


def project_user_preferences(db: Session, payload: dict[str, Any]) -> None:
    payload = payload or {}
    user_id_value = payload.get("user_id")
    if not user_id_value:
        return

    user_id = UUID(str(user_id_value))

    prefs = db.get(UserPreferencesProjection, user_id)
    if prefs is None:
        prefs = UserPreferencesProjection(user_id=user_id)
        db.add(prefs)

    prefs.muted_keywords = payload.get("muted_keywords") or []
    prefs.muted_categories = payload.get("muted_categories") or []
    prefs.blocked_source_ids = [
        str(UUID(str(source_id)))
        for source_id in payload.get("blocked_source_ids") or []
    ]
    prefs.languages = payload.get("languages") or []
    prefs.updated_at = _parse_dt(payload.get("updated_at")) or prefs.updated_at
