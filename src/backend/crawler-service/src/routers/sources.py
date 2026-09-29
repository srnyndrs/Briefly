import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.adapters.source_discovery import (
    SourceDiscoveryAdapter,
    normalize_feed_url,
)
from src.config.database import get_db
from src.config.settings import settings
from src.repositories.source_repository import (
    SourceRepository,
)
from src.schemas.sources import (
    SourceCreateRequest,
    SourceDiscoverRequest,
    SourceDiscoverResponse,
    SourcePatchRequest,
    SourceResponse,
)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
def list_sources(
    active_only: bool = False,
    verified_only: bool = False,
    db: Session = Depends(get_db),
) -> list[SourceResponse]:
    repository = SourceRepository(db)
    sources = (
        repository.get_active_sources(
            now=datetime.now(timezone.utc),
            max_retries=settings.max_retries,
            verified_only=verified_only,
        )
        if active_only
        else repository.get_sources(verified_only=verified_only)
    )

    return [SourceResponse.model_validate(source) for source in sources]


@router.post("/discover", response_model=list[SourceDiscoverResponse])
def discover_sources_endpoint(
    body: SourceDiscoverRequest,
) -> list[SourceDiscoverResponse]:
    return SourceDiscoveryAdapter().discover(str(body.url))


@router.post("", response_model=SourceResponse, status_code=201)
def register_source(
    body: SourceCreateRequest,
    db: Session = Depends(get_db),
) -> SourceResponse:
    try:
        final_url = normalize_feed_url(str(body.url))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    repository = SourceRepository(db)
    if repository.get_source_by_url(final_url) is not None:
        raise HTTPException(
            status_code=409, detail="Source URL already registered."
        )

    source = repository.create_source(
        url=final_url,
        title=body.title,
        description=body.description,
        favicon=str(body.favicon) if body.favicon else None,
        verified=False,
        submitted_by_user_id=body.submitted_by_user_id,
    )

    return SourceResponse.model_validate(source)


@router.delete("/{source_id}", status_code=204)
def delete_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> None:
    repository = SourceRepository(db)
    deleted = repository.delete_source(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found.")


@router.get("/{source_id}", response_model=SourceResponse)
def get_source(
    source_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> SourceResponse:
    repository = SourceRepository(db)
    source = repository.get_source_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")

    return SourceResponse.model_validate(source)


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

    patch_data = body.model_dump(mode="json", exclude_unset=True)
    try:
        resolved_url = normalize_feed_url(patch_data.get("url", current.url))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    existing = repository.get_source_by_url(resolved_url)
    if existing is not None and existing.source_id != source_id:
        raise HTTPException(
            status_code=409, detail="Source URL already registered."
        )

    updated = repository.update_source(
        source_id=source_id,
        url=resolved_url,
        title=patch_data.get("title", current.title),
        description=patch_data.get("description", current.description),
        favicon=patch_data.get("favicon", current.favicon),
    )
    if updated is None:
        raise HTTPException(status_code=404, detail="Source not found.")

    return SourceResponse.model_validate(updated)
