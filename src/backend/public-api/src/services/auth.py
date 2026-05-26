from typing import Annotated, Any
from uuid import UUID

from authlib.jose import JoseError, jwt
from fastapi import Depends, Header, HTTPException, status

from src.config.settings import settings
from src.schemas.api import AuthContext


def _decode_jwt(token: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(token, settings.jwt_secret)
        claims.validate()
        data = dict(claims)
    except JoseError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    if data.get("iss") != settings.jwt_issuer:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token issuer",
        )
    if data.get("aud") != settings.jwt_audience:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token audience",
        )
    if data.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token required",
        )

    return data


def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthContext:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header",
        )

    claims = _decode_jwt(token)
    try:
        raw_scopes = claims.get("scopes", [])
        if isinstance(raw_scopes, str):
            scopes = [
                scope for scope in raw_scopes.split(" ") if scope
            ]
        elif isinstance(raw_scopes, list):
            scopes = [str(scope) for scope in raw_scopes]
        else:
            scopes = []

        return AuthContext(
            user_id=UUID(claims["sub"]),
            token_type=claims["type"],
            token_version=int(claims.get("tv", 0)),
            scopes=scopes,
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims",
        ) from exc


CurrentUser = Annotated[AuthContext, Depends(get_current_user)]


def require_admin_user(user: CurrentUser) -> AuthContext:
    if "admin" not in user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin scope required",
        )
    return user


CurrentAdminUser = Annotated[
    AuthContext, Depends(require_admin_user)
]
