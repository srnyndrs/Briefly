from src.services.feed_types import ArticleEntity, UserPreferencesVO


class FeedScoringService:
    def rank(
        self,
        *,
        articles: list[ArticleEntity],
        preferences: UserPreferencesVO,
        limit: int,
    ) -> list[ArticleEntity]:
        if not preferences.has_preferred_categories:
            return articles[:limit]

        preferred = {
            cat.lower() for cat in preferences.preferred_categories
        }

        def _score(
            article: ArticleEntity,
        ) -> tuple[int, object, object]:
            categories = {cat.lower() for cat in article.categories}
            overlap = len(categories.intersection(preferred))
            return (
                overlap,
                article.rank_published_at,
                article.rank_updated_at,
            )

        return sorted(articles, key=_score, reverse=True)[:limit]
