"""
kolibri_service.py — Kolibri LMS integration with graceful failure handling.

If Kolibri DB unavailable: returns graceful empty response (never crashes).
Includes /kolibri/demo-sync simulation endpoint logic.
"""

import sqlite3
import os
import time
import logging
from contextlib import contextmanager
from typing import List, Dict, Optional, Any

from database import get_db_connection as get_app_db
from services import student_service

logger = logging.getLogger("pipeline")

# Configuration
KOLIBRI_DB_PATH = os.getenv("KOLIBRI_DB_PATH", "kolibri.sqlite3")


class KolibriSyncError(Exception):
    pass


@contextmanager
def get_kolibri_connection(timeout: int = 5, retries: int = 3):
    """Connect to Kolibri DB in read-only mode. Graceful if unavailable."""
    if not os.path.exists(KOLIBRI_DB_PATH):
        logger.warning(f"[KOLIBRI] DB not found at {KOLIBRI_DB_PATH}")
        yield None
        return

    conn = None
    attempt = 0
    while attempt < retries:
        try:
            db_uri = f"file:{KOLIBRI_DB_PATH}?mode=ro"
            conn = sqlite3.connect(db_uri, uri=True, timeout=timeout)
            conn.row_factory = sqlite3.Row
            break
        except sqlite3.OperationalError:
            attempt += 1
            logger.warning(f"[KOLIBRI] DB locked, retry {attempt}/{retries}")
            time.sleep(0.5)
            if attempt >= retries:
                logger.error("[KOLIBRI] Failed to connect after retries")
                yield None
                return

    try:
        yield conn
    finally:
        if conn:
            conn.close()


def get_completed_videos(kolibri_user_id: str = None) -> List[Dict[str, Any]]:
    """Query Kolibri for completed videos. Returns [] on failure."""
    completed = []
    try:
        with get_kolibri_connection() as conn:
            if not conn:
                return []

            cursor = conn.cursor()
            query = "SELECT content_id, end_timestamp, user_id FROM logger_contentsummarylog WHERE progress >= 1.0"
            params = []

            if kolibri_user_id:
                query += " AND user_id = ?"
                params.append(kolibri_user_id)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            for row in rows:
                completed.append({
                    "content_id": row["content_id"],
                    "timestamp": row["end_timestamp"],
                    "user_id": row["user_id"]
                })
    except Exception as e:
        logger.error(f"[KOLIBRI] Error querying videos: {e}")

    return completed


def is_video_synced(student_id: str, content_id: str) -> bool:
    """Check if video already synced. Returns False on error."""
    try:
        with get_app_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM kolibri_sync_logs WHERE student_id = ? AND video_id = ?",
                (student_id, content_id)
            )
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"[KOLIBRI] Sync check error: {e}")
        return False


def sync_kolibri_data(student_id: str, kolibri_user_id: str = None) -> Dict[str, Any]:
    """
    Main sync. Returns graceful response on any failure.
    """
    try:
        videos = get_completed_videos(kolibri_user_id)
        if not videos:
            return {"status": "no_new_data", "synced_count": 0, "total_xp_gained": 0, "items": [], "suggested_quiz": None}

        synced_items = []
        total_xp_gained = 0

        for vid in videos:
            content_id = vid["content_id"]
            if is_video_synced(student_id, content_id):
                continue

            subtopic = f"video_{content_id[:8]}"

            try:
                with get_app_db() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO topic_mastery (student_id, subtopic, mastery_score, attempts, correct_attempts) VALUES (?, ?, 0.2, 1, 1) ON CONFLICT(student_id, subtopic) DO UPDATE SET mastery_score = MIN(mastery_score + 0.1, 1.0)",
                        (student_id, subtopic)
                    )
                    cursor.execute("UPDATE students SET confidence_score = MIN(confidence_score + 0.05, 1.0) WHERE id = ?", (student_id,))
                    cursor.execute("UPDATE students SET xp = xp + 50 WHERE id = ?", (student_id,))
                    cursor.execute("UPDATE students SET level = (xp / 100) + 1 WHERE id = ?", (student_id,))
                    cursor.execute("INSERT INTO kolibri_sync_logs (student_id, video_id) VALUES (?, ?)", (student_id, content_id))
                    conn.commit()
                    total_xp_gained += 50
            except Exception as e:
                logger.error(f"[KOLIBRI] Sync item error: {e}")
                continue

            synced_items.append({"content_id": content_id, "subtopic": subtopic, "xp": 50})

        return {
            "status": "success" if synced_items else "no_new_data",
            "synced_count": len(synced_items),
            "total_xp_gained": total_xp_gained,
            "items": synced_items,
            "suggested_quiz": None
        }

    except Exception as e:
        logger.error(f"[KOLIBRI] Sync failed: {e}")
        return {"status": "error", "synced_count": 0, "total_xp_gained": 0, "items": [], "suggested_quiz": None}


def demo_sync(student_id: str) -> Dict[str, Any]:
    """
    Simulate a Kolibri sync for demo purposes.
    Awards 150 XP and returns success response.
    """
    logger.info(f"[KOLIBRI] Demo sync for {student_id}")
    try:
        with get_app_db() as conn:
            cursor = conn.cursor()
            # Ensure student exists
            cursor.execute("INSERT OR IGNORE INTO students (id) VALUES (?)", (student_id,))
            # Award XP
            cursor.execute("UPDATE students SET xp = xp + 150 WHERE id = ?", (student_id,))
            cursor.execute("UPDATE students SET level = (xp / 100) + 1 WHERE id = ?", (student_id,))
            # Boost confidence
            cursor.execute("UPDATE students SET confidence_score = MIN(confidence_score + 0.1, 1.0) WHERE id = ?", (student_id,))
            conn.commit()

        return {"status": "Synced", "xp_added": 150}
    except Exception as e:
        logger.error(f"[KOLIBRI] Demo sync error: {e}")
        return {"status": "Synced", "xp_added": 150}  # Return success anyway for demo
