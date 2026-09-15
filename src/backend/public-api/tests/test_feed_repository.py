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
    *, category: str | None, language: str, source_id: str
) -> PostProjection:
    now = datetime.now(UTC)
    return PostProjection(
        post_id=str(uuid4()),
        source_id=source_id,
        source_title="Test Source",
        canonical_url=f"https://example.com/{uuid4()}",
        title="Article",
        category=category,
        language=language,
        keywords=[],
        published_at=now,
        updated_at=now,
    )


def test_filter_options_ignore_their_own_active_dimension():
    session, repository = _repository()
    source = str(uuid4())
    other_source = str(uuid4())
    session.add_all(
        [
            _post(
                category=" Technology ", language="en", source_id=source
            ),
            _post(category="business", language="hu", source_id=source),
            _post(category=None, language="en", source_id=source),
            _post(
                category="sports", language="de", source_id=other_source
            ),
        ]
    )
    session.commit()

    category_options = repository.list_filter_options(
        EffectiveFeedQuery(
            source_ids=[source], categories=["technology"]
        )
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
    visible = _post(
        category="technology", language="en", source_id=allowed
    )
    visible.published_at = now
    muted = _post(category="sports", language="en", source_id=allowed)
    blocked_post = _post(
        category="technology", language="en", source_id=blocked
    )
    old = _post(category="technology", language="en", source_id=allowed)
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


def test_personal_category_options_rank_normalized_categories():
    session, repository = _repository()
    source = str(uuid4())
    posts = [
        _post(category=" Technology ", language="en", source_id=source),
        _post(category="technology", language="en", source_id=source),
        _post(category="business", language="en", source_id=source),
        _post(category="World", language="en", source_id=source),
        _post(category=None, language="en", source_id=source),
        _post(category=" ", language="en", source_id=source),
    ]
    session.add_all(posts)
    session.commit()

    options = repository.list_personal_filter_options(
        EffectiveFeedQuery(
            source_ids=[source],
            categories=["technology"],
            excluded_post_ids=[posts[0].post_id],
        )
    )

    assert options.categories == ["business", "technology", "world"]
