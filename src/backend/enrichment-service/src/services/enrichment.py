"""Persist classifier results and reuse successful unchanged enrichments."""

import hashlib
import json
from dataclasses import asdict, replace
from datetime import UTC, datetime
from uuid import UUID

from src.events.post_enriched import build_result_event
from src.repositories.enrichment_repository import (
    EnrichmentRepository,
    EnrichmentStatus,
    StoredEnrichment,
)
from src.services.classification import (
    ArticleInput,
    Classifier,
    classify_article,
    normalize_article,
)

DEFAULT_ENRICHMENT_VERSION = "classification-v2"


class EnrichmentService:
    """Classify and persist one post without holding a database transaction."""

    def __init__(
        self,
        repository: EnrichmentRepository,
        classifier: Classifier,
        enrichment_version: str = DEFAULT_ENRICHMENT_VERSION,
    ) -> None:
        if not enrichment_version or len(enrichment_version) > 100:
            raise ValueError(
                "Enrichment version must contain 1 to 100 characters"
            )
        self._repository = repository
        self._classifier = classifier
        self._enrichment_version = enrichment_version

    def enrich_article(
        self,
        post_id: UUID,
        article: ArticleInput,
        *,
        post_revision: int = 1,
        correlation_id: str | None = None,
    ) -> StoredEnrichment:
        if (
            isinstance(post_revision, bool)
            or not isinstance(post_revision, int)
            or post_revision < 1
        ):
            raise ValueError("Post revision must be a positive integer")
        normalized = normalize_article(article)
        input_hash = _hash_classifier_input(normalized)
        existing = self._repository.get_by_post_id(post_id)
        if existing is not None and existing.post_revision > post_revision:
            return existing
        if (
            existing is not None
            and existing.post_revision == post_revision
            and existing.status in ("completed", "abstained")
        ):
            if correlation_id is not None and existing.result_event is None:
                return self._save_result(
                    self._with_event(existing, correlation_id)
                )
            return existing
        if (
            existing is not None
            and existing.input_hash == input_hash
            and existing.enrichment_version == self._enrichment_version
            and existing.status in ("completed", "abstained")
        ):
            if existing.post_revision < post_revision:
                refreshed = replace(existing, post_revision=post_revision)
                if correlation_id is not None:
                    refreshed = self._with_event(refreshed, correlation_id)
                return self._save_result(refreshed)
            return existing

        try:
            result = classify_article(normalized, self._classifier)
        except Exception:
            failed_saved = self._repository.save(
                self._result(
                    post_id=post_id,
                    input_hash=input_hash,
                    category_id=None,
                    status="failed",
                    reason="classifier_error",
                    post_revision=post_revision,
                )
            )
            if not failed_saved:
                latest = self._latest_or_raise(post_id)
                if latest.post_revision > post_revision:
                    return latest
            raise

        if result.category_id is None:
            reason = (
                "no_usable_text"
                if not any(
                    (normalized.title, normalized.description, normalized.body)
                )
                else "classifier_abstained"
            )
            status: EnrichmentStatus = "abstained"
        else:
            reason = None
            status = "completed"

        enrichment = self._result(
            post_id=post_id,
            input_hash=input_hash,
            category_id=result.category_id,
            status=status,
            reason=reason,
            post_revision=post_revision,
        )
        if correlation_id is not None:
            enrichment = self._with_event(enrichment, correlation_id)
        return self._save_result(enrichment)

    def _with_event(
        self, enrichment: StoredEnrichment, correlation_id: str
    ) -> StoredEnrichment:
        event = build_result_event(
            post_id=str(enrichment.post_id),
            post_revision=enrichment.post_revision,
            input_hash=enrichment.input_hash,
            enrichment_version=enrichment.enrichment_version,
            status=enrichment.status,
            category_id=enrichment.category_id,
            processed_at=enrichment.processed_at,
            correlation_id=correlation_id,
        )
        return replace(
            enrichment,
            event_id=event["event_id"],
            result_event=event,
            publication_pending=True,
        )

    def _save_result(self, enrichment: StoredEnrichment) -> StoredEnrichment:
        if self._repository.save(enrichment):
            return enrichment
        return self._latest_or_raise(enrichment.post_id)

    def _result(
        self,
        *,
        post_id: UUID,
        input_hash: str,
        category_id: str | None,
        status: EnrichmentStatus,
        reason: str | None,
        post_revision: int,
    ) -> StoredEnrichment:
        return StoredEnrichment(
            post_id=post_id,
            input_hash=input_hash,
            enrichment_version=self._enrichment_version,
            category_id=category_id,
            status=status,
            reason=reason,
            processed_at=datetime.now(UTC),
            post_revision=post_revision,
        )

    def _latest_or_raise(self, post_id: UUID) -> StoredEnrichment:
        latest = self._repository.get_by_post_id(post_id)
        if latest is None:
            raise RuntimeError("Enrichment disappeared during save")
        return latest

    def mark_published(self, post_id: UUID, event_id: str) -> None:
        self._repository.mark_published(post_id, event_id)


def _hash_classifier_input(article: ArticleInput) -> str:
    payload = json.dumps(
        asdict(article),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
