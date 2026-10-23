from typing import cast

import pytest

from src.services.classification import (
    ArticleInput,
    ClassificationResult,
    Classifier,
    classify_article,
    normalize_article,
)
from src.services.provider import parse_categories


class FakeClassifier:
    def __init__(self, result: tuple[str, ...]) -> None:
        self.result = result
        self.inputs: list[ArticleInput] = []

    def __call__(self, article: ArticleInput) -> tuple[str, ...]:
        self.inputs.append(article)
        return self.result


def test_classifies_normalized_article_with_configured_result() -> None:
    classifier = FakeClassifier(("health", "science"))

    result = classify_article(
        ArticleInput(
            title="  New   device ",
            body="A\nnew device was announced.",
            language=" EN-US ",
            source_category="  Gadgets & Devices  ",
            keywords=(" AI ", "AI", "hardware"),
        ),
        classifier,
    )

    assert result == ClassificationResult(category_ids=("science", "health"))
    assert classifier.inputs == [
        ArticleInput(
            title="New device",
            body="A new device was announced.",
            language="en-us",
            source_category="Gadgets & Devices",
            keywords=("AI", "hardware"),
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


def test_input_fields_are_bounded() -> None:
    classifier = FakeClassifier(("other",))

    classify_article(
        ArticleInput(
            title="T" * 600,
            source_category="S" * 110,
            keywords=tuple(str(i) * 100 for i in range(10)),
            description="D" * 2_100,
            body="Opening context. " + "B" * 8_100,
            language="HU" * 30,
        ),
        classifier,
    )

    normalized = classifier.inputs[0]
    assert len(normalized.title) == 500
    assert normalized.body.startswith("Opening context. ")
    assert len(normalized.source_category) == 100
    assert len(normalized.keywords) == 8
    assert all(len(word) == 80 for word in normalized.keywords)
    assert normalized.description is not None
    assert len(normalized.description) == 2_000
    assert normalized.body is not None
    assert len(normalized.body) == 1_200
    assert normalized.language is not None
    assert len(normalized.language) == 35


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


def test_provider_output_rejects_extra_keys() -> None:
    with pytest.raises(ValueError):
        parse_categories({"category_ids": ["science"], "extra": True})
