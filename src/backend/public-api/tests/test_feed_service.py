from unittest.mock import Mock
from uuid import uuid4

from src.services.feed_models import PostDTO, UserPreferencesDTO
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
    post = PostDTO(post_id="post", title="Post")
    preferences.get_preferences.return_value = UserPreferencesDTO(
        languages=["hu"],
        muted_keywords=["crypto"],
        muted_categories=["sports"],
        blocked_source_ids=["blocked"],
    )
    repository.list_candidates.return_value = ([post], 1)
    monkeypatch.setattr(
        "src.services.feed_service.account_list_subscriptions",
        lambda _: [{"source_id": "subscribed"}],
    )

    result = FeedService(repository, preferences).get_personal_feed(
        PersonalFeedInput(user_id=uuid4(), limit=20, offset=0)
    )

    assert result.items == [post]
    query = repository.list_candidates.call_args.args[0]
    assert query.languages == ["hu"]
    assert query.source_ids == ["subscribed"]
    assert query.sort == "freshness"


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
    repository.list_candidates.assert_not_called()


def test_explore_feed_uses_explicit_filters_not_saved_scope():
    repository = Mock()
    preferences = Mock()
    preferences.get_preferences.return_value = UserPreferencesDTO(
        languages=["hu"], blocked_source_ids=["blocked"]
    )
    repository.list_candidates.return_value = ([], 0)

    FeedService(repository, preferences).get_explore_feed(
        ExploreFeedInput(
            user_id=uuid4(),
            limit=20,
            offset=0,
            categories=["technology"],
            languages=["en"],
            sort="oldest",
        )
    )

    query = repository.list_candidates.call_args.args[0]
    assert query.languages == ["en"]
    assert query.source_ids is None
    assert query.sort == "oldest"
    assert query.blocked_source_ids == ["blocked"]


def test_get_post_delegates_to_repository():
    repository = Mock()
    repository.get_post.return_value = PostDTO(
        post_id="post", title="Post"
    )

    result = FeedService(repository, Mock()).get_post(
        GetPostInput(post_id=uuid4())
    )

    assert result is not None
    assert result.post_id == "post"
