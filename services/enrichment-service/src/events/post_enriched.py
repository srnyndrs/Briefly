"""Build the saved result event for one post revision."""

from typing import Any

from src.events.envelope import build_envelope
from src.repositories.stored_enrichment import StoredEnrichment
from src.services.categories import validate_category_ids


def build_enrichment_event(saved: StoredEnrichment) -> dict[str, Any]:
    """Build the same event on every attempt from the saved result."""
    if not saved.event_id:
        raise ValueError("Result has no saved event ID")
    categories = validate_category_ids(saved.category_ids)
    if (
        type(saved.post_revision) is not int
        or saved.post_revision < 1
        or type(saved.enrichment_revision) is not int
        or saved.enrichment_revision < 1
        or (saved.status == "completed" and not categories)
        or (saved.status in ("abstained", "failed") and categories)
        or saved.status not in ("completed", "abstained", "failed")
    ):
        raise ValueError("Invalid enrichment result status or revision")
    payload = {
        "post_id": str(saved.post_id),
        "post_revision": saved.post_revision,
        "enrichment_revision": saved.enrichment_revision,
        "status": saved.status,
        "category_ids": list(categories),
    }
    return build_envelope(
        event_type="post.enriched.v1",
        partition_key=f"post:{saved.post_id}",
        payload=payload,
        event_id=saved.event_id,
        occurred_at=saved.processed_at.isoformat(),
    )
