import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.event_publisher import publish_event
from src.config.database import get_db
from src.config.message_broker import publisher_channel
from src.config.settings import settings
from src.events.post_deleted import build_post_deleted_event
from src.events.post_parsed import build_post_parsed_event
from src.models.post import Post
from src.routers.admin_auth import require_internal_admin_token

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/posts/replay", dependencies=[Depends(require_internal_admin_token)])
def replay_posts(
    post_id: uuid.UUID | None = Query(None),
    since: datetime | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(Post)
    if post_id is not None:
        stmt = stmt.where(Post.post_id == post_id)
    if since is not None:
        stmt = stmt.where(Post.parsed_at >= since)
    stmt = stmt.order_by(Post.parsed_at.asc()).limit(limit)

    posts = list(db.scalars(stmt).all())
    if not posts:
        return {"replayed": 0}

    replayed_count = 0
    with publisher_channel(exchange=settings.parsed_exchange) as channel:
        for post in posts:
            correlation_id = f"replay-{uuid.uuid4()}"
            if post.is_deleted:
                if post.deleted_at is None:
                    raise RuntimeError("Deleted post has no deletion timestamp")
                envelope = build_post_deleted_event(
                    post_id=str(post.post_id),
                    post_revision=post.post_revision,
                    deleted_at=post.deleted_at,
                    correlation_id=correlation_id,
                )
            else:
                snapshot = {
                    column.name: getattr(post, column.name)
                    for column in Post.__table__.columns
                }
                envelope = build_post_parsed_event(
                    snapshot, correlation_id=correlation_id
                )
            publish_event(
                channel,
                exchange=settings.parsed_exchange,
                envelope=envelope,
            )
            replayed_count += 1

    return {"replayed": replayed_count}
