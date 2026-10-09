import logging
from datetime import datetime
from typing import Any
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
        "world",
        "business",
        "economy",
        "finance",
        "technology",
        "science",
        "health",
        "environment",
        "entertainment",
        "lifestyle",
        "automotive",
        "sports",
        "society",
        "other",
    }
)


class EnrichmentPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    post_id: str = Field(min_length=1, max_length=64)
    post_revision: int = Field(strict=True, ge=1)
    enrichment_revision: int = Field(strict=True, ge=1)
    taxonomy_version: Literal["categories-v2"]
    status: Literal["completed", "abstained", "failed"]
    category_ids: list[str] = Field(strict=True, max_length=2)
    input_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    enrichment_version: str = Field(min_length=1, max_length=100)
    processed_at: datetime

    @model_validator(mode="after")
    def validate_categories(self) -> "EnrichmentPayload":
        categories = self.category_ids
        if (
            any(category not in SUPPORTED_CATEGORIES for category in categories)
            or len(set(categories)) != len(categories)
            or ("other" in categories and len(categories) != 1)
            or (self.status == "completed") != bool(categories)
        ):
            raise ValueError("Invalid enrichment category collection or status")
        return self


def _public_categories(result: PostEnrichmentProjection | None) -> list[str]:
    if (
        result is not None
        and result.taxonomy_version == "categories-v2"
        and result.status == "completed"
    ):
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
    post_id = payload["post_id"]
    revision = payload["post_revision"]
    result = db.get(PostEnrichmentProjection, post_id)
    post = db.get(PostProjection, post_id)
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
    result.taxonomy_version = payload["taxonomy_version"]
    result.status = payload["status"]
    result.enrichment_revision = payload["enrichment_revision"]
    result.category_ids = payload["category_ids"]

    if post is not None and post.post_revision == revision:
        post.categories = _public_categories(result)


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
