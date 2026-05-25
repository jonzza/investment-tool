"""Fetches news articles from RSS feeds."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import hashlib

import feedparser
from bs4 import BeautifulSoup
from loguru import logger

from config import RSS_FEEDS, MAX_ARTICLES_PER_FEED


@dataclass
class Article:
    """Normalized article from any RSS feed."""
    id: str               # hash of url, for deduplication
    title: str
    url: str
    source: str
    region: str           # FI / EU / US / GLOBAL
    published_at: Optional[datetime]
    summary: str          # short lead text from feed

    @property
    def short_text(self) -> str:
        """Short form for screening - title + summary."""
        return f"{self.title}\n\n{self.summary}"


def _clean_html(html: str) -> str:
    """Strip HTML tags from RSS summary text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ", strip=True)


def _make_id(url: str) -> str:
    """Stable id from URL for deduplication."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]


def _parse_published(entry) -> Optional[datetime]:
    """Best-effort parsing of publication date."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6])
        except (TypeError, ValueError):
            pass
    return None


def fetch_feed(feed_config: dict) -> list[Article]:
    """Fetch and normalize one RSS feed."""
    name = feed_config["name"]
    url = feed_config["url"]
    region = feed_config["region"]

    logger.info(f"Fetching {name}...")
    try:
        parsed = feedparser.parse(url)
    except Exception as e:
        logger.error(f"Failed to fetch {name}: {e}")
        return []

    if parsed.bozo and not parsed.entries:
        logger.warning(f"{name} feed had errors and no entries")
        return []

    articles = []
    for entry in parsed.entries[:MAX_ARTICLES_PER_FEED]:
        try:
            article_url = entry.get("link", "")
            if not article_url:
                continue
            summary_html = entry.get("summary", entry.get("description", ""))
            articles.append(
                Article(
                    id=_make_id(article_url),
                    title=entry.get("title", "(no title)").strip(),
                    url=article_url,
                    source=name,
                    region=region,
                    published_at=_parse_published(entry),
                    summary=_clean_html(summary_html),
                )
            )
        except Exception as e:
            logger.warning(f"Skipping malformed entry in {name}: {e}")
            continue

    logger.info(f"  -> {len(articles)} articles from {name}")
    return articles


def fetch_all() -> list[Article]:
    """Fetch all configured feeds, deduplicate by URL."""
    all_articles: dict[str, Article] = {}
    for feed in RSS_FEEDS:
        for article in fetch_feed(feed):
            if article.id not in all_articles:
                all_articles[article.id] = article

    logger.info(f"Total unique articles: {len(all_articles)}")
    return list(all_articles.values())


if __name__ == "__main__":
    # Standalone test: print fetched articles
    articles = fetch_all()
    for a in articles[:5]:
        print(f"[{a.source} / {a.region}] {a.title}")
        print(f"  {a.url}")
        print(f"  {a.summary[:200]}")
        print()
