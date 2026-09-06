import uuid

from fastapi import Depends
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.repositories.feed_repository import (
    PostRepository,
    UserPreferencesRepository,
)
from src.schemas.api import PostResponse
from src.services.feed_models import PostDTO
from src.services.feed_service import FeedService


def to_post_response(item: PostDTO) -> PostResponse:
    return PostResponse(
        post_id=uuid.UUID(item.post_id),
        source_id=uuid.UUID(item.source_id)
        if item.source_id
        else None,
        title=item.title,
        source_title=item.source_title,
        description=item.description,
        canonical_url=item.canonical_url,
        language=item.language,
        category=item.category,
        image_ref=item.image_ref,
        published_at=item.published_at,
        has_content=item.content is not None,
        content=item.content,
    )


def get_feed_service(
    db: Session = Depends(get_db),
) -> FeedService:
    return FeedService(
        PostRepository(db),
        UserPreferencesRepository(db),
    )
