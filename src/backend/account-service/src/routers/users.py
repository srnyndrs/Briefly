import uuid

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Response,
    status,
)

from src.routers.deps import (
    correlation_id,
    get_account_service,
)
from src.schemas.users import (
    PreferencesPatchRequest,
    PreferencesResponse,
    PreferencesUpdateRequest,
    AccountPatchRequest,
    SubscriptionCreateRequest,
    SubscriptionResponse,
    UserResponse,
)
from src.services.account_service import (
    AccountService,
    ConflictError,
    NotFoundError,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: uuid.UUID,
    service: AccountService = Depends(get_account_service),
) -> UserResponse:
    try:
        user = service.get_user(str(user_id))
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def patch_user(
    user_id: uuid.UUID,
    body: AccountPatchRequest,
    service: AccountService = Depends(get_account_service),
) -> UserResponse:
    try:
        user = service.patch_display_name(
            user_id=str(user_id),
            fields=body.model_dump(mode="json", exclude_unset=True),
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}/preferences", response_model=PreferencesResponse
)
def get_preferences(
    user_id: uuid.UUID,
    service: AccountService = Depends(get_account_service),
) -> PreferencesResponse:
    try:
        preferences = service.get_preferences(str(user_id))
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return PreferencesResponse.model_validate(preferences)


@router.put(
    "/{user_id}/preferences", response_model=PreferencesResponse
)
def update_preferences(
    user_id: uuid.UUID,
    body: PreferencesUpdateRequest,
    service: AccountService = Depends(get_account_service),
    x_correlation_id: str | None = Header(default=None),
) -> PreferencesResponse:
    request_id = correlation_id(x_correlation_id)
    try:
        preferences = service.update_preferences(
            user_id=str(user_id),
            muted_keywords=body.muted_keywords,
            muted_categories=body.muted_categories,
            blocked_source_ids=[
                str(value) for value in body.blocked_source_ids
            ],
            languages=body.languages,
            correlation_id=request_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return PreferencesResponse.model_validate(preferences)


@router.patch(
    "/{user_id}/preferences", response_model=PreferencesResponse
)
def patch_preferences(
    user_id: uuid.UUID,
    body: PreferencesPatchRequest,
    service: AccountService = Depends(get_account_service),
    x_correlation_id: str | None = Header(default=None),
) -> PreferencesResponse:
    try:
        patch_data = body.model_dump(mode="json", exclude_unset=True)
        request_id = correlation_id(x_correlation_id)
        preferences = service.patch_preferences(
            user_id=str(user_id),
            fields=patch_data,
            correlation_id=request_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return PreferencesResponse.model_validate(preferences)


@router.post(
    "/{user_id}/subscriptions",
    response_model=SubscriptionResponse,
    status_code=201,
)
def create_subscription(
    user_id: uuid.UUID,
    body: SubscriptionCreateRequest,
    service: AccountService = Depends(get_account_service),
) -> SubscriptionResponse:
    try:
        subscription = service.create_subscription(
            user_id=str(user_id),
            source_id=str(body.source_id),
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return SubscriptionResponse.model_validate(subscription)


@router.get(
    "/{user_id}/subscriptions",
    response_model=list[SubscriptionResponse],
)
def list_subscriptions(
    user_id: uuid.UUID,
    service: AccountService = Depends(get_account_service),
) -> list[SubscriptionResponse]:
    try:
        subscriptions = service.list_subscriptions(str(user_id))
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return [
        SubscriptionResponse.model_validate(item)
        for item in subscriptions
    ]


@router.delete(
    "/{user_id}/subscriptions/{source_id}",
    status_code=204,
)
def delete_subscription(
    user_id: uuid.UUID,
    source_id: uuid.UUID,
    service: AccountService = Depends(get_account_service),
) -> Response:
    try:
        service.delete_subscription(
            user_id=str(user_id),
            source_id=str(source_id),
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return Response(status_code=204)
