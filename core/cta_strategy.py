"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🎯 ContentOrbit CTA Strategy Engine                        ║
║                    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                         ║
║                                                                              ║
║   Smart Cross-Platform Call-to-Action System                                 ║
║                                                                              ║
║   Traffic Flow Strategy:                                                     ║
║   ┌─────────────────────────────────────────────────────────────────────┐   ║
║   │                         RSS SOURCE                                   │   ║
║   │                              │                                       │   ║
║   │                              ▼                                       │   ║
║   │   ┌──────────────┐    ┌──────────────┐                              │   ║
║   │   │   Dev.to     │───▶│   Blogger    │                              │   ║
║   │   │  (English)   │    │   (Arabic)   │                              │   ║
║   │   │  Tech Pros   │    │  Arab Readers│                              │   ║
║   │   └──────┬───────┘    └──────┬───────┘                              │   ║
║   │          │                   │                                       │   ║
║   │          │    ┌──────────────┼──────────────┐                       │   ║
║   │          │    │              │              │                       │   ║
║   │          ▼    ▼              ▼              ▼                       │   ║
║   │   ┌──────────────┐    ┌──────────────┐                              │   ║
║   │   │   Telegram   │◀───│   Facebook   │                              │   ║
║   │   │  (Hub/News)  │    │  (Social)    │                              │   ║
║   │   │ All Links    │    │ →Blogger     │                              │   ║
║   │   └──────────────┘    └──────────────┘                              │   ║
║   └─────────────────────────────────────────────────────────────────────┘   ║
║                                                                              ║
║   Author: ContentOrbit Marketing & Dev Team                                  ║
║   Version: 1.0.0                                                             ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported publishing platforms"""

    DEVTO = "devto"
    BLOGGER = "blogger"
    FACEBOOK = "facebook"
    TELEGRAM = "telegram"


@dataclass
class PlatformLinks:
    """Container for all platform URLs"""

    devto_url: Optional[str] = None
    blogger_url: Optional[str] = None
    facebook_url: Optional[str] = None
    telegram_url: Optional[str] = None

    # Public hubs/pages
    telegram_channel: str = "@robovai_hub"
    telegram_hub_url: str = "https://t.me/robovai_hub"
    facebook_page: str = "https://www.facebook.com/robovaisolutions"
    devto_profile: str = "https://dev.to/mohamedshabanai/"
    blogger_home: str = "https://www.robovai.tech/"
    whatsapp_url: str = "https://wa.me/201234567890"  # Update with actual number

    # Personal Branding & Community
    personal_site: str = "https://moshaban.me"
    community_chat: str = "https://t.me/robovai_chat"

    # RoboVAI Ecosystem
    academy_url: str = "https://academy.robovai.tech"
    bot_url: str = "https://bot.robovai.tech"
    junior_url: str = "https://junior.robovai.tech"
    core_url: str = "https://core.robovai.tech"

    def update_from_dict(self, config: Dict[str, str]):
        """Updates fields from a dictionary (e.g., from Google Sheets)."""
        for key, value in config.items():
            if hasattr(self, key):
                setattr(self, key, value)



class CTAStrategy:
    """
    🎯 Smart CTA Generator

    Generates platform-specific CTAs that create a traffic loop:

    Strategy Goals:
    1. Keep readers in our ecosystem
    2. Cross-promote all platforms
    3. Build community across channels
    4. Maximize engagement per platform

    Platform Roles:
    - Dev.to: Authority building (English tech community)
    - Blogger: Arabic content hub (main blog)
    - Facebook: Social engagement & sharing
    - Telegram: News hub & direct updates
    """

    def __init__(self, links: Optional[PlatformLinks] = None, config_manager=None):
        self.links = links or PlatformLinks()
        
        # If config manager provided and has sheets connected, sync
        if config_manager and config_manager.sheets_manager.is_connected():
            logger.info("⚡ Syncing CTA Links from Google Sheets...")
            sheet_config = config_manager.sheets_manager.fetch_config()
            if sheet_config:
                self.links.update_from_dict(sheet_config)

    # ═══════════════════════════════════════════════════════════════════════════
    # 📝 BLOGGER CTAs (Arabic - Main Blog)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_blogger_cta(
        self, devto_url: Optional[str] = None, article_title: Optional[str] = None
    ) -> str:
        """
        Generate CTA for Blogger articles (Arabic).
        Strategy: "The Professional Friend" - Ecosystem Integration.
        """

        telegram_url = self.links.telegram_hub_url
        facebook_url = self.links.facebook_page
        personal_site = self.links.personal_site

        # RoboVAI Platforms
        academy = self.links.academy_url
        bot = self.links.bot_url
        junior = self.links.junior_url
        core = self.links.core_url

        cta_html = f"""
