"""Explicit provider constructors for manual evaluation."""

from src.adapters.gemini_provider import GeminiProvider
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


PROVIDERS = {"gemini": create_gemini}
