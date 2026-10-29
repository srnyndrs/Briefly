import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.repositories.enrichment_repository import EnrichmentRepository
from src.repositories.stored_enrichment import EnrichmentStatus, StoredEnrichment
from src.services.classification import (
    ArticleInput,
    Classifier,
    classify_article,
    normalize_article,
)
from src.services.provider import ProviderError, ProviderUnavailableError

logger = logging.getLogger(__name__)


class ReclassificationConflict(RuntimeError):
    pass


class EnrichmentService:
    def __init__(
        self, repository: EnrichmentRepository, classifier: Classifier
    ) -> None:
        self._repository = repository
        self._classifier = classifier

    def enrich_article(
        self,
        post_id: UUID,
        article: ArticleInput,
        *,
        post_revision: int = 1,
        correlation_id: str | None = None,
        force_reclassify: bool = False,
    ) -> StoredEnrichment:
        if type(post_revision) is not int or post_revision < 1:
            raise ValueError("Post revision must be a positive integer")

        existing = self._repository.get_by_post_id(post_id)
        if existing is not None:
            if force_reclassify:
                if existing.post_revision > post_revision:
                    raise ReclassificationConflict("Canonical snapshot is stale")
                if existing.publication_pending:
                    raise ReclassificationConflict(
                        "Publish the pending result first with "
                        "python -m src.scripts.republish_result " + str(post_id)
                    )
            elif existing.post_revision > post_revision or (
                existing.post_revision == post_revision
                and (existing.status != "failed" or existing.publication_pending)
            ):
                return existing

        correlation_id = correlation_id or str(uuid4())
        status: EnrichmentStatus
        normalized = normalize_article(article)

        try:
            result = classify_article(normalized, self._classifier)
        except ProviderUnavailableError:
            raise
        except Exception as exc:
            logger.warning(
                "Classification failed (post_id=%s, error=%s)",
                post_id,
                str(exc)[:300]
                if isinstance(exc, ProviderError)
                else type(exc).__name__,
            )
            categories = ()
            status = "failed"
            reason = "classifier_error"
        else:
            categories = result.category_ids
            status = "completed" if categories else "abstained"
            reason = None
            if not categories:
                reason = (
                    "no_usable_text"
                    if not any(
                        (
                            normalized.title,
                            normalized.description,
                            normalized.body,
                        )
                    )
                    else "classifier_abstained"
                )

        enrichment = StoredEnrichment(
            post_id=post_id,
            post_revision=post_revision,
            category_ids=categories,
            status=status,
            reason=reason,
            processed_at=datetime.now(UTC),
            event_id=str(uuid4()),
            correlation_id=correlation_id,
            publication_pending=True,
        )
        saved = self._repository.save(
            enrichment,
            expected_enrichment_revision=(
                existing.enrichment_revision if existing else 0
            )
            if force_reclassify
            else None,
        )
        if saved is not None:
            return saved

        if force_reclassify:
            raise ReclassificationConflict(
                "Saved result changed during classification; inspect before retrying"
            )

        latest = self._repository.get_by_post_id(post_id)
        if latest is None:
            raise RuntimeError("Enrichment disappeared during save")

        return latest

    def mark_published(self, post_id: UUID, event_id: str) -> None:
        self._repository.mark_published(post_id, event_id)
