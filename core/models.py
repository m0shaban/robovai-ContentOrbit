"""
ContentOrbit Enterprise - Pydantic Models
=========================================
Data validation and serialization models for the entire system.
Using Pydantic for type safety and automatic validation.
"""

from pydantic import BaseModel, Field, HttpUrl, SecretStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# ENUMS
# ═══════════════════════════════════════════════════════════════════════════════


class PostStatus(str, Enum):
    """Status of a post in the pipeline"""

    PENDING = "pending"
    PROCESSING = "processing"
    PUBLISHED = "published"
    FAILED = "failed"
    SKIPPED = "skipped"


class Platform(str, Enum):
    """Supported publishing platforms"""

    BLOGGER = "blogger"
    DEVTO = "devto"
    TELEGRAM = "telegram"
    FACEBOOK = "facebook"


class LogLevel(str, Enum):
    """Log severity levels"""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class FeedCategory(str, Enum):
    """RSS Feed categories for content filtering"""

    TECH = "tech"
    BUSINESS = "business"
    AI = "ai"
    PROGRAMMING = "programming"
    NEWS = "news"
    LIFESTYLE = "lifestyle"
    EDUCATION = "education"
    OTHER = "other"


# ═══════════════════════════════════════════════════════════════════════════════
# API CREDENTIALS MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class TelegramConfig(BaseModel):
    """Telegram Bot configuration"""

    bot_token: str = Field(..., description="Telegram Bot Token from @BotFather")
    channel_id: str = Field(
        ..., description="Channel ID (e.g., @channelname or -100xxx)"
    )
    admin_user_ids: List[int] = Field(
        default_factory=list, description="Admin user IDs for notifications"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "bot_token": "123456789:ABCdefGHIjklMNOpqrSTUvwxYZ",
                "channel_id": "@mychannel",
                "admin_user_ids": [123456789],
            }
        }


class BloggerConfig(BaseModel):
    """Blogger API configuration"""

    blog_id: str = Field(..., description="Blogger Blog ID")
    client_id: str = Field(..., description="Google OAuth Client ID")
    client_secret: str = Field(..., description="Google OAuth Client Secret")
    refresh_token: str = Field(..., description="OAuth Refresh Token")

    class Config:
        json_schema_extra = {
            "example": {
                "blog_id": "1234567890123456789",
                "client_id": "xxx.apps.googleusercontent.com",
                "client_secret": "GOCSPX-xxx",
                "refresh_token": "1//xxx",
            }
        }


class DevToConfig(BaseModel):
    """Dev.to API configuration"""

    api_key: str = Field(..., description="Dev.to API Key")
    organization_id: Optional[str] = Field(
        None, description="Organization ID (optional)"
    )

    class Config:
        json_schema_extra = {"example": {"api_key": "xxx", "organization_id": None}}


class FacebookConfig(BaseModel):
    """Facebook Graph API configuration"""

    page_id: str = Field(..., description="Facebook Page ID")
    page_access_token: str = Field(..., description="Page Access Token")

    class Config:
        json_schema_extra = {
            "example": {"page_id": "123456789", "page_access_token": "EAABxxx"}
        }


class GroqConfig(BaseModel):
    """Groq LLM API configuration"""

    api_key: str = Field(..., description="Groq API Key")
    model: str = Field(
        default="llama-3.1-70b-versatile", description="LLM Model to use"
    )
    temperature: float = Field(
        default=0.7, ge=0, le=2, description="Generation temperature"
    )
    max_tokens: int = Field(
        default=4096, ge=100, le=32000, description="Max output tokens"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "api_key": "gsk_xxx",
                "model": "llama-3.1-70b-versatile",
                "temperature": 0.7,
                "max_tokens": 4096,
            }
        }


# ═══════════════════════════════════════════════════════════════════════════════
# RSS FEED MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class RSSFeed(BaseModel):
    """RSS Feed source configuration"""

    id: Optional[str] = Field(None, description="Unique feed ID (auto-generated)")
    name: str = Field(..., description="Feed display name")
    url: str = Field(..., description="RSS Feed URL")
    category: FeedCategory = Field(
        default=FeedCategory.OTHER, description="Content category"
    )
    language: str = Field(default="ar", description="Primary language (ar/en)")
    is_active: bool = Field(default=True, description="Whether to fetch from this feed")
    priority: int = Field(
        default=5, ge=1, le=10, description="Selection priority (1-10)"
    )
    last_fetched: Optional[datetime] = Field(
        None, description="Last successful fetch time"
    )
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @validator("url")
    def validate_url(cls, v):
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class FetchedArticle(BaseModel):
    """Article fetched from RSS feed"""

    id: Optional[str] = Field(None, description="Unique article ID")
    source_feed_id: str = Field(..., description="Source RSS Feed ID")
    original_url: str = Field(..., description="Original article URL")
    title: str = Field(..., description="Article title")
    summary: Optional[str] = Field(None, description="Article summary/excerpt")
    content: Optional[str] = Field(None, description="Full article content")
    image_url: Optional[str] = Field(None, description="Best-effort image URL")
    author: Optional[str] = Field(None, description="Article author")
    published_date: Optional[datetime] = Field(
        None, description="Original publish date"
    )
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    word_count: int = Field(default=0, description="Content word count")
    language: str = Field(default="ar", description="Detected language")


