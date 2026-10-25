from typing import Any
from uuid import UUID

from src.events.envelope import build_envelope

_FEED_EVENT_TYPE = "feed.raw_fetched.v1"


def build_feed_fetched_event(
    *,
    source_id: UUID,
    source_url: str,
    correlation_id: str,
    source_title: str,
    raw_xml: str,
) -> dict[str, Any]:
    payload = {
        "source_id": str(source_id),
        "source_url": source_url,
        "source_title": source_title,
        "raw_xml": raw_xml,
    }

    return build_envelope(
        event_type=_FEED_EVENT_TYPE,
        partition_key=f"source:{source_id}",
        payload=payload,
        correlation_id=correlation_id,
    )
