"""
ContentOrbit Enterprise - Dev.to Publisher
===========================================
Publishes technical articles to Dev.to using their API.

Setup Requirements:
1. Go to https://dev.to/settings/extensions
2. Generate an API Key
3. Add to config

Usage:
    from core.publisher import DevToPublisher

    publisher = DevToPublisher(config)
    url = await publisher.publish(title, content, tags=['python', 'tutorial'])
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import re

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class DevToPublisher:
    """
    Dev.to API Publisher

    Publishes Markdown articles to Dev.to with proper formatting.
    """

    DEVTO_API_URL = "https://dev.to/api"

    def __init__(self, config: ConfigManager):
        """
        Initialize Dev.to Publisher

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=60.0,
                headers={
                    "api-key": self.config.app_config.devto.api_key,
                    "Content-Type": "application/json",
                },
            )
        return self._http_client

    async def close(self):
        """Close HTTP client"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    @property
    def devto_config(self):
        """Get Dev.to configuration"""
        return self.config.app_config.devto

    def is_configured(self) -> bool:
        """Check if Dev.to is properly configured"""
        return self.config.is_configured("devto")

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLISHING
    # ═══════════════════════════════════════════════════════════════════════════

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30)
    )
    async def publish(
        self,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        series: Optional[str] = None,
        canonical_url: Optional[str] = None,
        cover_image: Optional[str] = None,
        is_published: bool = True,
    ) -> Optional[str]:
        """
        Publish article to Dev.to

        Args:
            title: Article title
            content: Markdown content
            tags: List of tags (max 4)
            series: Series name (optional)
            canonical_url: Original article URL (for SEO)
            is_published: If False, save as draft

        Returns:
            Published article URL, or None if failed
        """
        if not self.is_configured():
            logger.error("Dev.to not configured")
            return None

        client = await self._get_client()

        # Clean and validate tags
        if tags:
            tags = [self._clean_tag(tag) for tag in tags[:4]]

        # Build article data
        article_data = {
            "article": {
                "title": title,
                "body_markdown": content,
                "published": is_published,
                "tags": tags or [],
            }
        }

        if cover_image:
            article_data["article"]["cover_image"] = cover_image

        if series:
            article_data["article"]["series"] = series

        if canonical_url:
            article_data["article"]["canonical_url"] = canonical_url

        if self.devto_config.organization_id:
            article_data["article"]["organization_id"] = int(
                self.devto_config.organization_id
            )

        url = f"{self.DEVTO_API_URL}/articles"

        try:
            response = await client.post(url, json=article_data)
            response.raise_for_status()

            data = response.json()
            article_url = data.get("url")
            article_id = data.get("id")

            logger.info(f"✅ Published to Dev.to: {article_url}")
            return article_url

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(
                f"Dev.to publish failed: {e.response.status_code} - {error_detail}"
            )

            if e.response.status_code == 401:
                logger.error("Invalid API key")
            elif e.response.status_code == 422:
                logger.error(f"Validation error: {error_detail}")

            return None
        except Exception as e:
            logger.error(f"Dev.to publish error: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # USER INFO
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get authenticated user information

        Returns:
            User info dict or None
        """
        if not self.is_configured():
            return None

        client = await self._get_client()
        url = f"{self.DEVTO_API_URL}/users/me"

        try:
            response = await client.get(url)
            response.raise_for_status()

            data = response.json()
            return {
                "id": data.get("id"),
                "username": data.get("username"),
                "name": data.get("name"),
                "profile_image": data.get("profile_image"),
                "twitter_username": data.get("twitter_username"),
                "github_username": data.get("github_username"),
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def get_my_articles(
        self, page: int = 1, per_page: int = 10, state: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Get user's articles

        Args:
            page: Page number
            per_page: Articles per page (max 1000)
            state: Filter by state (all, published, unpublished)

        Returns:
            List of article info dicts
        """
        if not self.is_configured():
            return []

        client = await self._get_client()
        url = f"{self.DEVTO_API_URL}/articles/me"

        params = {"page": page, "per_page": min(per_page, 1000), "state": state}

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()

            articles = []
            for item in response.json():
                articles.append(
                    {
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "published_at": item.get("published_at"),
                        "positive_reactions_count": item.get(
                            "positive_reactions_count"
                        ),
                        "comments_count": item.get("comments_count"),
                        "page_views_count": item.get("page_views_count"),
                        "tags": item.get("tag_list", []),
                    }
                )

            return articles
        except Exception as e:
            logger.error(f"Failed to get articles: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════════════════
    # ARTICLE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def update_article(
        self,
        article_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        is_published: Optional[bool] = None,
    ) -> bool:
        """
        Update an existing article

        Args:
            article_id: Dev.to article ID
            title: New title (optional)
            content: New content (optional)
            tags: New tags (optional)
            is_published: Publish status (optional)

        Returns:
            True if updated successfully
        """
        if not self.is_configured():
            return False

        client = await self._get_client()
        url = f"{self.DEVTO_API_URL}/articles/{article_id}"

        article_data = {"article": {}}

        if title:
            article_data["article"]["title"] = title
        if content:
            article_data["article"]["body_markdown"] = content
        if tags:
            article_data["article"]["tags"] = [self._clean_tag(t) for t in tags[:4]]
        if is_published is not None:
            article_data["article"]["published"] = is_published

        if not article_data["article"]:
            return True  # Nothing to update

        try:
            response = await client.put(url, json=article_data)
            response.raise_for_status()
            logger.info(f"✅ Updated Dev.to article: {article_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update article: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════════════

    def _clean_tag(self, tag: str) -> str:
        """
        Clean tag for Dev.to requirements

        Rules:
        - Lowercase
        - No spaces (use hyphens)
        - Only letters, numbers, hyphens
        - Max 20 characters
        """
        tag = tag.lower().strip()
        tag = re.sub(r"[^a-z0-9\-]", "", tag.replace(" ", "-"))
        tag = re.sub(r"-+", "-", tag)  # Remove multiple hyphens
        return tag[:20]

    def is_tech_topic(self, topic: str) -> bool:
        """
        Check if topic is suitable for Dev.to (tech-related)

        Args:
            topic: Article topic/title

        Returns:
            True if tech-related
        """
        tech_keywords = [
            "programming",
            "code",
            "coding",
            "developer",
            "development",
            "software",
            "api",
            "database",
            "python",
            "javascript",
            "react",
            "node",
            "web",
            "app",
            "mobile",
            "cloud",
            "devops",
            "ai",
            "machine learning",
            "data",
            "algorithm",
            "github",
            "git",
            "docker",
            "kubernetes",
            "linux",
            "برمجة",
            "كود",
            "تطوير",
            "مطور",
            "تقنية",
            "ذكاء اصطناعي",
        ]

        topic_lower = topic.lower()
        return any(keyword in topic_lower for keyword in tech_keywords)

    def format_markdown(self, content: str) -> str:
        """
        Ensure content is properly formatted for Dev.to

        Args:
            content: Raw markdown content

        Returns:
            Cleaned markdown
        """
        # Remove any HTML if present
        content = re.sub(r"<[^>]+>", "", content)

        # Ensure proper code block formatting
        content = re.sub(r"```(\w+)?\n", r"\n```\1\n", content)

        # Add line breaks before headers
        content = re.sub(r"([^\n])(\n#{1,3} )", r"\1\n\2", content)

        return content.strip()
