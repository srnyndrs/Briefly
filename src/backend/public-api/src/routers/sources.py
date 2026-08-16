import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Query, Response

from src.repositories.service_clients import (
    ServiceClientError,
    account_create_subscription,
    account_delete_subscription,
    account_list_subscriptions,
    ingestion_create_source,
    ingestion_delete_source,
    ingestion_explore_sources,
    ingestion_get_source,
    ingestion_list_sources,
    ingestion_patch_source,
    map_service_error,
)
from src.schemas.api import (
    SourceCreateRequest,
    SourceExploreRequest,
    SourceExploreResult,
    SourcePatchRequest,
    SourceResponse,
    SubscriptionResponse,
)
from src.services.auth import CurrentUser

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("", status_code=201)
def create_source(
    body: SourceCreateRequest, user: CurrentUser
) -> dict:
    _ = user
    try:
        return ingestion_create_source(body.model_dump())
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.get("", response_model=list[SourceResponse])
def list_sources(
    user: CurrentUser,
    query: str = Query(
        default="", description="Search text to filter sources"
    ),
    subscribed_only: bool = Query(
        default=False, description="Filter only subscribed sources"
    ),
) -> list[SourceResponse]:
    try:
        sources = ingestion_list_sources()
        subscriptions = account_list_subscriptions(
            str(user.user_id)
        )
        subscribed_ids = {
            str(s["source_id"]) for s in subscriptions
        }

        results = []
        for item in sources:
            is_sub = str(item["feed_id"]) in subscribed_ids
            if subscribed_only and not is_sub:
                continue

            source_response = SourceResponse(
                **item,
                is_subscribed=is_sub,
            )

            # Filter by search query if provided
            if query:
                search_fields = [
                    source_response.title or "",
                    source_response.description or "",
                    source_response.url or "",
                ]
                search_text = " ".join(search_fields).lower()
                if query.lower() in search_text:
                    results.append(source_response)
            else:
                results.append(source_response)

        return results
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post(
    "/explore",
    response_model=list[SourceExploreResult],
)
def explore_sources(
    body: SourceExploreRequest,
    user: CurrentUser,
) -> list[SourceExploreResult]:
    _ = user
    try:
        results = ingestion_explore_sources(
            body.model_dump(mode="json")
        )
        return [SourceExploreResult(**item) for item in results]
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.get(
    "/{source_id}",
    response_model=SourceResponse,
)
def get_source(
    source_id: uuid.UUID, user: CurrentUser
) -> SourceResponse:
    try:
        source_data = ingestion_get_source(str(source_id))
        subscriptions = account_list_subscriptions(
            str(user.user_id)
        )
        subscribed_ids = {
            str(s["source_id"]) for s in subscriptions
        }

        return SourceResponse(
            **source_data,
            is_subscribed=str(source_data["feed_id"])
            in subscribed_ids,
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.patch(
    "/{source_id}",
    response_model=SourceResponse,
)
def patch_source(
    source_id: uuid.UUID,
    body: SourcePatchRequest,
    user: CurrentUser,
) -> SourceResponse:
    _ = user
    try:
        updated = ingestion_patch_source(
            str(source_id),
            body.model_dump(mode="json", exclude_unset=True),
        )
        return SourceResponse(**updated)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.delete("/{source_id}", status_code=204)
def delete_source(
    source_id: uuid.UUID, user: CurrentUser
) -> Response:
    _ = user
    try:
        ingestion_delete_source(str(source_id))
        return Response(status_code=204)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post(
    "/{source_id}/subscription",
    response_model=SubscriptionResponse,
    status_code=201,
)
def create_source_subscription(
    source_id: uuid.UUID,
    user: CurrentUser,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> SubscriptionResponse:
    try:
        created = account_create_subscription(
            str(user.user_id),
            {"source_id": str(source_id)},
            correlation_id=x_correlation_id or str(uuid.uuid4()),
        )
        return SubscriptionResponse(**created)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.delete(
    "/{source_id}/subscription",
    status_code=204,
)
def delete_source_subscription(
    source_id: uuid.UUID,
    user: CurrentUser,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> Response:
    try:
        account_delete_subscription(
            str(user.user_id),
            str(source_id),
            correlation_id=x_correlation_id or str(uuid.uuid4()),
        )
        return Response(status_code=204)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc
