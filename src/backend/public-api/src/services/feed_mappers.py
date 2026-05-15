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
        title=model.title,
        canonical_url=model.canonical_url,
        language=model.language,
        categories=model.categories or [],
        content=model.content,
        content_ref=model.content_ref,
        image_ref=model.image_ref,
        sentiment=model.sentiment,
        topics=model.topics or [],
        published_at=model.published_at,
        updated_at=model.updated_at,
        cluster_id=model.cluster_id,
        model_version=model.model_version,
    )


def entity_to_feed_item_dto(entity: ArticleEntity) -> FeedItemDTO:
    return FeedItemDTO(
        article_id=entity.article_id,
        source_id=entity.source_id,
        title=entity.title,
        canonical_url=entity.canonical_url,
        language=entity.language,
        categories=entity.categories,
        content=entity.content,
        content_ref=entity.content_ref,
        image_ref=entity.image_ref,
        sentiment=entity.sentiment,
        topics=entity.topics,
        published_at=entity.published_at,
        cluster_id=entity.cluster_id,
        model_version=entity.model_version,
    )


def user_preferences_projection_to_dto(
    model: UserPreferencesProjection | None,
) -> UserPreferencesDTO:
    if model is None:
        return UserPreferencesDTO()
    return UserPreferencesDTO(
        preferred_categories=model.preferred_categories or [],
        preferred_languages=model.preferred_languages or [],
        excluded_languages=model.excluded_languages or [],
        blocked_source_ids=model.blocked_source_ids or [],
    )


def user_preferences_dto_to_vo(
    dto: UserPreferencesDTO,
) -> UserPreferencesVO:
    return UserPreferencesVO(
        preferred_categories=dto.preferred_categories,
        preferred_languages=dto.preferred_languages,
        excluded_languages=dto.excluded_languages,
        blocked_source_ids=dto.blocked_source_ids,
    )
