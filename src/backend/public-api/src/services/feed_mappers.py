from src.models.read_models import (
    ArticleProjection,
    UserPreferencesProjection,
)
from src.services.feed_dtos import FeedItemDTO, UserPreferencesDTO
from src.services.feed_types import ArticleEntity, UserPreferencesVO


def article_projection_to_entity(
    model: ArticleProjection,
) -> ArticleEntity:
    return ArticleEntity(
        article_id=model.article_id,
        source_id=model.source_id,
        source_title=model.source_title,
        title=model.title,
        description=model.description,
        canonical_url=model.canonical_url,
        language=model.language,
        category=model.category,
        keywords=model.keywords or [],
        content=model.content,
        image_ref=model.image_ref,
        sentiment=model.sentiment,
        topics=model.topics or [],
        published_at=model.published_at,
        updated_at=model.updated_at,
    )


def entity_to_feed_item_dto(entity: ArticleEntity) -> FeedItemDTO:
    return FeedItemDTO(
        article_id=entity.article_id,
        source_id=entity.source_id,
        source_title=entity.source_title,
        title=entity.title,
        description=entity.description,
        canonical_url=entity.canonical_url,
        language=entity.language,
        category=entity.category,
        keywords=entity.keywords,
        content=entity.content,
        image_ref=entity.image_ref,
        sentiment=entity.sentiment,
        topics=entity.topics,
        published_at=entity.published_at,
    )


def user_preferences_projection_to_dto(
    model: UserPreferencesProjection | None,
) -> UserPreferencesDTO:
    if model is None:
        return UserPreferencesDTO()
    return UserPreferencesDTO(
        muted_keywords=model.muted_keywords or [],
        muted_categories=model.muted_categories or [],
        blocked_source_ids=model.blocked_source_ids or [],
        languages=model.languages or [],
        category_interests=model.category_interests or [],
    )


def user_preferences_dto_to_vo(
    dto: UserPreferencesDTO,
) -> UserPreferencesVO:
    return UserPreferencesVO(
        muted_keywords=dto.muted_keywords,
        muted_categories=dto.muted_categories,
        blocked_source_ids=dto.blocked_source_ids,
        languages=dto.languages,
        category_interests=dto.category_interests,
    )
