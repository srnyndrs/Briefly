from unittest.mock import Mock
from uuid import uuid4

from src.services.feed_dtos import UserPreferencesDTO
from src.services.feed_service import (
    FeedService,
    GetArticleInput,
    ListFeedInput,
    SearchFeedInput,
)
from src.services.feed_types import ArticleEntity


class TestFeedServiceList:
    def test_execute_calls_repository_with_correct_parameters(self):
        # Arrange
        mock_repo = Mock()
        mock_prefs_reader = Mock()
        mock_scoring_service = Mock()

        article = ArticleEntity(
            article_id="a1",
            source_id="s1",
            title="Test",
            canonical_url="http://test.com",
            language="en",
        )
        mock_repo.list_feed_candidates.return_value = ([article], 1)
        mock_prefs_reader.get_preferences.return_value = (
            UserPreferencesDTO(preferred_categories=["tech"])
        )
        mock_scoring_service.rank.return_value = [article]

        use_case = FeedService(
            mock_repo, mock_prefs_reader, mock_scoring_service
        )
        user_id = uuid4()

        # Act
        result = use_case.list_feed(
            ListFeedInput(user_id=user_id, limit=20, offset=0)
        )

        # Assert
        mock_prefs_reader.get_preferences.assert_called_once_with(
            user_id
        )
        mock_repo.list_feed_candidates.assert_called_once()
        assert result.total == 1
        assert len(result.items) == 1

    def test_execute_returns_empty_when_no_articles(self):
        # Arrange
        mock_repo = Mock()
        mock_prefs_reader = Mock()
        mock_scoring_service = Mock()

        mock_repo.list_feed_candidates.return_value = ([], 0)
        mock_prefs_reader.get_preferences.return_value = (
            UserPreferencesDTO()
        )
        mock_scoring_service.rank.return_value = []

        use_case = FeedService(
            mock_repo, mock_prefs_reader, mock_scoring_service
        )

        # Act
        result = use_case.list_feed(
            ListFeedInput(user_id=uuid4(), limit=20, offset=0)
        )

        # Assert
        assert result.total == 0
        assert len(result.items) == 0

    def test_execute_ignores_profile_when_use_profile_false(self):
        mock_repo = Mock()
        mock_prefs_reader = Mock()
        mock_scoring_service = Mock()

        mock_repo.list_feed_candidates.return_value = ([], 0)
        mock_prefs_reader.get_preferences.return_value = (
            UserPreferencesDTO(
                excluded_languages=["en"],
                blocked_source_ids=["blocked"],
            )
        )
        mock_scoring_service.rank.return_value = []

        use_case = FeedService(
            mock_repo, mock_prefs_reader, mock_scoring_service
        )
        use_case.list_feed(
            ListFeedInput(
                user_id=uuid4(),
                limit=20,
                offset=0,
                use_profile=False,
            )
        )

        call_kwargs = mock_repo.list_feed_candidates.call_args[1]
        assert call_kwargs["excluded_languages"] == []
        assert call_kwargs["blocked_source_ids"] == []

    def test_execute_applies_query_override_for_excluded_languages(
        self,
    ):
        mock_repo = Mock()
        mock_prefs_reader = Mock()
        mock_scoring_service = Mock()

        mock_repo.list_feed_candidates.return_value = ([], 0)
        mock_prefs_reader.get_preferences.return_value = (
            UserPreferencesDTO(
                excluded_languages=["fr"],
            )
        )
        mock_scoring_service.rank.return_value = []

        use_case = FeedService(
            mock_repo, mock_prefs_reader, mock_scoring_service
        )
        use_case.list_feed(
            ListFeedInput(
                user_id=uuid4(),
                limit=20,
                offset=0,
                exclude_languages=["en"],
            )
        )

        call_kwargs = mock_repo.list_feed_candidates.call_args[1]
        assert call_kwargs["excluded_languages"] == ["en"]


class TestFeedServiceSearch:
    def test_execute_calls_repository_with_search_query(self):
        # Arrange
        mock_repo = Mock()
        mock_prefs_reader = Mock()

        article = ArticleEntity(
            article_id="a1",
            source_id="s1",
            title="Python Programming",
            canonical_url="http://test.com",
            language="en",
        )
        mock_repo.search_feed.return_value = ([article], 1)
        mock_prefs_reader.get_preferences.return_value = (
            UserPreferencesDTO()
        )

        use_case = FeedService(mock_repo, mock_prefs_reader)
        user_id = uuid4()

        # Act
        result = use_case.search_feed(
            SearchFeedInput(
                user_id=user_id, q="python", limit=20, offset=0
            )
        )

        # Assert
        mock_repo.search_feed.assert_called_once()
        call_kwargs = mock_repo.search_feed.call_args[1]
        assert call_kwargs["q"] == "python"
        assert result.total == 1

    def test_execute_applies_preferences_filters(self):
        # Arrange
        mock_repo = Mock()
        mock_prefs_reader = Mock()

        mock_repo.search_feed.return_value = ([], 0)
        prefs = UserPreferencesDTO(
            excluded_languages=["fr"],
            blocked_source_ids=["blocked_source"],
        )
        mock_prefs_reader.get_preferences.return_value = prefs

        use_case = FeedService(mock_repo, mock_prefs_reader)

        # Act
        use_case.search_feed(
            SearchFeedInput(
                user_id=uuid4(), q="test", limit=20, offset=0
            )
        )

        # Assert
        mock_repo.search_feed.assert_called_once()
        call_kwargs = mock_repo.search_feed.call_args[1]
        assert call_kwargs["excluded_languages"] == ["fr"]
        assert call_kwargs["blocked_source_ids"] == [
            "blocked_source"
        ]

    def test_execute_ignores_profile_when_use_profile_false(self):
        mock_repo = Mock()
        mock_prefs_reader = Mock()

        mock_repo.search_feed.return_value = ([], 0)
        mock_prefs_reader.get_preferences.return_value = (
            UserPreferencesDTO(
                excluded_languages=["fr"],
                blocked_source_ids=["blocked_source"],
            )
        )

        use_case = FeedService(mock_repo, mock_prefs_reader)
        use_case.search_feed(
            SearchFeedInput(
                user_id=uuid4(),
                q="test",
                limit=20,
                offset=0,
                use_profile=False,
            )
        )

        call_kwargs = mock_repo.search_feed.call_args[1]
        assert call_kwargs["excluded_languages"] == []
        assert call_kwargs["blocked_source_ids"] == []


class TestFeedServiceGetArticle:
    def test_execute_returns_article_when_found(self):
        # Arrange
        mock_repo = Mock()
        article = ArticleEntity(
            article_id="a1",
            source_id="s1",
            title="Test",
            canonical_url="http://test.com",
            language="en",
        )
        mock_repo.get_article.return_value = article

        use_case = FeedService(mock_repo, Mock())

        # Act
        result = use_case.get_article(
            GetArticleInput(article_id=uuid4())
        )

        # Assert
        assert result is not None
        assert result.article_id == "a1"

    def test_execute_returns_none_when_not_found(self):
        # Arrange
        mock_repo = Mock()
        mock_repo.get_article.return_value = None

        use_case = FeedService(mock_repo, Mock())

        # Act
        result = use_case.get_article(
            GetArticleInput(article_id=uuid4())
        )

        # Assert
        assert result is None
