"""
Unified Bot Runner - Combines main_bot.py + telegram_chatbot.py
Runs both bots in parallel with a simple health endpoint for Render
"""

import asyncio
import logging
import os
from threading import Thread
from aiohttp import web

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_main_bot():
    """Run the content publishing bot (main_bot.py)"""
    try:
        from main_bot import ContentOrbitBot

        logger.info("🤖 Starting Content Publishing Bot...")
        bot = ContentOrbitBot()
        await bot.start()
    except Exception as e:
        logger.error(f"❌ Content bot error: {e}")


async def run_chatbot():
    """Run the interactive Telegram chatbot (telegram_chatbot.py)"""
    try:
        from telegram_chatbot import start_chatbot

        logger.info("💬 Starting Interactive Chatbot...")
        await start_chatbot()
    except Exception as e:
        logger.error(f"❌ Chatbot error: {e}")


async def health_handler(request):
    """Simple health check for Render to keep the service alive"""
    return web.Response(text="OK", status=200)


async def run_health_server():
    """Run a simple HTTP server for health checks"""
    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/", health_handler)

    port = int(os.getenv("PORT", 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)

    logger.info(f"🏥 Health server running on port {port}")
    await site.start()

    # Keep running
    await asyncio.Event().wait()


async def main():
    """Run all services in parallel"""
    logger.info("🚀 Starting Unified Bot Service...")

    # Telegram polling commonly conflicts during deploys/scaling. Posting to channels
    # does NOT require polling, so keep chatbot optional.
    chatbot_enabled = os.getenv("ENABLE_TELEGRAM_CHATBOT", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    # Run all tasks concurrently
    tasks = [
        run_health_server(),
        run_main_bot(),
    ]

    if chatbot_enabled:
        tasks.append(run_chatbot())
    else:
        logger.info(
            "💤 Telegram chatbot polling disabled (set ENABLE_TELEGRAM_CHATBOT=1 to enable)."
        )

    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
