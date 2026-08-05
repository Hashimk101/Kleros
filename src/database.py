"""
Database management module for storing, updating, and querying free AI resource offers.
"""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Handles SQLite operations for Kleros offer caching and storage."""

    def __init__(self, db_path: str = "offers.db", auto_cleanup_days: int = 30):
        self.db_path = db_path
        self.init_db()
        if auto_cleanup_days > 0:
            self.cleanup_expired_offers(days_limit=auto_cleanup_days)

    def get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection with Row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initialize the database schema and indexes if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS offers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    offer_type TEXT NOT NULL,
                    value TEXT,
                    description TEXT,
                    geo_restricted BOOLEAN DEFAULT 0,
                    eligible_regions TEXT DEFAULT '["global"]',
                    date_posted DATE,
                    source_type TEXT,
                    source_url TEXT,
                    is_valid BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_type ON offers(offer_type);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_date ON offers(date_posted);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_offers_valid ON offers(is_valid);")
            conn.commit()

    def cleanup_expired_offers(self, days_limit: int = 30) -> int:
        """
        Delete offers that are older than the specified time limit (in days).
        Checks date_posted, created_at, and last_seen.
        Returns count of deleted records.
        """
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days_limit)).strftime("%Y-%m-%d")
        cutoff_timestamp = (datetime.now(timezone.utc) - timedelta(days=days_limit)).strftime("%Y-%m-%d %H:%M:%S")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM offers
                WHERE (date_posted IS NOT NULL AND date_posted < ?)
                   OR (date_posted IS NULL AND created_at < ?)
                   OR last_seen < ?
            """, (cutoff_date, cutoff_timestamp, cutoff_timestamp))
            deleted_count = cursor.rowcount
            conn.commit()
            if deleted_count > 0:
                logger.info(f"Database cleanup removed {deleted_count} offers older than {days_limit} days.")
            return deleted_count

    def is_url_recently_seen(self, url: str, cache_days: int = 7) -> bool:
        """Check if a URL was already processed within the specified cache_days."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cutoff = (datetime.now(timezone.utc) - timedelta(days=cache_days)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "SELECT 1 FROM offers WHERE url = ? AND last_seen >= ?",
                (url, cutoff)
            )
            return cursor.fetchone() is not None

    def save_offer(self, offer: Dict[str, Any]) -> bool:
        """
        Insert a new offer or update last_seen if URL exists.
        Returns True if newly inserted, False if updated/skipped.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        eligible_regions_str = offer.get("eligible_regions")
        if isinstance(eligible_regions_str, (list, tuple)):
            eligible_regions_str = json.dumps(eligible_regions_str)
        elif not eligible_regions_str:
            eligible_regions_str = json.dumps(["global"])

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM offers WHERE url = ?", (offer["url"],))
            existing = cursor.fetchone()

            if existing:
                cursor.execute("""
                    UPDATE offers
                    SET name = ?,
                        offer_type = ?,
                        value = ?,
                        description = ?,
                        geo_restricted = ?,
                        eligible_regions = ?,
                        date_posted = ?,
                        source_type = ?,
                        source_url = ?,
                        is_valid = ?,
                        last_seen = ?
                    WHERE url = ?
                """, (
                    offer.get("name", "Unknown Offer"),
                    offer.get("offer_type", "api"),
                    offer.get("value", "Free Access"),
                    offer.get("description", ""),
                    1 if offer.get("geo_restricted") else 0,
                    eligible_regions_str,
                    offer.get("date_posted"),
                    offer.get("source_type", "blog"),
                    offer.get("source_url", offer["url"]),
                    1 if offer.get("is_valid", True) else 0,
                    now,
                    offer["url"]
                ))
                conn.commit()
                return False
            else:
                cursor.execute("""
                    INSERT INTO offers (
                        name, url, offer_type, value, description,
                        geo_restricted, eligible_regions, date_posted,
                        source_type, source_url, is_valid, created_at, last_seen
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    offer.get("name", "Unknown Offer"),
                    offer["url"],
                    offer.get("offer_type", "api"),
                    offer.get("value", "Free Access"),
                    offer.get("description", ""),
                    1 if offer.get("geo_restricted") else 0,
                    eligible_regions_str,
                    offer.get("date_posted"),
                    offer.get("source_type", "blog"),
                    offer.get("source_url", offer["url"]),
                    1 if offer.get("is_valid", True) else 0,
                    now,
                    now
                ))
                conn.commit()
                return True

    def save_offers(self, offers: List[Dict[str, Any]]) -> int:
        """Bulk save offers. Returns count of newly inserted offers."""
        new_count = 0
        for offer in offers:
            if offer.get("url"):
                if self.save_offer(offer):
                    new_count += 1
        return new_count

    def get_offers(
        self,
        offer_type: Optional[str] = None,
        region: Optional[str] = None,
        is_valid_only: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve offers based on optional type, region, and validity filters."""
        query = "SELECT * FROM offers WHERE 1=1"
        params: List[Any] = []

        if is_valid_only:
            query += " AND is_valid = 1"

        if offer_type and offer_type.lower() != "all":
            query += " AND LOWER(offer_type) = LOWER(?)"
            params.append(offer_type)

        query += " ORDER BY created_at DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        results = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                item = dict(row)
                # Parse JSON array for eligible_regions
                try:
                    item["eligible_regions"] = json.loads(item["eligible_regions"]) if item["eligible_regions"] else ["global"]
                except (json.JSONDecodeError, TypeError):
                    item["eligible_regions"] = ["global"]

                # Apply region filter if provided
                if region and region.lower() != "all":
                    reg_lower = region.lower()
                    regions_lower = [r.lower() for r in item["eligible_regions"]]
                    if reg_lower not in regions_lower and "global" not in regions_lower:
                        continue

                results.append(item)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """Aggregate statistics on stored offers."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM offers WHERE is_valid = 1")
            total_offers = cursor.fetchone()[0]

            cursor.execute("""
                SELECT offer_type, COUNT(*) as cnt
                FROM offers
                WHERE is_valid = 1
                GROUP BY offer_type
            """)
            type_counts = {row["offer_type"]: row["cnt"] for row in cursor.fetchall()}

            today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM offers WHERE DATE(created_at) = ? AND is_valid = 1",
                (today,)
            )
            new_today = cursor.fetchone()[0]

            return {
                "total_offers": total_offers,
                "new_today": new_today,
                "by_type": type_counts
            }
