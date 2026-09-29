import logging
import re
from time import perf_counter
from typing import Any
from urllib.parse import urljoin, urlsplit

from newspaper import Article, Config

from src.config.settings import settings

logger = logging.getLogger(__name__)


_HTML_TAG_RE = re.compile(r"<[^>]+>")
_IMAGE_METADATA_ATTRIBUTES = {
    "property": ("og:image", "og:image:url", "twitter:image"),
    "name": ("twitter:image",),
}


def _image_metadata_xpath() -> str:
    selectors = [
        f"@{attribute}='{value}'"
        for attribute, values in _IMAGE_METADATA_ATTRIBUTES.items()
        for value in values
    ]
    return f"//meta[{' or '.join(selectors)}]/@content"


class _MetadataArticle(Article):
    def fetch_images(self) -> None:
        images = self.doc.xpath(_image_metadata_xpath())
        image = next(
            (value.strip() for value in images if value.strip()), None
        )
        self.top_image = urljoin(self.url, image) if image else None


def normalize_article_url(value: Any) -> str | None:
    if value is None or value == "":
        return None
    url = value.strip() if isinstance(value, str) else ""
    try:
        parts = urlsplit(url)
        if (
            parts.scheme in {"http", "https"}
            and parts.hostname
            and parts.username is None
            and parts.password is None
            and (parts.port is None or parts.port > 0)
            and not any(
                char.isspace() or ord(char) < 32 for char in url
            )
        ):
            return url
    except ValueError:
        pass

    # Escaping preserves suspicious punctuation without logging query values.
    display = re.sub(r"(//)[^/?#]*@", r"\1[redacted]@", url)
    display = display.split("?", 1)[0].split("#", 1)[0][:200]
    logger.warning("Invalid article link: %r", display)
    return None


def normalize_html_text(text: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(text, "lxml")
    for line_break in soup.find_all("br"):
        line_break.replace_with("\n")
    for block in soup.find_all(
        [
            "address",
            "article",
            "blockquote",
            "div",
            "li",
            "p",
            "section",
        ]
    ):
        block.append("\n")
    cleaned = soup.get_text()
    lines = [line.strip() for line in cleaned.splitlines()]
    return "\n".join([line for line in lines if line])


def extract_article(url: str) -> dict[str, Any]:
    normalized_url = normalize_article_url(url)
    if normalized_url is None:
        return {"error": "invalid_url", "outcome": "invalid_url"}
    url = normalized_url
    started = perf_counter()
    host = urlsplit(url).hostname
    outcome = "failed"
    error_type = None
    try:
        config = Config()
        config.request_timeout = (
            settings.article_request_timeout_seconds
        )
        config.fetch_images = False
        article = _MetadataArticle(url, config=config)
        article.download()
        article.parse()

        content = (
            article.text_cleaned
            if article.text_cleaned
            else article.text or None
        )
        if content and _HTML_TAG_RE.search(content):
            content = normalize_html_text(content)
        content = content.strip() if content else None
        outcome = "success" if content else "empty"
        image = article.top_image or article.top_img or None
        keywords = article.meta_keywords or article.keywords or None

        return {
            "outcome": outcome,
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
        outcome = "failed"
        error_type = type(exc).__name__
        return {"error": error_type, "outcome": outcome}
    finally:
        logger.log(
            logging.INFO if outcome == "success" else logging.WARNING,
            "Article extraction (host=%s, outcome=%s, error_type=%s, "
            "duration_seconds=%.3f)",
            host,
            outcome,
            error_type,
            perf_counter() - started,
        )
