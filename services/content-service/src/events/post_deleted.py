from datetime import UTC, datetime
from typing import Any

from src.events.envelope import build_envelope


def build_post_deleted_event(
    *,
    post_id: str,
    post_revision: int,
    deleted_at: datetime,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    if deleted_at.tzinfo is None:
        deleted_at = deleted_at.replace(tzinfo=UTC)
    return build_envelope(
        event_type="post.deleted.v1",
        partition_key=f"post:{post_id}",
        correlation_id=correlation_id,
        payload={
            "post_id": post_id,
            "post_revision": post_revision,
            "deleted_at": deleted_at.isoformat(),
        },
    )
