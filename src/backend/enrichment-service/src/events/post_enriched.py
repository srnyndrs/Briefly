"""Build the saved result event for one post revision."""

from datetime import UTC, datetime
from uuid import uuid4

from src.services.categories import (
    CATEGORY_TAXONOMY_VERSION,
    validate_category_ids,
)


def build_result_event(
    *,
    post_id: str,
    post_revision: int,
    enrichment_revision: int,
    input_hash: str,
    enrichment_version: str,
    status: str,
    category_ids: tuple[str, ...],
    processed_at: datetime,
    correlation_id: str,
) -> dict:
    categories = validate_category_ids(category_ids)
    if (
        type(post_revision) is not int
        or post_revision < 1
        or type(enrichment_revision) is not int
        or enrichment_revision < 1
        or (status == "completed" and not categories)
        or (status in ("abstained", "failed") and categories)
        or status not in ("completed", "abstained", "failed")
    ):
        raise ValueError("Invalid enrichment result status or revision")
    return {
        "event_id": str(uuid4()),
        "event_type": "post.enriched.v2",
        "schema_version": 2,
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
            "enrichment_revision": enrichment_revision,
            "input_hash": input_hash,
            "enrichment_version": enrichment_version,
            "taxonomy_version": CATEGORY_TAXONOMY_VERSION,
            "status": status,
            "category_ids": list(categories),
            "processed_at": processed_at.isoformat(),
        },
    }
