from unittest.mock import Mock
from uuid import uuid4

from src.services.feed_models import (
    FilterOptionsDTO,
    PostDTO,
    UserPreferencesDTO,
)
from src.services.feed_service import (
    ExploreFeedInput,
    FeedService,
    GetPostInput,
    PersonalFeedInput,
)


def test_personal_feed_applies_preferences_and_subscriptions(
    monkeypatch,
):
    repository = Mock()
    preferences = Mock()
    post = PostDTO(
        post_id="post",
        title="Post",
        source_id=str(uuid4()),
        source_title="Test Source",
    )
    preferences.get_preferences.return_value = UserPreferencesDTO(
        languages=["hu"],
        muted_keywords=["crypto"],
        muted_categories=["sports"],
        blocked_source_ids=["blocked"],
    )
    repository.list_candidates.return_value = ([post], 1)
    repository.list_headlines.return_value = [post]
    repository.list_personal_filter_options.return_value = (
        FilterOptionsDTO(categories=[], languages=[])
    )
    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [{"source_id": "subscribed"}],
    )

    result = FeedService(repository, preferences).get_personal_feed(
        PersonalFeedInput(
            user_id=uuid4(),
            limit=20,
            offset=0,
            include_filter_options=True,
        )
    )

    assert result.items == [post]
    query = repository.list_candidates.call_args.args[0]
    assert query.languages == ["hu"]
    assert query.source_ids == ["subscribed"]
    assert query.sort == "freshness"
    assert query.excluded_post_ids == [post.post_id]
    repository.list_personal_filter_options.assert_called_once_with(
        query
    )


def test_personal_feed_without_subscriptions_skips_repository(
    monkeypatch,
):
    repository = Mock()
    preferences = Mock()
    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [],
    )

    result = FeedService(repository, preferences).get_personal_feed(
        PersonalFeedInput(
            user_id=uuid4(),
            limit=20,
            offset=0,
            include_filter_options=True,
        )
    )

    assert result.items == []
    assert result.total == 0
    assert result.filter_options is not None
    assert result.filter_options.categories == []
    assert result.filter_options.authors == []
    assert result.filter_options.keywords == []
    repository.list_candidates.assert_not_called()


def test_personal_feed_keeps_headlines_unfiltered_and_excludes_them(
    monkeypatch,
):
    repository = Mock()
    preferences = Mock()
    headlines = [
        PostDTO(
            post_id=f"headline-{index}",
            title="Headline",
            source_id=str(uuid4()),
            source_title="Source",
        )
        for index in range(3)
    ]
    repository.list_headlines.return_value = headlines
    repository.list_candidates.return_value = ([], 0)
    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [{"source_id": "subscribed"}],
    )

    result = FeedService(repository, preferences).get_personal_feed(
        PersonalFeedInput(
            user_id=uuid4(),
            limit=20,
            offset=0,
            category="technology",
        )
    )

    headline_query = repository.list_headlines.call_args.args[0]
    content_query = repository.list_candidates.call_args.args[0]
    assert headline_query.categories is None
    assert content_query.categories == ["technology"]
    assert content_query.excluded_post_ids == [
        post.post_id for post in headlines
    ]
    assert result.headlines == headlines


def test_explore_feed_uses_explicit_filters_not_saved_scope():
    repository = Mock()
    preferences = Mock()
    preferences.get_preferences.return_value = UserPreferencesDTO(
        languages=["hu"], blocked_source_ids=["blocked"]
    )
    repository.list_candidates.return_value = ([], 0)
    repository.list_filter_options.return_value = FilterOptionsDTO(
        categories=[], languages=[], sources=[]
    )

    FeedService(repository, preferences).get_explore_feed(
        ExploreFeedInput(
            user_id=uuid4(),
            limit=20,
            offset=0,
            categories=["technology"],
            languages=["en"],
            sort="oldest",
            include_filter_options=True,
        )
    )

    query = repository.list_candidates.call_args.args[0]
    assert query.languages == ["en"]
    assert query.source_ids is None
    assert query.sort == "oldest"
    assert query.blocked_source_ids == ["blocked"]
    repository.list_filter_options.assert_called_once_with(
        query, include_sources=True
    )


def test_get_post_delegates_to_repository():
    repository = Mock()
    repository.get_post.return_value = PostDTO(
        post_id="post",
        title="Post",
        source_id=str(uuid4()),
        source_title="Test Source",
    )

    result = FeedService(repository, Mock()).get_post(
        GetPostInput(post_id=uuid4())
    )

    assert result is not None
    assert result.post_id == "post"
