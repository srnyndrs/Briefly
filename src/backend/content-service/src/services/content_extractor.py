import logging
from typing import Any

logger = logging.getLogger(__name__)


def extract_article(url: str) -> dict[str, Any]:
    try:
        from newspaper import Article

        article = Article(url)
        article.download()
        article.parse()

        content = (
            article.text_cleaned
            if article.text_cleaned
            else article.text or None
        )
        image = article.top_image or article.top_img or None
        keywords = article.meta_keywords or article.keywords or None

        return {
            "title": article.title,
            "description": article.meta_description,
            "content": content,
            "image": image,
            "authors": article.authors,
            "language": article.meta_lang,
            "keywords": keywords,
            "publish_date": article.publish_date or None,
        }
    except Exception as exc:
        logger.warning(
            "Content extraction failed for %s: %s", url, exc
        )
        return {"error": str(exc), "content": "", "title": ""}
