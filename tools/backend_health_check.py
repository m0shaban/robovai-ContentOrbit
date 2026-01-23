
import sys
import os
import logging
from pathlib import Path
import json

# Setup constraints
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("HealthCheck")

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_manager import ConfigManager
from core.database_manager import DatabaseManager
from core.google_sheets_manager import GoogleSheetsManager

def check_structure():
    logger.info("📂 Checking Directory Structure...")
    required_dirs = ["data", "logs", "output", "core", "dashboard"]
    all_ok = True
    for d in required_dirs:
        if not os.path.isdir(d):
            logger.error(f"❌ Missing directory: {d}")
            all_ok = False
        else:
            logger.info(f"✅ Found: {d}")
    return all_ok

def check_config():
    logger.info("⚙️ Checking Configuration...")
    try:
        cm = ConfigManager()
        cm.load()
        logger.info(f"✅ Config Loaded. Brand: {cm.app_config.brand_name}")
        
        # Check specific critical keys
        if not cm.app_config.telegram.bot_token:
            logger.warning("⚠️ Telegram Bot Token is missing in config.")
        
        return cm
    except Exception as e:
        logger.error(f"❌ Config Load Failed: {e}")
        return None

def check_sheets(cm):
    logger.info("📊 Checking Google Sheets Control Room...")
    try:
        gsm = GoogleSheetsManager(sheet_id=cm.app_config.google_sheet_id, sheet_name=cm.app_config.google_sheet_name)
        if gsm.is_connected():
            logger.info(f"✅ Connected to Sheet: {gsm.sheet.title}")
            
            # Check Tabs
            worksheets = [ws.title for ws in gsm.sheet.worksheets()]
            logger.info(f"   Tabs found: {worksheets}")
            
            required_tabs = ["Configuration", "Feeds", "Logs"]
            missing = [t for t in required_tabs if t not in worksheets]
            if missing:
                logger.warning(f"⚠️ Missing recommended tabs: {missing}")
            else:
                logger.info("✅ All Control Room tabs present.")
            return True
        else:
            logger.warning("⚠️ Google Sheets Not Connected (Check credentials or sheet share).")
            return False
    except Exception as e:
        logger.error(f"❌ Sheets Check Failed: {e}")
        return False

def check_database():
    logger.info("💾 Checking Database...")
    try:
        db = DatabaseManager()
        logger.info(f"✅ Database Initialized at {db.db_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Database Check Failed: {e}")
        return False

def main():
    print("\n" + "="*50)
    print(" 🚀 ContentOrbit Backend System Diagnostic")
    print("="*50 + "\n")
    
    if not check_structure():
        print("\n❌ Critical: Directory structure issues.")
        return

    cm = check_config()
    if not cm:
        print("\n❌ Critical: Config load failed.")
        return

    check_database()
    check_sheets(cm)
    
    print("\n" + "="*50)
    print(" ✅ Diagnostic Complete")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