# ═══════════════════════════════════════════════════════════════════════════════
# CONTENT PIPELINE MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class PublishedPost(BaseModel):
    """Record of a published post"""

    id: Optional[str] = Field(None, description="Unique post ID")
    source_article_id: str = Field(..., description="Source article ID")
    original_url: str = Field(..., description="Original source URL")

    # Generated Content
    title_ar: Optional[str] = Field(None, description="Arabic title")
    title_en: Optional[str] = Field(None, description="English title")
    content_ar: Optional[str] = Field(None, description="Arabic content")
    content_en: Optional[str] = Field(None, description="English content")

    # Platform URLs (The Spider Web)
    blogger_url: Optional[str] = Field(None, description="Published Blogger URL")
    devto_url: Optional[str] = Field(None, description="Published Dev.to URL")
    telegram_message_id: Optional[int] = Field(None, description="Telegram message ID")
    facebook_post_id: Optional[str] = Field(None, description="Facebook post ID")

    # Status tracking
    status: PostStatus = Field(default=PostStatus.PENDING)
    error_message: Optional[str] = Field(None, description="Error details if failed")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = Field(None)

    # Metadata
    processing_time_seconds: Optional[float] = Field(None)
    retry_count: int = Field(default=0)


class ContentQueueItem(BaseModel):
    """Item in the content processing queue"""

    id: Optional[str] = Field(None)
    article: FetchedArticle
    priority: int = Field(default=5, ge=1, le=10)
    status: PostStatus = Field(default=PostStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_for: Optional[datetime] = Field(None)
    attempts: int = Field(default=0)
    max_attempts: int = Field(default=3)


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM LOGGING MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class SystemLog(BaseModel):
    """System execution log entry"""

    id: Optional[str] = Field(None)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: LogLevel = Field(default=LogLevel.INFO)
    component: str = Field(..., description="Component name (fetcher/publisher/ai)")
    action: str = Field(..., description="Action performed")
    message: str = Field(..., description="Log message")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    error_traceback: Optional[str] = Field(None)

    class Config:
        json_schema_extra = {
            "example": {
                "level": "info",
                "component": "publisher",
                "action": "publish_to_blogger",
                "message": "Successfully published article",
                "details": {"blogger_url": "https://..."},
            }
        }


class SystemStats(BaseModel):
    """System statistics for dashboard"""

    posts_today: int = Field(default=0)
    posts_this_week: int = Field(default=0)
    posts_this_month: int = Field(default=0)
    total_posts: int = Field(default=0)

    errors_today: int = Field(default=0)
    errors_this_week: int = Field(default=0)

    queue_size: int = Field(default=0)
    active_feeds: int = Field(default=0)

    last_post_time: Optional[datetime] = Field(None)
    last_error_time: Optional[datetime] = Field(None)

    system_uptime_hours: float = Field(default=0)
    is_running: bool = Field(default=False)


# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM CONFIGURATION MODELS
# ═══════════════════════════════════════════════════════════════════════════════


class SystemPrompts(BaseModel):
    """AI System Prompts (The Persona)"""

    brand_name: str = Field(
        default="ContentOrbit", description="Brand name for content"
    )
    brand_voice: str = Field(
        default="Professional, engaging, and informative",
        description="Brand voice description",
    )

    # Arabic Content Prompts
    blogger_article_prompt: str = Field(
        default="""أنت كاتب محتوى محترف. اكتب مقال عربي شامل ومفصل عن الموضوع التالي.
المقال يجب أن يكون:
- 1500 كلمة على الأقل
- يحتوي على مقدمة جذابة
- عناوين فرعية واضحة (H2, H3)
- نقاط مرقمة وقوائم
- خاتمة مع دعوة للتفاعل
- SEO Optimized مع كلمات مفتاحية

الموضوع: {topic}
المصدر: {source_summary}""",
        description="Prompt for generating Blogger articles",
    )

    telegram_post_prompt: str = Field(
        default="""اكتب منشور تليجرام جذاب وقصير (150-200 كلمة) عن الموضوع التالي.
استخدم:
- إيموجي مناسبة 🎯
- لغة حوارية وجذابة
- نقاط مختصرة
- دعوة للقراءة والتفاعل

الموضوع: {topic}
رابط المقال: {article_url}""",
        description="Prompt for Telegram posts",
    )

    facebook_post_prompt: str = Field(
        default="""اكتب منشور فيسبوك بأسلوب Storytelling عن الموضوع التالي.
يجب أن يكون:
- يبدأ بقصة أو موقف
- يثير الفضول
- 200-300 كلمة
- ينتهي بسؤال للتفاعل
- يتضمن رابط المقال

الموضوع: {topic}
رابط المقال: {article_url}""",
        description="Prompt for Facebook posts",
    )

    # English Content Prompts
    devto_article_prompt: str = Field(
        default="""You are a technical writer. Write a comprehensive Dev.to article about the following topic.
The article should:
- Be 1000+ words
- Include code examples if applicable
- Have clear sections with headers
- Be beginner-friendly but informative
- Include practical tips and best practices

Topic: {topic}
Source: {source_summary}""",
        description="Prompt for Dev.to articles",
    )


class ScheduleConfig(BaseModel):
    """Scheduling configuration"""

    posting_interval_minutes: int = Field(
        default=120, ge=5, le=1440, description="Minutes between posts"
    )
    active_hours_start: int = Field(
        default=8, ge=0, le=23, description="Start hour (24h)"
    )
    active_hours_end: int = Field(default=23, ge=0, le=23, description="End hour (24h)")
    timezone: str = Field(default="Africa/Cairo", description="Timezone")
    max_posts_per_day: int = Field(
        default=7, ge=1, le=50, description="Maximum posts per day"
    )

    # Platform-specific intervals
    blogger_enabled: bool = Field(default=True)
    devto_enabled: bool = Field(default=True)
    telegram_enabled: bool = Field(default=True)
    facebook_enabled: bool = Field(default=True)


class PosterStyleConfig(BaseModel):
    """Poster / OG image style settings.

    These settings are safe to expose in the dashboard (no secrets) and are
    designed to make the poster system easily white-labelable per client.
    """

    enabled: bool = Field(default=True, description="Enable generating branded poster images")

    # Language / layout
    default_language: str = Field(default="ar", description="Default poster language (ar/en)")
    text_align: str = Field(default="center", description="Text alignment: center/right")

    # Typography
    title_font_size: int = Field(default=104, ge=16, le=180)
    hook_font_size: int = Field(default=52, ge=12, le=120)
    min_title_font_size: int = Field(default=64, ge=10, le=160)
    min_hook_font_size: int = Field(default=34, ge=10, le=100)
    max_title_lines: int = Field(default=2, ge=1, le=5)
    max_hook_lines: int = Field(default=1, ge=0, le=3)

    # Contrast / readability
    overlay_opacity: float = Field(default=0.55, ge=0.0, le=1.0)
    card_opacity: int = Field(default=150, ge=0, le=255)
    border_width: int = Field(default=4, ge=0, le=20)
    border_glow: bool = Field(default=True)

    # Text effects
    text_shadow: bool = Field(default=True)
    text_shadow_offset: int = Field(default=3, ge=0, le=20)
    text_shadow_alpha: int = Field(default=220, ge=0, le=255)
    text_outline_width: int = Field(default=3, ge=0, le=20)
    text_outline_alpha: int = Field(default=220, ge=0, le=255)

    # Watermark
    watermark_text: str = Field(default="", description="Optional watermark shown on images")
    watermark_opacity: float = Field(default=0.33, ge=0.0, le=1.0)
    watermark_font_size: int = Field(default=18, ge=8, le=48)

    # Convenience
    auto_emoji_title: bool = Field(default=True, description="Auto-prefix title with topic emoji")

    @validator("default_language")
    def _validate_language(cls, v: str):
        v = (v or "").strip().lower()
        if v not in ("ar", "en"):
            return "ar"
        return v

    @validator("text_align")
    def _validate_align(cls, v: str):
        v = (v or "").strip().lower()
        if v not in ("center", "right"):
            return "center"
        return v


class AppConfig(BaseModel):
    """Main Application Configuration - The Heart of Config-Driven Architecture"""

    # Brand Identity
    brand_name: str = Field(default="ContentOrbit Enterprise")
    brand_tagline: str = Field(default="Your Content, Everywhere")

    # API Configurations
    telegram: Optional[TelegramConfig] = None
    blogger: Optional[BloggerConfig] = None
    devto: Optional[DevToConfig] = None
    facebook: Optional[FacebookConfig] = None
    groq: Optional[GroqConfig] = None

    # System Prompts
    prompts: SystemPrompts = Field(default_factory=SystemPrompts)

    # Schedule
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)

    # Poster / Image Styling (white-label)
    poster: PosterStyleConfig = Field(default_factory=PosterStyleConfig)

    # Dashboard Security
    dashboard_password: str = Field(
        default="admin123", description="Dashboard access password"
    )

    # System Settings
    min_article_words: int = Field(
        default=200, description="Minimum words to process article"
    )
    enable_devto_for_tech_only: bool = Field(
        default=True, description="Only post tech content to Dev.to"
    )
    fallback_on_blogger_fail: bool = Field(
        default=True, description="Post to social even if Blogger fails"
    )

    # Metadata
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "My Academy",
                "telegram": {"bot_token": "xxx", "channel_id": "@myacademy"},
            }
        }
