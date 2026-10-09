"""Apply validated parsed-post events to the enrichment service."""

from dataclasses import replace
from typing import Any

from src.adapters.result_publisher import publish_result
from src.events.post_parsed import ParsedPostEvent
from src.repositories.enrichment_repository import StoredEnrichment
from src.services.classification import ArticleInput
from src.services.enrichment import EnrichmentService


class PostEventProcessor:
    def __init__(self, enrichment_service: EnrichmentService) -> None:
        self._enrichment_service = enrichment_service

    def __call__(self, event: Any) -> StoredEnrichment:
        parsed_event = ParsedPostEvent.model_validate(event)
        payload = parsed_event.payload
        return self._enrichment_service.enrich_article(
            payload.post_id,
            ArticleInput(
                title=payload.title,
                description=payload.description,
                body=payload.content,
                language=payload.language,
                source_category=payload.category,
                keywords=tuple(payload.keywords),
            ),
            post_revision=payload.post_revision,
            correlation_id=parsed_event.correlation_id,
        )

    @staticmethod
    def publish(saved: StoredEnrichment, channel: Any) -> None:
        """Publish a saved event on the broker connection's thread."""
        if saved.publication_pending:
            if saved.result_event is None or saved.event_id is None:
                raise RuntimeError("Pending result has no saved event")
            publish_result(channel, saved.result_event)

    def mark_published(self, saved: StoredEnrichment) -> StoredEnrichment:
        """Mark the confirmed event in a scoped worker database session."""
        if saved.event_id is None:
            raise RuntimeError("Published result has no saved event ID")
        self._enrichment_service.mark_published(saved.post_id, saved.event_id)
        return replace(saved, publication_pending=False)