<div style="background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%); padding: 40px; border-radius: 15px; margin: 50px 0; direction: rtl; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
    
    <!-- Header -->
    <div style="text-align: center; margin-bottom: 35px;">
        <h3 style="color: #ffffff; font-size: 28px; margin: 0 0 10px 0; font-weight: 800;">
            🚀 الفرصة بتيجي للي جاهز لها.. وأنا هنا عشان أساعدك
        </h3>
        <p style="color: #a0aec0; font-size: 18px; margin: 0;">
            التحول الرقمي مش مجرد كلام، دي خطوات عملية بنبنيها سوا في RoboVAI
        </p>
    </div>
    
    <!-- RoboVAI Grid -->
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 35px;">
        
        <a href="{academy}" target="_blank" style="text-decoration: none; text-align: center; background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; transition: transform 0.2s; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 30px; margin-bottom: 10px;">🎓</div>
            <div style="color: white; font-weight: bold; margin-bottom: 5px;">RoboVAI Academy</div>
            <div style="color: #a0aec0; font-size: 12px;">كيريرك في الـ AI يبدأ هنا</div>
        </a>

        <a href="{bot}" target="_blank" style="text-decoration: none; text-align: center; background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; transition: transform 0.2s; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 30px; margin-bottom: 10px;">🤖</div>
            <div style="color: white; font-weight: bold; margin-bottom: 5px;">RoboVAI Bot</div>
            <div style="color: #a0aec0; font-size: 12px;">أتمتة أعمالك بذكاء</div>
        </a>

        <a href="{junior}" target="_blank" style="text-decoration: none; text-align: center; background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; transition: transform 0.2s; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 30px; margin-bottom: 10px;">🧒</div>
            <div style="color: white; font-weight: bold; margin-bottom: 5px;">RoboVAI Junior</div>
            <div style="color: #a0aec0; font-size: 12px;">علّم أولادك لغة المستقبل</div>
        </a>

        <a href="{core}" target="_blank" style="text-decoration: none; text-align: center; background: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; transition: transform 0.2s; border: 1px solid rgba(255,255,255,0.1);">
            <div style="font-size: 30px; margin-bottom: 10px;">⚙️</div>
            <div style="color: white; font-weight: bold; margin-bottom: 5px;">RoboVAI Core</div>
            <div style="color: #a0aec0; font-size: 12px;">حلول المصانع والشركات</div>
        </a>

    </div>
    
    <!-- Platform Buttons -->
    <div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; margin-bottom: 25px;">
        
        <!-- Telegram Button (Primary) -->
        <a href="{telegram_url}" target="_blank" 
           style="display: inline-flex; align-items: center; gap: 8px; 
                  background: #0088cc; color: white; padding: 12px 24px; 
                  border-radius: 50px; text-decoration: none; font-weight: bold;
                  transition: transform 0.2s; box-shadow: 0 4px 15px rgba(0,136,204,0.4);">
            <span style="font-size: 20px;">📱</span>
            مجتمع تيليجرام
        </a>
        
        <!-- Personal Site Button -->
        <a href="{personal_site}" target="_blank"
           style="display: inline-flex; align-items: center; gap: 8px;
                  background: #2d3748; color: white; padding: 12px 24px;
                  border-radius: 50px; text-decoration: none; font-weight: bold;
                  transition: transform 0.2s; border: 1px solid rgba(255,255,255,0.2);">
            <span style="font-size: 20px;">👤</span>
            من هو محمد شعبان؟
        </a>
        
    </div>
</div>
"""

        # Add Dev.to link if available (for English version)
        if devto_url:
            cta_html += f"""
<div style="text-align: center; margin-top: 20px;">
    <a href="{devto_url}" target="_blank" style="color: #666; text-decoration: none; font-size: 14px;">
        🌍 Prefer English? Read this article on Dev.to
    </a>
</div>
"""

        return cta_html

    # ═══════════════════════════════════════════════════════════════════════════
    # 💻 DEV.TO CTAs (English - Tech Community)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_devto_cta(
        self, blogger_url: Optional[str] = None, article_topic: Optional[str] = None
    ) -> str:
        """
        Generate CTA for Dev.to articles (English).

        Strategy:
        - Dev.to builds authority in tech community
        - Drive engagement (likes, comments, follows)
        - Mention Telegram for instant updates
        - Cross-link to Arabic version for bilingual readers
        """

        telegram_url = self.links.telegram_hub_url
        blogger_home = self.links.blogger_home

        cta_md = f"""
