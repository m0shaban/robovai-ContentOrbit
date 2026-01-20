"""
ContentOrbit Enterprise - Main Bot Worker
==========================================
The Background Worker (The Engine) that runs 24/7.
Handles the content pipeline: Fetch -> Generate -> Publish

Usage:
    python main_bot.py

Or with specific config:
    python main_bot.py --config /path/to/config.json
"""

import asyncio
import signal
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from core.config_manager import ConfigManager, get_config
from core.database_manager import DatabaseManager, get_db, close_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            Path(__file__).parent / "data" / "logs" / "bot.log", encoding="utf-8"
        ),
    ],
)
logger = logging.getLogger("ContentOrbit")


class ContentOrbitBot:
    """
    Main Bot Worker Class

    Orchestrates the entire content pipeline:
    1. Fetches content from RSS feeds
    2. Generates articles using AI
    3. Publishes to multiple platforms
    4. Tracks everything in the database
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the bot"""
        self.config = (
            ConfigManager(config_path=config_path) if config_path else get_config()
        )
        self.db = get_db()
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._running = False
        self._shutdown_event = asyncio.Event()

        logger.info("🚀 ContentOrbit Enterprise initialized")

    async def start(self):
        """Start the bot worker"""
        logger.info("=" * 60)
        logger.info("🌟 ContentOrbit Enterprise - Starting Up")
        logger.info("=" * 60)

        # Load configuration
        if not self.config._is_loaded:
            self.config.load()

        # Check if system is ready
        if not self.config.is_ready:
            logger.warning("⚠️ System not fully configured. Check dashboard for setup.")
            status = self.config.get_config_status()
            logger.info(f"Config status: {status}")

        # Initialize scheduler
        schedule = self.config.app_config.schedule
        if not schedule:
            from core.models import ScheduleConfig

            schedule = ScheduleConfig()

        self.scheduler = AsyncIOScheduler(timezone=schedule.timezone)

        # Add the main job
        interval_minutes = schedule.posting_interval_minutes
        self.scheduler.add_job(
            self._execute_pipeline,
            IntervalTrigger(minutes=interval_minutes),
            id="content_pipeline",
            name="Content Pipeline",
            replace_existing=True,
            next_run_time=datetime.now(),  # Run immediately on start
        )

        # Start scheduler
        self.scheduler.start()
        self._running = True
        self.db.set_bot_running(True)

        self.db.log_info(
            component="bot",
            action="start",
            message=f"Bot started with {interval_minutes} minute interval",
            interval=interval_minutes,
        )

        logger.info(f"✅ Bot started! Running every {interval_minutes} minutes")
        logger.info(f"📊 Active feeds: {len(self.config.get_active_feeds())}")

        # Keep running until shutdown
        await self._shutdown_event.wait()

    async def stop(self):
        """Stop the bot worker gracefully"""
        logger.info("🛑 Shutting down ContentOrbit...")

        self._running = False
        self.db.set_bot_running(False)

        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)

        self.db.log_info(
            component="bot", action="stop", message="Bot stopped gracefully"
        )

        close_db()
        self._shutdown_event.set()

        logger.info("✅ Bot stopped successfully")

    async def _execute_pipeline(self):
        """
        Execute the main content pipeline

        This is where the magic happens!
        """
        if not self._running:
            return

        logger.info("=" * 40)
        logger.info("🔄 Starting content pipeline execution")
        logger.info("=" * 40)

        try:
            # Hot-reload config so prompt/CTA edits (via dashboard/Telegram) apply.
            try:
                self.config.reload()
            except Exception:
                pass

            # Check if within active hours
            if not self._is_active_hours():
                logger.info("💤 Outside active hours, skipping...")
                return

            # Check daily limit
            stats = self.db.get_stats()
            schedule = self.config.app_config.schedule
            max_daily = schedule.max_posts_per_day if schedule else 10
            if stats.posts_today >= max_daily:
                logger.info(
                    f"📊 Daily limit reached ({stats.posts_today}/{max_daily}), skipping..."
                )
                return

            # Import and use ContentOrchestrator
            from core.content_orchestrator import ContentOrchestrator

            orchestrator = ContentOrchestrator(self.config, self.db)

            try:
                result = await orchestrator.execute()

                if result.success:
                    logger.info(f"✅ Pipeline completed successfully!")
                    logger.info(
                        f"   Article: {result.article.title[:50] if result.article else 'N/A'}..."
                    )
                    logger.info(f"   Steps: {' -> '.join(result.steps_completed)}")
                else:
                    logger.warning(f"⚠️ Pipeline completed with errors: {result.error}")

                # Notify admins with a compact summary + links
                try:
                    from core.publisher.telegram_publisher import TelegramPublisher

                    tg = TelegramPublisher(self.config)

                    def _esc(s: str) -> str:
                        return (
                            (s or "")
                            .replace("&", "&amp;")
                            .replace("<", "&lt;")
                            .replace(">", "&gt;")
                            .replace('"', "&quot;")
                        )

                    title = _esc(result.article.title) if result.article else "-"
                    steps = " → ".join(result.steps_completed or [])

                    # Best-effort Telegram message link
                    tg_link = None
                    ch = (self.config.app_config.telegram.channel_id or "").strip()
                    if result.telegram_message_id and ch.startswith("@"):
                        tg_link = f"https://t.me/{ch[1:]}/{result.telegram_message_id}"

                    # Best-effort Facebook post link
                    fb_link = None
                    page_id = (
                        (self.config.app_config.facebook.page_id or "").strip()
                        if self.config.app_config.facebook
                        else ""
                    )
                    if result.facebook_post_id and page_id:
                        post_id = str(result.facebook_post_id)
                        post_tail = (
                            post_id.split("_", 1)[-1] if "_" in post_id else post_id
                        )
                        fb_link = (
                            f"https://www.facebook.com/{page_id}/posts/{post_tail}"
                        )

                    if result.success:
                        msg = (
                            "✅ <b>تم النشر بنجاح</b>\n\n"
                            f"📰 <b>{title}</b>\n"
                            f"🧩 <b>Steps:</b> { _esc(steps) }\n\n"
                        )
                        if result.blogger_url:
                            msg += f'• 🇪🇬 <a href="{result.blogger_url}">Blogger</a>\n'
                        if result.devto_url:
                            msg += f'• 🌍 <a href="{result.devto_url}">Dev.to</a>\n'
                        if tg_link:
                            msg += f'• 📣 <a href="{tg_link}">Telegram</a>\n'
                        elif result.telegram_message_id:
                            msg += f"• 📣 Telegram Msg: <code>{result.telegram_message_id}</code>\n"
                        if fb_link:
                            msg += f'• 👍 <a href="{fb_link}">Facebook</a>\n'
                        elif result.facebook_post_id:
                            msg += f"• 👍 Facebook Post: <code>{_esc(str(result.facebook_post_id))}</code>\n"
                    else:
                        err = _esc(result.error or "Unknown error")
                        msg = (
                            "⚠️ <b>النشر خلّص وفيه مشكلة</b>\n\n"
                            f"📰 <b>{title}</b>\n"
                            f"🧩 <b>Steps:</b> { _esc(steps) }\n\n"
                            f"<b>Error:</b> <code>{err}</code>"
                        )

                    await tg.notify_admins(msg)
                    await tg.close()
                except Exception as _e:
                    logger.warning(f"Admin notify failed: {_e}")

            finally:
                await orchestrator.close()

            self.db.log_info(
                component="bot",
                action="pipeline_executed",
                message="Content pipeline executed",
                success=result.success,
                steps=result.steps_completed,
            )

        except Exception as e:
            logger.error(f"❌ Pipeline error: {e}")
            self.db.log_error(
                component="bot", action="pipeline_error", message=str(e), error=e
            )

    def _is_active_hours(self) -> bool:
        """Check if current time is within active hours"""
        from datetime import datetime
        import pytz

        schedule = self.config.app_config.schedule
        if not schedule:
            from core.models import ScheduleConfig

            schedule = ScheduleConfig()

        tz = pytz.timezone(schedule.timezone)
        now = datetime.now(tz)

        start_hour = schedule.active_hours_start
        end_hour = schedule.active_hours_end

        current_hour = now.hour

        if start_hour <= end_hour:
            return start_hour <= current_hour <= end_hour
        else:
            # Handle overnight range (e.g., 22:00 to 06:00)
            return current_hour >= start_hour or current_hour <= end_hour


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="ContentOrbit Enterprise Bot Worker")
    parser.add_argument("--config", type=Path, help="Path to config.json file")
    args = parser.parse_args()

    # Create bot instance
    bot = ContentOrbitBot(config_path=args.config)

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()

    def signal_handler():
        logger.info("Received shutdown signal...")
        asyncio.create_task(bot.stop())

    # Handle Ctrl+C and termination signals
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, signal_handler)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda s, f: asyncio.create_task(bot.stop()))

    # Start the bot
    try:
        await bot.start()
    except KeyboardInterrupt:
        await bot.stop()


if __name__ == "__main__":
    print(
        """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🚀 ContentOrbit Enterprise v1.0.0                       ║
    ║   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ║
    ║   Your Content, Everywhere                                ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    )

    asyncio.run(main())
