"""
ContentOrbit Enterprise - Prompt Manager
=========================================
Centralized prompt management and templating.
Allows dynamic prompt customization from dashboard.

Usage:
    from core.ai_engine import PromptManager

    pm = PromptManager(config)
    prompt = pm.get_blogger_prompt(topic="AI", summary="...")
"""

from typing import Optional, Dict, Any
from string import Template
import logging

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Prompt Manager for centralized prompt handling

    Features:
    - Template-based prompts
    - Dynamic variable substitution
    - Easy customization from dashboard
    """

    def __init__(self, config: ConfigManager):
        """
        Initialize Prompt Manager

        Args:
            config: ConfigManager instance
        """
        self.config = config

    @property
    def prompts(self):
        """Get current prompts from config"""
        return self.config.app_config.prompts

    @property
    def brand_name(self) -> str:
        """Get brand name"""
        return self.prompts.brand_name

    @property
    def brand_voice(self) -> str:
        """Get brand voice description"""
        return self.prompts.brand_voice

    # ═══════════════════════════════════════════════════════════════════════════
    # PROMPT GETTERS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_blogger_prompt(self, topic: str, source_summary: str) -> str:
        """
        Get formatted Blogger article prompt

        Args:
            topic: Article topic/title
            source_summary: Source article summary

        Returns:
            Formatted prompt string
        """
        template = self.prompts.blogger_article_prompt
        return template.format(topic=topic, source_summary=source_summary)

    def get_telegram_prompt(self, topic: str, article_url: str) -> str:
        """
        Get formatted Telegram post prompt

        Args:
            topic: Post topic
            article_url: Link to article

        Returns:
            Formatted prompt string
        """
        template = self.prompts.telegram_post_prompt
        return template.format(topic=topic, article_url=article_url)

    def get_facebook_prompt(self, topic: str, article_url: str) -> str:
        """
        Get formatted Facebook post prompt

        Args:
            topic: Post topic
            article_url: Link to article

        Returns:
            Formatted prompt string
        """
        template = self.prompts.facebook_post_prompt
        return template.format(topic=topic, article_url=article_url)

    def get_devto_prompt(self, topic: str, source_summary: str) -> str:
        """
        Get formatted Dev.to article prompt

        Args:
            topic: Article topic
            source_summary: Source summary

        Returns:
            Formatted prompt string
        """
        template = self.prompts.devto_article_prompt
        return template.format(topic=topic, source_summary=source_summary)

    # ═══════════════════════════════════════════════════════════════════════════
    # SYSTEM PROMPTS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_blogger_system_prompt(self) -> str:
        """Get system prompt for Blogger article generation"""
        return f"""أنت كاتب محتوى محترف لموقع "{self.brand_name}".
صوت البراند: {self.brand_voice}

قواعد مهمة:
1. اكتب المقال بالعربية الفصحى السليمة
2. استخدم HTML للتنسيق (h2, h3, p, ul, ol, strong, em)
3. لا تستخدم كلمات مثل "في هذا المقال" أو "سنتعرف على"
4. ابدأ بمقدمة جذابة تثير الفضول
5. اجعل المحتوى شامل ومفيد وعملي
6. أضف أمثلة وحالات استخدام حقيقية
7. اختم بخاتمة تلخص النقاط الرئيسية مع دعوة للتفاعل"""

    def get_telegram_system_prompt(self) -> str:
        """Get system prompt for Telegram post generation"""
        return f"""أنت مدير سوشيال ميديا محترف لـ "{self.brand_name}".
اكتب منشورات تليجرام بأسلوب:
- جذاب ومشوق
- استخدام إيموجي مناسبة (لكن بدون إفراط)
- لغة حوارية وودودة
- نقاط مختصرة ومفيدة
- دعوة واضحة للقراءة"""

    def get_facebook_system_prompt(self) -> str:
        """Get system prompt for Facebook post generation"""
        return f"""أنت كاتب محتوى سوشيال ميديا لـ "{self.brand_name}".
تخصصك كتابة منشورات فيسبوك بأسلوب Storytelling:
- ابدأ بقصة أو موقف شخصي
- اجعل القارئ يتفاعل عاطفياً
- اطرح سؤال يثير النقاش
- اختم بدعوة للتعليق والمشاركة"""

    def get_devto_system_prompt(self) -> str:
        """Get system prompt for Dev.to article generation"""
        return f"""You are a senior technical writer for "{self.brand_name}".
Brand voice: {self.brand_voice}

Guidelines:
1. Write in clear, professional English
2. Use Markdown formatting (##, ###, `, ```, -, etc.)
3. Include code examples where relevant
4. Be practical and actionable
5. Avoid fluff and filler content
6. Add real-world examples and use cases
7. End with a summary and call to action"""

    # ═══════════════════════════════════════════════════════════════════════════
    # PROMPT VALIDATION
    # ═══════════════════════════════════════════════════════════════════════════

    def validate_prompt(self, prompt: str, required_vars: list) -> tuple[bool, str]:
        """
        Validate a prompt template

        Args:
            prompt: Prompt template string
            required_vars: List of required variables (e.g., ['topic', 'summary'])

        Returns:
            Tuple of (is_valid, error_message)
        """
        for var in required_vars:
            placeholder = "{" + var + "}"
            if placeholder not in prompt:
                return False, f"Missing required variable: {placeholder}"

        # Try formatting with dummy values
        try:
            dummy_values = {var: "test" for var in required_vars}
            prompt.format(**dummy_values)
            return True, "Valid"
        except KeyError as e:
            return False, f"Invalid variable reference: {e}"
        except Exception as e:
            return False, f"Template error: {e}"

    def update_prompt(self, prompt_type: str, new_prompt: str) -> bool:
        """
        Update a prompt in config

        Args:
            prompt_type: Type of prompt (blogger, telegram, facebook, devto)
            new_prompt: New prompt template

        Returns:
            True if updated successfully
        """
        required_vars_map = {
            "blogger": ["topic", "source_summary"],
            "telegram": ["topic", "article_url"],
            "facebook": ["topic", "article_url"],
            "devto": ["topic", "source_summary"],
        }

        if prompt_type not in required_vars_map:
            logger.error(f"Unknown prompt type: {prompt_type}")
            return False

        # Validate
        is_valid, message = self.validate_prompt(
            new_prompt, required_vars_map[prompt_type]
        )
        if not is_valid:
            logger.error(f"Invalid prompt: {message}")
            return False

        # Update config
        update_kwargs = {}
        if prompt_type == "blogger":
            update_kwargs["blogger_prompt"] = new_prompt
        elif prompt_type == "telegram":
            update_kwargs["telegram_prompt"] = new_prompt
        elif prompt_type == "facebook":
            update_kwargs["facebook_prompt"] = new_prompt
        elif prompt_type == "devto":
            update_kwargs["devto_prompt"] = new_prompt

        return self.config.update_prompts(**update_kwargs)
