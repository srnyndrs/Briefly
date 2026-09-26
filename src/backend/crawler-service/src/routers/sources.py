import uuid
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.adapters.source_discovery import (
    SourceDiscoveryAdapter,
    normalize_feed_url,
    normalize_host,
    normalize_source_title,
    registrable_domain,
)
from src.config.database import get_db
from src.config.settings import settings
from src.repositories.source_repository import (
    SourceRepository,
)
from src.schemas.sources import (
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


@router.get("", response_model=List[SourceResponse])
def list_sources(
    active_only: bool = False,
    verified_only: bool = False,
    db: Session = Depends(get_db),
) -> List[SourceResponse]:
    repository = SourceRepository(db)
    if active_only:
        sources = repository.get_active_sources(
            now=datetime.now(timezone.utc),
            max_retries=settings.max_retries,
            verified_only=verified_only,
        )
    else:
        sources = repository.get_sources(verified_only=verified_only)
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

    if len(discovered) > 1:
        raise HTTPException(
            status_code=422,
            detail="Multiple valid feeds found; submit a direct feed URL.",
        )

    candidate = discovered[0]
    final_url = normalize_feed_url(candidate.url)
    source_title = body.title or candidate.title
    if source_title is None or not source_title.strip():
        raise HTTPException(
            status_code=422,
            detail="A nonblank source title is required.",
        )

    website_url = candidate.website_url
    source_domain = candidate.registrable_domain or registrable_domain(
        website_url or final_url
    )

    repository = SourceRepository(db)
    same_domain_sources = repository.get_sources_by_registrable_domain(
        source_domain
    )
    exact_existing = repository.get_source_by_url(final_url)
    if exact_existing is not None or any(
        normalize_feed_url(existing.url) == final_url
        for existing in same_domain_sources
    ):
        raise HTTPException(
            status_code=409, detail="Source URL already registered."
        )

    candidate_website_host = (
        normalize_host(website_url) if website_url else None
    )
    candidate_title = normalize_source_title(candidate.title)
    for existing in same_domain_sources:
        existing_website_host = (
            normalize_host(existing.website_url)
            if existing.website_url
            else None
        )
        if (
            candidate_website_host is not None
            and candidate_website_host == existing_website_host
        ) or (
            candidate_title is not None
            and candidate_title
            == normalize_source_title(existing.title)
        ):
            raise HTTPException(
                status_code=409,
                detail="A source from this publisher is already registered.",
            )

    source = repository.create_source(
        url=final_url,
        title=" ".join(source_title.split()),
        description=body.description or candidate.description,
        favicon=body.favicon or candidate.favicon,
        website_url=website_url,
        registrable_domain=source_domain,
        verified=False,
        submitted_by_user_id=body.submitted_by_user_id,
    )
    return source


@router.delete("/{source_id}", status_code=204)
def delete_source(
    source_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    repository = SourceRepository(db)
    deleted = repository.delete_source(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found.")


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: uuid.UUID, db: Session = Depends(get_db)
) -> SourceResponse:
    repository = SourceRepository(db)
    source = repository.get_source_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    return source


@router.patch("/{source_id}", response_model=SourceResponse)
def patch_source(
    source_id: uuid.UUID,
    body: SourcePatchRequest,
    db: Session = Depends(get_db),
) -> SourceResponse:
    repository = SourceRepository(db)
    current = repository.get_source_by_id(source_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Source not found.")

    patch_data = body.model_dump(exclude_unset=True)
    resolved_url = (
        str(patch_data["url"]) if "url" in patch_data else current.url
    )

    existing = repository.get_source_by_url(resolved_url)
    if existing is not None and existing.source_id != source_id:
        raise HTTPException(
            status_code=409, detail="Source URL already registered."
        )

    updated = repository.update_source(
        source_id=source_id,
        url=resolved_url,
        description=patch_data.get("description", current.description),
        favicon=patch_data.get("favicon", current.favicon),
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Source not found.")

    return updated
