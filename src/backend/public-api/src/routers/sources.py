import uuid

from fastapi import APIRouter, Query, Response

from src.adapters.service_clients import (
    ServiceClientError,
    account_list_subscriptions,
    ingestion_create_source,
    ingestion_delete_source,
    ingestion_discover_sources,
    ingestion_get_source,
    ingestion_list_sources,
    ingestion_patch_source,
    map_service_error,
)
from src.schemas.api import (
    SourceCreateRequest,
    SourceDiscoverRequest,
    SourceDiscoverResult,
    SourcePatchRequest,
    SourceResponse,
)
from src.services.auth import CurrentUser

router = APIRouter(prefix="/sources", tags=["sources"])


@router.post("", status_code=201)
def create_source(
    body: SourceCreateRequest, user: CurrentUser
) -> dict:
    _ = user
    try:
        return ingestion_create_source(body.model_dump(mode="json"))
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
            source_id_val = str(item["source_id"])
            is_sub = source_id_val in subscribed_ids
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
    "/discover",
    response_model=list[SourceDiscoverResult],
)
def discover_sources(
    body: SourceDiscoverRequest,
    user: CurrentUser,
) -> list[SourceDiscoverResult]:
    _ = user
    try:
        results = ingestion_discover_sources(
            body.model_dump(mode="json")
        )
        return [SourceDiscoverResult(**item) for item in results]
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
            is_subscribed=str(source_data["source_id"])
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
