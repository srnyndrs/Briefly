"""Build the saved result event for one post revision."""

from datetime import UTC, datetime
from uuid import uuid4

from src.services.categories import CATEGORY_TAXONOMY_VERSION


def build_result_event(
    *,
    post_id: str,
    post_revision: int,
    input_hash: str,
    enrichment_version: str,
    status: str,
    category_id: str | None,
    processed_at: datetime,
    correlation_id: str,
) -> dict:
    return {
        "event_id": str(uuid4()),
        "event_type": "post.enriched.v1",
        "schema_version": 1,
        "occurred_at": datetime.now(UTC).isoformat(),
        "producer": "enrichment-service",
        "correlation_id": correlation_id,
        "partition_key": f"post:{post_id}",
        "trace": {
            "trace_id": uuid4().hex,
            "span_id": uuid4().hex[:16],
        },
        "payload": {
            "post_id": post_id,
            "post_revision": post_revision,
            "input_hash": input_hash,
            "enrichment_version": enrichment_version,
            "taxonomy_version": CATEGORY_TAXONOMY_VERSION,
            "status": status,
            "category_id": category_id,
            "processed_at": processed_at.isoformat(),
        },
    }
