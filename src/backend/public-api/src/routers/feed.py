from datetime import datetime

from fastapi import APIRouter, Depends, Query

from src.adapters.service_clients import (
    ServiceClientError,
    map_service_error,
)
from src.routers.feed_common import (
    get_feed_service,
    to_post_list_item_response,
)
from src.schemas.api import FeedResponse, FilterOptionsResponse
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
    from_: datetime | None = Query(default=None, alias="from"),
    to_: datetime | None = Query(default=None, alias="to"),
    sort: str = Query(default="freshness"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    include_filter_options: bool = False,
) -> FeedResponse:
    try:
        output = service.get_explore_feed(
            ExploreFeedInput(
                user_id=user.user_id,
                limit=page_size,
                offset=(page - 1) * page_size,
                categories=categories,
                languages=languages,
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
