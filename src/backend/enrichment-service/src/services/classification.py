"""In-memory article classification with an injected classifier callable."""

import unicodedata
from collections.abc import Callable
from dataclasses import dataclass

from src.services.categories import CATEGORY_DEFINITIONS

MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 2_000
MAX_BODY_LENGTH = 8_000
MAX_LANGUAGE_LENGTH = 35


@dataclass(frozen=True, slots=True)
class ArticleInput:
    """Text and optional language metadata used for classification."""

    title: str
    description: str | None = None
    body: str | None = None
    language: str | None = None


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    """A supported category or ``None`` when classification abstains."""

    category_id: str | None


Classifier = Callable[[ArticleInput], str | None]


def classify_article(
    article: ArticleInput,
    classifier: Classifier,
) -> ClassificationResult:
    """Normalize bounded article text and validate the classifier result.

    Empty text returns an abstention without calling the classifier. Exceptions
    from the injected classifier are allowed to propagate to the caller.
    """
    normalized = normalize_article(article)
    if not any((normalized.title, normalized.description, normalized.body)):
        return ClassificationResult(category_id=None)

    category_id = classifier(normalized)
    if category_id is not None and (
        not isinstance(category_id, str)
        or category_id not in CATEGORY_DEFINITIONS
    ):
        raise ValueError(f"Unsupported category ID: {category_id!r}")

    return ClassificationResult(category_id=category_id)


def normalize_article(article: ArticleInput) -> ArticleInput:
    """Return the exact normalized, bounded input passed to a classifier."""
    return ArticleInput(
        title=_normalize_text(article.title, MAX_TITLE_LENGTH),
        description=_normalize_optional_text(
            article.description, MAX_DESCRIPTION_LENGTH
        ),
        body=_normalize_optional_text(article.body, MAX_BODY_LENGTH),
        language=_normalize_language(article.language),
    )


def _normalize_optional_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    return _normalize_text(value, max_length)


def _normalize_text(value: str, max_length: int) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.split())[:max_length]


def _normalize_language(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split()).lower()
    return normalized[:MAX_LANGUAGE_LENGTH] or None
