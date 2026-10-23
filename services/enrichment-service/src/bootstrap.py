"""Compose the concrete Ollama runtime and its saved-result identity."""

import logging

from src.adapters.ollama_provider import OllamaProvider
from src.config.database import SessionLocal
from src.config.settings import settings
from src.repositories.enrichment_repository import EnrichmentRepository
from src.services.classification import ArticleInput
from src.services.enrichment_service import (
    EnrichmentService,
)
from src.services.post_processor import PostProcessor
from src.services.provider import instructions

logger = logging.getLogger(__name__)


def create_enrichment_service() -> EnrichmentService:
    """Use the configured model and the existing scoped repository sessions."""
    if not settings.ollama_model or not settings.ollama_model.strip():
        raise ValueError("OLLAMA_MODEL is required for runtime enrichment")
    prompt = instructions([])
    provider = OllamaProvider(
        model=settings.ollama_model,
        instructions=prompt,
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_timeout_seconds,
    )
    digest = provider.model_digest()
    logger.info(
        "Ollama runtime model=%s digest=%s",
        settings.ollama_model,
        digest,
    )

    def classify(article: ArticleInput) -> tuple[str, ...]:
        return provider(article).category_ids

    return EnrichmentService(
        EnrichmentRepository(SessionLocal),
        classify,
    )


def create_post_processor() -> PostProcessor:
    """Compose parsed-event processing for the broker consumer."""
    return PostProcessor(create_enrichment_service())
