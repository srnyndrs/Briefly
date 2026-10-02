"""Apply validated parsed-post events to the enrichment service."""

from typing import Any

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
            ),
            post_revision=payload.post_revision,
        )
