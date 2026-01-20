"""
ContentOrbit Enterprise - Blogger Publisher
============================================
Publishes articles to Google Blogger using OAuth2.

Setup Requirements:
1. Create project in Google Cloud Console
2. Enable Blogger API
3. Create OAuth2 credentials
4. Get refresh token using OAuth flow

Usage:
    from core.publisher import BloggerPublisher

    publisher = BloggerPublisher(config)
    url = await publisher.publish(title, content, labels=['tech'])
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class BloggerAuthError(Exception):
    """Non-retriable authentication/config error for Blogger."""


class BloggerPublisher:
    """
    Blogger API Publisher

    Handles OAuth2 authentication and article publishing to Google Blogger.
    """

    BLOGGER_API_URL = "https://www.googleapis.com/blogger/v3"
    TOKEN_URL = "https://oauth2.googleapis.com/token"

    def __init__(self, config: ConfigManager):
        """
        Initialize Blogger Publisher

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self._http_client: Optional[httpx.AsyncClient] = None
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=60.0)
        return self._http_client

    async def close(self):
        """Close HTTP client"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    @property
    def blogger_config(self):
        """Get Blogger configuration"""
        return self.config.app_config.blogger

    def is_configured(self) -> bool:
        """Check if Blogger is properly configured"""
        return self.config.is_configured("blogger")

    # ═══════════════════════════════════════════════════════════════════════════
    # OAUTH2 AUTHENTICATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def _refresh_access_token(self) -> str:
        """
        Refresh OAuth2 access token using refresh token

        Returns:
            New access token
        """
        if not self.is_configured():
            raise ValueError("Blogger API not configured")

        client = await self._get_client()

        payload = {
            "client_id": self.blogger_config.client_id,
            "client_secret": self.blogger_config.client_secret,
            "refresh_token": self.blogger_config.refresh_token,
            "grant_type": "refresh_token",
        }

        try:
            response = await client.post(self.TOKEN_URL, data=payload)
            response.raise_for_status()

            data = response.json()
            self._access_token = data["access_token"]

            # Token typically expires in 3600 seconds
            expires_in = data.get("expires_in", 3600)
            self._token_expires = (
                datetime.utcnow().timestamp() + expires_in - 60
            )  # 1 min buffer

            logger.info("✅ Blogger access token refreshed")
            return self._access_token

        except httpx.HTTPStatusError as e:
            body = e.response.text
            # Common permanent failure: refresh token revoked/expired.
            if e.response.status_code == 400:
                try:
                    data = e.response.json()
                except Exception:
                    data = {}
                if data.get("error") == "invalid_grant":
                    logger.error(
                        "Token refresh failed: invalid_grant (refresh token expired or revoked)."
                    )
                    raise BloggerAuthError("invalid_grant")

            logger.error(f"Token refresh failed: {body}")
            raise

    async def _get_access_token(self) -> str:
        """Get valid access token, refreshing if needed"""
        now = datetime.utcnow().timestamp()

        if self._access_token and self._token_expires and now < self._token_expires:
            return self._access_token

        return await self._refresh_access_token()

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
        labels: Optional[List[str]] = None,
        is_draft: bool = False,
    ) -> Optional[str]:
        """
        Publish article to Blogger

        Args:
            title: Article title
            content: HTML content
            labels: List of labels/tags
            is_draft: If True, save as draft instead of publishing

        Returns:
            Published article URL, or None if failed
        """
        if not self.is_configured():
            logger.error("Blogger not configured")
            return None

        try:
            access_token = await self._get_access_token()
        except BloggerAuthError:
            # Permanent auth issue: don't retry; surface as a clean failure.
            return None
        client = await self._get_client()

        # Build post data
        post_data = {"kind": "blogger#post", "title": title, "content": content}

        if labels:
            post_data["labels"] = labels

        # API endpoint
        blog_id = self.blogger_config.blog_id
        url = f"{self.BLOGGER_API_URL}/blogs/{blog_id}/posts"

        params = {}
        if is_draft:
            params["isDraft"] = "true"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        try:
            response = await client.post(
                url, json=post_data, headers=headers, params=params
            )
            response.raise_for_status()

            data = response.json()
            post_url = data.get("url")
            post_id = data.get("id")

            logger.info(f"✅ Published to Blogger: {post_url}")
            return post_url

        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            logger.error(
                f"Blogger publish failed: {e.response.status_code} - {error_detail}"
            )

            # Handle specific errors
            if e.response.status_code == 401:
                # Token might be invalid, clear it
                self._access_token = None
                raise
            elif e.response.status_code == 403:
                logger.error("Permission denied. Check API access.")

            return None
        except Exception as e:
            logger.error(f"Blogger publish error: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # BLOG INFO
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_blog_info(self) -> Optional[Dict[str, Any]]:
        """
        Get blog information

        Returns:
            Blog info dict or None
        """
        if not self.is_configured():
            return None

        access_token = await self._get_access_token()
        client = await self._get_client()

        blog_id = self.blogger_config.blog_id
        url = f"{self.BLOGGER_API_URL}/blogs/{blog_id}"

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            return {
                "id": data.get("id"),
                "name": data.get("name"),
                "url": data.get("url"),
                "posts_count": data.get("posts", {}).get("totalItems", 0),
                "published": data.get("published"),
            }
        except Exception as e:
            logger.error(f"Failed to get blog info: {e}")
            return None

    async def get_recent_posts(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent posts from blog

        Args:
            max_results: Maximum number of posts to fetch

        Returns:
            List of post info dicts
        """
        if not self.is_configured():
            return []

        access_token = await self._get_access_token()
        client = await self._get_client()

        blog_id = self.blogger_config.blog_id
        url = f"{self.BLOGGER_API_URL}/blogs/{blog_id}/posts"

        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"maxResults": max_results}

        try:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            posts = []

            for item in data.get("items", []):
                posts.append(
                    {
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "published": item.get("published"),
                        "labels": item.get("labels", []),
                    }
                )

            return posts
        except Exception as e:
            logger.error(f"Failed to get posts: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════════════════
    # POST MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def update_post(
        self,
        post_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> bool:
        """
        Update an existing post

        Args:
            post_id: Blogger post ID
            title: New title (optional)
            content: New content (optional)
            labels: New labels (optional)

        Returns:
            True if updated successfully
        """
        if not self.is_configured():
            return False

        access_token = await self._get_access_token()
        client = await self._get_client()

        blog_id = self.blogger_config.blog_id
        url = f"{self.BLOGGER_API_URL}/blogs/{blog_id}/posts/{post_id}"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        post_data = {}
        if title:
            post_data["title"] = title
        if content:
            post_data["content"] = content
        if labels is not None:
            post_data["labels"] = labels

        if not post_data:
            return True  # Nothing to update

        try:
            response = await client.patch(url, json=post_data, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Updated Blogger post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update post: {e}")
            return False

    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a post

        Args:
            post_id: Blogger post ID

        Returns:
            True if deleted successfully
        """
        if not self.is_configured():
            return False

        access_token = await self._get_access_token()
        client = await self._get_client()

        blog_id = self.blogger_config.blog_id
        url = f"{self.BLOGGER_API_URL}/blogs/{blog_id}/posts/{post_id}"

        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()
            logger.info(f"✅ Deleted Blogger post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete post: {e}")
            return False
