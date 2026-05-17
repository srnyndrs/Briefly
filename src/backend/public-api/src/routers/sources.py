"""Subscription and source creation routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Response

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
    SubscriptionCreateRequest,
    SubscriptionResponse,
)
from src.services.auth import CurrentUser

router = APIRouter(tags=["users", "sources"])


@router.post("/sources", status_code=201, tags=["sources"])
def create_source(
    body: SourceCreateRequest, user: CurrentUser
) -> dict:
    _ = user
    try:
        return ingestion_create_source(body.model_dump())
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.get(
    "/sources",
    response_model=list[SourceResponse],
    tags=["sources"],
)
def list_sources(
    user: CurrentUser,
    subscribed_only: bool = False,
) -> list[SourceResponse]:
    """
    List news sources.
    By default, returns all available sources for discovery.
    If subscribed_only=True, only returns sources the user is subscribed to.
    """
    try:
        sources = ingestion_list_sources()

        if subscribed_only:
            subscriptions = account_list_subscriptions(
                str(user.user_id)
            )
            subscribed_ids = {
                str(s["source_id"]) for s in subscriptions
            }
            return [
                SourceResponse(**item)
                for item in sources
                if str(item["feed_id"]) in subscribed_ids
            ]

        return [SourceResponse(**item) for item in sources]
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post(
    "/sources/explore",
    response_model=list[SourceExploreResult],
    tags=["sources"],
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
    "/sources/{source_id}",
    response_model=SourceResponse,
    tags=["sources"],
)
def get_source(
    source_id: uuid.UUID, user: CurrentUser
) -> SourceResponse:
    _ = user
    try:
        return SourceResponse(
            **ingestion_get_source(str(source_id))
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.patch(
    "/sources/{source_id}",
    response_model=SourceResponse,
    tags=["sources"],
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


@router.delete(
    "/sources/{source_id}", status_code=204, tags=["sources"]
)
def delete_source(
    source_id: uuid.UUID, user: CurrentUser
) -> Response:
    _ = user
    try:
        ingestion_delete_source(str(source_id))
        return Response(status_code=204)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.get(
    "/me/subscriptions", response_model=list[SubscriptionResponse]
)
def list_my_subscriptions(
    user: CurrentUser,
) -> list[SubscriptionResponse]:
    try:
        subscriptions = account_list_subscriptions(
            str(user.user_id)
        )
        return [
            SubscriptionResponse(**item) for item in subscriptions
        ]
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post(
    "/me/subscriptions",
    response_model=SubscriptionResponse,
    status_code=201,
)
def create_my_subscription(
    body: SubscriptionCreateRequest,
    user: CurrentUser,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> SubscriptionResponse:
    try:
        created = account_create_subscription(
            str(user.user_id),
            body.model_dump(mode="json"),
            correlation_id=x_correlation_id or str(uuid.uuid4()),
        )
        return SubscriptionResponse(**created)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.delete("/me/subscriptions/{source_id}", status_code=204)
def delete_my_subscription(
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
