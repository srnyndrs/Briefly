import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from src.models.read_models import (
    ArticleProjection,
    UserPreferencesProjection,
    UserSubscriptionProjection,
)
from src.services.projection_utils import parse_dt

logger = logging.getLogger("public-api.projections")


@dataclass(frozen=True)
class ProjectArticleInput:
    article_id: str
    payload: dict[str, Any]


class ProjectArticleUseCase:
    """Project parsed article event into read model."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: ProjectArticleInput) -> None:
        payload = data.payload
        article_id = payload.get("article_id") or data.article_id
        if not article_id:
            return

        source_id = payload.get("source_id") or payload.get(
            "feed_id"
        )
        published_at_raw = payload.get("published_at")
        parsed_at_raw = payload.get("parsed_at")
        published_at = parse_dt(published_at_raw or parsed_at_raw)

        logger.info(
            "ProjectArticle: article_id=%s, published_at_raw=%s, parsed_at_raw=%s, final_published_at=%s",
            article_id,
            published_at_raw,
            parsed_at_raw,
            published_at,
        )

        existing = self._db.get(ArticleProjection, article_id)
        if existing is None:
            existing = ArticleProjection(article_id=article_id)
            self._db.add(existing)

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
        # Store content if present on the parsed event.
        if (
            "content" in payload
            and payload.get("content") is not None
        ):
            existing.content = payload.get("content")
        existing.category = (
            payload.get("category") or existing.category
        )
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
            existing.image_ref = (
                payload.get("image_url") or payload.get("image_ref")
            )


@dataclass(frozen=True)
class ProjectUserPreferencesInput:
    user_id: str
    payload: dict[str, Any]


class ProjectUserPreferencesUseCase:
    """Project user preferences update event."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: ProjectUserPreferencesInput) -> None:
        payload = data.payload
        user_id = payload.get("user_id") or data.user_id
        if not user_id:
            return

        prefs = self._db.get(UserPreferencesProjection, user_id)
        if prefs is None:
            prefs = UserPreferencesProjection(user_id=user_id)
            self._db.add(prefs)

        prefs.muted_keywords = (
            payload.get("muted_keywords") or []
        )
        prefs.muted_categories = (
            payload.get("muted_categories") or []
        )
        prefs.blocked_source_ids = (
            payload.get("blocked_source_ids") or []
        )
        prefs.languages = (
            payload.get("languages") or []
        )
        prefs.category_interests = (
            payload.get("category_interests") or []
        )
        prefs.updated_at = (
            parse_dt(payload.get("updated_at")) or prefs.updated_at
        )



@dataclass(frozen=True)
class CreateSubscriptionInput:
    user_id: str
    source_id: str
    payload: dict[str, Any]


class CreateSubscriptionUseCase:
    """Project subscription creation event."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: CreateSubscriptionInput) -> None:
        payload = data.payload
        user_id = payload.get("user_id") or data.user_id
        source_id = payload.get("source_id") or data.source_id

        if not user_id or not source_id:
            return

        sub = UserSubscriptionProjection(
            user_id=user_id,
            source_id=source_id,
            created_at=parse_dt(payload.get("created_at")),
        )
        self._db.merge(sub)


@dataclass(frozen=True)
class DeleteSubscriptionInput:
    user_id: str
    source_id: str


class DeleteSubscriptionUseCase:
    """Project subscription deletion event."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: DeleteSubscriptionInput) -> None:
        self._db.query(UserSubscriptionProjection).filter(
            UserSubscriptionProjection.user_id == data.user_id,
            UserSubscriptionProjection.source_id == data.source_id,
        ).delete()
