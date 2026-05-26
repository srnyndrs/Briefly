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


@dataclass(frozen=True)
class UpdateArticleInput:
    article_id: str
    payload: dict[str, Any]


class UpdateArticleUseCase:
    """Project article update event."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: UpdateArticleInput) -> None:
        payload = data.payload
        article_id = payload.get("article_id") or data.article_id
        if not article_id:
            return

        article = self._db.get(ArticleProjection, article_id)
        if article is None:
            article = ArticleProjection(article_id=article_id)
            self._db.add(article)

        article.source_id = (
            payload.get("source_id") or article.source_id
        )
        article.source_title = (
            payload.get("source_title") or article.source_title
        )
        if "description" in payload:
            article.description = payload.get("description")
        article.updated_at = (
            parse_dt(payload.get("updated_at"))
            or article.updated_at
        )
        if (
            "content" in payload
            and payload.get("content") is not None
        ):
            article.content = payload.get("content")
        article.category = (
            payload.get("category") or article.category
        )
        if not article.language and payload.get("language"):
            article.language = payload.get("language")
        keywords_payload = payload.get("keywords")
        if (
            not article.keywords or article.keywords == []
        ) and keywords_payload:
            article.keywords = keywords_payload


@dataclass(frozen=True)
class ExtractArticleContentInput:
    article_id: str
    payload: dict[str, Any]


class ExtractArticleContentUseCase:
    """Project article content extraction event."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: ExtractArticleContentInput) -> None:
        payload = data.payload
        article_id = payload.get("article_id") or data.article_id
        if not article_id:
            return

        article = self._db.get(ArticleProjection, article_id)
        if article is None:
            article = ArticleProjection(article_id=article_id)
            self._db.add(article)

        article.source_id = (
            payload.get("source_id") or article.source_id
        )
        article.content_ref = (
            payload.get("content_ref") or article.content_ref
        )
        article.image_ref = (
            payload.get("image_ref") or article.image_ref
        )
        article.updated_at = (
            parse_dt(payload.get("extracted_at"))
            or article.updated_at
        )
        # Never update published_at, language, or categories in extract events


@dataclass(frozen=True)
class EnrichArticleInput:
    article_id: str
    payload: dict[str, Any]


class EnrichArticleUseCase:
    """Project article enrichment event (ML features)."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def execute(self, data: EnrichArticleInput) -> None:
        payload = data.payload
        article_id = payload.get("article_id") or data.article_id
        if not article_id:
            return

        article = self._db.get(ArticleProjection, article_id)
        if article is None:
            article = ArticleProjection(article_id=article_id)
            self._db.add(article)

        article.sentiment = (
            payload.get("sentiment") or article.sentiment
        )
        article.topics = (
            payload.get("topics") or article.topics or []
        )
        article.updated_at = (
            parse_dt(payload.get("enriched_at"))
            or article.updated_at
        )
        # Never update published_at, language, or categories in enrichment events


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

        prefs.preferred_categories = (
            payload.get("preferred_categories") or []
        )
        prefs.preferred_languages = (
            payload.get("preferred_languages") or []
        )
        prefs.excluded_languages = (
            payload.get("excluded_languages") or []
        )
        prefs.blocked_source_ids = (
            payload.get("blocked_source_ids") or []
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
