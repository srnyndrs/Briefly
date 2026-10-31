from typing import Annotated

from fastapi import Header, HTTPException

from src.config.settings import settings


def require_internal_admin_token(
    x_admin_token: Annotated[str | None, Header(alias="x-admin-token")] = None,
) -> None:
    if (
        not settings.internal_admin_token
        or x_admin_token != settings.internal_admin_token
    ):
        raise HTTPException(status_code=401, detail="Unauthorized")
