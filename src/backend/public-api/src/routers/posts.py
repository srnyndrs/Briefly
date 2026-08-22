import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.repositories.feed_repository import (
    PostRepository,
    UserPreferencesRepository,
)
from src.repositories.service_clients import (
    ServiceClientError,
    content_get_post,
    content_list_posts,
    content_posts_count,
    map_service_error,
)
from src.schemas.api import (
    AdminPostResponse,
    PostCountResponse,
    PostResponse,
)
from src.services.auth import CurrentAdminUser, CurrentUser
from src.services.feed_dtos import PostDTO
from src.services.feed_service import FeedService, GetPostInput

router = APIRouter(prefix="/posts", tags=["posts"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _to_post_response(item: PostDTO) -> PostResponse:
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


@router.get(
    "/{post_id}",
    response_model=PostResponse,
)
def get_post_by_id(
    post_id: uuid.UUID,
    user: CurrentUser,
    service: FeedService = Depends(get_feed_service),
) -> PostResponse:
    _ = user
    item = service.get_post(
        GetPostInput(post_id=post_id)
    )
    if item is None:
        raise HTTPException(
            status_code=404, detail="Post not found"
        )
    return _to_post_response(item)


@admin_router.get(
    "/posts/count", response_model=PostCountResponse
)
def admin_post_count(
    admin_user: CurrentAdminUser,
) -> PostCountResponse:
    _ = admin_user
    try:
        return PostCountResponse(**content_posts_count())
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@admin_router.get(
    "/posts", response_model=list[AdminPostResponse]
)
def admin_list_posts(
    admin_user: CurrentAdminUser,
    limit: int = 20,
    skip: int = 0,
    source_id: str | None = None,
    language: str | None = None,
    category: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    parsed_from: datetime | None = None,
    parsed_to: datetime | None = None,
) -> list[AdminPostResponse]:
    _ = admin_user
    params: dict[str, str | int] = {
        "limit": max(1, min(limit, 200)),
        "skip": max(0, skip),
    }
    if source_id:
        params["source_id"] = source_id
    if language:
        params["language"] = language
    if category:
        params["category"] = category
    if published_from:
        params["published_from"] = published_from.isoformat()
    if published_to:
        params["published_to"] = published_to.isoformat()
    if parsed_from:
        params["parsed_from"] = parsed_from.isoformat()
    if parsed_to:
        params["parsed_to"] = parsed_to.isoformat()

    try:
        rows = content_list_posts(params)
        return [AdminPostResponse(**r) for r in rows]
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@admin_router.get(
    "/posts/{post_id}", response_model=AdminPostResponse
)
def admin_get_post(
    post_id: str,
    admin_user: CurrentAdminUser,
) -> AdminPostResponse:
    _ = admin_user
    try:
        res = content_get_post(post_id)
        return AdminPostResponse(**res)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc
