import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters import post_publisher
from src.config.database import get_db
from src.config.message_broker import (
    create_replay_publisher_channel,
)
from src.config.settings import settings
from src.models.post import Post

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_token(
    x_admin_token: str | None = Header(None, alias="x-admin-token"),
) -> None:
    if settings.admin_token and x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post(
    "/posts/replay", dependencies=[Depends(require_admin_token)]
)
def replay_posts(
    since: datetime | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(Post)
    if since is not None:
        stmt = stmt.where(Post.parsed_at >= since)
    stmt = stmt.order_by(Post.parsed_at.asc()).limit(limit)

    posts = list(db.scalars(stmt).all())
    if not posts:
        return {"replayed": 0}

    channel = create_replay_publisher_channel()
    replayed_count = 0
    try:
        for post in posts:
            correlation_id = f"replay-{uuid.uuid4()}"
            keywords_val = (
                post.keywords if isinstance(post.keywords, list) else []
            )
            post_publisher.publish_post_parsed_success(
                channel,
                post_id=str(post.post_id),
                source_id=str(post.source_id),
                item_guid=post.item_guid,
                url=post.url,
                title=post.title,
                correlation_id=correlation_id,
                category=post.category,
                content=post.content,
                content_length=len(post.content or ""),
                description=post.description,
                published_at=post.published_at.isoformat()
                if post.published_at
                else None,
                language=post.language,
                keywords=keywords_val,
                source_title=post.source_title,
                image_url=post.image_url,
            )
            replayed_count += 1
    finally:
        if channel.connection and channel.connection.is_open:
            channel.connection.close()

    return {"replayed": replayed_count}
