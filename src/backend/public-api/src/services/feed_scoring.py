from src.services.feed_models import PostDTO, UserPreferencesDTO


class FeedScoringService:
    def rank(
        self,
        *,
        articles: list[PostDTO],
        preferences: UserPreferencesDTO,
        limit: int,
    ) -> list[PostDTO]:
        if not preferences.has_category_interests:
            return articles[:limit]

        interests = {
            cat.lower(): 1.0 for cat in preferences.category_interests
        }

        def _score(
            post: PostDTO,
        ) -> tuple[float, object, object]:
            score = 0.0

            # Direct category affinity boost
            if post.category and post.category.lower() in interests:
                score += interests[post.category.lower()] * 2.0

            # Keyword / Topic affinity boost
            post_keywords = {k.lower() for k in (post.keywords or [])}
            keyword_matches = len(
                post_keywords.intersection(interests.keys())
            )
            score += keyword_matches * 0.5

            return (
                score,
                post.rank_published_at,
                post.rank_updated_at,
            )

        return sorted(articles, key=_score, reverse=True)[:limit]
