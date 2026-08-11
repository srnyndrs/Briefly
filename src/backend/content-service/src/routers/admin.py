import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.config.message_broker import create_channel
from src.config.settings import settings
from src.models.article import Article
from src.services import event_publisher

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin_token(
    x_admin_token: str | None = Header(None, alias="x-admin-token")
) -> None:
    if settings.admin_token and x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/articles/replay", dependencies=[Depends(require_admin_token)])
def replay_articles(
    since: datetime | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    stmt = select(Article)
    if since is not None:
        stmt = stmt.where(Article.parsed_at >= since)
    stmt = stmt.order_by(Article.parsed_at.asc()).limit(limit)

    articles = list(db.scalars(stmt).all())
    if not articles:
        return {"replayed": 0}

    channel = create_channel()
    replayed_count = 0
    try:
        for article in articles:
            correlation_id = f"replay-{uuid.uuid4()}"
            keywords_val = (
                article.keywords
                if isinstance(article.keywords, list)
                else []
            )
            event_publisher.publish_parsed_success(
                channel,
                article_id=str(article.id),
                feed_id=str(article.feed_id),
                item_guid=article.item_guid,
                url=article.url,
                title=article.title,
                correlation_id=correlation_id,
                category=article.category,
                content=article.content,
                content_length=len(article.content or ""),
                description=article.description,
                published_at=article.published_at.isoformat()
                if article.published_at
                else None,
                language=article.language,
                keywords=keywords_val,
                source_title=None,
            )
            replayed_count += 1
    finally:
        if channel.connection and channel.connection.is_open:
            channel.connection.close()

    return {"replayed": replayed_count}
