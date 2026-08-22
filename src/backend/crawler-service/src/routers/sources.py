import uuid
from datetime import datetime, timezone
from typing import List

import feedparser
import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.config.settings import settings
from src.repositories.source_discovery import SourceDiscoveryAdapter
from src.repositories.source_repository import (
    SqlAlchemySourceRepository,
)
from src.schemas.schemas import (
    SourceCreate,
    SourceDiscoverRequest,
    SourceDiscoverResult,
    SourcePatchRequest,
    SourceResponse,
)

router = APIRouter(prefix="/sources", tags=["sources"])


def discover_sources(url: str) -> List[SourceDiscoverResult]:
    discovery = SourceDiscoveryAdapter()
    return discovery.discover(url)


def extract_website_url(source_url: str) -> str | None:
    try:
        response = requests.get(source_url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if hasattr(feed, "feed") and hasattr(feed.feed, "link"):
            return feed.feed.link or None
        return None
    except Exception:
        return None


@router.get("", response_model=List[SourceResponse])
def list_sources(
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> List[SourceResponse]:
    repository = SqlAlchemySourceRepository(db)
    if active_only:
        sources = repository.get_active_sources(
            now=datetime.now(timezone.utc),
            max_retries=settings.max_retries,
        )
    else:
        sources = repository.get_sources()
    return sources


@router.post("/discover", response_model=List[SourceDiscoverResult])
def discover_sources_endpoint(
    body: SourceDiscoverRequest,
) -> List[SourceDiscoverResult]:
    return discover_sources(str(body.url))


@router.post("", response_model=SourceResponse, status_code=201)
def register_source(
    body: SourceCreate,
    db: Session = Depends(get_db),
) -> SourceResponse:
    discovered = discover_sources(str(body.url))
    if not discovered:
        raise HTTPException(
            status_code=400,
            detail="No valid RSS/Atom feed found at the provided URL.",
        )

    first_source = discovered[0]
    final_url = first_source.url

    repository = SqlAlchemySourceRepository(db)
    existing = repository.get_source_by_url(final_url)
    if existing:
        raise HTTPException(
            status_code=409, detail="Source URL already registered."
        )

    website_url = extract_website_url(final_url)

    source = repository.create_source(
        url=final_url,
        title=body.title or first_source.title,
        description=body.description or first_source.description,
        favicon=body.favicon or first_source.favicon,
        website_url=website_url,
        enrich_with_ai=body.enrich_with_ai,
    )
    return source


@router.delete("/{source_id}", status_code=204)
def delete_source(
    source_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    repository = SqlAlchemySourceRepository(db)
    deleted = repository.delete_source(source_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail="Source not found."
        )


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: uuid.UUID, db: Session = Depends(get_db)
) -> SourceResponse:
    repository = SqlAlchemySourceRepository(db)
    source = repository.get_source_by_id(source_id)
    if source is None:
        raise HTTPException(
            status_code=404, detail="Source not found."
        )
    return source


@router.patch("/{source_id}", response_model=SourceResponse)
def patch_source(
    source_id: uuid.UUID,
    body: SourcePatchRequest,
    db: Session = Depends(get_db),
) -> SourceResponse:
    repository = SqlAlchemySourceRepository(db)
    current = repository.get_source_by_id(source_id)
    if current is None:
        raise HTTPException(
            status_code=404, detail="Source not found."
        )

    patch_data = body.model_dump(exclude_unset=True)
    resolved_url = (
        str(patch_data["url"])
        if "url" in patch_data
        else current.url
    )

    existing = repository.get_source_by_url(resolved_url)
    if existing is not None and existing.source_id != source_id:
        raise HTTPException(
            status_code=409, detail="Source URL already registered."
        )

    updated = repository.update_source(
        source_id=source_id,
        url=resolved_url,
        title=patch_data.get("title", current.title),
        description=patch_data.get(
            "description", current.description
        ),
        favicon=patch_data.get("favicon", current.favicon),
        enrich_with_ai=patch_data.get(
            "enrich_with_ai", current.enrich_with_ai
        ),
    )
    if updated is None:
        raise HTTPException(
            status_code=404, detail="Source not found."
        )

    return updated
