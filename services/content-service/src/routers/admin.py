import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.adapters.event_publisher import publish_event
from src.config.database import get_db
from src.config.message_broker import publisher_channel
from src.config.settings import settings
from src.events.post_parsed import build_post_parsed_event
from src.models.post import Post

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_token(
    x_admin_token: str | None = Header(None, alias="x-admin-token"),
) -> None:
    if settings.admin_token and x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/posts/replay", dependencies=[Depends(require_admin_token)])
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

    replayed_count = 0
    with publisher_channel(exchange=settings.parsed_exchange) as channel:
        for post in posts:
            correlation_id = f"replay-{uuid.uuid4()}"
            keywords_val = (
                post.keywords if isinstance(post.keywords, list) else []
            )
            envelope = build_post_parsed_event(
                post_id=str(post.post_id),
                source_id=str(post.source_id),
                post_revision=post.post_revision,
                item_guid=post.item_guid,
                url=post.url,
                title=post.title,
                correlation_id=correlation_id,
                category=post.category,
                content=post.content,
                description=post.description,
                published_at=post.published_at.isoformat()
                if post.published_at
                else None,
                language=post.language,
                keywords=keywords_val,
                author=post.author,
                source_title=post.source_title,
                image_url=post.image_url,
            )
            publish_event(
                channel,
                exchange=settings.parsed_exchange,
                envelope=envelope,
            )
            replayed_count += 1

    return {"replayed": replayed_count}
