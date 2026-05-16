from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.repositories.article_repository import ArticleRepository
from src.services.article_service import ArticleService

router = APIRouter(prefix="/articles", tags=["articles"])


def get_article_repository(
    db: Session = Depends(get_db),
) -> ArticleRepository:
    return ArticleRepository(db)


def get_article_service(
    repo: ArticleRepository = Depends(get_article_repository),
) -> ArticleService:
    return ArticleService(repo)


@router.get("/count")
def article_count(
    service: ArticleService = Depends(get_article_service),
) -> dict:
    return {"count": service.get_count()}


@router.get("")
def list_articles(
    limit: int = 20,
    skip: int = 0,
    source_id: str | None = None,
    language: str | None = None,
    category: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    parsed_from: datetime | None = None,
    parsed_to: datetime | None = None,
    service: ArticleService = Depends(get_article_service),
) -> list[dict]:
    return service.list_articles(
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


@router.get("/{article_id}")
def get_article(
    article_id: str,
    service: ArticleService = Depends(get_article_service),
) -> dict:
    article = service.get_by_id(article_id)
    if article is None:
        raise HTTPException(
            status_code=404, detail="Article not found"
        )
    return article
