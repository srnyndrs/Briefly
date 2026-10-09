from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.models.read_models import PostProjection
from src.config.database import Base
from src.repositories.feed_repository import PostRepository
from src.services.feed_models import EffectiveFeedQuery


def _repository() -> tuple[Session, PostRepository]:
    engine = create_engine(
        "sqlite:///:memory:",
        execution_options={"schema_translate_map": {"query": None}},
    )
    Base.metadata.create_all(bind=engine)
    session = Session(engine)
    return session, PostRepository(session)


def _post(
    *,
    categories: list[str],
    language: str,
    source_id: str,
    author: str | None = None,
    keywords: list[str] | None = None,
) -> PostProjection:
    now = datetime.now(UTC)
    return PostProjection(
        post_id=str(uuid4()),
        source_id=source_id,
        source_title="Test Source",
        canonical_url=f"https://example.com/{uuid4()}",
        title="Article",
        categories=categories,
        language=language,
        author=author,
        keywords=keywords or [],
        published_at=now,
        updated_at=now,
    )


def test_filter_options_ignore_their_own_active_dimension():
    session, repository = _repository()
    source = str(uuid4())
    other_source = str(uuid4())
    session.add_all(
        [
            _post(categories=["technology"], language="en", source_id=source),
            _post(categories=["business"], language="hu", source_id=source),
            _post(categories=[], language="en", source_id=source),
            _post(categories=["sports"], language="de", source_id=other_source),
        ]
    )
    session.commit()

    category_options = repository.list_filter_options(
        EffectiveFeedQuery(source_ids=[source], categories=["technology"])
    )
    language_options = repository.list_filter_options(
        EffectiveFeedQuery(source_ids=[source], languages=["en"])
    )
    source_options = repository.list_filter_options(
        EffectiveFeedQuery(source_ids=[source]),
        include_sources=True,
    )

    assert category_options.categories == ["business", "technology"]
    assert language_options.languages == ["en", "hu"]
    assert category_options.authors == []
    assert category_options.keywords == []
    assert category_options.sources is None
    assert language_options.sources is None
    assert source_options.sources is not None
    assert {option.source_id for option in source_options.sources} == {
        source,
        other_source,
    }


def test_candidates_apply_exclusions_and_order_before_pagination():
    session, repository = _repository()
    allowed = str(uuid4())
    blocked = str(uuid4())
    now = datetime.now(UTC)
    visible = _post(categories=["technology"], language="en", source_id=allowed)
    visible.published_at = now
    muted = _post(categories=["sports"], language="en", source_id=allowed)
    blocked_post = _post(
        categories=["technology"], language="en", source_id=blocked
    )
    old = _post(categories=["technology"], language="en", source_id=allowed)
    old.published_at = now - timedelta(days=1)
    session.add_all([visible, muted, blocked_post, old])
    session.commit()

    items, total = repository.list_candidates(
        EffectiveFeedQuery(
            blocked_source_ids=[blocked],
            muted_categories=[" sports "],
            source_ids=[allowed],
            categories=["technology"],
            limit=1,
            offset=0,
        )
    )

    assert total == 2
    assert items[0].post_id == visible.post_id


def test_allowed_source_ids_filter_items_totals_and_every_option_dimension():
    session, repository = _repository()
    verified = str(uuid4())
    verified_other = str(uuid4())
    unverified = str(uuid4())
    verified_post = _post(
        categories=["technology"],
        language="en",
        source_id=verified,
        author="Verified Author",
        keywords=["verified-keyword"],
    )
    verified_post.source_title = "Verified Source"
    verified_other_post = _post(
        categories=["business"],
        language="fr",
        source_id=verified_other,
        author="Second Verified Author",
        keywords=["second-verified-keyword"],
    )
    verified_other_post.source_title = "Second Verified Source"
    unverified_post = _post(
        categories=["sports"],
        language="hu",
        source_id=unverified,
        author="Unverified Author",
        keywords=["unverified-keyword"],
    )
    unverified_post.source_title = "Unverified Source"
    session.add_all([verified_post, verified_other_post, unverified_post])
    session.commit()

    query = EffectiveFeedQuery(
        allowed_source_ids=[verified, verified_other],
        source_ids=[verified, unverified],
        limit=20,
    )
    items, total = repository.list_candidates(query)
    options = repository.list_filter_options(query, include_sources=True)

    assert [item.post_id for item in items] == [verified_post.post_id]
    assert total == 1
    assert options.categories == ["technology"]
    assert options.languages == ["en"]
    assert options.authors == ["Verified Author"]
    assert options.keywords == ["verified-keyword"]
    assert options.sources is not None
    assert {source.source_id for source in options.sources} == {
        verified,
        verified_other,
    }


def test_personal_category_options_rank_categories():
    session, repository = _repository()
    source = str(uuid4())
    posts = [
        _post(categories=["technology"], language="en", source_id=source),
        _post(categories=["technology"], language="en", source_id=source),
        _post(categories=["business"], language="en", source_id=source),
        _post(categories=["world"], language="en", source_id=source),
        _post(categories=[], language="en", source_id=source),
        _post(categories=[], language="en", source_id=source),
    ]
    session.add_all(posts)
    session.commit()

    options = repository.list_personal_filter_options(
        EffectiveFeedQuery(
            source_ids=[source],
            categories=["technology"],
            excluded_post_ids=[posts[3].post_id],
        )
    )

    assert options.categories == ["technology", "business"]


def test_filter_options_normalize_authors_and_keywords_from_all_rows():
    session, repository = _repository()
    source = str(uuid4())
    session.add_all(
        [
            _post(
                categories=["technology"],
                language="en",
                source_id=source,
                author="  Ada Lovelace ",
                keywords=["Climate", "policy"],
            ),
            _post(
                categories=["technology"],
                language="en",
                source_id=source,
                author="ada lovelace",
                keywords=[" climate ", "AI"],
            ),
            _post(
                categories=["technology"],
                language="en",
                source_id=source,
                author=" ",
                keywords=["", " POLICY "],
            ),
        ]
    )
    session.commit()

    options = repository.list_filter_options(
        EffectiveFeedQuery(source_ids=[source], limit=1)
    )

    assert options.authors == ["Ada Lovelace"]
    assert options.keywords == ["AI", "Climate", "POLICY"]