---

## 🚀 Enjoyed this article?

If you found this helpful, here's how you can support:

### 💙 Engage
- **Like** this post if it helped you
- **Comment** with your thoughts or questions
- **Follow** me for more tech content

### 📱 Stay Connected
- **Telegram**: Join our updates hub → [{telegram_url}]({telegram_url})
- **More Articles**: Check out the Arabic hub → [{blogger_home}]({blogger_home})

"""

        if blogger_url:
            cta_md += f"""
### 🌍 Arabic Version
تفضل العربية؟ اقرأ المقال بالعربية:
→ [{blogger_url}]({blogger_url})

"""

        cta_md += """
---

*Thanks for reading! See you in the next one.* ✌️

"""

        return cta_md

    # ═══════════════════════════════════════════════════════════════════════════
    # 📘 FACEBOOK CTAs (Social Engagement)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_facebook_post(
        self, title: str, hook: str, blogger_url: str, emoji: str = "🔥"
    ) -> str:
        """
        Generate Facebook post with CTA to Blogger.
        Strategy: "The Professional Friend" - First person, relatable, smart CTA.
        """

        telegram_url = self.links.telegram_hub_url
        whatsapp_url = self.links.whatsapp_url
        personal_site = self.links.personal_site
        community_chat = self.links.community_chat

        post = f"""{emoji} {title}

{hook}

أنا بقولك: التحول الرقمي بيبدأ بخطوة بسيطة، والفرصة بتيجي للي جاهز لها. الموضوع مش رفاهية، ده تأمين لمستقبل شركتك في سوق مبيستناش حد. 🇪🇬🏭

📖 شوف التفاصيل كاملة هنا:
👇👇👇
{blogger_url}

━━━━━━━━━━━━━━━━━━━━

محتاج مساعدة تبدأ أول خطوة في تحول شركتك الرقمي؟
تواصل معايا مباشرة لنقاش تقني يغير مسار شغلك: {whatsapp_url}

أو خد فكرة عن مشاريعنا وقدراتنا من هنا:
🌐 {personal_site}

📣 تابعني على التليجرام عشان ميفوتكش الأدوات المجانية:
{telegram_url}

للنقاشات التقنية، انضم لجروبنا: {community_chat}

