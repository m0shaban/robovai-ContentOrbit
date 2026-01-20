"""
ContentOrbit Enterprise - LLM Client (Groq)
============================================
AI-powered content generation using Groq's blazing fast inference.
Supports multiple models including Llama 3.1 70B.

Usage:
    from core.ai_engine import LLMClient

    llm = LLMClient(config)

    # Generate Blogger article
    article = await llm.generate_blogger_article(topic, source_summary)

    # Generate Telegram post
    post = await llm.generate_telegram_post(topic, article_url)
"""

import asyncio
import json
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config_manager import ConfigManager
from core.models import FetchedArticle

logger = logging.getLogger(__name__)


@dataclass
class GeneratedContent:
    """Container for generated content"""

    title: str
    content: str
    meta_description: Optional[str] = None
    tags: List[str] = None
    language: str = "ar"

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class LLMClient:
    """
    LLM Client for Content Generation

    Uses Groq API for fast inference with Llama 3.1
    """

    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, config: ConfigManager):
        """
        Initialize LLM Client

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self._http_client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=120.0,  # LLM calls can be slow
                headers={
                    "Authorization": f"Bearer {self.config.app_config.groq.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._http_client

    async def close(self):
        """Close HTTP client"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE GENERATION
    # ═══════════════════════════════════════════════════════════════════════════

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    async def _generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Core generation method

        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Generation temperature (uses config default if None)
            max_tokens: Max output tokens (uses config default if None)

        Returns:
            Generated text
        """
        if not self.config.is_configured("groq"):
            raise ValueError("Groq API not configured")

        groq_config = self.config.app_config.groq

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": groq_config.model,
            "messages": messages,
            "temperature": temperature or groq_config.temperature,
            "max_tokens": max_tokens or groq_config.max_tokens,
            "top_p": 0.9,
            "stream": False,
        }

        client = await self._get_client()

        try:
            response = await client.post(self.GROQ_API_URL, json=payload)
            response.raise_for_status()

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            logger.info(f"✅ Generated {len(content)} characters")
            return content.strip()

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Groq API error: {e.response.status_code} - {e.response.text}"
            )
            raise
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise

    # ═══════════════════════════════════════════════════════════════════════════
    # BLOGGER ARTICLE GENERATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def generate_blogger_article(
        self, article: FetchedArticle, custom_prompt: Optional[str] = None
    ) -> GeneratedContent:
        """
        Generate a full SEO-optimized Blogger article in Arabic

        Args:
            article: Source article from RSS
            custom_prompt: Override default prompt

        Returns:
            GeneratedContent with title and HTML content
        """
        prompts = self.config.app_config.prompts

        system_prompt = f"""أنت كاتب محتوى محترف لموقع "{prompts.brand_name}".
صوت البراند: {prompts.brand_voice}

قواعد مهمة:
1. اكتب المقال بالعربية الفصحى السليمة
2. استخدم HTML للتنسيق (h2, h3, p, ul, ol, strong, em)
3. لا تستخدم كلمات مثل "في هذا المقال" أو "سنتعرف على"
4. ابدأ بمقدمة جذابة تثير الفضول
5. اجعل المحتوى شامل ومفيد وعملي
6. أضف أمثلة وحالات استخدام حقيقية
7. اختم بخاتمة تلخص النقاط الرئيسية مع دعوة للتفاعل"""

        prompt_template = custom_prompt or prompts.blogger_article_prompt

        user_prompt = prompt_template.format(
            topic=article.title, source_summary=article.summary or article.content[:500]
        )

        # Add structure requirements
        user_prompt += """

الهيكل المطلوب:
```
<h2>عنوان جذاب للمقال</h2>

<p>مقدمة جذابة (2-3 فقرات)</p>

<h3>العنوان الفرعي الأول</h3>
<p>محتوى...</p>

<h3>العنوان الفرعي الثاني</h3>
<ul>
<li>نقطة 1</li>
<li>نقطة 2</li>
</ul>

<!-- استمر بنفس النمط -->

<h3>الخاتمة</h3>
<p>ملخص وخاتمة مع دعوة للتفاعل</p>
```

