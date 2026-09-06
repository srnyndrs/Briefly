import uuid
from typing import Annotated

from fastapi import APIRouter, Header, Response

from src.adapters.service_clients import (
    ServiceClientError,
    account_login,
    account_logout,
    account_password_reset_confirm,
    account_password_reset_request,
    account_refresh,
    account_register,
    map_service_error,
)
from src.schemas.api import (
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    RegisterRequest,
    StatusResponse,
    TokenPairResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=TokenPairResponse, status_code=201
)
def register(body: RegisterRequest) -> TokenPairResponse:
    try:
        return TokenPairResponse(
            **account_register(body.model_dump(mode="json"))
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post("/login", response_model=TokenPairResponse)
def login(body: LoginRequest) -> TokenPairResponse:
    try:
        return TokenPairResponse(
            **account_login(body.model_dump(mode="json"))
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post("/refresh", response_model=TokenPairResponse)
def refresh(body: RefreshRequest) -> TokenPairResponse:
    try:
        return TokenPairResponse(
            **account_refresh(body.model_dump(mode="json"))
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post(
    "/password-reset/request",
    response_model=PasswordResetRequestResponse,
)
def password_reset_request(
    body: PasswordResetRequest,
) -> PasswordResetRequestResponse:
    try:
        return PasswordResetRequestResponse(
            **account_password_reset_request(
                body.model_dump(mode="json")
            )
        )
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post("/password-reset/confirm", response_model=StatusResponse)
def password_reset_confirm(
    body: PasswordResetConfirmRequest,
) -> StatusResponse:
    try:
        result = account_password_reset_confirm(
            body.model_dump(mode="json")
        )
        return StatusResponse(**result)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@router.post("/logout", status_code=204)
def logout(
    body: LogoutRequest,
    x_correlation_id: Annotated[str | None, Header()] = None,
) -> Response:
    try:
        account_logout(
            body.model_dump(mode="json"),
            correlation_id=x_correlation_id or str(uuid.uuid4()),
        )
        return Response(status_code=204)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc
