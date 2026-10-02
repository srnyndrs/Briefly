from typing import cast

import pytest

from src.services.categories import CATEGORY_DEFINITIONS
from src.services.classification import (
    ArticleInput,
    Classifier,
    ClassificationResult,
    classify_article,
)


class FakeClassifier:
    def __init__(self, result: str | None) -> None:
        self.result = result
        self.inputs: list[ArticleInput] = []

    def __call__(self, article: ArticleInput) -> str | None:
        self.inputs.append(article)
        return self.result


def test_classifies_normalized_article_with_configured_result() -> None:
    classifier = FakeClassifier("technology")

    result = classify_article(
        ArticleInput(
            title="  New   device ",
            body="A\nnew device was announced.",
            language=" HU ",
        ),
        classifier,
    )

    assert result == ClassificationResult(category_id="technology")
    assert classifier.inputs == [
        ArticleInput(
            title="New device",
            body="A new device was announced.",
            language="hu",
        )
    ]


def test_uses_description_when_body_is_missing() -> None:
    classifier = FakeClassifier("science")

    result = classify_article(
        ArticleInput(title="Research update", description="New study results"),
        classifier,
    )

    assert result.category_id == "science"
    assert classifier.inputs[0].body is None
    assert classifier.inputs[0].description == "New study results"


def test_empty_text_abstains_without_calling_classifier() -> None:
    classifier = FakeClassifier("other")

    result = classify_article(
        ArticleInput(title="  ", description="\n", body=None, language="hu"),
        classifier,
    )

    assert result == ClassificationResult(category_id=None)
    assert classifier.inputs == []


def test_classifier_can_abstain() -> None:
    classifier = FakeClassifier(None)

    result = classify_article(ArticleInput(title="Unclear report"), classifier)

    assert result == ClassificationResult(category_id=None)
    assert len(classifier.inputs) == 1


@pytest.mark.parametrize("invalid_result", ["unknown", " Technology ", 4])
def test_rejects_unsupported_classifier_result(invalid_result: object) -> None:
    classifier = cast(Classifier, lambda _: invalid_result)

    with pytest.raises(ValueError, match="Unsupported category ID"):
        classify_article(ArticleInput(title="A report"), classifier)


def test_classifier_failure_propagates() -> None:
    def fail(_: ArticleInput) -> str | None:
        raise RuntimeError("classifier failed")

    with pytest.raises(RuntimeError, match="classifier failed"):
        classify_article(ArticleInput(title="A report"), fail)


def test_input_fields_are_bounded() -> None:
    classifier = FakeClassifier("other")

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
    assert len(normalized.body) == 8_000
    assert normalized.language is not None
    assert len(normalized.language) == 35


def test_category_definitions_are_the_supported_ids() -> None:
    assert set(CATEGORY_DEFINITIONS) == {
        "politics",
        "business",
        "technology",
        "science",
        "health",
        "environment",
        "culture",
        "sports",
        "society",
        "other",
    }
