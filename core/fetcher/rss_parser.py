"""
ContentOrbit Enterprise - RSS Feed Parser
==========================================
Fetches and parses content from RSS/Atom feeds.
Handles multiple languages, content extraction, and word counting.

Usage:
    from core.fetcher import RSSFetcher

    fetcher = RSSFetcher(config, db)
    article = await fetcher.fetch_random_article()
"""

import asyncio
import random
import re
import hashlib
from datetime import datetime
from typing import Optional, List, Tuple
from urllib.parse import urlparse
import logging

import feedparser
import httpx
from bs4 import BeautifulSoup

from core.models import RSSFeed, FetchedArticle, FeedCategory
from core.config_manager import ConfigManager
from core.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class RSSFetcher:
    """
    RSS Feed Fetcher

    Responsibilities:
    - Fetch RSS/Atom feeds asynchronously
    - Extract and clean article content
    - Filter by word count and duplicates
    - Smart feed selection based on priority
    """

    # User agent to avoid blocks
    USER_AGENT = "ContentOrbit/1.0 (RSS Reader; +https://contentorbit.io)"

    # Timeout for HTTP requests
    REQUEST_TIMEOUT = 30.0

    def __init__(self, config: ConfigManager, db: DatabaseManager):
        """
        Initialize RSS Fetcher

        Args:
            config: ConfigManager instance
            db: DatabaseManager instance
        """
        self.config = config
        self.db = db
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=self.REQUEST_TIMEOUT,
                headers={"User-Agent": self.USER_AGENT},
                follow_redirects=True,
            )
        return self._http_client

    async def close(self):
        """Close HTTP client"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN FETCH METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    async def fetch_random_article(
        self, category: Optional[FeedCategory] = None, min_words: Optional[int] = None
    ) -> Optional[FetchedArticle]:
        """
        Fetch a random article from active feeds

        Args:
            category: Filter by category (optional)
            min_words: Minimum word count (uses config default if None)

        Returns:
            FetchedArticle if found, None otherwise
        """
        min_words = min_words or self.config.app_config.min_article_words

        # Get active feeds (sorted by priority)
        feeds = self.config.get_active_feeds(category)

        if not feeds:
            logger.warning("No active feeds available")
            self.db.log_warning(
                component="fetcher",
                action="no_feeds",
                message="No active RSS feeds configured",
            )
            return None

        # Shuffle with weighted priority
        feeds = self._weighted_shuffle(feeds)

        # Try each feed until we find valid content
        for feed in feeds:
            try:
                article = await self._fetch_from_feed(feed, min_words)
                if article:
                    logger.info(f"✅ Found article: {article.title[:50]}...")
                    self.db.log_info(
                        component="fetcher",
                        action="article_found",
                        message=f"Found article from {feed.name}",
                        feed_name=feed.name,
                        article_title=article.title,
                    )
                    return article
            except Exception as e:
                logger.error(f"Error fetching from {feed.name}: {e}")
                self.db.log_error(
                    component="fetcher",
                    action="feed_error",
                    message=f"Failed to fetch from {feed.name}",
                    error=e,
                    feed_url=feed.url,
                )
                continue

        logger.warning("No valid articles found in any feed")
        return None

    async def _fetch_from_feed(
        self, feed: RSSFeed, min_words: int
    ) -> Optional[FetchedArticle]:
        """
        Fetch a valid article from a specific feed

        Args:
            feed: RSSFeed to fetch from
            min_words: Minimum word count

        Returns:
            FetchedArticle if found
        """
        logger.info(f"🔍 Checking feed: {feed.name}")

        # Fetch feed content
        client = await self._get_client()
        response = await client.get(feed.url)
        response.raise_for_status()

        # Parse feed
        parsed = feedparser.parse(response.text)

        if not parsed.entries:
            logger.debug(f"No entries in feed: {feed.name}")
            return None

        # Shuffle entries for randomness
        entries = list(parsed.entries)
        random.shuffle(entries)

        # Check each entry
        for entry in entries[:20]:  # Limit to first 20 to avoid long processing
            try:
                # Get URL
                url = entry.get("link", "")
                if not url:
                    continue

                # Check for duplicates
                if self.db.is_url_posted(url):
                    logger.debug(f"Skipping duplicate: {url}")
                    continue

                # Get title
                title = self._clean_text(entry.get("title", ""))
                if not title:
                    continue

                # Get content
                content = self._extract_content(entry)
                word_count = self._count_words(content)

                # Check word count
                if word_count < min_words:
                    logger.debug(
                        f"Skipping (too short: {word_count} words): {title[:30]}"
                    )
                    continue

                # Get summary
                summary = self._clean_text(entry.get("summary", ""))[:500]

                # Best-effort image URL (from feed + optional og:image)
                image_url = self._extract_image_url_from_entry(entry)
                if not image_url:
                    image_url = await self._extract_image_url_from_page(url)

                # Get author
                author = entry.get("author", entry.get("dc_creator", ""))

                # Get published date
                published = None
                if entry.get("published_parsed"):
                    published = datetime(*entry.published_parsed[:6])

                # Detect language
                language = self._detect_language(title + " " + content[:200])

                # Create article
                article = FetchedArticle(
                    id=self._generate_article_id(url),
                    source_feed_id=feed.id,
                    original_url=url,
                    title=title,
                    summary=summary,
                    content=content,
                    image_url=image_url,
                    author=author,
                    published_date=published,
                    word_count=word_count,
                    language=language,
                )

                # Update feed last fetched
                self.config.update_feed(feed.id, last_fetched=datetime.utcnow())

                return article

            except Exception as e:
                logger.debug(f"Error processing entry: {e}")
                continue

        return None

    # ═══════════════════════════════════════════════════════════════════════════
    # IMAGE EXTRACTION
    # ═══════════════════════════════════════════════════════════════════════════

    def _extract_image_url_from_entry(self, entry: dict) -> Optional[str]:
        """Try to extract an image URL from a feed entry without extra HTTP calls."""
        try:
            # media:thumbnail (common in RSS)
            thumbs = entry.get("media_thumbnail") or entry.get("media:thumbnail")
            if thumbs and isinstance(thumbs, list):
                url = thumbs[0].get("url")
                if self._is_http_url(url):
                    return url

            # media:content (sometimes includes image)
            media = entry.get("media_content") or entry.get("media:content")
            if media and isinstance(media, list):
                url = media[0].get("url")
                if self._is_http_url(url):
                    return url

            # enclosures (Atom/RSS)
            enclosures = entry.get("enclosures") or []
            if isinstance(enclosures, list):
                for enc in enclosures:
                    enc_url = enc.get("href") or enc.get("url")
                    enc_type = (enc.get("type") or "").lower()
                    if self._is_http_url(enc_url) and (
                        enc_type.startswith("image/")
                        or any(
                            ext in (enc_url or "").lower()
                            for ext in (".jpg", ".jpeg", ".png", ".webp")
                        )
                    ):
                        return enc_url

            # Look for <img> in content/summary HTML
            html_candidates = []
            if "content" in entry and entry.content:
                html_candidates.append(entry.content[0].get("value", ""))
            html_candidates.append(entry.get("summary", ""))
            html_candidates.append(entry.get("description", ""))

            for html in html_candidates:
                if not html:
                    continue
                soup = BeautifulSoup(html, "lxml")
                img = soup.find("img")
                if img:
                    src = img.get("src") or img.get("data-src")
                    if self._is_http_url(src):
                        return src

        except Exception:
            return None

        return None

    async def _extract_image_url_from_page(self, url: str) -> Optional[str]:
        """Fallback: fetch page and parse og:image/twitter:image. Best-effort with short timeout."""
        if not self._is_http_url(url):
            return None

        try:
            client = await self._get_client()
            # Keep this lightweight to avoid slowing pipeline too much
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            for selector in (
                ("meta", {"property": "og:image"}),
                ("meta", {"name": "twitter:image"}),
                ("meta", {"property": "og:image:secure_url"}),
            ):
                tag = soup.find(selector[0], selector[1])
                if tag:
                    content = tag.get("content")
                    if self._is_http_url(content):
                        return content

        except Exception:
            return None

        return None

    def _is_http_url(self, url: Optional[str]) -> bool:
        return (
            bool(url)
            and isinstance(url, str)
            and url.startswith(("http://", "https://"))
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTENT EXTRACTION
    # ═══════════════════════════════════════════════════════════════════════════

    def _extract_content(self, entry: dict) -> str:
        """
        Extract the best content from a feed entry

        Tries multiple fields in order of preference
        """
        content = ""

        # Try content:encoded first (usually full content)
        if "content" in entry and entry.content:
            content = entry.content[0].get("value", "")

        # Try summary if content is short
        if len(content) < 200:
            summary = entry.get("summary", "")
            if len(summary) > len(content):
                content = summary

        # Try description
        if len(content) < 200:
            desc = entry.get("description", "")
            if len(desc) > len(content):
                content = desc

        # Clean HTML
        content = self._html_to_text(content)

        return content

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to clean text"""
        if not html:
            return ""

        try:
            soup = BeautifulSoup(html, "lxml")

            # Remove scripts and styles
            for tag in soup(["script", "style", "iframe", "nav", "header", "footer"]):
                tag.decompose()

            # Get text
            text = soup.get_text(separator=" ")

            # Clean up whitespace
            text = re.sub(r"\s+", " ", text)
            text = text.strip()

            return text

        except Exception as e:
            logger.debug(f"HTML parsing error: {e}")
            # Fallback: simple tag removal
            return re.sub(r"<[^>]+>", " ", html)

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""

        # Remove HTML entities
        text = BeautifulSoup(text, "lxml").get_text()

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════════════

    def _count_words(self, text: str) -> int:
        """Count words in text (handles Arabic and English)"""
        if not text:
            return 0

        # Split by whitespace and filter empty
        words = [w for w in text.split() if w.strip()]
        return len(words)

    def _detect_language(self, text: str) -> str:
        """
        Simple language detection based on character ranges

        Returns 'ar' for Arabic, 'en' for English
        """
        if not text:
            return "en"

        # Count Arabic characters
        arabic_pattern = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
        arabic_count = len(arabic_pattern.findall(text))

        # Count Latin characters
        latin_pattern = re.compile(r"[a-zA-Z]")
        latin_count = len(latin_pattern.findall(text))

        # Determine language
        if arabic_count > latin_count:
            return "ar"
        return "en"

    def _generate_article_id(self, url: str) -> str:
        """Generate unique article ID from URL"""
        hash_str = hashlib.md5(url.encode()).hexdigest()[:12]
        return f"article_{hash_str}"

    def _weighted_shuffle(self, feeds: List[RSSFeed]) -> List[RSSFeed]:
        """
        Shuffle feeds with priority weighting

        Higher priority feeds have more chance of being selected first
        """
        # Create weighted list
        weighted = []
        for feed in feeds:
            # Add feed multiple times based on priority
            weighted.extend([feed] * feed.priority)

        # Shuffle
        random.shuffle(weighted)

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for feed in weighted:
            if feed.id not in seen:
                seen.add(feed.id)
                result.append(feed)

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # BULK OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def validate_feed(self, url: str) -> Tuple[bool, str]:
        """
        Validate if URL is a valid RSS feed

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()

            parsed = feedparser.parse(response.text)

            if parsed.bozo and not parsed.entries:
                return False, f"Invalid feed format: {parsed.bozo_exception}"

            if not parsed.entries:
                return False, "Feed has no entries"

            feed_title = parsed.feed.get("title", "Unknown")
            entry_count = len(parsed.entries)

            return True, f"Valid feed: '{feed_title}' with {entry_count} entries"

        except httpx.HTTPError as e:
            return False, f"HTTP Error: {e}"
        except Exception as e:
            return False, f"Error: {e}"

    async def fetch_multiple(
        self, count: int = 5, category: Optional[FeedCategory] = None
    ) -> List[FetchedArticle]:
        """
        Fetch multiple articles (for queue pre-filling)

        Args:
            count: Number of articles to fetch
            category: Filter by category

        Returns:
            List of FetchedArticle
        """
        articles = []
        attempts = 0
        max_attempts = count * 3

        while len(articles) < count and attempts < max_attempts:
            attempts += 1
            article = await self.fetch_random_article(category)

            if article and article.original_url not in [
                a.original_url for a in articles
            ]:
                articles.append(article)

        return articles
