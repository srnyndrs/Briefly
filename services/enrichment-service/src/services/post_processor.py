from dataclasses import replace
from typing import Any

from src.events.post_parsed import ParsedPostEvent, ParsedPostPayload
from src.repositories.stored_enrichment import StoredEnrichment
from src.services.classification import ArticleInput
from src.services.enrichment_service import EnrichmentService


class PostProcessor:
    def __init__(self, enrichment_service: EnrichmentService) -> None:
        self._enrichment_service = enrichment_service

    def process(self, event: Any) -> StoredEnrichment:
        parsed_event = ParsedPostEvent.model_validate(event)
        payload = parsed_event.payload
        return self._enrichment_service.enrich_article(
            payload.post_id,
            article_from_payload(payload),
            post_revision=payload.post_revision,
            correlation_id=parsed_event.correlation_id,
        )

    def mark_published(self, saved: StoredEnrichment) -> StoredEnrichment:
        if saved.event_id is None:
            raise RuntimeError("Published result has no saved event ID")

        self._enrichment_service.mark_published(saved.post_id, saved.event_id)

        return replace(saved, publication_pending=False)


def article_from_payload(payload: ParsedPostPayload) -> ArticleInput:
    return ArticleInput(
        title=payload.title,
        description=payload.description,
        body=payload.content,
        language=payload.language,
        source_category=payload.category,
        keywords=tuple(payload.keywords),
    )
