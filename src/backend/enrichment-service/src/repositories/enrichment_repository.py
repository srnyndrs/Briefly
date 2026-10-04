from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID

from sqlalchemy import and_, or_, update
from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from src.models.post_enrichment import PostEnrichment
from src.services.categories import validate_category_ids

EnrichmentStatus = Literal["completed", "abstained", "failed"]


@dataclass(frozen=True, slots=True)
class StoredEnrichment:
    post_id: UUID
    input_hash: str
    enrichment_version: str
    category_ids: tuple[str, ...]
    status: EnrichmentStatus
    reason: str | None
    processed_at: datetime
    post_revision: int = 1
    enrichment_revision: int = 1
    event_id: str | None = None
    result_event: dict | None = None
    publication_pending: bool = False


class EnrichmentRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_by_post_id(self, post_id: UUID) -> StoredEnrichment | None:
        with self._session_factory() as session:
            record = session.get(PostEnrichment, post_id)
            if record is None:
                return None
            return self._to_stored(record)

    def save(self, enrichment: StoredEnrichment) -> StoredEnrichment | None:
        categories = validate_category_ids(enrichment.category_ids)
        if (enrichment.status == "completed") != bool(categories):
            raise ValueError("Result status and category IDs disagree")
        with self._session_factory.begin() as session:
            dialect_name = session.get_bind().dialect.name
            if dialect_name == "sqlite":
                insert = sqlite_insert
            elif dialect_name == "postgresql":
                insert = postgresql_insert
            else:
                raise RuntimeError(
                    f"Unsupported database dialect: {dialect_name}"
                )

            statement = insert(PostEnrichment).values(
                post_id=enrichment.post_id,
                post_revision=enrichment.post_revision,
                input_hash=enrichment.input_hash,
                enrichment_version=enrichment.enrichment_version,
                category_ids=list(categories),
                enrichment_revision=1,
                status=enrichment.status,
                reason=enrichment.reason,
                processed_at=enrichment.processed_at,
                event_id=enrichment.event_id,
                result_event=enrichment.result_event,
                publication_pending=enrichment.publication_pending,
            )
            excluded = statement.excluded
            row = session.execute(
                statement.on_conflict_do_update(
                    index_elements=[PostEnrichment.post_id],
                    set_={
                        "post_revision": excluded.post_revision,
                        "input_hash": excluded.input_hash,
                        "enrichment_version": excluded.enrichment_version,
                        "category_ids": excluded.category_ids,
                        "enrichment_revision": PostEnrichment.enrichment_revision
                        + 1,
                        "status": excluded.status,
                        "reason": excluded.reason,
                        "processed_at": excluded.processed_at,
                        "event_id": excluded.event_id,
                        "result_event": excluded.result_event,
                        "publication_pending": excluded.publication_pending,
                    },
                    where=or_(
                        PostEnrichment.post_revision < excluded.post_revision,
                        and_(
                            PostEnrichment.post_revision
                            == excluded.post_revision,
                            or_(
                                PostEnrichment.status == "failed",
                                PostEnrichment.input_hash
                                != excluded.input_hash,
                                PostEnrichment.enrichment_version
                                != excluded.enrichment_version,
                                and_(
                                    PostEnrichment.event_id.is_(None),
                                    excluded.event_id.is_not(None),
                                ),
                            ),
                        ),
                    ),
                ).returning(PostEnrichment.enrichment_revision)
            ).scalar_one_or_none()
            if row is None:
                return None
            event = enrichment.result_event
            if event is not None and "payload" in event:
                event = {
                    **event,
                    "payload": {
                        **event["payload"],
                        "enrichment_revision": row,
                    },
                }
                session.execute(
                    update(PostEnrichment)
                    .where(PostEnrichment.post_id == enrichment.post_id)
                    .values(result_event=event)
                )
            return replace(
                enrichment,
                category_ids=categories,
                enrichment_revision=row,
                result_event=event,
            )

    def mark_published(self, post_id: UUID, event_id: str) -> None:
        with self._session_factory.begin() as session:
            result = session.execute(
                update(PostEnrichment)
                .where(
                    PostEnrichment.post_id == post_id,
                    PostEnrichment.event_id == event_id,
                )
                .values(publication_pending=False)
            )
            if result.rowcount != 1:
                raise RuntimeError(
                    "Saved result changed before publication completed"
                )

    @staticmethod
    def _to_stored(record: PostEnrichment) -> StoredEnrichment:
        processed_at = record.processed_at
        if processed_at.tzinfo is None:
            processed_at = processed_at.replace(tzinfo=UTC)
        return StoredEnrichment(
            post_id=record.post_id,
            post_revision=record.post_revision,
            input_hash=record.input_hash,
            enrichment_version=record.enrichment_version,
            category_ids=tuple(record.category_ids),
            enrichment_revision=record.enrichment_revision,
            status=cast(EnrichmentStatus, record.status),
            reason=record.reason,
            processed_at=processed_at,
            event_id=record.event_id,
            result_event=record.result_event,
            publication_pending=record.publication_pending,
        )
