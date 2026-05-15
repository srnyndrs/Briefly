from sqlalchemy import text
from sqlalchemy.orm import Session


def backfill_article_projections(
    db: Session, *, batch_size: int = 500
) -> int:
    """Backfill missing article projections from the articles table."""
    _ = batch_size  # Kept for backward compatibility of call sites.

    result = db.execute(
        text(
            """
            INSERT INTO article_projections (
                article_id,
                source_id,
                canonical_url,
                title,
                language,
                categories,
                content_ref,
                image_ref,
                sentiment,
                topics,
                cluster_id,
                model_version,
                published_at,
                updated_at
            )
            SELECT
                a.id::text,
                CASE WHEN a.feed_id IS NULL THEN NULL ELSE a.feed_id::text END,
                a.url,
                COALESCE(a.title, ''),
                NULL,
                '[]'::json,
                NULL,
                a.image_url,
                NULL,
                '[]'::json,
                NULL,
                NULL,
                a.published_at,
                COALESCE(a.parsed_at, NOW())
            FROM articles a
            LEFT JOIN article_projections p ON p.article_id = a.id::text
            WHERE p.article_id IS NULL
            ON CONFLICT DO NOTHING
            """
        )
    )
    db.commit()
    return result.rowcount or 0
