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
from src.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)
from src.schemas.common import StatusResponse
from src.services.account_service import (
    AccountService,
    ConflictError,
)
from src.services.auth_service import AuthError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=TokenPairResponse, status_code=201
)
def register(
    body: RegisterRequest,
    service: AccountService = Depends(get_account_service),
    x_correlation_id: str | None = Header(default=None),
) -> TokenPairResponse:
    request_id = correlation_id(x_correlation_id)
    trace_id, span_id = trace_ids(request_id)
    try:
        access_token, refresh_token = service.register_user(
            username=body.username,
            email=body.email,
            password=body.password,
            correlation_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
        )
    except ConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenPairResponse)
def login(
    body: LoginRequest,
    service: AccountService = Depends(get_account_service),
) -> TokenPairResponse:
    try:
        access_token, refresh_token = service.login(
            email=body.email, password=body.password
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenPairResponse)
def refresh(
    body: RefreshRequest,
    service: AccountService = Depends(get_account_service),
) -> TokenPairResponse:
    try:
        access_token, refresh_token = service.refresh_tokens(
            body.refresh_token
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/password-reset/request",
    response_model=PasswordResetRequestResponse,
)
def password_reset_request(
    body: PasswordResetRequest,
    service: AccountService = Depends(get_account_service),
) -> PasswordResetRequestResponse:
    token = service.password_reset_request(body.email)
    return PasswordResetRequestResponse(
        status="accepted", reset_token=token
    )


@router.post(
    "/password-reset/confirm",
    response_model=StatusResponse,
)
def password_reset_confirm(
    body: PasswordResetConfirmRequest,
    service: AccountService = Depends(get_account_service),
) -> StatusResponse:
    try:
        service.password_reset_confirm(
            reset_token=body.reset_token,
            new_password=body.new_password,
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return StatusResponse(status="ok")


@router.post("/logout", status_code=204)
def logout(
    body: LogoutRequest,
    service: AccountService = Depends(get_account_service),
    x_correlation_id: str | None = Header(default=None),
) -> Response:
    request_id = correlation_id(x_correlation_id)
    trace_id, span_id = trace_ids(request_id)
    try:
        service.logout(
            refresh_token=body.refresh_token,
            reason=body.reason,
            correlation_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    return Response(status_code=204)
