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


def test_force_reclassification_rejects_pending_before_model(session_factory):
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
            post_revision=1,
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
