import logging
from typing import Any

import httpx
from fastapi import HTTPException, status

from src.config.settings import settings

logger = logging.getLogger(__name__)


class ServiceClientError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _forward(
    method: str,
    base_url: str,
    path: str,
    *,
    json: dict | None = None,
    params: dict | None = None,
    correlation_id: str | None = None,
    timeout_seconds: float | None = None,
    internal_admin: bool = False,
) -> Any:
    headers: dict[str, str] = {}
    if correlation_id:
        headers["x-correlation-id"] = correlation_id
    if internal_admin:
        if not settings.internal_admin_token:
            raise ServiceClientError(503, "INTERNAL_ADMIN_TOKEN is not configured")
        headers["x-admin-token"] = settings.internal_admin_token

    url = f"{base_url}{path}"
    timeout = (
        settings.request_timeout_seconds
        if timeout_seconds is None
        else timeout_seconds
    )
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers,
            )
    except httpx.RequestError as exc:
        logger.warning("Upstream request failed: %s", exc)
        raise ServiceClientError(
            status.HTTP_502_BAD_GATEWAY,
            "Upstream service unavailable",
        ) from exc

    if response.status_code >= status.HTTP_400_BAD_REQUEST:
        detail = "Upstream service error"
        try:
            payload = response.json()
            detail = payload.get("detail", detail)
        except Exception:
            if response.text:
                detail = response.text

        raise ServiceClientError(response.status_code, detail)

    if response.status_code == status.HTTP_204_NO_CONTENT or not response.content:
        return {}

    return response.json()


def map_service_error(exc: ServiceClientError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.detail)


def account_get_user(user_id: str) -> dict:
    return _forward("GET", settings.account_service_url, f"/users/{user_id}")


def account_register(body: dict) -> dict:
    return _forward(
        "POST",
        settings.account_service_url,
        "/auth/register",
        json=body,
    )


def account_login(body: dict) -> dict:
    return _forward(
        "POST",
        settings.account_service_url,
        "/auth/login",
        json=body,
    )


def account_refresh(body: dict) -> dict:
    return _forward(
        "POST",
        settings.account_service_url,
        "/auth/refresh",
        json=body,
    )


def account_password_reset_request(body: dict) -> dict:
    return _forward(
        "POST",
        settings.account_service_url,
        "/auth/password-reset/request",
        json=body,
    )


def account_password_reset_confirm(body: dict) -> dict:
    return _forward(
        "POST",
        settings.account_service_url,
        "/auth/password-reset/confirm",
        json=body,
    )


def account_logout(body: dict, correlation_id: str | None = None) -> None:
    _forward(
        "POST",
        settings.account_service_url,
        "/auth/logout",
        json=body,
        correlation_id=correlation_id,
    )


def account_get_preferences(user_id: str) -> dict:
    return _forward(
        "GET",
        settings.account_service_url,
        f"/users/{user_id}/preferences",
    )


def account_list_subscriptions(user_id: str) -> list[dict]:
    result = _forward(
        "GET",
        settings.account_service_url,
        f"/users/{user_id}/subscriptions",
    )

    return result if isinstance(result, list) else []


def account_patch_user(user_id: str, body: dict) -> dict:
    return _forward(
        "PATCH",
        settings.account_service_url,
        f"/users/{user_id}",
        json=body,
    )


def account_patch_preferences(
    user_id: str, body: dict, correlation_id: str | None
) -> dict:
    return _forward(
        "PATCH",
        settings.account_service_url,
        f"/users/{user_id}/preferences",
        json=body,
        correlation_id=correlation_id,
    )


def account_create_subscription(user_id: str, body: dict) -> dict:
    return _forward(
        "POST",
        settings.account_service_url,
        f"/users/{user_id}/subscriptions",
        json=body,
    )


def account_delete_subscription(user_id: str, source_id: str) -> None:
    _forward(
        "DELETE",
        settings.account_service_url,
        f"/users/{user_id}/subscriptions/{source_id}",
    )


def crawler_create_source(body: dict) -> dict:
    return _forward(
        "POST",
        settings.crawler_service_url,
        "/sources",
        json=body,
        internal_admin=True,
    )


def crawler_list_sources(*, verified_only: bool = False) -> list[dict]:
    params = {"verified_only": "true"} if verified_only else None
    result = _forward(
        "GET", settings.crawler_service_url, "/sources", params=params
    )

    return result if isinstance(result, list) else []


def crawler_discover_sources(body: dict) -> list[dict]:
    result = _forward(
        "POST",
        settings.crawler_service_url,
        "/sources/discover",
        json=body,
        timeout_seconds=settings.source_discovery_timeout_seconds,
    )

    return result if isinstance(result, list) else []


def crawler_get_source(source_id: str) -> dict:
    return _forward(
        "GET",
        settings.crawler_service_url,
        f"/sources/{source_id}",
    )


def crawler_patch_source(source_id: str, body: dict) -> dict:
    return _forward(
        "PATCH",
        settings.crawler_service_url,
        f"/sources/{source_id}",
        json=body,
        internal_admin=True,
    )


def crawler_delete_source(source_id: str) -> None:
    _forward(
        "DELETE",
        settings.crawler_service_url,
        f"/sources/{source_id}",
        internal_admin=True,
    )


def content_get_post(post_id: str) -> dict:
    return _forward(
        "GET",
        settings.content_service_url,
        f"/posts/{post_id}",
    )


def content_patch_post(post_id: str, body: dict) -> dict:
    return _forward(
        "PATCH",
        settings.content_service_url,
        f"/posts/{post_id}",
        json=body,
        internal_admin=True,
    )


def content_delete_post(post_id: str) -> None:
    _forward(
        "DELETE",
        settings.content_service_url,
        f"/posts/{post_id}",
        internal_admin=True,
    )
