"""
ContentOrbit Enterprise - Telegram Publisher
=============================================
Publishes posts to Telegram channels using aiogram.

Setup Requirements:
1. Create bot via @BotFather
2. Get bot token
3. Add bot as admin to your channel
4. Get channel ID (username or numeric)

Usage:
    from core.publisher import TelegramPublisher

    publisher = TelegramPublisher(config)
    message_id = await publisher.publish_post(text, image_url)
"""

import asyncio
from typing import Optional, List, Union
from pathlib import Path
import logging
import io

import httpx
from aiogram import Bot
from aiogram.types import FSInputFile, URLInputFile, BufferedInputFile
from aiogram.enums import ParseMode
from tenacity import retry, stop_after_attempt, wait_exponential

from core.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class TelegramPublisher:
    """
    Telegram Channel Publisher

    Publishes formatted posts with images to Telegram channels.
    Uses aiogram for async Telegram Bot API access.
    """

    def __init__(self, config: ConfigManager):
        """
        Initialize Telegram Publisher

        Args:
            config: ConfigManager instance
        """
        self.config = config
        self._bot: Optional[Bot] = None

    def _get_bot(self) -> Bot:
        """Get or create bot instance"""
        if self._bot is None:
            self._bot = Bot(token=self.config.app_config.telegram.bot_token)
        return self._bot

    async def close(self):
        """Close bot session"""
        if self._bot:
            await self._bot.session.close()
            self._bot = None

    @property
    def telegram_config(self):
        """Get Telegram configuration"""
        return self.config.app_config.telegram

    @property
    def channel_id(self) -> str:
        """Get channel ID"""
        return self.telegram_config.channel_id

    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return self.config.is_configured("telegram")

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLISHING
    # ═══════════════════════════════════════════════════════════════════════════

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    async def publish_text(
        self,
        text: str,
        parse_mode: ParseMode = ParseMode.HTML,
        disable_preview: bool = False,
        disable_notification: bool = False,
    ) -> Optional[int]:
        """
        Publish text message to channel

        Args:
            text: Message text (supports HTML/Markdown)
            parse_mode: Parse mode (HTML or Markdown)
            disable_preview: Disable link previews
            disable_notification: Send silently

        Returns:
            Message ID if successful, None otherwise
        """
        if not self.is_configured():
            logger.error("Telegram not configured")
            return None

        bot = self._get_bot()

        try:
            # Ensure text is within limits (4096 chars)
            if len(text) > 4096:
                text = text[:4090] + "..."

            message = await bot.send_message(
                chat_id=self.channel_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_preview,
                disable_notification=disable_notification,
            )

            logger.info(f"✅ Published to Telegram: message_id={message.message_id}")
            return message.message_id

        except Exception as e:
            logger.error(f"Telegram publish failed: {e}")
            return None

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    async def publish_photo(
        self,
        text: str,
        photo: Union[str, Path, bytes],
        parse_mode: ParseMode = ParseMode.HTML,
        disable_notification: bool = False,
    ) -> Optional[int]:
        """
        Publish photo with caption to channel

        Args:
            text: Caption text (max 1024 chars)
            photo: Photo URL, file path, or bytes
            parse_mode: Parse mode for caption
            disable_notification: Send silently

        Returns:
            Message ID if successful, None otherwise
        """
        if not self.is_configured():
            logger.error("Telegram not configured")
            return None

        bot = self._get_bot()

        try:
            # Ensure caption is within limits (1024 chars)
            if len(text) > 1024:
                text = text[:1020] + "..."

            # Prepare photo input
            if isinstance(photo, str):
                if photo.startswith(("http://", "https://")):
                    # More reliable than URLInputFile (Telegram fetching remote URLs can fail).
                    try:
                        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                            r = await client.get(photo, headers={"User-Agent": "Mozilla/5.0"})
                            r.raise_for_status()
                            content_type = (r.headers.get("content-type") or "").lower()
                            if "image" not in content_type:
                                raise ValueError(f"Non-image content-type: {content_type}")
                            photo_input = BufferedInputFile(r.content, filename="image.jpg")
                    except Exception:
                        photo_input = URLInputFile(photo)
                else:
                    photo_input = FSInputFile(photo)
            elif isinstance(photo, Path):
                photo_input = FSInputFile(str(photo))
            elif isinstance(photo, bytes):
                photo_input = BufferedInputFile(photo, filename="image.jpg")
            else:
                raise ValueError(f"Invalid photo type: {type(photo)}")

            message = await bot.send_photo(
                chat_id=self.channel_id,
                photo=photo_input,
                caption=text,
                parse_mode=parse_mode,
                disable_notification=disable_notification,
            )

            logger.info(
                f"✅ Published photo to Telegram: message_id={message.message_id}"
            )
            return message.message_id

        except Exception as e:
            logger.error(f"Telegram photo publish failed: {e}")
            # Fallback to text only
            logger.info("Falling back to text-only post")
            return await self.publish_text(
                text, parse_mode, disable_notification=disable_notification
            )

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    async def publish_document(
        self,
        caption: str,
        document: Union[str, Path, bytes],
        filename: str = "document",
        parse_mode: ParseMode = ParseMode.HTML,
    ) -> Optional[int]:
        """
        Publish document to channel

        Args:
            caption: Document caption
            document: Document URL, path, or bytes
            filename: Filename for bytes input
            parse_mode: Parse mode for caption

        Returns:
            Message ID if successful
        """
        if not self.is_configured():
            return None

        bot = self._get_bot()

        try:
            if isinstance(document, str):
                if document.startswith(("http://", "https://")):
                    doc_input = URLInputFile(document)
                else:
                    doc_input = FSInputFile(document)
            elif isinstance(document, Path):
                doc_input = FSInputFile(str(document))
            elif isinstance(document, bytes):
                doc_input = BufferedInputFile(document, filename=filename)
            else:
                raise ValueError(f"Invalid document type: {type(document)}")

            message = await bot.send_document(
                chat_id=self.channel_id,
                document=doc_input,
                caption=caption[:1024] if len(caption) > 1024 else caption,
                parse_mode=parse_mode,
            )

            return message.message_id

        except Exception as e:
            logger.error(f"Document publish failed: {e}")
            return None

    # ═══════════════════════════════════════════════════════════════════════════
    # HIGH-LEVEL METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    async def publish_post(
        self,
        text: str,
        image_url: Optional[str] = None,
        parse_mode: ParseMode = ParseMode.HTML,
    ) -> Optional[int]:
        """
        Publish a post (with optional image)

        This is the main method for publishing content.
        Automatically handles image fetching and fallback.

        Args:
            text: Post text/caption
            image_url: Optional image URL
            parse_mode: Parse mode

        Returns:
            Message ID if successful
        """
        if not image_url:
            return await self.publish_text(text, parse_mode)

        # Telegram caption limit is 1024; preserve the full CTA by sending a follow-up.
        if len(text) <= 1024:
            return await self.publish_photo(text, image_url, parse_mode)

        short_caption = text[:900].rstrip() + "\n\n⬇️ <b>التفاصيل والروابط بالأسفل</b>"

        first_id = await self.publish_photo(short_caption, image_url, parse_mode)
        # Send full text as separate message (4096 limit handled in publish_text)
        await self.publish_text(text, parse_mode)
        return first_id

    async def publish_article_announcement(
        self,
        title: str,
        summary: str,
        blogger_url: Optional[str] = None,
        devto_url: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> Optional[int]:
        """
        Publish a formatted article announcement

        Args:
            title: Article title
            summary: Article summary
            blogger_url: Link to Blogger article
            devto_url: Link to Dev.to article
            image_url: Article thumbnail

        Returns:
            Message ID if successful
        """
        # Build formatted message
        message = f"📝 <b>{self._escape_html(title)}</b>\n\n"
        message += f"{self._escape_html(summary)}\n\n"

        if blogger_url:
            message += f'📖 <a href="{blogger_url}">اقرأ المقال كامل</a>\n'

        if devto_url:
            message += f'🇬🇧 <a href="{devto_url}">English Version</a>\n'

        message += f"\n#{self.config.app_config.prompts.brand_name.replace(' ', '_')}"

        return await self.publish_post(message, image_url)

    # ═══════════════════════════════════════════════════════════════════════════
    # CHANNEL MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    async def get_channel_info(self) -> Optional[dict]:
        """
        Get channel information

        Returns:
            Channel info dict or None
        """
        if not self.is_configured():
            return None

        bot = self._get_bot()

        try:
            chat = await bot.get_chat(self.channel_id)

            return {
                "id": chat.id,
                "title": chat.title,
                "username": chat.username,
                "type": chat.type,
                "description": chat.description,
                "member_count": await self._get_member_count(),
            }
        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")
            return None

    async def _get_member_count(self) -> int:
        """Get channel member count"""
        try:
            bot = self._get_bot()
            count = await bot.get_chat_member_count(self.channel_id)
            return count
        except:
            return 0

    async def delete_message(self, message_id: int) -> bool:
        """
        Delete a message from channel

        Args:
            message_id: Message ID to delete

        Returns:
            True if deleted successfully
        """
        if not self.is_configured():
            return False

        bot = self._get_bot()

        try:
            await bot.delete_message(self.channel_id, message_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
            return False

    async def edit_message(
        self, message_id: int, new_text: str, parse_mode: ParseMode = ParseMode.HTML
    ) -> bool:
        """
        Edit a message in channel

        Args:
            message_id: Message ID to edit
            new_text: New message text
            parse_mode: Parse mode

        Returns:
            True if edited successfully
        """
        if not self.is_configured():
            return False

        bot = self._get_bot()

        try:
            await bot.edit_message_text(
                chat_id=self.channel_id,
                message_id=message_id,
                text=new_text,
                parse_mode=parse_mode,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # ADMIN NOTIFICATIONS
    # ═══════════════════════════════════════════════════════════════════════════

    async def notify_admins(self, message: str) -> None:
        """
        Send notification to admin users

        Args:
            message: Notification message
        """
        bot = self._get_bot()

        for admin_id in self.telegram_config.admin_user_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"🔔 <b>ContentOrbit Alert</b>\n\n{message}",
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

    async def send_error_alert(self, error: str, component: str = "system") -> None:
        """
        Send error alert to admins

        Args:
            error: Error message
            component: System component that failed
        """
        message = (
            f"⚠️ <b>Error in {component}</b>\n\n<code>{self._escape_html(error)}</code>"
        )
        await self.notify_admins(message)

    # ═══════════════════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════════════════

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def format_post(
        self,
        title: str,
        body: str,
        links: Optional[dict] = None,
        hashtags: Optional[List[str]] = None,
    ) -> str:
        """
        Format a complete post with standard structure

        Args:
            title: Post title
            body: Post body
            links: Dict of {label: url}
            hashtags: List of hashtags (without #)

        Returns:
            Formatted HTML post
        """
        post = f"<b>{self._escape_html(title)}</b>\n\n"
        post += f"{self._escape_html(body)}\n"

        if links:
            post += "\n"
            for label, url in links.items():
                post += f'🔗 <a href="{url}">{label}</a>\n'

        if hashtags:
            post += "\n" + " ".join(f"#{tag}" for tag in hashtags)

        return post
