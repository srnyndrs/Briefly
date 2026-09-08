from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.models.post import Post
from src.repositories.post_repository import PostRepository
from src.schemas.posts import PostCountResponse, PostResponse

router = APIRouter(prefix="/posts", tags=["posts"])


def get_post_repository(
    db: Session = Depends(get_db),
) -> PostRepository:
    return PostRepository(db)


@router.get("/count", response_model=PostCountResponse)
def post_count(
    repo: PostRepository = Depends(get_post_repository),
) -> PostCountResponse:
    return PostCountResponse(count=repo.count())


@router.get("", response_model=list[PostResponse])
def list_posts(
    limit: int = 20,
    skip: int = 0,
    source_id: str | None = None,
    language: str | None = None,
    category: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    parsed_from: datetime | None = None,
    parsed_to: datetime | None = None,
    repo: PostRepository = Depends(get_post_repository),
) -> list[Post]:
    return repo.list(
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


@router.get("/{post_id}", response_model=PostResponse)
def get_post(
    post_id: str,
    repo: PostRepository = Depends(get_post_repository),
) -> Post:
    post = repo.get_by_id(post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
