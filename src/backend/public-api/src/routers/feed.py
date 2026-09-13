import re
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.adapters.service_clients import (
    ServiceClientError,
    map_service_error,
)
from src.routers.feed_common import (
    get_feed_service,
    to_post_list_item_response,
)
from src.schemas.api import (
    FeedResponse,
    FilterOptionsResponse,
    SourceOptionResponse,
)
from src.services.auth import CurrentAdminUser, CurrentUser
from src.services.feed_service import (
    AdminFeedInput,
    ExploreFeedInput,
    FeedOutput,
    FeedService,
    PersonalFeedInput,
)

router = APIRouter(tags=["feed"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _normalize_search_query(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        raise HTTPException(
            status_code=422, detail="query must not be blank"
        )
    terms = re.findall(r'"([^"]+)"|([^\s]+)', normalized)
    has_term = any(
        re.search(r"[^\W_]", phrase or word, flags=re.UNICODE)
        and (phrase or word).lstrip("-").casefold() != "or"
        for phrase, word in terms
    )
    if not has_term:
        raise HTTPException(
            status_code=422, detail="query must contain a search term"
        )
    return normalized


def _response(
    output: FeedOutput, page: int, page_size: int
) -> FeedResponse:
    total_pages = (
        (output.total + page_size - 1) // page_size
        if output.total > 0
        else 0
    )
    options = (
        FilterOptionsResponse(
            categories=output.filter_options.categories,
            languages=output.filter_options.languages,
            sources=(
                [
                    SourceOptionResponse(
                        id=UUID(option.source_id), title=option.title
                    )
                    for option in output.filter_options.sources
                ]
                if output.filter_options.sources is not None
                else None
            ),
        )
        if output.filter_options is not None
        else None
    )
    return FeedResponse(
        items=[
            to_post_list_item_response(item) for item in output.items
        ],
        total=output.total,
        page=page,
        page_count=total_pages,
        page_size=page_size,
        filter_options=options,
    )


@router.get(
    "/feed",
    response_model=FeedResponse,
    response_model_exclude_none=True,
)
def get_feed(
    user: CurrentUser,
    service: FeedService = Depends(get_feed_service),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    include_filter_options: bool = False,
) -> FeedResponse:
    try:
        output = service.get_personal_feed(
            PersonalFeedInput(
                user_id=user.user_id,
                limit=page_size,
                offset=(page - 1) * page_size,
                category=category,
                include_filter_options=include_filter_options,
            )
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc
    return _response(output, page, page_size)


@router.get(
    "/explore",
    response_model=FeedResponse,
    response_model_exclude_none=True,
)
def get_explore(
    user: CurrentUser,
    service: FeedService = Depends(get_feed_service),
    categories: list[str] | None = Query(default=None),
    languages: list[str] | None = Query(default=None),
    source_ids: list[UUID] | None = Query(default=None),
    query: str | None = Query(default=None, max_length=200),
    from_: datetime | None = Query(default=None, alias="from"),
    to_: datetime | None = Query(default=None, alias="to"),
    sort: str | None = Query(
        default=None, pattern="^(freshness|oldest)$"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    include_filter_options: bool = False,
) -> FeedResponse:
    normalized_query = _normalize_search_query(query)
    if normalized_query is not None and sort is not None:
        raise HTTPException(
            status_code=422,
            detail="sort cannot be combined with query",
        )
    try:
        output = service.get_explore_feed(
            ExploreFeedInput(
                user_id=user.user_id,
                limit=page_size,
                offset=(page - 1) * page_size,
                categories=categories,
                languages=languages,
                source_ids=(
                    [str(source_id) for source_id in source_ids]
                    if source_ids is not None
                    else None
                ),
                query=normalized_query,
                published_from=from_,
                published_to=to_,
                sort=sort,
                include_filter_options=include_filter_options,
            )
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc
    return _response(output, page, page_size)


@admin_router.get(
    "/feed",
    response_model=FeedResponse,
    response_model_exclude_none=True,
)
def get_general_feed(
    admin_user: CurrentAdminUser,
    service: FeedService = Depends(get_feed_service),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> FeedResponse:
    _ = admin_user
    output = service.get_admin_feed(
        AdminFeedInput(limit=page_size, offset=(page - 1) * page_size)
    )
    return _response(output, page, page_size)
