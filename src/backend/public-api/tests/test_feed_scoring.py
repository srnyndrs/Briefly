import pytest
from datetime import UTC, datetime

from src.services.feed_scoring import FeedScoringService
from src.services.feed_types import ArticleEntity, UserPreferencesVO


class TestFeedScoringService:
    def test_rank_with_no_preferences_returns_in_order(self):
        service = FeedScoringService()
        prefs = UserPreferencesVO()

        articles = [
            ArticleEntity(
                article_id="1",
                source_id="s1",
                title="Article 1",
                canonical_url="http://a1.com",
                language="en",
                keywords=["tech", "news"],
            ),
            ArticleEntity(
                article_id="2",
                source_id="s2",
                title="Article 2",
                canonical_url="http://a2.com",
                language="en",
                keywords=["business"],
            ),
        ]

        ranked = service.rank(
            articles=articles, preferences=prefs, limit=10
        )

        assert len(ranked) == 2
        assert ranked[0].article_id == "1"
        assert ranked[1].article_id == "2"

    def test_rank_with_preferences_prioritizes_matching_categories(
        self,
    ):
        service = FeedScoringService()
        prefs = UserPreferencesVO(
            category_interests=["tech", "science"]
        )

        now = datetime.now(UTC)
        articles = [
            ArticleEntity(
                article_id="1",
                source_id="s1",
                title="Business Article",
                canonical_url="http://a1.com",
                language="en",
                category="business",
                keywords=["business"],
                published_at=now,
            ),
            ArticleEntity(
                article_id="2",
                source_id="s2",
                title="Tech Article",
                canonical_url="http://a2.com",
                language="en",
                category="tech",
                keywords=["tech"],
                published_at=now,
            ),
        ]

        ranked = service.rank(
            articles=articles, preferences=prefs, limit=10
        )

        assert len(ranked) == 2
        assert ranked[0].article_id == "2"  # Tech article first
        assert (
            ranked[1].article_id == "1"
        )  # Business article second

    def test_rank_respects_limit(self):
        service = FeedScoringService()
        prefs = UserPreferencesVO()

        articles = [
            ArticleEntity(
                article_id=str(i),
                source_id="s1",
                title=f"Article {i}",
                canonical_url=f"http://a{i}.com",
                language="en",
                keywords=[],
            )
            for i in range(10)
        ]

        ranked = service.rank(
            articles=articles, preferences=prefs, limit=5
        )

        assert len(ranked) == 5

    def test_rank_with_category_and_keyword_boost(self):
        service = FeedScoringService()
        prefs = UserPreferencesVO(
            category_interests=["tech", "science"]
        )

        now = datetime.now(UTC)
        articles = [
            ArticleEntity(
                article_id="1",
                source_id="s1",
                title="Keyword Only Match",
                canonical_url="http://a1.com",
                language="en",
                category="general",
                keywords=["tech"],  # +0.5 keyword match
                published_at=now,
            ),
            ArticleEntity(
                article_id="2",
                source_id="s2",
                title="Category Exact Match",
                canonical_url="http://a2.com",
                language="en",
                category="tech",  # +2.0 category match
                keywords=[],
                published_at=now,
            ),
            ArticleEntity(
                article_id="3",
                source_id="s3",
                title="Category and Keyword Match",
                canonical_url="http://a3.com",
                language="en",
                category="tech",  # +2.0
                keywords=["science"],  # +0.5 -> total 2.5
                published_at=now,
            ),
        ]

        ranked = service.rank(
            articles=articles, preferences=prefs, limit=10
        )

        assert ranked[0].article_id == "3"  # Score 2.5
        assert ranked[1].article_id == "2"  # Score 2.0
        assert ranked[2].article_id == "1"  # Score 0.5


class TestArticleEntity:
    def test_rank_published_at_returns_min_when_none(self):
        article = ArticleEntity(
            article_id="1",
            source_id="s1",
            title="No Pub Date",
            canonical_url="http://a.com",
            language="en",
            published_at=None,
        )

        # Should not raise, should return min datetime
        assert article.rank_published_at == datetime.min.replace(
            tzinfo=UTC
        )

    def test_entity_is_frozen(self):
        article = ArticleEntity(
            article_id="1",
            source_id="s1",
            title="Test",
            canonical_url="http://a.com",
            language="en",
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            article.title = "Modified"


class TestUserPreferencesVO:
    def test_empty_preferences_has_no_category_interests(self):
        prefs = UserPreferencesVO()

        assert not prefs.has_category_interests

    def test_preferences_with_category_interests_reports_true(self):
        prefs = UserPreferencesVO(category_interests=["tech"])

        assert prefs.has_category_interests

    def test_value_object_is_frozen(self):
        prefs = UserPreferencesVO(category_interests=["tech"])

        with pytest.raises(Exception):  # FrozenInstanceError
            prefs.category_interests = ["business"]

