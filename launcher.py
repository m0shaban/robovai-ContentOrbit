#!/usr/bin/env python3
"""
Combined launcher for Fly.io deployment
Runs both main_bot.py and telegram_chatbot.py in parallel
"""
import asyncio
import sys
import signal
from multiprocessing import Process
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_main_bot():
    """Run the content pipeline bot"""
    import main_bot
    try:
        asyncio.run(main_bot.main())
    except KeyboardInterrupt:
        logger.info("Main bot stopped")
    except Exception as e:
        logger.error(f"Main bot error: {e}")
        sys.exit(1)

def run_chatbot():
    """Run the interactive Telegram chatbot"""
    import telegram_chatbot
    try:
        asyncio.run(telegram_chatbot.main())
    except KeyboardInterrupt:
        logger.info("Chatbot stopped")
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        sys.exit(1)

def main():
    logger.info("🚀 Starting ContentOrbit Bots...")
    
    # Start both processes
    bot_process = Process(target=run_main_bot, name="MainBot")
    chatbot_process = Process(target=run_chatbot, name="Chatbot")
    
    bot_process.start()
    chatbot_process.start()
    
    logger.info("✅ Both bots started")
    
    def signal_handler(sig, frame):
        logger.info("Shutting down...")
        bot_process.terminate()
        chatbot_process.terminate()
        bot_process.join(timeout=5)
        chatbot_process.join(timeout=5)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Wait for both
    bot_process.join()
    chatbot_process.join()

if __name__ == "__main__":
    main()
