import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Response

from src.repositories.service_clients import (
    ServiceClientError,
    account_create_subscription,
    account_delete_subscription,
    account_get_preferences,
    account_get_profile,
    account_get_user,
    account_list_subscriptions,
    account_patch_preferences,
    account_patch_profile,
    map_service_error,
)
from src.schemas.api import (
    MeDetailsResponse,
    PreferencesPatchRequest,
    PreferencesResponse,
    ProfilePatchRequest,
    ProfileResponse,
    SubscriptionCreateRequest,
    SubscriptionResponse,
)
from src.services.auth import CurrentUser

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=MeDetailsResponse)
def get_me(user: CurrentUser) -> MeDetailsResponse:
    try:
        user_data = account_get_user(str(user.user_id))

        profile_data = None
        try:
            profile_data = account_get_profile(str(user.user_id))
        except ServiceClientError as exc:
            if exc.status_code != 404:
                raise map_service_error(exc) from exc

        prefs_data = None
        try:
            prefs_data = account_get_preferences(str(user.user_id))
        except ServiceClientError as exc:
            if exc.status_code != 404:
                raise map_service_error(exc) from exc

        return MeDetailsResponse(
            **user_data,
            profile=ProfileResponse(**profile_data)
            if profile_data
            else None,
            preferences=PreferencesResponse(**prefs_data)
            if prefs_data
            else None,
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.patch("/profile", response_model=ProfileResponse)
def patch_my_profile(
    body: ProfilePatchRequest,
    user: CurrentUser,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> ProfileResponse:
    try:
        updated = account_patch_profile(
            str(user.user_id),
            body.model_dump(mode="json", exclude_unset=True),
            correlation_id=x_correlation_id or str(uuid.uuid4()),
        )
        return ProfileResponse(**updated)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.get("/preferences", response_model=PreferencesResponse)
def get_my_preferences(user: CurrentUser) -> PreferencesResponse:
    try:
        return PreferencesResponse(
            **account_get_preferences(str(user.user_id))
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.patch("/preferences", response_model=PreferencesResponse)
def patch_my_preferences(
    body: PreferencesPatchRequest,
    user: CurrentUser,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> PreferencesResponse:
    try:
        updated = account_patch_preferences(
            str(user.user_id),
            body.model_dump(mode="json", exclude_unset=True),
            correlation_id=x_correlation_id or str(uuid.uuid4()),
        )
        return PreferencesResponse(**updated)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.get(
    "/subscriptions",
    response_model=list[SubscriptionResponse],
)
def get_my_subscriptions(
    user: CurrentUser,
) -> list[SubscriptionResponse]:
    try:
        subscriptions = account_list_subscriptions(str(user.user_id))
        return [SubscriptionResponse(**item) for item in subscriptions]
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post(
    "/subscriptions",
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
            {"source_id": str(body.source_id)},
            correlation_id=x_correlation_id or str(uuid.uuid4()),
        )
        return SubscriptionResponse(**created)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.delete(
    "/subscriptions/{source_id}",
    status_code=204,
)
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

