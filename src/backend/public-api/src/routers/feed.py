"""Feed and article routes (list, search, get article)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.repositories.feed_repository import (
    ArticleRepository,
    UserPreferencesRepository,
)
from src.repositories.service_clients import (
    ServiceClientError,
    content_articles_count,
    content_get_article,
    content_list_articles,
    map_service_error,
)
from src.schemas.api import (
    AdminArticleResponse,
    ArticleCountResponse,
    ArticleResponse,
    FeedItemResponse,
    FeedResponse,
)
from src.services.auth import CurrentAdminUser, CurrentUser
from src.services.feed_dtos import FeedItemDTO
from src.services.feed_service import (
    FeedService,
    GetArticleInput,
    ListFeedInput,
    SearchFeedInput,
)

router = APIRouter(prefix="/feed", tags=["feed"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


def _to_feed_item_response(item: FeedItemDTO) -> FeedItemResponse:
    return FeedItemResponse(
        article_id=uuid.UUID(item.article_id),
        title=item.title,
        source_title=item.source_title,
        description=item.description,
        canonical_url=item.canonical_url,
        language=item.language,
        category=item.category,
        image_ref=item.image_ref,
        published_at=item.published_at,
    )


def _to_article_response(item: FeedItemDTO) -> ArticleResponse:
    feed_item = _to_feed_item_response(item)
    return ArticleResponse(
        **feed_item.model_dump(),
        content=item.content,
    )


def get_feed_service(
    db: Session = Depends(get_db),
) -> FeedService:
    return FeedService(
        ArticleRepository(db),
        UserPreferencesRepository(db),
    )


@router.get("", response_model=FeedResponse)
def get_feed(
    user: CurrentUser,
    service: FeedService = Depends(get_feed_service),
    limit: int = 20,
    offset: int = 0,
    use_profile: bool = True,
    categories: list[str] | None = Query(default=None),
    languages: list[str] | None = Query(default=None),
    exclude_languages: list[str] | None = Query(default=None),
    source_ids: list[str] | None = Query(default=None),
    from_: datetime | None = Query(default=None, alias="from"),
    to_: datetime | None = Query(default=None, alias="to"),
    sort: str | None = None,
) -> FeedResponse:
    output = service.list_feed(
        ListFeedInput(
            user_id=user.user_id,
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
            use_profile=use_profile,
            categories=categories,
            languages=languages,
            exclude_languages=exclude_languages,
            source_ids=source_ids,
            published_from=from_,
            published_to=to_,
            sort=sort,
        )
    )
    return FeedResponse(
        items=[
            _to_feed_item_response(item) for item in output.items
        ],
        total=output.total,
    )


@router.get("/search", response_model=FeedResponse)
def feed_search(
    q: str,
    user: CurrentUser,
    service: FeedService = Depends(get_feed_service),
    limit: int = 20,
    offset: int = 0,
    use_profile: bool = True,
    categories: list[str] | None = Query(default=None),
    languages: list[str] | None = Query(default=None),
    exclude_languages: list[str] | None = Query(default=None),
    source_ids: list[str] | None = Query(default=None),
    from_: datetime | None = Query(default=None, alias="from"),
    to_: datetime | None = Query(default=None, alias="to"),
    sort: str | None = None,
) -> FeedResponse:
    q = q.strip()
    if not q:
        raise HTTPException(
            status_code=400, detail="Query cannot be empty"
        )

    output = service.search_feed(
        SearchFeedInput(
            user_id=user.user_id,
            q=q,
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
            use_profile=use_profile,
            categories=categories,
            languages=languages,
            exclude_languages=exclude_languages,
            source_ids=source_ids,
            published_from=from_,
            published_to=to_,
            sort=sort,
        )
    )
    return FeedResponse(
        items=[
            _to_feed_item_response(item) for item in output.items
        ],
        total=output.total,
    )


@router.get(
    "/articles/{article_id}",
    response_model=ArticleResponse,
    tags=["feed"],
)
def get_article_by_id(
    article_id: uuid.UUID,
    user: CurrentUser,
    service: FeedService = Depends(get_feed_service),
) -> ArticleResponse:
    _ = user
    item = service.get_article(
        GetArticleInput(article_id=article_id)
    )
    if item is None:
        raise HTTPException(
            status_code=404, detail="Article not found"
        )
    return _to_article_response(item)


@admin_router.get("/feed", response_model=FeedResponse)
def get_general_feed(
    admin_user: CurrentAdminUser,
    service: FeedService = Depends(get_feed_service),
    limit: int = 20,
    offset: int = 0,
) -> FeedResponse:
    _ = admin_user
    output = service.list_feed(
        ListFeedInput(
            user_id=uuid.UUID(
                "00000000-0000-0000-0000-000000000000"
            ),
            limit=max(1, min(limit, 100)),
            offset=max(0, offset),
            use_profile=False,
        )
    )
    return FeedResponse(
        items=[
            _to_feed_item_response(item) for item in output.items
        ],
        total=output.total,
    )


@admin_router.get(
    "/articles/count", response_model=ArticleCountResponse
)
def admin_article_count(
    admin_user: CurrentAdminUser,
) -> ArticleCountResponse:
    _ = admin_user
    try:
        return ArticleCountResponse(**content_articles_count())
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@admin_router.get(
    "/articles", response_model=list[AdminArticleResponse]
)
def admin_list_articles(
    admin_user: CurrentAdminUser,
    limit: int = 20,
    skip: int = 0,
    source_id: str | None = None,
    language: str | None = None,
    category: str | None = None,
    published_from: datetime | None = None,
    published_to: datetime | None = None,
    parsed_from: datetime | None = None,
    parsed_to: datetime | None = None,
) -> list[AdminArticleResponse]:
    _ = admin_user
    params: dict[str, str | int] = {
        "limit": max(1, min(limit, 200)),
        "skip": max(0, skip),
    }
    if source_id:
        params["source_id"] = source_id
    if language:
        params["language"] = language
    if category:
        params["category"] = category
    if published_from:
        params["published_from"] = published_from.isoformat()
    if published_to:
        params["published_to"] = published_to.isoformat()
    if parsed_from:
        params["parsed_from"] = parsed_from.isoformat()
    if parsed_to:
        params["parsed_to"] = parsed_to.isoformat()

    try:
        rows = content_list_articles(params)
        return [AdminArticleResponse(**row) for row in rows]
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@admin_router.get(
    "/articles/{article_id}", response_model=AdminArticleResponse
)
def admin_get_article(
    article_id: str,
    admin_user: CurrentAdminUser,
) -> AdminArticleResponse:
    _ = admin_user
    try:
        return AdminArticleResponse(
            **content_get_article(article_id)
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc
