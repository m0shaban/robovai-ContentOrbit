"""
ContentOrbit Enterprise - Content Orchestrator
===============================================
The Maestro that coordinates the entire content pipeline.
Implements the "Spider Web Strategy" for content distribution.

Pipeline Flow:
1. Fetch random article from RSS
2. Generate Blogger article (Arabic SEO) -> blogger_url
3. Generate Dev.to article (English Tech) -> devto_url (optional)
4. Generate & post to Telegram (with CTAs to articles)
5. Generate & post to Facebook (Storytelling)
6. Log everything to database

Usage:
    from core.content_orchestrator import ContentOrchestrator

    orchestrator = ContentOrchestrator(config, db)
    result = await orchestrator.execute()
"""

import asyncio
import time
import os
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime
from dataclasses import dataclass, field
import logging
import traceback

from core.config_manager import ConfigManager
from core.database_manager import DatabaseManager
from core.models import FetchedArticle, PublishedPost, PostStatus, FeedCategory
from core.fetcher.rss_parser import RSSFetcher
from core.ai_engine.llm_client import LLMClient, GeneratedContent
from core.publisher.blogger_publisher import BloggerPublisher
from core.publisher.devto_publisher import DevToPublisher
from core.publisher.telegram_publisher import TelegramPublisher
from core.publisher.facebook_publisher import FacebookPublisher
from core.cta_strategy import CTAStrategy  # 🎯 CTA Integration
from core.image_generator import ImageGenerator

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a pipeline execution"""

    success: bool = False
    article: Optional[FetchedArticle] = None
    blogger_url: Optional[str] = None
    devto_url: Optional[str] = None
    telegram_message_id: Optional[int] = None
    facebook_post_id: Optional[str] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    steps_completed: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "article_title": self.article.title if self.article else None,
            "blogger_url": self.blogger_url,
            "devto_url": self.devto_url,
            "telegram_message_id": self.telegram_message_id,
            "facebook_post_id": self.facebook_post_id,
            "error": self.error,
            "processing_time": self.processing_time,
            "steps_completed": self.steps_completed,
        }


class ContentOrchestrator:
    """
    Content Orchestrator - The Spider Web Strategy Implementation

    Coordinates all components to execute the content distribution pipeline:
    1. Fetcher -> Get content from RSS
    2. AI Engine -> Generate platform-specific content
    3. Publishers -> Distribute to all platforms
    4. Database -> Track everything
    """

    def __init__(self, config: ConfigManager, db: DatabaseManager):
        """
        Initialize Content Orchestrator

        Args:
            config: ConfigManager instance
            db: DatabaseManager instance
        """
        self.config = config
        self.db = db

        # Initialize components
        self.fetcher = RSSFetcher(config, db)
        self.llm = LLMClient(config)
        self.blogger = BloggerPublisher(config)
        self.devto = DevToPublisher(config)
        self.telegram = TelegramPublisher(config)
        self.facebook = FacebookPublisher(config)
        self.image_generator = ImageGenerator()

        #  Initialize CTA Strategy
        self.cta = CTAStrategy()

        logger.info("🎭 Content Orchestrator initialized")

    async def close(self):
        """Close all component connections"""
        await self.fetcher.close()
        await self.llm.close()
        await self.blogger.close()
        await self.devto.close()
        await self.telegram.close()
        await self.facebook.close()

    # ═══════════════════════════════════════════════════════════════════════════
    # MAIN PIPELINE
    # ═══════════════════════════════════════════════════════════════════════════

    async def execute(self, category: Optional[FeedCategory] = None) -> PipelineResult:
        """
        Execute the complete content pipeline

        This is the main entry point that orchestrates:
        1. Fetch content
        2. Generate articles for asset platforms (Blogger, Dev.to)
        3. Distribute to social platforms (Telegram, Facebook)

        Args:
            category: Optional category filter for RSS feeds

        Returns:
            PipelineResult with all outcomes
        """
        result = PipelineResult()
        start_time = time.time()

        logger.info("=" * 60)
        logger.info("🚀 Starting Content Pipeline Execution")
        logger.info("=" * 60)

        try:
            # ═══════════════════════════════════════════════════════════════
            # STEP 1: FETCH CONTENT
            # ═══════════════════════════════════════════════════════════════
            logger.info("📥 Step 1: Fetching content from RSS...")

            article = await self.fetcher.fetch_random_article(category)

            if not article:
                result.error = "No valid articles found in RSS feeds"
                logger.warning(f"❌ {result.error}")
                self._log_failure("fetch", result.error)
                return result

            result.article = article
            result.steps_completed.append("fetch")

            logger.info(f"✅ Found article: {article.title[:50]}...")
            logger.info(f"   Source: {article.original_url}")
            logger.info(f"   Words: {article.word_count}")

            # Resolve an image early so all platforms can use it.
            image_url = await self._resolve_or_generate_image_url(article)

            social_image_urls: Optional[List[str]] = None
            if (
                self.config.app_config.schedule.telegram_enabled
                and self.telegram.is_configured()
            ) or (
                self.config.app_config.schedule.facebook_enabled
                and self.facebook.is_configured()
            ):
                social_image_urls = await self._resolve_or_generate_social_image_urls(
                    article, image_url
                )

            # ═══════════════════════════════════════════════════════════════
            # STEP 2: GENERATE ASSET CONTENT (The Hubs)
            # Blogger FIRST so Dev.to canonical_url points to robovai.tech
            # ═══════════════════════════════════════════════════════════════

            # 2A: Blogger Article (Arabic)
            blogger_url = None
            if (
                self.config.app_config.schedule.blogger_enabled
                and self.blogger.is_configured()
            ):
                logger.info("📝 Step 2A: Generating Blogger article (Arabic)...")
                blogger_url = await self._publish_to_blogger(
                    article, devto_url=None, image_url=image_url
                )
                if blogger_url:
                    result.blogger_url = blogger_url
                    result.steps_completed.append("blogger")
                    logger.info(f"✅ Blogger published: {blogger_url}")

            # 2B: Dev.to Article (English - Tech only) - canonical points to Blogger
            devto_url = None
            if (
                self.config.app_config.schedule.devto_enabled
                and self.devto.is_configured()
                and self._should_post_to_devto(article)
            ):
                logger.info("📝 Step 2B: Generating Dev.to article (English)...")
                devto_url = await self._publish_to_devto(
                    article, blogger_url=blogger_url, image_url=image_url
                )
                if devto_url:
                    result.devto_url = devto_url
                    result.steps_completed.append("devto")
                    logger.info(f"✅ Dev.to published: {devto_url}")

            # 2C: Update Dev.to with Blogger link (if both published)
            # Note: This would require editing the Dev.to post - future enhancement

            # ═══════════════════════════════════════════════════════════════
            # STEP 3: SOCIAL DISTRIBUTION (The Spokes)
            # 🎯 CTA Strategy: Facebook→Blogger, Telegram→All
            # ═══════════════════════════════════════════════════════════════

            # Use original URL as fallback if Blogger failed
            primary_url = blogger_url or article.original_url

            # 3A: Telegram (HUB - links to ALL platforms)
            if (
                self.config.app_config.schedule.telegram_enabled
                and self.telegram.is_configured()
            ):
                logger.info("📱 Step 3A: Publishing to Telegram (Hub)...")
                message_id = await self._publish_to_telegram(
                    article, blogger_url, devto_url, social_image_urls
                )
                if message_id:
                    result.telegram_message_id = message_id
                    result.steps_completed.append("telegram")
                    logger.info(f"✅ Telegram published: message_id={message_id}")

            # 3B: Facebook (drives traffic to Blogger)
            if (
                self.config.app_config.schedule.facebook_enabled
                and self.facebook.is_configured()
            ):
                logger.info("📘 Step 3B: Publishing to Facebook (→Blogger)...")
                post_id = await self._publish_to_facebook(
                    article, primary_url, social_image_urls
                )
                if post_id:
                    result.facebook_post_id = post_id
                    result.steps_completed.append("facebook")
                    logger.info(f"✅ Facebook published: post_id={post_id}")

            # ═══════════════════════════════════════════════════════════════
            # STEP 4: RECORD SUCCESS
            # ═══════════════════════════════════════════════════════════════

            result.success = (
                len(result.steps_completed) > 1
            )  # At least fetch + one publish
            result.processing_time = time.time() - start_time

            # Save to database
            self._save_published_post(result)

            logger.info("=" * 60)
            logger.info(f"✅ Pipeline completed in {result.processing_time:.2f}s")
            logger.info(f"   Steps: {' -> '.join(result.steps_completed)}")
            logger.info("=" * 60)

            return result

        except Exception as e:
            result.error = str(e)
            result.processing_time = time.time() - start_time

            logger.error(f"❌ Pipeline failed: {e}")
            logger.error(traceback.format_exc())

            self._log_failure("pipeline", str(e), traceback.format_exc())

            # Try to notify admins
            try:
                await self.telegram.send_error_alert(str(e), "pipeline")
            except:
                pass

            return result

    # ═══════════════════════════════════════════════════════════════════════════
    # PLATFORM-SPECIFIC PUBLISHERS
    # ═══════════════════════════════════════════════════════════════════════════

    async def _publish_to_blogger(
        self,
        article: FetchedArticle,
        devto_url: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Optional[str]:
        """Generate and publish to Blogger with smart CTA"""
        try:
            # Generate content
            content = await self.llm.generate_blogger_article(article)

            hero_img = ""
            if image_url:
                hero_img = (
                    f'<p style="text-align:center; margin: 0 0 16px 0;">'
                    f'<img src="{image_url}" alt="{article.title}" style="max-width:100%; border-radius: 14px;" />'
                    f"</p>"
                )

            # 🎯 Add CTA section at the end of the article
            cta_html = self.cta.get_blogger_cta(devto_url=devto_url)
            final_content = hero_img + "\n\n" + content.content + "\n\n" + cta_html

            # Publish
            url = await self.blogger.publish(
                title=content.title, content=final_content, labels=content.tags
            )

            if url:
                self.db.log_info(
                    component="orchestrator",
                    action="blogger_published",
                    message=f"Published to Blogger: {content.title[:50]}",
                    url=url,
                )

            return url

        except Exception as e:
            logger.error(f"Blogger publish failed: {e}")
            self.db.log_error(
                component="orchestrator",
                action="blogger_failed",
                message=str(e),
                error=e,
            )

            if not self.config.app_config.fallback_on_blogger_fail:
                raise

            return None

    async def _publish_to_devto(
        self,
        article: FetchedArticle,
        blogger_url: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Optional[str]:
        """Generate and publish to Dev.to with smart CTA"""
        try:
            # Generate content
            content = await self.llm.generate_devto_article(article)

            # 🎯 Add CTA section at the end of the article
            cta_md = self.cta.get_devto_cta(blogger_url=blogger_url)
            final_content = content.content + "\n\n" + cta_md

            # Publish
            url = await self.devto.publish(
                title=content.title,
                content=final_content,
                tags=content.tags,
                canonical_url=blogger_url or self.cta.links.blogger_home,
                cover_image=image_url,
            )

            if url:
                self.db.log_info(
                    component="orchestrator",
                    action="devto_published",
                    message=f"Published to Dev.to: {content.title[:50]}",
                    url=url,
                )

            return url

        except Exception as e:
            logger.error(f"Dev.to publish failed: {e}")
            self.db.log_error(
                component="orchestrator", action="devto_failed", message=str(e), error=e
            )
            return None

    async def _publish_to_telegram(
        self,
        article: FetchedArticle,
        blogger_url: Optional[str],
        devto_url: Optional[str],
        image_urls: Optional[List[str]],
    ) -> Optional[int]:
        """Generate and publish to Telegram with smart CTA"""
        try:
            # 🎯 Telegram must be Arabic (Egyptian). Allow English technical terms.
            try:
                title = await self.llm.generate_egyptian_arabic_title(article)
            except Exception:
                title = ""

            # Generate an Egyptian Arabic summary (source might be English)
            try:
                summary = await self.llm.generate_egyptian_arabic_summary(article)
            except Exception:
                summary = ""

            # Never post raw source-language content.
            if not title or not summary:
                logger.warning(
                    "Skipping Telegram post: failed to generate Arabic title/summary."
                )
                return None

            # Use CTA strategy for structured message
            post_text = self.cta.get_telegram_message(
                title=title,
                summary=summary,
                blogger_url=blogger_url,
                devto_url=devto_url,
                key_points=None,  # Can be extracted from article later
            )

            # Publish (with image if available)
            message_id = await self.telegram.publish_post(
                text=post_text,
                image_urls=image_urls,
                image_url=(image_urls[0] if image_urls else None),
            )

            if message_id:
                self.db.log_info(
                    component="orchestrator",
                    action="telegram_published",
                    message=f"Published to Telegram with CTA",
                    message_id=message_id,
                )

            return message_id

        except Exception as e:
            logger.error(f"Telegram publish failed: {e}")
            self.db.log_error(
                component="orchestrator",
                action="telegram_failed",
                message=str(e),
                error=e,
            )
            return None

    async def _publish_to_facebook(
        self, article: FetchedArticle, article_url: str, image_urls: Optional[List[str]]
    ) -> Optional[str]:
        """Generate and publish to Facebook with smart CTA"""
        try:
            # 🎯 Use CTA Strategy for Facebook (drives to Blogger)
            try:
                title = await self.llm.generate_egyptian_arabic_title(article)
            except Exception:
                title = ""

            try:
                hook = await self.llm.generate_egyptian_arabic_summary(
                    article, max_words=55
                )
            except Exception:
                hook = ""

            if not title or not hook:
                logger.warning(
                    "Skipping Facebook post: failed to generate Arabic title/hook."
                )
                return None

            post_text = self.cta.get_facebook_post(
                title=title,
                hook=(hook or "") + "...",
                blogger_url=article_url,
                emoji="🔥",
            )

            # Publish
            if image_urls:
                photo_urls = [u for u in image_urls if (u or "").strip()]
            else:
                photo_urls = []

            if len(photo_urls) >= 2:
                post_id = await self.facebook.publish_photos(
                    message=f"{post_text}\n\n{article_url}",
                    photo_urls=photo_urls,
                )
            elif len(photo_urls) == 1:
                post_id = await self.facebook.publish_photo(
                    message=f"{post_text}\n\n{article_url}", photo_url=photo_urls[0]
                )
            else:
                post_id = await self.facebook.publish_post(
                    message=post_text, link=article_url
                )

            if post_id:
                self.db.log_info(
                    component="orchestrator",
                    action="facebook_published",
                    message=f"Published to Facebook with CTA",
                    post_id=post_id,
                )

            return post_id

        except Exception as e:
            logger.error(f"Facebook publish failed: {e}")
            self.db.log_error(
                component="orchestrator",
                action="facebook_failed",
                message=str(e),
                error=e,
            )
            return None

    async def _resolve_or_generate_image_url(
        self, article: FetchedArticle
    ) -> Optional[str]:
        """Use RSS/og:image if available; otherwise generate a branded OG image and upload it."""
        existing = getattr(article, "image_url", None)
        if existing:
            # Prefer stable/public hosts for cover images.
            stable_hosts = ("i.ibb.co", "ibb.co", "robovai.tech", "www.robovai.tech")
            try:
                host = existing.split("/", 3)[2].lower()
            except Exception:
                host = ""
            if host and any(h == host or host.endswith("." + h) for h in stable_hosts):
                return existing

            # Validate external images; if inaccessible, fallback to generated.
            try:
                async with httpx.AsyncClient(
                    timeout=10.0, follow_redirects=True
                ) as client:
                    r = await client.head(
                        existing, headers={"User-Agent": "Mozilla/5.0"}
                    )
                    if (
                        r.status_code < 400
                        and "image" in (r.headers.get("content-type") or "").lower()
                    ):
                        return existing
            except Exception:
                pass

        try:
            hook = (article.summary or "").strip()[:110] or None
            url = await asyncio.to_thread(
                self.image_generator.generate_and_upload,
                article.title,
                hook,
                None,
            )
            if url:
                try:
                    article.image_url = url
                except Exception:
                    pass
                self.db.log_info(
                    component="orchestrator",
                    action="image_generated",
                    message="Generated fallback image",
                    url=url,
                )
            return url
        except Exception as e:
            logger.warning(f"Image generation failed: {e}")
            return None

    async def _resolve_or_generate_social_image_urls(
        self, article: FetchedArticle, base_image_url: Optional[str]
    ) -> List[str]:
        """Return a list of image URLs for social posts (Telegram/Facebook)."""
        smart_enabled = (
            os.getenv("SOCIAL_IMAGE_SMART", "1") or "1"
        ).strip().lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

        # Back-compat: SOCIAL_IMAGE_VARIANTS behaves like a max cap.
        # Default is 1 to avoid unnecessary multi-image sets.
        raw_max = (os.getenv("SOCIAL_IMAGE_VARIANTS", "1") or "1").strip()
        try:
            max_variants = int(raw_max)
        except Exception:
            max_variants = 1
        max_variants = max(1, min(max_variants, 5))

        if smart_enabled:
            desired = self._decide_social_image_variant_count(article, base_image_url)
            desired = min(desired, max_variants)
        else:
            desired = max_variants

        urls: List[str] = []
        if base_image_url:
            urls.append(base_image_url)

        if len(urls) < desired:
            hook = (article.summary or "").strip()[:110] or None
            try:
                extra = await asyncio.to_thread(
                    self.image_generator.generate_variants_and_upload,
                    article.title,
                    hook,
                    desired - len(urls),
                    None,
                )
            except Exception as e:
                logger.warning(f"Social image variants generation failed: {e}")
                extra = []
            urls.extend(extra)

        # De-dup while preserving order
        seen = set()
        out: List[str] = []
        for u in urls:
            if not u:
                continue
            if u in seen:
                continue
            seen.add(u)
            out.append(u)

        return out[:desired]

    def _decide_social_image_variant_count(
        self, article: FetchedArticle, base_image_url: Optional[str]
    ) -> int:
        """Heuristic: choose 1 image for simple posts, 2-4 for list/guide/long topics."""
        title = (article.title or "").strip()
        summary = (article.summary or "").strip()

        title_len = len(title)
        summary_len = len(summary)

        # If we already have an external image (RSS/og:image), default to 1 unless
        # the post is clearly a list/guide that benefits from a carousel.
        has_existing = bool(base_image_url)

        text = f"{title} {summary}".lower()
        # Keywords that usually imply a multi-slide carousel / breakdown.
        carousel_keys = [
            # Arabic
            "خطوة",
            "خطوات",
            "دليل",
            "شرح",
            "ملخص",
            "مقارنة",
            "أفضل",
            "افضل",
            "قائمة",
            "نصائح",
            "أخطاء",
            "اخطاء",
            "مميزات",
            "عيوب",
            "أسئلة",
            "اسئلة",
            "كيف",
            "لماذا",
            # English
            "how to",
            "guide",
            "step",
            "steps",
            "tips",
            "mistakes",
            "comparison",
            "vs",
            "top ",
            "best ",
            "checklist",
        ]

        has_numbered_list = any(ch.isdigit() for ch in title) and (
            "top" in text or "أفضل" in text or "افضل" in text
        )
        wants_carousel = has_numbered_list or any(k in text for k in carousel_keys)

        # Very short topics rarely need more than one.
        if title_len <= 55 and summary_len <= 140 and not wants_carousel:
            return 1

        # Medium complexity: 2 images (headline + variant style)
        if (title_len <= 85 and summary_len <= 240) and not wants_carousel:
            return 2 if not has_existing else 1

        # List/guide/long topic: 3 images
        if wants_carousel and (title_len > 55 or summary_len > 140):
            return 3

        # Very long/complex: 4 images
        if title_len > 95 or summary_len > 320:
            return 4

        return 2

    # ═══════════════════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def _should_post_to_devto(self, article: FetchedArticle) -> bool:
        """
        Check if article should be posted to Dev.to

        Only tech-related content goes to Dev.to
        """
        if not self.config.app_config.enable_devto_for_tech_only:
            return True

        return self.devto.is_tech_topic(article.title + " " + (article.summary or ""))

    def _save_published_post(self, result: PipelineResult) -> None:
        """Save pipeline result to database"""
        if not result.article:
            return

        post = PublishedPost(
            source_article_id=result.article.id,
            original_url=result.article.original_url,
            title_ar=result.article.title,
            blogger_url=result.blogger_url,
            devto_url=result.devto_url,
            telegram_message_id=result.telegram_message_id,
            facebook_post_id=result.facebook_post_id,
            status=PostStatus.PUBLISHED if result.success else PostStatus.FAILED,
            error_message=result.error,
            published_at=datetime.utcnow() if result.success else None,
            processing_time_seconds=result.processing_time,
        )

        self.db.create_post(post)

    def _log_failure(
        self, step: str, error: str, traceback_str: Optional[str] = None
    ) -> None:
        """Log pipeline failure"""
        self.db.log_error(
            component="orchestrator",
            action=f"pipeline_{step}_failed",
            message=error,
            error_traceback=traceback_str,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # MANUAL OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def execute_single_platform(
        self, platform: str, article: FetchedArticle
    ) -> Tuple[bool, Optional[str]]:
        """
        Execute pipeline for a single platform only

        Useful for retrying failed platforms

        Args:
            platform: Platform name (blogger, devto, telegram, facebook)
            article: Article to publish

        Returns:
            Tuple of (success, result_url_or_id)
        """
        try:
            if platform == "blogger":
                url = await self._publish_to_blogger(article)
                return (url is not None, url)

            elif platform == "devto":
                url = await self._publish_to_devto(article)
                return (url is not None, url)

            elif platform == "telegram":
                image_url = await self._resolve_or_generate_image_url(article)
                image_urls = await self._resolve_or_generate_social_image_urls(
                    article, image_url
                )
                msg_id = await self._publish_to_telegram(
                    article, None, None, image_urls
                )
                return (msg_id is not None, str(msg_id) if msg_id else None)

            elif platform == "facebook":
                image_url = await self._resolve_or_generate_image_url(article)
                image_urls = await self._resolve_or_generate_social_image_urls(
                    article, image_url
                )
                post_id = await self._publish_to_facebook(
                    article, article.original_url, image_urls
                )
                return (post_id is not None, post_id)

            else:
                return (False, f"Unknown platform: {platform}")

        except Exception as e:
            return (False, str(e))

    async def test_all_connections(self) -> Dict[str, bool]:
        """
        Test all platform connections

        Returns:
            Dict of {platform: is_working}
        """
        results = {}

        # Test Groq/LLM
        try:
            test = await self.llm._generate("Say 'OK'", max_tokens=10)
            results["groq"] = "ok" in test.lower()
        except:
            results["groq"] = False

        # Test Blogger
        try:
            info = await self.blogger.get_blog_info()
            results["blogger"] = info is not None
        except:
            results["blogger"] = False

        # Test Dev.to
        try:
            info = await self.devto.get_user_info()
            results["devto"] = info is not None
        except:
            results["devto"] = False

        # Test Telegram
        try:
            info = await self.telegram.get_channel_info()
            results["telegram"] = info is not None
        except:
            results["telegram"] = False

        # Test Facebook
        try:
            info = await self.facebook.get_page_info()
            results["facebook"] = info is not None
        except:
            results["facebook"] = False

        return results
