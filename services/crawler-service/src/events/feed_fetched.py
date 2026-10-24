"""Build the raw feed event produced after a successful fetch."""

from typing import Any
from uuid import UUID

from src.events.envelope import build_envelope


def build_feed_fetched_event(
    *,
    source_id: UUID,
    source_url: str,
    correlation_id: str,
    source_title: str,
    raw_xml: str,
) -> dict[str, Any]:
    return build_envelope(
        event_type="feed.raw_fetched.v1",
        partition_key=f"source:{source_id}",
        correlation_id=correlation_id,
        payload={
            "source_id": str(source_id),
            "source_url": source_url,
            "source_title": source_title,
            "raw_xml": raw_xml,
        },
    )
