import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(text, "lxml")
    cleaned = soup.get_text("\n")
    lines = [line.strip() for line in cleaned.splitlines()]
    return "\n".join([line for line in lines if line])


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
        if content and _HTML_TAG_RE.search(content):
            content = _strip_html(content)
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
        logger.warning("Content extraction failed for %s: %s", url, exc)
        return {"error": str(exc), "content": "", "title": ""}
