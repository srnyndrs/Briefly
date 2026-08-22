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
    trace_ids,
)
from src.schemas.users import (
    PreferencesPatchRequest,
    PreferencesResponse,
    PreferencesUpdateRequest,
    ProfileResponse,
    ProfileUpdateRequest,
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
    return UserResponse(
        user_id=uuid.UUID(user.user_id),
        email=user.email,
        status=user.status,
        created_at=user.created_at,
    )


@router.get("/{user_id}/profile", response_model=ProfileResponse)
def get_profile(
    user_id: uuid.UUID,
    service: AccountService = Depends(get_account_service),
) -> ProfileResponse:
    try:
        profile = service.get_profile(str(user_id))
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return ProfileResponse(
        user_id=user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        updated_at=profile.updated_at,
    )


@router.put("/{user_id}/profile", response_model=ProfileResponse)
def update_profile(
    user_id: uuid.UUID,
    body: ProfileUpdateRequest,
    service: AccountService = Depends(get_account_service),
    x_correlation_id: str | None = Header(default=None),
) -> ProfileResponse:
    request_id = correlation_id(x_correlation_id)
    trace_id, span_id = trace_ids(request_id)
    try:
        profile = service.update_profile(
            user_id=str(user_id),
            display_name=body.display_name,
            bio=body.bio,
            avatar_url=body.avatar_url,
            correlation_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return ProfileResponse(
        user_id=user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        updated_at=profile.updated_at,
    )


@router.patch("/{user_id}/profile", response_model=ProfileResponse)
def patch_profile(
    user_id: uuid.UUID,
    body: ProfileUpdateRequest,
    service: AccountService = Depends(get_account_service),
    x_correlation_id: str | None = Header(default=None),
) -> ProfileResponse:
    try:
        existing = service.get_profile(str(user_id))
        patch_data = body.model_dump(
            mode="json", exclude_unset=True
        )
        request_id = correlation_id(x_correlation_id)
        trace_id, span_id = trace_ids(request_id)
        profile = service.update_profile(
            user_id=str(user_id),
            display_name=patch_data.get(
                "display_name", existing.display_name
            ),
            bio=patch_data.get("bio", existing.bio),
            avatar_url=patch_data.get(
                "avatar_url", existing.avatar_url
            ),
            correlation_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return ProfileResponse(
        user_id=user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        updated_at=profile.updated_at,
    )


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
    return PreferencesResponse(
        user_id=user_id,
        muted_keywords=preferences.muted_keywords,
        muted_categories=preferences.muted_categories,
        blocked_source_ids=[
            uuid.UUID(value)
            for value in preferences.blocked_source_ids
        ],
        languages=preferences.languages,
        category_interests=preferences.category_interests,
        updated_at=preferences.updated_at,
    )


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
    trace_id, span_id = trace_ids(request_id)
    try:
        preferences = service.update_preferences(
            user_id=str(user_id),
            muted_keywords=body.muted_keywords,
            muted_categories=body.muted_categories,
            blocked_source_ids=[
                str(value) for value in body.blocked_source_ids
            ],
            languages=body.languages,
            category_interests=body.category_interests,
            correlation_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return PreferencesResponse(
        user_id=user_id,
        muted_keywords=preferences.muted_keywords,
        muted_categories=preferences.muted_categories,
        blocked_source_ids=[
            uuid.UUID(value)
            for value in preferences.blocked_source_ids
        ],
        languages=preferences.languages,
        category_interests=preferences.category_interests,
        updated_at=preferences.updated_at,
    )


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
        existing = service.get_preferences(str(user_id))
        patch_data = body.model_dump(
            mode="json", exclude_unset=True
        )
        request_id = correlation_id(x_correlation_id)
        trace_id, span_id = trace_ids(request_id)
        preferences = service.update_preferences(
            user_id=str(user_id),
            muted_keywords=patch_data.get(
                "muted_keywords",
                existing.muted_keywords,
            ),
            muted_categories=patch_data.get(
                "muted_categories",
                existing.muted_categories,
            ),
            blocked_source_ids=[
                str(value)
                for value in patch_data.get(
                    "blocked_source_ids",
                    existing.blocked_source_ids,
                )
            ],
            languages=patch_data.get(
                "languages",
                existing.languages,
            ),
            category_interests=patch_data.get(
                "category_interests",
                existing.category_interests,
            ),
            correlation_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc

    return PreferencesResponse(
        user_id=user_id,
        muted_keywords=preferences.muted_keywords,
        muted_categories=preferences.muted_categories,
        blocked_source_ids=[
            uuid.UUID(value)
            for value in preferences.blocked_source_ids
        ],
        languages=preferences.languages,
        category_interests=preferences.category_interests,
        updated_at=preferences.updated_at,
    )


@router.post(
    "/{user_id}/subscriptions",
    response_model=SubscriptionResponse,
    status_code=201,
)
def create_subscription(
    user_id: uuid.UUID,
    body: SubscriptionCreateRequest,
    service: AccountService = Depends(get_account_service),
    x_correlation_id: str | None = Header(default=None),
) -> SubscriptionResponse:
    request_id = correlation_id(x_correlation_id)
    trace_id, span_id = trace_ids(request_id)
    try:
        subscription = service.create_subscription(
            user_id=str(user_id),
            source_id=str(body.source_id),
            correlation_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return SubscriptionResponse(
        user_id=user_id,
        source_id=body.source_id,
        created_at=subscription.created_at,
    )


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
        SubscriptionResponse(
            user_id=uuid.UUID(item.user_id),
            source_id=uuid.UUID(item.source_id),
            created_at=item.created_at,
        )
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
    x_correlation_id: str | None = Header(default=None),
) -> Response:
    request_id = correlation_id(x_correlation_id)
    trace_id, span_id = trace_ids(request_id)
    try:
        service.delete_subscription(
            user_id=str(user_id),
            source_id=str(source_id),
            correlation_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return Response(status_code=204)
