from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.adapters.service_clients import (
    ServiceClientError,
    content_delete_post,
    content_get_post,
    content_patch_post,
    map_service_error,
)
from src.routers.feed_common import (
    get_feed_service,
    to_post_response,
)
from src.schemas.api import (
    AdminPostPatchRequest,
    AdminPostPatchResponse,
    AdminPostResponse,
    PostResponse,
)
from src.services.auth import CurrentAdminUser, CurrentUser
from src.services.feed_service import FeedService

router = APIRouter(prefix="/posts", tags=["posts"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/{post_id}",
    response_model=PostResponse,
)
def get_post_by_id(
    post_id: UUID,
    user: CurrentUser,
    service: FeedService = Depends(get_feed_service),
) -> PostResponse:
    _ = user
    item = service.get_post(post_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return to_post_response(item)


@admin_router.get("/posts/{post_id}", response_model=AdminPostResponse)
def admin_get_post(
    post_id: UUID,
    admin_user: CurrentAdminUser,
) -> AdminPostResponse:
    _ = admin_user
    try:
        res = content_get_post(str(post_id))

        return AdminPostResponse(**res)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@admin_router.patch("/posts/{post_id}", response_model=AdminPostPatchResponse)
def admin_patch_post(
    post_id: UUID,
    body: AdminPostPatchRequest,
    admin_user: CurrentAdminUser,
) -> AdminPostPatchResponse:
    _ = admin_user
    try:
        updated = content_patch_post(
            str(post_id), body.model_dump(mode="json", exclude_unset=True)
        )
        return AdminPostPatchResponse(**updated)
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc


@admin_router.delete("/posts/{post_id}", status_code=204)
def admin_delete_post(
    post_id: UUID,
    admin_user: CurrentAdminUser,
) -> None:
    _ = admin_user
    try:
        content_delete_post(str(post_id))
    except ServiceClientError as exc:
        raise map_service_error(exc) from exc