#TechnoEgypt #SMEs #DigitalTransformation #RoboVAI"""

        return post

    def get_facebook_post_engaging(
        self, title: str, key_points: List[str], blogger_url: str
    ) -> str:
        """
        Generate engaging Facebook post with bullet points.
        Strategy: "The Professional Friend" - Value first.
        """

        points_text = "\n".join([f"✅ {point}" for point in key_points[:5]])

        telegram_url = self.links.telegram_hub_url
        whatsapp_url = self.links.whatsapp_url
        personal_site = self.links.personal_site

        post = f"""🚀 {title}

من كتر ما شوفت شركات بتضيع وقت وفلوس، حبيت أشاركك الخلاصة دي:

{points_text}

في الأول والآخر، التكنولوجيا معمولة عشان تخدمنا مش تعقدنا. 

━━━━━━━━━━━━━━━━━━━━

🔗 اقرأ المقال الكامل عشان تفهم الصورة الأكبر:
{blogger_url}

لو شايف إن الكلام ده مفيد لبيزنس صاحبك، اعمله منشن.
وتابعني هنا لمحتوى يومي بيغير طريقة تفكيرك.

محتاج استشارة خاصة لمشروعك؟
📞 {whatsapp_url}

اعرف أكتر عن اللي بنقدمه: {personal_site}

#تطوير #صناعة #RoboVAI"""

        return post

    # ═══════════════════════════════════════════════════════════════════════════
    # 📱 TELEGRAM CTAs (News Hub - All Links)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_telegram_message(
        self,
        title: str,
        summary: str,
        blogger_url: Optional[str] = None,
        devto_url: Optional[str] = None,
        key_points: Optional[List[str]] = None,
    ) -> str:
        """
        Generate Telegram message with all platform links.
        Strategy: Technical Value + "The Professional Friend" signature.
        """

        telegram_url = self.links.telegram_hub_url
        personal_site = self.links.personal_site
        community_chat = self.links.community_chat

        # Telegram UX: concise, technical, direct value.
        safe_title = title
        safe_summary = summary

        message = (
            "🚀 <b>Technical Update</b>\n\n"
            f"<b>{safe_title}</b>\n\n"
            f"{safe_summary}\n\n"
        )

        # Add key points if provided
        if key_points:
            message += "\n<b>🛠️ Key Technical Insights:</b>\n"
            for point in key_points[:4]:
                message += f"• {point}\n"
            message += "\n"

        # Links section
        message += "━━━━━━━━━━━━━━━━━━━━\n\n"
        message += "👇 <b>Get the Full Solution:</b>\n"

        if blogger_url:
            message += f'• 📑 <a href="{blogger_url}">Strategy Guide (Arabic)</a>\n'

        if devto_url:
            message += f'• 💻 <a href="{devto_url}">Technical Breakdown (Dev.to)</a>\n'

        message += f'\n💬 <a href="{community_chat}">Discuss with Tech Community</a>\n'
        message += f'👤 <a href="{personal_site}">About Mohamed Shaban</a>\n\n'

        # Engagement CTA
        message += (
            "<i>Need technical implementation? DM me.</i>\n"
            "#RoboVAI #DigitalTransformation #Tech"
        )

        return message

    def get_telegram_news_brief(
        self, title: str, one_liner: str, blogger_url: str
    ) -> str:
        """
        Generate short Telegram news brief.

        Strategy:
        - Ultra-short format for quick consumption
        - Single link focus
        - Easy engagement
        """

        return f"""⚡️ <b>{title}</b>

    {one_liner}

    👉 <a href="{blogger_url}">اقرأ دلوقتي</a>

    ❤️ للمزيد تابع {self.links.telegram_channel}"""

    # ═══════════════════════════════════════════════════════════════════════════
    # 🔄 CROSS-PLATFORM INTEGRATION
    # ═══════════════════════════════════════════════════════════════════════════

    def generate_all_ctas(
        self,
        title_ar: str,
        title_en: str,
        summary_ar: str,
        summary_en: str,
        blogger_url: str,
        devto_url: str,
        key_points_ar: Optional[List[str]] = None,
        key_points_en: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Generate CTAs for all platforms at once.

        Returns a dictionary with ready-to-use content for each platform.
        """

        return {
            "blogger_cta": self.get_blogger_cta(devto_url=devto_url),
            "devto_cta": self.get_devto_cta(blogger_url=blogger_url),
            "facebook_post": self.get_facebook_post(
                title=title_ar,
                hook=summary_ar[:200] + "...",
                blogger_url=blogger_url,
                emoji="🔥",
            ),
            "telegram_message": self.get_telegram_message(
                title=title_ar,
                summary=summary_ar,
                blogger_url=blogger_url,
                devto_url=devto_url,
                key_points=key_points_ar,
            ),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 CONTENT STRATEGY RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════════


class ContentStrategyAdvisor:
    """
    📊 Marketing Strategy Advisor

    Provides recommendations for content optimization and cross-platform growth.
    """

    @staticmethod
    def get_platform_roles() -> Dict[str, Dict]:
        """Define the role of each platform in your ecosystem."""

        return {
            "devto": {
                "role": "Authority Builder",
                "audience": "English-speaking developers & tech enthusiasts",
                "content_type": "Long-form technical articles",
                "goal": "Build credibility, earn followers, get featured",
                "cta_focus": "Follow + Telegram",
                "posting_frequency": "2-3 articles/week",
                "best_times": "Tuesday-Thursday, 9AM-11AM EST",
            },
            "blogger": {
                "role": "Arabic Content Hub",
                "audience": "Arabic-speaking tech readers",
                "content_type": "Comprehensive articles with examples",
                "goal": "Be the go-to Arabic tech blog",
                "cta_focus": "Telegram + Facebook + Comments",
                "posting_frequency": "Daily",
                "best_times": "Evening hours (6PM-10PM Cairo time)",
            },
            "facebook": {
                "role": "Social Amplifier",
                "audience": "Casual tech-interested readers",
                "content_type": "Teasers, snippets, engagement posts",
                "goal": "Drive traffic to Blogger, build community",
                "cta_focus": "Read full article → Blogger",
                "posting_frequency": "1-2 posts/day",
                "best_times": "12PM-2PM, 7PM-9PM",
            },
            "telegram": {
                "role": "News Hub & Community",
                "audience": "Engaged followers wanting instant updates",
                "content_type": "News briefs, all links, discussions",
                "goal": "Instant notification, cross-platform promotion",
                "cta_focus": "All platform links + engagement",
                "posting_frequency": "Every new article + daily tips",
                "best_times": "Anytime (instant delivery)",
            },
        }

    @staticmethod
    def get_traffic_flow_strategy() -> str:
        """Explain the optimal traffic flow between platforms."""

        return """
╔═══════════════════════════════════════════════════════════════════════╗
║                    🔄 TRAFFIC FLOW STRATEGY                           ║
╠═══════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   CONTENT CREATION FLOW:                                              ║
║   ━━━━━━━━━━━━━━━━━━━━━                                               ║
║   RSS Source → AI Processing → Dev.to (EN) + Blogger (AR)             ║
║                                                                       ║
║   TRAFFIC DISTRIBUTION:                                               ║
║   ━━━━━━━━━━━━━━━━━━━━━                                               ║
║                                                                       ║
║   ┌──────────┐         ┌──────────┐                                   ║
║   │  Dev.to  │ ──────▶ │ Telegram │ ◀────── All traffic               ║
║   │  (EN)    │         │  (Hub)   │         converges here            ║
║   └────┬─────┘         └────┬─────┘                                   ║
║        │                    │                                         ║
║        │    ┌───────────────┼───────────────┐                         ║
║        │    │               │               │                         ║
║        ▼    ▼               ▼               ▼                         ║
║   ┌──────────┐         ┌──────────┐                                   ║
║   │ Blogger  │ ◀────── │ Facebook │                                   ║
║   │  (AR)    │         │ (Social) │                                   ║
║   └──────────┘         └──────────┘                                   ║
║        ▲                    │                                         ║
║        │                    │                                         ║
║        └────────────────────┘                                         ║
║        (Facebook drives to Blogger)                                   ║
║                                                                       ║
║   KEY PRINCIPLES:                                                     ║
║   ━━━━━━━━━━━━━━                                                      ║
║   1. Telegram = Central Hub (links to everything)                     ║
║   2. Facebook = Social proof → drives to Blogger                      ║
║   3. Blogger = Arabic home (comprehensive content)                    ║
║   4. Dev.to = English authority (tech credibility)                    ║
║   5. Each platform mentions others strategically                      ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
"""

    @staticmethod
    def get_growth_tips() -> List[str]:
        """Get actionable growth tips."""

        return [
            "🎯 Telegram: Pin a welcome message with links to all platforms",
            "📊 Track which platform drives most traffic using UTM parameters",
            "🔄 Cross-post teasers at different times for maximum reach",
            "💬 Engage with comments on all platforms within 1 hour",
            "📱 Use Instagram Stories to drive to Telegram (future expansion)",
            "🎬 Create short video summaries for TikTok/Reels (future expansion)",
            "📧 Build email list from Blogger for direct communication",
            "🏷️ Use consistent hashtags across all platforms",
            "📅 Create a content calendar for coordinated posting",
            "🤝 Collaborate with other Arabic tech content creators",
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TESTING
# ═══════════════════════════════════════════════════════════════════════════════


def demo():
    """Demonstrate the CTA strategy system."""

    print("=" * 60)
    print("🎯 CTA STRATEGY ENGINE DEMO")
    print("=" * 60)

    cta = CTAStrategy()
    advisor = ContentStrategyAdvisor()

    # Generate sample CTAs
    print("\n📝 BLOGGER CTA (Arabic):")
    print("-" * 40)
    blogger_cta = cta.get_blogger_cta(devto_url="https://dev.to/robovai/sample-article")
    print(blogger_cta[:500] + "...")

    print("\n💻 DEV.TO CTA (English):")
    print("-" * 40)
    devto_cta = cta.get_devto_cta(blogger_url="https://robovai.blogspot.com/article")
    print(devto_cta)

    print("\n📘 FACEBOOK POST:")
    print("-" * 40)
    fb_post = cta.get_facebook_post(
        title="كيف تجعل الذكاء الاصطناعي يكتب بأسلوب أنيق",
        hook="اكتشف أسرار الكتابة الإبداعية مع AI في هذا المقال الشامل",
        blogger_url="https://robovai.blogspot.com/article",
    )
    print(fb_post)

    print("\n📱 TELEGRAM MESSAGE:")
    print("-" * 40)
    tg_msg = cta.get_telegram_message(
        title="كيف تجعل الذكاء الاصطناعي يكتب بأسلوب أنيق",
        summary="في هذا المقال نستكشف كيف يمكن تحسين مخرجات نماذج اللغة",
        blogger_url="https://robovai.blogspot.com/article",
        devto_url="https://dev.to/robovai/article",
        key_points_ar=["تقنيات البرومبت", "أساليب التحسين", "أمثلة عملية"],
    )
    print(tg_msg)

    print("\n📊 PLATFORM STRATEGY:")
    print("-" * 40)
    print(advisor.get_traffic_flow_strategy())

    print("\n💡 GROWTH TIPS:")
    print("-" * 40)
    for tip in advisor.get_growth_tips():
        print(tip)


if __name__ == "__main__":
    demo()
