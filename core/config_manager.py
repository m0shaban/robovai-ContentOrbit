"""
ContentOrbit Enterprise - Configuration Manager
================================================
Handles loading, saving, and validating system configuration.
Config-Driven Architecture: Change settings, not code.

Usage:
    from core.config_manager import ConfigManager

    config = ConfigManager()
    config.load()

    # Access settings
    telegram_token = config.app_config.telegram.bot_token

    # Update settings
    config.update_telegram_config(bot_token="new_token", channel_id="@channel")
    config.save()
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from copy import deepcopy

from .models import (
    AppConfig,
    TelegramConfig,
    BloggerConfig,
    DevToConfig,
    FacebookConfig,
    GroqConfig,
    SystemPrompts,
    ScheduleConfig,
    RSSFeed,
    FeedCategory,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Configuration Manager - The Brain of Config-Driven Architecture

    Responsibilities:
    - Load/Save configuration from JSON file
    - Validate all settings using Pydantic
    - Provide easy access to all config sections
    - Support hot-reloading for dashboard updates
    """

    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "data" / "config.json"
    DEFAULT_CONFIG_EXAMPLE_PATH = (
        Path(__file__).parent.parent / "data" / "config.example.json"
    )
    DEFAULT_FEEDS_PATH = Path(__file__).parent.parent / "data" / "feeds.json"

    def __init__(
        self, config_path: Optional[Path] = None, feeds_path: Optional[Path] = None
    ):
        """
        Initialize ConfigManager

        Args:
            config_path: Path to config.json (uses default if None)
            feeds_path: Path to feeds.json (uses default if None)
        """
        self.config_path = (
            Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        )
        self.feeds_path = Path(feeds_path) if feeds_path else self.DEFAULT_FEEDS_PATH

        # Ensure data directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize with defaults
        self.app_config: AppConfig = AppConfig()
        self.feeds: List[RSSFeed] = []

        # Track if loaded
        self._is_loaded = False
        self._last_loaded: Optional[datetime] = None

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE LOAD/SAVE OPERATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def load(self, create_if_missing: bool = True) -> bool:
        """
        Load configuration from JSON files

        Args:
            create_if_missing: Create default config if file doesn't exist

        Returns:
            True if loaded successfully
        """
        try:
            # Load main config
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                self.app_config = AppConfig(**config_data)
                logger.info(f"✅ Loaded config from {self.config_path}")
            elif create_if_missing:
                if self.DEFAULT_CONFIG_EXAMPLE_PATH.exists():
                    logger.info(
                        f"📝 Config file not found, bootstrapping from {self.DEFAULT_CONFIG_EXAMPLE_PATH}..."
                    )
                    with open(
                        self.DEFAULT_CONFIG_EXAMPLE_PATH, "r", encoding="utf-8"
                    ) as f:
                        example_data = json.load(f)
                    self.app_config = AppConfig(**example_data)
                    self.save()
                else:
                    logger.info("📝 Config file not found, creating default...")
                    self.app_config = AppConfig()
                    self.save()

            # Load RSS feeds
            if self.feeds_path.exists():
                with open(self.feeds_path, "r", encoding="utf-8") as f:
                    feeds_data = json.load(f)
                self.feeds = [RSSFeed(**feed) for feed in feeds_data]
                logger.info(f"✅ Loaded {len(self.feeds)} RSS feeds")
            elif create_if_missing:
                logger.info("📝 Feeds file not found, creating with defaults...")
                self.feeds = self._get_default_feeds()
                self._save_feeds()

            # ──────────────────────────────────────────────────────────────
            # Environment Overrides (for local .env / Render deployment)
            # Fill ONLY missing values (never overwrite non-empty config.json)
            # ──────────────────────────────────────────────────────────────

            self._load_dotenv_if_present()
            self._hydrate_from_environment()

            self._is_loaded = True
            self._last_loaded = datetime.utcnow()
            return True

        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in config file: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return False

    def _hydrate_from_environment(self) -> None:
        """Fill missing config fields from environment variables."""
        changed = False

        def env(*keys: str) -> Optional[str]:
            for k in keys:
                v = os.getenv(k)
                if v is not None and str(v).strip() != "":
                    return str(v).strip()
            return None

        # Dashboard
        dashboard_password = env("DASHBOARD_PASSWORD")
        if (
            dashboard_password
            and not (getattr(self.app_config, "dashboard_password", "") or "").strip()
        ):
            self.app_config.dashboard_password = dashboard_password
            changed = True

        # Telegram
        tg_token = env("TELEGRAM_TOKEN", "TELEGRAM_BOT_TOKEN")
        tg_channel = env("CHANNEL_ID", "TELEGRAM_CHANNEL_ID")
        admin_id_raw = env("ADMIN_USER_ID")

        if (tg_token or tg_channel) and self.app_config.telegram is None:
            self.app_config.telegram = TelegramConfig(
                bot_token=tg_token or "",
                channel_id=tg_channel or "",
                admin_user_ids=[],
            )
            changed = True

        if self.app_config.telegram is not None:
            if tg_token and not (self.app_config.telegram.bot_token or "").strip():
                self.app_config.telegram.bot_token = tg_token
                changed = True
            if tg_channel and not (self.app_config.telegram.channel_id or "").strip():
                self.app_config.telegram.channel_id = tg_channel
                changed = True

            if admin_id_raw:
                try:
                    admin_id = int(admin_id_raw)
                    if admin_id not in self.app_config.telegram.admin_user_ids:
                        self.app_config.telegram.admin_user_ids.append(admin_id)
                        changed = True
                except Exception:
                    pass

        # Groq
        groq_key = env("GROQ_API_KEY")
        if groq_key and self.app_config.groq is None:
            self.app_config.groq = GroqConfig(api_key=groq_key)
            changed = True
        elif (
            groq_key
            and self.app_config.groq is not None
            and not (self.app_config.groq.api_key or "").strip()
        ):
            self.app_config.groq.api_key = groq_key
            changed = True

        # Dev.to
        devto_key = env("DEVTO_API_KEY")
        if devto_key and self.app_config.devto is None:
            self.app_config.devto = DevToConfig(api_key=devto_key)
            changed = True
        elif (
            devto_key
            and self.app_config.devto is not None
            and not (self.app_config.devto.api_key or "").strip()
        ):
            self.app_config.devto.api_key = devto_key
            changed = True

        # Blogger
        blog_id = env("BLOGGER_BLOG_ID")
        client_id = env("BLOGGER_CLIENT_ID")
        client_secret = env("BLOGGER_CLIENT_SECRET")
        refresh_token = env("BLOGGER_REFRESH_TOKEN")
        if (
            blog_id or client_id or client_secret or refresh_token
        ) and self.app_config.blogger is None:
            self.app_config.blogger = BloggerConfig(
                blog_id=blog_id or "",
                client_id=client_id or "",
                client_secret=client_secret or "",
                refresh_token=refresh_token or "",
            )
            changed = True
        if self.app_config.blogger is not None:
            if blog_id and not (self.app_config.blogger.blog_id or "").strip():
                self.app_config.blogger.blog_id = blog_id
                changed = True
            if client_id and not (self.app_config.blogger.client_id or "").strip():
                self.app_config.blogger.client_id = client_id
                changed = True
            if (
                client_secret
                and not (self.app_config.blogger.client_secret or "").strip()
            ):
                self.app_config.blogger.client_secret = client_secret
                changed = True
            if (
                refresh_token
                and not (self.app_config.blogger.refresh_token or "").strip()
            ):
                self.app_config.blogger.refresh_token = refresh_token
                changed = True

        # Facebook
        page_id = env("FACEBOOK_PAGE_ID")
        page_token = env("FACEBOOK_PAGE_ACCESS_TOKEN", "FACEBOOK_PAGE_TOKEN")
        if (page_id or page_token) and self.app_config.facebook is None:
            self.app_config.facebook = FacebookConfig(
                page_id=page_id or "",
                page_access_token=page_token or "",
            )
            changed = True
        if self.app_config.facebook is not None:
            if page_id and not (self.app_config.facebook.page_id or "").strip():
                self.app_config.facebook.page_id = page_id
                changed = True
            if (
                page_token
                and not (self.app_config.facebook.page_access_token or "").strip()
            ):
                self.app_config.facebook.page_access_token = page_token
                changed = True

        # Persist if anything was hydrated (best-effort)
        if changed:
            try:
                self.save()
            except Exception:
                pass

    def _load_dotenv_if_present(self) -> None:
        """Best-effort load of a local .env file (does not override real env vars)."""
        try:
            from dotenv import load_dotenv  # type: ignore
        except Exception:
            return

        # repo root is parent of /core
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            try:
                load_dotenv(dotenv_path=env_path, override=False)
            except Exception:
                pass

    def save(self) -> bool:
        """
        Save current configuration to JSON file

        Returns:
            True if saved successfully
        """
        try:
            # Update timestamp
            self.app_config.updated_at = datetime.utcnow()

            # Save main config
            config_dict = self.app_config.model_dump(mode="json")
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"✅ Saved config to {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving config: {e}")
            return False

    def _save_feeds(self) -> bool:
        """Save RSS feeds to JSON file"""
        try:
            feeds_data = [feed.model_dump(mode="json") for feed in self.feeds]
            with open(self.feeds_path, "w", encoding="utf-8") as f:
                json.dump(feeds_data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"✅ Saved {len(self.feeds)} feeds to {self.feeds_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving feeds: {e}")
            return False

    def reload(self) -> bool:
        """Hot-reload configuration from disk"""
        logger.info("🔄 Reloading configuration...")
        return self.load(create_if_missing=False)

    # ═══════════════════════════════════════════════════════════════════════════
    # API CONFIGURATION UPDATES
    # ═══════════════════════════════════════════════════════════════════════════

    def update_telegram_config(
        self,
        bot_token: Optional[str] = None,
        channel_id: Optional[str] = None,
        admin_user_ids: Optional[List[int]] = None,
    ) -> bool:
        """Update Telegram configuration"""
        try:
            if self.app_config.telegram is None:
                self.app_config.telegram = TelegramConfig(
                    bot_token=bot_token or "", channel_id=channel_id or ""
                )
            else:
                if bot_token:
                    self.app_config.telegram.bot_token = bot_token
                if channel_id:
                    self.app_config.telegram.channel_id = channel_id
                if admin_user_ids is not None:
                    self.app_config.telegram.admin_user_ids = admin_user_ids
            return self.save()
        except Exception as e:
            logger.error(f"Error updating Telegram config: {e}")
            return False

    def update_blogger_config(
        self,
        blog_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        refresh_token: Optional[str] = None,
    ) -> bool:
        """Update Blogger configuration"""
        try:
            if self.app_config.blogger is None:
                self.app_config.blogger = BloggerConfig(
                    blog_id=blog_id or "",
                    client_id=client_id or "",
                    client_secret=client_secret or "",
                    refresh_token=refresh_token or "",
                )
            else:
                if blog_id:
                    self.app_config.blogger.blog_id = blog_id
                if client_id:
                    self.app_config.blogger.client_id = client_id
                if client_secret:
                    self.app_config.blogger.client_secret = client_secret
                if refresh_token:
                    self.app_config.blogger.refresh_token = refresh_token
            return self.save()
        except Exception as e:
            logger.error(f"Error updating Blogger config: {e}")
            return False

    def update_devto_config(
        self, api_key: Optional[str] = None, organization_id: Optional[str] = None
    ) -> bool:
        """Update Dev.to configuration"""
        try:
            if self.app_config.devto is None:
                self.app_config.devto = DevToConfig(api_key=api_key or "")
            else:
                if api_key:
                    self.app_config.devto.api_key = api_key
                if organization_id is not None:
                    self.app_config.devto.organization_id = organization_id
            return self.save()
        except Exception as e:
            logger.error(f"Error updating Dev.to config: {e}")
            return False

    def update_facebook_config(
        self, page_id: Optional[str] = None, page_access_token: Optional[str] = None
    ) -> bool:
        """Update Facebook configuration"""
        try:
            if self.app_config.facebook is None:
                self.app_config.facebook = FacebookConfig(
                    page_id=page_id or "", page_access_token=page_access_token or ""
                )
            else:
                if page_id:
                    self.app_config.facebook.page_id = page_id
                if page_access_token:
                    self.app_config.facebook.page_access_token = page_access_token
            return self.save()
        except Exception as e:
            logger.error(f"Error updating Facebook config: {e}")
            return False

    def update_groq_config(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> bool:
        """Update Groq LLM configuration"""
        try:
            if self.app_config.groq is None:
                self.app_config.groq = GroqConfig(api_key=api_key or "")
            else:
                if api_key:
                    self.app_config.groq.api_key = api_key
                if model:
                    self.app_config.groq.model = model
                if temperature is not None:
                    self.app_config.groq.temperature = temperature
                if max_tokens is not None:
                    self.app_config.groq.max_tokens = max_tokens
            return self.save()
        except Exception as e:
            logger.error(f"Error updating Groq config: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # SYSTEM PROMPTS UPDATES
    # ═══════════════════════════════════════════════════════════════════════════

    def update_prompts(
        self,
        brand_name: Optional[str] = None,
        brand_voice: Optional[str] = None,
        blogger_prompt: Optional[str] = None,
        telegram_prompt: Optional[str] = None,
        facebook_prompt: Optional[str] = None,
        devto_prompt: Optional[str] = None,
    ) -> bool:
        """Update system prompts"""
        try:
            if brand_name:
                self.app_config.prompts.brand_name = brand_name
            if brand_voice:
                self.app_config.prompts.brand_voice = brand_voice
            if blogger_prompt:
                self.app_config.prompts.blogger_article_prompt = blogger_prompt
            if telegram_prompt:
                self.app_config.prompts.telegram_post_prompt = telegram_prompt
            if facebook_prompt:
                self.app_config.prompts.facebook_post_prompt = facebook_prompt
            if devto_prompt:
                self.app_config.prompts.devto_article_prompt = devto_prompt
            return self.save()
        except Exception as e:
            logger.error(f"Error updating prompts: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # SCHEDULE UPDATES
    # ═══════════════════════════════════════════════════════════════════════════

    def update_schedule(
        self,
        interval_minutes: Optional[int] = None,
        active_start: Optional[int] = None,
        active_end: Optional[int] = None,
        max_posts_per_day: Optional[int] = None,
        blogger_enabled: Optional[bool] = None,
        devto_enabled: Optional[bool] = None,
        telegram_enabled: Optional[bool] = None,
        facebook_enabled: Optional[bool] = None,
    ) -> bool:
        """Update scheduling configuration"""
        try:
            if interval_minutes is not None:
                self.app_config.schedule.posting_interval_minutes = interval_minutes
            if active_start is not None:
                self.app_config.schedule.active_hours_start = active_start
            if active_end is not None:
                self.app_config.schedule.active_hours_end = active_end
            if max_posts_per_day is not None:
                self.app_config.schedule.max_posts_per_day = max_posts_per_day
            if blogger_enabled is not None:
                self.app_config.schedule.blogger_enabled = blogger_enabled
            if devto_enabled is not None:
                self.app_config.schedule.devto_enabled = devto_enabled
            if telegram_enabled is not None:
                self.app_config.schedule.telegram_enabled = telegram_enabled
            if facebook_enabled is not None:
                self.app_config.schedule.facebook_enabled = facebook_enabled
            return self.save()
        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # RSS FEEDS MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def add_feed(
        self,
        name: str,
        url: str,
        category: FeedCategory = FeedCategory.OTHER,
        language: str = "ar",
        priority: int = 5,
    ) -> Optional[RSSFeed]:
        """Add a new RSS feed"""
        try:
            # Check for duplicate URL
            if any(feed.url == url for feed in self.feeds):
                logger.warning(f"Feed with URL {url} already exists")
                return None

            # Generate ID
            feed_id = f"feed_{len(self.feeds) + 1}_{int(datetime.utcnow().timestamp())}"

            feed = RSSFeed(
                id=feed_id,
                name=name,
                url=url,
                category=category,
                language=language,
                priority=priority,
            )

            self.feeds.append(feed)
            self._save_feeds()
            logger.info(f"✅ Added feed: {name}")
            return feed

        except Exception as e:
            logger.error(f"Error adding feed: {e}")
            return None

    def remove_feed(self, feed_id: str) -> bool:
        """Remove an RSS feed by ID"""
        try:
            original_count = len(self.feeds)
            self.feeds = [f for f in self.feeds if f.id != feed_id]

            if len(self.feeds) < original_count:
                self._save_feeds()
                logger.info(f"✅ Removed feed: {feed_id}")
                return True
            else:
                logger.warning(f"Feed not found: {feed_id}")
                return False
        except Exception as e:
            logger.error(f"Error removing feed: {e}")
            return False

    def update_feed(self, feed_id: str, **kwargs) -> bool:
        """Update an existing RSS feed"""
        try:
            for feed in self.feeds:
                if feed.id == feed_id:
                    for key, value in kwargs.items():
                        if hasattr(feed, key) and value is not None:
                            setattr(feed, key, value)
                    self._save_feeds()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error updating feed: {e}")
            return False

    def get_active_feeds(
        self, category: Optional[FeedCategory] = None
    ) -> List[RSSFeed]:
        """Get active RSS feeds, optionally filtered by category"""
        active = [f for f in self.feeds if f.is_active]
        if category:
            active = [f for f in active if f.category == category]
        return sorted(active, key=lambda x: x.priority, reverse=True)

    def toggle_feed(self, feed_id: str) -> bool:
        """Toggle feed active status"""
        for feed in self.feeds:
            if feed.id == feed_id:
                feed.is_active = not feed.is_active
                self._save_feeds()
                return True
        return False

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def is_configured(self, platform: str) -> bool:
        """Check if a platform is properly configured"""
        if platform == "telegram":
            return (
                self.app_config.telegram is not None
                and bool(self.app_config.telegram.bot_token)
                and bool(self.app_config.telegram.channel_id)
            )
        elif platform == "blogger":
            return (
                self.app_config.blogger is not None
                and bool(self.app_config.blogger.blog_id)
                and bool(self.app_config.blogger.refresh_token)
            )
        elif platform == "devto":
            return self.app_config.devto is not None and bool(
                self.app_config.devto.api_key
            )
        elif platform == "facebook":
            return (
                self.app_config.facebook is not None
                and bool(self.app_config.facebook.page_id)
                and bool(self.app_config.facebook.page_access_token)
            )
        elif platform == "groq":
            return self.app_config.groq is not None and bool(
                self.app_config.groq.api_key
            )
        return False

    def get_config_status(self) -> Dict[str, bool]:
        """Get configuration status for all platforms"""
        return {
            "telegram": self.is_configured("telegram"),
            "blogger": self.is_configured("blogger"),
            "devto": self.is_configured("devto"),
            "facebook": self.is_configured("facebook"),
            "groq": self.is_configured("groq"),
            "has_feeds": len(self.feeds) > 0,
        }

    def export_config(self) -> Dict[str, Any]:
        """Export full configuration (for backup/migration)"""
        return {
            "config": self.app_config.model_dump(mode="json"),
            "feeds": [f.model_dump(mode="json") for f in self.feeds],
            "exported_at": datetime.utcnow().isoformat(),
        }

    def import_config(self, data: Dict[str, Any]) -> bool:
        """Import configuration from exported data"""
        try:
            if "config" in data:
                self.app_config = AppConfig(**data["config"])
            if "feeds" in data:
                self.feeds = [RSSFeed(**f) for f in data["feeds"]]

            self.save()
            self._save_feeds()
            return True
        except Exception as e:
            logger.error(f"Error importing config: {e}")
            return False

    def _get_default_feeds(self) -> List[RSSFeed]:
        """Get default RSS feeds for initial setup"""
        default_feeds = [
            # Arabic Tech
            {
                "name": "عالم التقنية",
                "url": "https://www.tech-wd.com/wd/feed/",
                "category": "tech",
                "language": "ar",
            },
            {
                "name": "أراجيك تقنية",
                "url": "https://www.arageek.com/tech/feed",
                "category": "tech",
                "language": "ar",
            },
            {
                "name": "صدى التقنية",
                "url": "https://www.tech-echo.com/feed",
                "category": "tech",
                "language": "ar",
            },
            # English Tech
            {
                "name": "TechCrunch",
                "url": "https://techcrunch.com/feed/",
                "category": "tech",
                "language": "en",
            },
            {
                "name": "The Verge",
                "url": "https://www.theverge.com/rss/index.xml",
                "category": "tech",
                "language": "en",
            },
            {
                "name": "Hacker News",
                "url": "https://hnrss.org/frontpage",
                "category": "programming",
                "language": "en",
            },
            # AI/ML
            {
                "name": "AI News",
                "url": "https://www.artificialintelligence-news.com/feed/",
                "category": "ai",
                "language": "en",
            },
            {
                "name": "Towards AI",
                "url": "https://pub.towardsai.net/feed",
                "category": "ai",
                "language": "en",
            },
            # Programming
            {
                "name": "Dev.to Top",
                "url": "https://dev.to/feed",
                "category": "programming",
                "language": "en",
            },
            {
                "name": "CSS Tricks",
                "url": "https://css-tricks.com/feed/",
                "category": "programming",
                "language": "en",
            },
        ]

        feeds = []
        for i, feed_data in enumerate(default_feeds):
            feeds.append(
                RSSFeed(
                    id=f"feed_default_{i+1}",
                    name=feed_data["name"],
                    url=feed_data["url"],
                    category=FeedCategory(feed_data["category"]),
                    language=feed_data["language"],
                    priority=5,
                )
            )

        return feeds

    @property
    def is_ready(self) -> bool:
        """Check if system is ready to run"""
        return (
            self.is_configured("groq")
            and self.is_configured("telegram")
            and len(self.get_active_feeds()) > 0
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

# Global config instance (singleton pattern)
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global ConfigManager instance (singleton)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
        _config_instance.load()
    return _config_instance


def reload_config() -> ConfigManager:
    """Reload and return config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    _config_instance.reload()
    return _config_instance