أعطني المقال كاملاً بتنسيق HTML فقط."""

        content = await self._generate(user_prompt, system_prompt, temperature=0.7)

        # Extract title from generated content
        title = self._extract_title(content, article.title)

        # Clean up the HTML
        content = self._clean_html_content(content)

        # 🎯 CTA will be added by orchestrator after we have all URLs

        # Generate meta description
        meta_desc = await self._generate_meta_description(title, content[:500])

        # Extract tags
        tags = self._extract_arabic_tags(title + " " + content[:1000])

        return GeneratedContent(
            title=title,
            content=content,
            meta_description=meta_desc,
            tags=tags,
            language="ar",
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # DEV.TO ARTICLE GENERATION (ENGLISH)
    # ═══════════════════════════════════════════════════════════════════════════

    async def generate_devto_article(
        self, article: FetchedArticle, custom_prompt: Optional[str] = None
    ) -> GeneratedContent:
        """
        Generate a technical Dev.to article in English

        Args:
            article: Source article from RSS
            custom_prompt: Override default prompt

        Returns:
            GeneratedContent with title and Markdown content
        """
        prompts = self.config.app_config.prompts

        system_prompt = f"""You are a senior technical writer for "{prompts.brand_name}".
Brand voice: {prompts.brand_voice}

Guidelines:
1. Write in clear, professional English
2. Use Markdown formatting (##, ###, `, ```, -, etc.)
3. Include code examples where relevant
4. Be practical and actionable
5. Avoid fluff and filler content
6. Add real-world examples and use cases
7. End with a summary and call to action"""

        prompt_template = custom_prompt or prompts.devto_article_prompt

        user_prompt = prompt_template.format(
            topic=article.title, source_summary=article.summary or article.content[:500]
        )

        user_prompt += """

Required structure:
```markdown
# Compelling Title

Brief intro paragraph...

## Section 1
Content with examples...

```language
// Code example if applicable
```

## Section 2
More content...

## Key Takeaways
- Point 1
- Point 2
- Point 3

## Conclusion
Summary and call to action...
```

Provide the complete article in Markdown format."""

        content = await self._generate(user_prompt, system_prompt, temperature=0.6)

        # Extract title
        title = self._extract_markdown_title(content, article.title)

        # Extract tags
        tags = self._extract_tech_tags(title + " " + content[:1000])

        return GeneratedContent(
            title=title,
            content=content,
            tags=tags[:4],  # Dev.to allows max 4 tags
            language="en",
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # TECHNICAL Q&A (Telegram Chatbot)
    # ═══════════════════════════════════════════════════════════════════════════

    async def answer_technical_question(
        self,
        question: str,
        language: str = "ar",
        max_tokens: int = 700,
    ) -> str:
        """Answer technical questions for chatbot mode (concise, practical)."""
        prompts = self.config.app_config.prompts

        if language.lower().startswith("ar"):
            system_prompt = f"""أنت مساعد تقني محترف لبراند "{prompts.brand_name}".

قواعد:
1) أجب بإيجاز مع خطوات عملية.
2) لو السؤال يحتاج كود: أعطِ مثال صغير واضح.
3) لو فيه نقص معلومات: اسأل سؤال/سؤالين توضيحيين.
4) تجنب الإطالة.
"""
        else:
            system_prompt = f"""You are a senior technical assistant for "{prompts.brand_name}".

Rules:
1) Be concise and practical.
2) Provide small, clear code examples when needed.
3) Ask 1-2 clarifying questions if required.
4) Avoid fluff.
"""

        user_prompt = f"""Question:
{question.strip()}

