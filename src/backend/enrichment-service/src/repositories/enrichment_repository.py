from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, cast
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as postgresql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session, sessionmaker

from src.models.post_enrichment import PostEnrichment

EnrichmentStatus = Literal["completed", "abstained", "failed"]


@dataclass(frozen=True, slots=True)
class StoredEnrichment:
    post_id: UUID
    input_hash: str
    enrichment_version: str
    category_id: str | None
    status: EnrichmentStatus
    reason: str | None
    processed_at: datetime
    post_revision: int = 1


class EnrichmentRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_by_post_id(self, post_id: UUID) -> StoredEnrichment | None:
        with self._session_factory() as session:
            record = session.get(PostEnrichment, post_id)
            if record is None:
                return None
            return self._to_stored(record)

    def save(self, enrichment: StoredEnrichment) -> bool:
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
                category_id=enrichment.category_id,
                status=enrichment.status,
                reason=enrichment.reason,
                processed_at=enrichment.processed_at,
            )
            excluded = statement.excluded
            result = session.execute(
                statement.on_conflict_do_update(
                    index_elements=[PostEnrichment.post_id],
                    set_={
                        "post_revision": excluded.post_revision,
                        "input_hash": excluded.input_hash,
                        "enrichment_version": excluded.enrichment_version,
                        "category_id": excluded.category_id,
                        "status": excluded.status,
                        "reason": excluded.reason,
                        "processed_at": excluded.processed_at,
                    },
                    where=(
                        PostEnrichment.post_revision <= excluded.post_revision
                    ),
                )
            )
            return bool(result.rowcount)

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
            category_id=record.category_id,
            status=cast(EnrichmentStatus, record.status),
            reason=record.reason,
            processed_at=processed_at,
        )
