import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.repositories.feed_repository import (
    PostRepository,
    UserPreferencesRepository,
)
from src.repositories.service_clients import (
    ServiceClientError,
    account_list_subscriptions,
    map_service_error,
)
from src.schemas.api import (
    FeedResponse,
    PostResponse,
)
from src.services.auth import CurrentAdminUser, CurrentUser
from src.services.feed_dtos import PostDTO
from src.services.feed_service import (
    FeedService,
    ListFeedInput,
    SearchFeedInput,
)

router = APIRouter(tags=["feed"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _to_post_response(item: PostDTO) -> PostResponse:
    return PostResponse(
        post_id=uuid.UUID(item.post_id),
        source_id=uuid.UUID(item.source_id)
        if item.source_id
        else None,
        title=item.title,
        source_title=item.source_title,
        description=item.description,
        canonical_url=item.canonical_url,
        language=item.language,
        category=item.category,
        image_ref=item.image_ref,
        published_at=item.published_at,
        has_content=item.content is not None,
        content=item.content,
    )


def get_feed_service(
    db: Session = Depends(get_db),
) -> FeedService:
    return FeedService(
        PostRepository(db),
        UserPreferencesRepository(db),
    )


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    user: CurrentUser,
    service: FeedService = Depends(get_feed_service),
    query: str | None = Query(
        default=None, description="Optional search query text"
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Items per page"
    ),
    page_count: int | None = Query(
        default=None, ge=1, le=100, alias="page_count", description="Alias for page_size"
    ),
    pageCount: int | None = Query(
        default=None, ge=1, le=100, alias="pageCount", description="Alias for page_size"
    ),
    use_profile: bool = True,
    categories: list[str] | None = Query(default=None),
    languages: list[str] | None = Query(default=None),
    source_ids: list[str] | None = Query(default=None),
    from_: datetime | None = Query(default=None, alias="from"),
    to_: datetime | None = Query(default=None, alias="to"),
    sort: str | None = None,
    subscribed_only: bool = False,
) -> FeedResponse:
    resolved_size = page_count or pageCount or page_size
    resolved_size = max(1, min(resolved_size, 100))
    resolved_page = max(1, page)
    offset = (resolved_page - 1) * resolved_size
    limit = resolved_size

    # If subscribed_only is True, filter to only subscribed sources
    filtered_source_ids = source_ids
    if subscribed_only:
        try:
            subscriptions = account_list_subscriptions(
                str(user.user_id)
            )
            subscribed_ids = [
                str(s["source_id"]) for s in subscriptions
            ]
            # If no subscriptions, return empty result
            if not subscribed_ids:
                return FeedResponse(
                    items=[],
                    total=0,
                    page=resolved_page,
                    page_count=0,
                    page_size=resolved_size,
                )
            # If source_ids are already provided, intersect with subscriptions
            if filtered_source_ids:
                filtered_source_ids = [
                    sid
                    for sid in filtered_source_ids
                    if sid in subscribed_ids
                ]
            else:
                filtered_source_ids = subscribed_ids
        except ServiceClientError as exc:
            raise map_service_error(exc) from exc

    if query and query.strip():
        output = service.search_feed(
            SearchFeedInput(
                user_id=user.user_id,
                q=query.strip(),
                limit=limit,
                offset=offset,
                use_profile=use_profile,
                categories=categories,
                languages=languages,
                source_ids=filtered_source_ids,
                published_from=from_,
                published_to=to_,
                sort=sort,
            )
        )
    else:
        output = service.list_feed(
            ListFeedInput(
                user_id=user.user_id,
                limit=limit,
                offset=offset,
                use_profile=use_profile,
                categories=categories,
                languages=languages,
                source_ids=filtered_source_ids,
                published_from=from_,
                published_to=to_,
                sort=sort,
            )
        )

    total_pages = (
        (output.total + resolved_size - 1) // resolved_size
        if output.total > 0
        else 0
    )
    return FeedResponse(
        items=[
            _to_post_response(item) for item in output.items
        ],
        total=output.total,
        page=resolved_page,
        page_count=total_pages,
        page_size=resolved_size,
    )


@admin_router.get("/feed", response_model=FeedResponse)
def get_general_feed(
    admin_user: CurrentAdminUser,
    service: FeedService = Depends(get_feed_service),
    page: int = Query(default=1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(
        default=20, ge=1, le=100, description="Items per page"
    ),
    page_count: int | None = Query(
        default=None, ge=1, le=100, alias="page_count", description="Alias for page_size"
    ),
    pageCount: int | None = Query(
        default=None, ge=1, le=100, alias="pageCount", description="Alias for page_size"
    ),
) -> FeedResponse:
    _ = admin_user
    resolved_size = page_count or pageCount or page_size
    resolved_size = max(1, min(resolved_size, 100))
    resolved_page = max(1, page)
    offset = (resolved_page - 1) * resolved_size
    limit = resolved_size

    output = service.list_feed(
        ListFeedInput(
            user_id=uuid.UUID(
                "00000000-0000-0000-0000-000000000000"
            ),
            limit=limit,
            offset=offset,
            use_profile=False,
        )
    )
    total_pages = (
        (output.total + resolved_size - 1) // resolved_size
        if output.total > 0
        else 0
    )
    return FeedResponse(
        items=[
            _to_post_response(item) for item in output.items
        ],
        total=output.total,
        page=resolved_page,
        page_count=total_pages,
        page_size=resolved_size,
    )
