"""Explicit provider constructors for manual evaluation."""

from src.adapters.gemini_provider import GeminiProvider
from src.adapters.ollama_provider import OllamaProvider
from src.config.settings import settings
from src.services.provider import Provider


def create_gemini(*, model: str, instructions: str, timeout: float) -> Provider:
    if not settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY is missing (environment or service .env)"
        )
    return GeminiProvider(
        model=model,
        instructions=instructions,
        api_key=settings.gemini_api_key,
        timeout=timeout,
    )


def create_ollama(*, model: str, instructions: str, timeout: float) -> Provider:
    return OllamaProvider(
        model=model,
        instructions=instructions,
        base_url=settings.ollama_base_url,
        timeout=timeout,
    )


PROVIDERS = {"gemini": create_gemini, "ollama": create_ollama}