Answer:"""

        return await self._generate(
            user_prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=max_tokens,
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # TELEGRAM POST GENERATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def generate_telegram_post(
        self,
        article: FetchedArticle,
        blogger_url: Optional[str] = None,
        devto_url: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a native Telegram post in Arabic

        Args:
            article: Source article
            blogger_url: URL to Blogger article (CTA)
            devto_url: URL to Dev.to article (CTA)
            custom_prompt: Override default prompt

        Returns:
            Formatted Telegram post text
        """
        prompts = self.config.app_config.prompts

        system_prompt = f"""أنت مدير سوشيال ميديا محترف لـ "{prompts.brand_name}".
اكتب منشورات تليجرام بأسلوب:
- جذاب ومشوق
- استخدام إيموجي مناسبة (لكن بدون إفراط)
- لغة حوارية وودودة
- نقاط مختصرة ومفيدة
- دعوة واضحة للقراءة"""

        prompt_template = custom_prompt or prompts.telegram_post_prompt

        # Build CTA links
        cta_links = ""
        if blogger_url:
            cta_links += f"\n📖 اقرأ المقال كامل:\n{blogger_url}"
        if devto_url:
            cta_links += f"\n\n🇬🇧 English version:\n{devto_url}"

        user_prompt = f"""{prompt_template.format(
            topic=article.title,
            article_url=blogger_url or article.original_url
        )}

روابط المقال:
{cta_links if cta_links else article.original_url}

ملاحظات:
- الطول: 150-250 كلمة
- استخدم 3-5 إيموجي فقط
- اجعل أول سطر جذاب جداً (Hook)
- ضع الروابط في النهاية
- أضف هاشتاقات مناسبة (2-3)"""

        post = await self._generate(
            user_prompt, system_prompt, temperature=0.8, max_tokens=500
        )

        # Ensure links are included
        if blogger_url and blogger_url not in post:
            post += f"\n\n📖 {blogger_url}"
        if devto_url and devto_url not in post:
            post += f"\n🇬🇧 {devto_url}"

        return post

    async def generate_egyptian_arabic_summary(
        self, article: FetchedArticle, max_words: int = 90
    ) -> str:
        """Generate a short Egyptian Arabic summary (no English, no links).

        We use this to keep Telegram posts consistently Egyptian Arabic even when
        the RSS source is English.
        """
        prompts = self.config.app_config.prompts

        system_prompt = f"""أنت كاتب سوشيال ميديا مصري لـ "{prompts.brand_name}".

قواعد صارمة:
1) اكتب بالعربي المصري فقط (ممنوع الإنجليزية).
2) 2-4 جمل قصيرة.
3) ممنوع الروابط.
4) ممنوع تكرار عنوان المقال.
5) خلي الملخص مفهوم لحد مش متخصص.
"""

        src = (article.summary or article.content or "").strip()
        src = re.sub(r"\s+", " ", src)
        src = src[:1200]

        user_prompt = (
            f"عنوان المقال (للسياق فقط): {article.title}\n\n"
            f"نص/ملخص المصدر:\n{src}\n\n"
            f"اكتب ملخص مصري في حدود {max_words} كلمة."
        )

        out = await self._generate(user_prompt, system_prompt=system_prompt, temperature=0.6, max_tokens=220)
        out = out.strip()
        # Defensive cleanup: strip any accidental URLs/English remnants.
        out = re.sub(r"https?://\S+", "", out).strip()
        return out

    # ═══════════════════════════════════════════════════════════════════════════
    # FACEBOOK POST GENERATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def generate_facebook_post(
        self,
        article: FetchedArticle,
        blogger_url: Optional[str] = None,
        custom_prompt: Optional[str] = None,
    ) -> str:
        """
        Generate a storytelling Facebook post in Arabic

        Args:
            article: Source article
            blogger_url: URL to Blogger article (CTA)
            custom_prompt: Override default prompt

        Returns:
            Facebook post text
        """
        prompts = self.config.app_config.prompts

        system_prompt = f"""أنت كاتب محتوى سوشيال ميديا لـ "{prompts.brand_name}".
تخصصك كتابة منشورات فيسبوك بأسلوب Storytelling:
- ابدأ بقصة أو موقف شخصي
- اجعل القارئ يتفاعل عاطفياً
- اطرح سؤال يثير النقاش
- اختم بدعوة للتعليق والمشاركة"""

        prompt_template = custom_prompt or prompts.facebook_post_prompt

        user_prompt = f"""{prompt_template.format(
            topic=article.title,
            article_url=blogger_url or article.original_url
        )}

ملاحظات:
- الطول: 200-350 كلمة
- ابدأ بـ Hook قوي (سؤال أو قصة)
- لا تستخدم إيموجي كثيرة
- اختم بسؤال للجمهور
- ضع رابط المقال في النهاية

رابط المقال: {blogger_url or article.original_url}"""

        post = await self._generate(
            user_prompt, system_prompt, temperature=0.85, max_tokens=600
        )

        # Ensure link is included
        link = blogger_url or article.original_url
        if link not in post:
            post += f"\n\n🔗 {link}"

        return post

    # ═══════════════════════════════════════════════════════════════════════════
    # IMAGE PROMPT GENERATION
    # ═══════════════════════════════════════════════════════════════════════════

    async def generate_image_prompt(self, article: FetchedArticle) -> str:
        """
        Generate an image generation prompt for article thumbnail

        Args:
            article: Source article

        Returns:
            Image generation prompt (for DALL-E, Midjourney, etc.)
        """
        system_prompt = """You are an expert at creating image generation prompts.
Create prompts that produce professional, eye-catching thumbnails for blog posts.
Style: Modern, clean, professional, slightly abstract."""

        user_prompt = f"""Create an image generation prompt for a blog post about:
Title: {article.title}
Summary: {article.summary or article.content[:200]}

Requirements:
- Professional and modern style
- No text in the image
- Suitable for a blog thumbnail
- Wide format (16:9)

Provide only the prompt, nothing else."""

        return await self._generate(
            user_prompt, system_prompt, temperature=0.7, max_tokens=200
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def _extract_title(self, content: str, fallback: str) -> str:
        """Extract title from HTML content"""
        # Try h2 first
        match = re.search(r"<h2[^>]*>([^<]+)</h2>", content)
        if match:
            return match.group(1).strip()

        # Try h1
        match = re.search(r"<h1[^>]*>([^<]+)</h1>", content)
        if match:
            return match.group(1).strip()

        # Try first line
        first_line = content.split("\n")[0]
        if first_line and len(first_line) < 200:
            # Clean HTML tags
            first_line = re.sub(r"<[^>]+>", "", first_line).strip()
            if first_line:
                return first_line

        return fallback

    def _extract_markdown_title(self, content: str, fallback: str) -> str:
        """Extract title from Markdown content"""
        # Try # heading
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        return fallback

    def _clean_html_content(self, content: str) -> str:
        """Clean and normalize HTML content"""
        # Remove markdown code blocks if present
        content = re.sub(r"```html?\n?", "", content)
        content = re.sub(r"```\n?", "", content)

        # Ensure proper paragraph wrapping
        lines = content.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("<"):
                line = f"<p>{line}</p>"
            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    async def _generate_meta_description(self, title: str, content: str) -> str:
        """Generate SEO meta description"""
        prompt = f"""اكتب وصف ميتا (Meta Description) للمقال التالي:
العنوان: {title}
المحتوى: {content}

المتطلبات:
- 150-160 حرف بالضبط
- يحتوي على الكلمة المفتاحية الرئيسية
- جذاب ويشجع على النقر
- بالعربية

اكتب الوصف فقط، بدون علامات تنصيص."""

        return await self._generate(prompt, temperature=0.5, max_tokens=100)

    def _extract_arabic_tags(self, text: str) -> List[str]:
        """Extract relevant Arabic tags/keywords"""
        common_tags = [
            "تقنية",
            "تكنولوجيا",
            "برمجة",
            "ذكاء_اصطناعي",
            "تطوير",
            "أعمال",
            "ريادة",
            "تسويق",
            "إنتاجية",
            "تعلم",
            "هواتف",
            "تطبيقات",
            "ألعاب",
            "أمان",
            "سوشيال_ميديا",
        ]

        text_lower = text.lower()
        found_tags = []

        # Simple keyword matching
        keywords_map = {
            "تقنية": ["تقنية", "تكنولوجيا", "تقني"],
            "برمجة": ["برمجة", "كود", "مبرمج", "بايثون", "جافا"],
            "ذكاء_اصطناعي": ["ذكاء اصطناعي", "ai", "تعلم آلي", "machine learning"],
            "تطوير": ["تطوير", "developer", "مطور"],
            "أعمال": ["أعمال", "business", "شركة", "startup"],
            "تسويق": ["تسويق", "marketing", "إعلان"],
        }

        for tag, keywords in keywords_map.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_tags.append(tag)
                    break

        return list(set(found_tags))[:5]

    def _extract_tech_tags(self, text: str) -> List[str]:
        """Extract relevant tech tags for Dev.to"""
        common_tags = [
            "python",
            "javascript",
            "webdev",
            "programming",
            "tutorial",
            "beginners",
            "ai",
            "machinelearning",
            "devops",
            "react",
            "nodejs",
            "database",
            "api",
            "security",
            "productivity",
        ]

        text_lower = text.lower()
        found_tags = []

        for tag in common_tags:
            if tag in text_lower or tag.replace("_", " ") in text_lower:
                found_tags.append(tag)

        # Always include these if tech-related
        if not found_tags:
            found_tags = ["programming", "tutorial"]

        return found_tags[:4]
