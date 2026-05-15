"""User profile and preferences routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Header

from src.repositories.service_clients import (
    ServiceClientError,
    account_get_preferences,
    account_get_user,
    account_patch_preferences,
    account_patch_profile,
    account_update_preferences,
    account_update_profile,
    map_service_error,
)
from src.schemas.api import (
    PreferencesPatchRequest,
    PreferencesResponse,
    PreferencesUpdateRequest,
    ProfilePatchRequest,
    ProfileResponse,
    ProfileUpdateRequest,
    UserResponse,
)
from src.services.auth import CurrentUser

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=UserResponse)
def get_me(user: CurrentUser) -> UserResponse:
    try:
        return UserResponse(**account_get_user(str(user.user_id)))
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.put("/profile", response_model=ProfileResponse)
def update_my_profile(
    body: ProfileUpdateRequest,
    user: CurrentUser,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> ProfileResponse:
    try:
        updated = account_update_profile(
            str(user.user_id),
            body.model_dump(mode="json"),
            correlation_id=x_correlation_id or str(uuid.uuid4()),
        )
        return ProfileResponse(**updated)
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


@router.put("/preferences", response_model=PreferencesResponse)
def update_my_preferences(
    body: PreferencesUpdateRequest,
    user: CurrentUser,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> PreferencesResponse:
    try:
        updated = account_update_preferences(
            str(user.user_id),
            body.model_dump(mode="json"),
            correlation_id=x_correlation_id or str(uuid.uuid4()),
        )
        return PreferencesResponse(**updated)
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
