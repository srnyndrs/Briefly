import logging
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.adapters.event_publisher import publish_event
from src.config.database import get_db
from src.config.message_broker import publisher_channel
from src.config.settings import settings
from src.events.post_deleted import build_post_deleted_event
from src.events.post_parsed import build_post_parsed_event
from src.models.post import Post
from src.repositories.post_repository import PostRepository
from src.routers.admin_auth import require_internal_admin_token
from src.schemas.posts import (
    PostCountResponse,
    PostPatchRequest,
    PostPatchResponse,
    PostResponse,
)

router = APIRouter(prefix="/posts", tags=["posts"])
logger = logging.getLogger(__name__)


def get_post_repository(db: Session = Depends(get_db)) -> PostRepository:
    return PostRepository(db)


def _publish_snapshot(snapshot: dict[str, Any]) -> None:
    envelope = build_post_parsed_event(
        snapshot,
        correlation_id=f"admin-edit-{uuid.uuid4()}",
    )
    with publisher_channel(exchange=settings.parsed_exchange) as channel:
        publish_event(channel, exchange=settings.parsed_exchange, envelope=envelope)


def _publish_deletion(post: Post) -> None:
    if post.deleted_at is None:
        raise RuntimeError("Deleted post has no deletion timestamp")
    envelope = build_post_deleted_event(
        post_id=str(post.post_id),
        post_revision=post.post_revision,
        deleted_at=post.deleted_at,
    )
    with publisher_channel(exchange=settings.parsed_exchange) as channel:
        publish_event(channel, exchange=settings.parsed_exchange, envelope=envelope)


@router.get("", response_model=list[PostResponse])
def list_posts(
    limit: int = 20,
    skip: int = 0,
    source_id: UUID | None = None,
    language: str | None = None,
    category: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    parsed_from: datetime | None = None,
    parsed_to: datetime | None = None,
    repo: PostRepository = Depends(get_post_repository),
) -> list[Post]:
    return repo.list_posts(
        limit=max(1, min(limit, 200)),
        skip=max(0, skip),
        source_id=source_id,
        language=language,
        category=category,
        published_from=published_from,
        published_to=published_to,
        parsed_from=parsed_from,
        parsed_to=parsed_to,
    )


@router.get("/count", response_model=PostCountResponse)
def post_count(
    repo: PostRepository = Depends(get_post_repository),
) -> PostCountResponse:
    return PostCountResponse(count=repo.count_posts())


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: UUID,
    repo: PostRepository = Depends(get_post_repository),
) -> Post:
    post = repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return post


@router.patch(
    "/{post_id}",
    response_model=PostPatchResponse,
    dependencies=[Depends(require_internal_admin_token)],
)
def patch_post(
    post_id: UUID,
    body: PostPatchRequest,
    repo: PostRepository = Depends(get_post_repository),
) -> PostPatchResponse:
    try:
        snapshot = repo.patch_post(post_id, body.model_dump(exclude_unset=True))
        if snapshot is not None:
            repo.commit()
    except Exception:
        repo.rollback()
        raise
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Post not found")

    publication_status = "published"
    try:
        _publish_snapshot(snapshot)
    except Exception:
        logger.exception("Post saved, but parsed event publication failed")
        publication_status = "event_pending"

    return PostPatchResponse(**snapshot, publication_status=publication_status)


@router.delete(
    "/{post_id}",
    status_code=204,
    dependencies=[Depends(require_internal_admin_token)],
)
def delete_post(
    post_id: UUID,
    repo: PostRepository = Depends(get_post_repository),
) -> None:
    try:
        post = repo.delete_post(post_id)
        if post is not None:
            repo.commit()
    except Exception:
        repo.rollback()
        raise
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    try:
        _publish_deletion(post)
    except Exception as exc:
        logger.exception("Post deleted, but deletion event publication failed")
        raise HTTPException(
            status_code=503,
            detail=(
                "Post is deleted, but its event was not published. "
                "Do not recreate it; retry DELETE after RabbitMQ recovers."
            ),
        ) from exc
