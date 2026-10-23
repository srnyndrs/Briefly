from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from src.repositories.enrichment_repository import EnrichmentRepository
from src.services.classification import ArticleInput
from src.services.enrichment_service import EnrichmentService


class ConfiguredClassifier:
    def __init__(self, outputs: list[tuple[str, ...]]) -> None:
        self.outputs = iter(outputs)
        self.inputs: list[ArticleInput] = []

    def __call__(self, article: ArticleInput) -> tuple[str, ...]:
        self.inputs.append(article)
        return next(self.outputs)


def test_reuses_saved_result_after_service_recreation(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    article = ArticleInput(title="A science report", body="New research")
    first_classifier = ConfiguredClassifier([("science",)])
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


def test_new_revision_classifies_normalized_bounded_input(session_factory):
    classifier = ConfiguredClassifier([("technology",), ("technology",)])
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
    assert second.post_revision == 2
    assert second.enrichment_revision == first.enrichment_revision + 1
    assert len(classifier.inputs) == 2
    assert classifier.inputs[0] == classifier.inputs[1]
    assert len(classifier.inputs[0].title) == 500


def test_changed_text_at_new_revision_is_processed_again(session_factory):
    classifier = ConfiguredClassifier([("science",), ("health",)])
    service = EnrichmentService(
        EnrichmentRepository(session_factory), classifier
    )
    post_id = uuid4()
    first = service.enrich_article(post_id, ArticleInput(title="Research"))
    changed = service.enrich_article(
        post_id, ArticleInput(title="Medical"), post_revision=2
    )
    assert first.category_ids == ("science",)
    assert changed.category_ids == ("health",)
    assert len(classifier.inputs) == 2


def test_newer_revision_with_unchanged_input_classifies_again(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    article = ArticleInput(title="Same article", body="Same body")
    repository = EnrichmentRepository(session_factory)
    classifier = ConfiguredClassifier([("science",), ("science",)])
    service = EnrichmentService(repository, classifier)

    first = service.enrich_article(post_id, article, post_revision=4)
    newer = service.enrich_article(post_id, article, post_revision=5)

    assert first.category_ids == newer.category_ids == ("science",)
    assert first.post_revision == 4
    assert newer.post_revision == 5
    assert len(classifier.inputs) == 2


def test_stale_revision_is_ignored(
    session_factory: sessionmaker[Session],
) -> None:
    post_id = uuid4()
    repository = EnrichmentRepository(session_factory)
    classifier = ConfiguredClassifier([("science",)])
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


def test_explicit_reclassification_advances_identity_and_revision(
    session_factory,
):
    post_id = uuid4()
    repository = EnrichmentRepository(session_factory)
    classifier = ConfiguredClassifier([("science",), ("science", "health")])
    service = EnrichmentService(repository, classifier)
    first = service.enrich_article(
        post_id, ArticleInput(title="Research"), post_revision=3
    )
    service.mark_published(post_id, first.event_id)
    repeated = service.enrich_article(
        post_id,
        ArticleInput(title="Research"),
        post_revision=3,
        force_reclassify=True,
    )
    assert repeated.category_ids == ("science", "health")
    assert repeated.post_revision == first.post_revision
    assert repeated.event_id != first.event_id
    assert repeated.enrichment_revision == first.enrichment_revision + 1
    assert repeated.publication_pending
    assert len(classifier.inputs) == 2


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

    def fail_once(article: ArticleInput) -> tuple[str, ...]:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("temporary classifier failure")
        return ("business",)

    service = EnrichmentService(repository, fail_once)
    article = ArticleInput(title="Company report")

    service.enrich_article(post_id, article)

    failed = repository.get_by_post_id(post_id)
    assert failed is not None
    assert failed.status == "failed"
    assert failed.reason == "classifier_error"

    assert service.enrich_article(post_id, article) == failed
    assert calls == 1
    service.mark_published(post_id, failed.event_id)
    succeeded = service.enrich_article(post_id, article)

    assert succeeded.status == "completed"
    assert succeeded.category_ids == ("business",)
    assert calls == 2


@pytest.mark.parametrize("revision", [1, 2])
def test_force_reclassification_rejects_pending_before_model(
    session_factory, revision
):
    from src.services.enrichment_service import ReclassificationConflict

    repository = EnrichmentRepository(session_factory)
    classifier = ConfiguredClassifier([("science",)])
    service = EnrichmentService(repository, classifier)
    post_id = uuid4()
    first = service.enrich_article(post_id, ArticleInput(title="Research"))
    with pytest.raises(ReclassificationConflict, match="republish_result"):
        service.enrich_article(
            post_id,
            ArticleInput(title="Research"),
            post_revision=revision,
            force_reclassify=True,
        )
    assert repository.get_by_post_id(post_id) == first
    assert len(classifier.inputs) == 1


@pytest.mark.parametrize("force", [False, True])
def test_worker_cannot_overwrite_a_newer_saved_result(session_factory, force):
    from src.services.enrichment_service import ReclassificationConflict

    repository = EnrichmentRepository(session_factory)
    post_id = uuid4()
    article = ArticleInput(title="Research")
    first = EnrichmentService(
        repository, lambda _: ("science",)
    ).enrich_article(post_id, article)
    repository.mark_published(post_id, first.event_id)
    newer = None

    def classify(_):
        nonlocal newer
        newer = EnrichmentService(
            repository, lambda _: ("health",)
        ).enrich_article(post_id, article, post_revision=3)
        return ("business",)

    service = EnrichmentService(repository, classify)
    if force:
        with pytest.raises(ReclassificationConflict, match="changed during"):
            service.enrich_article(post_id, article, force_reclassify=True)
    else:
        assert (
            service.enrich_article(post_id, article, post_revision=2) == newer
        )
    assert repository.get_by_post_id(post_id) == newer


def test_same_revision_reclassification_conflict_does_not_repeat_model(
    session_factory,
):
    from src.services.enrichment_service import ReclassificationConflict

    repository = EnrichmentRepository(session_factory)
    post_id = uuid4()
    article = ArticleInput(title="Research")
    first = EnrichmentService(
        repository, lambda _: ("science",)
    ).enrich_article(post_id, article)
    repository.mark_published(post_id, first.event_id)
    calls = 0
    winner = None

    def classify(_):
        nonlocal calls, winner
        calls += 1
        winner = EnrichmentService(
            repository, lambda _: ("health",)
        ).enrich_article(post_id, article, force_reclassify=True)
        return ("business",)

    with pytest.raises(ReclassificationConflict, match="changed during"):
        EnrichmentService(repository, classify).enrich_article(
            post_id, article, force_reclassify=True
        )
    assert calls == 1
    assert repository.get_by_post_id(post_id) == winner


def test_force_reclassification_rejects_stale_snapshot(session_factory):
    from src.services.enrichment_service import ReclassificationConflict

    repository = EnrichmentRepository(session_factory)
    classifier = ConfiguredClassifier([("science",)])
    service = EnrichmentService(repository, classifier)
    post_id = uuid4()
    saved = service.enrich_article(
        post_id, ArticleInput(title="Research"), post_revision=3
    )
    repository.mark_published(post_id, saved.event_id)
    with pytest.raises(ReclassificationConflict, match="stale"):
        service.enrich_article(
            post_id,
            ArticleInput(title="Old"),
            post_revision=2,
            force_reclassify=True,
        )
    assert len(classifier.inputs) == 1
