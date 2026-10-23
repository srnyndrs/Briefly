from datetime import UTC, datetime
from uuid import uuid4

import pytest

from src.models.read_models import (
    PostEnrichmentProjection,
    PostProjection,
    UserPreferencesProjection,
)
from src.repositories.feed_repository import PostRepository
from src.services.feed_models import EffectiveFeedQuery


@pytest.fixture(params=["sqlite", "postgresql"])
def collection_db(request):
    if request.param == "postgresql":
        yield request.getfixturevalue("postgres_db")
    else:
        yield request.getfixturevalue("db")


def test_muting_matches_decoded_keywords_only(collection_db):
    posts = [
        _post(
            categories=[], language="en", source_id="source", keywords=keywords
        )
        for keywords in [
            [r'árvíz "100%_growth" \path'],
            [r'árvíz "1000xgrowth" \path'],
            ["Co$t"],
            ["alpha", "beta"],
            [],
        ]
    ]
    collection_db.add_all(posts)
    collection_db.commit()
    items, total = PostRepository(collection_db).list_candidates(
        EffectiveFeedQuery(
            muted_keywords=[
                r'árvíz "100%_GROWTH" \PATH',
                "cost",
                "alpha beta",
                '", "',
            ]
        )
    )
    # Decode literal values, preserve escaping, and never join separate keywords.
    assert total == 3
    assert {item.post_id for item in items} == {
        posts[index].post_id for index in (1, 3, 4)
    }


def test_collection_round_trip_and_replacement(collection_db):
    values = ["science", "health"]
    post = _post(
        categories=values, language="en", source_id="source", keywords=values
    )
    preferences = UserPreferencesProjection(
        user_id="user",
        muted_keywords=values,
        muted_categories=values,
        blocked_source_ids=values,
        languages=values,
    )
    enrichment = PostEnrichmentProjection(
        post_id=post.post_id,
        post_revision=1,
        status="completed",
        enrichment_revision=1,
        category_ids=values,
    )
    overlapping = _post(categories=[], language="en", source_id="other-source")
    overlapping.canonical_url = post.canonical_url
    collection_db.add_all([post, overlapping, preferences, enrichment])
    collection_db.commit()
    collection_db.expire_all()
    assert (
        collection_db.query(PostProjection)
        .filter_by(canonical_url=post.canonical_url)
        .count()
        == 2
    )
    fields = [
        (post, "categories"),
        (post, "keywords"),
        (enrichment, "category_ids"),
        *[
            (preferences, name)
            for name in (
                "muted_keywords",
                "muted_categories",
                "blocked_source_ids",
                "languages",
            )
        ],
    ]
    for model, name in fields:
        assert getattr(model, name) == values
        setattr(model, name, [])
    collection_db.commit()
    collection_db.expire_all()
    for model, name in fields:
        assert getattr(model, name) == []


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


def test_filter_options_ignore_their_own_active_dimension(db):
    repository = PostRepository(db)
    source = str(uuid4())
    other_source = str(uuid4())
    db.add_all(
        [
            _post(
                categories=["technology"],
                language="en",
                source_id=source,
                author="  Ada Lovelace ",
                keywords=["Climate", "policy"],
            ),
            _post(
                categories=["business"],
                language="hu",
                source_id=source,
                author="ada lovelace",
                keywords=[" climate ", "AI"],
            ),
            _post(categories=[], language="en", source_id=source),
            _post(categories=["sports"], language="de", source_id=other_source),
        ]
    )
    db.commit()

    category_options = repository.list_filter_options(
        EffectiveFeedQuery(
            source_ids=[source], categories=["technology"], limit=1
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
    all_options = repository.list_filter_options(
        EffectiveFeedQuery(source_ids=[source], limit=1)
    )
    assert [author.casefold() for author in all_options.authors] == [
        "ada lovelace"
    ]
    assert all(author == author.strip() for author in all_options.authors)
    assert {keyword.casefold() for keyword in all_options.keywords} == {
        "ai",
        "climate",
        "policy",
    }
    assert all(keyword == keyword.strip() for keyword in all_options.keywords)
    assert category_options.sources is None
    assert language_options.sources is None
    assert source_options.sources is not None
    assert {option.source_id for option in source_options.sources} == {
        source,
        other_source,
    }


def test_category_collection_selection_muting_and_pagination(db):
    repository = PostRepository(db)
    posts = [
        _post(
            categories=["science", "health"],
            language="en",
            source_id="source",
            keywords=["business"],
        ),
        _post(categories=["science"], language="en", source_id="source"),
        _post(categories=["health"], language="en", source_id="source"),
        _post(
            categories=["business"],
            language="en",
            source_id="source",
            keywords=["science"],
        ),
        _post(categories=[], language="en", source_id="source"),
    ]
    for post in posts:
        post.source_category = "science"
    db.add_all(posts)
    db.commit()
    query = dict(categories=[" SCIENCE ", "health"], limit=1)
    first, total = repository.list_candidates(EffectiveFeedQuery(**query))
    second, second_total = repository.list_candidates(
        EffectiveFeedQuery(**query, offset=1)
    )
    third, third_total = repository.list_candidates(
        EffectiveFeedQuery(**query, offset=2)
    )
    assert total == second_total == third_total == 3
    assert {page[0].post_id for page in (first, second, third)} == {
        post.post_id for post in posts[:3]
    }
    visible, total = repository.list_candidates(
        EffectiveFeedQuery(muted_categories=[" HEALTH "])
    )
    assert total == 3
    assert {post.post_id for post in visible} == {
        posts[index].post_id for index in (1, 3, 4)
    }
    assert repository.list_filter_options(EffectiveFeedQuery()).categories == [
        "business",
        "health",
        "science",
    ]
    assert repository.list_filter_options(
        EffectiveFeedQuery(muted_categories=["health"])
    ).categories == ["business", "science"]


def test_allowed_source_ids_filter_items_totals_and_every_option_dimension(db):
    repository = PostRepository(db)
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
    db.add_all([verified_post, verified_other_post, unverified_post])
    db.commit()

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


def test_personal_category_options_rank_categories(db):
    repository = PostRepository(db)
    source = str(uuid4())
    posts = [
        _post(categories=["technology"], language="en", source_id=source),
        _post(categories=["technology"], language="en", source_id=source),
        _post(categories=["business"], language="en", source_id=source),
        _post(categories=["world"], language="en", source_id=source),
        _post(categories=[], language="en", source_id=source),
        _post(categories=[], language="en", source_id=source),
    ]
    db.add_all(posts)
    db.commit()

    options = repository.list_personal_filter_options(
        EffectiveFeedQuery(
            source_ids=[source],
            categories=["technology"],
        )
    )

    assert options.categories == ["technology", "business", "world"]
