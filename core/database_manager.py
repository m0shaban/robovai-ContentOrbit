"""
ContentOrbit Enterprise - Database Manager
==========================================
SQLite-based persistence layer for:
- Published posts tracking (avoid duplicates)
- Execution logs (for dashboard)
- Content queue management
- System statistics

Usage:
    from core.database_manager import DatabaseManager, get_db

    db = get_db()

    # Check if URL was already posted
    if not db.is_url_posted(url):
        # Process and post
        db.record_posted_url(url, platform="telegram")

    # Log execution
    db.log_event("info", "publisher", "Post published successfully")

    # Get stats
    stats = db.get_stats()
"""

import sqlite3
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from contextlib import contextmanager
import threading
import logging

from .models import (
    PublishedPost,
    SystemLog,
    LogLevel,
    PostStatus,
    Platform,
    SystemStats,
    FetchedArticle,
    ContentQueueItem,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database Manager - The Memory of ContentOrbit

    Uses SQLite for lightweight, file-based persistence.
    Thread-safe with connection pooling.
    """

    DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "contentorbit.db"

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize DatabaseManager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path) if db_path else self.DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread-local storage for connections
        self._local = threading.local()

        # Initialize schema
        self._init_schema()

        logger.info(f"✅ Database initialized at {self.db_path}")

    # ═══════════════════════════════════════════════════════════════════════════
    # CONNECTION MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path), check_same_thread=False, timeout=30.0
            )
            self._local.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection

    @contextmanager
    def _get_cursor(self):
        """Context manager for database cursor with auto-commit"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cursor.close()

    def close(self):
        """Close database connection"""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

    # ═══════════════════════════════════════════════════════════════════════════
    # SCHEMA INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════════════

    def _init_schema(self):
        """Initialize database schema"""
        with self._get_cursor() as cursor:
            # Posted URLs table (for duplicate detection)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS posted_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_hash TEXT UNIQUE NOT NULL,
                    original_url TEXT NOT NULL,
                    title TEXT,
                    source_feed_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Published posts table (full tracking)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS published_posts (
                    id TEXT PRIMARY KEY,
                    source_article_id TEXT,
                    original_url TEXT NOT NULL,
                    title_ar TEXT,
                    title_en TEXT,
                    content_ar TEXT,
                    content_en TEXT,
                    blogger_url TEXT,
                    devto_url TEXT,
                    telegram_message_id INTEGER,
                    facebook_post_id TEXT,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    published_at TIMESTAMP,
                    processing_time_seconds REAL,
                    retry_count INTEGER DEFAULT 0
                )
            """
            )

            # System logs table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    component TEXT NOT NULL,
                    action TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    error_traceback TEXT
                )
            """
            )

            # Content queue table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS content_queue (
                    id TEXT PRIMARY KEY,
                    article_data TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scheduled_for TIMESTAMP,
                    attempts INTEGER DEFAULT 0,
                    max_attempts INTEGER DEFAULT 3
                )
            """
            )

            # System state table (for tracking bot status)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS system_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes for performance
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_posted_urls_hash ON posted_urls(url_hash)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_posts_status ON published_posts(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_queue_status ON content_queue(status)"
            )

            # Telegram chatbot: per-user quota
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_quotas (
                    user_id INTEGER NOT NULL,
                    quota_date TEXT NOT NULL,
                    questions_used INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (user_id, quota_date)
                )
            """
            )

            # Telegram chatbot: bot settings (simple key/value)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Telegram chatbot: per-group settings
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS group_settings (
                    chat_id INTEGER PRIMARY KEY,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    auto_reply INTEGER NOT NULL DEFAULT 0,
                    cta_enabled INTEGER NOT NULL DEFAULT 1,
                    language TEXT DEFAULT 'ar',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

    # ═══════════════════════════════════════════════════════════════════════════
    # DUPLICATE DETECTION
    # ═══════════════════════════════════════════════════════════════════════════

    def _hash_url(self, url: str) -> str:
        """Generate hash for URL (for efficient duplicate checking)"""
        # Normalize URL before hashing
        normalized = url.lower().strip().rstrip("/")
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    def is_url_posted(self, url: str) -> bool:
        """
        Check if URL was already posted

        Args:
            url: The source URL to check

        Returns:
            True if already posted
        """
        url_hash = self._hash_url(url)
        with self._get_cursor() as cursor:
            cursor.execute("SELECT 1 FROM posted_urls WHERE url_hash = ?", (url_hash,))
            return cursor.fetchone() is not None

    def record_posted_url(
        self,
        url: str,
        title: Optional[str] = None,
        source_feed_id: Optional[str] = None,
    ) -> bool:
        """
        Record a URL as posted (for duplicate prevention)

        Args:
            url: The source URL
            title: Article title (optional)
            source_feed_id: Source feed ID (optional)

        Returns:
            True if recorded successfully
        """
        try:
            url_hash = self._hash_url(url)
            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO posted_urls (url_hash, original_url, title, source_feed_id)
                    VALUES (?, ?, ?, ?)
                """,
                    (url_hash, url, title, source_feed_id),
                )
            return True
        except Exception as e:
            logger.error(f"Error recording posted URL: {e}")
            return False

    def get_posted_urls_count(self, days: int = 0) -> int:
        """Get count of posted URLs, optionally filtered by days"""
        with self._get_cursor() as cursor:
            if days > 0:
                since = datetime.utcnow() - timedelta(days=days)
                cursor.execute(
                    "SELECT COUNT(*) FROM posted_urls WHERE created_at >= ?", (since,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM posted_urls")
            return cursor.fetchone()[0]

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLISHED POSTS MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def create_post(self, post: PublishedPost) -> Optional[str]:
        """
        Create a new published post record

        Args:
            post: PublishedPost object

        Returns:
            Post ID if created successfully
        """
        try:
            # Generate ID if not provided
            if not post.id:
                post.id = f"post_{int(datetime.utcnow().timestamp() * 1000)}"

            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO published_posts (
                        id, source_article_id, original_url, title_ar, title_en,
                        content_ar, content_en, blogger_url, devto_url,
                        telegram_message_id, facebook_post_id, status,
                        error_message, created_at, published_at,
                        processing_time_seconds, retry_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        post.id,
                        post.source_article_id,
                        post.original_url,
                        post.title_ar,
                        post.title_en,
                        post.content_ar,
                        post.content_en,
                        post.blogger_url,
                        post.devto_url,
                        post.telegram_message_id,
                        post.facebook_post_id,
                        post.status.value,
                        post.error_message,
                        post.created_at,
                        post.published_at,
                        post.processing_time_seconds,
                        post.retry_count,
                    ),
                )

            # Also record URL to prevent duplicates
            self.record_posted_url(post.original_url, post.title_ar or post.title_en)

            return post.id
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            return None

    def update_post(self, post_id: str, **kwargs) -> bool:
        """Update a published post"""
        try:
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    set_clauses.append(f"{key} = ?")
                    # Handle enums
                    if isinstance(value, (PostStatus, Platform)):
                        value = value.value
                    values.append(value)

            if not set_clauses:
                return False

            values.append(post_id)
            query = f"UPDATE published_posts SET {', '.join(set_clauses)} WHERE id = ?"

            with self._get_cursor() as cursor:
                cursor.execute(query, values)
            return True
        except Exception as e:
            logger.error(f"Error updating post: {e}")
            return False

    def get_post(self, post_id: str) -> Optional[PublishedPost]:
        """Get a post by ID"""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT * FROM published_posts WHERE id = ?", (post_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_post(row)
        return None

    def get_recent_posts(
        self, limit: int = 50, status: Optional[PostStatus] = None
    ) -> List[PublishedPost]:
        """Get recent posts, optionally filtered by status"""
        with self._get_cursor() as cursor:
            if status:
                cursor.execute(
                    """
                    SELECT * FROM published_posts 
                    WHERE status = ? 
                    ORDER BY created_at DESC LIMIT ?
                """,
                    (status.value, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM published_posts 
                    ORDER BY created_at DESC LIMIT ?
                """,
                    (limit,),
                )
            return [self._row_to_post(row) for row in cursor.fetchall()]

    def _row_to_post(self, row: sqlite3.Row) -> PublishedPost:
        """Convert database row to PublishedPost object"""
        return PublishedPost(
            id=row["id"],
            source_article_id=row["source_article_id"],
            original_url=row["original_url"],
            title_ar=row["title_ar"],
            title_en=row["title_en"],
            content_ar=row["content_ar"],
            content_en=row["content_en"],
            blogger_url=row["blogger_url"],
            devto_url=row["devto_url"],
            telegram_message_id=row["telegram_message_id"],
            facebook_post_id=row["facebook_post_id"],
            status=PostStatus(row["status"]) if row["status"] else PostStatus.PENDING,
            error_message=row["error_message"],
            created_at=row["created_at"],
            published_at=row["published_at"],
            processing_time_seconds=row["processing_time_seconds"],
            retry_count=row["retry_count"],
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # LOGGING SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════

    def log_event(
        self,
        level: str | LogLevel,
        component: str,
        action: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_traceback: Optional[str] = None,
    ) -> bool:
        """
        Log a system event

        Args:
            level: Log level (info, warning, error, etc.)
            component: Component name (fetcher, publisher, ai_engine)
            action: Action being performed
            message: Log message
            details: Additional details (JSON serialized)
            error_traceback: Error traceback if applicable

        Returns:
            True if logged successfully
        """
        try:
            if isinstance(level, LogLevel):
                level = level.value

            details_json = json.dumps(details, ensure_ascii=False) if details else None

            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO system_logs (level, component, action, message, details, error_traceback)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (level, component, action, message, details_json, error_traceback),
                )
            return True
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return False

    def log_info(self, component: str, action: str, message: str, **details):
        """Shorthand for info log"""
        return self.log_event(
            "info", component, action, message, details if details else None
        )

    def log_warning(self, component: str, action: str, message: str, **details):
        """Shorthand for warning log"""
        return self.log_event(
            "warning", component, action, message, details if details else None
        )

    def log_error(
        self,
        component: str,
        action: str,
        message: str,
        error: Optional[Exception] = None,
        **details,
    ):
        """Shorthand for error log"""
        traceback_str = str(error) if error else None
        return self.log_event(
            "error",
            component,
            action,
            message,
            details if details else None,
            traceback_str,
        )

    def get_logs(
        self,
        limit: int = 100,
        level: Optional[str] = None,
        component: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[SystemLog]:
        """Get system logs with optional filters"""
        query = "SELECT * FROM system_logs WHERE 1=1"
        params = []

        if level:
            query += " AND level = ?"
            params.append(level)

        if component:
            query += " AND component = ?"
            params.append(component)

        if since:
            query += " AND timestamp >= ?"
            params.append(since)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self._get_cursor() as cursor:
            cursor.execute(query, params)
            logs = []
            for row in cursor.fetchall():
                details = json.loads(row["details"]) if row["details"] else None
                logs.append(
                    SystemLog(
                        id=str(row["id"]),
                        timestamp=row["timestamp"],
                        level=LogLevel(row["level"]),
                        component=row["component"],
                        action=row["action"],
                        message=row["message"],
                        details=details,
                        error_traceback=row["error_traceback"],
                    )
                )
            return logs

    # ═══════════════════════════════════════════════════════════════════════════
    # TELEGRAM CHATBOT SUPPORT
    # ═══════════════════════════════════════════════════════════════════════════

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a simple bot setting from DB."""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_setting(self, key: str, value: str) -> bool:
        """Set a simple bot setting in DB."""
        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO bot_settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                    """,
                    (key, value),
                )
            return True
        except Exception as e:
            logger.error(f"Error setting bot setting {key}: {e}")
            return False

    def get_group_settings(self, chat_id: int) -> Dict[str, Any]:
        """Get group settings; creates defaults if missing."""
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT * FROM group_settings WHERE chat_id = ?", (chat_id,)
            )
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    "INSERT OR IGNORE INTO group_settings (chat_id) VALUES (?)",
                    (chat_id,),
                )
                cursor.execute(
                    "SELECT * FROM group_settings WHERE chat_id = ?", (chat_id,)
                )
                row = cursor.fetchone()

            return {
                "chat_id": row["chat_id"],
                "enabled": bool(row["enabled"]),
                "auto_reply": bool(row["auto_reply"]),
                "cta_enabled": bool(row["cta_enabled"]),
                "language": row["language"] or "ar",
            }

    def update_group_settings(
        self,
        chat_id: int,
        enabled: Optional[bool] = None,
        auto_reply: Optional[bool] = None,
        cta_enabled: Optional[bool] = None,
        language: Optional[str] = None,
    ) -> bool:
        """Update group settings."""
        fields = {}
        if enabled is not None:
            fields["enabled"] = 1 if enabled else 0
        if auto_reply is not None:
            fields["auto_reply"] = 1 if auto_reply else 0
        if cta_enabled is not None:
            fields["cta_enabled"] = 1 if cta_enabled else 0
        if language is not None:
            fields["language"] = language

        if not fields:
            return True

        set_clause = ", ".join([f"{k} = ?" for k in fields.keys()])
        values = list(fields.values()) + [chat_id]

        try:
            with self._get_cursor() as cursor:
                cursor.execute(
                    "INSERT OR IGNORE INTO group_settings (chat_id) VALUES (?)",
                    (chat_id,),
                )
                cursor.execute(
                    f"UPDATE group_settings SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?",
                    values,
                )
            return True
        except Exception as e:
            logger.error(f"Error updating group settings: {e}")
            return False

    def get_daily_questions_used(self, user_id: int, quota_date: str) -> int:
        with self._get_cursor() as cursor:
            cursor.execute(
                "SELECT questions_used FROM user_quotas WHERE user_id = ? AND quota_date = ?",
                (user_id, quota_date),
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0

    def increment_daily_questions(
        self, user_id: int, quota_date: str, inc: int = 1
    ) -> int:
        """Increment daily question counter and return new value."""
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO user_quotas (user_id, quota_date, questions_used)
                VALUES (?, ?, 0)
                ON CONFLICT(user_id, quota_date) DO NOTHING
                """,
                (user_id, quota_date),
            )
            cursor.execute(
                "UPDATE user_quotas SET questions_used = questions_used + ? WHERE user_id = ? AND quota_date = ?",
                (inc, user_id, quota_date),
            )
            cursor.execute(
                "SELECT questions_used FROM user_quotas WHERE user_id = ? AND quota_date = ?",
                (user_id, quota_date),
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0
        cutoff = datetime.utcnow() - timedelta(days=days)
        with self._get_cursor() as cursor:
            cursor.execute("DELETE FROM system_logs WHERE timestamp < ?", (cutoff,))
            return cursor.rowcount

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTENT QUEUE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def add_to_queue(self, item: ContentQueueItem) -> Optional[str]:
        """Add item to content processing queue"""
        try:
            if not item.id:
                item.id = f"queue_{int(datetime.utcnow().timestamp() * 1000)}"

            article_json = item.article.model_dump_json()

            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO content_queue (
                        id, article_data, priority, status, created_at,
                        scheduled_for, attempts, max_attempts
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        item.id,
                        article_json,
                        item.priority,
                        item.status.value,
                        item.created_at,
                        item.scheduled_for,
                        item.attempts,
                        item.max_attempts,
                    ),
                )
            return item.id
        except Exception as e:
            logger.error(f"Error adding to queue: {e}")
            return None

    def get_next_queue_item(self) -> Optional[ContentQueueItem]:
        """Get next pending item from queue (by priority)"""
        with self._get_cursor() as cursor:
            cursor.execute(
                """
                SELECT * FROM content_queue 
                WHERE status = 'pending' AND (scheduled_for IS NULL OR scheduled_for <= ?)
                ORDER BY priority DESC, created_at ASC 
                LIMIT 1
            """,
                (datetime.utcnow(),),
            )
            row = cursor.fetchone()
            if row:
                article = FetchedArticle.model_validate_json(row["article_data"])
                return ContentQueueItem(
                    id=row["id"],
                    article=article,
                    priority=row["priority"],
                    status=PostStatus(row["status"]),
                    created_at=row["created_at"],
                    scheduled_for=row["scheduled_for"],
                    attempts=row["attempts"],
                    max_attempts=row["max_attempts"],
                )
        return None

    def update_queue_item(
        self, item_id: str, status: PostStatus, attempts: Optional[int] = None
    ) -> bool:
        """Update queue item status"""
        try:
            with self._get_cursor() as cursor:
                if attempts is not None:
                    cursor.execute(
                        "UPDATE content_queue SET status = ?, attempts = ? WHERE id = ?",
                        (status.value, attempts, item_id),
                    )
                else:
                    cursor.execute(
                        "UPDATE content_queue SET status = ? WHERE id = ?",
                        (status.value, item_id),
                    )
            return True
        except Exception as e:
            logger.error(f"Error updating queue item: {e}")
            return False

    def remove_from_queue(self, item_id: str) -> bool:
        """Remove item from queue"""
        try:
            with self._get_cursor() as cursor:
                cursor.execute("DELETE FROM content_queue WHERE id = ?", (item_id,))
            return True
        except Exception as e:
            logger.error(f"Error removing from queue: {e}")
            return False

    def get_queue_size(self, status: Optional[PostStatus] = None) -> int:
        """Get queue size, optionally filtered by status"""
        with self._get_cursor() as cursor:
            if status:
                cursor.execute(
                    "SELECT COUNT(*) FROM content_queue WHERE status = ?",
                    (status.value,),
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM content_queue")
            return cursor.fetchone()[0]

    # ═══════════════════════════════════════════════════════════════════════════
    # SYSTEM STATE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def set_state(self, key: str, value: Any) -> bool:
        """Set a system state value"""
        try:
            value_json = json.dumps(value, ensure_ascii=False, default=str)
            with self._get_cursor() as cursor:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO system_state (key, value, updated_at)
                    VALUES (?, ?, ?)
                """,
                    (key, value_json, datetime.utcnow()),
                )
            return True
        except Exception as e:
            logger.error(f"Error setting state: {e}")
            return False

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a system state value"""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT value FROM system_state WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return json.loads(row["value"])
        return default

    def is_bot_running(self) -> bool:
        """Check if bot is marked as running"""
        return self.get_state("bot_running", False)

    def set_bot_running(self, running: bool):
        """Set bot running state"""
        self.set_state("bot_running", running)
        if running:
            self.set_state("bot_started_at", datetime.utcnow().isoformat())
        else:
            self.set_state("bot_stopped_at", datetime.utcnow().isoformat())

    # ═══════════════════════════════════════════════════════════════════════════
    # STATISTICS
    # ═══════════════════════════════════════════════════════════════════════════

    def get_stats(self) -> SystemStats:
        """Get comprehensive system statistics for dashboard"""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        with self._get_cursor() as cursor:
            # Posts counts
            cursor.execute(
                "SELECT COUNT(*) FROM published_posts WHERE status = 'published' AND created_at >= ?",
                (today_start,),
            )
            posts_today = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM published_posts WHERE status = 'published' AND created_at >= ?",
                (week_start,),
            )
            posts_week = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM published_posts WHERE status = 'published' AND created_at >= ?",
                (month_start,),
            )
            posts_month = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM published_posts WHERE status = 'published'"
            )
            total_posts = cursor.fetchone()[0]

            # Error counts
            cursor.execute(
                "SELECT COUNT(*) FROM system_logs WHERE level = 'error' AND timestamp >= ?",
                (today_start,),
            )
            errors_today = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM system_logs WHERE level = 'error' AND timestamp >= ?",
                (week_start,),
            )
            errors_week = cursor.fetchone()[0]

            # Queue size
            cursor.execute(
                "SELECT COUNT(*) FROM content_queue WHERE status = 'pending'"
            )
            queue_size = cursor.fetchone()[0]

            # Last post time
            cursor.execute(
                "SELECT MAX(published_at) FROM published_posts WHERE status = 'published'"
            )
            last_post = cursor.fetchone()[0]

            # Last error time
            cursor.execute(
                "SELECT MAX(timestamp) FROM system_logs WHERE level = 'error'"
            )
            last_error = cursor.fetchone()[0]

        # Calculate uptime
        started_at = self.get_state("bot_started_at")
        uptime_hours = 0
        if started_at and self.is_bot_running():
            start_time = datetime.fromisoformat(started_at)
            uptime_hours = (now - start_time).total_seconds() / 3600

        return SystemStats(
            posts_today=posts_today,
            posts_this_week=posts_week,
            posts_this_month=posts_month,
            total_posts=total_posts,
            errors_today=errors_today,
            errors_this_week=errors_week,
            queue_size=queue_size,
            active_feeds=0,  # Will be filled from ConfigManager
            last_post_time=last_post,
            last_error_time=last_error,
            system_uptime_hours=round(uptime_hours, 2),
            is_running=self.is_bot_running(),
        )

    # ═══════════════════════════════════════════════════════════════════════════
    # MAINTENANCE
    # ═══════════════════════════════════════════════════════════════════════════

    def vacuum(self):
        """Optimize database file size"""
        conn = self._get_connection()
        conn.execute("VACUUM")
        logger.info("Database vacuumed")

    def backup(self, backup_path: Path) -> bool:
        """Create database backup"""
        try:
            import shutil

            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    def get_db_size_mb(self) -> float:
        """Get database file size in MB"""
        if self.db_path.exists():
            return self.db_path.stat().st_size / (1024 * 1024)
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_db_instance: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Get global DatabaseManager instance (singleton)"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance


def close_db():
    """Close global database connection"""
    global _db_instance
    if _db_instance:
        _db_instance.close()
        _db_instance = None
