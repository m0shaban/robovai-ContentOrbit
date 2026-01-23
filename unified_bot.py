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


def setup_google_credentials():
    """
    Recover service_account.json from environment variables for cloud deployment (Render/Heroku).
    Crucial for security so we don't commit keys to Git.
    """
    import json
    
    creds_path = os.path.join("data", "service_account.json")
    
    # If file exists (local dev), do nothing
    if os.path.exists(creds_path):
        return

    # Check for Env Var
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        logger.info("🔐 Found GOOGLE_CREDENTIALS_JSON in env. Restoring service_account.json...")
        try:
            # Validate JSON
            creds_data = json.loads(creds_json)
            
            # Ensure data dir exists
            os.makedirs("data", exist_ok=True)
            
            # Write to file
            with open(creds_path, "w", encoding="utf-8") as f:
                json.dump(creds_data, f, indent=2)
            
            logger.info("✅ service_account.json restored successfully.")
        except json.JSONDecodeError:
            logger.error("❌ Failed to decode GOOGLE_CREDENTIALS_JSON. Is it valid JSON?")
        except Exception as e:
            logger.error(f"❌ Error restoring credentials: {e}")
    else:
        # Check standard Render Secret File path if Env is missing
        render_secret_path = "/etc/secrets/service_account.json"
        if os.path.exists(render_secret_path):
             logger.info(f"🔐 Found Render Secret File at {render_secret_path}")
             # We can't move it easily if it's read-only, but we can update the code to look there?
             # Actually, simpler to copy it to the expected location if possible, or read from it.
             # Let's try to copy.
             try:
                 with open(render_secret_path, 'r') as secret, open(creds_path, 'w') as dest:
                     dest.write(secret.read())
                 logger.info("✅ Copied Render Secret to data/service_account.json")
                 return
             except Exception as e:
                 logger.error(f"❌ Failed to copy Render Secret: {e}")

        logger.warning("⚠️ No service_account.json found and no GOOGLE_CREDENTIALS_JSON env var (or Secret File) set. Sheets Control Room will be disabled.")


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

    # setup cloud credentials
    setup_google_credentials()

    # Telegram polling commonly conflicts during deploys/scaling. Posting to channels
    # does NOT require polling, so keep chatbot optional.
    chatbot_enabled = os.getenv("ENABLE_TELEGRAM_CHATBOT", "1").strip().lower() in (
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
