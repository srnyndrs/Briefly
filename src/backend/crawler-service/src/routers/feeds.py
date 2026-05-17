import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.config.settings import settings
from src.repositories.feed_repository import (
    SqlAlchemyFeedRepository,
)
from src.repositories.feed_discovery import FeedDiscoveryAdapter
from src.schemas.schemas import (
    ExploreRequest,
    ExploreResult,
    FeedCreate,
    FeedPatchRequest,
    FeedResponse,
)

router = APIRouter(prefix="/feeds", tags=["feeds"])


def discover_feeds(url: str) -> List[ExploreResult]:
    """Discover candidate feed endpoints for a website URL."""
    discovery = FeedDiscoveryAdapter()
    return discovery.discover(url)


@router.get("", response_model=List[FeedResponse])
def list_feeds(
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> List[FeedResponse]:
    """
    Return feeds registered in the crawler service.

    If active_only=True, only returns feeds that are due for crawling
    (next_crawl_scheduled_at <= now and failures < max_retries).
    """
    repository = SqlAlchemyFeedRepository(db)
    if active_only:
        feeds = repository.get_active_feeds(
            now=datetime.now(timezone.utc),
            max_retries=settings.max_retries,
        )
    else:
        feeds = repository.get_feeds()
    return feeds


@router.post("/explore", response_model=List[ExploreResult])
def explore_feeds(body: ExploreRequest) -> List[ExploreResult]:
    """Discover RSS/Atom feeds at the given URL."""
    return discover_feeds(str(body.url))


@router.post("", response_model=FeedResponse, status_code=201)
def register_feed(
    body: FeedCreate,
    db: Session = Depends(get_db),
) -> FeedResponse:
    """
    Register a new feed URL.

    Returns 409 if the URL is already registered.
    """
    discovered = discover_feeds(str(body.url))
    if not discovered:
        raise HTTPException(
            status_code=400,
            detail="No valid RSS/Atom feed found at the provided URL.",
        )

    first_feed = discovered[0]
    final_url = first_feed.url

    repository = SqlAlchemyFeedRepository(db)
    existing = repository.get_feed_by_url(final_url)
    if existing:
        raise HTTPException(
            status_code=409, detail="Feed URL already registered."
        )

    # In production the user_id comes from the validated JWT token.
    # Using a sentinel UUID until auth middleware is wired up.
    placeholder_user_id = uuid.UUID(
        "00000000-0000-0000-0000-000000000001"
    )

    feed = repository.create_feed(
        user_id=placeholder_user_id,
        url=final_url,
        title=body.title or first_feed.title,
        description=body.description or first_feed.description,
        favicon=body.favicon or first_feed.favicon,
    )
    return feed


@router.delete("/{feed_id}", status_code=204)
def delete_feed(
    feed_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    """Remove a feed from the crawl schedule."""
    repository = SqlAlchemyFeedRepository(db)
    deleted = repository.delete_feed(feed_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Feed not found."
        )


@router.get("/{feed_id}", response_model=FeedResponse)
def get_feed(
    feed_id: uuid.UUID, db: Session = Depends(get_db)
) -> FeedResponse:
    repository = SqlAlchemyFeedRepository(db)
    feed = repository.get_feed_by_id(feed_id)
    if feed is None:
        raise HTTPException(
            status_code=404, detail="Feed not found."
        )
    return feed


@router.patch("/{feed_id}", response_model=FeedResponse)
def patch_feed(
    feed_id: uuid.UUID,
    body: FeedPatchRequest,
    db: Session = Depends(get_db),
) -> FeedResponse:
    repository = SqlAlchemyFeedRepository(db)
    current = repository.get_feed_by_id(feed_id)
    if current is None:
        raise HTTPException(
            status_code=404, detail="Feed not found."
        )

    patch_data = body.model_dump(exclude_unset=True)
    resolved_url = (
        str(patch_data["url"])
        if "url" in patch_data
        else current.url
    )

    existing = repository.get_feed_by_url(resolved_url)
    if existing is not None and existing.feed_id != feed_id:
        raise HTTPException(
            status_code=409, detail="Feed URL already registered."
        )

    updated = repository.update_feed(
        feed_id=feed_id,
        url=resolved_url,
        title=patch_data.get("title", current.title),
        description=patch_data.get(
            "description", current.description
        ),
        favicon=patch_data.get("favicon", current.favicon),
    )
    if updated is None:
        raise HTTPException(
            status_code=404, detail="Feed not found."
        )

    return updated
