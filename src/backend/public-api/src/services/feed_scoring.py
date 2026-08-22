from src.services.feed_types import ArticleEntity, UserPreferencesVO


class FeedScoringService:
    def rank(
        self,
        *,
        articles: list[ArticleEntity],
        preferences: UserPreferencesVO,
        limit: int,
    ) -> list[ArticleEntity]:
        if not preferences.has_category_interests:
            return articles[:limit]

        interests = {
            cat.lower(): 1.0
            for cat in preferences.category_interests
        }

        def _score(
            article: ArticleEntity,
        ) -> tuple[float, object, object]:
            score = 0.0

            # Direct category affinity boost
            if (
                article.category
                and article.category.lower() in interests
            ):
                score += interests[article.category.lower()] * 2.0

            # Keyword / Topic affinity boost
            article_keywords = {
                k.lower() for k in (article.keywords or [])
            }
            keyword_matches = len(
                article_keywords.intersection(interests.keys())
            )
            score += keyword_matches * 0.5

            return (
                score,
                article.rank_published_at,
                article.rank_updated_at,
            )

        return sorted(articles, key=_score, reverse=True)[:limit]

