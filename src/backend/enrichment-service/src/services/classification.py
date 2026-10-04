"""In-memory article classification with an injected classifier callable."""

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass

from src.services.categories import CATEGORY_DEFINITIONS

MAX_TITLE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 2_000
MAX_BODY_LENGTH = 1_200
MAX_LANGUAGE_LENGTH = 35
MAX_SOURCE_CATEGORY_LENGTH = 100
MAX_KEYWORDS = 8
MAX_KEYWORD_LENGTH = 80


@dataclass(frozen=True, slots=True)
class ArticleInput:
    """Text and optional language metadata used for classification."""

    title: str
    description: str | None = None
    body: str | None = None
    language: str | None = None
    source_category: str | None = None
    keywords: tuple[str, ...] = ()


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
    title = _normalize_text(article.title, MAX_TITLE_LENGTH)
    description = _normalize_optional_text(
        article.description, MAX_DESCRIPTION_LENGTH
    )
    while description and title:
        if description.casefold() == title.casefold():
            description = None
        elif description[: len(title)].casefold() == title.casefold():
            remainder = description[len(title) :]
            separator = re.match(r"^(?:[.:]\s+|\s+[-|—–]\s+)", remainder)
            if separator is None:
                break
            description = remainder[separator.end() :].strip() or None
        else:
            break
    keywords = tuple(
        dict.fromkeys(
            keyword
            for value in article.keywords[:MAX_KEYWORDS]
            if (keyword := _normalize_text(value, MAX_KEYWORD_LENGTH))
        )
    )
    return ArticleInput(
        title=title,
        description=description,
        body=_normalize_optional_text(article.body, MAX_BODY_LENGTH),
        language=_normalize_language(article.language),
        source_category=_normalize_optional_text(
            article.source_category, MAX_SOURCE_CATEGORY_LENGTH
        ),
        keywords=keywords,
    )


def _normalize_optional_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    return _normalize_text(value, max_length) or None


def _normalize_text(value: str, max_length: int) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return " ".join(normalized.split())[:max_length]


def _normalize_language(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = " ".join(value.split()).lower()
    return normalized[:MAX_LANGUAGE_LENGTH] or None
