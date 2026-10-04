from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from src.repositories.enrichment_repository import EnrichmentRepository
from src.services.classification import ArticleInput
from src.services.enrichment import EnrichmentService


class ConfiguredClassifier:
    def __init__(self, outputs: list[str | None]) -> None:
        self.outputs = iter(outputs)
        self.inputs: list[ArticleInput] = []

    def __call__(self, article: ArticleInput) -> str | None:
        self.inputs.append(article)
        return next(self.outputs)


def test_reuses_saved_result_after_service_recreation(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    article = ArticleInput(title="A science report", body="New research")
    first_classifier = ConfiguredClassifier(["science"])
    first_service = EnrichmentService(
        EnrichmentRepository(session_factory), first_classifier
    )

    first_result = first_service.enrich_article(post_id, article)
    recreated_classifier = ConfiguredClassifier([])
    recreated_service = EnrichmentService(
        EnrichmentRepository(session_factory), recreated_classifier
    )

    reused_result = recreated_service.enrich_article(post_id, article)

    assert first_result == reused_result
    assert first_result.status == "completed"
    assert first_classifier.inputs == [article]
    assert recreated_classifier.inputs == []


def test_hash_uses_the_normalized_bounded_classifier_input(
    session_factory: sessionmaker[Session],
) -> None:
    classifier = ConfiguredClassifier(["technology"])
    service = EnrichmentService(
        EnrichmentRepository(session_factory), classifier
    )
    post_id = uuid4()

    first = service.enrich_article(
        post_id, ArticleInput(title="X" * 500 + "one")
    )
    second = service.enrich_article(
        post_id,
        ArticleInput(title="X" * 500 + "different tail"),
        post_revision=2,
    )

    assert first.input_hash == second.input_hash
    assert second.post_revision == 2
    assert len(classifier.inputs) == 1
    assert len(classifier.inputs[0].title) == 500


def test_changed_text_and_version_are_processed_again(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    classifier = ConfiguredClassifier(["science", "health", "health"])
    repository = EnrichmentRepository(session_factory)

    first = EnrichmentService(repository, classifier).enrich_article(
        post_id, ArticleInput(title="Research update")
    )
    changed_text = EnrichmentService(repository, classifier).enrich_article(
        post_id, ArticleInput(title="Medical update"), post_revision=2
    )
    changed_version = EnrichmentService(
        repository, classifier, enrichment_version="changed-version"
    ).enrich_article(
        post_id,
        ArticleInput(title="Medical update"),
        post_revision=3,
    )

    assert first.category_id == "science"
    assert changed_text.category_id == "health"
    assert changed_version.category_id == "health"
    assert changed_version.enrichment_version == "changed-version"
    assert len(classifier.inputs) == 3


def test_newer_revision_with_unchanged_input_reuses_result(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    article = ArticleInput(title="Same article", body="Same body")
    repository = EnrichmentRepository(session_factory)
    classifier = ConfiguredClassifier(["science"])
    service = EnrichmentService(repository, classifier)

    first = service.enrich_article(post_id, article, post_revision=4)
    newer = service.enrich_article(post_id, article, post_revision=5)

    assert first.category_id == newer.category_id == "science"
    assert first.input_hash == newer.input_hash
    assert first.post_revision == 4
    assert newer.post_revision == 5
    assert len(classifier.inputs) == 1


def test_stale_revision_is_ignored(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    repository = EnrichmentRepository(session_factory)
    classifier = ConfiguredClassifier(["science"])
    service = EnrichmentService(repository, classifier)
    latest = service.enrich_article(
        post_id,
        ArticleInput(title="Latest snapshot"),
        post_revision=3,
    )

    stale = service.enrich_article(
        post_id,
        ArticleInput(title="Older snapshot"),
        post_revision=2,
    )

    assert stale == latest
    assert stale.post_revision == 3
    assert len(classifier.inputs) == 1


def test_completed_revision_is_not_reclassified_after_version_change(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    repository = EnrichmentRepository(session_factory)
    first_classifier = ConfiguredClassifier(["science"])
    first = EnrichmentService(repository, first_classifier).enrich_article(
        post_id, ArticleInput(title="Research update"), post_revision=3
    )
    newer_classifier = ConfiguredClassifier([])

    repeated = EnrichmentService(
        repository, newer_classifier, enrichment_version="changed-version"
    ).enrich_article(
        post_id, ArticleInput(title="Changed text"), post_revision=3
    )

    assert repeated == first
    assert newer_classifier.inputs == []


def test_abstention_is_saved_and_reused_without_classifier_call(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    repository = EnrichmentRepository(session_factory)
    first_classifier = ConfiguredClassifier([])
    first = EnrichmentService(repository, first_classifier).enrich_article(
        post_id, ArticleInput(title="  ", body=None)
    )
    recreated_classifier = ConfiguredClassifier([])
    second = EnrichmentService(repository, recreated_classifier).enrich_article(
        post_id, ArticleInput(title="", body=None)
    )

    assert first.status == "abstained"
    assert first.reason == "no_usable_text"
    assert first == second
    assert first_classifier.inputs == []
    assert recreated_classifier.inputs == []


def test_failed_result_is_saved_but_not_reused(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    repository = EnrichmentRepository(session_factory)
    calls = 0

    def fail_once(article: ArticleInput) -> str | None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary classifier failure")
        return "business"

    service = EnrichmentService(repository, fail_once)
    article = ArticleInput(title="Company report")

    with pytest.raises(RuntimeError, match="temporary classifier failure"):
        service.enrich_article(post_id, article)

    failed = repository.get_by_post_id(post_id)
    assert failed is not None
    assert failed.status == "failed"
    assert failed.reason == "classifier_error"

    succeeded = service.enrich_article(post_id, article)

    assert succeeded.status == "completed"
    assert succeeded.category_id == "business"
    assert calls == 2
