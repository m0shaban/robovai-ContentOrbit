"""
ContentOrbit Enterprise - Facebook Publisher
=============================================
Publishes posts to Facebook Pages using Graph API.

Setup Requirements:
1. Create Facebook App at developers.facebook.com
2. Add Pages permissions
3. Get Page Access Token (long-lived)
4. Get Page ID

Usage:
    from core.publisher import FacebookPublisher

    publisher = FacebookPublisher(config)
    post_id = await publisher.publish_post(message, link)
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class FacebookPublisher:
    """
    Facebook Page Publisher

    Publishes posts to Facebook Pages using Graph API.
    Supports text posts, link posts, and photo posts.
    """

    GRAPH_API_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, config: ConfigManager):
        """
        Initialize Facebook Publisher

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self._http_client: Optional[httpx.AsyncClient] = None

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
    def facebook_config(self):
        """Get Facebook configuration"""
        return self.config.app_config.facebook

    @property
    def page_id(self) -> str:
        """Get Page ID"""
        return self.facebook_config.page_id

    @property
    def access_token(self) -> str:
        """Get Page Access Token"""
        return self.facebook_config.page_access_token

    def is_configured(self) -> bool:
        """Check if Facebook is properly configured"""
        return self.config.is_configured("facebook")

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLISHING
    # ═══════════════════════════════════════════════════════════════════════════

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30)
    )
    async def publish_post(
        self,
        message: str,
        link: Optional[str] = None,
        scheduled_time: Optional[datetime] = None,
    ) -> Optional[str]:
        """
        Publish a post to Facebook Page

        Args:
            message: Post message
            link: Optional link to share
            scheduled_time: Schedule post for later (UTC)

        Returns:
            Post ID if successful, None otherwise
        """
        if not self.is_configured():
            logger.error("Facebook not configured")
            return None

        client = await self._get_client()

        url = f"{self.GRAPH_API_URL}/{self.page_id}/feed"

        params = {"access_token": self.access_token, "message": message}

        if link:
            params["link"] = link

        if scheduled_time:
            # Convert to Unix timestamp
            params["published"] = "false"
            params["scheduled_publish_time"] = int(scheduled_time.timestamp())

        try:
            response = await client.post(url, params=params)
            response.raise_for_status()

            data = response.json()
            post_id = data.get("id")

            logger.info(f"✅ Published to Facebook: post_id={post_id}")
            return post_id

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.text else {}
            error_msg = error_data.get("error", {}).get("message", str(e))
            logger.error(f"Facebook publish failed: {error_msg}")

            # Handle specific errors
            error_code = error_data.get("error", {}).get("code")
            if error_code == 190:
                logger.error("Access token expired or invalid")
            elif error_code == 200:
                logger.error("Permission denied. Check Page access.")

            return None
        except Exception as e:
            logger.error(f"Facebook publish error: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30)
    )
    async def publish_photo(self, message: str, photo_url: str) -> Optional[str]:
        """
        Publish a photo post to Facebook Page

        Args:
            message: Post caption
            photo_url: URL of the photo

        Returns:
            Post ID if successful
        """
        if not self.is_configured():
            return None

        client = await self._get_client()

        url = f"{self.GRAPH_API_URL}/{self.page_id}/photos"

        params = {
            "access_token": self.access_token,
            "caption": message,
            "url": photo_url,
        }

        try:
            response = await client.post(url, params=params)
            response.raise_for_status()

            data = response.json()
            post_id = data.get("post_id") or data.get("id")

            logger.info(f"✅ Published photo to Facebook: {post_id}")
            return post_id

        except Exception as e:
            logger.error(f"Facebook photo publish failed: {e}")
            # Fallback to text post with link
            return await self.publish_post(f"{message}\n\n📷 {photo_url}")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=30)
    )
    async def publish_photos(
        self, message: str, photo_urls: List[str]
    ) -> Optional[str]:
        """Publish multiple photos as a single Facebook post (attached media)."""
        if not self.is_configured():
            return None

        urls = [u for u in (photo_urls or []) if (u or "").strip()]
        if not urls:
            return await self.publish_post(message)

        # Keep it reasonable; FB supports more, but this avoids rate/timeout issues.
        urls = urls[:10]

        client = await self._get_client()

        try:
            media_fbids: List[str] = []
            upload_url = f"{self.GRAPH_API_URL}/{self.page_id}/photos"

            # 1) Upload photos as unpublished
            for url in urls:
                params = {
                    "access_token": self.access_token,
                    "url": url,
                    "published": "false",
                }
                r = await client.post(upload_url, params=params)
                r.raise_for_status()
                data = r.json()
                media_id = data.get("id")
                if media_id:
                    media_fbids.append(str(media_id))

            if not media_fbids:
                return await self.publish_photo(message, urls[0])

            # 2) Create feed post with attached_media
            feed_url = f"{self.GRAPH_API_URL}/{self.page_id}/feed"
            params: Dict[str, Any] = {
                "access_token": self.access_token,
                "message": message,
            }
            for i, fbid in enumerate(media_fbids):
                params[f"attached_media[{i}]"] = json.dumps({"media_fbid": fbid})

            r2 = await client.post(feed_url, data=params)
            r2.raise_for_status()
            data2 = r2.json()
            post_id = data2.get("id")

            logger.info(
                f"✅ Published multi-photo to Facebook: post_id={post_id} photos={len(media_fbids)}"
            )
            return post_id

        except Exception as e:
            logger.error(f"Facebook multi-photo publish failed: {e}")
            return await self.publish_photo(message, urls[0])

    # ═══════════════════════════════════════════════════════════════════════════
    # PAGE INFO
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_page_info(self) -> Optional[Dict[str, Any]]:
        """
        Get Facebook Page information

        Returns:
            Page info dict or None
        """
        if not self.is_configured():
            return None

        client = await self._get_client()

        url = f"{self.GRAPH_API_URL}/{self.page_id}"
        params = {
            "access_token": self.access_token,
            "fields": "id,name,about,fan_count,link,picture",
        }

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            return {
                "id": data.get("id"),
                "name": data.get("name"),
                "about": data.get("about"),
                "followers": data.get("fan_count", 0),
                "url": data.get("link"),
                "picture": data.get("picture", {}).get("data", {}).get("url"),
            }
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return None

    async def get_recent_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent posts from the Page

        Args:
            limit: Maximum number of posts

        Returns:
            List of post info dicts
        """
        if not self.is_configured():
            return []

        client = await self._get_client()

        url = f"{self.GRAPH_API_URL}/{self.page_id}/posts"
        params = {
            "access_token": self.access_token,
            "fields": "id,message,created_time,permalink_url,shares,likes.summary(true),comments.summary(true)",
            "limit": limit,
        }

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            posts = []

            for item in data.get("data", []):
                posts.append(
                    {
                        "id": item.get("id"),
                        "message": item.get("message", "")[:100],
                        "created_time": item.get("created_time"),
                        "url": item.get("permalink_url"),
                        "shares": item.get("shares", {}).get("count", 0),
                        "likes": item.get("likes", {})
                        .get("summary", {})
                        .get("total_count", 0),
                        "comments": item.get("comments", {})
                        .get("summary", {})
                        .get("total_count", 0),
                    }
                )

            return posts
        except Exception as e:
            logger.error(f"Failed to get posts: {e}")
            return []

    # ═══════════════════════════════════════════════════════════════════════════
    # POST MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a post

        Args:
            post_id: Facebook post ID

        Returns:
            True if deleted successfully
        """
        if not self.is_configured():
            return False

        client = await self._get_client()

        url = f"{self.GRAPH_API_URL}/{post_id}"
        params = {"access_token": self.access_token}

        try:
            response = await client.delete(url, params=params)
            response.raise_for_status()
            logger.info(f"✅ Deleted Facebook post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete post: {e}")
            return False

    async def update_post(self, post_id: str, message: str) -> bool:
        """
        Update a post's message

        Args:
            post_id: Facebook post ID
            message: New message

        Returns:
            True if updated successfully
        """
        if not self.is_configured():
            return False

        client = await self._get_client()

        url = f"{self.GRAPH_API_URL}/{post_id}"
        params = {"access_token": self.access_token, "message": message}

        try:
            response = await client.post(url, params=params)
            response.raise_for_status()
            logger.info(f"✅ Updated Facebook post: {post_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update post: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # TOKEN MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def verify_token(self) -> bool:
        """
        Verify that the access token is valid

        Returns:
            True if token is valid
        """
        if not self.is_configured():
            return False

        client = await self._get_client()

        url = f"{self.GRAPH_API_URL}/debug_token"
        params = {"input_token": self.access_token, "access_token": self.access_token}

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json().get("data", {})

            if data.get("is_valid"):
                expires_at = data.get("expires_at", 0)
                if expires_at == 0:
                    logger.info("Token is valid (never expires)")
                else:
                    from datetime import datetime

                    expires = datetime.fromtimestamp(expires_at)
                    logger.info(f"Token is valid until {expires}")
                return True
            else:
                logger.error("Token is invalid")
                return False

        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            return False

    async def get_token_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed token information

        Returns:
            Token info dict or None
        """
        if not self.is_configured():
            return None

        client = await self._get_client()

        url = f"{self.GRAPH_API_URL}/debug_token"
        params = {"input_token": self.access_token, "access_token": self.access_token}

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json().get("data", {})

            return {
                "is_valid": data.get("is_valid"),
                "app_id": data.get("app_id"),
                "type": data.get("type"),
                "expires_at": data.get("expires_at"),
                "scopes": data.get("scopes", []),
            }
        except Exception as e:
            logger.error(f"Failed to get token info: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # INSIGHTS (ANALYTICS)
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_page_insights(
        self, metrics: List[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get Page insights/analytics

        Args:
            metrics: List of metrics to fetch (defaults to common metrics)

        Returns:
            Insights dict or None
        """
        if not self.is_configured():
            return None

        if not metrics:
            metrics = [
                "page_impressions",
                "page_engaged_users",
                "page_fans",
                "page_views_total",
            ]

        client = await self._get_client()

        url = f"{self.GRAPH_API_URL}/{self.page_id}/insights"
        params = {
            "access_token": self.access_token,
            "metric": ",".join(metrics),
            "period": "day",
        }

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()

            data = response.json()

            insights = {}
            for item in data.get("data", []):
                name = item.get("name")
                values = item.get("values", [])
                if values:
                    insights[name] = values[-1].get("value", 0)

            return insights
        except Exception as e:
            logger.error(f"Failed to get insights: {e}")
            return None
