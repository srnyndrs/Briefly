from typing import cast

import pytest

from src.services.categories import CATEGORY_DEFINITIONS
from src.services.classification import (
    ArticleInput,
    Classifier,
    ClassificationResult,
    classify_article,
    normalize_article,
)


class FakeClassifier:
    def __init__(self, result: tuple[str, ...]) -> None:
        self.result = result
        self.inputs: list[ArticleInput] = []

    def __call__(self, article: ArticleInput) -> tuple[str, ...]:
        self.inputs.append(article)
        return self.result


def test_classifies_normalized_article_with_configured_result() -> None:
    classifier = FakeClassifier(("technology",))

    result = classify_article(
        ArticleInput(
            title="  New   device ",
            body="A\nnew device was announced.",
            language=" HU ",
        ),
        classifier,
    )

    assert result == ClassificationResult(category_ids=("technology",))
    assert classifier.inputs == [
        ArticleInput(
            title="New device",
            body="A new device was announced.",
            language="hu",
        )
    ]


def test_uses_description_when_body_is_missing() -> None:
    classifier = FakeClassifier(("science",))

    result = classify_article(
        ArticleInput(title="Research update", description="New study results"),
        classifier,
    )

    assert result.category_ids == ("science",)
    assert classifier.inputs[0].body is None
    assert classifier.inputs[0].description == "New study results"


def test_empty_text_abstains_without_calling_classifier() -> None:
    classifier = FakeClassifier(("other",))

    result = classify_article(
        ArticleInput(
            title="  ",
            description="\n",
            language="hu",
            source_category="Sports",
            keywords=("football",),
        ),
        classifier,
    )

    assert result == ClassificationResult(category_ids=())
    assert classifier.inputs == []


def test_classifier_can_abstain() -> None:
    classifier = FakeClassifier(())

    result = classify_article(ArticleInput(title="Unclear report"), classifier)

    assert result == ClassificationResult(category_ids=())
    assert len(classifier.inputs) == 1


@pytest.mark.parametrize("invalid_result", [("unknown",), (" Technology ",), 4])
def test_rejects_unsupported_classifier_result(invalid_result: object) -> None:
    classifier = cast(Classifier, lambda _: invalid_result)

    with pytest.raises(ValueError):
        classify_article(ArticleInput(title="A report"), classifier)


@pytest.mark.parametrize(
    "invalid",
    [
        ("science", "science"),
        ("science", "health", "business"),
        ("other", "health"),
        ("unknown",),
        "science",
    ],
)
def test_rejects_invalid_category_collections(invalid: object) -> None:
    with pytest.raises(ValueError):
        classify_article(
            ArticleInput(title="A report"), cast(Classifier, lambda _: invalid)
        )


def test_two_categories_follow_taxonomy_order() -> None:
    result = classify_article(
        ArticleInput(title="A report"), lambda _: ("health", "science")
    )
    assert result.category_ids == ("science", "health")


def test_classifier_failure_propagates() -> None:
    def fail(_: ArticleInput) -> tuple[str, ...]:
        raise RuntimeError("classifier failed")

    with pytest.raises(RuntimeError, match="classifier failed"):
        classify_article(ArticleInput(title="A report"), fail)


def test_input_fields_are_bounded() -> None:
    classifier = FakeClassifier(("other",))

    classify_article(
        ArticleInput(
            title="T" * 600,
            description="D" * 2_100,
            body="B" * 8_100,
            language="HU" * 30,
        ),
        classifier,
    )

    normalized = classifier.inputs[0]
    assert len(normalized.title) == 500
    assert normalized.description is not None
    assert len(normalized.description) == 2_000
    assert normalized.body is not None
    assert len(normalized.body) == 1_200
    assert normalized.language is not None
    assert len(normalized.language) == 35


def test_description_deduplicates_title_and_body_uses_opening_excerpt() -> None:
    classifier = FakeClassifier(("science",))
    classify_article(
        ArticleInput(
            title="Research update",
            description="Research update — New study results & analysis",
            body="Opening context. " + "Later details. " * 200,
        ),
        classifier,
    )

    article = classifier.inputs[0]
    assert article.title == "Research update"
    assert article.description == "New study results & analysis"
    assert article.body is not None
    assert article.body.startswith("Opening context.")
    assert len(article.body) <= 1_200
    assert ("Opening context. " + "Later details. " * 200).startswith(
        article.body
    )


def test_language_hint_preserves_regional_tag() -> None:
    classifier = FakeClassifier(("science",))
    classify_article(
        ArticleInput(title="Report", language=" EN-US "), classifier
    )

    assert classifier.inputs[0].language == "en-us"


def test_source_metadata_is_bounded_hints() -> None:
    classifier = FakeClassifier(("technology",))
    classify_article(
        ArticleInput(
            title="Device report",
            source_category="  Gadgets & Devices  ",
            keywords=(" AI ", "AI", "hardware", *("extra" for _ in range(10))),
        ),
        classifier,
    )

    article = classifier.inputs[0]
    assert article.source_category == "Gadgets & Devices"
    assert article.keywords == ("AI", "hardware", "extra")


def test_repeated_normalization_preserves_exact_classifier_input() -> None:
    article = ArticleInput(
        title="Research update",
        description="Research update. Research update — -5 degrees recorded",
        body="Literal &amp; text " * 200,
        source_category="  ",
    )

    normalized = normalize_article(article)

    assert normalized.description == "-5 degrees recorded"
    assert normalized.source_category is None
    assert normalize_article(normalized) == normalized


def test_category_definitions_are_the_supported_ids() -> None:
    assert set(CATEGORY_DEFINITIONS) == {
        "politics",
        "world",
        "business",
        "economy",
        "finance",
        "technology",
        "science",
        "health",
        "environment",
        "entertainment",
        "lifestyle",
        "automotive",
        "sports",
        "society",
        "other",
    }
