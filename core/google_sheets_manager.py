import logging
import gspread
import os
import json
from google.oauth2.service_account import Credentials
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class GoogleSheetsManager:
    """
    Manages interactions with Google Sheets to act as a Control Room.
    Handles:
    1. Reading dynamic configuration (CTAs, Product names).
    2. Reading dynamic Feeds.
    3. Logging published content (Dashboard).
    4. Reading manual content queue.
    """

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    # Standard column names expected in the sheet
    COLS_CONFIG = ["Key", "Value", "Description"]
    COLS_FEEDS = ["Category", "Name", "URL", "Priority", "Active"]
    COLS_LOGS = [
        "Date",
        "Title",
        "Source URL",
        "Blogger Link",
        "Dev.to Link",
        "Facebook Link",
        "Telegram Link",
        "Status",
    ]

    def __init__(
        self,
        key_path: str = "service_account.json",
        sheet_name: str = "ContentOrbit Control Room",
        sheet_id: Optional[str] = None,
    ):
        self.key_path = key_path
        self.sheet_name = sheet_name
        self.sheet_id = sheet_id
        self.client = None
        self.sheet = None
        self._connect_if_possible()

    def _connect_if_possible(self):
        """Attempts to connect to Google Sheets if credentials exist."""
        if not os.path.exists(self.key_path):
            logger.warning(f"⚠️ Google Sheets API skipped: '{self.key_path}' not found.")
            return

        try:
            creds = Credentials.from_service_account_file(
                self.key_path, scopes=self.SCOPES
            )
            self.client = gspread.authorize(creds)
            try:
                if self.sheet_id:
                    self.sheet = self.client.open_by_key(self.sheet_id)
                    logger.info(f"✅ Connected to Google Sheet by ID: {self.sheet_id}")
                else:
                    self.sheet = self.client.open(self.sheet_name)
                    logger.info(
                        f"✅ Connected to Google Sheet by Name: {self.sheet_name}"
                    )
            except gspread.SpreadsheetNotFound:
                logger.error(
                    f"❌ Spreadsheet not found (ID: {self.sheet_id} | Name: {self.sheet_name}). Please share it with the service account."
                )
                self.client = None
        except Exception as e:
            logger.error(f"❌ Google Sheets Connection Error: {str(e)}")
            self.client = None

    def is_connected(self) -> bool:
        return self.client is not None and self.sheet is not None

    def fetch_config(self) -> Dict[str, str]:
        """Reads 'Config' tab and returns key-value pairs."""
        if not self.is_connected():
            return {}

        try:
            worksheet = self.sheet.worksheet("Config")
            records = worksheet.get_all_records()
            # Expected format: [{'Key': 'academy_url', 'Value': '...'}, ...]
            config = {
                item["Key"]: item["Value"]
                for item in records
                if item.get("Key") and item.get("Value")
            }
            logger.info("✅ Synced Config from Google Sheet")
            return config
        except Exception as e:
            logger.error(f"⚠️ Failed to fetch Config from Sheet: {e}")
            return {}

    def fetch_feeds(self) -> List[Dict]:
        """Reads 'Feeds' tab and returns list of feed objects."""
        if not self.is_connected():
            return []

        try:
            worksheet = self.sheet.worksheet("Feeds")
            records = worksheet.get_all_records()
            # Filter active feeds
            active_feeds = [
                {
                    "category": r.get("Category", "General"),
                    "name": r.get("Name", "Unknown"),
                    "url": r.get("URL"),
                    "priority": r.get("Priority", 1),
                }
                for r in records
                if str(r.get("Active", "")).lower() in ["true", "yes", "1", "active"]
            ]
            logger.info(f"✅ Synced {len(active_feeds)} Feeds from Google Sheet")
            return active_feeds
        except Exception as e:
            logger.error(f"⚠️ Failed to fetch Feeds from Sheet: {e}")
            return []

    def log_activity(self, data: Dict[str, Any]):
        """Logs a publishing event to the 'Logs' tab."""
        if not self.is_connected():
            return

        try:
            worksheet = self.sheet.worksheet("Logs")
            row = [
                data.get("timestamp", ""),
                data.get("title", ""),
                data.get("source_url", ""),
                data.get("blogger_link", ""),
                data.get("devto_link", ""),
                data.get("facebook_link", ""),
                data.get("telegram_link", ""),
                data.get("status", "Success"),
            ]
            worksheet.append_row(row)
            logger.info("✅ Logged activity to Google Sheet")
        except Exception as e:
            logger.error(f"⚠️ Failed to log to Sheet: {e}")

    def fetch_queue(self) -> List[Dict]:
        """Reads 'Queue' tab for manual content injection."""
        # Implementation left for future expansion or if requested specifically.
        pass
