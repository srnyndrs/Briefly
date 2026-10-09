"""Compose the concrete Ollama runtime and its saved-result identity."""

import hashlib
import json
import logging

from src.adapters.ollama_provider import GENERATION_OPTIONS, OllamaProvider
from src.config.database import SessionLocal
from src.config.settings import settings
from src.repositories.enrichment_repository import EnrichmentRepository
from src.services.categories import CATEGORY_TAXONOMY_VERSION
from src.services.classification import ArticleInput, INPUT_POLICY_VERSION
from src.services.enrichment import EnrichmentService
from src.services.post_processor import PostEventProcessor
from src.services.provider import PROMPT_VERSION, category_schema, instructions

logger = logging.getLogger(__name__)


def enrichment_version(model: str, digest: str, prompt: str) -> str:
    """Bound the identity while retaining all model and policy components."""
    identity = {
        "provider": "ollama",
        "model": model,
        "digest": digest,
        "taxonomy": CATEGORY_TAXONOMY_VERSION,
        "prompt_version": PROMPT_VERSION,
        "prompt": prompt,
        "schema": category_schema(),
        "input_policy": INPUT_POLICY_VERSION,
        "options": GENERATION_OPTIONS,
    }
    encoded = json.dumps(identity, sort_keys=True).encode("utf-8")
    return f"ollama-{hashlib.sha256(encoded).hexdigest()}"


def create_post_processor() -> PostEventProcessor:
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
    version = enrichment_version(settings.ollama_model, digest, prompt)
    logger.info(
        "Ollama runtime model=%s digest=%s enrichment_version=%s",
        settings.ollama_model,
        digest,
        version,
    )

    def classify(article: ArticleInput) -> tuple[str, ...]:
        return provider(article).category_ids

    service = EnrichmentService(
        EnrichmentRepository(SessionLocal),
        classify,
        version,
    )
    return PostEventProcessor(service)
